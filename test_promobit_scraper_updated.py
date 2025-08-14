"""
Teste para o módulo promobit_scraper.py

Este script testa a funcionalidade básica do scraper do Promobit.
"""
import asyncio
import json
import logging
import sys
from datetime import datetime

import aiohttp

# Adiciona o diretório raiz ao path para importar o módulo
sys.path.append('.')
from promobit_scraper import buscar_ofertas_promobit

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_promobit_scraper.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_buscar_ofertas():
    """Testa a função buscar_ofertas_promobit."""
    timeout = aiohttp.ClientTimeout(total=30)  # 30 segundos de timeout
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            logger.info("Iniciando teste do Promobit Scraper...")
            
            # Parâmetros de teste
            params = {
                'max_paginas': 2,  # Apenas 2 páginas para teste
                'min_desconto': 10,  # Mínimo 10% de desconto
                'categoria': 'informatica',
                'min_preco': 100,  # Preço mínimo R$ 100
                'max_preco': 5000,  # Preço máximo R$ 5000
                'min_avaliacao': 4.0,  # Mínimo 4 estrelas
                'min_votos': 5,  # Mínimo 5 votos
                'apenas_frete_gratis': True,
                'apenas_lojas_oficiais': True,
                'max_requests': 3  # Máximo de 3 requisições simultâneas
            }
            
            logger.info(f"Parâmetros do teste: {json.dumps(params, indent=2, ensure_ascii=False)}")
            
            # Chama a função de busca
            ofertas = await buscar_ofertas_promobit(session, **params)
            
            # Exibe os resultados
            logger.info(f"Total de ofertas encontradas: {len(ofertas)}")
            
            for i, oferta in enumerate(ofertas, 1):
                logger.info(f"\nOferta #{i}:")
                logger.info(f"  Título: {oferta['titulo']}")
                logger.info(f"  Preço: {oferta['preco']}")
                if oferta['preco_original']:
                    logger.info(f"  Preço Original: {oferta['preco_original']}")
                logger.info(f"  Desconto: {oferta['desconto']}%")
                logger.info(f"  Loja: {oferta['loja']}")
                logger.info(f"  Avaliação: {oferta['avaliacao']} ({oferta['votos']} votos)")
                logger.info(f"  Frete Grátis: {'Sim' if oferta['frete_gratis'] else 'Não'}")
                logger.info(f"  URL do Produto: {oferta['url_produto']}")
                logger.info(f"  URL da Oferta: {oferta['url_fonte']}")
                if oferta['imagem_url']:
                    logger.info(f"  Imagem: {oferta['imagem_url']}")
            
            # Salva as ofertas em um arquivo JSON para análise posterior
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'ofertas_promobit_{timestamp}.json'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(ofertas, f, ensure_ascii=False, indent=2)
                
            logger.info(f"\nOfertas salvas em: {output_file}")
            
            return len(ofertas) > 0  # Retorna True se encontrou ofertas
            
        except Exception as e:
            logger.error(f"Erro durante o teste: {e}", exc_info=True)
            return False

if __name__ == "__main__":
    # Executa o teste
    success = asyncio.run(test_buscar_ofertas())
    
    if success:
        logger.info("✅ Teste do Promobit Scraper concluído com sucesso!")
    else:
        logger.error("❌ O teste do Promobit Scraper falhou ou não encontrou ofertas.")
    
    sys.exit(0 if success else 1)
