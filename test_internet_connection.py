"""
Script para testar a conectividade com a internet e com a API do Telegram.
"""
import socket
import requests
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """
    Testa a conectividade com a internet tentando se conectar ao DNS do Google.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        logger.info("✅ Conectividade com a internet: OK")
        return True
    except socket.error as ex:
        logger.error(f"❌ Sem conectividade com a internet: {ex}")
        return False

def test_telegram_api():
    """
    Testa a conectividade com a API do Telegram.
    """
    try:
        # URL da API pública do Telegram para obter informações sobre o Bot API
        url = "https://api.telegram.org/bot8478680741:AAHguaQAL1bTDTqr3AQke1BqAqLeiv1TXnQ/getMe"
        
        logger.info(f"Testando conexão com a API do Telegram...")
        logger.info(f"URL: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                logger.info("✅ Conexão com a API do Telegram: OK")
                logger.info(f"🤖 Nome do bot: {data['result'].get('first_name')}")
                logger.info(f"👤 Usuário: @{data['result'].get('username')}")
                logger.info(f"🆔 ID: {data['result'].get('id')}")
                return True
            else:
                logger.error(f"❌ Erro na resposta da API: {data}")
        else:
            logger.error(f"❌ Erro na requisição: {response.status_code} - {response.text}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Falha na conexão com a API do Telegram: {e}")
    
    return False

def main():
    """Função principal."""
    print("\n=== Teste de Conectividade ===\n")
    
    # Testa a conectividade com a internet
    internet_ok = test_internet_connection()
    
    # Se houver conectividade com a internet, testa a API do Telegram
    if internet_ok:
        telegram_ok = test_telegram_api()
        
        if telegram_ok:
            print("\n✅ Testes concluídos com sucesso! O bot deve estar funcionando corretamente.")
        else:
            print("\n❌ Não foi possível conectar à API do Telegram. Verifique o token do bot e sua conexão com a internet.")
    else:
        print("\n❌ Sem conectividade com a internet. Verifique sua conexão de rede.")

if __name__ == "__main__":
    main()
