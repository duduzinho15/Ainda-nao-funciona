"""
Debug script for Promobit scraper
"""
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_promobit.log')
    ]
)
logger = logging.getLogger('promobit_debug')

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
]

async def fetch_page(url: str):
    """Fetch a single page and log the response."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            logger.info(f"Fetching URL: {url}")
            async with session.get(url, headers=headers) as response:
                logger.info(f"Status: {response.status}")
                logger.info(f"Content-Type: {response.headers.get('content-type')}")
                
                html = await response.text()
                logger.info(f"HTML length: {len(html)} characters")
                
                # Save HTML for inspection
                with open('promobit_page.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                
                # Try to parse with BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                # Try different selectors to find offers
                selectors = [
                    'article[data-testid="offer-card"]',
                    'div.thread--deal',
                    'div.thread',
                    'div.deal',
                    'div[class*="card"]',
                    'article',
                    'div[class*="offer"]'
                ]
                
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        for i, elem in enumerate(elements[:2], 1):  # Show first 2 matches
                            logger.info(f"\n--- Match {i} with selector '{selector}' ---")
                            logger.info(f"Element: {elem.name} with classes: {elem.get('class', [])}")
                            logger.info(f"Text preview: {elem.get_text(strip=True)[:200]}...")
                            logger.info(f"HTML preview: {str(elem)[:200]}...")
                        break
                else:
                    logger.warning("No offer elements found with any selector")
                    
                    # Dump all divs with classes for debugging
                    divs = soup.find_all('div', class_=True)
                    logger.info(f"Found {len(divs)} divs with classes")
                    for div in divs[:10]:  # Show first 10 divs with classes
                        logger.info(f"Div class: {div.get('class')}")
                
                return html
                
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}", exc_info=True)
            return None

async def main():
    """Main function to test Promobit scraping."""
    # Test different URLs
    urls = [
        'https://www.promobit.com.br/ofertas/informatica/',
        'https://www.promobit.com.br/ofertas/celulares/',
        'https://www.promobit.com.br/ofertas/games/'
    ]
    
    for url in urls:
        logger.info(f"\n{'='*80}")
        logger.info(f"TESTING URL: {url}")
        logger.info(f"{'='*80}")
        
        html = await fetch_page(url)
        
        if html:
            logger.info(f"Successfully fetched {len(html)} bytes from {url}")
        else:
            logger.error(f"Failed to fetch {url}")
        
        # Add a small delay between requests
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
