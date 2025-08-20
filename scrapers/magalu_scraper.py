"""
Scraper do Magazine Luiza para coleta de ofertas.
Usa HTML scraping para buscar ofertas em promoção.
"""

import os
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup


# Configurações
name = "magalu_scraper"
priority = 40
rate_limit = 1.0  # 1 request por segundo
retry_count = 3
retry_delay = 2.0

# URLs base
BASE_URL = "https://www.magazineluiza.com.br"
DOMAIN = "www.magazineluiza.com.br"

# Headers para evitar bloqueios
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0"
}

# Páginas de ofertas
OFFER_PAGES = [
    "/ofertas",
    "/ofertas/mais-vendidos",
    "/ofertas/lancamentos",
    "/ofertas/black-friday",
    "/ofertas/cyber-monday",
    "/ofertas/promocoes"
]

# Categorias populares
CATEGORIES = [
    "/eletronicos",
    "/informatica",
    "/games",
    "/casa",
    "/moda",
    "/beleza"
]


def enabled() -> bool:
    """Verifica se o scraper está habilitado."""
    # Verificar se scraping é permitido
    if os.getenv("GG_SEED") and os.getenv("GG_FREEZE_TIME"):
        return False  # Modo CI
    
    return os.getenv("GG_ALLOW_SCRAPING") == "1"


async def get_ofertas(periodo: str) -> List[Dict[str, Any]]:
    """
    Coleta ofertas do Magazine Luiza via HTML scraping.
    
    Args:
        periodo: Período para coleta (24h, 7d, 30d, all)
        
    Returns:
        Lista de ofertas encontradas
    """
    logger = logging.getLogger(f"scraper.{name}")
    logger.info(f"🔄 Iniciando coleta de ofertas para período: {periodo}")
    
    if not enabled():
        logger.info("⚠️ Scraper desabilitado (modo CI ou GG_ALLOW_SCRAPING != 1)")
        return []
    
    try:
        all_ofertas = []
        
        # Coletar de páginas de ofertas
        for page in OFFER_PAGES[:3]:  # Limitar a 3 páginas para evitar rate limit
            try:
                logger.info(f"📡 Coletando da página: {page}")
                page_ofertas = await _scrape_offer_page(page)
                
                if page_ofertas:
                    all_ofertas.extend(page_ofertas)
                    logger.info(f"✅ Página {page}: {len(page_ofertas)} ofertas")
                
                # Rate limiting entre páginas
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.warning(f"⚠️ Erro na página {page}: {e}")
                continue
        
        # Coletar de categorias populares
        for category in CATEGORIES[:2]:  # Limitar a 2 categorias
            try:
                logger.info(f"📡 Coletando da categoria: {category}")
                category_ofertas = await _scrape_category_page(category)
                
                if category_ofertas:
                    all_ofertas.extend(category_ofertas)
                    logger.info(f"✅ Categoria {category}: {len(category_ofertas)} ofertas")
                
                # Rate limiting entre categorias
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.warning(f"⚠️ Erro na categoria {category}: {e}")
                continue
        
        # Remover duplicatas
        unique_ofertas = _remove_duplicates(all_ofertas)
        
        logger.info(f"🎯 Coleta concluída: {len(unique_ofertas)} ofertas únicas")
        return unique_ofertas
        
    except Exception as e:
        logger.error(f"❌ Erro geral na coleta: {e}")
        return []


async def _scrape_offer_page(page_path: str) -> List[Dict[str, Any]]:
    """Scrapa uma página de ofertas."""
    logger = logging.getLogger(f"scraper.{name}")
    
    try:
        url = urljoin(BASE_URL, page_path)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=DEFAULT_HEADERS, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    return _parse_offer_page(html, page_path)
                else:
                    logger.warning(f"⚠️ Status {response.status} para {page_path}")
                    return []
                    
    except Exception as e:
        logger.error(f"❌ Erro ao fazer scraping de {page_path}: {e}")
        return []


async def _scrape_category_page(category_path: str) -> List[Dict[str, Any]]:
    """Scrapa uma página de categoria."""
    logger = logging.getLogger(f"scraper.{name}")
    
    try:
        url = urljoin(BASE_URL, category_path)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=DEFAULT_HEADERS, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    return _parse_category_page(html, category_path)
                else:
                    logger.warning(f"⚠️ Status {response.status} para {category_path}")
                    return []
                    
    except Exception as e:
        logger.error(f"❌ Erro ao fazer scraping de {category_path}: {e}")
        return []


