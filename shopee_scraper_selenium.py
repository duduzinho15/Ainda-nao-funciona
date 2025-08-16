#!/usr/bin/env python3
"""
Scraper da Shopee usando Selenium - Versão Avançada
Contorna proteções anti-bot usando navegador real
"""

import time
import json
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ShopeeSeleniumScraper:
    """Scraper da Shopee usando Selenium para contornar proteções anti-bot"""
    
    def __init__(self, headless: bool = False):
        self.base_url = "https://shopee.com.br"
        self.headless = headless
        self.driver = None
        self.wait = None
        
        # Categorias populares para buscar ofertas
        self.categorias = [
            "smartphone",
            "notebook", 
            "fone de ouvido",
            "smart tv",
            "console de videogame",
            "câmera digital",
            "tablet",
            "smartwatch"
        ]
        
        # URLs de ofertas especiais
        self.ofertas_urls = [
            "https://shopee.com.br/daily-discover",
            "https://shopee.com.br/flash-sale",
            "https://shopee.com.br/ofertas-relampago"
        ]
    
    def setup_driver(self):
        """Configura o driver do Chrome com opções otimizadas"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Configurações para parecer navegador real
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent realista
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Configurações de janela
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Remove indicadores de automação
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 20)
            
            logger.info("✅ Driver do Chrome configurado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar driver: {e}")
            return False
    
    def get_random_delay(self, min_delay: float = 2.0, max_delay: float = 5.0):
        """Retorna um delay aleatório para parecer humano"""
        return random.uniform(min_delay, max_delay)
    
    def scroll_page(self, scroll_pause: float = 1.0):
        """Faz scroll da página para carregar conteúdo dinâmico"""
        try:
            # Scroll para baixo
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)
            
            # Scroll para cima
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(scroll_pause)
            
            # Scroll para o meio
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(scroll_pause)
            
            logger.debug("✅ Scroll da página realizado")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao fazer scroll: {e}")
    
    def search_products_by_category(self, categoria: str, max_pages: int = 2) -> List[Dict]:
        """Busca produtos por categoria usando Selenium"""
        ofertas = []
        
        try:
            logger.info(f"🔍 Buscando ofertas na categoria: {categoria}")
            
            for page in range(1, max_pages + 1):
                try:
                    # Constrói URL de busca
                    search_url = f"{self.base_url}/search"
                    params = {
                        'keyword': categoria,
                        'page': page,
                        'sortBy': 'sales',
                        'order': 'desc'
                    }
                    
                    # Adiciona parâmetros à URL
                    if page > 1:
                        search_url += f"?page={page}&keyword={quote(categoria)}&sortBy=sales&order=desc"
                    else:
                        search_url += f"?keyword={quote(categoria)}&sortBy=sales&order=desc"
                    
                    logger.info(f"📄 Acessando página {page}: {search_url}")
                    
                    # Acessa a página
                    self.driver.get(search_url)
                    time.sleep(self.get_random_delay(3, 6))
                    
                    # Faz scroll para carregar produtos
                    self.scroll_page()
                    
                    # Aguarda carregamento dos produtos
                    try:
                        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-sqe="name"], .ie3A\\+n, [class*="item"]')))
                    except TimeoutException:
                        logger.warning(f"⚠️ Timeout aguardando produtos na página {page}")
                    
                    # Extrai produtos da página atual
                    page_ofertas = self.extract_products_from_page(categoria)
                    ofertas.extend(page_ofertas)
                    
                    logger.info(f"✅ Página {page}: {len(page_ofertas)} produtos encontrados")
                    
                    # Delay entre páginas
                    time.sleep(self.get_random_delay(3, 7))
                    
                    # Limita o número de produtos por categoria
                    if len(ofertas) >= 20:
                        logger.info(f"🛑 Limite de 20 produtos atingido para {categoria}")
                        break
                        
                except Exception as e:
                    logger.error(f"❌ Erro na página {page}: {e}")
                    continue
            
            logger.info(f"🎯 Total de ofertas para {categoria}: {len(ofertas)}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar categoria {categoria}: {e}")
        
        return ofertas
    
    def extract_products_from_page(self, categoria: str) -> List[Dict]:
        """Extrai produtos da página atual usando Selenium"""
        ofertas = []
        
        try:
            # Aguarda um pouco para garantir carregamento
            time.sleep(2)
            
            # Procura por produtos usando diferentes seletores
            product_selectors = [
                '[data-sqe="name"]',
                '.ie3A\\+n',
                '[class*="shopee-search-item-result"]',
                '[class*="item"]',
                '[class*="product"]',
                '[class*="card"]'
            ]
            
            products_found = []
            for selector in product_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        products_found = elements
                        logger.info(f"✅ Encontrados {len(elements)} produtos com selector: {selector}")
                        break
                except:
                    continue
            
            if not products_found:
                # Fallback: procura por qualquer elemento que contenha link de produto
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/product/"], a[href*="/item/"]')
                    if links:
                        logger.info(f"✅ Encontrados {len(links)} links de produto")
                        # Cria containers artificiais para os links
                        products_found = [{'link_element': link} for link in links]
                except:
                    pass
            
            logger.info(f"🔍 Total de produtos encontrados: {len(products_found)}")
            
            # Extrai informações de cada produto
            for i, product in enumerate(products_found[:15]):  # Limita a 15 produtos por página
                try:
                    produto = self.extract_single_product_selenium(product, categoria)
                    if produto:
                        ofertas.append(produto)
                        
                        # Delay pequeno entre produtos
                        time.sleep(0.5)
                        
                except Exception as e:
                    logger.debug(f"⚠️ Erro ao extrair produto {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Erro ao extrair produtos da página: {e}")
        
        return ofertas
    
    def extract_single_product_selenium(self, product_element, categoria: str) -> Optional[Dict]:
        """Extrai informações de um produto usando Selenium"""
        try:
            # Título do produto
            titulo = None
            title_selectors = [
                '[data-sqe="name"]',
                '.ie3A\\+n',
                '[class*="title"]',
                '[class*="name"]',
                'h1', 'h2', 'h3', 'h4'
            ]
            
            for selector in title_selectors:
                try:
                    if hasattr(product_element, 'find_element'):
                        title_elem = product_element.find_element(By.CSS_SELECTOR, selector)
                        if title_elem and title_elem.text.strip():
                            titulo = title_elem.text.strip()
                            break
                    else:
                        # Fallback para elementos que não são WebElement
                        continue
                except:
                    continue
            
            # Preço do produto
            preco = None
            price_selectors = [
                '[class*="price"]',
                '.price',
                '[class*="cost"]',
                '[class*="value"]'
            ]
            
            for selector in price_selectors:
                try:
                    if hasattr(product_element, 'find_element'):
                        price_elem = product_element.find_element(By.CSS_SELECTOR, selector)
                        if price_elem and price_elem.text.strip():
                            preco_text = price_elem.text.strip()
                            # Remove caracteres não numéricos exceto vírgula e ponto
                            import re
                            preco = re.sub(r'[^\d,.]', '', preco_text)
                            if preco:
                                break
                except:
                    continue
            
            # Link do produto
            link = None
            try:
                if hasattr(product_element, 'find_element'):
                    link_elem = product_element.find_element(By.CSS_SELECTOR, 'a[href*="/product/"], a[href*="/item/"]')
                    if link_elem:
                        href = link_elem.get_attribute('href')
                        if href and ('/product/' in href or '/item/' in href):
                            link = href
                elif hasattr(product_element, 'link_element'):
                    # Fallback para elementos com link_element
                    link = product_element['link_element'].get_attribute('href')
            except:
                pass
            
            # Imagem do produto
            imagem = None
            try:
                if hasattr(product_element, 'find_element'):
                    img_elem = product_element.find_element(By.CSS_SELECTOR, 'img')
                    if img_elem:
                        imagem = img_elem.get_attribute('src') or img_elem.get_attribute('data-src')
            except:
                pass
            
            # Desconto
            desconto = None
            discount_selectors = [
                '[class*="discount"]',
                '[class*="off"]',
                '.badge',
                '[class*="badge"]'
            ]
            
            for selector in discount_selectors:
                try:
                    if hasattr(product_element, 'find_element'):
                        discount_elem = product_element.find_element(By.CSS_SELECTOR, selector)
                        if discount_elem and discount_elem.text.strip():
                            discount_text = discount_elem.text.strip()
                            import re
                            discount_match = re.search(r'(\d+)%?', discount_text)
                            if discount_match:
                                desconto = int(discount_match.group(1))
                                break
                except:
                    continue
            
            # Validação: produto deve ter título e preço
            if titulo and preco:
                return {
                    'titulo': titulo,
                    'preco': preco,
                    'link': link,
                    'imagem': imagem,
                    'desconto': desconto,
                    'loja': 'Shopee Brasil',
                    'categoria': categoria,
                    'timestamp': time.time()
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"❌ Erro ao extrair produto individual: {e}")
            return None
    
    def buscar_ofertas_gerais(self) -> List[Dict]:
        """Busca ofertas gerais de todas as categorias"""
        todas_ofertas = []
        
        if not self.setup_driver():
            logger.error("❌ Não foi possível configurar o driver")
            return []
        
        try:
            logger.info("🚀 INICIANDO BUSCA DE OFERTAS NA SHOPEE COM SELENIUM")
            logger.info("=" * 60)
            
            for categoria in self.categorias:
                try:
                    logger.info(f"\n🔍 Buscando: {categoria.upper()}")
                    ofertas_categoria = self.search_products_by_category(categoria)
                    todas_ofertas.extend(ofertas_categoria)
                    
                    # Delay entre categorias
                    time.sleep(self.get_random_delay(3, 6))
                    
                except Exception as e:
                    logger.error(f"❌ Erro na categoria {categoria}: {e}")
                    continue
            
            # Remove duplicatas baseado no título
            ofertas_unicas = []
            titulos_vistos = set()
            
            for oferta in todas_ofertas:
                if oferta['titulo'] not in titulos_vistos:
                    ofertas_unicas.append(oferta)
                    titulos_vistos.add(oferta['titulo'])
            
            logger.info(f"\n🎯 TOTAL DE OFERTAS ÚNICAS: {len(ofertas_unicas)}")
            
        except Exception as e:
            logger.error(f"❌ Erro geral na busca: {e}")
        
        finally:
            # Fecha o driver
            if self.driver:
                self.driver.quit()
                logger.info("🔒 Driver fechado")
        
        return todas_ofertas
    
    def test_connection(self) -> bool:
        """Testa a conexão com a Shopee"""
        if not self.setup_driver():
            return False
        
        try:
            logger.info("🔍 Testando conexão com a Shopee...")
            
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Verifica se a página carregou
            if "Shopee" in self.driver.title:
                logger.info("✅ Conexão com a Shopee funcionando")
                return True
            else:
                logger.warning(f"⚠️ Título da página: {self.driver.title}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro na conexão: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Função principal para teste"""
    print("🚀 TESTANDO SHOPEE SCRAPER COM SELENIUM")
    print("=" * 60)
    
    scraper = ShopeeSeleniumScraper(headless=True)  # True para evitar problemas na primeira execução
    
    # Testa conexão primeiro
    if not scraper.test_connection():
        print("❌ Não foi possível conectar com a Shopee")
        return
    
    # Busca ofertas
    ofertas = scraper.buscar_ofertas_gerais()
    
    print(f"\n🎯 RESULTADO: {len(ofertas)} ofertas encontradas")
    print("=" * 60)
    
    for i, oferta in enumerate(ofertas[:10], 1):  # Mostra apenas as primeiras 10
        print(f"\n{i}. {oferta['titulo']}")
        print(f"   💰 Preço: {oferta['preco']}")
        if oferta.get('desconto'):
            print(f"   🏷️ Desconto: {oferta['desconto']}%")
        print(f"   🏪 Loja: {oferta['loja']}")
        print(f"   📂 Categoria: {oferta['categoria']}")
        if oferta.get('link'):
            print(f"   🔗 Link: {oferta['link'][:80]}...")
    
    # Salva as ofertas em arquivo JSON
    if ofertas:
        filename = f"ofertas_shopee_{int(time.time())}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(ofertas, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Ofertas salvas em: {filename}")

if __name__ == "__main__":
    main()
