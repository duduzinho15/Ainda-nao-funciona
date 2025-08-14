"""
Bot de eco simples para testar a conexão com a API do Telegram.
Responde a mensagens com o mesmo texto recebido.
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('echo_bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Função de callback para o comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem quando o comando /start é acionado."""
    user = update.effective_user
    logger.info(f"Comando /start recebido de {user.username} (ID: {user.id})")
    await update.message.reply_text(f'Olá {user.first_name}! Eu sou um bot de eco. Envie-me uma mensagem e eu a repetirei para você.')

# Função de callback para mensagens de texto
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Repete a mensagem recebida."""
    user = update.effective_user
    text = update.message.text
    logger.info(f"Mensagem recebida de {user.username} (ID: {user.id}): {text}")
    await update.message.reply_text(f'Você disse: {text}')

# Função principal
def main() -> None:
    """Inicia o bot."""
    # Obtém o token do bot a partir das variáveis de ambiente
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Token do bot não encontrado. Verifique a variável de ambiente TELEGRAM_BOT_TOKEN.")
        return

    logger.info("Iniciando o bot de eco...")
    
    try:
        # Cria a aplicação
        application = Application.builder().token(token).build()
        logger.info("Aplicação do bot criada com sucesso!")
        
        # Adiciona os manipuladores de comandos
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        # Inicia o bot
        logger.info("Iniciando o bot...")
        application.run_polling(drop_pending_updates=True)
        logger.info("Bot em execução. Pressione Ctrl+C para encerrar.")
        
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {e}", exc_info=True)

if __name__ == "__main__":
    main()
