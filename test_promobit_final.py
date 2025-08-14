"""
Test script for the Promobit scraper.
"""
import asyncio
import json
import logging
from datetime import datetime

from promobit_scraper import buscar_ofertas_promobit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_promobit.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('test_promobit')

async def test_scraper():
    """Test the Promobit scraper with different configurations."""
    import aiohttp
    
    # Create an aiohttp session
    timeout = aiohttp.ClientTimeout(total=60)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Test configuration 1: Basic search
        logger.info("\n" + "="*80)
        logger.info("TEST 1: Basic search (Electronics category, 2 pages)")
        logger.info("="*80)
        
        ofertas = await buscar_ofertas_promobit(
            session=session,
            categoria='eletronicos',
            max_paginas=2,
            min_desconto=10,
            min_preco=100,
            max_preco=5000,
            min_avaliacao=4.0,
            min_votos=5,
            apenas_frete_gratis=False,
            apenas_lojas_oficiais=False,
            max_requests=3
        )
        
        logger.info(f"Found {len(ofertas)} offers in Test 1")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f'promobit_results_test1_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(ofertas, f, ensure_ascii=False, indent=2, default=str)
        
        # Test configuration 2: Filter by free shipping
        logger.info("\n" + "="*80)
        logger.info("TEST 2: Filter by free shipping (Computers category, 1 page)")
        logger.info("="*80)
        
        ofertas = await buscar_ofertas_promobit(
            session=session,
            categoria='informatica',
            max_paginas=1,
            min_desconto=20,
            min_preco=500,
            max_preco=3000,
            min_avaliacao=4.0,
            min_votos=10,
            apenas_frete_gratis=True,
            apenas_lojas_oficiais=False,
            max_requests=2
        )
        
        logger.info(f"Found {len(ofertas)} offers with free shipping in Test 2")
        
        # Save results to file
        with open(f'promobit_results_test2_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(ofertas, f, ensure_ascii=False, indent=2, default=str)
        
        # Test configuration 3: Official stores only
        logger.info("\n" + "="*80)
        logger.info("TEST 3: Official stores only (Gaming category, 1 page)")
        logger.info("="*80)
        
        ofertas = await buscar_ofertas_promobit(
            session=session,
            categoria='games',
            max_paginas=1,
            min_desconto=15,
            min_preco=1000,
            max_preco=5000,
            min_avaliacao=4.5,
            min_votos=5,
            apenas_frete_gratis=False,
            apenas_lojas_oficiais=True,
            max_requests=2
        )
        
        logger.info(f"Found {len(ofertas)} offers from official stores in Test 3")
        
        # Save results to file
        with open(f'promobit_results_test3_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(ofertas, f, ensure_ascii=False, indent=2, default=str)

if __name__ == "__main__":
    logger.info("Starting Promobit scraper tests...")
    asyncio.run(test_scraper())
    logger.info("Tests completed. Check the log files for details.")
