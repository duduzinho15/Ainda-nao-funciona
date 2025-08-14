"""
Sistema de Rate Limiting Inteligente para o Bot Garimpeiro Geek

Este módulo implementa um sistema de rate limiting avançado com:
- Múltiplas estratégias de limitação (fixo, adaptativo, exponencial)
- Detecção automática de bloqueios e ajuste dinâmico
- Diferentes tipos de limites por domínio/API
- Sistema de backoff exponencial
- Métricas de performance e bloqueios
- Integração com sistema de cache
"""

import time
import random
import asyncio
import threading
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import json

logger = logging.getLogger(__name__)

class RateLimitStrategy:
    """Estratégia base para rate limiting."""
    
    def __init__(self, name: str):
        self.name = name
    
    def should_allow(self, identifier: str, current_time: float) -> bool:
        """Verifica se a requisição deve ser permitida."""
        raise NotImplementedError
    
    def record_request(self, identifier: str, current_time: float):
        """Registra uma requisição."""
        raise NotImplementedError
    
    def get_wait_time(self, identifier: str, current_time: float) -> float:
        """Retorna o tempo de espera necessário."""
        raise NotImplementedError

class FixedWindowStrategy(RateLimitStrategy):
    """Estratégia de janela fixa para rate limiting."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        super().__init__("fixed_window")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    def should_allow(self, identifier: str, current_time: float) -> bool:
        # Remove requisições antigas
        self._cleanup_old_requests(identifier, current_time)
        
        # Verifica se ainda há espaço na janela
        return len(self.requests[identifier]) < self.max_requests
    
    def record_request(self, identifier: str, current_time: float):
        self.requests[identifier].append(current_time)
    
    def get_wait_time(self, identifier: str, current_time: float) -> float:
        if self.should_allow(identifier, current_time):
            return 0.0
        
        # Calcula tempo até a próxima janela
        oldest_request = min(self.requests[identifier])
        next_window_start = oldest_request + self.window_seconds
        return max(0.0, next_window_start - current_time)
    
    def _cleanup_old_requests(self, identifier: str, current_time: float):
        """Remove requisições antigas da janela."""
        cutoff_time = current_time - self.window_seconds
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff_time
        ]

class SlidingWindowStrategy(RateLimitStrategy):
    """Estratégia de janela deslizante para rate limiting."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        super().__init__("sliding_window")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
    
    def should_allow(self, identifier: str, current_time: float) -> bool:
        # Remove requisições antigas
        self._cleanup_old_requests(identifier, current_time)
        
        # Verifica se ainda há espaço na janela
        return len(self.requests[identifier]) < self.max_requests
    
    def record_request(self, identifier: str, current_time: float):
        self.requests[identifier].append(current_time)
    
    def get_wait_time(self, identifier: str, current_time: float) -> float:
        if self.should_allow(identifier, current_time):
            return 0.0
        
        # Calcula tempo até a requisição mais antiga sair da janela
        oldest_request = self.requests[identifier][0]
        return max(0.0, oldest_request + self.window_seconds - current_time)
    
    def _cleanup_old_requests(self, identifier: str, current_time: float):
        """Remove requisições antigas da janela."""
        cutoff_time = current_time - self.window_seconds
        while (self.requests[identifier] and 
               self.requests[identifier][0] <= cutoff_time):
            self.requests[identifier].popleft()

