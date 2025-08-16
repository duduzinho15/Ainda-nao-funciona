#!/usr/bin/env python3
"""
Scraper da Shopee usando Playwright - Versão Otimizada
Herdando da classe base para máxima eficiência
"""

import asyncio
import logging
from base_playwright_scraper import BasePlaywrightScraper

# Configuração de logging
logger = logging.getLogger(__name__)

class ShopeePlaywrightScraper(BasePlaywrightScraper):
    """Scraper da Shopee usando Playwright para máxima eficiência"""
    
    def __init__(self, headless: bool = True):
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
        
        # Seletores específicos da Shopee
        self.product_selectors = [
            '[data-sqe="name"]',
            '.ie3A\\+n',
            '[class*="shopee-search-item-result"]',
            '[class*="item"]',
            '[class*="product"]',
            '[class*="card"]'
        ]
        
        self.title_selectors = [
            '[data-sqe="name"]',
            '.ie3A\\+n',
            '[class*="title"]',
            '[class*="name"]',
            'h1', 'h2', 'h3', 'h4'
        ]
        
        self.price_selectors = [
            '[class*="price"]',
            '.price',
            '[class*="cost"]',
            '[class*="value"]'
        ]
        
        self.link_selectors = [
            'a[href*="/product/"]',
            'a[href*="/item/"]'
        ]
        
        self.image_selectors = [
            'img'
        ]
        
        self.discount_selectors = [
            '[class*="discount"]',
            '[class*="off"]',
            '.badge',
            '[class*="badge"]'
        ]
    
    async def buscar_ofertas_gerais(self):
        """Busca ofertas gerais de todas as categorias"""
        todas_ofertas = []
        
        if not await self.setup_browser():
            logger.error("❌ Não foi possível configurar o navegador")
            return []
        
        try:
            logger.info("🚀 INICIANDO BUSCA DE OFERTAS NA SHOPEE COM PLAYWRIGHT")
            logger.info("=" * 60)
            
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
    print("🚀 TESTANDO SHOPEE SCRAPER COM PLAYWRIGHT")
    print("=" * 60)
    
    scraper = ShopeePlaywrightScraper(headless=True)
    
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
        filename = scraper.save_results(ofertas, "ofertas_shopee_playwright")
        if filename:
            print(f"\n💾 Ofertas salvas em: {filename}")

if __name__ == "__main__":
    asyncio.run(main())
