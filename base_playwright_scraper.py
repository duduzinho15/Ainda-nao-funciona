#!/usr/bin/env python3
"""
Classe Base para Scrapers usando Playwright
Fornece funcionalidades comuns para todos os scrapers
"""

import time
import json
import logging
import asyncio
from typing import List, Dict, Optional, Any
from urllib.parse import quote, urljoin
import random
from playwright.async_api import async_playwright, Browser, Page
import re

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BasePlaywrightScraper:
    """Classe base para todos os scrapers usando Playwright"""
    
    def __init__(self, base_url: str, store_name: str, headless: bool = True):
        self.base_url = base_url
        self.store_name = store_name
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None
        
        # Configurações padrão
        self.max_products_per_page = 20
        self.max_pages_per_category = 2
        self.delay_between_requests = (2, 5)
        self.delay_between_products = (0.3, 0.8)
        
    async def setup_browser(self):
        """Configura o navegador Playwright com opções otimizadas"""
        try:
            self.playwright = await async_playwright().start()
            
            # Configurações do navegador
            browser_options = {
                "headless": self.headless,
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-images",  # Acelera o carregamento
                    "--disable-javascript",  # Para sites simples
                    "--disable-css"
                ]
            }
            
            # Inicia o navegador
            self.browser = await self.playwright.chromium.launch(**browser_options)
            
            # Cria nova página
            self.page = await self.browser.new_page()
            
            # Configura viewport
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            # User agent realista
            await self.page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            })
            
            # Remove indicadores de automação
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en'],
                });
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32',
                });
            """)
            
            logger.info(f"✅ Navegador Playwright configurado para {self.store_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar navegador: {e}")
            return False
    
    def get_random_delay(self, min_delay: float = None, max_delay: float = None):
        """Retorna um delay aleatório para parecer humano"""
        min_d = min_delay or self.delay_between_requests[0]
        max_d = max_delay or self.delay_between_requests[1]
        return random.uniform(min_d, max_d)
    
    async def scroll_page_smart(self, scroll_pause: float = 1.0):
        """Faz scroll inteligente da página para carregar conteúdo dinâmico"""
        try:
            # Scroll suave para baixo
            await self.page.evaluate("""
                window.scrollTo({
                    top: document.body.scrollHeight,
                    behavior: 'smooth'
                });
            """)
            await asyncio.sleep(scroll_pause)
            
            # Scroll para o meio
            await self.page.evaluate("""
                window.scrollTo({
                    top: document.body.scrollHeight / 2,
                    behavior: 'smooth'
                });
            """)
            await asyncio.sleep(scroll_pause * 0.7)
            
            # Scroll para cima
            await self.page.evaluate("""
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            """)
            await asyncio.sleep(scroll_pause * 0.5)
            
            logger.debug("✅ Scroll inteligente da página realizado")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao fazer scroll: {e}")
    
    async def wait_for_page_load(self, timeout: int = 10000):
        """Aguarda o carregamento da página"""
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        except:
            try:
                await self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
            except:
                logger.warning("⚠️ Timeout aguardando carregamento da página")
    
    async def extract_text_safe(self, element, selector: str) -> Optional[str]:
        """Extrai texto de um elemento de forma segura"""
        try:
            if hasattr(element, 'query_selector'):
                text_elem = await element.query_selector(selector)
                if text_elem:
                    text = await text_elem.text_content()
                    return text.strip() if text else None
            return None
        except:
            return None
    
    async def extract_attribute_safe(self, element, selector: str, attribute: str) -> Optional[str]:
        """Extrai atributo de um elemento de forma segura"""
        try:
            if hasattr(element, 'query_selector'):
                attr_elem = await element.query_selector(selector)
                if attr_elem:
                    value = await attr_elem.get_attribute(attribute)
                    return value
            return None
        except:
            return None
    
    async def search_products_by_category(self, categoria: str, search_url: str, 
                                        product_selectors: List[str], 
                                        title_selectors: List[str],
                                        price_selectors: List[str],
                                        link_selectors: List[str],
                                        image_selectors: List[str],
                                        discount_selectors: List[str] = None) -> List[Dict]:
        """Método genérico para buscar produtos por categoria"""
        ofertas = []
        
        try:
            logger.info(f"🔍 Buscando ofertas na categoria: {categoria}")
            
            for page_num in range(1, self.max_pages_per_category + 1):
                try:
                    # Constrói URL da página
                    if page_num > 1:
                        page_url = f"{search_url}&page={page_num}" if "?" in search_url else f"{search_url}?page={page_num}"
                    else:
                        page_url = search_url
                    
                    logger.info(f"📄 Acessando página {page_num}: {page_url}")
                    
                    # Acessa a página
                    await self.page.goto(page_url, wait_until="networkidle")
                    await asyncio.sleep(self.get_random_delay())
                    
                    # Faz scroll inteligente
                    await self.scroll_page_smart()
                    
                    # Extrai produtos da página atual
                    page_ofertas = await self.extract_products_from_page(
                        categoria, product_selectors, title_selectors, 
                        price_selectors, link_selectors, image_selectors, discount_selectors
                    )
                    ofertas.extend(page_ofertas)
                    
                    logger.info(f"✅ Página {page_num}: {len(page_ofertas)} produtos encontrados")
                    
                    # Delay entre páginas
                    await asyncio.sleep(self.get_random_delay())
                    
                    # Limita o número de produtos por categoria
                    if len(ofertas) >= self.max_products_per_page * 2:
                        logger.info(f"🛑 Limite de produtos atingido para {categoria}")
                        break
                        
                except Exception as e:
                    logger.error(f"❌ Erro na página {page_num}: {e}")
                    continue
            
            logger.info(f"🎯 Total de ofertas para {categoria}: {len(ofertas)}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar categoria {categoria}: {e}")
        
        return ofertas
    
    async def extract_products_from_page(self, categoria: str, 
                                       product_selectors: List[str],
                                       title_selectors: List[str],
                                       price_selectors: List[str],
                                       link_selectors: List[str],
                                       image_selectors: List[str],
                                       discount_selectors: List[str] = None) -> List[Dict]:
        """Extrai produtos da página atual de forma genérica"""
        ofertas = []
        
        try:
            # Aguarda um pouco para garantir carregamento
            await asyncio.sleep(2)
            
            # Procura por produtos usando diferentes seletores
            products_found = []
            for selector in product_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        products_found = elements
                        logger.info(f"✅ Encontrados {len(elements)} produtos com selector: {selector}")
                        break
                except:
                    continue
            
            if not products_found:
                # Fallback: procura por links de produto
                try:
                    links = await self.page.query_selector_all('a[href*="/product/"], a[href*="/item/"]')
                    if links:
                        logger.info(f"✅ Encontrados {len(links)} links de produto")
                        products_found = [{'link_element': link} for link in links]
                except:
                    pass
            
            logger.info(f"🔍 Total de produtos encontrados: {len(products_found)}")
            
            # Extrai informações de cada produto
            for i, product in enumerate(products_found[:self.max_products_per_page]):
                try:
                    produto = await self.extract_single_product(
                        product, categoria, title_selectors, price_selectors,
                        link_selectors, image_selectors, discount_selectors
                    )
                    if produto:
                        ofertas.append(produto)
                        
                        # Delay pequeno entre produtos
                        await asyncio.sleep(random.uniform(*self.delay_between_products))
                        
                except Exception as e:
                    logger.debug(f"⚠️ Erro ao extrair produto {i}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Erro ao extrair produtos da página: {e}")
        
        return ofertas
    
    async def extract_single_product(self, product_element, categoria: str,
                                   title_selectors: List[str],
                                   price_selectors: List[str],
                                   link_selectors: List[str],
                                   image_selectors: List[str],
                                   discount_selectors: List[str] = None) -> Optional[Dict]:
        """Extrai informações de um produto de forma genérica"""
        try:
            # Título do produto
            titulo = None
            for selector in title_selectors:
                titulo = await self.extract_text_safe(product_element, selector)
                if titulo:
                    break
            
            # Preço do produto
            preco = None
            for selector in price_selectors:
                price_text = await self.extract_text_safe(product_element, selector)
                if price_text:
                    # Remove caracteres não numéricos exceto vírgula e ponto
                    preco = re.sub(r'[^\d,.]', '', price_text)
                    if preco:
                        break
            
            # Link do produto
            link = None
            for selector in link_selectors:
                href = await self.extract_attribute_safe(product_element, selector, 'href')
                if href:
                    if not href.startswith('http'):
                        link = urljoin(self.base_url, href)
                    else:
                        link = href
                    break
            
            # Imagem do produto
            imagem = None
            for selector in image_selectors:
                src = await self.extract_attribute_safe(product_element, selector, 'src')
                if not src:
                    src = await self.extract_attribute_safe(product_element, selector, 'data-src')
                if src:
                    if not src.startswith('http'):
                        imagem = urljoin(self.base_url, src)
                    else:
                        imagem = src
                    break
            
            # Desconto (opcional)
            desconto = None
            if discount_selectors:
                for selector in discount_selectors:
                    discount_text = await self.extract_text_safe(product_element, selector)
                    if discount_text:
                        discount_match = re.search(r'(\d+)%?', discount_text)
                        if discount_match:
                            desconto = int(discount_match.group(1))
                            break
            
            # Validação: produto deve ter título e preço
            if titulo and preco:
                return {
                    'titulo': titulo,
                    'preco': preco,
                    'link': link,
                    'imagem': imagem,
                    'desconto': desconto,
                    'loja': self.store_name,
                    'categoria': categoria,
                    'timestamp': time.time()
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"❌ Erro ao extrair produto individual: {e}")
            return None
    
    async def test_connection(self) -> bool:
        """Testa a conexão com o site"""
        if not await self.setup_browser():
            return False
        
        try:
            logger.info(f"🔍 Testando conexão com {self.store_name}...")
            
            await self.page.goto(self.base_url, wait_until="networkidle")
            await asyncio.sleep(3)
            
            # Verifica se a página carregou
            title = await self.page.title()
            if title and len(title) > 0:
                logger.info(f"✅ Conexão com {self.store_name} funcionando")
                return True
            else:
                logger.warning(f"⚠️ Título da página vazio")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro na conexão: {e}")
            return False
        
        finally:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
    
    async def close_browser(self):
        """Fecha o navegador de forma segura"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("🔒 Navegador fechado")
        except Exception as e:
            logger.error(f"❌ Erro ao fechar navegador: {e}")
    
    def save_results(self, ofertas: List[Dict], filename_prefix: str = "ofertas"):
        """Salva os resultados em arquivo JSON"""
        if ofertas:
            timestamp = int(time.time())
            filename = f"{filename_prefix}_{self.store_name.lower()}_{timestamp}.json"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(ofertas, f, ensure_ascii=False, indent=2)
                logger.info(f"💾 Resultados salvos em: {filename}")
                return filename
            except Exception as e:
                logger.error(f"❌ Erro ao salvar arquivo: {e}")
        return None
