"""
Script para testar especificamente o extrator do AliExpress.
"""
import logging
import sys
import json
from bs4 import BeautifulSoup
from product_scraper import extract_aliexpress_product, make_request

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('test_aliexpress')

def test_aliexpress_extractor(url):
    """Testa o extrator do AliExpress com uma URL específica."""
    logger.info(f"\n{'='*80}")
    logger.info(f"🔍 Testando extrator do AliExpress")
    logger.info(f"URL: {url}")
    logger.info(f"{'='*80}")
    
    try:
        # 1. Faz a requisição HTTP
        logger.info("Fazendo requisição HTTP...")
        response = make_request(url)
        
        if not response or not response.content:
            logger.error("Falha ao carregar a página")
            return None
            
        # 2. Faz o parse do HTML
        logger.info("Fazendo parse do HTML...")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 3. Salva o HTML para análise
        with open('aliexpress_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        logger.info("HTML da página salvo em 'aliexpress_page.html'")
        
        # 4. Tenta extrair dados do JSON-LD
        logger.info("Procurando por dados estruturados (JSON-LD)...")
        json_ld = soup.find('script', {'type': 'application/ld+json'})
        
        if json_ld:
            try:
                data = json.loads(json_ld.string)
                logger.info("Dados estruturados encontrados:")
                logger.info(json.dumps(data, indent=2, ensure_ascii=False))
            except Exception as e:
                logger.error(f"Erro ao analisar JSON-LD: {e}")
        else:
            logger.warning("Nenhum dado estruturado (JSON-LD) encontrado")
        
        # 5. Extrai informações usando o extrator
        logger.info("\nExtraindo informações com o extrator...")
        product_info = extract_aliexpress_product(soup, url)
        
        # 6. Exibe os resultados
        if product_info:
            logger.info("\n✅ Informações extraídas com sucesso!")
            logger.info(f"Título: {getattr(product_info, 'title', 'N/A')}")
            logger.info(f"Preço: {getattr(product_info, 'price', 'N/A')}")
            logger.info(f"Preço Original: {getattr(product_info, 'original_price', 'N/A')}")
            logger.info(f"Imagem: {getattr(product_info, 'image_url', 'N/A')}")
            logger.info(f"Disponível: {getattr(product_info, 'available', 'N/A')}")
            logger.info(f"Desconto: {getattr(product_info, 'discount', 'N/A')}%")
        else:
            logger.warning("❌ Nenhuma informação foi extraída")
        
        return product_info
        
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    # URL de teste do AliExpress
    test_url = "https://pt.aliexpress.com/item/1005009463783046.html"
    
    # Executa o teste
    test_aliexpress_extractor(test_url)
