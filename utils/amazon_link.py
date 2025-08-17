# utils/amazon_link.py
from __future__ import annotations
import re
import asyncio
import logging
from typing import Optional
from urllib.parse import urlparse, parse_qs, unquote, urljoin
import aiohttp
import os

logger = logging.getLogger("amazon_link")

AMAZON_DOMS = {
    "amazon.com.br", "www.amazon.com.br",
    "amzn.to", "www.amzn.to",  # short
}

# ---- 1) Extração de ASIN diretamente da URL ----
_ASIN_PATTERNS = [
    r"/dp/(?P<asin>[A-Z0-9]{10})(?:[/?]|$)",
    r"/gp/product/(?P<asin>[A-Z0-9]{10})(?:[/?]|$)",
    r"/product/(?P<asin>[A-Z0-9]{10})(?:[/?]|$)",
    r"[?&]asin=(?P<asin>[A-Z0-9]{10})(?:[&#]|$)",
    r"/-/(?:pt_BR|pt)/dp/(?P<asin>[A-Z0-9]{10})(?:[/?]|$)",
]

def extract_asin_from_url(url: str) -> Optional[str]:
    """Extrai ASIN diretamente da URL usando regex"""
    if not url:
        return None
    
    for pat in _ASIN_PATTERNS:
        m = re.search(pat, url, flags=re.IGNORECASE)
        if m:
            asin = m.group("asin").upper()
            logger.debug(f"✅ ASIN extraído da URL: {asin}")
            return asin
    
    logger.debug(f"❌ ASIN não encontrado na URL: {url[:100]}...")
    return None

