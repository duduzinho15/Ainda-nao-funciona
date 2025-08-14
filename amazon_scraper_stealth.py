"""
Scraper Stealth para a Amazon Brasil - Usando Playwright com técnicas anti-detecção
"""
import asyncio
import time
import logging
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin
from playwright.async_api import async_playwright, Browser, Page

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AmazonStealthScraper:
    """Scraper stealth para a Amazon Brasil usando Playwright"""
    
    def __init__(self, headless: bool = True):
        self.base_url = "https://www.amazon.com.br"
        self.ofertas_url = "https://www.amazon.com.br/deals"
        self.headless = headless
        self.browser = None
        self.page = None
        
    async def setup_browser(self):
        """Configura o navegador Playwright com técnicas stealth"""
        try:
            self.playwright = await async_playwright().start()
            
            # Configurações stealth para o Chromium
            browser_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--disable-javascript-harmony-shipping',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-hang-monitor',
                '--disable-prompt-on-repost',
                '--disable-domain-reliability',
                '--disable-component-extensions-with-background-pages',
                '--disable-features=VizDisplayCompositor',
                '--disable-software-rasterizer',
                '--disable-background-networking',
                '--disable-sync',
                '--metrics-recording-only',
                '--no-report-upload',
                '--disable-web-security'
            ]
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
            
            # Cria contexto com configurações stealth
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
                extra_http_headers={
                    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            # Cria página
            self.page = await context.new_page()
            
            # Configurações adicionais de stealth
            await self.page.add_init_script("""
                // Remove propriedades que identificam automação
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Remove propriedades do Chrome
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Remove propriedades do Chrome
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en-US', 'en'],
                });
                
                // Simula movimento do mouse
                const originalQuery = window.document.querySelector;
                window.document.querySelector = function(...args) {
                    if (args[0] === 'body') {
                        // Simula movimento do mouse
                        const event = new MouseEvent('mousemove', {
                            clientX: Math.random() * window.innerWidth,
                            clientY: Math.random() * window.innerHeight
                        });
                        document.dispatchEvent(event);
                    }
                    return originalQuery.apply(this, args);
                };
            """)
            
            logger.info("✅ Navegador stealth configurado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar navegador stealth: {e}")
            return False
    
    async def close_browser(self):
        """Fecha o navegador Playwright"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("✅ Navegador stealth fechado")
        except Exception as e:
            logger.error(f"❌ Erro ao fechar navegador: {e}")
    
    async def wait_for_page_load(self, timeout: int = 30000):
        """Aguarda o carregamento da página com técnicas stealth"""
        try:
            # Aguarda o carregamento básico
            await self.page.wait_for_load_state('networkidle', timeout=timeout)
            
            # Aguarda um pouco mais para JavaScript carregar
            await asyncio.sleep(3)
            
            # Simula comportamento humano
            await self.simulate_human_behavior()
            
            return True
        except Exception as e:
            logger.warning(f"⚠️ Timeout aguardando carregamento da página: {e}")
            return False
    
    async def simulate_human_behavior(self):
        """Simula comportamento humano para evitar detecção"""
        try:
            # Simula movimento do mouse
            await self.page.mouse.move(
                x=100 + (time.time() % 100),
                y=100 + (time.time() % 100)
            )
            
            # Simula scroll natural
            await self.page.mouse.wheel(delta_y=100)
            await asyncio.sleep(0.5)
            await self.page.mouse.wheel(delta_y=-50)
            await asyncio.sleep(0.3)
            
            # Simula pequenas pausas
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.debug(f"Erro ao simular comportamento humano: {e}")
    
    async def scroll_page_stealth(self):
        """Faz scroll da página de forma stealth"""
        try:
            # Scroll suave e natural
            for i in range(3):
                await self.page.evaluate("""
                    window.scrollTo({
                        top: document.body.scrollHeight,
                        behavior: 'smooth'
                    });
                """)
                await asyncio.sleep(2)
                
                # Simula movimento do mouse durante scroll
                await self.page.mouse.move(
                    x=200 + (i * 100),
                    y=300 + (i * 50)
                )
            
            # Volta ao topo suavemente
            await self.page.evaluate("""
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            """)
            await asyncio.sleep(2)
            
            logger.info("✅ Scroll stealth da página realizado")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao fazer scroll stealth: {e}")
            return False
    
    async def extract_product_info(self, product_element) -> Optional[Dict]:
        """Extrai informações de um produto de forma stealth"""
        try:
            # Extrai título - tenta diferentes seletores
            titulo = None
            titulo_selectors = [
                'h2', 'h3', 'h4', 
                '[data-testid="product-title"]',
                '.product-title',
                '.product-name',
                '[class*="title"]',
                '[class*="name"]'
            ]
            
            for selector in titulo_selectors:
                try:
                    titulo_elem = await product_element.query_selector(selector)
                    if titulo_elem:
                        titulo_text = await titulo_elem.text_content()
                        if titulo_text and len(titulo_text.strip()) > 10:
                            titulo = titulo_text.strip()
                            break
                except Exception:
                    continue
            
            if not titulo:
                # Fallback: extrai todo o texto e procura por linhas que pareçam títulos
                try:
                    full_text = await product_element.text_content()
                    if full_text:
                        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                        for line in lines:
                            if len(line) > 10 and not any(word in line.lower() for word in ['r$', 'reais', 'preço', 'price']):
                                titulo = line
                                break
                except Exception:
                    pass
            
            if not titulo:
                return None
            
            # Extrai preço - tenta diferentes seletores
            preco = None
            preco_selectors = [
                '[data-testid="price"]',
                '[class*="price"]',
                '.a-price-whole',
                'span[class*="price"]',
                'div[class*="price"]'
            ]
            
            for selector in preco_selectors:
                try:
                    preco_elem = await product_element.query_selector(selector)
                    if preco_elem:
                        preco_text = await preco_elem.text_content()
                        if preco_text:
                            # Procura por padrões de preço
                            preco_match = re.search(r'R?\$?\s*([\d.,]+)', preco_text, re.IGNORECASE)
                            if preco_match:
                                preco = preco_match.group(1)
                                break
                except Exception:
                    continue
            
            if not preco:
                # Fallback: procura por qualquer texto que contenha números e R$
                try:
                    full_text = await product_element.text_content()
                    if full_text:
                        preco_match = re.search(r'R?\$?\s*([\d.,]+)', full_text, re.IGNORECASE)
                        if preco_match:
                            preco = preco_match.group(1)
                except Exception:
                    pass
            
            # Extrai link
            link = None
            try:
                link_elem = await product_element.query_selector('a[href*="/dp/"]')
                if link_elem:
                    link = await link_elem.get_attribute('href')
                    if link and not link.startswith('http'):
                        link = urljoin(self.base_url, link)
            except Exception:
                pass
            
            # Extrai imagem
            imagem = None
            try:
                img_elem = await product_element.query_selector('img')
                if img_elem:
                    imagem = await img_elem.get_attribute('src')
            except Exception:
                pass
            
            # Extrai desconto
            desconto = None
            try:
                desconto_elem = await product_element.query_selector('[class*="discount"], [class*="off"], .a-badge-text')
                if desconto_elem:
                    desconto_text = await desconto_elem.text_content()
                    if desconto_text:
                        desconto_match = re.search(r'(\d+)%?', desconto_text)
                        if desconto_match:
                            desconto = int(desconto_match.group(1))
            except Exception:
                pass
            
            # Se não encontrou desconto, tenta extrair do texto completo
            if not desconto:
                try:
                    full_text = await product_element.text_content()
                    if full_text:
                        desconto_match = re.search(r'(\d+)%?\s*off|\-(\d+)%?|(\d+)%?\s*desconto', full_text, re.IGNORECASE)
                        if desconto_match:
                            desconto = int(desconto_match.group(1) or desconto_match.group(2) or desconto_match.group(3))
                except Exception:
                    pass
            
            if titulo and preco:
                return {
                    'titulo': titulo,
                    'preco': preco,
                    'link': link,
                    'imagem': imagem,
                    'desconto': desconto,
                    'loja': 'Amazon Brasil',
                    'categoria': 'Ofertas do Dia'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair informações do produto: {e}")
            return None
    
    async def buscar_ofertas(self, max_paginas: int = 3) -> List[Dict]:
        """Busca ofertas da Amazon Brasil de forma stealth"""
        ofertas = []
        
        try:
            if not await self.setup_browser():
                return ofertas
            
            logger.info(f"🔍 Acessando de forma stealth: {self.ofertas_url}")
            
            # Acessa a página com técnicas stealth
            await self.page.goto(self.ofertas_url, wait_until='networkidle')
            
            if not await self.wait_for_page_load():
                logger.warning("⚠️ Página não carregou completamente")
            
            # Faz scroll stealth
            await self.scroll_page_stealth()
            
            # Procura por produtos
            logger.info("🔍 Procurando por produtos de forma stealth...")
            
            # Tenta diferentes seletores
            product_selectors = [
                '[data-testid="product-card"]',
                'div[class*="product"]',
                'div[class*="deal"]',
                'div[class*="card"]',
                '.product-card',
                '.deal-card'
            ]
            
            produtos_encontrados = []
            for selector in product_selectors:
                try:
                    produtos = await self.page.query_selector_all(selector)
                    if produtos:
                        produtos_encontrados = produtos
                        logger.info(f"✅ Encontrados {len(produtos)} produtos com seletor: {selector}")
                        break
                except Exception:
                    continue
            
            if not produtos_encontrados:
                # Fallback: procura por links de produto
                try:
                    links_produto = await self.page.query_selector_all('a[href*="/dp/"]')
                    if links_produto:
                        # Agrupa por produto pai
                        produtos_encontrados = []
                        for link in links_produto:
                            try:
                                produto_pai = await link.query_selector('xpath=./ancestor::*[contains(@class, "card") or contains(@class, "item") or contains(@class, "product") or contains(@class, "deal")]')
                                if produto_pai and produto_pai not in produtos_encontrados:
                                    produtos_encontrados.append(produto_pai)
                            except Exception:
                                continue
                        logger.info(f"✅ Encontrados {len(produtos_encontrados)} produtos via fallback")
                except Exception as e:
                    logger.warning(f"⚠️ Fallback falhou: {e}")
            
            # Extrai informações dos produtos
            if produtos_encontrados:
                logger.info(f"📋 Extraindo informações de {len(produtos_encontrados)} produtos...")
                
                for i, produto in enumerate(produtos_encontrados):
                    try:
                        info_produto = await self.extract_product_info(produto)
                        if info_produto:
                            ofertas.append(info_produto)
                            logger.info(f"✅ Produto {i+1}: {info_produto['titulo'][:50]}...")
                        else:
                            logger.warning(f"⚠️ Produto {i+1}: Não foi possível extrair informações")
                    except Exception as e:
                        logger.error(f"❌ Erro ao processar produto {i+1}: {e}")
                        continue
                    
                    # Limita o número de produtos
                    if len(ofertas) >= 50:
                        logger.info("🛑 Limite de 50 produtos atingido")
                        break
                    
                    # Pausa entre produtos para simular comportamento humano
                    await asyncio.sleep(0.1)
            
            logger.info(f"🎯 Total de ofertas extraídas: {len(ofertas)}")
            
        except Exception as e:
            logger.error(f"❌ Erro geral na busca de ofertas: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.close_browser()
        
        return ofertas

async def main():
    """Função principal para teste"""
    scraper = AmazonStealthScraper(headless=False)  # False para debug
    ofertas = await scraper.buscar_ofertas()
    
    print(f"\n🎯 RESULTADO: {len(ofertas)} ofertas encontradas")
    print("=" * 60)
    
    for i, oferta in enumerate(ofertas[:5], 1):
        print(f"\n{i}. {oferta['titulo']}")
        print(f"   💰 Preço: {oferta['preco']}")
        if oferta.get('desconto'):
            print(f"   🏷️ Desconto: {oferta['desconto']}%")
        print(f"   🔗 Link: {oferta.get('link', 'N/A')}")
        print(f"   🏪 Loja: {oferta['loja']}")

if __name__ == "__main__":
    asyncio.run(main())
