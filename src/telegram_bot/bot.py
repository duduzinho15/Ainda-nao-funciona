"""
Bot Telegram principal do Garimpeiro Geek
"""

import logging
from typing import Any, Dict, Optional

try:
    from telegram import Update
    from telegram.ext import (
        Application,
        CallbackQueryHandler,
        CommandHandler,
        ContextTypes,
    )

    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logging.warning("python-telegram-bot não disponível. Bot Telegram desabilitado.")

    # Criar classes dummy para evitar erros de importação
    class Update:
        pass

    class Application:
        pass

    class CallbackQueryHandler:
        pass

    class CommandHandler:
        pass

    class ContextTypes:
        class DEFAULT_TYPE:
            pass


from .message_builder import MessageBuilder
from .notification_manager import NotificationManager


class TelegramBot:
    """Bot Telegram para notificações e interação"""

    def __init__(self, token: str, chat_id: Optional[str] = None):
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot não está instalado")

        self.token = token
        self.chat_id = chat_id
        self.application = None
        self.message_builder = MessageBuilder()
        self.notification_manager = NotificationManager()
        self.logger = logging.getLogger("telegram.bot")

        # Comandos disponíveis
        self.commands = {
            "start": "Iniciar o bot",
            "help": "Mostrar ajuda",
            "status": "Status do sistema",
            "ofertas": "Buscar ofertas",
            "config": "Configurações",
            "stats": "Estatísticas",
        }

        # Usuários autorizados
        self.authorized_users = set()
        if chat_id:
            self.authorized_users.add(chat_id)

    async def start(self):
        """Inicia o bot"""
        try:
            self.application = Application.builder().token(self.token).build()

            # Adicionar handlers
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("help", self.cmd_help))
            self.application.add_handler(CommandHandler("status", self.cmd_status))
            self.application.add_handler(CommandHandler("ofertas", self.cmd_ofertas))
            self.application.add_handler(CommandHandler("config", self.cmd_config))
            self.application.add_handler(CommandHandler("stats", self.cmd_stats))

            # Handler para botões inline
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))

            # Iniciar bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()

            self.logger.info("Bot Telegram iniciado com sucesso")

        except Exception as e:
            self.logger.error(f"Erro ao iniciar bot: {e}")
            raise

    async def stop(self):
        """Para o bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self.logger.info("Bot Telegram parado")

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user_id = str(update.effective_user.id)

        if user_id not in self.authorized_users:
            await update.message.reply_text(
                "❌ Acesso negado. Você não está autorizado a usar este bot."
            )
            return

        welcome_message = self.message_builder.build_welcome_message()
        await update.message.reply_text(welcome_message, parse_mode="HTML")

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        user_id = str(update.effective_user.id)

        if user_id not in self.authorized_users:
            return

        help_text = self.message_builder.build_help_message(self.commands)
        await update.message.reply_text(help_text, parse_mode="HTML")

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /status"""
        user_id = str(update.effective_user.id)

        if user_id not in self.authorized_users:
            return

        status_message = self.message_builder.build_status_message()
        await update.message.reply_text(status_message, parse_mode="HTML")

    async def cmd_ofertas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /ofertas"""
        user_id = str(update.effective_user.id)

        if user_id not in self.authorized_users:
            return

        # Buscar ofertas (implementar lógica)
        offers = []  # Placeholder

        if offers:
            message = self.message_builder.build_offers_message(offers)
            keyboard = self.message_builder.build_offers_keyboard(offers)
            await update.message.reply_text(
                message, parse_mode="HTML", reply_markup=keyboard
            )
        else:
            await update.message.reply_text("🔍 Nenhuma oferta encontrada no momento.")

    async def cmd_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /config"""
        user_id = str(update.effective_user.id)

        if user_id not in self.authorized_users:
            return

        config_message = self.message_builder.build_config_message()
        keyboard = self.message_builder.build_config_keyboard()
        await update.message.reply_text(
            config_message, parse_mode="HTML", reply_markup=keyboard
        )

    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /stats"""
        user_id = str(update.effective_user.id)

        if user_id not in self.authorized_users:
            return

        stats_message = self.message_builder.build_stats_message()
        await update.message.reply_text(stats_message, parse_mode="HTML")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Trata callbacks de botões inline"""
        query = update.callback_query
        await query.answer()

        user_id = str(query.from_user.id)
        if user_id not in self.authorized_users:
            return

        data = query.data
        self.logger.info(f"Callback recebido: {data}")

        # Processar callback baseado no tipo
        if data.startswith("offer_"):
            await self.handle_offer_callback(query, data)
        elif data.startswith("config_"):
            await self.handle_config_callback(query, data)
        else:
            await query.edit_message_text("❌ Ação não reconhecida")

    async def handle_offer_callback(self, query, data: str):
        """Trata callbacks relacionados a ofertas"""
        try:
            offer_id = data.split("_")[1]
            # Implementar lógica para mostrar detalhes da oferta
            await query.edit_message_text(f"📋 Detalhes da oferta {offer_id}")
        except Exception as e:
            self.logger.error(f"Erro ao processar callback de oferta: {e}")
            await query.edit_message_text("❌ Erro ao processar oferta")

    async def handle_config_callback(self, query, data: str):
        """Trata callbacks relacionados a configurações"""
        try:
            action = data.split("_")[1]
            # Implementar lógica para alterar configurações
            await query.edit_message_text(f"⚙️ Configuração alterada: {action}")
        except Exception as e:
            self.logger.error(f"Erro ao processar callback de configuração: {e}")
            await query.edit_message_text("❌ Erro ao alterar configuração")

    async def send_notification(self, message: str, chat_id: Optional[str] = None):
        """Envia notificação para um chat específico"""
        target_chat = chat_id or self.chat_id

        if not target_chat:
            self.logger.warning("Nenhum chat_id configurado para notificação")
            return

        try:
            if self.application:
                await self.application.bot.send_message(
                    chat_id=target_chat, text=message, parse_mode="HTML"
                )
                self.logger.info(f"Notificação enviada para {target_chat}")
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação: {e}")

    async def broadcast_message(self, message: str, exclude_chat: Optional[str] = None):
        """Envia mensagem para todos os usuários autorizados"""
        for user_id in self.authorized_users:
            if user_id != exclude_chat:
                await self.send_notification(message, user_id)

    def add_authorized_user(self, user_id: str):
        """Adiciona usuário autorizado"""
        self.authorized_users.add(user_id)
        self.logger.info(f"Usuário {user_id} autorizado")

    def remove_authorized_user(self, user_id: str):
        """Remove usuário autorizado"""
        self.authorized_users.discard(user_id)
        self.logger.info(f"Usuário {user_id} removido")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do bot"""
        return {
            "authorized_users": len(self.authorized_users),
            "commands_available": len(self.commands),
            "bot_running": bool(self.application),
            "token_configured": bool(self.token),
            "chat_id_configured": bool(self.chat_id),
        }
