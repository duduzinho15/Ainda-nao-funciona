#!/usr/bin/env python3
"""
Scraper Corrigido para a Amazon Brasil - Versão Robusta e Atualizada
Resolve problemas de seletores CSS e implementa fallbacks robustos
"""
import time
import logging
import re
import random
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AmazonScraperFixed:
    """Scraper corrigido e robusto para a Amazon Brasil"""
    
    def __init__(self, headless: bool = True):
        self.base_url = "https://www.amazon.com.br"
        self.ofertas_url = "https://www.amazon.com.br/deals"
        self.headless = headless
        self.driver = None
        
        # User agents para rotação
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0"
        ]
        
    def setup_driver(self):
        """Configura o driver do Chrome com configurações anti-detecção"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless=new")  # Nova versão do headless
            
            # Configurações anti-detecção
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent aleatório
            user_agent = random.choice(self.user_agents)
            chrome_options.add_argument(f"--user-agent={user_agent}")
            
            # Configurações de performance
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
                "profile.managed_default_content_settings.stylesheets": 2,
                "profile.managed_default_content_settings.cookies": 1,
                "profile.managed_default_content_settings.javascript": 1,
                "profile.managed_default_content_settings.plugins": 1,
                "profile.managed_default_content_settings.popups": 2,
                "profile.managed_default_content_settings.geolocation": 2,
                "profile.managed_default_content_settings.media_stream": 2,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Desabilita logs do Chrome
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--silent")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Remove propriedades que identificam automação
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
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
    
    def wait_for_page_load(self, timeout: int = 45):
        """Aguarda o carregamento da página com timeout maior"""
        try:
            # Aguarda o body carregar
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Aguarda JavaScript carregar
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Delay aleatório para parecer humano
            time.sleep(random.uniform(2, 5))
            return True
            
        except TimeoutException:
            logger.warning("⚠️ Timeout aguardando carregamento da página")
            return False
    
    def scroll_page(self, scroll_pause: float = 2.0):
        """Faz scroll da página de forma mais humana"""
        try:
            # Scroll gradual para baixo
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            current_position = 0
            
            while current_position < total_height:
                current_position += viewport_height
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(1, 3))
            
            # Scroll para cima
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(scroll_pause)
            
            logger.info("✅ Scroll da página realizado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer scroll: {e}")
            return False
    
    def extract_product_info(self, product_element) -> Optional[Dict]:
        """Extrai informações de um produto com seletores atualizados"""
        try:
            # Tenta diferentes seletores para o título (atualizados)
            titulo = None
            titulo_selectors = [
                # Seletores principais da Amazon
                '[data-testid="product-title"]',
                'h2[data-testid="product-title"]',
                '.product-title',
                '.product-name',
                '[class*="title"]',
                'h2', 'h3', 'h4',
                # Seletores específicos de ofertas
                '[data-testid="deal-title"]',
                '.deal-title',
                '[class*="deal"] [class*="title"]',
                # Fallbacks genéricos
                '[class*="product"] [class*="title"]',
                '[class*="item"] [class*="title"]'
            ]
            
            for selector in titulo_selectors:
                try:
                    titulo_elem = product_element.find_element(By.CSS_SELECTOR, selector)
                    if titulo_elem and titulo_elem.text.strip():
                        titulo = titulo_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Fallback: procura por qualquer texto que pareça título
            if not titulo:
                try:
                    # Procura por elementos com texto que pareça título
                    all_elements = product_element.find_elements(By.CSS_SELECTOR, '*')
                    for elem in all_elements:
                        text = elem.text.strip()
                        if text and len(text) > 10 and len(text) < 200:
                            # Verifica se parece um título de produto
                            if any(word in text.lower() for word in ['smartphone', 'notebook', 'fone', 'camera', 'tv', 'console']):
                                titulo = text
                                break
                except Exception:
                    pass
            
            # Extrai preço com seletores atualizados
            preco = None
            preco_selectors = [
                # Seletores principais de preço
                '[data-testid="price-value"]',
                '.price-value',
                '.price',
                '[class*="price"]',
                '.a-price-whole',
                # Seletores específicos da Amazon
                '.a-price .a-offscreen',
                '.a-price-range .a-offscreen',
                '[data-a-color="price"] .a-offscreen',
                # Seletores de oferta
                '[data-testid="deal-price"]',
                '.deal-price',
                '[class*="deal"] [class*="price"]'
            ]
            
            for selector in preco_selectors:
                try:
                    preco_elem = product_element.find_element(By.CSS_SELECTOR, selector)
                    if preco_elem:
                        preco_text = preco_elem.text.strip()
                        # Remove caracteres não numéricos exceto vírgula e ponto
                        preco = re.sub(r'[^\d,.]', '', preco_text)
                        if preco:
                            break
                except NoSuchElementException:
                    continue
            
            # Extrai link do produto
            link = None
            link_selectors = [
                'a[href*="/dp/"]',
                'a[href*="/gp/product/"]',
                'a[href*="/d/"]',
                'a[href*="/deal/"]'
            ]
            
            for selector in link_selectors:
                try:
                    link_elem = product_element.find_element(By.CSS_SELECTOR, selector)
                    if link_elem:
                        link = link_elem.get_attribute('href')
                        if link and not link.startswith('http'):
                            link = urljoin(self.base_url, link)
                        if link:
                            break
                except NoSuchElementException:
                    continue
            
            # Extrai imagem
            imagem = None
            try:
                img_elem = product_element.find_element(By.CSS_SELECTOR, 'img')
                if img_elem:
                    imagem = img_elem.get_attribute('src')
                    if not imagem:
                        imagem = img_elem.get_attribute('data-src')  # Imagens lazy loading
            except NoSuchElementException:
                pass
            
            # Extrai desconto
            desconto = None
            desconto_selectors = [
                '[class*="discount"]',
                '[class*="off"]',
                '.badge',
                '.a-badge-text',
                '[data-testid="discount-badge"]',
                '.deal-badge',
                '[class*="deal"] [class*="badge"]'
            ]
            
            for selector in desconto_selectors:
                try:
                    desconto_elem = product_element.find_element(By.CSS_SELECTOR, selector)
                    if desconto_elem:
                        desconto_text = desconto_elem.text.strip()
                        # Extrai números do texto de desconto
                        desconto_match = re.search(r'(\d+)%?', desconto_text)
                        if desconto_match:
                            desconto = int(desconto_match.group(1))
                            break
                except NoSuchElementException:
                    continue
            
            # Validação: produto deve ter pelo menos título e preço
            if titulo and preco:
                return {
                    'titulo': titulo,
                    'preco': preco,
                    'link': link,
                    'imagem': imagem,
                    'desconto': desconto,
                    'loja': 'Amazon Brasil',
                    'categoria': 'Ofertas do Dia',
                    'timestamp': time.time()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair informações do produto: {e}")
            return None
    
    def buscar_ofertas(self, max_paginas: int = 3) -> List[Dict]:
        """Busca ofertas da Amazon Brasil com método robusto"""
        ofertas = []
        
        try:
            if not self.setup_driver():
                return ofertas
            
            logger.info(f"🔍 Acessando: {self.ofertas_url}")
            self.driver.get(self.ofertas_url)
            
            if not self.wait_for_page_load():
                logger.warning("⚠️ Página não carregou completamente")
            
            # Faz scroll para carregar conteúdo dinâmico
            self.scroll_page()
            
            # Procura por produtos com seletores atualizados
            logger.info("🔍 Procurando por produtos...")
            
            # Seletores atualizados para produtos
            product_selectors = [
                # Seletores principais
                '[data-testid="product-card"]',
                '[data-testid="deal-card"]',
                '.product-card',
                '.deal-card',
                # Seletores específicos da Amazon
                '[data-testid="grid-deal-card"]',
                '.grid-deal-card',
                '[class*="deal"] [class*="card"]',
                '[class*="product"] [class*="card"]',
                # Fallbacks
                'div[class*="product"]',
                'div[class*="deal"]',
                'div[class*="card"]',
                'div[class*="item"]'
            ]
            
            produtos_encontrados = []
            for selector in product_selectors:
                try:
                    produtos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if produtos:
                        produtos_encontrados = produtos
                        logger.info(f"✅ Encontrados {len(produtos)} produtos com seletor: {selector}")
                        break
                except Exception:
                    continue
            
            # Fallback: procura por qualquer elemento que contenha link de produto
            if not produtos_encontrados:
                logger.info("🔄 Tentando fallback para encontrar produtos...")
                try:
                    links_produto = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/dp/"], a[href*="/gp/product/"]')
                    if links_produto:
                        # Agrupa links por produto pai
                        produtos_encontrados = []
                        for link in links_produto:
                            try:
                                # Procura pelo elemento pai que contém o produto
                                produto_pai = link.find_element(By.XPATH, './ancestor::*[contains(@class, "card") or contains(@class, "item") or contains(@class, "product") or contains(@class, "deal") or contains(@class, "grid")]')
                                if produto_pai and produto_pai not in produtos_encontrados:
                                    produtos_encontrados.append(produto_pai)
                            except NoSuchElementException:
                                # Se não encontrar pai, usa o próprio link
                                produtos_encontrados.append(link)
                        logger.info(f"✅ Encontrados {len(produtos_encontrados)} produtos via fallback")
                except Exception as e:
                    logger.warning(f"⚠️ Fallback falhou: {e}")
            
            # Extrai informações dos produtos
            if produtos_encontrados:
                logger.info(f"📋 Extraindo informações de {len(produtos_encontrados)} produtos...")
                
                for i, produto in enumerate(produtos_encontrados):
                    try:
                        info_produto = self.extract_product_info(produto)
                        if info_produto:
                            ofertas.append(info_produto)
                            logger.info(f"✅ Produto {i+1}: {info_produto['titulo'][:50]}...")
                        else:
                            logger.warning(f"⚠️ Produto {i+1}: Não foi possível extrair informações")
                    except Exception as e:
                        logger.error(f"❌ Erro ao processar produto {i+1}: {e}")
                        continue
                    
                    # Limita o número de produtos para evitar sobrecarga
                    if len(ofertas) >= 50:
                        logger.info("🛑 Limite de 50 produtos atingido")
                        break
            else:
                logger.warning("⚠️ Nenhum produto encontrado")
            
            logger.info(f"🎯 Total de ofertas extraídas: {len(ofertas)}")
            
        except Exception as e:
            logger.error(f"❌ Erro geral na busca de ofertas: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.close_driver()
        
        return ofertas

def main():
    """Função principal para teste"""
    print("🚀 TESTANDO AMAZON SCRAPER CORRIGIDO")
    print("=" * 60)
    
    scraper = AmazonScraperFixed(headless=False)  # False para debug
    ofertas = scraper.buscar_ofertas()
    
    print(f"\n🎯 RESULTADO: {len(ofertas)} ofertas encontradas")
    print("=" * 60)
    
    for i, oferta in enumerate(ofertas[:5], 1):  # Mostra apenas as primeiras 5
        print(f"\n{i}. {oferta['titulo']}")
        print(f"   💰 Preço: {oferta['preco']}")
        if oferta.get('desconto'):
            print(f"   🏷️ Desconto: {oferta['desconto']}%")
        print(f"   🔗 Link: {oferta.get('link', 'N/A')}")
        print(f"   🏪 Loja: {oferta['loja']}")

if __name__ == "__main__":
    main()
