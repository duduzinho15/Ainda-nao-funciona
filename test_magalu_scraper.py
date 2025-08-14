"""
Script para testar o scraper do Magazine Luiza.
"""
import logging
import sys

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Saída para o console
        logging.FileHandler('magalu_test.log', mode='w', encoding='utf-8')  # Saída para arquivo
    ]
)
logger = logging.getLogger('test_magalu')

def main():
    logger.info("🚀 Iniciando teste do scraper do Magazine Luiza")
    
    try:
        # Importa o módulo dinamicamente
        from magalu_scraper import buscar_ofertas_magalu
        
        logger.info("🔍 Buscando ofertas na primeira página...")
        ofertas = buscar_ofertas_magalu(paginas=1)
        
        if not ofertas:
            logger.warning("⚠️ Nenhuma oferta encontrada no Magazine Luiza")
            return
        
        logger.info(f"✅ Encontradas {len(ofertas)} ofertas no Magazine Luiza")
        
        # Mostra detalhes das ofertas encontradas
        for i, oferta in enumerate(ofertas[:5], 1):  # Mostra apenas as 5 primeiras
            logger.info(f"\n📦 Oferta {i}:")
            logger.info(f"   Título: {oferta.get('titulo')}")
            logger.info(f"   Preço: {oferta.get('preco')}")
            logger.info(f"   Preço Original: {oferta.get('preco_original', 'N/A')}")
            logger.info(f"   Desconto: {oferta.get('desconto', 'N/A')}")
            logger.info(f"   URL: {oferta.get('url_produto')}")
            logger.info(f"   Loja: {oferta.get('loja')}")
            logger.info(f"   Fonte: {oferta.get('fonte')}")
        
        logger.info("\n🎉 Teste concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}", exc_info=True)

if __name__ == "__main__":
    main()
