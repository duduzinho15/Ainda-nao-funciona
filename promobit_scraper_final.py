"""
Módulo para busca de ofertas no site Promobit.
Versão final com seletores otimizados e tratamento de erros robusto.
"""
import asyncio
import logging
import random
import re
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import aiohttp
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('promobit_scraper.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger('promobit_scraper')

# User Agents para rotação
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
]

# URLs base para busca de ofertas
BASE_URL = "https://www.promobit.com.br/"
CATEGORIAS = {
    'informatica': 'ofertas/informatica/',
    'eletronicos': 'ofertas/eletronicos/',
    'games': 'ofertas/games/',
    'celulares': 'ofertas/celulares/',
    'tv-e-video': 'ofertas/tv-e-video/',
    'audio': 'ofertas/audio/',
    'eletrodomesticos': 'ofertas/eletrodomesticos/',
    'casa-e-cozinha': 'ofertas/casa-e-cozinha/',
    'livros': 'ofertas/livros/',
    'moda': 'ofertas/moda/',
    'saude': 'ofertas/saude/',
    'beleza': 'ofertas/beleza/',
    'esporte': 'ofertas/esporte/',
    'automotivo': 'ofertas/automotivo/',
    'brinquedos': 'ofertas/brinquedos/',
    'outros': 'ofertas/outros/'
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
        'Referer': 'https://www.promobit.com.br/',
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
        'alza': 'Alza',
        'aliexpress': 'AliExpress',
        'mercadolivre': 'Mercado Livre',
        'ml': 'Mercado Livre',
        'dell': 'Dell',
        'lenovo': 'Lenovo',
        'acer': 'Acer',
        'asus': 'ASUS'
    }
    
    # Verifica se o nome da loja está no mapeamento
    for key, value in lojas.items():
        if key in nome_loja:
            return value
    
    # Se não encontrar, retorna o nome original com a primeira letra maiúscula
    return nome_loja.capitalize()

def extrair_preco(texto: str) -> float:
    """Extrai o valor numérico de um texto de preço."""
    if not texto:
        return 0.0
    
    # Remove caracteres não numéricos, exceto vírgula e ponto
    valor = re.sub(r'[^\d,]', '', texto)
    
    # Substitui vírgula por ponto e converte para float
    try:
        # Se houver apenas uma vírgula, assume que é o separador decimal
        if valor.count(',') == 1:
            valor = valor.replace('.', '').replace(',', '.')
        # Se houver mais de uma vírgula, assume que é o separador de milhar
        elif valor.count(',') > 1:
            valor = valor.replace('.', '').replace(',', '')
        
        return float(valor) if valor else 0.0
    except (ValueError, AttributeError):
        return 0.0

def extrair_desconto(texto: str) -> int:
    """Extrai o valor percentual de desconto de um texto."""
    if not texto:
        return 0
    
    # Procura por padrões como "10%", "-10%", "10% OFF", etc.
    padroes = [
        r'(\d+)%',
        r'-(\d+)%',
        r'(\d+)%\s*OFF',
        r'OFF\s*(\d+)%',
        r'desconto\s*de\s*(\d+)%',
        r'(\d+)\s*%',
    ]
    
    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue
    
    return 0
