#!/usr/bin/env python3
"""
Sistema Unificado de Produtos
Integra com múltiplas lojas para obter dados reais
"""

import requests
import time
import logging
import json
from typing import Optional, Dict, Any, List
import random
from urllib.parse import urlparse

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedProductSystem:
    """Sistema unificado para obter dados reais de produtos de múltiplas lojas"""
    
    def __init__(self):
        self.session = requests.Session()
        
        # Headers padrão
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        
        # APIs das lojas
        self.amazon_api = "https://www.amazon.com.br/dp/"
        self.magalu_api = "https://www.magazineluiza.com.br/"
        self.ali_api = "https://pt.aliexpress.com/item/"
        
    def _add_delay(self):
        """Adiciona delay aleatório"""
        time.sleep(random.uniform(1, 2))
    
    def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """Extrai detalhes do produto de qualquer loja"""
        try:
            logger.info(f"🔍 Extraindo detalhes: {product_url}")
            
            # Identifica a loja pela URL
            domain = urlparse(product_url).netloc.lower()
            
            if 'amazon' in domain:
                return self._get_amazon_product(product_url)
            elif 'magazineluiza' in domain or 'magalu' in domain:
                return self._get_magalu_product(product_url)
            elif 'aliexpress' in domain:
                return self._get_aliexpress_product(product_url)
            elif 'shopee' in domain:
                return self._get_shopee_fallback(product_url)
            else:
                logger.warning(f"⚠️ Loja não suportada: {domain}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao extrair detalhes: {e}")
            return None
    
    def _get_amazon_product(self, product_url: str) -> Optional[Dict[str, Any]]:
        """Extrai dados de produtos da Amazon"""
        try:
            logger.info("   🏪 Processando produto da Amazon")
            
            # Extrai ASIN da URL
            asin = self._extract_amazon_asin(product_url)
            if not asin:
                logger.warning("   ⚠️ Não foi possível extrair ASIN da Amazon")
                return None
            
            logger.info(f"   📊 ASIN: {asin}")
            
            # 1. TENTATIVA: API de busca da Amazon
            search_result = self._search_amazon_by_asin(asin)
            if search_result:
                logger.info(f"   ✅ Dados extraídos via busca: {search_result.get('title', 'N/A')}")
                return search_result
            
            # 2. TENTATIVA: Scraping da página
            page_result = self._scrape_amazon_page(product_url)
            if page_result:
                logger.info(f"   ✅ Dados extraídos via scraping: {page_result.get('title', 'N/A')}")
                return page_result
            
            logger.warning("   ⚠️ Falha na extração da Amazon")
            return None
            
        except Exception as e:
            logger.debug(f"Erro na Amazon: {e}")
            return None
    
    def _extract_amazon_asin(self, product_url: str) -> Optional[str]:
        """Extrai ASIN da URL da Amazon"""
        try:
            # Formato: https://www.amazon.com.br/dp/B08N5WRWNW
            if '/dp/' in product_url:
                asin = product_url.split('/dp/')[1].split('/')[0].split('?')[0]
                return asin
            return None
        except:
            return None
    
    def _search_amazon_by_asin(self, asin: str) -> Optional[Dict[str, Any]]:
        """Busca produto da Amazon por ASIN"""
        try:
            self._add_delay()
            
            # API de busca da Amazon (simulada)
            search_url = f"https://www.amazon.com.br/dp/{asin}"
            
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                # Extrai dados da página
                return self._parse_amazon_response(response.text, asin)
            
            return None
            
        except Exception as e:
            logger.debug(f"Erro na busca Amazon: {e}")
            return None
    
    def _scrape_amazon_page(self, product_url: str) -> Optional[Dict[str, Any]]:
        """Scraping da página da Amazon"""
        try:
            self._add_delay()
            
            response = self.session.get(product_url, timeout=15)
            
            if response.status_code == 200:
                return self._parse_amazon_response(response.text)
            
            return None
            
        except Exception as e:
            logger.debug(f"Erro no scraping Amazon: {e}")
            return None
    
    def _parse_amazon_response(self, html_content: str, asin: str = None) -> Optional[Dict[str, Any]]:
        """Parse da resposta da Amazon"""
        try:
            data = {}
            
            # Título - múltiplas estratégias
            title_patterns = [
                r'<title[^>]*>([^<]+)</title>',
                r'<h1[^>]*id="title"[^>]*>([^<]+)</h1>',
                r'<span[^>]*id="productTitle"[^>]*>([^<]+)</span>'
            ]
            
            for pattern in title_patterns:
                import re
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if title and len(title) > 5:
                        data['title'] = title
                        break
            
            # Imagem - múltiplas estratégias
            image_patterns = [
                r'<img[^>]*id="landingImage"[^>]*src="([^"]+)"',
                r'<img[^>]*id="imgBlkFront"[^>]*src="([^"]+)"',
                r'<img[^>]*data-old-hires="([^"]+)"'
            ]
            
            for pattern in image_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    image_url = match.group(1).strip()
                    if image_url and image_url.startswith('http'):
                        data['image_url'] = image_url
                        break
            
            # ASIN
            if asin:
                data['asin'] = asin
            
            # Loja
            data['store'] = 'Amazon'
            
            return data if data.get('title') else None
            
        except Exception as e:
            logger.debug(f"Erro no parse Amazon: {e}")
            return None
    
    def _get_magalu_product(self, product_url: str) -> Optional[Dict[str, Any]]:
        """Extrai dados de produtos da Magazine Luiza"""
        try:
            logger.info("   🏪 Processando produto da Magazine Luiza")
            
            # Scraping da página
            self._add_delay()
            
            response = self.session.get(product_url, timeout=15)
            
            if response.status_code == 200:
                return self._parse_magalu_response(response.text)
            
            return None
            
        except Exception as e:
            logger.debug(f"Erro na Magazine Luiza: {e}")
            return None
    
    def _parse_magalu_response(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Parse da resposta da Magazine Luiza"""
        try:
            data = {}
            
            # Título
            import re
            title_patterns = [
                r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h1>',
                r'<h1[^>]*>([^<]+)</h1>',
                r'<title[^>]*>([^<]+)</title>'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if title and len(title) > 5:
                        data['title'] = title
                        break
            
            # Imagem
            image_patterns = [
                r'<img[^>]*class="[^"]*image[^"]*"[^>]*src="([^"]+)"',
                r'<img[^>]*data-src="([^"]+)"',
                r'<img[^>]*src="([^"]+)"'
            ]
            
            for pattern in image_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    image_url = match.group(1).strip()
                    if image_url and image_url.startswith('http'):
                        data['image_url'] = image_url
                        break
            
            # Loja
            data['store'] = 'Magazine Luiza'
            
            return data if data.get('title') else None
            
        except Exception as e:
            logger.debug(f"Erro no parse Magazine Luiza: {e}")
            return None
    
    def _get_aliexpress_product(self, product_url: str) -> Optional[Dict[str, Any]]:
        """Extrai dados de produtos do AliExpress"""
        try:
            logger.info("   🏪 Processando produto do AliExpress")
            
            # Scraping da página
            self._add_delay()
            
            response = self.session.get(product_url, timeout=15)
            
            if response.status_code == 200:
                return self._parse_aliexpress_response(response.text)
            
            return None
            
        except Exception as e:
            logger.debug(f"Erro no AliExpress: {e}")
            return None
    
    def _parse_aliexpress_response(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Parse da resposta do AliExpress"""
        try:
            data = {}
            
            # Título
            import re
            title_patterns = [
                r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h1>',
                r'<title[^>]*>([^<]+)</title>',
                r'<h1[^>]*>([^<]+)</h1>'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if title and len(title) > 5:
                        data['title'] = title
                        break
            
            # Imagem
            image_patterns = [
                r'<img[^>]*class="[^"]*image[^"]*"[^>]*src="([^"]+)"',
                r'<img[^>]*data-src="([^"]+)"',
                r'<img[^>]*src="([^"]+)"'
            ]
            
            for pattern in image_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    image_url = match.group(1).strip()
                    if image_url and image_url.startswith('http'):
                        data['image_url'] = image_url
                        break
            
            # Loja
            data['store'] = 'AliExpress'
            
            return data if data.get('title') else None
            
        except Exception as e:
            logger.debug(f"Erro no parse AliExpress: {e}")
            return None
    
    def _get_shopee_fallback(self, product_url: str) -> Optional[Dict[str, Any]]:
        """Fallback para produtos da Shopee"""
        try:
            logger.info("   🏪 Processando produto da Shopee (fallback)")
            
            # Extrai IDs do produto
            if '/product/' in product_url:
                parts = product_url.split('/product/')[1].split('/')
                if len(parts) >= 2:
                    shop_id = parts[0]
                    item_id = parts[1]
                    
                    data = {
                        'title': f"Produto Shopee #{item_id}",
                        'image_url': None,  # Shopee bloqueia imagens
                        'store': 'Shopee',
                        'shop_id': shop_id,
                        'item_id': item_id
                    }
                    
                    logger.info(f"   📊 Fallback criado: {data['title']}")
                    return data
            
            return None
            
        except Exception as e:
            logger.debug(f"Erro no fallback Shopee: {e}")
            return None
    
    def test_image_url(self, image_url: str) -> bool:
        """Testa se a URL da imagem é válida"""
        try:
            response = self.session.head(image_url, timeout=10)
            return response.status_code == 200
        except:
            return False

def main():
    """Teste do sistema unificado"""
    print("🧪 TESTANDO SISTEMA UNIFICADO DE PRODUTOS")
    print("=" * 60)
    
    system = UnifiedProductSystem()
    
    # URLs de teste de diferentes lojas
    test_urls = [
        'https://www.amazon.com.br/dp/B08N5WRWNW',  # Amazon
        'https://www.magazineluiza.com.br/smartphone-samsung-galaxy-a15-128gb-4g-octa-core-4gb-ram-65-cam-tripla-selfie-13mp-dual-chip/p/235579800/te/ga15/',  # Magazine Luiza
        'https://pt.aliexpress.com/item/1005009463783046.html',  # AliExpress
        'https://shopee.com.br/product/366295833/18297606894'  # Shopee (fallback)
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🔍 Teste {i}: {url}")
        
        try:
            result = system.get_product_details(url)
            
            if result:
                print(f"   ✅ Título: {result.get('title', 'N/A')}")
                print(f"   ✅ Imagem: {result.get('image_url', 'N/A')}")
                print(f"   ✅ Loja: {result.get('store', 'N/A')}")
                
                # Testa a URL da imagem
                if result.get('image_url'):
                    is_valid = system.test_image_url(result['image_url'])
                    print(f"   🖼️ Imagem válida: {'✅ Sim' if is_valid else '❌ Não'}")
            else:
                print(f"   ❌ Falha na extração")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        print("-" * 40)
        
        # Pausa entre testes
        if i < len(test_urls):
            time.sleep(2)

if __name__ == "__main__":
    main()
