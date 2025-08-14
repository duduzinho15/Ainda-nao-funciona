"""
Script de teste para o módulo promobit_scraper_clean.py

Este script testa a funcionalidade básica do scraper do Promobit com as URLs atualizadas.
"""
import asyncio
import logging
import aiohttp
from promobit_scraper_clean import buscar_ofertas_promobit

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_promobit_updated.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('test_promobit_updated')

async def main():
    """Função principal para testar o scraper do Promobit."""
    logger.info("=== Iniciando teste do Promobit Scraper ===")
    
    # Configuração da sessão HTTP
    connector = aiohttp.TCPConnector(force_close=True, enable_cleanup_closed=True)
    timeout = aiohttp.ClientTimeout(total=60)  # 60 segundos de timeout
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        try:
            logger.info("Testando busca de ofertas na categoria 'informatica'...")
            ofertas = await buscar_ofertas_promobit(
                session=session,
                max_paginas=1,  # Apenas a primeira página para teste
                min_desconto=10,
                categoria='informatica',
                min_avaliacao=4.0,
                min_votos=5,
                apenas_frete_gratis=False,
                apenas_lojas_oficiais=False,
                max_requests=3
            )
            
            # Exibe os resultados
            if ofertas:
                logger.info(f"Encontradas {len(ofertas)} ofertas na categoria 'informatica'")
                for i, oferta in enumerate(ofertas[:5], 1):  # Mostra apenas as 5 primeiras ofertas
                    logger.info(f"\nOferta {i}:")
                    logger.info(f"  Título: {oferta.get('titulo', 'N/A')}")
                    logger.info(f"  Preço: {oferta.get('preco_atual', 'N/A')} (original: {oferta.get('preco_original', 'N/A')})")
                    logger.info(f"  Desconto: {oferta.get('desconto', 'N/A')}%")
                    logger.info(f"  Loja: {oferta.get('loja', 'N/A')}")
                    logger.info(f"  URL: {oferta.get('url', 'N/A')}")
            else:
                logger.warning("Nenhuma oferta encontrada na categoria 'informatica'")
                
            # Testa uma categoria inválida para verificar o tratamento de erros
            logger.info("\nTestando busca em categoria inválida...")
            ofertas_invalidas = await buscar_ofertas_promobit(
                session=session,
                max_paginas=1,
                categoria='categoria_invalida',
                max_requests=1
            )
            
            if not ofertas_invalidas:
                logger.info("Teste de categoria inválida passou com sucesso (nenhuma oferta retornada)")
            
        except Exception as e:
            logger.error(f"Erro durante o teste: {e}", exc_info=True)
        finally:
            await session.close()
    
    logger.info("=== Teste concluído ===")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Teste interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}", exc_info=True)
