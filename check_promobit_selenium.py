"""
Script para verificar a estrutura do site Promobit usando Selenium WebDriver.
Este script abre um navegador controlado para inspecionar o site.
"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('promobit_selenium_check.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('promobit_selenium')

# URL base do Promobit
BASE_URL = "https://www.promobit.com.br"
CATEGORY_URL = f"{BASE_URL}/ofertas/1?categoria=informatica"

# Configurações do navegador
CHROME_OPTIONS = Options()
# Configurações para modo headless
CHROME_OPTIONS.add_argument("--headless")  # Executa em modo headless (sem interface gráfica)
CHROME_OPTIONS.add_argument("--window-size=1920,1080")  # Define um tamanho de janela fixo
CHROME_OPTIONS.add_argument("--disable-extensions")  # Desativa extensões
CHROME_OPTIONS.add_argument("--disable-popup-blocking")  # Desativa bloqueio de popups
CHROME_OPTIONS.add_argument("--disable-notifications")  # Desativa notificações
CHROME_OPTIONS.add_argument("--disable-infobars")  # Desativa a barra de informações
CHROME_OPTIONS.add_argument("--disable-dev-shm-usage")  # Evita problemas de memória
CHROME_OPTIONS.add_argument("--no-sandbox")  # Necessário para alguns ambientes
CHROME_OPTIONS.add_argument("--disable-gpu")  # Desativa aceleração de GPU
CHROME_OPTIONS.add_argument("--disable-blink-features=AutomationControlled")  # Torna menos detectável
CHROME_OPTIONS.add_argument("--disable-web-security")  # Desativa a política de mesma origem
CHROME_OPTIONS.add_argument("--allow-running-insecure-content")  # Permite conteúdo inseguro

# Headers para simular um navegador real
CHROME_OPTIONS.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

def setup_driver():
    """Configura e retorna uma instância do WebDriver do Chrome."""
    try:
        logger.info("Iniciando o navegador Chrome...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=CHROME_OPTIONS)
        driver.implicitly_wait(10)  # Espera implícita de 10 segundos
        return driver
    except Exception as e:
        logger.error(f"Erro ao configurar o WebDriver: {e}")
        raise

def save_page_source(driver, filename):
    """Salva o código-fonte da página atual em um arquivo."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info(f"Código-fonte da página salvo em '{filename}'")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar o código-fonte da página: {e}")
        return False

def check_elements(driver, page_name):
    """Verifica a presença de elementos-chave na página."""
    logger.info(f"\nAnalisando elementos em: {page_name}")
    
    # Verifica título da página
    title = driver.title
    logger.info(f"Título da página: {title if title else 'Não encontrado'}")
    
    # Verifica se há um formulário de login/cadastro
    login_forms = driver.find_elements(By.CSS_SELECTOR, 'form[id*="login"], form[id*="signin"], form[id*="signup"]')
    if login_forms:
        logger.info(f"Formulário de login/cadastro encontrado: {len(login_forms)} elementos")
    
    # Verifica se há um CAPTCHA
    captcha = driver.find_elements(By.CSS_SELECTOR, '.g-recaptcha, .captcha, iframe[src*="recaptcha"]')
    if captcha:
        logger.warning("CAPTCHA detectado na página!")
    
    # Verifica se há mensagens de bloqueio
    block_terms = ['Access Denied', 'Forbidden', 'Bot detected', 'DDOS protection',
                  'Acesso negado', 'Bloqueado', 'Proteção contra bots', 'Cloudflare']
    
    block_messages = []
    for term in block_terms:
        elements = driver.find_elements(By.XPATH, f"//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{term.lower()}')]")
        block_messages.extend(elements)
    
    if block_messages:
        logger.warning(f"Possíveis mensagens de bloqueio encontradas: {len(block_messages)}")
        for i, msg in enumerate(block_messages[:3], 1):  # Mostra apenas as 3 primeiras mensagens
            logger.warning(f"  {i}. {msg.text[:200] if msg.text else '[conteúdo vazio]'}")
    
    # Verifica se há ofertas na página
    check_offer_selectors(driver)
    
    # Verifica se há scripts de terceiros
    check_third_party_scripts(driver)

