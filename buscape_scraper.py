#!/usr/bin/env python3
"""
Scraper para o Buscapé - Comparador de preços
Coleta ofertas de produtos com preços e avaliações
"""
import asyncio
import logging
import random
import re
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('buscape_scraper.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger('buscape_scraper')

# User Agents para rotação
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
]

# URLs base para busca de ofertas
BASE_URL = "https://www.buscape.com.br"
CATEGORIAS = {
    'celulares': '/celular-e-smartphone',
    'notebooks': '/notebook',
    'tvs': '/tv',
    'geladeiras': '/geladeira',
    'lavadoras': '/lavadora-de-roupas',
    'ar-condicionado': '/ar-condicionado',
    'fogao': '/fogao',
    'tablet': '/tablet',
    'micro-ondas': '/micro-ondas',
    'forno': '/forno',
    'fone-de-ouvido': '/fone-de-ouvido-e-headset',
    'console': '/console-de-video-game',
    'impressora': '/impressora-e-multifuncional',
    'monitor': '/monitor',
    'smartwatch': '/smartwatch',
    'caixa-de-som': '/caixa-de-som-bluetooth',
    'tenis': '/tenis',
    'cafeteira': '/cafeteira-eletrica',
    'purificador': '/purificador-de-agua',
    'livros': '/livros',
    'panelas': '/panelas'
}

# URLs reais baseadas na estrutura do site
CATEGORIAS_REAIS = {
    'celulares': '/celular-e-smartphone',
    'notebooks': '/notebook',
    'tvs': '/tv',
    'geladeiras': '/geladeira',
    'lavadoras': '/lavadora-de-roupas',
    'ar-condicionado': '/ar-condicionado',
    'fogao': '/fogao',
    'tablet': '/tablet',
    'micro-ondas': '/micro-ondas',
    'forno': '/forno',
    'fone-de-ouvido': '/fone-de-ouvido-e-headset',
    'console': '/console-de-video-game',
    'impressora': '/impressora-e-multifuncional',
    'monitor': '/monitor',
    'smartwatch': '/smartwatch',
    'caixa-de-som': '/caixa-de-som-bluetooth',
    'tenis': '/tenis',
    'cafeteira': '/cafeteira-eletrica',
    'purificador': '/purificador-de-agua',
    'livros': '/livros',
    'panelas': '/panelas'
}

def get_random_headers() -> dict:
    """Retorna headers aleatórios para evitar bloqueio."""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.buscape.com.br/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

def normalizar_loja(nome_loja: str) -> str:
    """Normaliza o nome da loja para consistência."""
    if not nome_loja:
        return "Desconhecida"
    
    nome_loja = nome_loja.strip().lower()
    
    # Mapeamento de variações de nomes de lojas
    lojas = {
        'amazon': 'Amazon',
        'magazine luiza': 'Magazine Luiza',
        'magalu': 'Magazine Luiza',
        'americanas': 'Americanas',
        'submarino': 'Submarino',
        'shoptime': 'Shoptime',
        'ponto frio': 'Ponto Frio',
        'pontofrio': 'Ponto Frio',
        'casas bahia': 'Casas Bahia',
        'casasbahia': 'Casas Bahia',
        'extra': 'Extra',
        'carrefour': 'Carrefour',
        'kabum': 'Kabum!',
        'pichau': 'Pichau',
        'terabyte': 'Terabyte',
        'fast shop': 'Fast Shop',
        'fastshop': 'Fast Shop',
        'polishop': 'Polishop',
        'cama inbox': 'Cama Inbox',
        'aaz web': 'AAZ Web',
        'carioca móveis': 'Carioca Móveis',
        'mercadotek': 'Mercadotek',
        'nutrify': 'Nutrify',
        'gorila shield': 'Gorila Shield',
        'spicy': 'Spicy',
        'b&m shop': 'B&M Shop',
        'unicpharma': 'Unicpharma'
    }
    
    for variação, nome_normalizado in lojas.items():
        if variação in nome_loja:
            return nome_normalizado
    
    return nome_loja.title()

