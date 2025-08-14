"""
Script de teste para a API de Afiliados do AliExpress.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pprint import pprint

# Adiciona o diretório raiz ao path para importar o módulo aliexpress_api
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Define as variáveis de ambiente necessárias
os.environ['ALIEXPRESS_APP_KEY'] = '517956'
os.environ['ALIEXPRESS_APP_SECRET'] = 'okv8nzEGIvWqV0XxONcN9loPNrYwWDsm'
os.environ['ALIEXPRESS_TRACKING_ID'] = 'telegram'

# Agora importa o módulo aliexpress_api
from aliexpress_api import AliExpressAPI, extract_product_id, format_product_info

# Configuração de logging
log_filename = f'aliexpress_api_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_filename, mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('test_aliexpress_api')
logger.info(f"Log file: {os.path.abspath(log_filename)}")

def test_product_info(api, product_url):
    """Testa a obtenção de informações de um produto pelo URL."""
    logger.info(f"\n=== TESTE: Obtendo informações do produto ===")
    logger.info(f"URL: {product_url}")
    
    try:
        # Extrai o ID do produto da URL
        product_id = extract_product_id(product_url)
        if not product_id:
            logger.error("❌ Não foi possível extrair o ID do produto da URL")
            return False
        
        logger.info(f"ID do produto extraído: {product_id}")
        
        # Obtém as informações do produto
        logger.info("Obtendo informações do produto...")
        product_data = api.get_product_info(product_id)
        
        # Log da resposta bruta da API para diagnóstico
        logger.debug(f"Resposta bruta da API: {json.dumps(product_data, ensure_ascii=False, indent=2)}")
        
        # Formata os dados do produto
        formatted_data = format_product_info(product_data)
        
        # Exibe os resultados
        logger.info("\n=== INFORMAÇÕES DO PRODUTO ===")
        logger.info(f"Título: {formatted_data.get('title')}")
        logger.info(f"Preço: {formatted_data.get('price')} {formatted_data.get('currency')}")
        logger.info(f"Preço Original: {formatted_data.get('original_price')} {formatted_data.get('currency')}")
        logger.info(f"Desconto: {formatted_data.get('discount')}")
        logger.info(f"Avaliação: {formatted_data.get('rating')}")
        logger.info(f"Pedidos: {formatted_data.get('orders')}")
        logger.info(f"Loja: {formatted_data.get('store_name')}")
        logger.info(f"Disponível: {'Sim' if formatted_data.get('available') else 'Não'}")
        logger.info(f"URL: {formatted_data.get('url')}")
        logger.info(f"Imagem: {formatted_data.get('image_url')}")
        
        # Salva os dados completos em um arquivo para análise
        output_file = f'product_info_{product_id}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)
        logger.info(f"\nDados completos salvos em '{output_file}'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter informações do produto: {str(e)}", exc_info=True)
        return False

def test_promotion_links(api, product_urls):
    """Testa a geração de links de afiliado."""
    logger.info(f"\n=== TESTE: Gerando links de afiliado ===")
    
    if not isinstance(product_urls, list):
        product_urls = [product_urls]
    
    logger.info(f"URLs para converter: {product_urls}")
    
    try:
        # Gera os links de afiliado
        logger.info("Gerando links de afiliado...")
        links = api.get_promotion_links(product_urls)
        
        logger.info("\n=== LINKS DE AFILIADO GERADOS ===")
        for i, link in enumerate(links, 1):
            logger.info(f"\nLink {i}:")
            logger.info(f"URL Original: {link.get('source_value', 'N/A')}")
            logger.info(f"URL de Afiliado: {link.get('promotion_url', 'N/A')}")
            logger.info(f"ID de Rastreamento: {link.get('tracking_id', 'N/A')}")
        
        # Salva os links em um arquivo para referência
        with open('affiliate_links.json', 'w', encoding='utf-8') as f:
            json.dump(links, f, ensure_ascii=False, indent=2)
        logger.info("\nLinks de afiliado salvos em 'affiliate_links.json'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar links de afiliado: {e}", exc_info=True)
        return False

def test_product_search(api, keywords, category_id=None, min_price=None, max_price=None):
    """Testa a busca de produtos por palavras-chave."""
    logger.info(f"\n=== TESTE: Buscando produtos por palavras-chave ===")
    logger.info(f"Palavras-chave: {keywords}")
    
    if category_id:
        logger.info(f"Filtrando por categoria: {category_id}")
    if min_price is not None:
        logger.info(f"Preço mínimo: {min_price}")
    if max_price is not None:
        logger.info(f"Preço máximo: {max_price}")
    
    try:
        # Realiza a busca
        logger.info("Realizando busca...")
        search_results = api.search_products(
            keywords=keywords,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            page_size=5  # Limita a 5 resultados para teste
        )
        
        # Processa os resultados
        products = search_results.get('products', {}).get('product', [])
        
        logger.info(f"\n=== RESULTADOS DA BUSCA ({len(products)} itens) ===")
        
        for i, product in enumerate(products, 1):
            formatted = format_product_info({'result': product})
            logger.info(f"\n{i}. {formatted.get('title')}")
            logger.info(f"   Preço: {formatted.get('price')} {formatted.get('currency')}")
            logger.info(f"   Avaliação: {formatted.get('rating')}")
            logger.info(f"   Pedidos: {formatted.get('orders')}")
            logger.info(f"   URL: {formatted.get('url')}")
        
        # Salva os resultados completos em um arquivo
        with open('search_results.json', 'w', encoding='utf-8') as f:
            json.dump(search_results, f, ensure_ascii=False, indent=2)
        logger.info("\nResultados completos da busca salvos em 'search_results.json'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar produtos: {e}", exc_info=True)
        return False

def main():
    """Função principal do script de teste."""
    logger.info("=== INÍCIO DOS TESTES DA API DO ALIEXPRESS ===")
    
    # URL de teste (substitua por um produto real do AliExpress)
    test_url = "https://pt.aliexpress.com/item/1005009463783046.html"
    
    try:
        # Inicializa a API
        logger.info("Inicializando a API do AliExpress...")
        api = AliExpressAPI()
        
        # Testa a obtenção de informações do produto
        logger.info("\n" + "="*50)
        logger.info("TESTE 1: OBTENÇÃO DE INFORMAÇÕES DO PRODUTO")
        logger.info("="*50)
        test_product_info(api, test_url)
        
        # Testa a geração de links de afiliado
        logger.info("\n" + "="*50)
        logger.info("TESTE 2: GERAÇÃO DE LINKS DE AFILIADO")
        logger.info("="*50)
        test_promotion_links(api, test_url)
        
        # Testa a busca de produtos
        logger.info("\n" + "="*50)
        logger.info("TESTE 3: BUSCA DE PRODUTOS POR PALAVRAS-CHAVE")
        logger.info("="*50)
        test_product_search(api, "carrinho de armazenamento", min_price=50, max_price=200)
        
        logger.info("\n=== TESTES CONCLUÍDOS COM SUCESSO! ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ ERRO NOS TESTES: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
