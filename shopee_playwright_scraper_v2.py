#!/usr/bin/env python3
"""
Scraper da Shopee usando Playwright - Versão 2.0 com Debug
Seletores otimizados e análise detalhada da página
"""

import asyncio
import logging
import time
from base_playwright_scraper import BasePlaywrightScraper

# Configuração de logging
logger = logging.getLogger(__name__)

class ShopeePlaywrightScraperV2(BasePlaywrightScraper):
    """Scraper da Shopee usando Playwright - Versão 2.0 com Debug"""
    
    def __init__(self, headless: bool = False):  # Modo visível para debug
        super().__init__(
            base_url="https://shopee.com.br",
            store_name="Shopee Brasil",
            headless=headless
        )
        
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
        
        # Seletores atualizados da Shopee (baseados em análise real)
        self.product_selectors = [
            '[data-sqe="link"]',  # Container principal do produto
            '.shopee-search-item-result__item',  # Item de resultado
            '[class*="shopee-search-item-result"]',  # Classe genérica
            '[class*="item"]',  # Fallback genérico
            '[class*="product"]',  # Fallback genérico
            '[class*="card"]'  # Fallback genérico
        ]
        
        self.title_selectors = [
            '[data-sqe="name"]',  # Nome do produto
            '.ie3A\\+n',  # Classe específica da Shopee
            '[class*="title"]',  # Título genérico
            '[class*="name"]',  # Nome genérico
            'h1', 'h2', 'h3', 'h4'  # Headers como fallback
        ]
        
        self.price_selectors = [
            '.ie3A\\+n\\+b',  # Classe específica de preço da Shopee
            '[class*="price"]',  # Preço genérico
            '.price',  # Classe de preço
            '[class*="cost"]',  # Custo genérico
            '[class*="value"]'  # Valor genérico
        ]
        
        self.link_selectors = [
            'a[href*="/product/"]',  # Links de produto
            'a[href*="/item/"]',  # Links de item
            '[data-sqe="link"] a',  # Link dentro do container
            'a[href*="/"]'  # Qualquer link como fallback
        ]
        
        self.image_selectors = [
            'img[src*="shopee"]',  # Imagens da Shopee
            'img[data-src]',  # Imagens com data-src
            'img'  # Qualquer imagem como fallback
        ]
        
        self.discount_selectors = [
            '[class*="discount"]',  # Desconto genérico
            '[class*="off"]',  # Off genérico
            '.badge',  # Badge genérico
            '[class*="badge"]'  # Badge genérico
        ]
    
    async def debug_page_structure(self, categoria: str):
        """Debug: analisa a estrutura da página para encontrar seletores corretos"""
        try:
            logger.info(f"🔍 DEBUG: Analisando estrutura da página para {categoria}")
            
            # Constrói URL de busca
            search_url = f"{self.base_url}/search?keyword={categoria}&sortBy=sales&order=desc"
            
            # Acessa a página
            await self.page.goto(search_url, wait_until="networkidle")
            await asyncio.sleep(5)  # Aguarda carregamento completo
            
            # Faz scroll para carregar conteúdo dinâmico
            await self.scroll_page_smart(2.0)
            await asyncio.sleep(3)
            
            # Analisa elementos da página
            logger.info("🔍 DEBUG: Analisando elementos da página...")
            
            # Procura por containers de produto
            for i, selector in enumerate(self.product_selectors):
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        logger.info(f"✅ Selector {i+1} ({selector}): {len(elements)} elementos encontrados")
                        
                        # Analisa o primeiro elemento
                        if len(elements) > 0:
                            first_element = elements[0]
                            
                            # Tenta extrair informações básicas
                            try:
                                # Título
                                title_text = await first_element.text_content()
                                if title_text:
                                    logger.info(f"   📝 Texto do elemento: {title_text[:100]}...")
                                
                                # HTML interno
                                inner_html = await first_element.inner_html()
                                if inner_html:
                                    logger.info(f"   🏗️ HTML interno: {inner_html[:200]}...")
                                
                                # Classes
                                classes = await first_element.get_attribute('class')
                                if classes:
                                    logger.info(f"   🏷️ Classes: {classes}")
                                
                            except Exception as e:
                                logger.warning(f"   ⚠️ Erro ao analisar elemento: {e}")
                        
                        break
                    else:
                        logger.info(f"❌ Selector {i+1} ({selector}): 0 elementos")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erro com selector {i+1} ({selector}): {e}")
            
            # Procura por links de produto
            try:
                product_links = await self.page.query_selector_all('a[href*="/product/"], a[href*="/item/"]')
                logger.info(f"🔗 Links de produto encontrados: {len(product_links)}")
                
                if product_links:
                    for i, link in enumerate(product_links[:3]):  # Analisa os primeiros 3
                        try:
                            href = await link.get_attribute('href')
                            text = await link.text_content()
                            logger.info(f"   Link {i+1}: {href} | Texto: {text[:50]}...")
                        except Exception as e:
                            logger.warning(f"   ⚠️ Erro ao analisar link {i+1}: {e}")
                            
            except Exception as e:
                logger.warning(f"⚠️ Erro ao procurar links: {e}")
            
            # Procura por imagens
            try:
                images = await self.page.query_selector_all('img')
                logger.info(f"🖼️ Imagens encontradas: {len(images)}")
                
                if images:
                    for i, img in enumerate(images[:3]):  # Analisa as primeiras 3
                        try:
                            src = await img.get_attribute('src')
                            alt = await img.get_attribute('alt')
                            logger.info(f"   Imagem {i+1}: src={src[:50]}... | alt={alt[:30]}...")
                        except Exception as e:
                            logger.warning(f"   ⚠️ Erro ao analisar imagem {i+1}: {e}")
                            
            except Exception as e:
                logger.warning(f"⚠️ Erro ao procurar imagens: {e}")
            
            # Salva screenshot para análise visual
            screenshot_path = f"shopee_debug_{categoria}_{int(time.time())}.png"
            await self.page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"📸 Screenshot salvo: {screenshot_path}")
            
            # Salva HTML da página para análise
            html_content = await self.page.content()
            html_path = f"shopee_debug_{categoria}_{int(time.time())}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"📄 HTML salvo: {html_path}")
            
        except Exception as e:
            logger.error(f"❌ Erro no debug: {e}")
    
    async def buscar_ofertas_gerais(self):
        """Busca ofertas gerais de todas as categorias com debug"""
        todas_ofertas = []
        
        if not await self.setup_browser():
            logger.error("❌ Não foi possível configurar o navegador")
            return []
        
        try:
            logger.info("🚀 INICIANDO BUSCA DE OFERTAS NA SHOPEE COM PLAYWRIGHT V2.0")
            logger.info("=" * 60)
            
            # Testa apenas uma categoria para debug
            categoria_teste = "smartphone"
            logger.info(f"🔍 TESTE: Analisando apenas {categoria_teste} para debug")
            
            # Executa debug da estrutura da página
            await self.debug_page_structure(categoria_teste)
            
            # Aguarda input do usuário para continuar
            logger.info("⏸️ Pressione Enter para continuar com o scraping normal...")
            input()
            
            # Continua com o scraping normal
            for categoria in self.categorias:
                try:
                    logger.info(f"\n🔍 Buscando: {categoria.upper()}")
                    
                    # Constrói URL de busca
                    search_url = f"{self.base_url}/search?keyword={categoria}&sortBy=sales&order=desc"
                    
                    # Busca produtos usando método genérico
                    ofertas_categoria = await self.search_products_by_category(
                        categoria=categoria,
                        search_url=search_url,
                        product_selectors=self.product_selectors,
                        title_selectors=self.title_selectors,
                        price_selectors=self.price_selectors,
                        link_selectors=self.link_selectors,
                        image_selectors=self.image_selectors,
                        discount_selectors=self.discount_selectors
                    )
                    
                    todas_ofertas.extend(ofertas_categoria)
                    
                    # Delay entre categorias
                    await asyncio.sleep(self.get_random_delay(2, 4))
                    
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
            await self.close_browser()
        
        return todas_ofertas

async def main():
    """Função principal para teste"""
    print("🚀 TESTANDO SHOPEE SCRAPER COM PLAYWRIGHT V2.0 (DEBUG)")
    print("=" * 60)
    
    scraper = ShopeePlaywrightScraperV2(headless=False)  # Modo visível para debug
    
    # Testa conexão primeiro
    if not await scraper.test_connection():
        print("❌ Não foi possível conectar com a Shopee")
        return
    
    # Busca ofertas
    ofertas = await scraper.buscar_ofertas_gerais()
    
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
        filename = scraper.save_results(ofertas, "ofertas_shopee_playwright_v2")
        if filename:
            print(f"\n💾 Ofertas salvas em: {filename}")

if __name__ == "__main__":
    asyncio.run(main())