def extrair_preco(texto_preco: str) -> tuple:
    """Extrai preço atual e original de um texto de preço do Buscapé."""
    if not texto_preco:
        return 0.0, 0.0
    
    # Remove caracteres especiais e espaços
    texto_limpo = re.sub(r'[^\d,.]', '', texto_preco)
    
    try:
        # Converte para float
        preco = float(texto_limpo.replace(',', '.'))
        return preco, preco  # Buscapé geralmente mostra apenas o preço atual
    except ValueError:
        return 0.0, 0.0

def extrair_avaliacao(texto_avaliacao: str) -> float:
    """Extrai avaliação de um texto de avaliação do Buscapé."""
    if not texto_avaliacao:
        return 0.0
    
    # Busca por padrão de avaliação (ex: 4.7, 4.8)
    match = re.search(r'(\d+\.?\d*)', texto_avaliacao)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    
    return 0.0

async def buscar_ofertas_buscape(
    session: aiohttp.ClientSession,
    categoria: str = None,
    max_paginas: int = 3,
    delay: float = 1.0
) -> List[Dict[str, Any]]:
    """
    Busca ofertas no Buscapé baseado em categoria ou busca geral.
    
    Args:
        session: Sessão HTTP assíncrona
        categoria: Categoria específica para buscar
        max_paginas: Número máximo de páginas para buscar
        delay: Delay entre requisições em segundos
    
    Returns:
        Lista de ofertas encontradas
    """
    ofertas = []
    
    try:
        # Sempre busca na página inicial do Buscapé
        url_busca = BASE_URL
        logger.info("🔍 Buscando ofertas gerais no Buscapé")
        
        headers = get_random_headers()
        
        async with session.get(url_busca, headers=headers) as response:
            if response.status != 200:
                logger.error(f"❌ Erro ao acessar {url_busca}: {response.status}")
                return ofertas
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Busca por produtos na página inicial
            produtos = soup.find_all(['div', 'article'], class_=re.compile(r'product|item|card|oferta'))
            
            if not produtos:
                # Fallback: busca por elementos com links de produto
                produtos = soup.find_all('a', href=re.compile(r'/p/|/produto/'))
            
            logger.info(f"🔍 Encontrados {len(produtos)} produtos para análise")
            
            for produto in produtos[:20]:  # Limita a 20 produtos por página
                try:
                    oferta = extrair_oferta_produto(produto, categoria)
                    if oferta:
                        ofertas.append(oferta)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao extrair produto: {e}")
                    continue
                
                # Delay entre produtos
                await asyncio.sleep(delay * 0.1)
            
            logger.info(f"✅ {len(ofertas)} ofertas extraídas com sucesso")
            
    except Exception as e:
        logger.error(f"❌ Erro geral na busca: {e}")
    
    return ofertas

