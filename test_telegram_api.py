"""
Script para testar a conectividade com a API do Telegram.
"""
import os
import logging
import requests
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_telegram_connection():
    """Testa a conexão com a API do Telegram."""
    # Carrega as variáveis de ambiente
    load_dotenv()
    
    # Obtém o token do bot
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Token do bot não encontrado. Verifique a variável de ambiente TELEGRAM_BOT_TOKEN.")
        return False
    
    # URL da API do Telegram para obter informações do bot
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        logger.info(f"Testando conexão com a API do Telegram...")
        logger.info(f"URL da requisição: {url}")
        
        # Faz a requisição para a API do Telegram
        response = requests.get(url, timeout=10)
        
        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            data = response.json()
            if data.get('ok') and data.get('result'):
                bot_info = data['result']
                logger.info(f"✅ Conexão com a API do Telegram bem-sucedida!")
                logger.info(f"🤖 Nome do bot: {bot_info.get('first_name')}")
                logger.info(f"👤 Nome de usuário: @{bot_info.get('username')}")
                logger.info(f"🆔 ID do bot: {bot_info.get('id')}")
                return True
            else:
                logger.error(f"❌ Erro na resposta da API: {data}")
        else:
            logger.error(f"❌ Erro na requisição: {response.status_code} - {response.text}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro na conexão com a API do Telegram: {e}")
    
    return False

if __name__ == "__main__":
    test_telegram_connection()
