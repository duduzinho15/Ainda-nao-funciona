import asyncio
import logging
import sys
import traceback
from product_scraper import extract_product_info, ProductInfo
from typing import Dict, Any, Optional

# Configuração avançada de logging
logger = logging.getLogger('scraper_test')
logger.setLevel(logging.DEBUG)

# Remove handlers existentes
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Cria um formato de log detalhado
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Handler para arquivo de log
file_handler = logging.FileHandler('scraper_test.log', mode='w')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Handler para console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Adiciona os handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Redireciona exceções não capturadas para o logger
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Erro não capturado:", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# Links de teste
TEST_URLS = {
    'Amazon': 'https://www.amazon.com.br/PHILIPS-TAT1109BK-00-Bluetooth-Microfone/dp/B0DVMQVVDY',
    'AliExpress': 'https://pt.aliexpress.com/item/1005009463783046.html',
    'Mercado Livre': 'https://www.mercadolivre.com.br/smart-tv-samsung-u8100f-crystal-uhd-4k-2025-43-preto/p/MLB49740322',
    'Shopee': 'https://shopee.com.br/Meias-Divertidas-de-Personagens-em-Algod%C3%A3o-Unissex-i.441370953.22797653349',
    'Magazine Luiza': 'https://www.magazinevoce.com.br/magazinegarimpeirogeek/apple-iphone-14-128gb-estelar-61-12mp-ios-5g/p/237184100/te/ip14/'
}

def format_product_info(product: Dict[str, Any]) -> str:
    """Formata as informações do produto para exibição."""
    if not product:
        return "❌ Não foi possível extrair informações do produto"
    
    lines = [
        f"🏪 Loja: {product.get('loja', 'N/A')}",
        f"📌 Título: {product.get('titulo', 'N/A')}",
        f"💰 Preço: {product.get('preco', 'N/A')}",
    ]
    
    if product.get('preco_original'):
        lines.append(f"💲 Preço Original: {product['preco_original']}")
    
    if product.get('desconto'):
        lines.append(f"🎯 Desconto: {product['desconto']}%")
    
    lines.append(f"🖼️ Imagem: {'Sim' if product.get('imagem_url') else 'Não'}")
    lines.append(f"📦 Disponível: {'✅ Sim' if product.get('disponivel', True) else '❌ Não'}")
    lines.append(f"🔗 URL: {product.get('url_produto', 'N/A')}")
    
    return "\n".join(lines)

async def test_scraper():
    """Testa todos os scrapers com as URLs fornecidas."""
    results = {}
    
    for store, url in TEST_URLS.items():
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 Testando {store}")
        logger.info(f"URL: {url}")
        logger.info(f"{'='*80}")
        
        try:
            logger.debug(f"Iniciando extração para {store}")
            
            # Extrai as informações do produto
            product_info = extract_product_info(url)
            
            if product_info:
                logger.debug(f"Extração concluída com sucesso para {store}")
                logger.debug(f"Título: {getattr(product_info, 'title', 'N/A')}")
                logger.debug(f"Preço: {getattr(product_info, 'price', 'N/A')}")
                logger.debug(f"Disponível: {getattr(product_info, 'available', 'N/A')}")
            else:
                logger.warning(f"Falha ao extrair informações para {store}")
            
            # Armazena os resultados
            results[store] = {
                'success': product_info is not None,
                'data': product_info or {}
            }
            
            # Exibe os resultados formatados
            formatted_info = format_product_info(product_info) if product_info else "❌ Falha ao extrair informações do produto"
            logger.info(f"\n{formatted_info}")
            
        except Exception as e:
            error_msg = f"Erro ao testar {store}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results[store] = {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            logger.error(f"❌ {error_msg}")
        
        # Aguarda um pouco entre as requisições para evitar bloqueios
        if store != list(TEST_URLS.keys())[-1]:  # Não espera após o último
            await asyncio.sleep(3)
    
    # Resumo dos testes
    print("\n" + "="*50)
    print("📊 RESUMO DOS TESTES")
    print("="*50)
    
    total = len(results)
    success = sum(1 for r in results.values() if r['success'])
    
    print(f"✅ Testes bem-sucedidos: {success}/{total}")
    print(f"❌ Testes com falha: {total - success}/{total}\n")
    
    for store, result in results.items():
        status = "✅" if result['success'] else "❌"
        print(f"{status} {store}: {'Sucesso' if result['success'] else 'Falha'}")
        if not result['success'] and 'error' in result:
            print(f"   Erro: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test_scraper())