def extrair_oferta_produto(produto_element, categoria: str = None) -> Optional[Dict[str, Any]]:
    """Extrai informações de uma oferta de produto do Buscapé."""
    try:
        # Título do produto
        titulo_elem = produto_element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or \
                     produto_element.find('span', class_=re.compile(r'title|name|titulo'))
        
        if not titulo_elem:
            return None
        
        titulo = titulo_elem.get_text(strip=True)
        if not titulo or len(titulo) < 5:
            return None
        
        # Preço
        preco_elem = produto_element.find(['span', 'div'], class_=re.compile(r'price|preco|valor')) or \
                    produto_element.find(string=re.compile(r'R\$\s*\d+'))
        
        preco_texto = preco_elem.get_text(strip=True) if hasattr(preco_elem, 'get_text') else str(preco_elem)
        preco_atual, preco_original = extrair_preco(preco_texto)
        
        # Avaliação
        avaliacao_elem = produto_element.find(['span', 'div'], class_=re.compile(r'rating|avaliacao|score')) or \
                        produto_element.find(string=re.compile(r'\d+\.?\d*'))
        
        avaliacao_texto = avaliacao_elem.get_text(strip=True) if hasattr(avaliacao_elem, 'get_text') else str(avaliacao_elem)
        avaliacao = extrair_avaliacao(avaliacao_texto)
        
        # Loja
        loja_elem = produto_element.find(['span', 'div'], class_=re.compile(r'store|loja|vendor')) or \
                   produto_element.find('img', alt=re.compile(r'logo|store'))
        
        loja = "Buscapé"
        if loja_elem:
            loja_texto = loja_elem.get_text(strip=True) if hasattr(loja_elem, 'get_text') else loja_elem.get('alt', '')
            if loja_texto:
                loja = normalizar_loja(loja_texto)
        
        # Link do produto
        link_elem = produto_element.find('a', href=True)
        link_produto = ""
        if link_elem:
            link_produto = urljoin(BASE_URL, link_elem['href'])
        
        # Imagem
        img_elem = produto_element.find('img')
        imagem = ""
        if img_elem:
            imagem = urljoin(BASE_URL, img_elem.get('src', img_elem.get('data-src', '')))
        
        # Calcula desconto
        desconto = 0
        if preco_original > preco_atual > 0:
            desconto = int(((preco_original - preco_atual) / preco_original) * 100)
        
        # Cria oferta
        oferta = {
            'titulo': titulo,
            'preco_atual': preco_atual,
            'preco_original': preco_original if preco_original > preco_atual else preco_atual,
            'desconto_percentual': desconto,
            'loja': loja,
            'avaliacao': avaliacao,
            'link_produto': link_produto,
            'imagem': imagem,
            'categoria': categoria or 'geral',
            'fonte': 'Buscapé',
            'timestamp': datetime.now().isoformat(),
            'plataforma': 'buscape'
        }
        
        return oferta
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao extrair oferta: {e}")
        return None

async def buscar_ofertas_por_palavra_chave(
    session: aiohttp.ClientSession,
    palavra_chave: str,
    max_resultados: int = 10
) -> List[Dict[str, Any]]:
    """Busca ofertas por palavra-chave específica no Buscapé."""
    try:
        # Busca na página de busca do Buscapé
        url_busca = f"{BASE_URL}/search?q={palavra_chave}"
        
        headers = get_random_headers()
        
        async with session.get(url_busca, headers=headers) as response:
            if response.status != 200:
                logger.error(f"❌ Erro na busca por '{palavra_chave}': {response.status}")
                return []
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Busca por produtos na página de resultados
            produtos = soup.find_all(['div', 'article'], class_=re.compile(r'product|item|card|result'))
            
            ofertas = []
            for produto in produtos[:max_resultados]:
                oferta = extrair_oferta_produto(produto, palavra_chave)
                if oferta:
                    ofertas.append(oferta)
            
            logger.info(f"✅ Encontradas {len(ofertas)} ofertas para '{palavra_chave}'")
            return ofertas
            
    except Exception as e:
        logger.error(f"❌ Erro na busca por palavra-chave: {e}")
        return []

async def main():
    """Função principal para teste"""
    print("🚀 TESTANDO SCRAPER DO BUSCAPÉ")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Testa busca por categoria
        print("\n🔍 Testando busca por categoria (celulares)...")
        ofertas_categoria = await buscar_ofertas_buscape(session, 'celulares', max_paginas=1)
        
        print(f"✅ {len(ofertas_categoria)} ofertas encontradas na categoria")
        
        # Testa busca por palavra-chave
        print("\n🔍 Testando busca por palavra-chave (smartphone)...")
        ofertas_palavra = await buscar_ofertas_por_palavra_chave(session, 'smartphone', max_resultados=5)
        
        print(f"✅ {len(ofertas_palavra)} ofertas encontradas por palavra-chave")
        
        # Mostra algumas ofertas
        todas_ofertas = ofertas_categoria + ofertas_palavra
        print(f"\n📊 Total de ofertas: {len(todas_ofertas)}")
        
        for i, oferta in enumerate(todas_ofertas[:3], 1):
            print(f"\n{i}. {oferta['titulo'][:50]}...")
            print(f"   💰 R$ {oferta['preco_atual']:.2f}")
            print(f"   🏪 {oferta['loja']}")
            print(f"   ⭐ {oferta['avaliacao']:.1f}")

if __name__ == "__main__":
    asyncio.run(main())
