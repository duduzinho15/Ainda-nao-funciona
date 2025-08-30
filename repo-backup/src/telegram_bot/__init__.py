"""
Módulo do Bot Telegram do Garimpeiro Geek
Sistema de notificações e interação via Telegram
"""

__version__ = "2.0.0"
__author__ = "Eduardo Vitorino"

from .bot import TelegramBot
from .message_builder import MessageBuilder
from .notification_manager import NotificationManager

__all__ = ["TelegramBot", "MessageBuilder", "NotificationManager"]
