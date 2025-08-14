"""
Script para testar a conexão com a API do Telegram de forma detalhada.
Inclui verificação de webhook, informações detalhadas do bot e listagem de comandos.
"""
import os
import logging
import asyncio
import aiohttp
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('telegram_connection_test_v4.log')
    ]
)
logger = logging.getLogger(__name__)

# Variável global para armazenar o ID do chat
CHAT_ID = None

async def check_webhook(bot_token: str) -> None:
    """Verifica se há webhooks configurados no bot."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f'https://api.telegram.org/bot{bot_token}/getWebhookInfo'
            async with session.get(url) as response:
                data = await response.json()
                logger.info("\n=== INFORMAÇÕES DO WEBHOOK ===")
                logger.info(f"URL do Webhook: {data.get('result', {}).get('url', 'Nenhum webhook configurado')}")
                logger.info(f"Tem certificado pendente: {data.get('result', {}).get('has_custom_certificate', False)}")
                logger.info(f"Número de atualizações pendentes: {data.get('result', {}).get('pending_update_count', 0)}")
                
                if data.get('result', {}).get('url'):
                    logger.warning("\nATENÇÃO: Há um webhook configurado. Isso pode estar interferindo no modo polling.")
                    logger.warning("Para usar o modo polling, remova o webhook com o comando a seguir:")
                    logger.warning(f'curl -X GET "https://api.telegram.org/bot{bot_token}/deleteWebhook"')
    except Exception as e:
        logger.error(f"Erro ao verificar webhook: {e}", exc_info=True)

async def get_bot_commands(bot_token: str) -> None:
    """Obtém os comandos configurados para o bot."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f'https://api.telegram.org/bot{bot_token}/getMyCommands'
            async with session.get(url) as response:
                data = await response.json()
                logger.info("\n=== COMANDOS DO BOT ===")
                if data.get('result'):
                    for cmd in data['result']:
                        logger.info(f"/{cmd['command']} - {cmd.get('description', 'Sem descrição')}")
                else:
                    logger.info("Nenhum comando configurado para o bot.")
    except Exception as e:
        logger.error(f"Erro ao obter comandos do bot: {e}", exc_info=True)

async def get_updates(bot_token: str) -> None:
    """Obtém as atualizações recentes do bot."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f'https://api.telegram.org/bot{bot_token}/getUpdates'
            async with session.get(url) as response:
                data = await response.json()
                logger.info("\n=== ATUALIZAÇÕES RECENTES ===")
                if data.get('result'):
                    for update in data['result'][-3:]:  # Mostra as 3 atualizações mais recentes
                        logger.info(f"Update ID: {update.get('update_id')}")
                        if 'message' in update:
                            msg = update['message']
                            logger.info(f"  Mensagem de {msg.get('from', {}).get('first_name', 'N/A')} (@{msg.get('from', {}).get('username', 'N/A')}): {msg.get('text', 'Sem texto')}")
                            if 'chat' in msg:
                                logger.info(f"  Chat ID: {msg['chat'].get('id')} (Tipo: {msg['chat'].get('type')})")
                else:
                    logger.info("Nenhuma atualização recente.")
    except Exception as e:
        logger.error(f"Erro ao obter atualizações: {e}", exc_info=True)

async def test_telegram_connection() -> None:
    """Testa a conexão com a API do Telegram de forma assíncrona."""
    # Carrega as variáveis de ambiente
    load_dotenv()
    
    # Obtém o token do bot
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Token do bot não encontrado. Verifique a variável de ambiente TELEGRAM_BOT_TOKEN.")
        return
    
    logger.info("=== INICIANDO TESTE DE CONEXÃO COM A API DO TELEGRAM ===")
    
    try:
        # Cria uma instância do bot
        logger.info("\nCriando instância do bot...")
        bot = Bot(token=token)
        
        # Obtém informações do bot
        logger.info("\nObtendo informações do bot...")
        me = await bot.get_me()
        logger.info(f"Conexão bem-sucedida! Bot conectado como @{me.username} (ID: {me.id}, Nome: {me.first_name})")
        
        # Verifica webhooks configurados
        logger.info("\nVerificando webhooks configurados...")
        await check_webhook(token)
        
        # Obtém comandos do bot
        await get_bot_commands(token)
        
        # Obtém atualizações recentes
        logger.info("\nObtendo atualizações recentes...")
        await get_updates(token)
        
        # Envia uma mensagem de teste se o chat_id estiver configurado
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if chat_id:
            try:
                logger.info(f"\nEnviando mensagem de teste para o chat ID: {chat_id}...")
                await bot.send_message(chat_id=chat_id, text="Teste de conexão bem-sucedido!")
                logger.info("Mensagem de teste enviada com sucesso!")
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem de teste: {e}", exc_info=True)
        else:
            logger.warning("\nTELEGRAM_CHAT_ID não definido. Pulando envio de mensagem de teste.")
        
        logger.info("\n=== TESTE DE CONEXÃO CONCLUÍDO COM SUCESSO ===")
        
    except TelegramError as e:
        logger.error(f"Erro na conexão com a API do Telegram: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Erro inesperado: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_telegram_connection())
