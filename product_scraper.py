"""
Módulo para extrair informações de produtos a partir de URLs de várias lojas.

Este módulo contém funções para fazer scraping de páginas de produtos e extrair
informações como título, preço, preço original e URL da imagem.

Lojas suportadas:
- Aliexpress
- Amazon
- Mercado Livre
- Magazine Luiza (Magalu)
- Shopee
"""

import re
import json
import logging
import random
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, Any, List, Tuple, Callable
from urllib.parse import urlparse, parse_qs, urljoin
from dataclasses import dataclass

# Configuração de logging
logger = logging.getLogger('product_scraper')

# Configuração de headers para simular um navegador
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}

# Lista de user agents para rotação
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
]

@dataclass
class ProductInfo:
    """Classe para armazenar informações padronizadas sobre um produto."""
    title: str
    price: str
    original_price: Optional[str] = None
    image_url: Optional[str] = None
    store: str = ""
    url: str = ""
    currency: str = "R$"
    available: bool = True
    discount: Optional[int] = None


def get_random_user_agent() -> str:
    """Retorna um user agent aleatório da lista."""
    return random.choice(USER_AGENTS)


def make_request(url: str, max_retries: int = 3, delay: float = 1.5) -> Optional[requests.Response]:
    """
    Faz uma requisição HTTP com tratamento de erros e retentativas.
    
    Args:
        url: URL para fazer a requisição
        max_retries: Número máximo de tentativas
        delay: Tempo de espera entre as tentativas em segundos
        
    Returns:
        Response object ou None em caso de falha
    """
    headers = DEFAULT_HEADERS.copy()
    
    for attempt in range(max_retries):
        try:
            # Rotaciona o user agent a cada tentativa
            headers['User-Agent'] = get_random_user_agent()
            
            # Adiciona um pequeno delay aleatório entre requisições
            time_to_wait = delay * (1 + random.random())  # Entre delay e 2*delay
            time.sleep(time_to_wait)
            
            logger.debug(f"Fazendo requisição para {url} (tentativa {attempt + 1}/{max_retries})")
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=15,
                allow_redirects=True
            )
            
            # Verifica se a resposta é HTML
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type and 'application/json' not in content_type:
                logger.warning(f"Resposta não é HTML/JSON: {content_type}")
                raise requests.RequestException("Tipo de conteúdo inválido")
                
            response.raise_for_status()
            return response
            
        except requests.exceptions.TooManyRedirects:
            logger.error(f"Muitos redirecionamentos para {url}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Tentativa {attempt + 1}/{max_retries} - Erro na requisição para {url}: {e}")
            if attempt < max_retries - 1:
                # Aumenta o tempo de espera a cada tentativa
                time.sleep(delay * (attempt + 1))
            else:
                logger.error(f"Falha após {max_retries} tentativas: {e}")
                return None

def extract_price(price_text: str) -> Optional[float]:
    """
    Extrai o valor numérico de uma string de preço.
    
    Args:
        price_text: String contendo o preço (ex: "R$ 1.299,99")
        
    Returns:
        float: Valor numérico do preço ou None se não for possível extrair
    """
    if not price_text or not isinstance(price_text, str):
        return None
        
    try:
        # Remove todos os caracteres não numéricos, exceto vírgula e ponto
        clean_value = re.sub(r'[^\d,]', '', price_text)
        # Remove pontos de milhar e substitui vírgula por ponto
        clean_value = clean_value.replace('.', '').replace(',', '.')
        return float(clean_value)
    except (ValueError, AttributeError) as e:
        logger.debug(f"Erro ao extrair preço de '{price_text}': {e}")
        return None


def format_price(price: float, currency: str = "R$") -> str:
    """
    Formata um valor numérico como preço.
    
    Args:
        price: Valor numérico a ser formatado
        currency: Símbolo da moeda (padrão: "R$")
        
    Returns:
        str: Preço formatado (ex: "R$ 1.299,99")
    """
    return f"{currency} {price:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")


