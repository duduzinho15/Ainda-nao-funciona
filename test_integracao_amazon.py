#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de teste para integração ponta a ponta da Amazon PA-API com o bot do Telegram.
"""

import asyncio
import logging
import os
import sys
from pprint import pprint
from datetime import datetime

# Adiciona o diretório atual ao path para importar os módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_integracao_amazon.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('test_integracao_amazon')

# Importa as configurações e módulos necessários
import config
from amazon_api import buscar_ofertas_amazon
from telegram_poster import publicar_oferta_automatica
from database import setup_database, oferta_ja_existe

# Palavras-chave para teste
PALAVRAS_CHAVE_TESTE = ["notebook gamer", "ssd 1tb"]

async def testar_busca_e_publicacao():
    """Testa o fluxo completo de busca e publicação de ofertas."""
    try:
        logger.info("=" * 80)
        logger.info("🚀 INICIANDO TESTE DE INTEGRAÇÃO AMAZON PA-API + TELEGRAM")
        logger.info("=" * 80)
        
        # Verifica se as credenciais estão configuradas
        if not all([config.AMAZON_ACCESS_KEY, config.AMAZON_SECRET_KEY, config.AMAZON_ASSOCIATE_TAG]):
            logger.error("❌ Credenciais da Amazon PA-API não configuradas.")
            logger.error("Por favor, configure as credenciais no arquivo .env")
            return False
            
        if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
            logger.error("❌ Configurações do Telegram não encontradas.")
            logger.error("Por favor, verifique as variáveis TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no .env")
            return False
        
        # Configura o banco de dados
        logger.info("🔄 Configurando banco de dados...")
        if not setup_database():
            logger.error("❌ Falha ao configurar o banco de dados.")
            return False
            
        # Testa a busca de ofertas
        logger.info("\n🔍 Testando busca de ofertas na Amazon...")
        ofertas = await buscar_ofertas_amazon(PALAVRAS_CHAVE_TESTE, max_itens=2)
        
        if not ofertas:
            logger.warning("⚠️ Nenhuma oferta encontrada. Verifique as credenciais e a conexão com a API da Amazon.")
            return False
            
        logger.info(f"✅ {len(ofertas)} ofertas encontradas!")
        
        # Testa a publicação de ofertas
        logger.info("\n📤 Testando publicação de ofertas no Telegram...")
        publicadas = 0
        
        for i, oferta in enumerate(ofertas, 1):
            try:
                logger.info(f"\n📦 Processando oferta {i}/{len(ofertas)}:")
                logger.info(f"   Título: {oferta.get('titulo', 'Sem título')}")
                logger.info(f"   Preço: {oferta.get('preco', 'N/A')}")
                
                if 'preco_original' in oferta and oferta['preco_original']:
                    logger.info(f"   Preço Original: {oferta['preco_original']}")
                
                if 'desconto' in oferta and oferta['desconto']:
                    logger.info(f"   Desconto: {oferta['desconto']}%")
                
                # Verifica se a oferta já existe no banco de dados
                if oferta_ja_existe(url_produto=oferta.get('url'), asin=oferta.get('asin')):
                    logger.info("   ⚠️ Oferta já publicada anteriormente (pulando...)")
                    continue
                
                # Prepara os dados da oferta para publicação
                oferta_publicacao = {
                    'asin': oferta.get('asin'),
                    'titulo': oferta.get('titulo', 'Sem título'),
                    'preco': oferta.get('preco', 'Preço não informado'),
                    'preco_original': oferta.get('preco_original'),
                    'url': oferta.get('url'),
                    'imagem_url': oferta.get('imagem_url'),
                    'loja': 'Amazon',
                    'fonte': 'Amazon PA-API',
                    'data_atualizacao': datetime.now().isoformat()
                }
                
                # Publica a oferta
                logger.info("   📤 Publicando oferta no Telegram...")
                sucesso = await publicar_oferta_automatica(
                    oferta=oferta_publicacao,
                    chat_id=config.TELEGRAM_CHAT_ID
                )
                
                if sucesso:
                    publicadas += 1
                    logger.info("   ✅ Oferta publicada com sucesso!")
                else:
                    logger.warning("   ❌ Falha ao publicar oferta.")
                
                # Pequeno delay entre publicações
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"   ❌ Erro ao processar oferta: {e}", exc_info=True)
                continue
        
        # Resultado final
        logger.info("\n" + "=" * 80)
        logger.info(f"🏁 TESTE CONCLUÍDO!")
        logger.info(f"   Total de ofertas processadas: {len(ofertas)}")
        logger.info(f"   Ofertas publicadas: {publicadas}")
        logger.info(f"   Ofertas duplicadas: {len(ofertas) - publicadas}")
        logger.info("=" * 80)
        
        return publicadas > 0
        
    except Exception as e:
        logger.error(f"❌ ERRO NO TESTE: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("🛠️  TESTE DE INTEGRAÇÃO AMAZON PA-API + TELEGRAM")
    print("=" * 80)
    
    # Executa o teste
    sucesso = asyncio.run(testar_busca_e_publicacao())
    
    print("\n" + "=" * 80)
    if sucesso:
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("Verifique o arquivo 'test_integracao_amazon.log' para detalhes.")
    else:
        print("❌ ALGUNS TESTES FALHARAM.")
        print("Verifique o arquivo 'test_integracao_amazon.log' para mais informações.")
    print("=" * 80)
