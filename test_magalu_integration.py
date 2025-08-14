#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste de integração para o Magazine Luiza.

Este script testa o fluxo completo de scraping do Magazine Luiza,
geração de links de afiliado e verificação de duplicatas no banco de dados.
"""

import asyncio
import logging
import sys
from pprint import pprint

# Adiciona o diretório raiz ao path para importações
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importações dos módulos personalizados
try:
    import database
    import affiliate
    from magalu_scraper import buscar_ofertas_magalu
    IMPORT_ERROR = None
except ImportError as e:
    IMPORT_ERROR = e

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_magalu.log')
    ]
)
logger = logging.getLogger('test_magalu')

async def test_magalu_scraper():
    """Testa o scraper do Magazine Luiza."""
    logger.info("🔍 Iniciando teste do Magazine Luiza Scraper...")
    
    # Busca ofertas
    ofertas = buscar_ofertas_magalu(paginas=1)  # Apenas 1 página para teste
    
    if not ofertas:
        logger.error("❌ Nenhuma oferta encontrada no Magazine Luiza")
        return False
    
    logger.info(f"✅ Encontradas {len(ofertas)} ofertas no Magazine Luiza")
    
    # Mostra algumas ofertas
    logger.info("\n--- PRIMEIRAS 3 OFERTAS ENCONTRADAS ---")
    for i, oferta in enumerate(ofertas[:3], 1):
        logger.info(f"\n📦 Oferta {i}:")
        logger.info(f"Título: {oferta.get('titulo')}")
        logger.info(f"Preço: {oferta.get('preco')}")
        if oferta.get('preco_original'):
            logger.info(f"Preço Original: {oferta.get('preco_original')}")
        if oferta.get('desconto'):
            logger.info(f"Desconto: {oferta.get('desconto')}")
        logger.info(f"URL: {oferta.get('url_produto')}")
    
    return ofertas

def test_affiliate_links(ofertas):
    """Testa a geração de links de afiliado."""
    logger.info("\n🔗 Testando geração de links de afiliado...")
    
    for i, oferta in enumerate(ofertas[:3], 1):  # Testa apenas as 3 primeiras
        url_original = oferta['url_produto']
        url_afiliado = affiliate.gerar_link_afiliado(url_original)
        
        logger.info(f"\n🔗 Link {i}:")
        logger.info(f"Original: {url_original}")
        logger.info(f"Afiliado: {url_afiliado}")
        
        if 'magazinevoce.com.br/magazinegarimpeirogeek' not in url_afiliado:
            logger.error("❌ Link de afiliado incorreto!")
            return False
    
    logger.info("✅ Links de afiliado gerados com sucesso")
    return True

async def test_database_integration(ofertas):
    """Testa a integração com o banco de dados."""
    logger.info("\n💾 Testando integração com o banco de dados...")
    
    # Configura o banco de dados
    database.setup_database()
    
    # Pega a primeira oferta para teste
    if not ofertas:
        logger.error("❌ Nenhuma oferta para testar no banco de dados")
        return False
    
    oferta = ofertas[0]
    url_produto = oferta['url_produto']
    
    # Verifica se a oferta já existe (não deveria existir)
    if database.oferta_ja_existe(url_produto=url_produto):
        logger.warning("⚠️  Oferta já existe no banco de dados")
    else:
        logger.info("✅ Oferta ainda não existe no banco de dados")
    
    # Adiciona a oferta ao banco de dados
    sucesso = database.adicionar_oferta(
        url_produto=url_produto,
        titulo=oferta['titulo'],
        preco=oferta['preco'],
        loja=oferta.get('loja', 'Magazine Luiza'),
        fonte=oferta.get('fonte', 'Magalu - Ofertas do Dia'),
        url_fonte=oferta.get('url_fonte', ''),
        preco_original=oferta.get('preco_original'),
        imagem_url=oferta.get('imagem_url', '')
    )
    
    if not sucesso:
        logger.error("❌ Falha ao adicionar oferta ao banco de dados")
        return False
    
    logger.info("✅ Oferta adicionada com sucesso ao banco de dados")
    
    # Verifica se a oferta foi realmente adicionada
    if not database.oferta_ja_existe(url_produto=url_produto):
        logger.error("❌ Oferta não foi encontrada no banco de dados após a inserção")
        return False
    
    logger.info("✅ Oferta encontrada no banco de dados após a inserção")
    return True

async def main():
    """Função principal de teste."""
    logger.info("🚀 Iniciando teste de integração do Magazine Luiza")
    
    # Verifica se houve erro na importação
    if IMPORT_ERROR:
        logger.error(f"❌ Erro ao importar módulos: {IMPORT_ERROR}")
        logger.error("Certifique-se de que todas as dependências estão instaladas.")
        logger.error("Execute: pip install -r requirements.txt")
        return False
    
    # Testa o scraper
    ofertas = await test_magalu_scraper()
    if not ofertas:
        logger.error("❌ Teste do scraper falhou")
        return False
    
    # Testa a geração de links de afiliado
    if not test_affiliate_links(ofertas):
        logger.error("❌ Teste de links de afiliado falhou")
        return False
    
    # Testa a integração com o banco de dados
    if not await test_database_integration(ofertas):
        logger.error("❌ Teste de integração com o banco de dados falhou")
        return False
    
    logger.info("\n🎉 Todos os testes foram concluídos com sucesso!")
    return True

if __name__ == "__main__":
    # Executa os testes
    success = asyncio.run(main())
    
    # Retorna código de saída apropriado
    sys.exit(0 if success else 1)