def calculate_discount(original_price: float, current_price: float) -> Optional[int]:
    """
    Calcula o percentual de desconto entre dois preços.
    
    Args:
        original_price: Preço original
        current_price: Preço atual
        
    Returns:
        int: Percentual de desconto arredondado ou None se não for possível calcular
    """
    try:
        if original_price > current_price > 0:
            discount = ((original_price - current_price) / original_price) * 100
            return int(round(discount))
    except (TypeError, ValueError):
        pass
    return None

# ====================================
# Extractors para cada loja
# ====================================

def extract_magalu_product(soup: BeautifulSoup, url: str) -> Optional[ProductInfo]:
    """
    Extrai informações de um produto do Magazine Luiza.
    
    Args:
        soup: Objeto BeautifulSoup da página do produto
        url: URL da página do produto
        
    Returns:
        ProductInfo com as informações do produto ou None em caso de erro
    """
    try:
        # Inicializa o objeto de resultado
        result = ProductInfo(
            title="",
            price="",
            store="Magazine Luiza",
            url=url.split('?')[0].split('#')[0]  # Limpa a URL
        )
        
        # Extrai o título
        title_tag = (
            soup.find('h1', {'class': 'header-product__title'}) or
            soup.find('h1', {'class': 'header-product__title--desktop'}) or
            soup.find('h1')
        )
        if title_tag:
            result.title = title_tag.get_text(strip=True)
        
        # Extrai o preço atual
        price_tag = (
            soup.find('h2', {'class': 'price-template__text'}) or
            soup.find('span', {'class': 'price-template__text'}) or
            soup.find('span', {'class': lambda c: c and 'price' in c.lower()})
        )
        if price_tag:
            result.price = price_tag.get_text(strip=True)
        
        # Extrai o preço original (se disponível)
        original_price_tag = (
            soup.find('s', {'class': 'price-template__text--old'}) or
            soup.find('span', {'class': 'price-template__text--old'}) or
            soup.find('span', {'class': lambda c: c and 'old' in c.lower()})
        )
        if original_price_tag:
            result.original_price = original_price_tag.get_text(strip=True)
        
        # Extrai a URL da imagem
        image_tag = (
            soup.find('img', {'class': 'showcase-product__big-img'}) or
            soup.find('img', {'id': 'image'}) or
            soup.find('img', {'class': lambda c: c and 'image' in c.lower()}) or
            soup.find('img', {'data-testid': 'image-selected-thumbnail'})
        )
        
        if image_tag:
            image_url = image_tag.get('src') or image_tag.get('data-src')
            if image_url:
                if not image_url.startswith(('http://', 'https://')):
                    if image_url.startswith('//'):
                        image_url = f'https:{image_url}'
                    else:
                        image_url = f'https://www.magazineluiza.com.br{image_url if not image_url.startswith("/") else image_url}'
                result.image_url = image_url
        
        # Verifica se o produto está disponível
        unavailable_tag = soup.find('div', {'class': 'unavailable-product'})
        if unavailable_tag:
            result.available = False
        
        return result if result.title and result.price else None
        
    except Exception as e:
        logger.error(f"Erro ao extrair produto do Magazine Luiza: {e}")
        return None

