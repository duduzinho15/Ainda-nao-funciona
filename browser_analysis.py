"""
Script para analisar o site Promobit usando um navegador controlado.
"""
import asyncio
import logging
import json
from datetime import datetime
from urllib.parse import urljoin, urlparse

from pyppeteer import launch
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('browser_analysis.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger('browser_analysis')

# URLs para análise
BASE_URL = 'https://www.promobit.com.br/'
CATEGORY_URLS = [
    urljoin(BASE_URL, 'ofertas/informatica/'),
    urljoin(BASE_URL, 'ofertas/celulares/'),
    urljoin(BASE_URL, 'ofertas/games/')
]

async def analyze_page(page, url):
    """Analisa uma página específica e extrai informações úteis."""
    logger.info(f"Analisando a página: {url}")
    
    # Navega até a página
    await page.goto(url, {'waitUntil': 'networkidle2', 'timeout': 60000})
    
    # Espera um pouco para garantir que o conteúdo seja carregado
    await asyncio.sleep(5)
    
    # Obtém o conteúdo HTML da página
    html = await page.content()
    
    # Salva o HTML para análise
    domain = urlparse(url).netloc.replace('www.', '').split('.')[0]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_filename = f'promobit_{domain}_{timestamp}.html'
    
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    logger.info(f"Página salva como: {html_filename}")
    
    # Analisa o HTML com BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extrai informações básicas
    page_info = {
        'url': url,
        'title': await page.title(),
        'timestamp': datetime.now().isoformat(),
        'elements': {}
    }
    
    # Conta elementos por tag
    for tag in ['div', 'a', 'article', 'section', 'span', 'h1', 'h2', 'h3', 'img']:
        elements = soup.find_all(tag)
        if elements:
            page_info['elements'][tag] = len(elements)
    
    # Encontra ofertas com diferentes seletores
    offer_selectors = [
        'div.thread--deal',
        'div.thread',
        'article',
        'div[class*="card"]',
        'div[class*="deal"]',
        'div[class*="offer"]',
        'div[class*="product"]',
        'div[class*="item"]',
    ]
    
    page_info['offer_elements'] = {}
    
    for selector in offer_selectors:
        elements = soup.select(selector)
        if elements:
            page_info['offer_elements'][selector] = len(elements)
            
            # Analisa o primeiro elemento encontrado
            elem = elements[0]
            elem_info = {
                'tag': elem.name,
                'classes': elem.get('class', []),
                'id': elem.get('id'),
                'text_preview': elem.get_text(strip=True)[:200] + '...',
                'html_preview': str(elem)[:300] + '...'
            }
            
            # Encontra elementos filhos comuns
            for child_selector in ['h3', 'h2', 'a', 'img', 'span', 'div.price', 'div.thread-price']:
                child_elements = elem.select(child_selector)
                if child_elements:
                    elem_info[f'has_{child_selector}'] = len(child_elements)
            
            page_info['offer_elements'][f'{selector}_example'] = elem_info
            break  # Para após encontrar o primeiro seletor com resultados
    
    # Captura o console do navegador
    console_logs = await page.evaluate('''() => {
        const logs = [];
        const originalConsoleLog = console.log;
        console.log = function() {
            logs.push(Array.from(arguments).join(' '));
            originalConsoleLog.apply(console, arguments);
        };
        return logs;
    }''')
    
    if console_logs:
        page_info['console_logs'] = console_logs
    
    # Captura as requisições de rede
    network_requests = await page.evaluate('''() => {
        return window.performance.getEntriesByType('resource').map(r => ({
            name: r.name,
            entryType: r.entryType,
            startTime: r.startTime,
            duration: r.duration,
            initiatorType: r.initiatorType,
            nextHopProtocol: r.nextHopProtocol,
            workerStart: r.workerStart,
            redirectStart: r.redirectStart,
            redirectEnd: r.redirectEnd,
            fetchStart: r.fetchStart,
            domainLookupStart: r.domainLookupStart,
            domainLookupEnd: r.domainLookupEnd,
            connectStart: r.connectStart,
            connectEnd: r.connectEnd,
            secureConnectionStart: r.secureConnectionStart,
            requestStart: r.requestStart,
            responseStart: r.responseStart,
            responseEnd: r.responseEnd,
            transferSize: r.transferSize,
            encodedBodySize: r.encodedBodySize,
            decodedBodySize: r.decodedBodySize,
            serverTiming: r.serverTiming,
            workerTiming: r.workerTiming
        }));
    }''')
    
    if network_requests:
        page_info['network_requests'] = network_requests
        
        # Filtra requisições que podem conter dados de ofertas
        api_requests = [
            req for req in network_requests 
            if 'api.' in req['name'].lower() or 
               'ofertas' in req['name'].lower() or
               'products' in req['name'].lower() or
               'deals' in req['name'].lower()
        ]
        
        if api_requests:
            page_info['api_requests'] = api_requests
            logger.info(f"Encontradas {len(api_requests)} requisições de API relevantes")
    
    # Tenta encontrar elementos de paginação
    pagination = await page.evaluate('''() => {
        const pagination = [];
        document.querySelectorAll('a[href*="page"], a[href*="pagina"], a[href*="p="], a[href*="p/"], .pagination a, .pager a')
            .forEach(el => {
                if (el.href && el.textContent.trim() && !isNaN(parseInt(el.textContent.trim()))) {
                    pagination.push({
                        text: el.textContent.trim(),
                        href: el.href,
                        class: el.className,
                        id: el.id
                    });
                }
            });
        return pagination;
    }''')
    
    if pagination:
        page_info['pagination'] = pagination
        logger.info(f"Elementos de paginação encontrados: {len(pagination)}")
    
    # Salva as informações em um arquivo JSON
    json_filename = f'promobit_analysis_{domain}_{timestamp}.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(page_info, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info(f"Análise salva em: {json_filename}")
    return page_info

async def main():
    """Função principal."""
    logger.info("Iniciando análise do site Promobit com navegador controlado...")
    
    # Inicia o navegador
    browser = await launch(
        headless=False,  # Define como True para modo headless
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--window-size=1920,1080'
        ]
    )
    
    try:
        # Abre uma nova página
        page = await browser.newPage()
        
        # Configura o user agent
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Define o viewport
        await page.setViewport({'width': 1920, 'height': 1080})
        
        # Habilita o log de requisições
        await page.setRequestInterception(True)
        
        # Captura requisições de rede
        requests = []
        
        async def log_request(request):
            requests.append({
                'url': request.url,
                'method': request.method,
                'headers': request.headers,
                'resourceType': request.resourceType,
                'timestamp': datetime.now().isoformat()
            })
            await request.continue_()
        
        page.on('request', lambda req: asyncio.ensure_future(log_request(req)))
        
        # Captura erros da página
        page.on('pageerror', lambda err: logger.error(f"Erro na página: {err}"))
        page.on('console', lambda msg: logger.info(f"Console: {msg.text}"))
        
        # Analisa cada URL
        results = {}
        
        for url in CATEGORY_URLS:
            try:
                logger.info(f"\n{'='*80}")
                logger.info(f"ANALISANDO: {url}")
                logger.info(f"{'='*80}")
                
                result = await analyze_page(page, url)
                results[url] = result
                
                # Pequena pausa entre as requisições
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Erro ao analisar {url}: {e}", exc_info=True)
                continue
        
        # Salva todas as requisições de rede
        if requests:
            with open('network_requests.json', 'w', encoding='utf-8') as f:
                json.dump(requests, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"Salvas {len(requests)} requisições de rede em network_requests.json")
        
        return results
        
    finally:
        # Fecha o navegador
        await browser.close()
        logger.info("Navegador fechado.")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
