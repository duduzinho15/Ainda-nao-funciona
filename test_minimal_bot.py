"""
Script mínimo para testar a conexão com a API do Telegram.
"""
import os
import logging
import asyncio
from telegram import Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('minimal_bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Função para lidar com o comando /start
async def start(update, context):
    logger.info(f"Comando /start recebido de {update.effective_user.first_name} (ID: {update.effective_user.id})")
    await update.message.reply_text('Olá! Eu sou um bot de teste. Recebi seu comando /start!')

# Função para lidar com mensagens de texto
async def echo(update, context):
    logger.info(f"Mensagem recebida de {update.effective_user.first_name}: {update.message.text}")
    await update.message.reply_text(f'Você disse: {update.message.text}')

# Função principal
async def main():
    # Carrega as variáveis de ambiente
    load_dotenv()
    
    # Obtém o token do bot
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Token do bot não encontrado. Verifique a variável de ambiente TELEGRAM_BOT_TOKEN.")
        return
    
    # Cria a aplicação
    logger.info("Criando aplicação do bot...")
    application = Application.builder().token(token).build()
    
    # Adiciona os handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Inicia o bot
    logger.info("Iniciando o bot...")
    await application.initialize()
    await application.start()
    await application.bot.set_my_commands([
        ("start", "Inicia o bot"),
        ("help", "Mostra ajuda")
    ])
    
    # Obtém informações do bot
    me = await application.bot.get_me()
    logger.info(f"Bot iniciado como @{me.username} (ID: {me.id}, Nome: {me.first_name})")
    logger.info("Pressione Ctrl+C para encerrar o bot.")
    
    # Mantém o bot em execução
    try:
        await application.run_polling()
    except Exception as e:
        logger.error(f"Erro ao executar o bot: {e}", exc_info=True)
    finally:
        await application.stop()
        await application.shutdown()
        logger.info("Bot encerrado.")

if __name__ == "__main__":
    asyncio.run(main())
