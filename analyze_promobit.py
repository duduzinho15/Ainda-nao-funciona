"""
Script para analisar a estrutura do site Promobit e identificar seletores CSS.
"""
import asyncio
import logging
import json
from bs4 import BeautifulSoup
import aiohttp

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,  # Nível mais detalhado
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('analyze_promobit.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('promobit_analyzer')

# Adiciona um manipulador de arquivo separado para saída detalhada
detailed_logger = logging.FileHandler('promobit_detailed.log', mode='w', encoding='utf-8')
detailed_logger.setLevel(logging.DEBUG)
detailed_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
detailed_logger.setFormatter(detailed_formatter)
logger.addHandler(detailed_logger)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
]

async def fetch_page(url: str) -> str:
    """Busca uma página e retorna o HTML."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
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
    
    try:
        async with aiohttp.ClientSession() as session:
            logger.info(f"Buscando URL: {url}")
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                html = await response.text()
                
                # Salva o HTML para análise
                with open('promobit_page.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                
                logger.info(f"Página salva como 'promobit_page.html'")
                return html
                
    except Exception as e:
        logger.error(f"Erro ao buscar a página: {e}")
        return ""

def analyze_html(html: str):
    """Analisa o HTML e extrai informações úteis."""
    if not html:
        return
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Analisa a estrutura da página
    logger.info("\n=== ESTRUTURA DA PÁGINA ===")
    logger.info(f"Título: {soup.title.string if soup.title else 'N/A'}")
    
    # 2. Encontra todos os elementos com ID
    elements_with_id = soup.find_all(id=True)
    logger.info(f"\nElementos com ID ({len(elements_with_id)}):")
    for i, elem in enumerate(elements_with_id[:10], 1):  # Mostra apenas os 10 primeiros
        logger.info(f"  {i}. <{elem.name} id='{elem['id']}'>")
    
    # 3. Encontra todos os elementos com classes
    elements_with_class = soup.find_all(class_=True)
    class_count = {}
    for elem in elements_with_class:
        for cls in elem.get('class', []):
            class_count[cls] = class_count.get(cls, 0) + 1
    
    # Ordena as classes por frequência
    sorted_classes = sorted(class_count.items(), key=lambda x: x[1], reverse=True)
    
    logger.info("\nClasses mais comuns:")
    for cls, count in sorted_classes[:20]:  # Mostra as 20 classes mais comuns
        logger.info(f"  .{cls}: {count} elementos")
    
    # 4. Analisa a estrutura de ofertas
    logger.info("\n=== ANÁLISE DE OFERTAS ===")
    
    # Tenta encontrar ofertas com diferentes seletores
    selectors = [
        'div.thread--deal',
        'div.thread',
        'article',
        'div[class*="card"]',
        'div[class*="deal"]',
        'div[class*="offer"]',
        'div[class*="product"]',
        'div[class*="item"]',
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            logger.info(f"\nEncontrados {len(elements)} elementos com o seletor: {selector}")
            
            # Analisa o primeiro elemento encontrado
            if elements:
                logger.info(f"\nExemplo de elemento com o seletor '{selector}':")
                elem = elements[0]
                logger.info(f"Tag: <{elem.name}>")
                logger.info(f"Classes: {elem.get('class', [])}")
                
                # Tenta extrair informações do produto
                title_elem = elem.select_one('h1, h2, h3, h4, .title, .product-title, .thread-title')
                if title_elem:
                    logger.info(f"Título: {title_elem.get_text(strip=True)[:100]}...")
                
                price_elem = elem.select_one('.price, .thread-price, .product-price, [class*="price"], [class*="Price"]')
                if price_elem:
                    logger.info(f"Preço: {price_elem.get_text(strip=True)}")
                
                # Mostra a estrutura HTML do elemento
                logger.info("\nEstrutura HTML (primeiros 300 caracteres):")
                logger.info(str(elem)[:300] + "...")
                
                # Encontra todas as imagens no elemento
                images = elem.find_all('img')
                if images:
                    logger.info("\nImagens encontradas:")
                    for img in images[:3]:  # Mostra as 3 primeiras imagens
                        src = img.get('src', '') or img.get('data-src', '')
                        logger.info(f"  - {src[:100]}..." if len(src) > 100 else f"  - {src}")
                
                # Encontra todos os links no elemento
                links = elem.find_all('a', href=True)
                if links:
                    logger.info("\nLinks encontrados:")
                    for link in links[:3]:  # Mostra os 3 primeiros links
                        logger.info(f"  - {link.get('href')}")
                
                break  # Para após analisar o primeiro elemento
    
    # 5. Salva todas as tags únicas encontradas
    tags = set(tag.name for tag in soup.find_all(True))
    logger.info("\n=== TAGS HTML ENCONTRADAS ===")
    logger.info(", ".join(sorted(tags)))
    
    # 6. Salva as informações em um arquivo JSON para referência
    analysis = {
        'title': soup.title.string if soup.title else None,
        'common_classes': [{'class': cls, 'count': count} for cls, count in sorted_classes[:50]],
        'elements_with_id': [{'id': elem['id'], 'tag': elem.name} for elem in elements_with_id[:20]],
        'found_selectors': [
            {'selector': selector, 'count': len(soup.select(selector))}
            for selector in selectors if soup.select(selector)
        ],
        'html_structure_sample': str(soup.find('body'))[:1000] + '...' if soup.find('body') else None
    }
    
    with open('promobit_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    logger.info("\nAnálise concluída. Resultados salvos em 'promobit_analysis.json'")

async def main():
    """Função principal."""
    # URL para análise
    urls = [
        'https://www.promobit.com.br/ofertas/informatica/',
        'https://www.promobit.com.br/ofertas/celulares/',
        'https://www.promobit.com.br/ofertas/games/'
    ]
    
    for url in urls:
        logger.info(f"\n{'='*80}")
        logger.info(f"ANALISANDO: {url}")
        logger.info(f"{'='*80}")
        
        html = await fetch_page(url)
        if html:
            analyze_html(html)
        
        # Pequena pausa entre as requisições
        await asyncio.sleep(2)

if __name__ == "__main__":
    logger.info("Iniciando análise do site Promobit...")
    asyncio.run(main())
