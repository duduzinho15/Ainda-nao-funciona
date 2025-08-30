"""
Sistema de rate limiting para o Garimpeiro Geek.

Implementa limitação de taxa para:
- Requisições por plataforma/API
- Postagens no Telegram
- Scrapers individuais
- Conversores de afiliado
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RateLimitType(Enum):
    """Tipos de rate limiting"""

    API_REQUEST = "api_request"
    TELEGRAM_POST = "telegram_post"
    SCRAPER = "scraper"
    AFFILIATE_CONVERSION = "affiliate_conversion"
    DATABASE_WRITE = "database_write"


@dataclass
class RateLimit:
    """Configuração de rate limit"""

    max_requests: int  # Máximo de requisições
    window_seconds: int  # Janela de tempo em segundos
    burst_size: Optional[int] = None  # Tamanho do burst (opcional)
    cooldown_seconds: Optional[int] = None  # Cooldown após limite (opcional)


@dataclass
class RateLimitResult:
    """Resultado da verificação de rate limit"""

    allowed: bool
    remaining: int
    reset_time: datetime
    retry_after_seconds: Optional[int] = None
    reason: Optional[str] = None


class TokenBucket:
    """Implementação de Token Bucket para rate limiting"""

    def __init__(self, max_tokens: int, refill_rate: float):
        self.max_tokens = max_tokens
        self.tokens = max_tokens
        self.refill_rate = refill_rate  # tokens por segundo
        self.last_refill = time.time()
        self.lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """
        Tentar consumir tokens do bucket

        Args:
            tokens: Número de tokens a consumir

        Returns:
            True se tokens foram consumidos, False caso contrário
        """
        async with self.lock:
            now = time.time()

            # Reabastecer tokens baseado no tempo decorrido
            time_passed = now - self.last_refill
            new_tokens = time_passed * self.refill_rate
            self.tokens = min(self.max_tokens, self.tokens + new_tokens)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            else:
                return False

    def get_tokens(self) -> float:
        """Obter número atual de tokens"""
        return self.tokens


class SlidingWindow:
    """Implementação de Sliding Window para rate limiting"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self.lock = asyncio.Lock()

    async def is_allowed(self) -> Tuple[bool, int]:
        """
        Verificar se requisição é permitida

        Returns:
            Tuple (allowed, remaining_requests)
        """
        async with self.lock:
            now = time.time()
            cutoff_time = now - self.window_seconds

            # Remover requisições antigas
            while self.requests and self.requests[0] <= cutoff_time:
                self.requests.popleft()

            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True, self.max_requests - len(self.requests)
            else:
                return False, 0

    def get_reset_time(self) -> datetime:
        """Obter tempo de reset da janela"""
        if self.requests:
            oldest_request = self.requests[0]
            reset_time = oldest_request + self.window_seconds
            return datetime.fromtimestamp(reset_time)
        else:
            return datetime.now()