def extract_amazon_product(soup: BeautifulSoup, url: str) -> Optional[ProductInfo]:
    """
    Extrai informações de um produto da Amazon.
    
    Args:
        soup: Objeto BeautifulSoup da página do produto
        url: URL da página do produto
        
    Returns:
        ProductInfo com as informações do produto ou None em caso de erro
    """
    try:
        result = ProductInfo(
            title="",
            price="",
            store="Amazon",
            url=url.split('?')[0].split('#')[0]  # Limpa a URL
        )
        
        # Extrai o título
        title_tag = soup.find('span', {'id': 'productTitle'})
        if title_tag:
            result.title = title_tag.get_text(strip=True)
        
        # Tenta extrair do JSON-LD primeiro (mais confiável)
        json_ld = soup.find('script', {'type': 'application/ld+json'})
        if json_ld:
            try:
                data = json.loads(json_ld.string)
                if isinstance(data, dict):
                    # Tenta extrair oferta
                    if 'offers' in data and isinstance(data['offers'], dict):
                        offer = data['offers']
                        if 'price' in offer:
                            result.price = f"R$ {float(offer['price']):.2f}".replace('.', ',')
                        if 'highPrice' in offer and 'lowPrice' in offer and offer['highPrice'] != offer['lowPrice']:
                            result.price = f"R$ {float(offer['lowPrice']):.2f} - R$ {float(offer['highPrice']):.2f}".replace('.', ',')
                    
                    # Extrai preço original se disponível
                    if 'listPrice' in data:
                        result.original_price = f"R$ {float(data['listPrice']):.2f}".replace('.', ',')
                    
                    # Extrai imagem
                    if 'image' in data and not result.image_url:
                        result.image_url = data['image']
            except (json.JSONDecodeError, AttributeError, KeyError, ValueError) as e:
                logger.debug(f"Erro ao extrair dados do JSON-LD: {e}")
        
        # Se não encontrou preço no JSON-LD, tenta extrair do HTML
        if not result.price:
            price_whole = soup.find('span', {'class': 'a-price-whole'})
            price_fraction = soup.find('span', {'class': 'a-price-fraction'})
            if price_whole and price_fraction:
                result.price = f"R$ {price_whole.get_text(strip=True)},{price_fraction.get_text(strip=True)}"
            
            # Extrai o preço original (se disponível)
            original_price = soup.find('span', {'class': 'a-price a-text-price'})
            if original_price:
                price_text = original_price.get_text(strip=True)
                result.original_price = price_text.replace('R$', '').strip()
        
        # Extrai a URL da imagem
        if not result.image_url:
            image_tag = (
                soup.find('img', {'id': 'landingImage'}) or 
                soup.find('img', {'id': 'imgBlkFront'}) or
                soup.find('img', {'class': 'a-dynamic-image'})
            )
            if image_tag:
                result.image_url = image_tag.get('data-old-hires') or image_tag.get('src')
        
        # Verifica disponibilidade
        unavailable_tag = (
            soup.find('div', {'id': 'outOfStock'}) or
            soup.find('span', string=re.compile(r'esgotado|indisponível|sem estoque', re.IGNORECASE)) or
            soup.find('span', {'class': 'a-color-price'}, string=re.compile(r'disponível em', re.IGNORECASE))
        )
        
        if unavailable_tag or not result.price:
            result.available = False
        
        return result if result.title and (result.price or not result.available) else None
        
    except Exception as e:
        logger.error(f"Erro ao extrair produto da Amazon: {e}")
        return None

