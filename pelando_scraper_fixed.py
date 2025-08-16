#!/usr/bin/env python3
"""
Módulo para busca de ofertas no site Pelando.

Este módulo implementa um scraper para buscar ofertas de produtos de tecnologia
no site Pelando, respeitando as diretrizes do robots.txt.
"""
import asyncio
import logging
import re
import json
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
import aiohttp
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Headers para simular um navegador
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}

def extrair_preco(texto: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extrai preço atual e original de um texto de preço do Pelando.
    
    Args:
        texto: Texto contendo os preços (ex: "R$ 1.199,99 R$ 999,99")
        
    Returns:
        tuple: (preco_atual, preco_original) ou (preco_atual, None) se não houver desconto
    """
    # Encontra todos os valores numéricos no formato R$ X.XXX,XX
    precos = re.findall(r'R\$\s*[\d\.]+,\d{2}', texto)
    
    if not precos:
        return None, None
    
    # Remove o símbolo R$ e espaços para padronização
    precos = [p.replace('R$', '').strip() for p in precos]
    
    # Se tiver apenas um preço, retorna ele como preço atual
    if len(precos) == 1:
        return precos[0], None
    
    # Se tiver mais de um, assume que o primeiro é o preço original e o segundo o com desconto
    return precos[1], precos[0]

async def buscar_ofertas_pelando(
    session: aiohttp.ClientSession,
    max_paginas: int = 3,
    min_desconto: int = 10
) -> List[Dict[str, Any]]:
    """
    Busca ofertas no Pelando extraindo da página principal.
    
    Args:
        session: Sessão aiohttp para fazer as requisições
        max_paginas: Número máximo de páginas para buscar
        min_desconto: Percentual mínimo de desconto para considerar a oferta
        
    Returns:
        Lista de dicionários contendo as ofertas encontradas
    """
    ofertas = []
    
    try:
        # URLs das páginas principais do Pelando
        urls = [
            "https://www.pelando.com.br/",
            "https://www.pelando.com.br/hot",
            "https://www.pelando.com.br/ofertas"
        ]
        
        for url in urls[:max_paginas]:
            logger.info(f"Buscando ofertas em: {url}")
            
            try:
                async with session.get(url, headers=HEADERS, timeout=15) as response:
                    if response.status != 200:
                        logger.warning(f"Erro ao acessar {url}: HTTP {response.status}")
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Encontra todos os cards de oferta (usando seletores CSS modernos do Pelando)
                    cards = soup.select('[class*="default-deal-card"], [class*="deal-card"]')
                    
                    if not cards:
                        logger.warning(f"Nenhum card de oferta encontrado em {url}")
                        continue
                    
                    logger.info(f"Encontrados {len(cards)} ofertas em {url}")
                    
                    for card in cards:
                        try:
                            # Extrai título e URL do produto
                            titulo_elem = card.select_one('[class*="deal-card-title"] a, [class*="default-deal-card-title"] a, a[href*="/thread/"]')
                            if not titulo_elem:
                                logger.debug(f"Card sem título: {card.get('class', [])}")
                                continue
                                
                            titulo = titulo_elem.get_text(strip=True)
                            if not titulo or len(titulo) < 10:
                                logger.debug(f"Título muito curto: '{titulo}'")
                                continue
                                
                            url_oferta = titulo_elem.get('href', '')
                            
                            # Garante que a URL completa está sendo usada
                            if url_oferta and not url_oferta.startswith('http'):
                                url_oferta = f"https://www.pelando.com.br{url_oferta}"
                            
                            # Extrai preços (procura por diferentes padrões)
                            preco_elem = card.select_one('[class*="price"], [class*="deal-price"], .price, .deal-price')
                            if not preco_elem:
                                # Tenta extrair preço do texto do card
                                card_text = card.get_text()
                                preco_match = re.search(r'R\$\s*[\d\.]+,\d{2}', card_text)
                                if preco_match:
                                    preco_atual, preco_original = extrair_preco(preco_match.group())
                                    logger.debug(f"Preço extraído do texto: {preco_atual}")
                                else:
                                    logger.debug(f"Card sem preço: {titulo[:50]}...")
                                    continue
                            else:
                                preco_atual, preco_original = extrair_preco(preco_elem.get_text(strip=True))
                                logger.debug(f"Preço extraído do elemento: {preco_atual}")
                            
                            # Se não conseguiu extrair preço, pula para a próxima oferta
                            if not preco_atual:
                                logger.debug(f"Preço inválido: {preco_atual}")
                                continue
                            
                            # Extrai URL da imagem
                            img_elem = card.select_one('img')
                            imagem_url = ''
                            if img_elem:
                                imagem_url = img_elem.get('src', '')
                                if imagem_url.startswith('//'):
                                    imagem_url = f'https:{imagem_url}'
                            
                            # Extrai porcentagem de desconto (procura no texto do card)
                            card_text = card.get_text()
                            desconto = 0
                            desconto_match = re.search(r'(\d+)%?\s*off|(\d+)%?\s*desconto|(\d+)%?\s*menos', card_text, re.IGNORECASE)
                            if desconto_match:
                                for group in desconto_match.groups():
                                    if group:
                                        desconto = int(group)
                                        break
                            
                            # Filtra por desconto mínimo (mais flexível para o Pelando)
                            if desconto < min_desconto and desconto > 0:
                                # Se não tem desconto específico, aceita a oferta mesmo assim
                                pass
                            
                            # Extrai nome da loja
                            loja_elem = card.select_one('[class*="deal-card-store"] a, [class*="default-deal-card-store"] a')
                            loja = loja_elem.get_text(strip=True) if loja_elem else 'Desconhecida'
                            
                            # Extrai URL do produto na loja (procura por links externos)
                            url_produto = ''
                            external_links = card.select('a[href*="http"]')
                            for link in external_links:
                                href = link.get('href', '')
                                if any(domain in href for domain in ['amazon', 'shopee', 'mercadolivre', 'magazineluiza', 'aliexpress']):
                                    url_produto = href
                                    break
                            
                            # Se não tem URL do produto, usa a URL da oferta no Pelando
                            if not url_produto and url_oferta:
                                url_produto = url_oferta
                            
                            # Adiciona a oferta à lista
                            oferta = {
                                'titulo': titulo,
                                'url_produto': url_produto,
                                'url_fonte': url_oferta,
                                'preco': preco_atual,
                                'preco_original': preco_original,
                                'loja': loja,
                                'fonte': 'Pelando',
                                'imagem_url': imagem_url,
                                'desconto': desconto,
                                'data_coleta': datetime.now().isoformat()
                            }
                            
                            # Verifica se a oferta já foi adicionada (evita duplicatas)
                            if not any(o['url_produto'] == oferta['url_produto'] for o in ofertas):
                                ofertas.append(oferta)
                                logger.debug(f"Oferta adicionada: {titulo} - {preco_atual}")
                            
                        except Exception as e:
                            logger.error(f"Erro ao processar card: {e}", exc_info=True)
                            continue
                            
            except asyncio.TimeoutError:
                logger.warning(f"Timeout ao acessar {url}")
                continue
            except Exception as e:
                logger.error(f"Erro ao processar {url}: {e}", exc_info=True)
                continue
        
        logger.info(f"Busca concluída. Total de ofertas encontradas: {len(ofertas)}")
        return ofertas
        
    except Exception as e:
        logger.error(f"Erro inesperado ao buscar ofertas: {e}", exc_info=True)
        return []

async def main():
    """Função de teste para o módulo."""
    async with aiohttp.ClientSession() as session:
        ofertas = await buscar_ofertas_pelando(session, max_paginas=1)  # Apenas 1 página para teste
        
        print(f"\n=== OFERTAS ENCONTRADAS ({len(ofertas)}) ===\n")
        
        for i, oferta in enumerate(ofertas[:5], 1):  # Mostra apenas as 5 primeiras para teste
            print(f"\n--- Oferta {i} ---")
            print(f"Título: {oferta['titulo']}")
            print(f"Loja: {oferta['loja']}")
            print(f"Preço: R$ {oferta['preco']}")
            if oferta['preco_original']:
                print(f"Preço original: R$ {oferta['preco_original']}")
            print(f"Desconto: {oferta['desconto']}%")
            print(f"URL: {oferta['url_produto']}")
            print(f"Fonte: {oferta['fonte']}")
            if oferta['imagem_url']:
                print(f"Imagem: {oferta['imagem_url']}")
            print("-" * 50)

if __name__ == "__main__":
    # Configura logging para debug
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    
    # Executa o teste
    asyncio.run(main())