class AdaptiveStrategy(RateLimitStrategy):
    """Estratégia adaptativa que ajusta limites baseado em respostas."""
    
    def __init__(self, initial_max_requests: int, window_seconds: int, 
                 min_requests: int = 1, max_requests: int = 100):
        super().__init__("adaptive")
        self.initial_max_requests = initial_max_requests
        self.current_max_requests = initial_max_requests
        self.window_seconds = window_seconds
        self.min_requests = min_requests
        self.max_requests = max_requests
        
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.success_count = 0
        self.error_count = 0
        self.last_adjustment = time.time()
        self.adjustment_interval = 60  # Ajusta a cada minuto
    
    def should_allow(self, identifier: str, current_time: float) -> bool:
        self._cleanup_old_requests(identifier, current_time)
        return len(self.requests[identifier]) < self.current_max_requests
    
    def record_request(self, identifier: str, current_time: float):
        self.requests[identifier].append(current_time)
    
    def get_wait_time(self, identifier: str, current_time: float) -> float:
        if self.should_allow(identifier, current_time):
            return 0.0
        
        # Calcula tempo até a próxima janela
        oldest_request = min(self.requests[identifier])
        next_window_start = oldest_request + self.window_seconds
        return max(0.0, next_window_start - current_time)
    
    def record_response(self, success: bool):
        """Registra resposta para ajuste adaptativo."""
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        # Ajusta limites periodicamente
        current_time = time.time()
        if current_time - self.last_adjustment >= self.adjustment_interval:
            self._adjust_limits()
            self.last_adjustment = current_time
    
    def _adjust_limits(self):
        """Ajusta limites baseado no histórico de respostas."""
        total_responses = self.success_count + self.error_count
        if total_responses == 0:
            return
        
        success_rate = self.success_count / total_responses
        
        if success_rate > 0.95:  # Muito bem sucedido
            # Aumenta limite
            self.current_max_requests = min(
                self.max_requests,
                int(self.current_max_requests * 1.1)
            )
            logger.info(f"Rate limit aumentado para {self.current_max_requests}")
        
        elif success_rate < 0.8:  # Muitos erros
            # Diminui limite
            self.current_max_requests = max(
                self.min_requests,
                int(self.current_max_requests * 0.8)
            )
            logger.warning(f"Rate limit diminuído para {self.current_max_requests}")
        
        # Reset contadores
        self.success_count = 0
        self.error_count = 0
    
    def _cleanup_old_requests(self, identifier: str, current_time: float):
        """Remove requisições antigas da janela."""
        cutoff_time = current_time - self.window_seconds
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff_time
        ]

class ExponentialBackoffStrategy(RateLimitStrategy):
    """Estratégia de backoff exponencial para casos de erro."""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 300.0, 
                 multiplier: float = 2.0):
        super().__init__("exponential_backoff")
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.failure_count: Dict[str, int] = defaultdict(int)
        self.last_failure: Dict[str, float] = defaultdict(float)
    
    def should_allow(self, identifier: str, current_time: float) -> bool:
        if identifier not in self.last_failure:
            return True
        
        # Calcula delay atual
        delay = self._calculate_delay(identifier)
        time_since_failure = current_time - self.last_failure[identifier]
        
        return time_since_failure >= delay
    
    def record_request(self, identifier: str, current_time: float):
        # Reset contador de falhas em caso de sucesso
        if identifier in self.failure_count:
            self.failure_count[identifier] = 0
    
    def record_failure(self, identifier: str, current_time: float):
        """Registra uma falha para backoff."""
        self.failure_count[identifier] += 1
        self.last_failure[identifier] = current_time
        logger.warning(f"Falha registrada para {identifier}, backoff ativado")
    
    def get_wait_time(self, identifier: str, current_time: float) -> float:
        if self.should_allow(identifier, current_time):
            return 0.0
        
        delay = self._calculate_delay(identifier)
        time_since_failure = current_time - self.last_failure[identifier]
        return max(0.0, delay - time_since_failure)
    
    def _calculate_delay(self, identifier: str) -> float:
        """Calcula delay baseado no número de falhas."""
        failure_count = self.failure_count[identifier]
        delay = self.base_delay * (self.multiplier ** failure_count)
        return min(delay, self.max_delay)

