#!/usr/bin/env python3
"""
Scraper de Diagnóstico para a Amazon Brasil
Inspeciona a estrutura real da página para identificar os seletores corretos
"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AmazonScraperDebug:
    """Scraper de diagnóstico para a Amazon Brasil"""
    
    def __init__(self, headless: bool = False):  # Sempre False para debug
        self.base_url = "https://www.amazon.com.br"
        self.ofertas_url = "https://www.amazon.com.br/deals"
        self.headless = headless
        self.driver = None
        
    def setup_driver(self):
        """Configura o driver do Chrome"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless=new")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logger.info("✅ Driver do Chrome configurado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar driver: {e}")
            return False
    
    def close_driver(self):
        """Fecha o driver do Chrome"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Driver do Chrome fechado")
            except Exception as e:
                logger.error(f"❌ Erro ao fechar driver: {e}")
    
    def wait_for_page_load(self, timeout: int = 30):
        """Aguarda o carregamento da página"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)  # Aguarda JavaScript carregar
            return True
        except TimeoutException:
            logger.warning("⚠️ Timeout aguardando carregamento da página")
            return False
    
    def inspect_page_structure(self):
        """Inspeciona a estrutura da página para identificar seletores"""
        try:
            logger.info("🔍 INSPECIONANDO ESTRUTURA DA PÁGINA")
            logger.info("=" * 60)
            
            # 1. Verifica se a página carregou
            page_title = self.driver.title
            logger.info(f"📄 Título da página: {page_title}")
            
            # 2. Procura por elementos com data-testid
            testid_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid]')
            logger.info(f"🏷️ Elementos com data-testid: {len(testid_elements)}")
            
            for elem in testid_elements[:10]:  # Mostra apenas os primeiros 10
                testid = elem.get_attribute('data-testid')
                tag = elem.tag_name
                classes = elem.get_attribute('class')
                logger.info(f"   - {tag}[data-testid='{testid}'] .{classes}")
            
            # 3. Procura por produtos com diferentes seletores
            logger.info("\n🔍 PROCURANDO POR PRODUTOS:")
            
            selectors_to_test = [
                '[data-testid="product-card"]',
                '[data-testid="deal-card"]',
                '.product-card',
                '.deal-card',
                'div[class*="product"]',
                'div[class*="deal"]',
                'div[class*="card"]',
                'div[class*="item"]'
            ]
            
            for selector in selectors_to_test:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"✅ {selector}: {len(elements)} elementos encontrados")
                        
                        # Inspeciona o primeiro elemento
                        first_elem = elements[0]
                        logger.info(f"   📋 Primeiro elemento:")
                        logger.info(f"      Tag: {first_elem.tag_name}")
                        logger.info(f"      Classes: {first_elem.get_attribute('class')}")
                        logger.info(f"      ID: {first_elem.get_attribute('id')}")
                        
                        # Procura por título no primeiro elemento
                        title_selectors = ['h1', 'h2', 'h3', 'h4', '[class*="title"]', '[class*="name"]']
                        for title_sel in title_selectors:
                            try:
                                title_elem = first_elem.find_element(By.CSS_SELECTOR, title_sel)
                                if title_elem and title_elem.text.strip():
                                    logger.info(f"      📝 Título encontrado com {title_sel}: {title_elem.text.strip()[:100]}...")
                                    break
                            except NoSuchElementException:
                                continue
                        
                        # Procura por preço no primeiro elemento
                        price_selectors = ['[class*="price"]', '.price', '[data-testid*="price"]']
                        for price_sel in price_selectors:
                            try:
                                price_elem = first_elem.find_element(By.CSS_SELECTOR, price_sel)
                                if price_elem and price_elem.text.strip():
                                    logger.info(f"      💰 Preço encontrado com {price_sel}: {price_elem.text.strip()}")
                                    break
                            except NoSuchElementException:
                                continue
                        
                        # Procura por link no primeiro elemento
                        try:
                            link_elem = first_elem.find_element(By.CSS_SELECTOR, 'a[href*="/dp/"]')
                            if link_elem:
                                href = link_elem.get_attribute('href')
                                logger.info(f"      🔗 Link encontrado: {href[:100]}...")
                        except NoSuchElementException:
                            logger.info("      🔗 Link não encontrado")
                        
                        break  # Para no primeiro seletor que funcionar
                    else:
                        logger.info(f"❌ {selector}: 0 elementos encontrados")
                except Exception as e:
                    logger.info(f"❌ {selector}: Erro - {e}")
            
            # 4. Procura por links de produto em toda a página
            logger.info("\n🔍 LINKS DE PRODUTO NA PÁGINA:")
            product_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/dp/"]')
            logger.info(f"   📦 Links de produto encontrados: {len(product_links)}")
            
            if product_links:
                for i, link in enumerate(product_links[:5]):  # Mostra apenas os primeiros 5
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    parent_tag = link.find_element(By.XPATH, './..').tag_name
                    parent_class = link.find_element(By.XPATH, './..').get_attribute('class')
                    
                    logger.info(f"   {i+1}. Link: {href[:80]}...")
                    logger.info(f"      Texto: {text[:50]}...")
                    logger.info(f"      Pai: {parent_tag}.{parent_class}")
            
            # 5. Salva o HTML da página para análise
            logger.info("\n💾 SALVANDO HTML DA PÁGINA...")
            html_content = self.driver.page_source
            
            with open('amazon_debug_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info("✅ HTML salvo em 'amazon_debug_page.html'")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inspecionar página: {e}")
            import traceback
            traceback.print_exc()
    
    def run_diagnosis(self):
        """Executa o diagnóstico completo"""
        try:
            if not self.setup_driver():
                return
            
            logger.info(f"🔍 Acessando: {self.ofertas_url}")
            self.driver.get(self.ofertas_url)
            
            if not self.wait_for_page_load():
                logger.warning("⚠️ Página não carregou completamente")
            
            # Inspeciona a estrutura da página
            self.inspect_page_structure()
            
        except Exception as e:
            logger.error(f"❌ Erro geral no diagnóstico: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Mantém o navegador aberto para inspeção manual
            logger.info("\n🔍 Navegador mantido aberto para inspeção manual")
            logger.info("💡 Inspecione a página e pressione Enter para fechar...")
            input()

def main():
    """Função principal"""
    print("🔍 DIAGNÓSTICO DO AMAZON SCRAPER")
    print("=" * 60)
    
    scraper = AmazonScraperDebug()
    scraper.run_diagnosis()

if __name__ == "__main__":
    main()
