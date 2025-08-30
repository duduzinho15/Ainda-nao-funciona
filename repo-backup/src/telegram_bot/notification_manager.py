#!/usr/bin/env python3
"""
Notification Manager para o Bot Telegram do Garimpeiro Geek
Sistema de gerenciamento de notificações e alertas
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set

from src.core.models import Offer

from .message_builder import MessageBuilder


@dataclass
class NotificationConfig:
    """Configuração de notificações"""

    enabled: bool = True
    price_alerts: bool = True
    system_alerts: bool = True
    offer_notifications: bool = True
    error_notifications: bool = True
    success_notifications: bool = False  # Desabilitado por padrão para evitar spam

    # Intervalos mínimos entre notificações (em segundos)
    min_interval_price_alert: int = 300  # 5 minutos
    min_interval_system_alert: int = 600  # 10 minutos
    min_interval_error: int = 300  # 5 minutos

    # Horários de silêncio (não enviar notificações)
    quiet_hours_start: int = 23  # 23:00
    quiet_hours_end: int = 7  # 07:00


@dataclass
class NotificationRecord:
    """Registro de notificação enviada"""

    notification_type: str
    content_hash: str
    sent_at: datetime
    recipients: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


class NotificationManager:
    """
    Gerenciador de notificações para o sistema Garimpeiro Geek
    """

    def __init__(self):
        self.logger = logging.getLogger("telegram.notification_manager")
        self.message_builder = MessageBuilder()

        # Configuração
        self.config = NotificationConfig()

        # Histórico de notificações para evitar duplicatas
        self.notification_history: Dict[str, NotificationRecord] = {}

        # Usuários que receberão notificações
        self.subscribers: Set[str] = set()

        # Contadores de notificações
        self.notification_counters = {
            "price_alerts": 0,
            "system_alerts": 0,
            "offer_notifications": 0,
            "error_notifications": 0,
            "success_notifications": 0,
        }

        # Limpeza automática do histórico
        self._cleanup_task = None
        self._start_cleanup_task()

    def _start_cleanup_task(self):
        """Inicia tarefa de limpeza automática do histórico"""

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(3600)  # Limpar a cada hora
                    self._cleanup_old_notifications()
                except Exception as e:
                    self.logger.error(f"Erro na limpeza automática: {e}")

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._cleanup_task = asyncio.create_task(cleanup_loop())
            else:
                self._cleanup_task = asyncio.ensure_future(cleanup_loop(), loop=loop)
        except Exception as e:
            self.logger.warning(f"Não foi possível iniciar tarefa de limpeza: {e}")

    def add_subscriber(self, user_id: str) -> bool:
        """Adiciona usuário à lista de assinantes"""
        if user_id not in self.subscribers:
            self.subscribers.add(user_id)
            self.logger.info(f"Usuário {user_id} adicionado como assinante")
            return True
        return False

    def remove_subscriber(self, user_id: str) -> bool:
        """Remove usuário da lista de assinantes"""
        if user_id in self.subscribers:
            self.subscribers.remove(user_id)
            self.logger.info(f"Usuário {user_id} removido dos assinantes")
            return True
        return False

    def get_subscribers(self) -> Set[str]:
        """Retorna lista de assinantes"""
        return self.subscribers.copy()

    def update_config(self, **kwargs) -> bool:
        """Atualiza configuração de notificações"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    self.logger.info(f"Configuração atualizada: {key} = {value}")
                else:
                    self.logger.warning(f"Configuração inválida: {key}")
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Erro ao atualizar configuração: {e}")
            return False

    def get_config(self) -> NotificationConfig:
        """Retorna configuração atual"""
        return self.config

    def is_quiet_hours(self) -> bool:
        """Verifica se está em horário de silêncio"""
        current_hour = datetime.now().hour
        if self.config.quiet_hours_start > self.config.quiet_hours_end:
            # Horário de silêncio cruza a meia-noite
            return (
                current_hour >= self.config.quiet_hours_start
                or current_hour <= self.config.quiet_hours_end
            )
        else:
            return (
                self.config.quiet_hours_start
                <= current_hour
                <= self.config.quiet_hours_end
            )

    def _should_send_notification(
        self, notification_type: str, content_hash: str
    ) -> bool:
        """Verifica se deve enviar notificação baseado em regras"""
        if not self.config.enabled:
            return False

        if self.is_quiet_hours():
            self.logger.debug("Notificação suprimida durante horário de silêncio")
            return False

        # Verificar se já foi enviada recentemente
        if content_hash in self.notification_history:
            record = self.notification_history[content_hash]
            min_interval = getattr(self.config, f"min_interval_{notification_type}", 0)

            if datetime.now() - record.sent_at < timedelta(seconds=min_interval):
                self.logger.debug(
                    f"Notificação {notification_type} suprimida por intervalo mínimo"
                )
                return False

        return True

    def _record_notification(
        self,
        notification_type: str,
        content_hash: str,
        recipients: Set[str],
        metadata: Dict[str, Any] = None,
    ):
        """Registra notificação enviada"""
        self.notification_history[content_hash] = NotificationRecord(
            notification_type=notification_type,
            content_hash=content_hash,
            sent_at=datetime.now(),
            recipients=recipients,
            metadata=metadata or {},
        )

        # Atualizar contador
        counter_key = f"{notification_type}_notifications"
        if counter_key in self.notification_counters:
            self.notification_counters[counter_key] += 1

    def _cleanup_old_notifications(self, max_age_hours: int = 24):
        """Remove notificações antigas do histórico"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_keys = [
            key
            for key, record in self.notification_history.items()
            if record.sent_at < cutoff_time
        ]

        for key in old_keys:
            del self.notification_history[key]

        if old_keys:
            self.logger.info(f"Limpeza: {len(old_keys)} notificações antigas removidas")

    def get_notification_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de notificações"""
        return {
            "counters": self.notification_counters.copy(),
            "subscribers_count": len(self.subscribers),
            "history_size": len(self.notification_history),
            "config": {
                "enabled": self.config.enabled,
                "quiet_hours": self.is_quiet_hours(),
                "quiet_hours_range": f"{self.config.quiet_hours_start:02d}:00 - {self.config.quiet_hours_end:02d}:00",
            },
        }

    async def send_price_alert(
        self,
        offer: Offer,
        old_price: float,
        new_price: float,
        recipients: Optional[Set[str]] = None,
    ) -> bool:
        """Envia alerta de mudança de preço"""
        if not self.config.price_alerts:
            return False

        # Criar hash único para esta notificação
        content_hash = f"price_alert_{offer.url}_{old_price}_{new_price}"

        if not self._should_send_notification("price_alert", content_hash):
            return False

        try:
            self.message_builder.build_price_alert_message(offer, old_price, new_price)
            target_recipients = recipients or self.subscribers

            if not target_recipients:
                self.logger.warning("Nenhum destinatário para alerta de preço")
                return False

            # Aqui seria feita a integração com o bot para enviar as mensagens
            # Por enquanto, apenas registramos
            self._record_notification(
                "price_alert",
                content_hash,
                target_recipients,
                {
                    "offer_title": offer.title,
                    "old_price": old_price,
                    "new_price": new_price,
                    "price_change": new_price - old_price,
                },
            )

            self.logger.info(
                f"Alerta de preço enviado para {len(target_recipients)} destinatários"
            )
            return True

        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta de preço: {e}")
            return False

    async def send_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "info",
        recipients: Optional[Set[str]] = None,
    ) -> bool:
        """Envia alerta do sistema"""
        if not self.config.system_alerts:
            return False

        content_hash = f"system_alert_{alert_type}_{message[:50]}"

        if not self._should_send_notification("system_alert", content_hash):
            return False

        try:
            # Formatar mensagem baseada na severidade
            emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}.get(
                severity, "ℹ️"
            )

            f"""
{emoji} <b>ALERTA DO SISTEMA - {severity.upper()}</b>

🔍 <b>Tipo:</b> {alert_type}
📝 <b>Mensagem:</b> {message}
⏰ <b>Timestamp:</b> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
            """.strip()

            target_recipients = recipients or self.subscribers

            if not target_recipients:
                self.logger.warning("Nenhum destinatário para alerta do sistema")
                return False

            # Aqui seria feita a integração com o bot para enviar as mensagens
            self._record_notification(
                "system_alert",
                content_hash,
                target_recipients,
                {"alert_type": alert_type, "severity": severity, "message": message},
            )

            self.logger.info(
                f"Alerta do sistema enviado para {len(target_recipients)} destinatários"
            )
            return True

        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta do sistema: {e}")
            return False

    async def send_offer_notification(
        self,
        offer: Offer,
        notification_type: str = "new_offer",
        recipients: Optional[Set[str]] = None,
    ) -> bool:
        """Envia notificação sobre oferta"""
        if not self.config.offer_notifications:
            return False

        content_hash = f"offer_{notification_type}_{offer.url}"

        if not self._should_send_notification("offer", content_hash):
            return False

        try:
            # Usar template específico da plataforma
            self.message_builder.build_offer_message(offer)

            # Adicionar cabeçalho baseado no tipo
            type_headers = {
                "new_offer": "🆕 <b>NOVA OFERTA ENCONTRADA!</b>",
                "price_drop": "📉 <b>QUEDA DE PREÇO!</b>",
                "back_in_stock": "📦 <b>PRODUTO DE VOLTA AO ESTOQUE!</b>",
                "limited_time": "⏰ <b>OFERTA POR TEMPO LIMITADO!</b>",
            }

            type_headers.get(notification_type, "🛒 <b>OFERTA DISPONÍVEL!</b>")

            target_recipients = recipients or self.subscribers

            if not target_recipients:
                self.logger.warning("Nenhum destinatário para notificação de oferta")
                return False

            # Aqui seria feita a integração com o bot para enviar as mensagens
            self._record_notification(
                "offer",
                content_hash,
                target_recipients,
                {
                    "offer_title": offer.title,
                    "notification_type": notification_type,
                    "platform": getattr(offer, "platform", "unknown"),
                },
            )

            self.logger.info(
                f"Notificação de oferta enviada para {len(target_recipients)} destinatários"
            )
            return True

        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação de oferta: {e}")
            return False

    async def send_error_notification(
        self, error: str, context: str = "", recipients: Optional[Set[str]] = None
    ) -> bool:
        """Envia notificação de erro"""
        if not self.config.error_notifications:
            return False

        content_hash = f"error_{context}_{error[:50]}"

        if not self._should_send_notification("error", content_hash):
            return False

        try:
            self.message_builder.build_error_message(error, context)
            target_recipients = recipients or self.subscribers

            if not target_recipients:
                self.logger.warning("Nenhum destinatário para notificação de erro")
                return False

            # Aqui seria feita a integração com o bot para enviar as mensagens
            self._record_notification(
                "error",
                content_hash,
                target_recipients,
                {"error": error, "context": context},
            )

            self.logger.info(
                f"Notificação de erro enviada para {len(target_recipients)} destinatários"
            )
            return True

        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação de erro: {e}")
            return False

    async def send_success_notification(
        self, action: str, details: str = "", recipients: Optional[Set[str]] = None
    ) -> bool:
        """Envia notificação de sucesso"""
        if not self.config.success_notifications:
            return False

        content_hash = f"success_{action}_{details[:50]}"

        if not self._should_send_notification("success", content_hash):
            return False

        try:
            self.message_builder.build_success_message(action, details)
            target_recipients = recipients or self.subscribers

            if not target_recipients:
                self.logger.warning("Nenhum destinatário para notificação de sucesso")
                return False

            # Aqui seria feita a integração com o bot para enviar as mensagens
            self._record_notification(
                "success",
                content_hash,
                target_recipients,
                {"action": action, "details": details},
            )

            self.logger.info(
                f"Notificação de sucesso enviada para {len(target_recipients)} destinatários"
            )
            return True

        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação de sucesso: {e}")
            return False

    async def broadcast_message(
        self, message: str, recipients: Optional[Set[str]] = None
    ) -> bool:
        """Envia mensagem para todos os assinantes"""
        try:
            target_recipients = recipients or self.subscribers

            if not target_recipients:
                self.logger.warning("Nenhum destinatário para broadcast")
                return False

            # Aqui seria feita a integração com o bot para enviar as mensagens
            self.logger.info(
                f"Broadcast enviado para {len(target_recipients)} destinatários"
            )
            return True

        except Exception as e:
            self.logger.error(f"Erro ao enviar broadcast: {e}")
            return False

    def cleanup(self):
        """Limpa recursos do NotificationManager"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

        self.logger.info("NotificationManager limpo")