class RateLimiter:
    """Sistema principal de rate limiting"""

    def __init__(self):
        # Configurações padrão por tipo
        self.default_limits = {
            RateLimitType.API_REQUEST: RateLimit(100, 3600),  # 100 req/hora
            RateLimitType.TELEGRAM_POST: RateLimit(20, 60),  # 20 posts/min
            RateLimitType.SCRAPER: RateLimit(60, 3600),  # 60 req/hora
            RateLimitType.AFFILIATE_CONVERSION: RateLimit(200, 3600),  # 200 conv/hora
            RateLimitType.DATABASE_WRITE: RateLimit(1000, 60),  # 1000 writes/min
        }

        # Configurações específicas por plataforma/recurso
        self.platform_limits = {
            # APIs oficiais
            "amazon_api": RateLimit(100, 3600),
            "shopee_api": RateLimit(200, 3600),
            "aliexpress_api": RateLimit(150, 3600),
            "awin_api": RateLimit(100, 3600),
            "rakuten_api": RateLimit(100, 3600),
            # Scrapers de lojas
            "amazon_scraper": RateLimit(30, 3600),
            "shopee_scraper": RateLimit(60, 3600),
            "mercadolivre_scraper": RateLimit(60, 3600),
            "magalu_scraper": RateLimit(60, 3600),
            "aliexpress_scraper": RateLimit(30, 3600),
            # Scrapers de comunidades
            "promobit_scraper": RateLimit(120, 3600),
            "pelando_scraper": RateLimit(120, 3600),
            "meupc_scraper": RateLimit(60, 3600),
            # Scrapers de preços
            "zoom_scraper": RateLimit(60, 3600),
            "buscape_scraper": RateLimit(60, 3600),
            # Telegram
            "telegram_bot": RateLimit(30, 60),  # 30 msgs/min
            "telegram_channel": RateLimit(20, 60),  # 20 posts/min
        }

        # Instâncias de limitadores
        self.sliding_windows: Dict[str, SlidingWindow] = {}
        self.token_buckets: Dict[str, TokenBucket] = {}
        self.cooldowns: Dict[str, datetime] = {}

        # Estatísticas
        self.stats = defaultdict(
            lambda: {
                "total_requests": 0,
                "allowed_requests": 0,
                "blocked_requests": 0,
                "last_reset": datetime.now(),
            }
        )

    async def check_rate_limit(
        self,
        resource_id: str,
        limit_type: Optional[RateLimitType] = None,
        custom_limit: Optional[RateLimit] = None,
    ) -> RateLimitResult:
        """
        Verificar se requisição está dentro do rate limit

        Args:
            resource_id: Identificador do recurso (ex: "amazon_api", "telegram_bot")
            limit_type: Tipo de rate limit (usado se custom_limit não fornecido)
            custom_limit: Limite customizado

        Returns:
            Resultado da verificação
        """
        try:
            # Obter configuração de limite
            if custom_limit:
                limit_config = custom_limit
            elif resource_id in self.platform_limits:
                limit_config = self.platform_limits[resource_id]
            elif limit_type and limit_type in self.default_limits:
                limit_config = self.default_limits[limit_type]
            else:
                # Limite padrão muito permissivo
                limit_config = RateLimit(1000, 3600)

            # Verificar cooldown
            if resource_id in self.cooldowns:
                if datetime.now() < self.cooldowns[resource_id]:
                    cooldown_remaining = (
                        self.cooldowns[resource_id] - datetime.now()
                    ).total_seconds()
                    return RateLimitResult(
                        allowed=False,
                        remaining=0,
                        reset_time=self.cooldowns[resource_id],
                        retry_after_seconds=int(cooldown_remaining),
                        reason="Em cooldown",
                    )
                else:
                    # Cooldown expirado
                    del self.cooldowns[resource_id]

            # Obter ou criar sliding window
            if resource_id not in self.sliding_windows:
                self.sliding_windows[resource_id] = SlidingWindow(
                    limit_config.max_requests, limit_config.window_seconds
                )

            window = self.sliding_windows[resource_id]
            allowed, remaining = await window.is_allowed()

            # Atualizar estatísticas
            self.stats[resource_id]["total_requests"] += 1
            if allowed:
                self.stats[resource_id]["allowed_requests"] += 1
            else:
                self.stats[resource_id]["blocked_requests"] += 1

                # Aplicar cooldown se configurado
                if limit_config.cooldown_seconds:
                    cooldown_until = datetime.now() + timedelta(
                        seconds=limit_config.cooldown_seconds
                    )
                    self.cooldowns[resource_id] = cooldown_until

            reset_time = window.get_reset_time()
            retry_after = None

            if not allowed:
                retry_after = max(1, int((reset_time - datetime.now()).total_seconds()))

            return RateLimitResult(
                allowed=allowed,
                remaining=remaining,
                reset_time=reset_time,
                retry_after_seconds=retry_after,
                reason="Rate limit excedido" if not allowed else None,
            )

        except Exception as e:
            logger.error(f"Erro ao verificar rate limit para {resource_id}: {e}")
            # Em caso de erro, permitir requisição (fail open)
            return RateLimitResult(
                allowed=True,
                remaining=999,
                reset_time=datetime.now() + timedelta(hours=1),
                reason=f"Erro na verificação: {e}",
            )

    async def wait_if_needed(
        self,
        resource_id: str,
        limit_type: Optional[RateLimitType] = None,
        max_wait_seconds: int = 60,
    ) -> bool:
        """
        Aguardar se necessário para respeitar rate limit

        Args:
            resource_id: Identificador do recurso
            limit_type: Tipo de rate limit
            max_wait_seconds: Tempo máximo de espera

        Returns:
            True se requisição foi permitida (após espera), False se timeout
        """
        # Tentar primeiro sem consumir quota
        result = await self.check_rate_limit(resource_id, limit_type)

        if result.allowed:
            return True

        if (
            result.retry_after_seconds
            and result.retry_after_seconds <= max_wait_seconds
        ):
            logger.info(
                f"Rate limit para {resource_id}, aguardando {result.retry_after_seconds}s"
            )
            await asyncio.sleep(result.retry_after_seconds)

            # Verificar novamente após espera e consumir quota desta vez
            result = await self.check_rate_limit(resource_id, limit_type)
            return result.allowed

        logger.warning(
            f"Rate limit para {resource_id} excede tempo máximo de espera ({max_wait_seconds}s)"
        )
        return False

    def update_platform_limit(self, platform: str, limit: RateLimit):
        """Atualizar limite específico de uma plataforma"""
        self.platform_limits[platform] = limit

        # Remover instância existente para recriar com novo limite
        if platform in self.sliding_windows:
            del self.sliding_windows[platform]

        logger.info(
            f"Limite atualizado para {platform}: {limit.max_requests}/{limit.window_seconds}s"
        )

    def get_stats(self, resource_id: Optional[str] = None) -> Dict:
        """
        Obter estatísticas de rate limiting

        Args:
            resource_id: ID específico ou None para todos

        Returns:
            Estatísticas de uso
        """
        if resource_id:
            return dict(self.stats.get(resource_id, {}))
        else:
            return {k: dict(v) for k, v in self.stats.items()}

    def reset_stats(self, resource_id: Optional[str] = None):
        """Resetar estatísticas"""
        if resource_id:
            if resource_id in self.stats:
                self.stats[resource_id] = {
                    "total_requests": 0,
                    "allowed_requests": 0,
                    "blocked_requests": 0,
                    "last_reset": datetime.now(),
                }
        else:
            self.stats.clear()

        logger.info(f"Estatísticas resetadas para {resource_id or 'todos os recursos'}")

    def clear_cooldowns(self):
        """Limpar todos os cooldowns"""
        self.cooldowns.clear()
        logger.info("Todos os cooldowns foram limpos")

    async def batch_check(
        self, resource_requests: List[Tuple[str, Optional[RateLimitType]]]
    ) -> List[RateLimitResult]:
        """
        Verificar rate limit para múltiplos recursos de uma vez

        Args:
            resource_requests: Lista de (resource_id, limit_type)

        Returns:
            Lista de resultados
        """
        tasks = [
            self.check_rate_limit(resource_id, limit_type)
            for resource_id, limit_type in resource_requests
        ]

        return await asyncio.gather(*tasks)


# Instância global do rate limiter
rate_limiter = RateLimiter()
