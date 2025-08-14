"""
Script de teste mínimo para verificar a funcionalidade básica do bot do Telegram.
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração básica de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('minimal_bot_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Função de callback para o comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem quando o comando /start é acionado."""
    logger.info(f"Comando /start recebido de {update.effective_user.username}")
    await update.message.reply_text('Olá! Eu sou um bot de teste mínimo. Estou funcionando corretamente!')

# Função principal
def main() -> None:
    """Inicia o bot."""
    # Obtém o token do bot a partir das variáveis de ambiente
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Token do bot não encontrado. Verifique a variável de ambiente TELEGRAM_BOT_TOKEN.")
        return

    logger.info("Criando a aplicação do bot...")
    
    try:
        # Cria a aplicação
        application = Application.builder().token(token).build()
        logger.info("Aplicação do bot criada com sucesso!")
        
        # Adiciona o manipulador de comandos
        application.add_handler(CommandHandler("start", start))
        
        # Inicia o bot
        logger.info("Iniciando o bot...")
        application.run_polling(drop_pending_updates=True)
        logger.info("Bot em execução. Pressione Ctrl+C para encerrar.")
        
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {e}", exc_info=True)

if __name__ == "__main__":
    main()
