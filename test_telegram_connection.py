"""
Script para testar a conexão com a API do Telegram.
"""
import os
import asyncio
import logging
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('telegram_connection_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

async def test_telegram_connection() -> None:
    """Testa a conexão com a API do Telegram."""
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
        me = await bot.get_me()
        logger.info(f"Conexão bem-sucedida! Bot conectado como @{me.username} (ID: {me.id}, Nome: {me.first_name})")
        
        # Verifica se o bot está online
        logger.info("Verificando se o bot está online...")
        updates = await bot.get_updates()
        logger.info(f"Número de atualizações pendentes: {len(updates)}")
        
        # Se houver atualizações, mostra a mais recente
        if updates:
            last_update = updates[-1]
            logger.info(f"Última atualização (ID: {last_update.update_id}) recebida em {last_update.message.date}")
        
    except TelegramError as e:
        logger.error(f"Erro na conexão com a API do Telegram: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_telegram_connection())
