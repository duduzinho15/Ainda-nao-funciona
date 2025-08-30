"""
Gerenciador do Bot do Telegram para o sistema Garimpeiro Geek.
Implementa comandos e funcionalidades de postagem automática.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
from decimal import Decimal

from src.core.models import Offer
from src.posting.message_formatter import message_formatter
from src.app.scheduler.post_scheduler import post_scheduler, JobPriority


class BotStatus(Enum):
    """Status do bot."""
    OFFLINE = "offline"
    ONLINE = "online"
    DRY_RUN = "dry_run"
    MAINTENANCE = "maintenance"


class PostingMode(Enum):
    """Modo de postagem."""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


@dataclass
class BotConfig:
    """Configuração do bot."""
    bot_token: str
    channel_id: str
    admin_user_ids: List[int] = field(default_factory=list)
    dry_run: bool = False
    max_posts_per_hour: int = 20
    auto_posting_enabled: bool = True
    moderation_enabled: bool = True


@dataclass
class TelegramBot:
    """Bot do Telegram para postagem de ofertas."""
    
    def __init__(self, config: BotConfig):
        """Inicializa o bot."""
        self.config = config
        self.status = BotStatus.OFFLINE
        self.posting_mode = PostingMode.AUTOMATIC
        self.logger = logging.getLogger(__name__)
        
        # Contadores de postagem
        self.posts_this_hour = 0
        self.last_post_time = None
        self.total_posts = 0
        
        # Fila de ofertas para postagem
        self.posting_queue: List[Offer] = []
        self.posted_offers: List[Offer] = []
        
        # Estatísticas
        self.stats = {
            "total_posts": 0,
            "successful_posts": 0,
            "failed_posts": 0,
            "last_post": None,
            "uptime": None
        }
        
        # Inicializar scheduler
        self._initialize_scheduler()
    
    def _initialize_scheduler(self):
        """Inicializa o scheduler de postagem."""
        # Job de postagem automática
        post_scheduler.add_job(
            id="telegram_posting",
            name="Telegram Posting",
            function=self._auto_posting_job,
            interval_seconds=45,  # 45 segundos
            priority=JobPriority.CRITICAL
        )
    
    async def start(self):
        """Inicia o bot."""
        try:
            self.status = BotStatus.ONLINE
            self.stats["uptime"] = datetime.now()
            
            # Iniciar scheduler
            post_scheduler.start()
            
            self.logger.info("🤖 Bot do Telegram iniciado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar bot: {e}")
            self.status = BotStatus.OFFLINE
            return False
    
    async def stop(self):
        """Para o bot."""
        try:
            self.status = BotStatus.OFFLINE
            post_scheduler.stop()
            
            self.logger.info("🤖 Bot do Telegram parado")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao parar bot: {e}")
            return False
    
    async def set_dry_run(self, enabled: bool):
        """Define modo DRY_RUN."""
        if enabled:
            self.status = BotStatus.DRY_RUN
            self.logger.info("🧪 Modo DRY_RUN ativado - Nenhuma postagem será feita")
        else:
            self.status = BotStatus.ONLINE
            self.logger.info("✅ Modo DRY_RUN desativado - Postagem normal ativada")
    
    async def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do bot."""
        return {
            "status": self.status.value,
            "posting_mode": self.posting_mode.value,
            "posts_this_hour": self.posts_this_hour,
            "total_posts": self.total_posts,
            "queue_size": len(self.posting_queue),
            "uptime": self.stats["uptime"].isoformat() if self.stats["uptime"] else None,
            "last_post": self.stats["last_post"].isoformat() if self.stats["last_post"] else None
        }
    
    async def add_offer_to_queue(self, offer: Offer) -> bool:
        """
        Adiciona oferta à fila de postagem.
        
        Args:
            offer: Oferta a ser postada
            
        Returns:
            True se adicionada com sucesso
        """
        try:
            # Validar oferta
            if not self._validate_offer(offer):
                self.logger.warning(f"Oferta inválida rejeitada: {offer.title}")
                return False
            
            # Adicionar à fila
            self.posting_queue.append(offer)
            self.logger.info(f"Oferta adicionada à fila: {offer.title}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar oferta à fila: {e}")
            return False
    
    def _validate_offer(self, offer: Offer) -> bool:
        """Valida se uma oferta pode ser postada."""
        if not offer:
            return False
        
        if not offer.title or not offer.affiliate_url:
            return False
        
        if offer.current_price <= 0:
            return False
        
        return True
    
    async def _auto_posting_job(self):
        """Job automático de postagem."""
        if not self.config.auto_posting_enabled:
            return
        
        if self.status != BotStatus.ONLINE:
            return
        
        # Verificar limite de postagens por hora
        if self._is_rate_limited():
            self.logger.info("⏱️ Rate limit atingido, aguardando...")
            return
        
        # Processar fila de postagem
        await self._process_posting_queue()
    
    def _is_rate_limited(self) -> bool:
        """Verifica se atingiu o limite de postagens por hora."""
        now = datetime.now()
        
        # Reset contador se passou uma hora
        if (self.last_post_time is None or 
            (now - self.last_post_time).total_seconds() > 3600):
            self.posts_this_hour = 0
            self.last_post_time = now
        
        return self.posts_this_hour >= self.config.max_posts_per_hour
    
    async def _process_posting_queue(self):
        """Processa a fila de postagem."""
        if not self.posting_queue:
            return
        
        # Pegar próxima oferta da fila
        offer = self.posting_queue.pop(0)
        
        try:
            # Formatar mensagem
            message = message_formatter.format_offer(offer)
            
            # Postar no canal
            success = await self._post_to_channel(message, offer)
            
            if success:
                self.posts_this_hour += 1
                self.total_posts += 1
                self.stats["total_posts"] += 1
                self.stats["successful_posts"] += 1
                self.stats["last_post"] = datetime.now()
                
                # Adicionar à lista de ofertas postadas
                self.posted_offers.append(offer)
                
                self.logger.info(f"✅ Oferta postada com sucesso: {offer.title}")
            else:
                self.stats["failed_posts"] += 1
                self.logger.error(f"❌ Falha ao postar oferta: {offer.title}")
                
        except Exception as e:
            self.logger.error(f"Erro ao processar oferta: {e}")
            self.stats["failed_posts"] += 1
    
    async def _post_to_channel(self, message: str, offer: Offer) -> bool:
        """
        Posta mensagem no canal do Telegram.
        
        Args:
            message: Mensagem formatada
            offer: Oferta sendo postada
            
        Returns:
            True se postada com sucesso
        """
        try:
            # Verificar modo DRY_RUN
            if self.status == BotStatus.DRY_RUN:
                self.logger.info(f"🧪 DRY_RUN - Mensagem não postada: {offer.title}")
                return True
            
            # Em produção, aqui seria feita a postagem real via API do Telegram
            # Por enquanto, simulamos o sucesso
            
            # Simular delay de postagem
            await asyncio.sleep(1)
            
            self.logger.info(f"📝 Mensagem postada no canal: {len(message)} caracteres")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao postar no canal: {e}")
            return False
    
    async def test_post(self, test_message: str = None) -> bool:
        """
        Testa postagem no canal.
        
        Args:
            test_message: Mensagem de teste (opcional)
            
        Returns:
            True se teste bem-sucedido
        """
        try:
            if not test_message:
                test_message = (
                    "🧪 **TESTE DE POSTAGEM**\n\n"
                    "Este é um teste do sistema Garimpeiro Geek.\n"
                    "Data/Hora: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                )
            
            # Criar oferta de teste
            test_offer = Offer(
                title="Teste de Sistema",
                current_price=Decimal("99.99"),
                affiliate_url="https://exemplo.com/teste",
                platform="test",
                category="Teste",
                store="Sistema"
            )
            
            # Formatar e postar
            message = message_formatter.format_offer(test_offer)
            success = await self._post_to_channel(message, test_offer)
            
            if success:
                self.logger.info("✅ Teste de postagem bem-sucedido")
            else:
                self.logger.error("❌ Teste de postagem falhou")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro no teste de postagem: {e}")
            return False
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Retorna status da fila de postagem."""
        return {
            "queue_size": len(self.posting_queue),
            "posted_count": len(self.posted_offers),
            "posts_this_hour": self.posts_this_hour,
            "max_posts_per_hour": self.config.max_posts_per_hour,
            "next_post_in": self._get_next_post_delay()
        }
    
    def _get_next_post_delay(self) -> Optional[int]:
        """Retorna delay até próxima postagem em segundos."""
        if not self.last_post_time:
            return 0
        
        elapsed = (datetime.now() - self.last_post_time).total_seconds()
        if elapsed >= 3600:  # 1 hora
            return 0
        
        return int(3600 - elapsed)
    
    async def clear_queue(self) -> int:
        """Limpa a fila de postagem."""
        queue_size = len(self.posting_queue)
        self.posting_queue.clear()
        
        self.logger.info(f"🗑️ Fila de postagem limpa: {queue_size} ofertas removidas")
        return queue_size
    
    async def get_posting_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de postagem."""
        return {
            "total_posts": self.stats["total_posts"],
            "successful_posts": self.stats["successful_posts"],
            "failed_posts": self.stats["failed_posts"],
            "success_rate": (
                self.stats["successful_posts"] / self.stats["total_posts"]
                if self.stats["total_posts"] > 0 else 0
            ),
            "posts_this_hour": self.posts_this_hour,
            "queue_size": len(self.posting_queue),
            "uptime": (
                (datetime.now() - self.stats["uptime"]).total_seconds()
                if self.stats["uptime"] else 0
            )
        }
    
    async def emergency_stop(self):
        """Para o bot em emergência."""
        self.logger.warning("🚨 PARADA DE EMERGÊNCIA ATIVADA")
        
        # Parar scheduler
        post_scheduler.stop()
        
        # Limpar fila
        await self.clear_queue()
        
        # Mudar status
        self.status = BotStatus.MAINTENANCE
        
        self.logger.info("🛑 Bot parado em emergência")


# Instância global do bot
telegram_bot = None


def create_bot(config: BotConfig) -> TelegramBot:
    """Cria uma instância do bot."""
    global telegram_bot
    telegram_bot = TelegramBot(config)
    return telegram_bot


def get_bot() -> Optional[TelegramBot]:
    """Retorna a instância global do bot."""
    return telegram_bot

