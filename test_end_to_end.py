#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste de fluxo ponta a ponta para a integração com a API da Amazon PA-API.

Este script testa todo o fluxo, desde a busca de produtos até o processamento
dos resultados, exibindo as ofertas encontradas em um formato legível.
"""

import asyncio
import logging
import sys
from typing import List, Dict, Any

# Adiciona o diretório raiz ao path para importar os módulos locais
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa as funções necessárias
from amazon_api import buscar_ofertas_amazon, create_api_client

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Cria um logger específico para este script
logger = logging.getLogger('test_end_to_end')

async def testar_fluxo_completo():
    """Testa o fluxo completo de busca de ofertas na Amazon."""
    logger.info("🚀 Iniciando teste de fluxo completo...")
    
    # Lista de palavras-chave para busca
    palavras_chave = ["smartphone", "notebook", "fone de ouvido"]
    
    try:
        # Testa a criação do cliente da API
        logger.info("🔌 Testando conexão com a API da Amazon...")
        api = create_api_client()
        if not api:
            logger.error("❌ Falha ao criar cliente da API. Verifique as credenciais.")
            return False
        
        logger.info("✅ Cliente da API criado com sucesso!")
        
        # Testa a busca de ofertas
        logger.info(f"🔍 Buscando ofertas para as palavras-chave: {', '.join(palavras_chave)}")
        ofertas = await buscar_ofertas_amazon(palavras_chave, max_itens=3)
        
        # Exibe os resultados
        if not ofertas:
            logger.warning("⚠️  Nenhuma oferta encontrada.")
            return False
        
        logger.info(f"✅ Encontradas {len(ofertas)} ofertas!")
        
        # Exibe as ofertas encontradas
        for i, oferta in enumerate(ofertas, 1):
            print(f"\n📦 Oferta #{i}")
            print(f"📌 Título: {oferta.get('titulo', 'Sem título')}")
            print(f"💰 Preço: {oferta.get('preco', 'N/A')}")
            
            if oferta.get('preco_original'):
                print(f"💵 Preço original: {oferta['preco_original']} (Economia de {oferta.get('desconto', 0)}%)")
            
            print(f"🛒 URL: {oferta.get('url', 'N/A')}")
            
            if oferta.get('imagem_url'):
                print(f"🖼️  Imagem: {oferta['imagem_url']}")
            
            print("-" * 50)
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Erro durante o teste: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DE FLUXO PONTA A PONTA - AMAZON PA-API")
    print("=" * 60)
    print("")
    
    # Executa o teste
    sucesso = asyncio.run(testar_fluxo_completo())
    
    print("\n" + "=" * 60)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!" if sucesso else "❌ TESTE FALHOU!")
    print("=" * 60)
