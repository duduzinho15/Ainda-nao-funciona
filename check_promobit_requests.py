"""
Script para verificar a estrutura do site Promobit usando a biblioteca requests.
"""
import requests
import logging
import time
from bs4 import BeautifulSoup
import json

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('promobit_check_requests.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('promobit_check_requests')

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

def fetch_page(url, headers=None, timeout=30):
    """Faz a requisição HTTP e retorna o conteúdo da página."""
    try:
        logger.info(f"\nFazendo requisição para: {url}")
        logger.debug(f"Headers: {json.dumps(headers, indent=2) if headers else 'Nenhum'}")
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        logger.info(f"Status da resposta: {response.status_code}")
        logger.debug(f"Headers da resposta: {json.dumps(dict(response.headers), indent=2)}")
        
        # Verifica se a resposta foi bem-sucedida
        response.raise_for_status()
        
        logger.info(f"Tamanho do conteúdo: {len(response.content)} bytes")
        logger.info(f"Tipo de conteúdo: {response.headers.get('Content-Type', 'Desconhecido')}")
        
        # Verifica se é um redirecionamento
        if response.history:
            logger.warning(f"Redirecionado de: {response.history[0].url} para {response.url}")
        
        # Salva a resposta para análise
        filename = f"response_{int(time.time())}.html"
        save_response(response, filename)
        
        # Verifica se há indicações de bloqueio (CAPTCHA, Cloudflare, etc.)
        text = response.text.lower()
        if any(term in text for term in ['captcha', 'cloudflare', 'ddos', 'access denied', 'forbidden']):
            logger.warning("Possível bloqueio detectado na página!")
        
        return response.text
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao buscar a página: {e}", exc_info=True)
        return None

def check_elements(soup, page_name):
    """Verifica a presença de elementos-chave na página."""
    logger.info(f"\nAnalisando elementos em: {page_name}")
    
    # Verifica título da página
    title = soup.find('title')
    logger.info(f"Título da página: {title.text if title else 'Não encontrado'}")
    
    # Verifica se há um formulário de login/cadastro
    login_form = soup.find('form', {'id': 'login-form'}) or soup.find('form', {'id': 'signup-form'})
    if login_form:
        logger.info("Formulário de login/cadastro encontrado")
    
    # Verifica se há um CAPTCHA
    captcha = soup.find('div', {'class': 'g-recaptcha'}) or soup.find('div', {'class': 'captcha'})
    if captcha:
        logger.warning("CAPTCHA detectado na página!")
    
    # Verifica se há mensagens de bloqueio
    block_messages = soup.find_all(text=[
        'Access Denied', 'Forbidden', 'Bot detected', 'DDOS protection',
        'Acesso negado', 'Bloqueado', 'Proteção contra bots'
    ], recursive=True)
    
    if block_messages:
        logger.warning(f"Mensagens de bloqueio encontradas: {len(block_messages)}")
        for i, msg in enumerate(block_messages[:3], 1):  # Mostra apenas as 3 primeiras mensagens
            logger.warning(f"  {i}. {msg.strip() if msg.strip() else '[conteúdo vazio]'}")
    
    # Verifica se há ofertas na página
    check_offer_selectors(soup)
    
    # Verifica se há scripts de terceiros
    check_third_party_scripts(soup)

def check_offer_selectors(soup):
    """Verifica se há ofertas na página usando vários seletores."""
    logger.info("\nVerificando seletores de ofertas...")
    
    # Lista de seletores para tentar
    selectors = [
        'article[data-testid="offer-card"]',
        '.offer-card',
        '.offerCard',
        '.offer',
        '.product-card',
        '.productCard',
        '.product',
        '.item',
        '.ofertas-list article',
        '.ofertas-list .item',
        '.ofertas-container article',
        '.ofertas-container .item',
        '.list-offers article',
        '.list-offers .item',
        '.offers-list article',
        '.offers-list .item',
        '.promotion-card',
        '.promotionCard',
        '.promo-card',
        '.promoCard',
        '.oferta',
        '.ofertas',
        '.produto',
        '.produtos',
        '.product-list article',
        '.product-list .item',
        '.product-grid article',
        '.product-grid .item',
        '.grid-offers article',
        '.grid-offers .item',
        '.grid-ofertas article',
        '.grid-ofertas .item',
        '.list-products article',
        '.list-products .item',
        '.list-produtos article',
        '.list-produtos .item',
        '.box-oferta',
        '.box-ofertas',
        '.box-produto',
        '.box-produtos',
        '.card-oferta',
        '.card-ofertas',
        '.card-produto',
        '.card-produtos',
        '.offer-item',
        '.offerItem',
        '.product-item',
        '.productItem',
        '.item-oferta',
        '.item-produto',
    ]
    
    found = False
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            logger.info(f"Encontrados {len(elements)} elementos com o seletor: '{selector}'")
            if not found:  # Mostra um exemplo apenas para o primeiro seletor que encontrar
                logger.debug(f"Exemplo de elemento com o seletor '{selector}': {str(elements[0])[:200]}...")
                found = True
        
    if not found:
        logger.warning("Nenhum dos seletores de oferta retornou resultados")

def check_third_party_scripts(soup):
    """Verifica a presença de scripts de terceiros."""
    scripts = soup.find_all('script', src=True)
    third_party_scripts = [s for s in scripts if any(domain in s['src'] for domain in [
        'cloudflare', 'recaptcha', 'google-analytics', 'googletagmanager', 'doubleclick',
        'facebook', 'twitter', 'linkedin', 'pinterest', 'addthis', 'hotjar', 'optimizely'
    ])]
    
    if third_party_scripts:
        logger.info(f"\nScripts de terceiros encontrados: {len(third_party_scripts)}")
        for script in third_party_scripts[:5]:  # Mostra apenas os 5 primeiros
            logger.info(f"  - {script['src']}")
    else:
        logger.info("\nNenhum script de terceiros encontrado")

def main():
    """Função principal."""
    logger.info("=== Iniciando verificação do site Promobit ===")
    
    # Cria uma sessão para manter os cookies
    session = requests.Session()
    
    try:
        # Primeiro, tenta acessar a página inicial
        logger.info("\n=== Verificando acesso à página inicial ===")
        home_page = fetch_page(BASE_URL, HEADERS)
        
        if home_page:
            # Verifica se há elementos esperados na página inicial
            soup = BeautifulSoup(home_page, 'html.parser')
            check_elements(soup, "Página inicial")
        
        # Pequena pausa entre as requisições
        time.sleep(2)
        
        # Em seguida, tenta acessar a categoria de informática
        logger.info("\n=== Verificando acesso à categoria de informática ===")
        category_page = fetch_page(CATEGORY_URL, HEADERS)
        
        if category_page:
            # Verifica se há elementos esperados na página da categoria
            soup = BeautifulSoup(category_page, 'html.parser')
            check_elements(soup, "Página de categoria")
        
        logger.info("\n=== Verificação concluída com sucesso ===")
        
    except Exception as e:
        logger.critical(f"Erro durante a verificação: {e}", exc_info=True)
        print(f"\nERRO: A verificação falhou. Consulte o arquivo de log 'promobit_check_requests.log' para mais detalhes.")
        return 1
    finally:
        # Fecha a sessão
        session.close()
    
    return 0

if __name__ == "__main__":
    exit(main())
