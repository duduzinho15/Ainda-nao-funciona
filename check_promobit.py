"""
Script para verificar a estrutura do site Promobit e identificar possíveis bloqueios anti-bot.
"""
import aiohttp
import asyncio
import logging
import os
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('promobit_check.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('promobit_check')

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

async def fetch_page(session, url, headers):
    """Faz a requisição HTTP e retorna o conteúdo da página."""
    try:
        logger.info(f"Fazendo requisição para: {url}")
        logger.debug(f"Headers: {headers}")
        
        async with session.get(url, headers=headers, timeout=30) as response:
            logger.info(f"Status da resposta: {response.status}")
            logger.debug(f"Headers da resposta: {dict(response.headers)}")
            
            # Verifica se a resposta foi bem-sucedida
            response.raise_for_status()
            
            # Lê o conteúdo da resposta
            content = await response.read()
            logger.info(f"Tamanho do conteúdo: {len(content)} bytes")
            
            # Verifica o tipo de conteúdo
            content_type = response.headers.get('Content-Type', '').lower()
            logger.info(f"Tipo de conteúdo: {content_type}")
            
            # Verifica se é um redirecionamento
            if response.status in (301, 302, 303, 307, 308):
                location = response.headers.get('Location', '')
                logger.warning(f"Redirecionado para: {location}")
            
            # Tenta decodificar o conteúdo como texto
            try:
                text = content.decode('utf-8', errors='replace')
                logger.debug(f"Primeiros 500 caracteres do HTML: {text[:500]}")
                
                # Verifica se há indicações de bloqueio (CAPTCHA, Cloudflare, etc.)
                if any(term in text.lower() for term in ['captcha', 'cloudflare', 'ddos', 'access denied', 'forbidden']):
                    logger.warning("Possível bloqueio detectado na página!")
                
                return text
                
            except UnicodeDecodeError:
                logger.error("Não foi possível decodificar o conteúdo como texto UTF-8")
                return None
                
    except Exception as e:
        logger.error(f"Erro ao buscar a página: {e}", exc_info=True)
        return None

async def check_promobit():
    """Verifica a estrutura do site Promobit."""
    try:
        # Configuração da sessão
        timeout = aiohttp.ClientTimeout(total=60)  # Aumentando o timeout para 60 segundos
        connector = aiohttp.TCPConnector(force_close=True, enable_cleanup_closed=True)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Primeiro, tenta acessar a página inicial
            logger.info("\n=== Verificando acesso à página inicial ===")
            try:
                home_page = await fetch_page(session, BASE_URL, HEADERS)
                
                if home_page:
                    # Salva o HTML da página inicial
                    with open('promobit_home.html', 'w', encoding='utf-8') as f:
                        f.write(home_page)
                    logger.info("Página inicial salva em 'promobit_home.html'")
                    
                    # Verifica se há elementos esperados na página inicial
                    soup = BeautifulSoup(home_page, 'html.parser')
                    check_elements(soup, "Página inicial")
                else:
                    logger.warning("Não foi possível obter a página inicial")
                    
            except Exception as e:
                logger.error(f"Erro ao acessar a página inicial: {e}", exc_info=True)
            
            # Pequena pausa entre as requisições
            await asyncio.sleep(2)
            
            # Em seguida, tenta acessar a categoria de informática
            logger.info("\n=== Verificando acesso à categoria de informática ===")
            try:
                category_page = await fetch_page(session, CATEGORY_URL, HEADERS)
                
                if category_page:
                    # Salva o HTML da categoria
                    with open('promobit_category.html', 'w', encoding='utf-8') as f:
                        f.write(category_page)
                    logger.info("Página de categoria salva em 'promobit_category.html'")
                    
                    # Verifica se há elementos esperados na página da categoria
                    soup = BeautifulSoup(category_page, 'html.parser')
                    check_elements(soup, "Página de categoria")
                else:
                    logger.warning("Não foi possível obter a página de categoria")
                    
            except Exception as e:
                logger.error(f"Erro ao acessar a página de categoria: {e}", exc_info=True)
                
    except Exception as e:
        logger.critical(f"Erro crítico durante a verificação do site: {e}", exc_info=True)
        raise

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
    offers = soup.select('article[data-testid="offer-card"]')
    logger.info(f"Ofertas encontradas: {len(offers)}")
    
    # Se não encontrar ofertas, tenta outros seletores comuns
    if not offers:
        logger.warning("Nenhuma oferta encontrada com o seletor 'article[data-testid=\"offer-card\"]'")
        
        # Tenta outros seletores comuns
        alternative_selectors = [
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
        
        for selector in alternative_selectors:
            elements = soup.select(selector)
            if elements:
                logger.warning(f"Elementos encontrados com o seletor '{selector}': {len(elements)}")
                # Se encontrou elementos com este seletor, mostra um exemplo
                if elements:
                    logger.debug(f"Exemplo de conteúdo do primeiro elemento com o seletor '{selector}': {str(elements[0])[:200]}...")
                    break
        else:
            logger.warning("Nenhum dos seletores alternativos retornou resultados")
    else:
        # Se encontrou ofertas, mostra um exemplo
        logger.info(f"Exemplo de oferta: {str(offers[0])[:200]}...")
    
    # Verifica se há scripts de terceiros (como Cloudflare, Google reCAPTCHA, etc.)
    scripts = soup.find_all('script', src=True)
    third_party_scripts = [s for s in scripts if any(domain in s['src'] for domain in [
        'cloudflare', 'recaptcha', 'google-analytics', 'googletagmanager', 'doubleclick',
        'facebook', 'twitter', 'linkedin', 'pinterest', 'addthis', 'hotjar', 'optimizely'
    ])]
    
    if third_party_scripts:
        logger.info(f"Scripts de terceiros encontrados: {len(third_party_scripts)}")
        for script in third_party_scripts[:3]:  # Mostra apenas os 3 primeiros
            logger.info(f"  - {script['src']}")

if __name__ == "__main__":
    try:
        logger.info("=== Iniciando verificação do site Promobit ===")
        asyncio.run(check_promobit())
        logger.info("=== Verificação concluída com sucesso ===")
    except Exception as e:
        logger.critical(f"=== Verificação falhou: {e} ===", exc_info=True)
        print(f"\nERRO: A verificação falhou. Consulte o arquivo de log 'promobit_check.log' para mais detalhes.")
        exit(1)
