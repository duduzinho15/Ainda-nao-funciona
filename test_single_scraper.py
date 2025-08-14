"""
Script para testar os scrapers individualmente com logging detalhado.
"""
import logging
import sys
import traceback
from urllib.parse import urlparse
from product_scraper import (
    extract_product_info,
    extract_magalu_product,
    extract_amazon_product,
    extract_mercado_livre_product,
    extract_aliexpress_product,
    extract_shopee_product,
    make_request,
    ProductInfo
)

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('single_scraper_test.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('single_scraper_test')

def test_extractor(url: str, extractor_func):
    """Testa um extrator específico com uma URL."""
    logger.info(f"\n{'='*80}")
    logger.info(f"🔍 Testando extrator para: {url}")
    logger.info(f"Extrator: {extractor_func.__name__}")
    logger.info(f"{'='*80}")
    
    try:
        # Faz a requisição
        response = make_request(url)
        if not response or not response.content:
            logger.error("Falha ao carregar a página")
            return None
        
        # Faz o parse do HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extrai as informações
        product_info = extractor_func(soup, url)
        
        # Exibe os resultados
        if product_info:
            logger.info("✅ Extração bem-sucedida!")
            logger.info(f"Título: {getattr(product_info, 'title', 'N/A')}")
            logger.info(f"Preço: {getattr(product_info, 'price', 'N/A')}")
            logger.info(f"Preço Original: {getattr(product_info, 'original_price', 'N/A')}")
            logger.info(f"Imagem: {getattr(product_info, 'image_url', 'N/A')}")
            logger.info(f"Disponível: {getattr(product_info, 'available', 'N/A')}")
            logger.info(f"Desconto: {getattr(product_info, 'discount', 'N/A')}%")
        else:
            logger.warning("❌ Falha na extração: Nenhuma informação extraída")
        
        return product_info
        
    except Exception as e:
        logger.error(f"❌ Erro durante a extração: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def main():
    # Dicionário de URLs e seus respectivos extratores
    test_cases = [
        {
            'name': 'Amazon',
            'url': 'https://www.amazon.com.br/PHILIPS-TAT1109BK-00-Bluetooth-Microfone/dp/B0DVMQVVDY',
            'extractor': extract_amazon_product
        },
        {
            'name': 'AliExpress',
            'url': 'https://pt.aliexpress.com/item/1005009463783046.html',
            'extractor': extract_aliexpress_product
        },
        {
            'name': 'Mercado Livre',
            'url': 'https://www.mercadolivre.com.br/smart-tv-samsung-u8100f-crystal-uhd-4k-2025-43-preto/p/MLB49740322',
            'extractor': extract_mercado_livre_product
        },
        {
            'name': 'Shopee',
            'url': 'https://shopee.com.br/Meias-Divertidas-de-Personagens-em-Algod%C3%A3o-Unissex-i.441370953.22797653349',
            'extractor': extract_shopee_product
        },
        {
            'name': 'Magazine Luiza',
            'url': 'https://www.magazinevoce.com.br/magazinegarimpeirogeek/apple-iphone-14-128gb-estelar-61-12mp-ios-5g/p/237184100/te/ip14/',
            'extractor': extract_magalu_product
        }
    ]
    
    # Testa cada caso
    for case in test_cases:
        logger.info(f"\n{'#'*80}")
        logger.info(f"🚀 INICIANDO TESTE: {case['name']}")
        logger.info(f"URL: {case['url']}")
        logger.info(f"{'#'*80}")
        
        # Testa o extrator específico
        test_extractor(case['url'], case['extractor'])
        
        # Aguarda um pouco entre os testes
        if case != test_cases[-1]:
            import time
            time.sleep(3)
    
    logger.info("\n🎉 Todos os testes foram concluídos!")

if __name__ == "__main__":
    main()
