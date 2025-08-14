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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# URL base para busca no Pelando
BASE_URL = "https://www.pelando.com.br/search"

# Lista de palavras-chave para buscar ofertas relevantes
PALAVRAS_CHAVE = [
    'notebook', 'ssd', 'memória ram', 'placa de vídeo', 'processador',
    'monitor', 'mouse', 'teclado', 'headset', 'fone de ouvido',
    'webcam', 'impressora', 'roteador', 'cadeira gamer', 'mesa digitalizadora'
]

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
    Busca ofertas no Pelando baseado em palavras-chave de tecnologia.
    
    Args:
        session: Sessão aiohttp para fazer as requisições
        max_paginas: Número máximo de páginas para buscar por palavra-chave
        min_desconto: Percentual mínimo de desconto para considerar a oferta
        
    Returns:
        Lista de dicionários contendo as ofertas encontradas
    """
    ofertas = []
    
    try:
        for palavra_chave in PALAVRAS_CHAVE:
            logger.info(f"Buscando ofertas para: {palavra_chave}")
            
            for pagina in range(1, max_paginas + 1):
                params = {
                    'q': palavra_chave,
                    'order': 'recent',
                    'page': str(pagina)
                }
                
                try:
                    async with session.get(BASE_URL, params=params, headers=HEADERS, timeout=10) as response:
                        if response.status != 200:
                            logger.warning(f"Erro ao acessar busca para '{palavra_chave}': HTTP {response.status}")
                            break
                            
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Encontra todos os cards de oferta
                        cards = soup.select('article.thread')
                        
                        if not cards:
                            logger.warning(f"Nenhum card de oferta encontrado para '{palavra_chave}' na página {pagina}")
                            break
                        
                        logger.info(f"Encontrados {len(cards)} ofertas para '{palavra_chave}' na página {pagina}")
                        
                        for card in cards:
                            try:
                                # Extrai título e URL do produto
                                titulo_elem = card.select_one('a.thread-link')
                                if not titulo_elem:
                                    continue
                                    
                                titulo = titulo_elem.get_text(strip=True)
                                url_oferta = titulo_elem.get('href', '')
                                
                                # Garante que a URL completa está sendo usada
                                if url_oferta and not url_oferta.startswith('http'):
                                    url_oferta = f"https://www.pelando.com.br{url_oferta}"
                                
                                # Extrai preços
                                preco_elem = card.select_one('span.thread-price')
                                if not preco_elem:
                                    continue
                                    
                                preco_atual, preco_original = extrair_preco(preco_elem.get_text(strip=True))
                                
                                # Se não conseguiu extrair preço, pula para a próxima oferta
                                if not preco_atual:
                                    continue
                                
                                # Extrai URL da imagem
                                img_elem = card.select_one('img.thread-image')
                                imagem_url = ''
                                if img_elem:
                                    imagem_url = img_elem.get('src', '')
                                    if imagem_url.startswith('//'):
                                        imagem_url = f'https:{imagem_url}'
                                
                                # Extrai porcentagem de desconto
                                desconto_elem = card.select_one('span.thread-discount')
                                desconto = 0
                                
                                if desconto_elem:
                                    try:
                                        desconto_texto = desconto_elem.get_text(strip=True)
                                        desconto = int(re.search(r'\d+', desconto_texto).group())
                                    except (ValueError, AttributeError):
                                        pass
                                
                                # Filtra por desconto mínimo
                                if desconto < min_desconto:
                                    continue
                                
                                # Extrai nome da loja
                                loja_elem = card.select_one('span.thread-shop')
                                loja = loja_elem.get_text(strip=True) if loja_elem else 'Desconhecida'
                                
                                # Extrai URL do produto na loja
                                url_produto = card.select_one('a.cept-tt')
                                url_produto = url_produto.get('href', '') if url_produto else ''
                                
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
                                    'data_coleta': datetime.now().isoformat(),
                                    'palavra_chave': palavra_chave
                                }
                                
                                # Verifica se a oferta já foi adicionada (evita duplicatas)
                                if not any(o['url_produto'] == oferta['url_produto'] for o in ofertas):
                                    ofertas.append(oferta)
                                    logger.debug(f"Oferta adicionada: {titulo} - {preco_atual}")
                                
                            except Exception as e:
                                logger.error(f"Erro ao processar card: {e}", exc_info=True)
                                continue
                                
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout ao acessar busca para '{palavra_chave}' na página {pagina}")
                    break
                except Exception as e:
                    logger.error(f"Erro ao processar busca para '{palavra_chave}' na página {pagina}: {e}", exc_info=True)
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
            if oferta.get('palavra_chave'):
                print(f"Palavra-chave: {oferta['palavra_chave']}")
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