def _parse_offer_page(html: str, page_path: str) -> List[Dict[str, Any]]:
    """Parse de página de ofertas."""
    ofertas = []
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Procurar por produtos em oferta (Magalu usa diferentes classes)
        product_cards = soup.find_all('div', class_=re.compile(r'productCard|cardProduct|produto|product-item'))
        
        # Se não encontrar, tentar outras abordagens
        if not product_cards:
            product_cards = soup.find_all('li', class_=re.compile(r'product|item|card'))
        
        for card in product_cards[:20]:  # Limitar a 20 produtos por página
            try:
                oferta = _extract_product_info(card, page_path)
                if oferta:
                    ofertas.append(oferta)
                    
            except Exception as e:
                continue
        
    except Exception as e:
        logging.getLogger(f"scraper.{name}").error(f"❌ Erro ao fazer parse da página {page_path}: {e}")
    
    return ofertas


def _parse_category_page(html: str, category_path: str) -> List[Dict[str, Any]]:
    """Parse de página de categoria."""
    ofertas = []
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Procurar por produtos da categoria
        product_cards = soup.find_all('div', class_=re.compile(r'productCard|cardProduct|produto|product-item'))
        
        # Se não encontrar, tentar outras abordagens
        if not product_cards:
            product_cards = soup.find_all('li', class_=re.compile(r'product|item|card'))
        
        for card in product_cards[:15]:  # Limitar a 15 produtos por categoria
            try:
                oferta = _extract_product_info(card, category_path)
                if oferta:
                    ofertas.append(oferta)
                    
            except Exception as e:
                continue
        
    except Exception as e:
        logging.getLogger(f"scraper.{name}").error(f"❌ Erro ao fazer parse da categoria {category_path}: {e}")
    
    return ofertas


def _extract_product_info(card, page_path: str) -> Optional[Dict[str, Any]]:
    """Extrai informações de um produto do card HTML."""
    try:
        # Título do produto
        title_elem = card.find(['h2', 'h3', 'h4'], class_=re.compile(r'title|nome|name'))
        if not title_elem:
            title_elem = card.find('a', class_=re.compile(r'title|nome|name'))
        
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # Preço
        price_elem = card.find(['span', 'div'], class_=re.compile(r'price|preco|valor'))
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        
        # Extrair preço numérico
        price = _extract_price(price_text)
        
        # URL do produto
        link_elem = card.find('a', href=True)
        product_url = ""
        if link_elem:
            href = link_elem['href']
            if href.startswith('/'):
                product_url = urljoin(BASE_URL, href)
            else:
                product_url = href
        
        # Imagem
        img_elem = card.find('img')
        image_url = img_elem.get('src', '') if img_elem else ""
        if image_url and not image_url.startswith('http'):
            image_url = urljoin(BASE_URL, image_url)
        
        # Verificar se é uma oferta válida
        if not title or not price or not product_url:
            return None
        
        # Criar objeto de oferta
        oferta = {
            "titulo": title,
            "preco": price,
            "loja": "Magazine Luiza",
            "url": product_url,
            "imagem_url": image_url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fonte": name,
            "pagina_origem": page_path
        }
        
        return oferta
        
    except Exception as e:
        return None


def _extract_price(price_text: str) -> float:
    """Extrai preço numérico do texto."""
    try:
        # Remover "R$" e outros caracteres
        price_clean = re.sub(r'[^\d,.]', '', price_text)
        
        # Substituir vírgula por ponto
        price_clean = price_clean.replace(',', '.')
        
        # Converter para float
        return float(price_clean)
        
    except (ValueError, AttributeError):
        return 0.0


def _remove_duplicates(ofertas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove ofertas duplicadas baseado na URL."""
    seen_urls = set()
    unique_ofertas = []
    
    for oferta in ofertas:
        url = oferta.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_ofertas.append(oferta)
    
    return unique_ofertas


# Variáveis de ambiente necessárias
REQUIRED_ENV_VARS = []


# Teste local (se executado diretamente)
if __name__ == "__main__":
    async def test():
        print("🧪 Testando scraper do Magazine Luiza...")
        
        if not enabled():
            print("⚠️ Scraper desabilitado")
            return
        
        ofertas = await get_ofertas("7d")
        print(f"✅ Encontradas {len(ofertas)} ofertas")
        
        if ofertas:
            print("\n📋 Amostras:")
            for i, oferta in enumerate(ofertas[:3]):
                print(f"  {i+1}. {oferta['titulo'][:50]}... - R$ {oferta['preco']:.2f}")
    
    asyncio.run(test())