def extract_mercado_livre_product(soup: BeautifulSoup, url: str) -> Optional[ProductInfo]:
    """
    Extrai informações de um produto do Mercado Livre.
    
    Args:
        soup: Objeto BeautifulSoup da página do produto
        url: URL da página do produto
        
    Returns:
        ProductInfo com as informações do produto ou None em caso de erro
    """
    try:
        result = ProductInfo(
            title="",
            price="",
            store="Mercado Livre",
            url=url.split('?')[0].split('#')[0]  # Limpa a URL
        )
        
        # Tenta extrair do JSON-LD primeiro (mais confiável)
        json_ld = soup.find('script', {'type': 'application/ld+json'})
        if json_ld:
            try:
                data = json.loads(json_ld.string)
                if isinstance(data, dict):
                    # Extrai título
                    if 'name' in data:
                        result.title = data['name']
                    
                    # Extrai preço
                    if 'offers' in data and 'price' in data['offers']:
                        price = float(data['offers']['price'])
                        result.price = f"R$ {price:,.2f}".replace('.', ',')
                    
                    # Extrai preço original
                    if 'listPrice' in data['offers']:
                        original_price = float(data['offers']['listPrice'])
                        result.original_price = f"R$ {original_price:,.2f}".replace('.', ',')
                    
                    # Extrai imagem
                    if 'image' in data and not result.image_url:
                        result.image_url = data['image']
                        
            except (json.JSONDecodeError, AttributeError, KeyError, ValueError) as e:
                logger.debug(f"Erro ao extrair dados do JSON-LD do Mercado Livre: {e}")
        
        # Se não encontrou no JSON-LD, tenta extrair do HTML
        if not result.title:
            title_tag = soup.find('h1', {'class': 'ui-pdp-title'})
            if title_tag:
                result.title = title_tag.get_text(strip=True)
        
        if not result.price:
            price_tag = soup.find('span', {'class': 'andes-money-amount__fraction'})
            if price_tag:
                price = price_tag.get_text(strip=True).replace('\xa0', '')
                cents_tag = soup.find('span', {'class': 'andes-money-amount__cents'})
                if cents_tag:
                    price += f",{cents_tag.get_text(strip=True)}"
                result.price = f"R$ {price}"
        
        if not result.original_price:
            original_price_tag = (
                soup.find('s', {'class': 'andes-money-amount'}) or
                soup.find('span', {'class': 'andes-money-amount--previous'}) or
                soup.find('span', {'class': 'price-tag-text'})
            )
            if original_price_tag:
                price_text = original_price_tag.get_text(strip=True)
                result.original_price = re.sub(r'\s+', ' ', price_text).replace('R$', '').strip()
        
        # Extrai a URL da imagem
        if not result.image_url:
            image_tag = (
                soup.find('img', {'class': 'ui-pdp-image'}) or
                soup.find('img', {'class': 'ui-pdp-image__image'}) or
                soup.find('img', {'class': 'ui-pdp-gallery__figure__image'}) or
                soup.find('img', {'class': 'ui-pdp-gallery__figure__image--with-placeholder'})
            )
            if image_tag:
                result.image_url = image_tag.get('data-src') or image_tag.get('src')
        
        # Verifica disponibilidade
        unavailable_tag = (
            soup.find('p', string=re.compile(r'esgotado|indisponível', re.IGNORECASE)) or
            soup.find('div', {'class': 'ui-pdp-stock-information__title'}, 
                     string=re.compile(r'esgotado|indisponível', re.IGNORECASE)) or
            soup.find('div', {'class': 'ui-pdp-buybox__quantity'}, 
                     string=re.compile(r'sem estoque', re.IGNORECASE))
        )
        
        if unavailable_tag or not result.price:
            result.available = False
        
        return result if result.title and (result.price or not result.available) else None
        
        return result if result.title and (result.price or not result.available) else None
        
    except Exception as e:
        logger.error(f"Erro ao extrair produto do Aliexpress: {e}")
        return None


def extract_shopee_product(soup: BeautifulSoup, url: str) -> Optional[ProductInfo]:
    """
    Extrai informações de um produto da Shopee.
    
    Args:
        soup: Objeto BeautifulSoup da página do produto
        url: URL da página do produto
        
    Returns:
        ProductInfo com as informações do produto ou None em caso de erro
    """
    try:
        result = ProductInfo(
            title="",
            price="",
            store="Shopee",
            url=url.split('?')[0].split('#')[0]
        )
        
        # A Shopee usa muito JavaScript, então tentamos extrair dos dados embutidos
        script_data = soup.find('script', string=re.compile(r'"price":'))
        
        if script_data:
            script_text = script_data.string
            
            # Extrai o título
            title_match = re.search(r'"name":"([^"]+)"', script_text)
            if title_match:
                result.title = title_match.group(1).strip()
            
            # Extrai o preço
            price_match = re.search(r'"price":(\d+)', script_text)
            if price_match:
                price = int(price_match.group(1)) / 100000  # Preço vem em centavos * 1000
                result.price = f"R$ {price:,.2f}".replace('.', ',')
            
            # Extrai o preço original
            original_price_match = re.search(r'"price_before_discount":(\d+)', script_text)
            if original_price_match:
                original_price = int(original_price_match.group(1)) / 100000
                result.original_price = f"R$ {original_price:,.2f}".replace('.', ',')
            
            # Extrai a URL da imagem
            image_match = re.search(r'"image":"([^"]+)"', script_text)
            if image_match:
                image_url = image_match.group(1)
                if not image_url.startswith(('http://', 'https://')):
                    image_url = f'https://cf.shopee.com.br/file/{image_url}'
                result.image_url = image_url
        
        # Se não encontrou no script, tenta extrair do HTML
        if not result.title:
            title_tag = (
                soup.find('div', {'class': 'attM6y'}) or 
                soup.find('h1') or
                soup.find('div', {'class': 'product-title'})
            )
            if title_tag:
                result.title = title_tag.get_text(strip=True)
        
        if not result.price:
            price_tag = (
                soup.find('div', {'class': 'pqTWkA'}) or
                soup.find('div', {'class': 'product-price'}) or
                soup.find('div', {'class': 'product-price-current'})
            )
            if price_tag:
                result.price = price_tag.get_text(strip=True)
        
        if not result.original_price:
            original_price_tag = (
                soup.find('div', {'class': 'WObNFg'}) or
                soup.find('div', {'class': 'product-original-price'}) or
                soup.find('del')
            )
            if original_price_tag:
                result.original_price = original_price_tag.get_text(strip=True)
        
        # Extrai a URL da imagem
        if not result.image_url:
            image_tag = (
                soup.find('img', {'class': 'product-carousel__image'}) or
                soup.find('img', {'class': 'product-image'}) or
                soup.find('img', {'class': 'gallery-preview-panel__image'})
            )
            if image_tag:
                result.image_url = image_tag.get('src') or image_tag.get('data-src')
                if result.image_url and result.image_url.startswith('//'):
                    result.image_url = f'https:{result.image_url}'
        
        # Verifica disponibilidade
        unavailable_tag = (
            soup.find('div', string=re.compile(r'esgotado|indisponível|fora de estoque', re.IGNORECASE)) or
            soup.find('div', {'class': 'product-not-available'}) or
            soup.find('button', string=re.compile(r'esgotado|indisponível', re.IGNORECASE))
        )
        
        if unavailable_tag or not result.price:
            result.available = False
        
        return result if result.title and (result.price or not result.available) else None
        
    except Exception as e:
        logger.error(f"Erro ao extrair produto da Shopee: {e}")
        return None


