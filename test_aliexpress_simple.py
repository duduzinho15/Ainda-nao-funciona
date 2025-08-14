"""
Script de teste simplificado para extrair informações de produto do AliExpress.
"""
import json
import logging
import re
import sys
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('aliexpress_simple.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('aliexpress_simple')

# Headers para simular um navegador
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

def extract_product_info(html_content, url):
    """Extrai informações do produto do HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Inicializa o dicionário de resultados
    result = {
        'title': '',
        'price': '',
        'original_price': '',
        'image_url': '',
        'available': True,
        'currency': 'R$',
        'url': url.split('?')[0].split('#')[0]
    }
    
    # 1. Extrai o título da meta tag og:title
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        result['title'] = og_title['content'].split(' - AliExpress')[0].strip()
    
    # Se não encontrou no og:title, tenta do título da página
    if not result['title']:
        title_tag = soup.find('title')
        if title_tag:
            result['title'] = title_tag.get_text(strip=True).split(' - AliExpress')[0].strip()
    
    # 2. Extrai a URL da imagem da meta tag og:image
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        result['image_url'] = og_image['content'].strip()
    
    # 3. Tenta extrair preço de scripts JavaScript
    scripts = soup.find_all('script')
    price_patterns = [
        r'"price"\s*:\s*"([\d.,]+)"',
        r'"salePrice"\s*:\s*"([\d.,]+)"',
        r'"priceAmount"\s*:\s*"([\d.,]+)"',
        r'"price"\s*:\s*([\d.]+)',
        r'"salePrice"\s*:\s*([\d.]+)',
    ]
    
    for script in scripts:
        if not script.string:
            continue
            
        script_text = script.string
        
        # Tenta extrair preço atual
        if not result['price']:
            for pattern in price_patterns:
                match = re.search(pattern, script_text)
                if match:
                    price = match.group(1).replace('.', ',')
                    result['price'] = f"R$ {price}"
                    break
        
        # Tenta extrair preço original
        if not result['original_price']:
            original_price_match = re.search(r'"originalPrice"\s*:\s*"([\d.,]+)"', script_text)
            if original_price_match:
                original_price = original_price_match.group(1).replace('.', ',')
                result['original_price'] = f"R$ {original_price}"
    
    # 4. Se não encontrou preço, tenta extrair de elementos HTML
    if not result['price']:
        price_elements = soup.find_all(['span', 'div'], class_=re.compile(r'price|snow-price', re.IGNORECASE))
        for element in price_elements:
            price_text = element.get_text(strip=True)
            if any(c.isdigit() for c in price_text):
                result['price'] = f"R$ {price_text}"
                break
    
    # 5. Se não encontrou a imagem, tenta extrair de elementos de imagem
    if not result['image_url']:
        img_elements = soup.find_all('img', src=re.compile(r'\.(jpg|jpeg|png|webp)', re.IGNORECASE))
        for img in img_elements:
            img_url = img.get('src') or img.get('data-src')
            if img_url:
                if img_url.startswith('//'):
                    img_url = f'https:{img_url}'
                elif img_url.startswith('/'):
                    img_url = urljoin('https://www.aliexpress.com', img_url)
                
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
        with open('aliexpress_page_simple.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info("Página salva em 'aliexpress_page_simple.html'")
        
        # Extrai as informações do produto
        product_info = extract_product_info(response.text, url)
        
        # Exibe os resultados
        logger.info("\n=== INFORMAÇÕES EXTRAÍDAS ===")
        logger.info(f"Título: {product_info['title']}")
        logger.info(f"Preço: {product_info['price']}")
        logger.info(f"Preço Original: {product_info['original_price']}")
        logger.info(f"Imagem: {product_info['image_url']}")
        logger.info(f"Disponível: {'Sim' if product_info['available'] else 'Não'}")
        logger.info(f"URL: {product_info['url']}")
        
        # Salva o JSON com os dados extraídos
        with open('aliexpress_product_simple.json', 'w', encoding='utf-8') as f:
            json.dump(product_info, f, ensure_ascii=False, indent=2)
        logger.info("\nDados salvos em 'aliexpress_product_simple.json'")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao processar a página: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
