"""
Script extremamente simples para testar a conexão com a API do Telegram.
"""
import os
import logging
import asyncio
import aiohttp
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('telegram_test_v5.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_telegram_connection():
    """Testa a conexão com a API do Telegram."""
    # Carrega as variáveis de ambiente
    load_dotenv()
    
    # Obtém o token do bot
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Token do bot não encontrado. Verifique a variável de ambiente TELEGRAM_BOT_TOKEN.")
        return
    
    logger.info("=== INICIANDO TESTE DE CONEXÃO SIMPLES COM A API DO TELEGRAM ===")
    logger.info(f"Token: {token[:10]}...{token[-5:]}")
    
    # Testa a obtenção de informações do bot
    url = f'https://api.telegram.org/bot{token}/getMe'
    
    try:
        logger.info(f"Fazendo requisição para: {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                logger.info(f"Resposta da API: {data}")
                
                if data.get('ok'):
                    logger.info(f"Conexão bem-sucedida! Bot: @{data['result']['username']} (ID: {data['result']['id']})")
                    
                    # Testa o envio de uma mensagem
                    chat_id = os.getenv('TELEGRAM_CHAT_ID')
                    if chat_id:
                        logger.info(f"Enviando mensagem de teste para o chat ID: {chat_id}")
                        url_send = f'https://api.telegram.org/bot{token}/sendMessage'
                        payload = {
                            'chat_id': chat_id,
                            'text': 'Teste de conexão bem-sucedido!',
                            'parse_mode': 'HTML'
                        }
                        
                        async with session.post(url_send, json=payload) as send_response:
                            send_data = await send_response.json()
                            logger.info(f"Resposta do envio de mensagem: {send_data}")
                            if send_data.get('ok'):
                                logger.info("Mensagem de teste enviada com sucesso!")
                            else:
                                logger.error(f"Erro ao enviar mensagem: {send_data}")
                    else:
                        logger.warning("TELEGRAM_CHAT_ID não definido. Pulando envio de mensagem de teste.")
                else:
                    logger.error(f"Erro na resposta da API: {data}")
    
    except Exception as e:
        logger.error(f"Erro ao conectar à API do Telegram: {e}", exc_info=True)
    
    logger.info("=== TESTE DE CONEXÃO CONCLUÍDO ===")

if __name__ == "__main__":
    asyncio.run(test_telegram_connection())