# ---- 2) Expansão de shortlinks e wrappers (HEAD, baixo risco) ----
async def _expand_redirect(url: str, timeout: int = 8) -> Optional[str]:
    """
    Faz uma HEAD (com follow redirects) para resolver shortlinks (ex.: amzn.to).
    Evita GET para reduzir risco de anti-bot. Retorna URL final ou None.
    """
    try:
        headers = {
            "User-Agent": os.getenv("HTTP_UA", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                                               "Chrome/124.0.0.0 Safari/537.36"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        async with aiohttp.ClientSession(headers=headers) as sess:
            async with sess.head(url, allow_redirects=True, timeout=timeout) as r:
                final_url = str(r.url)
                logger.debug(f"✅ Redirect expandido: {url} -> {final_url}")
                return final_url
    except Exception as e:
        logger.warning(f"⚠️ Erro ao expandir redirect {url}: {e}")
        return None

def _unwrap_embedded(url: str) -> Optional[str]:
    """
    Alguns links vêm com ?url=HTTPS%3A%2F%2Fwww.amazon.com.br%2F...
    Tenta extrair a URL alvo sem fazer requisição.
    """
    try:
        qs = parse_qs(urlparse(url).query)
        for key in ("url", "u", "redirect", "ued"):  # ued é comum em Awin
            if key in qs and qs[key]:
                unwrapped = unquote(qs[key][0])
                logger.debug(f"✅ URL desembrulhada: {unwrapped}")
                return unwrapped
    except Exception as e:
        logger.debug(f"⚠️ Erro ao desembrulhar URL: {e}")
    return None

# ---- 3) Fallback Playwright opcional (só se realmente precisar) ----
async def _fetch_canonical_with_playwright(url: str, timeout_ms: int = 15000) -> Optional[str]:
    """
    Abre a página, lê <link rel="canonical"> e tenta extrair o ASIN do canônico.
    Evita baixar recursos pesados e não faz interações.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("⚠️ Playwright não instalado, fallback desabilitado")
        return None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ])
            context = await browser.new_context(
                locale="pt-BR",
                user_agent=os.getenv("HTTP_UA", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                                "Chrome/124.0.0.0 Safari/537.36"),
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()

            # Bloqueia imagens/fonte para reduzir pegada
            async def route_intercept(route):
                if route.request.resource_type in {"image", "media", "font", "stylesheet"}:
                    await route.abort()
                else:
                    await route.continue_()
            await context.route("**/*", route_intercept)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                
                # Tenta ler link canônico
                canonical = await page.eval_on_selector(
                    'link[rel="canonical"]',
                    "el => el.href",
                )
                
                if not canonical:
                    # Fallback: tenta meta ASIN
                    meta_asin = await page.eval_on_selector(
                        'meta[name="ASIN"]',
                        "el => el.content",
                    )
                    if meta_asin:
                        canonical = f"https://www.amazon.com.br/dp/{meta_asin}"
                
                if canonical:
                    logger.debug(f"✅ Canonical extraído via Playwright: {canonical}")
                    return canonical
                    
            except Exception as e:
                logger.warning(f"⚠️ Erro ao ler canonical via Playwright: {e}")
            finally:
                await context.close()
                await browser.close()

    except Exception as e:
        logger.error(f"❌ Erro no Playwright: {e}")
    
    return None

# ---- 4) Função principal: canonicaliza SEM tocar na página quando possível ----
async def canonicalize_amazon(url: str, associate_tag: str) -> Optional[str]:
    """
    Retorna https://www.amazon.com.br/dp/ASIN?tag=<associate_tag>
    sem scraping, preferindo extrair ASIN da própria URL.
    Fallback: HEAD em encurtadores; por último: Playwright.
    """
    if not url:
        return None

    logger.info(f"🔍 Canonicalizando URL Amazon: {url[:100]}...")

    # 4.1) Tenta URL direta
    asin = extract_asin_from_url(url)
    if asin:
        canonical_url = f"https://www.amazon.com.br/dp/{asin}?tag={associate_tag}"
        logger.info(f"✅ ASIN extraído diretamente: {asin}")
        return canonical_url

    # 4.2) Tenta desfazer wrappers/redirect embutido
    unwrapped = _unwrap_embedded(url)
    if unwrapped:
        asin = extract_asin_from_url(unwrapped)
        if asin:
            canonical_url = f"https://www.amazon.com.br/dp/{asin}?tag={associate_tag}"
            logger.info(f"✅ ASIN extraído de URL desembrulhada: {asin}")
            return canonical_url

    # 4.3) Se for amzn.to ou similar, tenta HEAD uma vez
    host = urlparse(url).netloc.lower()
    if host.endswith("amzn.to") or host.endswith("amazon.com.br"):
        logger.info(f"🔍 Expandindo redirect para: {url}")
        final = await _expand_redirect(url)
        if final:
            asin = extract_asin_from_url(final)
            if asin:
                canonical_url = f"https://www.amazon.com.br/dp/{asin}?tag={associate_tag}"
                logger.info(f"✅ ASIN extraído após expandir redirect: {asin}")
                return canonical_url

    # 4.4) Último recurso: Playwright para ler o canônico (evite usar em massa)
    logger.warning(f"⚠️ Usando Playwright como último recurso para: {url}")
    canonical = await _fetch_canonical_with_playwright(url)
    if canonical:
        asin = extract_asin_from_url(canonical)
        if asin:
            canonical_url = f"https://www.amazon.com.br/dp/{asin}?tag={associate_tag}"
            logger.info(f"✅ ASIN extraído via Playwright: {asin}")
            return canonical_url

    # 4.5) Não deu
    logger.error(f"❌ Não foi possível canonicalizar: {url}")
    return None

# ---- 5) Função síncrona para compatibilidade ----
def canonicalize_amazon_sync(url: str, associate_tag: str) -> Optional[str]:
    """Versão síncrona para compatibilidade com código existente"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Se já estiver em um loop async, retorna None para usar versão async
            logger.warning("⚠️ Loop async já rodando, use canonicalize_amazon()")
            return None
        else:
            return asyncio.run(canonicalize_amazon(url, associate_tag))
    except RuntimeError:
        # Se não há loop, cria um novo
        return asyncio.run(canonicalize_amazon(url, associate_tag))
