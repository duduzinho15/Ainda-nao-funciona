"""
Script de teste para o módulo promobit_scraper.py

Este script testa a funcionalidade de busca de ofertas no site Promobit.
"""
import asyncio
import json
import logging
from datetime import datetime

import aiohttp

# Importa o módulo a ser testado
from promobit_scraper import buscar_ofertas_promobit

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_promobit_scraper.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

async def test_scraper():
    """Função principal de teste do scraper."""
    logger.info("Iniciando teste do Promobit Scraper")
    
    # Cria uma sessão HTTP
    async with aiohttp.ClientSession() as session:
        try:
            logger.info("Buscando ofertas no Promobit...")
            
            # Chama a função de busca com parâmetros de teste
            ofertas = await buscar_ofertas_promobit(
                session=session,
                max_paginas=2,  # Apenas 2 páginas para teste
                min_desconto=20,  # Mínimo 20% de desconto
                min_preco=100,  # Preço mínimo R$ 100
                max_preco=5000,  # Preço máximo R$ 5000
                min_avaliacao=4.0,  # Mínimo 4 estrelas
                min_votos=5,  # Mínimo 5 votos
                apenas_frete_gratis=True,  # Apenas frete grátis
                apenas_lojas_oficiais=True,  # Apenas lojas oficiais
                max_requests=5  # Máximo 5 requisições simultâneas
            )
            
            # Exibe estatísticas
            logger.info(f"Total de ofertas encontradas: {len(ofertas)}")
            
            # Exibe as 5 primeiras ofertas (se houver)
            for i, oferta in enumerate(ofertas[:5], 1):
                logger.info(f"\n--- Oferta {i} ---")
                logger.info(f"Título: {oferta.get('titulo')}")
                logger.info(f"Preço: R$ {oferta.get('preco')}")
                if oferta.get('preco_original'):
                    logger.info(f"Preço Original: R$ {oferta.get('preco_original')}")
                logger.info(f"Desconto: {oferta.get('desconto', 0)}%")
                logger.info(f"Loja: {oferta.get('loja')}")
                logger.info(f"Avaliação: {oferta.get('avaliacao', 0)} ({oferta.get('votos', 0)} votos)")
                logger.info(f"Frete Grátis: {'Sim' if oferta.get('frete_gratis') else 'Não'}")
                logger.info(f"URL: {oferta.get('url_produto')}")
                logger.info(f"Fonte: {oferta.get('url_fonte')}")
            
            # Salva todas as ofertas em um arquivo JSON para análise
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f'ofertas_promobit_{timestamp}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(ofertas, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"\nDados completos salvos em: {output_file}")
            
        except Exception as e:
            logger.error(f"Erro durante o teste: {e}", exc_info=True)
        finally:
            await session.close()

if __name__ == "__main__":
    asyncio.run(test_scraper())
