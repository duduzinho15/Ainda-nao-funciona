"""
Teste direto para o Promobit Scraper
"""
import asyncio
import json
import logging
import sys
from datetime import datetime

import aiohttp

# Adiciona o diretório raiz ao path para importar o módulo
sys.path.append('.')
from promobit_scraper_new import buscar_ofertas_promobit

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_promobit_direct.log')
    ]
)
logger = logging.getLogger('promobit_test')

async def test_scraper():
    """Testa diretamente a função de scraping do Promobit."""
    logger.info("Iniciando teste direto do Promobit Scraper")
    
    # Configuração da sessão
    timeout = aiohttp.ClientTimeout(total=60)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Parâmetros de teste
            params = {
                'max_paginas': 1,  # Apenas 1 página para teste
                'min_desconto': 10,
                'categoria': 'informatica',
                'min_preco': 100,
                'max_preco': 5000,
                'min_avaliacao': 4.0,
                'min_votos': 5,
                'apenas_frete_gratis': False,
                'apenas_lojas_oficiais': False,
                'max_requests': 3
            }
            
            logger.info("Parâmetros da busca:")
            for key, value in params.items():
                logger.info(f"  {key}: {value}")
            
            # Executa o scraper
            logger.info("\nIniciando busca de ofertas...")
            ofertas = await buscar_ofertas_promobit(session, **params)
            
            # Exibe os resultados
            logger.info("\n=== RESULTADOS ===")
            logger.info(f"Total de ofertas encontradas: {len(ofertas)}")
            
            if ofertas:
                # Salva as ofertas em um arquivo JSON
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f'ofertas_promobit_{timestamp}.json'
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(ofertas, f, ensure_ascii=False, indent=2, default=str)
                
                logger.info(f"\nExibindo as primeiras 3 ofertas (todas salvas em {output_file}):")
                
                for i, oferta in enumerate(ofertas[:3], 1):
                    logger.info(f"\n--- Oferta #{i} ---")
                    logger.info(f"Título: {oferta['titulo']}")
                    logger.info(f"Loja: {oferta['loja']}")
                    logger.info(f"Preço: {oferta['preco']}")
                    if oferta['preco_original']:
                        logger.info(f"Preço original: {oferta['preco_original']}")
                    logger.info(f"Desconto: {oferta['desconto']}%")
                    logger.info(f"Avaliação: {oferta['avaliacao']} ({oferta['votos']} votos)")
                    logger.info(f"Frete Grátis: {'Sim' if oferta['frete_gratis'] else 'Não'}")
                    logger.info(f"URL: {oferta['url_produto']}")
                    if oferta['imagem_url']:
                        logger.info(f"Imagem: {oferta['imagem_url']}")
                
                return True
            else:
                logger.warning("Nenhuma oferta encontrada.")
                return False
                
    except Exception as e:
        logger.error(f"Erro durante o teste: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Executa o teste
    success = asyncio.run(test_scraper())
    
    # Encerra com código de status apropriado
    sys.exit(0 if success else 1)
