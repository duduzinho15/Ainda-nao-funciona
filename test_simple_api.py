"""
Script de teste simplificado para a API de Afiliados do AliExpress.
"""
import json
import logging
import os
import sys
import dotenv
from datetime import datetime

# Configuração básica de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('test_aliexpress_api')
logger.info("Iniciando teste da API do AliExpress...")

# Carrega as variáveis de ambiente do arquivo .env
dotenv.load_dotenv()

# Adiciona o diretório atual ao path para importar o módulo aliexpress_api
sys.path.insert(0, os.path.abspath('.'))

# Importa a API do AliExpress
from aliexpress_api import AliExpressAPI

def main():
    """Função principal do script de teste."""
    logger.info("=== TESTE SIMPLIFICADO DA API DO ALIEXPRESS ===")
    
    try:
        # Carrega as credenciais do ambiente
        app_key = os.getenv('ALIEXPRESS_APP_KEY')
        app_secret = os.getenv('ALIEXPRESS_APP_SECRET')
        tracking_id = os.getenv('ALIEXPRESS_TRACKING_ID')
        
        if not all([app_key, app_secret, tracking_id]):
            logger.error("❌ Erro: Credenciais da API do AliExpress não encontradas no arquivo .env")
            logger.info("Por favor, verifique se as seguintes variáveis estão definidas no arquivo .env:")
            logger.info("- ALIEXPRESS_APP_KEY")
            logger.info("- ALIEXPRESS_APP_SECRET")
            logger.info("- ALIEXPRESS_TRACKING_ID")
            return False
            
        logger.info("✅ Credenciais carregadas com sucesso do arquivo .env")
        logger.info(f"App Key: {app_key}")
        logger.info(f"App Secret: {'*' * len(app_secret) if app_secret else 'N/A'}")
        logger.info(f"Tracking ID: {tracking_id}")
        
        # Inicializa a API
        logger.info("\nInicializando a API do AliExpress...")
        api = AliExpressAPI(
            app_key=app_key,
            app_secret=app_secret,
            tracking_id=tracking_id
        )
        logger.info("✅ API inicializada com sucesso!")
        
        # URL de teste (usando um produto de exemplo)
        test_url = "https://pt.aliexpress.com/item/1005009463783046.html"
        logger.info(f"\nTestando com URL: {test_url}")
        
        # Extrai o ID do produto
        from aliexpress_api import extract_product_id
        product_id = extract_product_id(test_url)
        if not product_id:
            logger.error(f"❌ Não foi possível extrair o ID do produto da URL: {test_url}")
            return False
            
        logger.info(f"✅ ID do produto extraído: {product_id}")
        
        # Testa a obtenção de informações do produto
        logger.info("\n=== TESTE: OBTENÇÃO DE INFORMAÇÕES DO PRODUTO ===")
        try:
            logger.info(f"Obtendo informações para o produto ID: {product_id}")
            product_data = api.get_product_info(product_id)
                
            # Exibe os dados brutos da resposta
            logger.info("\n=== DADOS BRUTOS DA RESPOSTA ===")
            logger.info(json.dumps(product_data, indent=2, ensure_ascii=False))
            
            # Exibe um resumo dos dados
            if 'result' in product_data:
                result = product_data['result']
                logger.info("\n=== RESUMO DO PRODUTO ===")
                logger.info(f"Título: {result.get('product_title', 'N/A')}")
                logger.info(f"Preço: {result.get('target_sale_price', 'N/A')} {result.get('target_currency', 'BRL')}")
                logger.info(f"Loja: {result.get('shop_name', 'N/A')}")
                logger.info(f"Avaliação: {result.get('evaluate_rate', 'N/A')}")
                
                # Testa a geração de links de afiliado para este produto
                logger.info("\n=== TESTE: GERAÇÃO DE LINKS DE AFILIADO ===")
                try:
                    logger.info(f"Gerando link de afiliado para: {test_url}")
                    links = api.get_promotion_links([test_url])
                    
                    logger.info("\n=== RESULTADO DO LINK DE AFILIADO ===")
                    logger.info(json.dumps(links, indent=2, ensure_ascii=False))
                    
                    if links and isinstance(links, list) and len(links) > 0:
                        logger.info("✅ Link de afiliado gerado com sucesso!")
                        logger.info(f"URL original: {links[0].get('source_value', 'N/A')}")
                        logger.info(f"URL de afiliado: {links[0].get('promotion_url', 'N/A')}")
                    else:
                        logger.error("❌ Não foi possível gerar o link de afiliado")
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao gerar link de afiliado: {str(e)}", exc_info=True)
                
            else:
                logger.error("❌ Resposta inesperada da API:")
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter informações do produto: {str(e)}", exc_info=True)
        
        logger.info("\n✅ TESTE CONCLUÍDO!")
        return True
        
    except Exception as e:
        logger.error(f"❌ ERRO CRÍTICO: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
