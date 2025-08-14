"""
Teste para o módulo promobit_scraper_new.py

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
from promobit_scraper_new import buscar_ofertas_promobit, extrair_preco, normalizar_loja

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_promobit_final.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_extrair_preco():
    """Testa a função de extração de preços."""
    test_cases = [
        ("R$ 1.199,99 R$ 999,99 20% OFF", ("999.99", "1199.99", 20)),
        ("R$ 1.199,99", ("1199.99", None, None)),
        ("R$ 999,90 R$ 1.199,90 17% OFF", ("999.90", "1199.90", 17)),
        ("R$ 1.234,56", ("1234.56", None, None)),
    ]
    
    logger.info("\n=== TESTANDO EXTRAÇÃO DE PREÇOS ===")
    for texto, esperado in test_cases:
        resultado = extrair_preco(texto)
        status = "✅" if resultado == esperado else "❌"
        logger.info(f"{status} Teste: '{texto}'")
        logger.info(f"  Esperado: {esperado}")
        logger.info(f"  Obtido:   {resultado}")
        if status == "❌":
            logger.warning("  !!! FALHA NO TESTE !!!")

async def test_normalizar_loja():
    """Testa a normalização de nomes de lojas."""
    test_cases = [
        ("Magazine Luiza", "Magazine Luiza"),
        ("magalu", "Magazine Luiza"),
        ("americanas", "Americanas"),
        ("Kabum", "Kabum"),
        ("loja desconhecida", "Loja Desconhecida"),
    ]
    
    logger.info("\n=== TESTANDO NORMALIZAÇÃO DE LOJAS ===")
    for entrada, esperado in test_cases:
        resultado = normalizar_loja(entrada)
        status = "✅" if resultado == esperado else "❌"
        logger.info(f"{status} '{entrada}' -> '{resultado}'")
        if status == "❌":
            logger.warning(f"  Esperado: '{esperado}'")

async def test_buscar_ofertas():
    """Testa a função principal de busca de ofertas."""
    timeout = aiohttp.ClientTimeout(total=60)  # 60 segundos de timeout
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            logger.info("\n=== INICIANDO TESTE DO PROMOBIT SCRAPER ===\n")
            
            # Parâmetros de teste
            params = {
                'max_paginas': 2,  # Apenas 2 páginas para teste
                'min_desconto': 10,  # Mínimo 10% de desconto
                'categoria': 'informatica',
                'min_preco': 100,  # Preço mínimo R$ 100
                'max_preco': 5000,  # Preço máximo R$ 5000
                'min_avaliacao': 4.0,  # Mínimo 4 estrelas
                'min_votos': 5,  # Mínimo 5 votos
                'apenas_frete_gratis': False,  # Não filtrar por frete grátis para mais resultados
                'apenas_lojas_oficiais': False,  # Incluir todas as lojas
                'max_requests': 3  # Máximo de 3 requisições simultâneas
            }
            
            logger.info("Parâmetros da busca:")
            for chave, valor in params.items():
                logger.info(f"  {chave}: {valor}")
            
            # Chama a função de busca
            logger.info("\nIniciando busca de ofertas...")
            ofertas = await buscar_ofertas_promobit(session, **params)
            
            # Exibe os resultados
            logger.info(f"\n=== RESULTADOS DA BUSCA ===")
            logger.info(f"Total de ofertas encontradas: {len(ofertas)}")
            
            if ofertas:
                # Salva as ofertas em um arquivo JSON para análise
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f'ofertas_promobit_{timestamp}.json'
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(ofertas, f, ensure_ascii=False, indent=2, default=str)
                
                logger.info(f"\nDetalhes das ofertas (mostrando até 5):")
                for i, oferta in enumerate(ofertas[:5], 1):
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
                
                logger.info(f"\nTodas as ofertas foram salvas em: {output_file}")
            
            return len(ofertas) > 0  # Retorna True se encontrou ofertas
            
        except Exception as e:
            logger.error(f"Erro durante o teste: {e}", exc_info=True)
            return False

async def run_tests():
    """Executa todos os testes."""
    logger.info("=== INICIANDO TESTES DO PROMOBIT SCRAPPER ===\n")
    
    # Executa testes unitários
    await test_extrair_preco()
    await test_normalizar_loja()
    
    # Executa teste de integração
    logger.info("\n=== INICIANDO TESTE DE INTEGRAÇÃO ===\n")
    success = await test_buscar_ofertas()
    
    # Resultado final
    if success:
        logger.info("\n✅ TESTES CONCLUÍDOS COM SUCESSO!")
    else:
        logger.error("\n❌ ALGUNS TESTES FALHARAM OU NENHUMA OFERTA ENCONTRADA!")
    
    return success

if __name__ == "__main__":
    # Executa os testes
    test_result = asyncio.run(run_tests())
    
    # Encerra com código de status apropriado
    sys.exit(0 if test_result else 1)