def extract_aliexpress_product(soup: BeautifulSoup, url: str) -> Optional[ProductInfo]:
    """
    Extrai informações de um produto do Aliexpress.
    
    Args:
        soup: Objeto BeautifulSoup da página do produto
        url: URL da página do produto
        
    Returns:
        ProductInfo com as informações do produto ou None em caso de erro
    """
    try:
        # Inicializa o objeto de resultado
        result = ProductInfo(
            title="",
            price="",
            store="Aliexpress",
            url=url.split('?')[0].split('#')[0],
            currency="R$"  # O Aliexpress mostra preços em reais para o Brasil
        )
        
        # 1. Extrai o título da tag de título ou do meta og:title
        if not result.title:
            # Tenta do meta og:title primeiro
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                result.title = og_title['content'].strip()
            else:
                # Tenta do título da página
                title_tag = soup.find('title')
                if title_tag:
                    result.title = title_tag.get_text(strip=True)
                    # Remove partes desnecessárias do título
                    if ' - AliExpress' in result.title:
                        result.title = result.title.split(' - AliExpress')[0].strip()
        
        # 2. Extrai o preço atual
        if not result.price:
            # Tenta encontrar o preço em diferentes formatos
            price_selectors = [
                'div[class*="snow-price_SnowPrice"]',
                'div[class*="product-price-current"]',
                'div[class*="uniform-banner-box-price"]',
                'div[class*="product-price"]',
                'span[class*="product-price-value"]',
                'span[itemprop="price"]',
                'div[itemprop="price"]',
                'meta[itemprop="price"]',
                'div[class*="price"]',
            ]
            
            for selector in price_selectors:
                price_element = soup.select_one(selector)
                if price_element:
                    price_text = price_element.get_text(strip=True) if hasattr(price_element, 'get_text') else price_element.get('content', '')
                    if price_text and any(c.isdigit() for c in price_text):
                        # Limpa o texto do preço
                        price_text = ' '.join(price_text.split())  # Remove espaços extras
                        # Se não tiver o símbolo de moeda, adiciona
                        if 'R$' not in price_text and 'US$' not in price_text and '$' not in price_text:
                            price_text = f'R$ {price_text}'
                        result.price = price_text
                        break
        
        # 3. Extrai o preço original (se houver desconto)
        if not result.original_price:
            # Tenta encontrar o preço original riscado
            original_price_selectors = [
                'div[class*="snow-price_SnowPrice__original"]',
                'div[class*="product-price-original"]',
                'span[class*="original-price"]',
                'span[class*="price-original"]',
                'del',
                's',
                'strike'
            ]
            
            for selector in original_price_selectors:
                original_price_element = soup.select_one(selector)
                if original_price_element:
                    original_price_text = original_price_element.get_text(strip=True)
                    if original_price_text and any(c.isdigit() for c in original_price_text):
                        # Limpa o texto do preço original
                        original_price_text = ' '.join(original_price_text.split())  # Remove espaços extras
                        # Se não tiver o símbolo de moeda, adiciona
                        if 'R$' not in original_price_text and 'US$' not in original_price_text and '$' not in original_price_text:
                            original_price_text = f'R$ {original_price_text}'
                        result.original_price = original_price_text
                        break
        
        # 4. Extrai a URL da imagem
        if not result.image_url:
            # Tenta das meta tags primeiro
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                result.image_url = og_image['content'].strip()
            else:
                # Tenta encontrar a imagem principal
                image_selectors = [
                    'img[class*="gallery-preview-panel__image"]',
                    'img[class*="detail-gallery-preview__image"]',
                    'img[itemprop="image"]',
                    'img[class*="product-image"]',
                    'img[class*="main-img"]',
                    'img[class*="gallery-image"]',
                    'img[data-sku-id]',
                    'img[src*="alicdn.com"]',
                    'img[src*="ae01.alicdn.com"]',
                    'img[src*="ae02.alicdn.com"]',
                    'img[src*="ae03.alicdn.com"]',
                    'img[src*="ae04.alicdn.com"]',
                    'img[src*="ae05.alicdn.com"]',
                ]
                
                for selector in image_selectors:
                    img = soup.select_one(selector)
                    if img:
                        img_url = img.get('src') or img.get('data-src')
                        if img_url:
                            # Garante que a URL comece com http
                            if img_url.startswith('//'):
                                img_url = f'https:{img_url}'
                            elif img_url.startswith('/'):
                                img_url = f'https://www.aliexpress.com{img_url}'
                            
                            # Verifica se é uma URL de imagem válida
                            if any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                                result.image_url = img_url
                                break
        
        # 5. Verifica disponibilidade
        if not result.available:
            # Verifica se há mensagens de indisponibilidade
            unavailable_texts = [
                'esgotado', 'indisponível', 'fora de estoque', 'sold out', 'out of stock',
                'esgotada', 'esgotados', 'esgotadas', 'esgotou', 'fora de linha'
            ]
            
            # Verifica em elementos comuns que podem conter mensagens de indisponibilidade
            page_text = soup.get_text().lower()
            if any(text in page_text for text in unavailable_texts):
                result.available = False
            else:
                # Se não encontrou mensagens de indisponibilidade, assume que está disponível
                result.available = bool(result.price)  # Disponível se tiver preço
        
        # 6. Calcula o desconto se houver preço original e preço atual
        if result.price and result.original_price:
            try:
                # Extrai valores numéricos dos preços
                current_price = extract_price(result.price)
                original_price = extract_price(result.original_price)
                
                if current_price and original_price and original_price > current_price:
                    result.discount = calculate_discount(original_price, current_price)
            except Exception as e:
                logger.debug(f"Erro ao calcular desconto: {e}")
        
        # Retorna o resultado se tiver título e preço (ou estiver indisponível)
        return result if (result.title and (result.price or not result.available)) else None
        
    except Exception as e:
        logger.error(f"Erro ao extrair produto do Aliexpress: {e}", exc_info=True)
        return None