class IntelligentRateLimiter:
    """
    Sistema de rate limiting inteligente que combina múltiplas estratégias.
    """
    
    def __init__(self):
        self.strategies: Dict[str, RateLimitStrategy] = {}
        self.domain_strategies: Dict[str, str] = {}
        self.blocked_domains: Dict[str, Dict[str, Any]] = {}
        
        # Métricas
        self.total_requests = 0
        self.blocked_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
        # Configurações padrão
        self._setup_default_strategies()
        
        # Thread de monitoramento
        self._monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self._monitor_thread.start()
    
    def _setup_default_strategies(self):
        """Configura estratégias padrão de rate limiting."""
        # Estratégia padrão para APIs
        self.add_strategy("default_api", FixedWindowStrategy(100, 3600))  # 100 req/hora
        
        # Estratégia para scrapers
        self.add_strategy("scraper", SlidingWindowStrategy(30, 300))  # 30 req/5min
        
        # Estratégia para Amazon
        self.add_strategy("amazon", AdaptiveStrategy(20, 3600, 5, 50))
        
        # Estratégia para AliExpress
        self.add_strategy("aliexpress", FixedWindowStrategy(50, 3600))  # 50 req/hora
        
        # Estratégia para Magazine Luiza
        self.add_strategy("magalu", SlidingWindowStrategy(20, 300))  # 20 req/5min
        
        # Estratégia para Promobit
        self.add_strategy("promobit", AdaptiveStrategy(15, 300, 3, 30))
        
        # Estratégia para Awin
        self.add_strategy("awin", FixedWindowStrategy(200, 3600))  # 200 req/hora
    
    def add_strategy(self, name: str, strategy: RateLimitStrategy):
        """Adiciona uma nova estratégia de rate limiting."""
        self.strategies[name] = strategy
        logger.info(f"Estratégia de rate limiting adicionada: {name}")
    
    def set_domain_strategy(self, domain: str, strategy_name: str):
        """Define qual estratégia usar para um domínio específico."""
        if strategy_name in self.strategies:
            self.domain_strategies[domain] = strategy_name
            logger.info(f"Domínio {domain} configurado para usar estratégia {strategy_name}")
        else:
            logger.warning(f"Estratégia {strategy_name} não encontrada para domínio {domain}")
    
    def get_strategy_for_domain(self, domain: str) -> RateLimitStrategy:
        """Retorna a estratégia apropriada para um domínio."""
        # Verifica se há estratégia específica para o domínio
        if domain in self.domain_strategies:
            strategy_name = self.domain_strategies[domain]
            return self.strategies[strategy_name]
        
        # Verifica se o domínio corresponde a algum padrão conhecido
        if "amazon" in domain.lower():
            return self.strategies["amazon"]
        elif "aliexpress" in domain.lower():
            return self.strategies["aliexpress"]
        elif "magalu" in domain.lower() or "magazine" in domain.lower():
            return self.strategies["magalu"]
        elif "promobit" in domain.lower():
            return self.strategies["promobit"]
        elif "awin" in domain.lower():
            return self.strategies["awin"]
        
        # Retorna estratégia padrão
        return self.strategies["default_api"]
    
    def should_allow_request(self, domain: str, identifier: str = None) -> bool:
        """
        Verifica se uma requisição deve ser permitida.
        
        Args:
            domain: Domínio da requisição
            identifier: Identificador único (IP, user_id, etc.)
            
        Returns:
            True se a requisição deve ser permitida
        """
        if identifier is None:
            identifier = domain
        
        # Verifica se o domínio está bloqueado
        if self._is_domain_blocked(domain):
            self.blocked_requests += 1
            return False
        
        # Obtém estratégia apropriada
        strategy = self.get_strategy_for_domain(domain)
        current_time = time.time()
        
        # Verifica rate limit
        if strategy.should_allow(identifier, current_time):
            self.total_requests += 1
            return True
        
        self.blocked_requests += 1
        return False
    
    def record_request(self, domain: str, identifier: str = None, success: bool = True):
        """
        Registra uma requisição para estatísticas e ajustes.
        
        Args:
            domain: Domínio da requisição
            identifier: Identificador único
            success: Se a requisição foi bem-sucedida
        """
        if identifier is None:
            identifier = domain
        
        strategy = self.get_strategy_for_domain(domain)
        current_time = time.time()
        
        # Registra na estratégia
        strategy.record_request(identifier, current_time)
        
        # Registra métricas
        if success:
            self.successful_requests += 1
            # Registra sucesso para estratégias adaptativas
            if hasattr(strategy, 'record_response'):
                strategy.record_response(True)
        else:
            self.failed_requests += 1
            # Registra falha para estratégias adaptativas
            if hasattr(strategy, 'record_response'):
                strategy.record_response(False)
            # Registra falha para backoff exponencial
            if isinstance(strategy, ExponentialBackoffStrategy):
                strategy.record_failure(identifier, current_time)
    
    def get_wait_time(self, domain: str, identifier: str = None) -> float:
        """
        Retorna o tempo de espera necessário antes da próxima requisição.
        
        Args:
            domain: Domínio da requisição
            identifier: Identificador único
            
        Returns:
            Tempo de espera em segundos
        """
        if identifier is None:
            identifier = domain
        
        strategy = self.get_strategy_for_domain(domain)
        current_time = time.time()
        
        return strategy.get_wait_time(identifier, current_time)
    
    def block_domain(self, domain: str, reason: str, duration: int = 3600):
        """
        Bloqueia um domínio temporariamente.
        
        Args:
            domain: Domínio a ser bloqueado
            reason: Razão do bloqueio
            duration: Duração do bloqueio em segundos
        """
        current_time = time.time()
        self.blocked_domains[domain] = {
            'blocked_at': current_time,
            'expires_at': current_time + duration,
            'reason': reason
        }
        logger.warning(f"Domínio {domain} bloqueado por {duration}s: {reason}")
    
    def unblock_domain(self, domain: str):
        """Remove bloqueio de um domínio."""
        if domain in self.blocked_domains:
            del self.blocked_domains[domain]
            logger.info(f"Bloqueio removido do domínio {domain}")
    
    def _is_domain_blocked(self, domain: str) -> bool:
        """Verifica se um domínio está bloqueado."""
        if domain not in self.blocked_domains:
            return False
        
        block_info = self.blocked_domains[domain]
        current_time = time.time()
        
        # Remove bloqueio expirado
        if current_time > block_info['expires_at']:
            del self.blocked_domains[domain]
            return False
        
        return True
    
    def _monitor_worker(self):
        """Worker thread para monitoramento contínuo."""
        while True:
            try:
                time.sleep(60)  # Executa a cada minuto
                self._cleanup_expired_blocks()
                self._log_metrics()
            except Exception as e:
                logger.error(f"Erro no monitor de rate limiting: {e}")
    
    def _cleanup_expired_blocks(self):
        """Remove bloqueios expirados."""
        current_time = time.time()
        expired_domains = [
            domain for domain, block_info in self.blocked_domains.items()
            if current_time > block_info['expires_at']
        ]
        
        for domain in expired_domains:
            self.unblock_domain(domain)
    
    def _log_metrics(self):
        """Registra métricas de performance."""
        total = self.total_requests + self.blocked_requests
        if total > 0:
            success_rate = (self.successful_requests / total) * 100
            block_rate = (self.blocked_requests / total) * 100
            
            logger.info(f"Rate Limiter Stats - Total: {total}, "
                       f"Sucesso: {success_rate:.1f}%, Bloqueados: {block_rate:.1f}%")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas do rate limiter."""
        total = self.total_requests + self.blocked_requests
        success_rate = (self.successful_requests / total * 100) if total > 0 else 0
        block_rate = (self.blocked_requests / total * 100) if total > 0 else 0
        
        return {
            'total_requests': total,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'blocked_requests': self.blocked_requests,
            'success_rate_percent': round(success_rate, 2),
            'block_rate_percent': round(block_rate, 2),
            'blocked_domains_count': len(self.blocked_domains),
            'active_strategies': list(self.strategies.keys()),
            'domain_strategies': dict(self.domain_strategies)
        }
    
    def get_domain_status(self, domain: str) -> Dict[str, Any]:
        """Retorna status detalhado de um domínio específico."""
        strategy = self.get_strategy_for_domain(domain)
        current_time = time.time()
        
        status = {
            'domain': domain,
            'strategy': strategy.name,
            'is_blocked': self._is_domain_blocked(domain),
            'wait_time': self.get_wait_time(domain),
            'can_request': self.should_allow_request(domain)
        }
        
        if self._is_domain_blocked(domain):
            block_info = self.blocked_domains[domain]
            status.update({
                'blocked_at': datetime.fromtimestamp(block_info['blocked_at']).isoformat(),
                'expires_at': datetime.fromtimestamp(block_info['expires_at']).isoformat(),
                'reason': block_info['reason']
            })
        
        return status

# Instância global do rate limiter
rate_limiter = IntelligentRateLimiter()

# Decorator para rate limiting automático
def rate_limited(domain: str = None, identifier_func: Callable = None):
    """
    Decorator para aplicar rate limiting automaticamente.
    
    Args:
        domain: Domínio para rate limiting (None para detectar automaticamente)
        identifier_func: Função para gerar identificador único
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Detecta domínio se não fornecido
            target_domain = domain
            if target_domain is None:
                target_domain = _detect_domain_from_args(args, kwargs)
            
            # Gera identificador
            identifier = None
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            
            # Verifica rate limit
            if not rate_limiter.should_allow_request(target_domain, identifier):
                wait_time = rate_limiter.get_wait_time(target_domain, identifier)
                logger.warning(f"Rate limit atingido para {target_domain}, aguardando {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
            
            try:
                # Executa função
                result = await func(*args, **kwargs)
                rate_limiter.record_request(target_domain, identifier, success=True)
                return result
            except Exception as e:
                rate_limiter.record_request(target_domain, identifier, success=False)
                raise
        
        def sync_wrapper(*args, **kwargs):
            # Detecta domínio se não fornecido
            target_domain = domain
            if target_domain is None:
                target_domain = _detect_domain_from_args(args, kwargs)
            
            # Gera identificador
            identifier = None
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            
            # Verifica rate limit
            if not rate_limiter.should_allow_request(target_domain, identifier):
                wait_time = rate_limiter.get_wait_time(target_domain, identifier)
                logger.warning(f"Rate limit atingido para {target_domain}, aguardando {wait_time:.1f}s")
                time.sleep(wait_time)
            
            try:
                # Executa função
                result = func(*args, **kwargs)
                rate_limiter.record_request(target_domain, identifier, success=True)
                return result
            except Exception as e:
                rate_limiter.record_request(target_domain, identifier, success=False)
                raise
        
        # Retorna wrapper apropriado
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def _detect_domain_from_args(args, kwargs) -> str:
    """Detecta domínio automaticamente dos argumentos da função."""
    # Procura por URLs ou domínios nos argumentos
    for arg in args:
        if isinstance(arg, str) and ('http://' in arg or 'https://' in arg):
            from urllib.parse import urlparse
            try:
                parsed = urlparse(arg)
                return parsed.netloc
            except:
                pass
    
    # Procura em kwargs
    for key, value in kwargs.items():
        if isinstance(value, str) and ('http://' in value or 'https://' in value):
            from urllib.parse import urlparse
            try:
                parsed = urlparse(value)
                return parsed.netloc
            except:
                pass
    
    # Retorna domínio padrão
    return "default"

# Funções de conveniência
def check_rate_limit(domain: str, identifier: str = None) -> bool:
    """Verifica se uma requisição deve ser permitida."""
    return rate_limiter.should_allow_request(domain, identifier)

def get_wait_time(domain: str, identifier: str = None) -> float:
    """Retorna tempo de espera necessário."""
    return rate_limiter.get_wait_time(domain, identifier)

def record_request(domain: str, identifier: str = None, success: bool = True):
    """Registra uma requisição."""
    rate_limiter.record_request(domain, identifier, success)

def block_domain(domain: str, reason: str, duration: int = 3600):
    """Bloqueia um domínio temporariamente."""
    rate_limiter.block_domain(domain, reason, duration)

def get_rate_limiter_stats() -> Dict[str, Any]:
    """Retorna estatísticas do rate limiter."""
    return rate_limiter.get_stats()

if __name__ == "__main__":
    # Teste do sistema de rate limiting
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Teste básico
    print("Testando Rate Limiter...")
    
    # Testa estratégia fixa
    domain = "test.com"
    for i in range(5):
        allowed = check_rate_limit(domain)
        print(f"Requisição {i+1}: {'Permitida' if allowed else 'Bloqueada'}")
        if allowed:
            record_request(domain, success=True)
    
    # Mostra estatísticas
    stats = get_rate_limiter_stats()
    print(f"Estatísticas: {stats}")
