"""
Script simples para verificar a resposta do site Promobit.
"""
import requests
import logging
import time
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('promobit_check_simple.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('promobit_check_simple')

# URL base do Promobit
BASE_URL = "https://www.promobit.com.br"
CATEGORY_URL = f"{BASE_URL}/ofertas/1?categoria=informatica"

# Headers para simular um navegador
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

def save_response(response, filename):
    """Salva a resposta em um arquivo."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info(f"Resposta salva em '{filename}'")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar resposta em '{filename}': {e}")
        return False

def check_url(url, name):
    """Verifica uma URL e retorna informações sobre a resposta."""
    logger.info(f"\n=== Verificando {name} ===")
    logger.info(f"URL: {url}")
    
    try:
        # Faz a requisição
        start_time = time.time()
        response = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        elapsed_time = time.time() - start_time
        
        # Log de informações básicas
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Tempo de resposta: {elapsed_time:.2f} segundos")
        logger.info(f"Tamanho da resposta: {len(response.content)} bytes")
        logger.info(f"Tipo de conteúdo: {response.headers.get('Content-Type', 'Desconhecido')}")
        
        # Verifica redirecionamentos
        if response.history:
            logger.warning(f"Redirecionado {len(response.history)} vezes")
            for i, resp in enumerate(response.history, 1):
                logger.warning(f"  {i}. {resp.status_code} {resp.url}")
        
        # Salva a resposta em um arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"response_{name.lower().replace(' ', '_')}_{timestamp}.html"
        save_response(response, filename)
        
        # Verifica se há indícios de bloqueio
        text = response.text.lower()
        block_indicators = [
            'captcha', 'cloudflare', 'ddos', 'access denied', 'forbidden',
            'acesso negado', 'bloqueado', 'proteção', 'bot detected'
        ]
        
        for indicator in block_indicators:
            if indicator in text:
                logger.warning(f"Possível bloqueio detectado: '{indicator}'")
        
        return response
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao acessar a URL: {e}")
        return None

def main():
    """Função principal."""
    logger.info("=== Iniciando verificação do site Promobit ===")
    
    # Verifica a página inicial
    home_response = check_url(BASE_URL, "Página Inicial")
    
    # Pequena pausa entre as requisições
    time.sleep(2)
    
    # Verifica a página de categoria
    category_response = check_url(CATEGORY_URL, "Categoria Informática")
    
    logger.info("\n=== Verificação concluída ===")
    
    # Exibe um resumo
    if home_response and category_response:
        logger.info("Ambas as páginas foram verificadas com sucesso!")
    elif home_response or category_response:
        logger.warning("Apenas uma das páginas foi verificada com sucesso.")
    else:
        logger.error("Não foi possível verificar nenhuma das páginas.")
    
    return 0

if __name__ == "__main__":
    exit(main())
