"""
Script de teste para o bot do Telegram
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Configuração básica de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem quando o comando /start é acionado."""
    await update.message.reply_text('Olá! Eu sou o Garimpeiro Geek. Estou funcionando corretamente!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem quando o comando /help é acionado."""
    await update.message.reply_text('Comandos disponíveis:\n/start - Inicia o bot\n/help - Mostra esta mensagem')

def main() -> None:
    """Inicia o bot."""
    # Obtém o token do bot a partir das variáveis de ambiente
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Token do bot não encontrado. Verifique a variável de ambiente TELEGRAM_BOT_TOKEN.")
        return

    # Cria a aplicação
    application = Application.builder().token(token).build()

    # Adiciona os manipuladores de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Inicia o bot
    logger.info("Bot iniciado. Pressione Ctrl+C para encerrar.")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
