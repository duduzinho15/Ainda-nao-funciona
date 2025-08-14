"""
Script para testar a extração direta de dados do AliExpress.
"""
import json
import logging
import re
import sys
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('aliexpress_test.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('aliexpress_test')

# Headers para simular um navegador
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

def extract_json_ld(soup):
    """Extrai dados estruturados do JSON-LD."""
    try:
        json_ld = soup.find('script', {'type': 'application/ld+json'})
        if json_ld:
            data = json.loads(json_ld.string)
            logger.info("Dados JSON-LD encontrados:")
            logger.info(json.dumps(data, indent=2, ensure_ascii=False))
            return data
    except Exception as e:
        logger.error(f"Erro ao extrair JSON-LD: {e}")
    return None

def extract_meta_tags(soup):
    """Extrai metadados das tags meta."""
    meta_data = {}
    
    # Tags meta úteis
    meta_tags = [
        'og:title', 'og:description', 'og:image', 'og:url',
        'description', 'keywords', 'twitter:title', 'twitter:description',
        'twitter:image', 'product:price:amount', 'product:price:currency'
    ]
    
    for tag in meta_tags:
        meta = soup.find('meta', property=tag) or soup.find('meta', {'name': tag})
        if meta and meta.get('content'):
            meta_data[tag] = meta['content']
    
    return meta_data

def extract_script_data(soup):
    """Extrai dados de scripts que podem conter informações do produto."""
    script_data = {}
    
    # Procura por scripts que podem conter dados do produto
    scripts = soup.find_all('script', type=None)
    for script in scripts:
        if not script.string:
            continue
            
        # Tenta extrair dados de variáveis JavaScript
        var_matches = re.findall(r'window\.runParams\s*=\s*({.*?});', script.string, re.DOTALL)
        for match in var_matches:
            try:
                data = json.loads(match)
                script_data.update(data)
            except json.JSONDecodeError:
                pass
                
        # Tenta extrair dados de atributos data-
        data_attrs = re.findall(r'data-([a-z-]+)="([^"]+)"', script.string)
        for key, value in data_attrs:
            if any(k in key.lower() for k in ['price', 'title', 'image', 'product']):
                script_data[f'data-{key}'] = value
    
    return script_data

def extract_product_info(soup, url):
    """Extrai informações do produto da página."""
    result = {
        'title': '',
        'price': '',
        'original_price': '',
        'image_url': '',
        'available': True,
        'currency': 'R$',
        'url': url.split('?')[0].split('#')[0]
    }
    
    # 1. Extrai do JSON-LD
    json_ld = extract_json_ld(soup)
    if json_ld:
        if isinstance(json_ld, list):
            json_ld = json_ld[0]
        
        if 'name' in json_ld:
            result['title'] = json_ld['name']
        if 'offers' in json_ld and 'price' in json_ld['offers']:
            result['price'] = f"R$ {float(json_ld['offers']['price']):,.2f}".replace('.', ',')
        if 'image' in json_ld and not result['image_url']:
            result['image_url'] = json_ld['image']
    
    # 2. Extrai das meta tags
    meta_data = extract_meta_tags(soup)
    if 'og:title' in meta_data and not result['title']:
        result['title'] = meta_data['og:title'].split(' - AliExpress')[0].strip()
    if 'og:image' in meta_data and not result['image_url']:
        result['image_url'] = meta_data['og:image']
    
    # 3. Tenta extrair do título da página
    if not result['title']:
        title_tag = soup.find('title')
        if title_tag:
            result['title'] = title_tag.get_text(strip=True).split(' - AliExpress')[0].strip()
    
    # 4. Tenta extrair preço de elementos HTML
    if not result['price']:
        # Procura por elementos que possam conter preço
        price_selectors = [
            'span[class*="price"]',
            'div[class*="price"]',
            'span[itemprop="price"]',
            'div[itemprop="price"]',
            'meta[itemprop="price"]',
            'div[class*="snow-price"]',
            'div[class*="product-price"]',
            'span[class*="product-price"]'
        ]
        
        for selector in price_selectors:
            price_elements = soup.select(selector)
            for element in price_elements:
                price_text = element.get_text(strip=True) or element.get('content', '')
                if price_text and any(c.isdigit() for c in price_text):
                    # Limpa o texto do preço
                    price_text = ' '.join(price_text.split())
                    if 'R$' not in price_text and 'US$' not in price_text and '$' not in price_text:
                        price_text = f'R$ {price_text}'
                    result['price'] = price_text
                    break
            if result['price']:
                break
    
    # 5. Tenta extrair a imagem principal
    if not result['image_url']:
        img_selectors = [
            'img[class*="gallery"]',
            'img[class*="product"]',
            'img[class*="main"]',
            'img[itemprop="image"]',
            'img[src*="alicdn.com"]',
            'img[src*="ae01.alicdn.com"]',
            'img[src*="ae02.alicdn.com"]',
            'img[src*="ae03.alicdn.com"]',
            'img[src*="ae04.alicdn.com"]',
            'img[src*="ae05.alicdn.com"]',
        ]
        
        for selector in img_selectors:
            img = soup.select_one(selector)
            if img:
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    if img_url.startswith('//'):
                        img_url = f'https:{img_url}'
                    elif img_url.startswith('/'):
                        img_url = f'https://www.aliexpress.com{img_url}'
                    
                    if any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                        result['image_url'] = img_url
                        break
    
    # 6. Verifica disponibilidade
    if not result['price']:
        result['available'] = False
    
    return result

def main():
    # URL de teste do AliExpress
    url = "https://pt.aliexpress.com/item/1005009463783046.html"
    
    try:
        # Faz a requisição HTTP
        logger.info(f"Acessando URL: {url}")
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Salva o HTML para análise
        with open('aliexpress_page_direct.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info("Página salva em 'aliexpress_page_direct.html'")
        
        # Faz o parse do HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extrai as informações do produto
        product_info = extract_product_info(soup, url)
        
        # Exibe os resultados
        logger.info("\n=== INFORMAÇÕES EXTRAÍDAS ===")
        logger.info(f"Título: {product_info['title']}")
        logger.info(f"Preço: {product_info['price']}")
        logger.info(f"Preço Original: {product_info['original_price']}")
        logger.info(f"Imagem: {product_info['image_url']}")
        logger.info(f"Disponível: {'Sim' if product_info['available'] else 'Não'}")
        logger.info(f"URL: {product_info['url']}")
        
        # Salva o JSON com os dados extraídos
        with open('aliexpress_product.json', 'w', encoding='utf-8') as f:
            json.dump(product_info, f, ensure_ascii=False, indent=2)
        logger.info("\nDados salvos em 'aliexpress_product.json'")
        
    except Exception as e:
        logger.error(f"Erro ao processar a página: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    main()