# Mapeamento de domínios para funções de extração
STORE_EXTRACTORS = {
    'magazineluiza.com.br': extract_magalu_product,
    'amazon.com.br': extract_amazon_product,
    'mercadolivre.com.br': extract_mercado_livre_product,
    'mercadolivre.com': extract_mercado_livre_product,
    'alibaba.com': extract_aliexpress_product,
    'aliexpress.com': extract_aliexpress_product,
    'pt.aliexpress.com': extract_aliexpress_product,
    'shopee.com.br': extract_shopee_product,
    'shp.ee': extract_shopee_product,
    'mlb.com': extract_mercado_livre_product,
}

def extract_product_info(url: str) -> Optional[ProductInfo]:
    """
    Extrai informações de um produto a partir de sua URL.
    
    Args:
        url: URL do produto
        
    Returns:
        ProductInfo com as informações do produto ou None em caso de erro
    """
    try:
        # Valida a URL
        if not url or not isinstance(url, str):
            logger.error("URL inválida")
            return None
            
        # Obtém o domínio para determinar qual extrator usar
        domain = None
        try:
            parsed_url = urlparse(url)
            domain_parts = parsed_url.netloc.split('.')
            # Pega o domínio principal (últimas duas partes)
            if len(domain_parts) >= 2:
                domain = '.'.join(domain_parts[-2:])
        except Exception as e:
            logger.error(f"Erro ao analisar URL {url}: {e}")
            return None
        
        if not domain:
            logger.error(f"Não foi possível extrair domínio da URL: {url}")
            return None
        
        # Encontra o extrator apropriado
        extractor = None
        for store_domain, func in STORE_EXTRACTORS.items():
            if store_domain in parsed_url.netloc:
                extractor = func
                break
        
        if not extractor:
            logger.error(f"Nenhum extrator disponível para o domínio: {domain}")
            return None
        
        logger.info(f"Extraindo informações do produto de: {url} (usando extrator para {extractor.__name__})")
        
        # Faz a requisição HTTP
        response = make_request(url)
        if not response or not response.content:
            logger.error(f"Falha ao carregar a página: {url}")
            return None
        
        # Faz o parse do HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        if not soup:
            logger.error(f"Falha ao fazer parse do HTML: {url}")
            return None
        
        # Extrai as informações do produto
        product_info = extractor(soup, url)
        
        # Se não conseguiu extrair informações suficientes, tenta métodos alternativos
        if not product_info or not product_info.title or (not product_info.price and product_info.available):
            logger.warning(f"Falha ao extrair informações completas com o extrator principal, tentando métodos alternativos para: {url}")
            
            # Tenta extrair informações genéricas
            if not product_info:
                product_info = extract_generic_product(soup, url, domain)
            else:
                # Preenche campos ausentes com informações genéricas
                generic_info = extract_generic_product(soup, url, domain)
                if generic_info:
                    if not product_info.title and generic_info.title:
                        product_info.title = generic_info.title
                    if not product_info.price and generic_info.price:
                        product_info.price = generic_info.price
                    if not product_info.original_price and generic_info.original_price:
                        product_info.original_price = generic_info.original_price
                    if not product_info.image_url and generic_info.image_url:
                        product_info.image_url = generic_info.image_url
        
        # Calcula o desconto se possível
        if product_info and product_info.price and product_info.original_price:
            current_price = extract_price(product_info.price)
            original_price = extract_price(product_info.original_price)
            if current_price and original_price and original_price > current_price:
                product_info.discount = calculate_discount(original_price, current_price)
        
        return product_info if (product_info and product_info.title and (product_info.price or not product_info.available)) else None
        
    except Exception as e:
        logger.error(f"Erro ao extrair informações do produto {url}: {e}", exc_info=True)
        return None


