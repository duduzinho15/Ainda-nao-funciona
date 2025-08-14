"""
Script para testar a conexão com a API do Telegram e verificar se o bot está online.
"""
import os
import logging
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError, NetworkError
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot_connection_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Variável global para armazenar informações do bot
bot_info = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manipulador do comando /start."""
    user = update.effective_user
    logger.info(f"Comando /start recebido de {user.username} (ID: {user.id})")
    await update.message.reply_text(f'Olá {user.first_name}! Eu sou um bot de teste de conexão.')

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Repete a mensagem recebida."""
    user = update.effective_user
    text = update.message.text
    logger.info(f"Mensagem recebida de {user.username} (ID: {user.id}): {text}")
    await update.message.reply_text(f'Você disse: {text}')

async def test_bot_connection() -> None:
    """Testa a conexão com a API do Telegram e verifica se o bot está online."""
    # Carrega as variáveis de ambiente
    load_dotenv()
    
    # Obtém o token do bot
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Token do bot não encontrado. Verifique a variável de ambiente TELEGRAM_BOT_TOKEN.")
        return
    
    logger.info("Iniciando teste de conexão com a API do Telegram...")
    
    try:
        # Cria uma instância do bot
        bot = Bot(token=token)
        
        # Obtém informações do bot
        global bot_info
        bot_info = await bot.get_me()
        logger.info(f"Conexão bem-sucedida! Bot conectado como @{bot_info.username} (ID: {bot_info.id}, Nome: {bot_info.first_name})")
        
        # Verifica se o bot está online
        logger.info("Verificando se o bot está online...")
        try:
            updates = await bot.get_updates()
            logger.info(f"Número de atualizações pendentes: {len(updates)}")
            
            # Se houver atualizações, verifica a mais recente
            if updates:
                last_update = updates[-1]
                logger.info(f"Última atualização (ID: {last_update.update_id}) recebida em {last_update.message.date}")
        except Exception as e:
            logger.error(f"Erro ao verificar atualizações: {e}")
        
        # Cria uma aplicação para testar o polling
        logger.info("Criando aplicação para teste de polling...")
        application = Application.builder().token(token).build()
        
        # Adiciona os manipuladores de comandos
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        # Inicia o polling
        logger.info("Iniciando polling...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        logger.info("Polling iniciado com sucesso! O bot deve estar respondendo a comandos no Telegram.")
        logger.info("Pressione Ctrl+C para encerrar o teste.")
        
        # Mantém o script em execução
        while True:
            await asyncio.sleep(1)
            
    except NetworkError as e:
        logger.error(f"Erro de rede ao conectar ao Telegram: {e}")
    except TelegramError as e:
        logger.error(f"Erro na API do Telegram: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}", exc_info=True)
    finally:
        # Encerra a aplicação corretamente
        if 'application' in locals() and application.running:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(test_bot_connection())
    except KeyboardInterrupt:
        logger.info("Teste de conexão encerrado pelo usuário.")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}", exc_info=True)
