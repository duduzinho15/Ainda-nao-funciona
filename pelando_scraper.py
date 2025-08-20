"""
Módulo para busca de ofertas no site Pelando.

Este módulo implementa um scraper para buscar ofertas de produtos de tecnologia
no site Pelando, respeitando as diretrizes do robots.txt.
"""

import asyncio
import logging
import re
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
import aiohttp
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Headers para simular um navegador
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# URL base para busca no Pelando
BASE_URL = "https://www.pelando.com.br/search"

# Lista de palavras-chave para buscar ofertas relevantes
PALAVRAS_CHAVE = [
    "notebook",
    "ssd",
    "memória ram",
    "placa de vídeo",
    "processador",
    "monitor",
    "mouse",
    "teclado",
    "headset",
    "fone de ouvido",
    "webcam",
    "impressora",
    "roteador",
    "cadeira gamer",
    "mesa digitalizadora",
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
    precos = re.findall(r"R\$\s*[\d\.]+,\d{2}", texto)

    if not precos:
        return None, None

    # Remove o símbolo R$ e espaços para padronização
    precos = [p.replace("R$", "").strip() for p in precos]

    # Se tiver apenas um preço, retorna ele como preço atual
    if len(precos) == 1:
        return precos[0], None

    # Se tiver mais de um, assume que o primeiro é o preço original e o segundo o com desconto
    return precos[1], precos[0]


async def buscar_ofertas_pelando(
    session: aiohttp.ClientSession, max_paginas: int = 3, min_desconto: int = 10
) -> List[Dict[str, Any]]:
    """
    Busca ofertas no Pelando extraindo da página principal.

    Args:
        session: Sessão aiohttp para fazer as requisições
        max_paginas: Número máximo de páginas para buscar
        min_desconto: Percentual mínimo de desconto para considerar a oferta

    Returns:
        Lista de dicionários contendo as ofertas encontradas
    """
    ofertas = []

    try:
        # URLs das páginas principais do Pelando
        urls = [
            "https://www.pelando.com.br/",
            "https://www.pelando.com.br/hot",
            "https://www.pelando.com.br/ofertas",
        ]

        for url in urls[:max_paginas]:
            logger.info(f"Buscando ofertas em: {url}")

            try:
                async with session.get(
                    url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Erro ao acessar {url}: HTTP {response.status}")
                        continue

                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Encontra todos os cards de oferta
                    cards = soup.select("article.thread, .thread, .offer-card")

                    if not cards:
                        logger.warning(f"Nenhum card de oferta encontrado em {url}")
                        continue

                    logger.info(f"Encontrados {len(cards)} ofertas em {url}")

                    for card in cards:
                        try:
                            # Extrai título e URL do produto
                            titulo_elem = card.select_one("a.thread-link")
                            if not titulo_elem:
                                continue

                            titulo = titulo_elem.get_text(strip=True)
                            url_oferta = titulo_elem.get("href", "")

                            # Garante que a URL completa está sendo usada
                            if url_oferta and not url_oferta.startswith("http"):
                                url_oferta = f"https://www.pelando.com.br{url_oferta}"

                            # Extrai preços
                            preco_elem = card.select_one("span.thread-price")
                            if not preco_elem:
                                continue

                            preco_atual, preco_original = extrair_preco(
                                preco_elem.get_text(strip=True)
                            )

                            # Se não conseguiu extrair preço, pula para a próxima oferta
                            if not preco_atual:
                                continue

                            # Extrai URL da imagem
                            img_elem = card.select_one("img.thread-image")
                            imagem_url = ""
                            if img_elem:
                                imagem_url = img_elem.get("src", "")
                                if imagem_url.startswith("//"):
                                    imagem_url = f"https:{imagem_url}"

                            # Extrai porcentagem de desconto
                            desconto_elem = card.select_one("span.thread-discount")
                            desconto = 0

                            if desconto_elem:
                                try:
                                    desconto_texto = desconto_elem.get_text(strip=True)
                                    desconto = int(
                                        re.search(r"\d+", desconto_texto).group()
                                    )
                                except (ValueError, AttributeError):
                                    pass

                            # Filtra por desconto mínimo
                            if desconto < min_desconto:
                                continue

                            # Extrai nome da loja
                            loja_elem = card.select_one("span.thread-shop")
                            loja = (
                                loja_elem.get_text(strip=True)
                                if loja_elem
                                else "Desconhecida"
                            )

                            # Extrai URL do produto na loja
                            url_produto = card.select_one("a.cept-tt")
                            url_produto = (
                                url_produto.get("href", "") if url_produto else ""
                            )

                            # Se não tem URL do produto, usa a URL da oferta no Pelando
                            if not url_produto and url_oferta:
                                url_produto = url_oferta

                            # Adiciona a oferta à lista
                            oferta = {
                                "titulo": titulo,
                                "url_produto": url_produto,
                                "url_fonte": url_oferta,
                                "preco": preco_atual,
                                "preco_original": preco_original,
                                "loja": loja,
                                "fonte": "Pelando",
                                "imagem_url": imagem_url,
                                "desconto": desconto,
                                "data_coleta": datetime.now().isoformat(),
                            }

                            # Verifica se a oferta já foi adicionada (evita duplicatas)
                            if not any(
                                o["url_produto"] == oferta["url_produto"]
                                for o in ofertas
                            ):
                                ofertas.append(oferta)
                                logger.debug(
                                    f"Oferta adicionada: {titulo} - {preco_atual}"
                                )

                        except Exception as e:
                            logger.error(f"Erro ao processar card: {e}", exc_info=True)
                            continue

            except asyncio.TimeoutError:
                logger.warning(f"Timeout ao acessar {url}")
                continue
            except Exception as e:
                logger.error(f"Erro ao processar {url}: {e}", exc_info=True)
                continue

        logger.info(f"Busca concluída. Total de ofertas encontradas: {len(ofertas)}")
        return ofertas

    except Exception as e:
        logger.error(f"Erro inesperado ao buscar ofertas: {e}", exc_info=True)
        return []


async def _fetch_requests(url: str) -> str:
    """Busca HTML usando requests/aiohttp"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"❌ Status {response.status} para {url}")
                    return ""
    except Exception as e:
        logger.error(f"❌ Erro ao buscar {url}: {e}")
        return ""


def _parse(html: str) -> list[dict]:
    """Parse HTML para extrair ofertas"""
    try:
        soup = BeautifulSoup(html, "html.parser")
        items = []

        # Seletores para cards de oferta
        selectors = [
            '[data-test-id="threadBox"]',
            "article",
            ".threadCard",
            ".thread-box",
            ".offer-card",
        ]

        cards = []
        for selector in selectors:
            cards.extend(soup.select(selector))
            if cards:
                break

        logger.info(f"🔍 Encontrados {len(cards)} cards com selector: {selector}")

        for card in cards:
            try:
                # Extrai título
                titulo_elem = (
                    card.find("h3")
                    or card.find("h2")
                    or card.find("h1")
                    or card.find("a")
                )
                titulo = (titulo_elem.get_text(" ", strip=True) if titulo_elem else "")[
                    :120
                ]

                if not titulo:
                    continue

                # Extrai preço
                price_text = card.get_text(" ", strip=True)
                m = re.search(r"(R\$\s?\d{1,3}(?:\.\d{3})*,\d{2})", price_text)
                if not m:
                    continue

                preco = m.group(1)

                # Extrai outros campos
                url_produto = ""
                link_elem = card.find("a", href=True)
                if link_elem:
                    url_produto = link_elem["href"]
                    if not url_produto.startswith("http"):
                        url_produto = f"https://www.pelando.com.br{url_produto}"

                # Extrai imagem
                imagem_url = ""
                img_elem = card.find("img")
                if img_elem and img_elem.get("src"):
                    imagem_url = img_elem["src"]
                    if not imagem_url.startswith("http"):
                        imagem_url = f"https://www.pelando.com.br{imagem_url}"

                # Determina loja
                loja = "Pelando"
                if url_produto:
                    if "amazon" in url_produto.lower():
                        loja = "Amazon"
                    elif "shopee" in url_produto.lower():
                        loja = "Shopee"
                    elif "aliexpress" in url_produto.lower():
                        loja = "AliExpress"

                items.append(
                    {
                        "titulo": titulo,
                        "preco": preco,
                        "url_produto": url_produto,
                        "imagem_url": imagem_url,
                        "loja": loja,
                        "fonte": "Pelando",
                    }
                )

            except Exception as e:
                logger.debug(f"Erro ao processar card: {e}")
                continue

        logger.info(f"✅ {len(items)} ofertas extraídas com sucesso")
        return items

    except Exception as e:
        logger.error(f"❌ Erro ao fazer parse do HTML: {e}")
        return []


async def main(limit: int = 20) -> list[dict]:
    """Função principal com fallback Playwright"""
    url = "https://www.pelando.com.br/"

    # Primeira tentativa: scraping normal
    logger.info("🔄 Tentativa 1: Scraping normal com requests")
    html = await _fetch_requests(url)
    cards = _parse(html)

    # Se não encontrou cards, tenta com Playwright
    if not cards:
        logger.info("⚠️ Nenhum card encontrado, tentando com Playwright...")
        try:
            html = await _fetch_playwright(url)  # carregando JS
            cards = _parse(html)
            if cards:
                logger.info(f"✅ Playwright encontrou {len(cards)} cards")
            else:
                logger.warning("❌ Playwright também não encontrou cards")
        except Exception as e:
            logger.error(f"❌ Erro no fallback Playwright: {e}")

    logger.info(f"📊 Total de cards encontrados: {len(cards)}")
    return cards[:limit]


async def _fetch_playwright(url: str) -> str:
    """Fallback usando Playwright para carregar JavaScript"""
    try:
        from base_playwright_scraper import BasePlaywrightScraper

        scraper = BasePlaywrightScraper("https://www.pelando.com.br", "pelando")
        await scraper.setup_browser()

        page = scraper.page
        if not page:
            logger.error("❌ Falha ao configurar Playwright")
            return ""

        # Navega para a página
        await page.goto(url, wait_until="networkidle", timeout=30000)

        # Aguarda carregamento dos cards
        await page.wait_for_selector(
            '[data-test-id="threadBox"], article, .threadCard', timeout=10000
        )

        # Extrai HTML
        html = await page.content()
        logger.info(f"✅ Playwright carregou {len(html)} caracteres")

        return html

    except Exception as e:
        logger.error(f"❌ Erro no Playwright: {e}")
        return ""


# ===== FUNÇÃO COMPATIBILIDADE COM SCRAPER REGISTRY =====

async def get_ofertas(periodo: str = "24h") -> List[Dict[str, Any]]:
    """
    Função de compatibilidade com o scraper registry.
    
    Args:
        periodo: Período para coleta (24h, 7d, 30d, all)
        
    Returns:
        Lista de ofertas encontradas
    """
    try:
        # Buscar ofertas do Pelando
        ofertas = await main(limit=30)
        
        # Adicionar metadados de compatibilidade
        for oferta in ofertas:
            oferta['fonte'] = 'pelando_scraper'
            oferta['periodo'] = periodo
            oferta['timestamp'] = time.time()
        
        return ofertas
        
    except Exception as e:
        logger.error(f"❌ Erro na função get_ofertas: {e}")
        return []

# Configurações para o scraper registry
priority = 90  # Prioridade muito alta (site especializado)
rate_limit = 0.3  # 0.3 requisições por segundo (site sensível)
description = "Scraper para o Pelando - Site especializado em ofertas de tecnologia"

if __name__ == "__main__":
    # Configura logging para debug
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

    # Executa o teste
    asyncio.run(main())