def extract_generic_product(soup: BeautifulSoup, url: str, domain: str) -> Optional[ProductInfo]:
    """
    Tenta extrair informações de um produto de forma genérica quando o extrator específico falhar.
    
    Args:
        soup: Objeto BeautifulSoup da página do produto
        url: URL da página do produto
        domain: Domínio do site
        
    Returns:
        ProductInfo com as informações do produto ou None em caso de erro
    """
    try:
        result = ProductInfo(
            title="",
            price="",
            store=domain,
            url=url.split('?')[0].split('#')[0]
        )
        
        # Tenta extrair o título de tags comuns
        title_tags = [
            soup.find('h1'),
            soup.find('h2'),
            soup.find('meta', {'property': 'og:title'}),
            soup.find('meta', {'name': 'title'}),
            soup.find('title')
        ]
        
        for tag in title_tags:
            if tag and hasattr(tag, 'get_text'):
                result.title = tag.get_text(strip=True)
                if result.title:
                    break
            elif tag and 'content' in tag.attrs:
                result.title = tag['content'].strip()
                if result.title:
                    break
        
        # Tenta extrair o preço de tags comuns
        price_patterns = [
            r'R\$\s*[\d.,]+',  # R$ 1.234,56
            r'\$\s*[\d.,]+',    # $ 1,234.56
            r'[\d.,]+\s*R\$',  # 1.234,56 R$
            r'[\d.,]+\s*\$'     # 1,234.56 $
        ]
        
        # Procura por padrões de preço no HTML
        html_text = str(soup).lower()
        for pattern in price_patterns:
            match = re.search(pattern, html_text, re.IGNORECASE)
            if match:
                result.price = match.group(0).strip()
                break
        
        # Tenta extrair a URL da imagem
        image_tags = [
            soup.find('img', {'class': re.compile(r'product|image|img', re.IGNORECASE)}),
            soup.find('img', {'id': re.compile(r'product|image|img', re.IGNORECASE)}),
            soup.find('meta', {'property': 'og:image'}),
            soup.find('link', {'rel': 'image_src'}),
            soup.find('img')
        ]
        
        for tag in image_tags:
            if not tag:
                continue
                
            if tag.name == 'meta' and 'content' in tag.attrs:
                result.image_url = tag['content'].strip()
                break
            elif tag.name == 'link' and 'href' in tag.attrs:
                result.image_url = tag['href'].strip()
                break
            elif tag.name == 'img' and ('src' in tag.attrs or 'data-src' in tag.attrs):
                result.image_url = tag.get('data-src') or tag.get('src')
                if result.image_url:
                    break
        
        # Converte URLs relativas em absolutas
        if result.image_url and not result.image_url.startswith(('http://', 'https://')):
            if result.image_url.startswith('//'):
                result.image_url = f'https:{result.image_url}'
            else:
                result.image_url = f'https://{domain}{result.image_url if not result.image_url.startswith("/") else result.image_url}'
        
        # Verifica disponibilidade
        unavailable_texts = [
            'esgotado', 'indisponível', 'fora de estoque', 'sold out', 'out of stock', 'esgotada', 'esgotadas'
        ]
        
        html_text_lower = html_text.lower()
        if any(text in html_text_lower for text in unavailable_texts):
            result.available = False
        
        return result if result.title or result.price or result.image_url else None
        
    except Exception as e:
        logger.debug(f"Erro ao extrair informações genéricas do produto: {e}")
        return None