def check_offer_selectors(driver):
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
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                logger.info(f"Encontrados {len(elements)} elementos com o seletor: '{selector}'")
                if not found:  # Mostra um exemplo apenas para o primeiro seletor que encontrar
                    logger.debug(f"Exemplo de elemento com o seletor '{selector}': {elements[0].text[:200]}...")
                    found = True
        except Exception as e:
            logger.debug(f"Erro ao buscar elementos com o seletor '{selector}': {e}")
    
    if not found:
        logger.warning("Nenhum dos seletores de oferta retornou resultados")
        
        # Tenta encontrar qualquer elemento que possa conter ofertas
        logger.info("Tentando encontrar qualquer elemento que possa conter ofertas...")
        common_containers = driver.find_elements(By.CSS_SELECTOR, 'div, section, article, main')
        logger.info(f"Encontrados {len(common_containers)} containers na página")
        
        # Filtra containers que parecem conter conteúdo de ofertas
        offer_containers = []
        for container in common_containers[:50]:  # Limita a 50 para não ficar muito lento
            try:
                text = container.text.lower()
                if any(term in text for term in ['oferta', 'promoção', 'desconto', 'preço', 'comprar', 'r$']):
                    offer_containers.append(container)
            except:
                continue
        
        if offer_containers:
            logger.info(f"Encontrados {len(offer_containers)} containers que podem conter ofertas")
            logger.debug(f"Exemplo de container: {offer_containers[0].text[:200]}...")

def check_third_party_scripts(driver):
    """Verifica a presença de scripts de terceiros."""
    scripts = driver.find_elements(By.CSS_SELECTOR, 'script[src]')
    third_party_domains = [
        'cloudflare', 'recaptcha', 'google-analytics', 'googletagmanager', 'doubleclick',
        'facebook', 'twitter', 'linkedin', 'pinterest', 'addthis', 'hotjar', 'optimizely'
    ]
    
    third_party_scripts = []
    for script in scripts:
        src = script.get_attribute('src')
        if any(domain in src.lower() for domain in third_party_domains):
            third_party_scripts.append(src)
    
    if third_party_scripts:
        logger.info(f"\nScripts de terceiros encontrados: {len(third_party_scripts)}")
        for src in third_party_scripts[:5]:  # Mostra apenas os 5 primeiros
            logger.info(f"  - {src}")
    else:
        logger.info("\nNenhum script de terceiros encontrado")

def check_promobit():
    """Verifica a estrutura do site Promobit usando Selenium."""
    driver = None
    try:
        # Configura o navegador
        driver = setup_driver()
        
        # Primeiro, tenta acessar a página inicial
        logger.info("\n=== Verificando acesso à página inicial ===")
        driver.get(BASE_URL)
        logger.info(f"URL atual: {driver.current_url}")
        
        # Aguarda um pouco para o carregamento da página
        time.sleep(5)
        
        # Salva o código-fonte da página
        save_page_source(driver, 'promobit_home_selenium.html')
        
        # Tira um screenshot da página
        try:
            driver.save_screenshot('promobit_home_screenshot.png')
            logger.info("Screenshot da página inicial salvo em 'promobit_home_screenshot.png'")
        except Exception as e:
            logger.error(f"Erro ao salvar screenshot: {e}")
        
        # Verifica elementos na página
        check_elements(driver, "Página inicial")
        
        # Pequena pausa entre as requisições
        time.sleep(2)
        
        # Em seguida, tenta acessar a categoria de informática
        logger.info("\n=== Verificando acesso à categoria de informática ===")
        driver.get(CATEGORY_URL)
        logger.info(f"URL atual: {driver.current_url}")
        
        # Aguarda um pouco para o carregamento da página
        time.sleep(5)
        
        # Salva o código-fonte da página
        save_page_source(driver, 'promobit_category_selenium.html')
        
        # Tira um screenshot da página
        try:
            driver.save_screenshot('promobit_category_screenshot.png')
            logger.info("Screenshot da página de categoria salvo em 'promobit_category_screenshot.png'")
        except Exception as e:
            logger.error(f"Erro ao salvar screenshot: {e}")
        
        # Verifica elementos na página
        check_elements(driver, "Página de categoria")
        
        logger.info("\n=== Verificação concluída com sucesso ===")
        
    except Exception as e:
        logger.critical(f"Erro durante a verificação: {e}", exc_info=True)
        return 1
    finally:
        if driver:
            driver.quit()
            logger.info("Navegador fechado")
    
    return 0

if __name__ == "__main__":
    logger.info("=== Iniciando verificação do site Promobit com Selenium ===")
    exit_code = check_promobit()
    logger.info(f"=== Verificação concluída com código de saída: {exit_code} ===")
    exit(exit_code)
