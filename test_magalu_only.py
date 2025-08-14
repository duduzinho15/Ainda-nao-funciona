#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste simplificado para o Magazine Luiza Scraper.
"""

import logging
import sys
import os
from pprint import pprint
import requests
from bs4 import BeautifulSoup

# Configuração de logging detalhada
logging.basicConfig(
    level=logging.DEBUG,  # Nível mais detalhado para depuração
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('magalu_test.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('magalu_test')

# Adiciona um handler para o console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

def test_requests():
    """Testa a conexão com o site do Magazine Luiza."""
    logger.info("🔍 Testando conexão com o Magazine Luiza...")
    
    url = "https://www.magazineluiza.com.br/selecao/ofertasdodia/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info(f"Fazendo requisição para: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        logger.info(f"Resposta recebida - Status: {response.status_code}")
        logger.info(f"Tamanho da resposta: {len(response.text)} bytes")
        
        # Verifica se a resposta parece ser HTML
        if 'text/html' not in response.headers.get('content-type', ''):
            logger.error("A resposta não parece ser HTML válido")
            logger.error(f"Content-Type: {response.headers.get('content-type')}")
            return False
            
        # Verifica se o conteúdo parece ser do Magazine Luiza
        if 'magazineluiza' not in response.text.lower():
            logger.warning("O conteúdo não parece ser do Magazine Luiza")
            
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição: {e}")
        return False

def test_magalu_scraper():
    """Testa o scraper do Magazine Luiza."""
    logger.info("\n🔍 Iniciando teste do Magazine Luiza Scraper...")
    
    # Verifica se o módulo pode ser importado
    try:
        from magalu_scraper import buscar_ofertas_magalu
        logger.info("✅ Módulo magalu_scraper importado com sucesso")
    except ImportError as e:
        logger.error(f"❌ Erro ao importar módulo magalu_scraper: {e}")
        logger.error("Certifique-se de que o arquivo magalu_scraper.py existe no diretório.")
        return False
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao importar módulo: {e}", exc_info=True)
        return False
    
    # Busca ofertas (apenas 1 página para teste)
    logger.info("\n🔄 Buscando ofertas...")
    try:
        ofertas = buscar_ofertas_magalu(paginas=1)
    except Exception as e:
        logger.error(f"❌ Erro ao buscar ofertas: {e}", exc_info=True)
        return False
    
    if not ofertas:
        logger.error("❌ Nenhuma oferta encontrada no Magazine Luiza")
        return False
    
    logger.info(f"✅ Encontradas {len(ofertas)} ofertas no Magazine Luiza")
    
    # Mostra detalhes das ofertas
    logger.info("\n--- DETALHES DAS OFERTAS ENCONTRADAS ---")
    for i, oferta in enumerate(ofertas[:3], 1):  # Mostra apenas as 3 primeiras
        try:
            logger.info(f"\n📦 Oferta {i}:")
            logger.info(f"Título: {oferta.get('titulo', 'N/A')}")
            logger.info(f"Preço: {oferta.get('preco', 'N/A')}")
            if oferta.get('preco_original'):
                logger.info(f"Preço Original: {oferta.get('preco_original')}")
            if oferta.get('desconto'):
                logger.info(f"Desconto: {oferta.get('desconto')}")
            logger.info(f"URL: {oferta.get('url_produto', 'N/A')}")
            if oferta.get('imagem_url'):
                logger.debug(f"Imagem: {oferta.get('imagem_url')}")
        except Exception as e:
            logger.error(f"Erro ao processar oferta {i}: {e}", exc_info=True)
    
    return True

if __name__ == "__main__":
    # Executa os testes
    logger.info("=" * 80)
    logger.info("INICIANDO TESTES DO MAGAZINE LUÍZA")
    logger.info("=" * 80)
    
    # Testa a conexão primeiro
    if not test_requests():
        logger.error("❌ Teste de conexão falhou. Verifique sua conexão com a internet.")
        sys.exit(1)
    
    # Testa o scraper
    success = test_magalu_scraper()
    
    logger.info("\n" + "=" * 80)
    if success:
        logger.info("✅ TODOS OS TESTES FORAM BEM-SUCEDIDOS!")
    else:
        logger.error("❌ ALGUNS TESTES FALHARAM. Verifique os logs para mais detalhes.")
    logger.info("=" * 80)
    
    sys.exit(0 if success else 1)