def get_product_info(url: str) -> Optional[Dict[str, Any]]:
    """
    Função de conveniência para compatibilidade com código existente.
    Retorna um dicionário em vez de um objeto ProductInfo.
    
    Args:
        url: URL do produto
        
    Returns:
        Dicionário com as informações do produto ou None em caso de erro
    """
    product = extract_product_info(url)
    if not product:
        return None
    
    return {
        'titulo': product.title,
        'preco': product.price,
        'preco_original': product.original_price,
        'imagem_url': product.image_url,
        'loja': product.store,
        'url_produto': product.url,
        'disponivel': product.available,
        'desconto': product.discount
    }
    
    try:
        # Faz a requisição HTTP
        response = make_request(url)
        if not response or not response.content:
            logger.error("Falha ao carregar a página do produto")
            return None
        
        # Extrai o domínio para determinar qual função de extração usar
        domain = urlparse(url).netloc.lower()
        domain = domain.replace('www.', '')
        
        # Encontra a função de extração apropriada
        extractor = None
        for store_domain, func in STORE_EXTRACTORS.items():
            if store_domain in domain:
                extractor = func
                break
        
        if not extractor:
            logger.warning(f"Nenhum extrator disponível para o domínio: {domain}")
            return None
        
        # Faz o parsing do HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extrai as informações do produto
        product_info = extractor(soup, url)
        
        # Valida se as informações mínimas foram extraídas
        if not product_info.get('titulo') or not product_info.get('preco'):
            logger.warning("Informações essenciais não encontradas na página")
            return None
        
        return product_info
        
    except Exception as e:
        logger.error(f"Erro ao extrair informações do produto: {e}", exc_info=True)
        return None
