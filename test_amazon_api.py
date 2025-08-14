#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de teste para a integração com a API da Amazon (PA-API v5).
"""

import asyncio
import logging
import os
import sys
from pprint import pprint

# Adiciona o diretório atual ao path para importar o módulo local
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa as configurações
import config

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_amazon_api.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('test_amazon_api')

async def test_amazon_search():
    """Testa a busca de ofertas na Amazon."""
    try:
        from amazon_api import buscar_ofertas_amazon
        
        logger.info("🔍 Iniciando teste de busca na Amazon...")
        
        # Palavras-chave para teste
        palavras_chave = ["notebook gamer", "ssd 1tb", "monitor 4k"]
        
        logger.info(f"Buscando ofertas para: {', '.join(palavras_chave)}")
        
        # Chama a função de busca
        ofertas = await buscar_ofertas_amazon(palavras_chave, max_itens=3)
        
        # Exibe os resultados
        if not ofertas:
            logger.warning("❌ Nenhuma oferta encontrada.")
            return False
        
        logger.info(f"✅ {len(ofertas)} ofertas encontradas!")
        
        # Mostra detalhes das ofertas
        for i, oferta in enumerate(ofertas, 1):
            logger.info(f"\n📦 Oferta {i}:")
            logger.info(f"Título: {oferta.get('titulo', 'N/A')}")
            logger.info(f"Preço: {oferta.get('preco', 'N/A')}")
            
            if 'preco_original' in oferta and oferta['preco_original']:
                logger.info(f"Preço Original: {oferta['preco_original']}")
            
            if 'desconto' in oferta and oferta['desconto']:
                logger.info(f"Desconto: {oferta['desconto']}%")
            
            logger.info(f"URL: {oferta.get('url', 'N/A')}")
            
            if 'imagem_url' in oferta and oferta['imagem_url']:
                logger.info(f"Imagem: {oferta['imagem_url']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("TESTE DE INTEGRAÇÃO COM A API DA AMAZON (PA-API v5)")
    print("=" * 80)
    
    # Verifica se as credenciais estão configuradas
    if not all([config.AMAZON_ACCESS_KEY, config.AMAZON_SECRET_KEY, config.AMAZON_ASSOCIATE_TAG]):
        print("\n❌ ERRO: Credenciais da Amazon PA-API não configuradas.")
        print("Por favor, adicione suas credenciais no arquivo .env:")
        print("  - AMAZON_ACCESS_KEY")
        print("  - AMAZON_SECRET_KEY")
        print("  - AMAZON_ASSOCIATE_TAG")
        print("\nVocê pode usar o arquivo .env.example como modelo.")
        sys.exit(1)
    
    # Executa o teste
    success = asyncio.run(test_amazon_search())
    
    print("\n" + "=" * 80)
    if success:
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("Verifique o arquivo 'test_amazon_api.log' para detalhes completos.")
    else:
        print("❌ ALGUNS TESTES FALHARAM. Verifique o arquivo 'test_amazon_api.log' para detalhes.")
    print("=" * 80)
