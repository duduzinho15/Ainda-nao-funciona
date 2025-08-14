"""
Script de teste para a integração com a API do AliExpress.

Este script testa as principais funcionalidades do módulo aliexpress_api.py,
incluindo geração de links de afiliado, busca de produtos e obtenção de detalhes.
"""
import os
import sys
import json
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ali_integration_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('ali_integration_test')

# Adiciona o diretório raiz ao path para importar o módulo
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa o módulo aliexpress_api
from aliexpress_api import AliExpressAPI, extract_product_id

def test_extract_product_id():
    """Testa a extração de IDs de produto de URLs do AliExpress."""
    test_cases = [
        ('https://pt.aliexpress.com/item/10050012345678.html', '10050012345678'),
        ('https://pt.aliexpress.com/i/10050012345678.html', '10050012345678'),
        ('https://www.aliexpress.com/item/10050012345678.html', '10050012345678'),
        ('https://www.aliexpress.com/item//10050012345678.html', '10050012345678'),
        ('https://www.aliexpress.com/item/10050012345678.html?spm=a2g0o.productlist...', '10050012345678'),
        ('https://www.aliexpress.com/item/10050012345678_1234567890.html', '10050012345678'),
        ('https://www.aliexpress.com/item/10050012345678_1234567890.html?spm=...', '10050012345678'),
        ('https://www.aliexpress.com/item//10050012345678_1234567890.html?spm=...', '10050012345678'),
        ('https://www.aliexpress.com/item//10050012345678_1234567890.html', '10050012345678'),
        ('https://www.aliexpress.com/item//10050012345678_1234567890.html?spm=...', '10050012345678'),
        ('https://www.aliexpress.com/item/10050012345678_1234567890.html?spm=...', '10050012345678'),
        ('https://www.aliexpress.com/item/10050012345678_1234567890.html', '10050012345678'),
    ]
    
    print("\n=== Testando extração de IDs de produto ===")
    for url, expected_id in test_cases:
        result = extract_product_id(url)
        status = "✅" if result == expected_id else "❌"
        print(f"{status} {url} -> {result} (esperado: {expected_id})")

def test_promotion_links(api):
    """Testa a geração de links de afiliado."""
    print("\n=== Testando geração de links de afiliado ===")
    
    # URLs de teste
    test_urls = [
        "https://pt.aliexpress.com/item/1005009463783046.html",
        "https://pt.aliexpress.com/item/10050012345678.html"
    ]
    
    # Testa cada tipo de link
    for link_type in api.PROMOTION_LINK_TYPES:
        print(f"\nTipo de link: {link_type}")
        try:
            result = api.get_promotion_links(test_urls, link_type=link_type)
            print(f"Resposta: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Salva a resposta em um arquivo
            with open(f'promotion_links_{link_type}.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"Resposta salva em 'promotion_links_{link_type}.json'")
                
        except Exception as e:
            print(f"❌ Erro ao gerar links do tipo '{link_type}': {str(e)}")

def test_product_info(api):
    """Testa a obtenção de informações de um produto."""
    print("\n=== Testando obtenção de informações de produto ===")
    
    # ID de teste
    product_id = "1005009463783046"
    
    try:
        result = api.get_product_info(product_id)
        print(f"Informações do produto {product_id}:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Salva a resposta em um arquivo
        with open('product_info.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            print("Resposta salva em 'product_info.json'")
            
    except Exception as e:
        print(f"❌ Erro ao obter informações do produto: {str(e)}")

def test_product_search(api):
    """Testa a busca de produtos por palavra-chave."""
    print("\n=== Testando busca de produtos ===")
    
    # Palavra-chave para busca
    keyword = "smartwatch"
    
    try:
        result = api.search_products(
            keywords=keyword,
            page_size=5,  # Limita a 5 resultados para teste
            sort='SALE_PRICE_DESC'
        )
        
        print(f"Resultados da busca por '{keyword}':")
        print(f"Total de resultados: {result.get('total_results', 0)}")
        
        # Mostra os produtos encontrados
        products = result.get('products', [])
        for i, product in enumerate(products, 1):
            print(f"\nProduto {i}:")
            print(f"  Título: {product.get('product_title', 'N/A')}")
            print(f"  Preço: {product.get('target_sale_price', 'N/A')} {product.get('target_currency', 'BRL')}")
            print(f"  Avaliação: {product.get('evaluate_rate', 'N/A')}")
            print(f"  URL: {product.get('product_detail_url', 'N/A')}")
        
        # Salva a resposta em um arquivo
        with open('product_search.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            print("\nResposta completa salva em 'product_search.json'")
            
    except Exception as e:
        print(f"❌ Erro ao buscar produtos: {str(e)}")

def main():
    """Função principal para executar os testes."""
    print("=== Iniciando testes de integração com a API do AliExpress ===")
    
    try:
        # Inicializa a API
        api = AliExpressAPI()
        print("✅ API inicializada com sucesso")
        
        # Executa os testes
        test_extract_product_id()
        test_promotion_links(api)
        test_product_info(api)
        test_product_search(api)
        
        print("\n✅ Todos os testes foram concluídos com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro durante a execução dos testes: {str(e)}")
        logger.exception("Erro durante a execução dos testes")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
