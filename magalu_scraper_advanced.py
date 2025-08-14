"""
Scraper Avançado para o Magazine Luiza - Multi-categoria e Multi-página
"""
import asyncio
import time
import logging
import re
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse, parse_qs
from playwright.async_api import async_playwright, Browser, Page

# Importa o sistema de logging centralizado
from logger_config import get_logger, log_scraping_start, log_scraping_complete, log_product_found, log_error, log_info, log_warning

# Configuração de logging
logger = get_logger("magalu_advanced")

class MagazineLuizaAdvancedScraper:
    """Scraper avançado para o Magazine Luiza com suporte a múltiplas categorias e páginas"""
    
    def __init__(self, headless: bool = True):
        self.base_url = "https://www.magazinevoce.com.br/magazinegarimpeirogeek"
        self.headless = headless
        self.browser = None
        self.page = None
        
        # Categorias principais para scraping
        self.categorias = {
            'ofertas_gerais': [
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/selecao/ofertasdodia/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/selecao/im_achadinhosdoinflu180325/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/selecao/im_android_0108/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/selecao/im_ed1_0108/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/selecao/110825_smartphones/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/selecao/110825_portateis/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/selecao/110825_ar/'
            ],
            'informatica': [
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/informatica/l/in/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/macbook/informatica/s/in/mack/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/imac/informatica/s/in/ifim/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/notebook/informatica/s/in/note/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/computador-desktop/informatica/s/in/cptd/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/tablets-ipads-e-e-reader/l/tb/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/monitores/informatica/s/in/mlcd/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/roteador/informatica/s/in/rtdr/brand---tp-link/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/hd-externo/informatica/s/in/hdex/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/notebook-gamer/informatica/s/in/ntbg/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/computador-gamer/informatica/s/in/cptg/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/monitor-gamer/informatica/s/in/mogm/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/gabinete-gamer/informatica/s/in/gbgm/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/mouse-gamer/informatica/s/in/mger/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/teclado-gamer/informatica/s/in/tcdg/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/placa-de-video/informatica/s/in/pcvd/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/placa-mae/informatica/s/in/pmae/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/processador/informatica/s/in/prsd/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/teclado/informatica/s/in/tcld/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/mouse/informatica/s/in/rato/'
            ],
            'componentes_pc': [
                # Novas categorias de componentes
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/memoria-ram/informatica/s/in/mram/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/hd-ssd/informatica/s/in/ssdi/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/fonte-para-pc/informatica/s/in/ftpc/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/fonte-gamer-para-pc/informatica/s/in/fgpc/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/water-cooler/informatica/s/in/waco/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/keycaps-teclas-para-teclado/informatica/s/in/keyc/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/placa-de-rede/informatica/s/in/plcr/'
            ],
            'setup_gamer': [
                # Cadeiras e mesas gamer - URLs corrigidas
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/escritorio/cadeira-de-escritorio/s/es/cegr/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/escritorio/mesa-de-escritorio/s/es/mesc/'
            ],
            'tv_video': [
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/tv-e-video/l/et/'
            ],
            'games': [
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/games/l/ga/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/colecionaveis/games/s/ga/cois/'
            ],
            'cultura_geek': [
                # URLs corrigidas para categorias que funcionam
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/livros/l/ld/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/busca/hq+quadrinhos/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/busca/camiseta+geek/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/marcas/decora-geek/'
            ],
            'cultura_tech': [
                # URLs corrigidas para categorias que funcionam
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/relogios-e-smartwatches/relogios/s/es/resw/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/casa-inteligente/automacao-residencial/s/au/cain/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/busca/drone/'
            ],
            'audio_acessorios': [
                # URLs corrigidas para categorias que funcionam
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/busca/fone+de+ouvido+bluetooth/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/audio/caixa-de-som/s/ea/csom/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/celulares-e-smartphones/acessorios-para-celular/carregador-e-power-bank/s/te/acpb/'
            ],
            'consoles_games': [
                # URLs para consoles e jogos
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/games/console/s/ga/cons/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/games/jogos/s/ga/jogo/',
                'https://www.magazinevoce.com.br/magazinevoce.com.br/magazinegarimpeirogeek/games/acessorios/s/ga/aces/'
            ],
            'smartphones': [
                # URLs para smartphones e acessórios
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/celulares-e-smartphones/l/te/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/celulares-e-smartphones/smartphone/s/te/smar/',
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/celulares-e-smartphones/acessorios-para-celular/s/te/aces/'
            ]
            ],
            'aliexpress': [
                'https://www.magazinevoce.com.br/magazinegarimpeirogeek/lojista/aliexpress/'
            ]
        }
        
        # Produtos já encontrados para evitar duplicatas
        self.produtos_encontrados: Set[str] = set()
        
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
    
    def get_next_page_url(self, current_url: str, page: int) -> str:
        """Gera URL da próxima página"""
        try:
            if '?' in current_url:
                # URL já tem parâmetros
                if 'page=' in current_url:
                    # Substitui o número da página
                    return re.sub(r'page=\d+', f'page={page}', current_url)
                else:
                    # Adiciona parâmetro de página
                    return f"{current_url}&page={page}"
            else:
                # URL não tem parâmetros
                return f"{current_url}?page={page}"
        except Exception:
            return current_url
    
    async def check_pagination(self) -> int:
        """Verifica quantas páginas existem na categoria atual"""
        try:
            # Procura por elementos de paginação
            pagination_selectors = [
                '.pagination',
                '[class*="pagination"]',
                '[class*="page"]',
                'nav[class*="pagination"]'
            ]
            
            for selector in pagination_selectors:
                try:
                    pagination = await self.page.query_selector(selector)
                    if pagination:
                        # Procura por números de página
                        page_numbers = await pagination.query_selector_all('a, button, span')
                        max_page = 1
                        
                        for elem in page_numbers:
                            try:
                                text = await elem.text_content()
                                if text and text.isdigit():
                                    page_num = int(text)
                                    max_page = max(max_page, page_num)
                            except Exception:
                                continue
                        
                        if max_page > 1:
                            logger.info(f"📄 Paginação encontrada: {max_page} páginas")
                            return max_page
                        break
                except Exception:
                    continue
            
            # Fallback: procura por padrões de URL na página
            try:
                page_content = await self.page.content()
                page_matches = re.findall(r'page=(\d+)', page_content)
                if page_matches:
                    max_page = max(int(p) for p in page_matches)
                    logger.info(f"📄 Paginação detectada via URL: {max_page} páginas")
                    return max_page
            except Exception:
                pass
            
            logger.info("📄 Paginação não encontrada, assumindo 1 página")
            return 1
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar paginação: {e}")
            return 1
    
    async def extract_product_info(self, product_element, categoria: str) -> Optional[Dict]:
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
                '[data-testid="price-value"]',
                '.price-value',
                '.price',
                '[class*="price"]',
                '[class*="cost"]',
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
                link_elem = await product_element.query_selector('a[href*="/p/"]')
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
                desconto_elem = await product_element.query_selector('[class*="discount"], [class*="off"], [class*="badge"]')
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
                # Cria chave única para evitar duplicatas
                product_key = f"{titulo}_{preco}_{categoria}"
                
                if product_key not in self.produtos_encontrados:
                    self.produtos_encontrados.add(product_key)
                    
                    # Log do produto encontrado
                    log_product_found('Magazine Luiza', titulo, preco, str(desconto) if desconto else None)
                    
                    return {
                        'titulo': titulo,
                        'preco': preco,
                        'link': link,
                        'imagem': imagem,
                        'desconto': desconto,
                        'loja': 'Magazine Luiza',
                        'categoria': categoria
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair informações do produto: {e}")
            return None
    
    async def scrape_category_page(self, url: str, categoria: str, max_paginas: int = 5) -> List[Dict]:
        """Scrapa uma categoria específica com múltiplas páginas"""
        ofertas = []
        
        try:
            logger.info(f"🔍 Acessando categoria: {categoria} - {url}")
            
            # Acessa a primeira página
            await self.page.goto(url, wait_until='networkidle')
            
            if not await self.wait_for_page_load():
                logger.warning("⚠️ Página não carregou completamente")
            
            # Verifica quantas páginas existem
            total_paginas = await self.check_pagination()
            paginas_para_scraping = min(max_paginas, total_paginas)
            
            logger.info(f"📄 Scrapando {paginas_para_scraping} de {total_paginas} páginas")
            
            for pagina in range(1, paginas_para_scraping + 1):
                try:
                    if pagina > 1:
                        # Navega para a próxima página
                        next_url = self.get_next_page_url(url, pagina)
                        logger.info(f"📄 Navegando para página {pagina}: {next_url}")
                        
                        await self.page.goto(next_url, wait_until='networkidle')
                        await asyncio.sleep(2)
                    
                    # Faz scroll stealth
                    await self.scroll_page_stealth()
                    
                    # Procura por produtos
                    logger.info(f"🔍 Procurando por produtos na página {pagina}...")
                    
                    # Tenta diferentes seletores
                    product_selectors = [
                        '[data-testid="product-card-container"]',
                        'li[class*="product"]',
                        'div[class*="product"]',
                        'article[class*="product"]',
                        '.product-card',
                        '.product-item'
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
                            links_produto = await self.page.query_selector_all('a[href*="/p/"]')
                            if links_produto:
                                # Agrupa por produto pai
                                produtos_encontrados = []
                                for link in links_produto:
                                    try:
                                        produto_pai = await link.query_selector('xpath=./ancestor::*[contains(@class, "card") or contains(@class, "item") or contains(@class, "product")]')
                                        if produto_pai and produto_pai not in produtos_encontrados:
                                            produtos_encontrados.append(produto_pai)
                                    except Exception:
                                        continue
                                logger.info(f"✅ Encontrados {len(produtos_encontrados)} produtos via fallback")
                        except Exception as e:
                            logger.warning(f"⚠️ Fallback falhou: {e}")
                    
                    # Extrai informações dos produtos
                    if produtos_encontrados:
                        logger.info(f"📋 Extraindo informações de {len(produtos_encontrados)} produtos da página {pagina}...")
                        
                        for i, produto in enumerate(produtos_encontrados):
                            try:
                                info_produto = await self.extract_product_info(produto, categoria)
                                if info_produto:
                                    ofertas.append(info_produto)
                                    logger.info(f"✅ Produto {len(ofertas)}: {info_produto['titulo'][:50]}...")
                                else:
                                    logger.warning(f"⚠️ Produto {i+1} da página {pagina}: Não foi possível extrair informações")
                            except Exception as e:
                                logger.error(f"❌ Erro ao processar produto {i+1} da página {pagina}: {e}")
                                continue
                            
                            # Limita o número de produtos por categoria
                            if len(ofertas) >= 100:
                                logger.info("🛑 Limite de 100 produtos por categoria atingido")
                                break
                        
                        # Pausa entre páginas para simular comportamento humano
                        if pagina < paginas_para_scraping:
                            await asyncio.sleep(3)
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao processar página {pagina}: {e}")
                    continue
                
                # Verifica se atingiu o limite de produtos
                if len(ofertas) >= 100:
                    break
            
            logger.info(f"🎯 Categoria {categoria}: {len(ofertas)} ofertas extraídas")
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer scraping da categoria {categoria}: {e}")
        
        return ofertas
    
    async def scrape_all_categories(self, max_paginas_por_categoria: int = 3) -> List[Dict]:
        """Scrapa todas as categorias configuradas"""
        all_ofertas = []
        
        try:
            if not await self.setup_browser():
                return all_ofertas
            
            log_info("SCRAPING", f"Iniciando scraping de {len(self.categorias)} categorias")
            logger.info(f"🚀 Iniciando scraping de {len(self.categorias)} categorias")
            
            # Categorias em ordem de prioridade
            categorias_ordenadas = [
                ('ofertas_gerais', '🎯 Ofertas Gerais'),
                ('informatica', '💻 Informática'),
                ('componentes_pc', '🔧 Componentes PC'),
                ('setup_gamer', '🎮 Setup Gamer'),
                ('tv_video', '📺 TV e Vídeo'),
                ('games', '🎲 Games e Colecionáveis'),
                ('cultura_geek', '🌟 Cultura Geek'),
                ('cultura_tech', '📱 Cultura Tech'),
                ('audio_acessorios', '🎧 Áudio e Acessórios'),
                ('aliexpress', '🌐 AliExpress')
            ]
            
            for categoria_nome, categoria_display in categorias_ordenadas:
                if categoria_nome in self.categorias:
                    urls = self.categorias[categoria_nome]
                    log_scraping_start(categoria_display, len(urls))
                    logger.info(f"{categoria_display} - {len(urls)} URLs para processar")
                    
                    for i, url in enumerate(urls, 1):
                        try:
                            logger.info(f"  📍 URL {i}/{len(urls)}: {url.split('/')[-2] if url.split('/')[-1] == '' else url.split('/')[-1]}")
                            
                            ofertas_categoria = await self.scrape_category_page(
                                url, categoria_nome, max_paginas_por_categoria
                            )
                            
                            if ofertas_categoria:
                                all_ofertas.extend(ofertas_categoria)
                                log_info("SCRAPING", f"{categoria_display}: {len(ofertas_categoria)} ofertas extraídas da URL {i}")
                                logger.info(f"    ✅ {len(ofertas_categoria)} ofertas extraídas")
                            
                            # Pausa entre URLs da mesma categoria
                            if i < len(urls):
                                await asyncio.sleep(3)
                            
                        except Exception as e:
                            log_error(f"SCRAPING {categoria_display}", e, f"URL {i}: {url}")
                            logger.error(f"    ❌ Erro ao processar URL {url}: {e}")
                            continue
                    
                    log_scraping_complete(categoria_display, len([o for o in all_ofertas if o.get('categoria') == categoria_nome]), 0)
                    logger.info(f"✅ {categoria_display} concluída. Total acumulado: {len(all_ofertas)} ofertas")
                    
                    # Pausa entre categorias para evitar sobrecarga
                    if categoria_nome != 'aliexpress':  # Última categoria
                        await asyncio.sleep(5)
            
            log_info("SCRAPING", f"Scraping completo: {len(all_ofertas)} ofertas únicas de todas as categorias")
            logger.info(f"🎯 Scraping completo: {len(all_ofertas)} ofertas únicas de todas as categorias")
            
        except Exception as e:
            logger.error(f"❌ Erro geral no scraping de categorias: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.close_browser()
        
        return all_ofertas

async def main():
    """Função principal para teste"""
    scraper = MagazineLuizaAdvancedScraper(headless=True)  # True para produção
    
    print("🚀 INICIANDO SCRAPING AVANÇADO MULTI-CATEGORIA")
    print("=" * 60)
    print("📋 CATEGORIAS IMPLEMENTADAS:")
    print("  🎯 Ofertas Gerais (8 URLs)")
    print("  💻 Informática (19 URLs)")
    print("  🔧 Componentes PC (7 URLs)")
    print("  🎮 Setup Gamer (2 URLs)")
    print("  📺 TV e Vídeo (1 URL)")
    print("  🎲 Games e Colecionáveis (2 URLs)")
    print("  🌟 Cultura Geek (4 URLs)")
    print("  📱 Cultura Tech (3 URLs)")
    print("  🎧 Áudio e Acessórios (3 URLs)")
    print("  🌐 AliExpress (1 URL)")
    print("=" * 60)
    
    # Executa scraping de todas as categorias
    ofertas = await scraper.scrape_all_categories(max_paginas_por_categoria=2)
    
    print(f"\n🎯 RESULTADO FINAL: {len(ofertas)} ofertas únicas encontradas")
    print("=" * 60)
    
    # Mostra as melhores ofertas
    for i, oferta in enumerate(ofertas[:10], 1):
        print(f"\n{i}. {oferta['titulo'][:60]}...")
        print(f"   💰 Preço: {oferta['preco']}")
        if oferta.get('desconto'):
            print(f"   🏷️ Desconto: {oferta['desconto']}%")
        print(f"   🏪 Loja: {oferta['loja']}")
        print(f"   📂 Categoria: {oferta['categoria']}")
        if oferta.get('link'):
            print(f"   🔗 Link: {oferta['link']}")

if __name__ == "__main__":
    asyncio.run(main())
