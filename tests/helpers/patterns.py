"""
Padrões regex para validação de URLs de afiliados em testes.

Este módulo contém expressões regulares usadas para validar
formato e estrutura de URLs de diferentes plataformas.
"""

import re
from typing import Pattern

# Padrões para URLs da Awin
AWIN_DEEPLINK_PATTERN: Pattern = re.compile(
    r"^https://www\.awin1\.com/cread\.php\?"
    r"awinmid=(\d+)&"
    r"awinaffid=(\d+)&"
    r"ued=.+$"
)

AWIN_ALLOWED_DOMAINS: Pattern = re.compile(
    r"^(www\.)?(comfy\.com\.br|trocafy\.com\.br|lg\.com|kabum\.com\.br)$"
)

# Padrões para URLs do Mercado Livre
ML_PRODUCT_PATTERN: Pattern = re.compile(
    r"^https://(www\.|produto\.)?mercadolivre\.com\.br/.*?/(p/MLB\d+|up/MLBU\d+|MLB-\d+|[^/]*MLB\d+|[^/]*MLB-\d+)"
)

ML_SHORTLINK_PATTERN: Pattern = re.compile(
    r"^https://mercadolivre\.com/sec/[a-zA-Z0-9]+$"
)

ML_SOCIAL_PATTERN: Pattern = re.compile(
    r"^https://www\.mercadolivre\.com\.br/social/garimpeirogeek\?"
    r"matt_word=garimpeirogeek&"
    r"matt_tool=\d+&"
    r"forceInApp=true&"
    r"ref=[a-zA-Z0-9+/=%]+$"
)

# Padrões para URLs da Shopee
SHOPEE_PRODUCT_PATTERN: Pattern = re.compile(r"^https://shopee\.com\.br/.*?i\.\d+\.\d+")

SHOPEE_SHORTLINK_PATTERN: Pattern = re.compile(
    r"^https://s\.shopee\.com\.br/[a-zA-Z0-9]+$"
)

SHOPEE_CATEGORY_PATTERN: Pattern = re.compile(r"^https://shopee\.com\.br/.*?cat\.\d+")

# Padrões para URLs do Magazine Luiza
MAGALU_VITRINE_PATTERN: Pattern = re.compile(
    r"^https://www\.magazinevoce\.com\.br/"
    r"magazinegarimpeirogeek/.*?/p/\d+/te/[a-zA-Z0-9-]+/?$"
)

# Padrões para URLs da Amazon
AMAZON_PRODUCT_PATTERN: Pattern = re.compile(
    r"^https://www\.amazon\.com\.br/.*?/dp/([A-Z0-9]{10})"
)

AMAZON_SHORTLINK_PATTERN: Pattern = re.compile(r"^https://amzn\.to/[a-zA-Z0-9]+$")

AMAZON_CANONICAL_PATTERN: Pattern = re.compile(
    r"^https://www\.amazon\.com\.br/.*?/dp/[A-Z0-9]{10}\?"
    r".*?tag=garimpeirogee-20.*?"
    r"linkCode=ll1.*?"
    r"linkId=[a-zA-Z0-9]+"
)

# Padrões para URLs do AliExpress
ALIEXPRESS_PRODUCT_PATTERN: Pattern = re.compile(
    r"^https://pt\.aliexpress\.com/item/\d+\.html"
)

ALIEXPRESS_SHORTLINK_PATTERN: Pattern = re.compile(
    r"^https://s\.click\.aliexpress\.com/e/_[a-zA-Z0-9]+$"
)

# Padrões para validação geral
VALID_HTTP_URL: Pattern = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")

VALID_DOMAIN: Pattern = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
)


def is_valid_awin_deeplink(url: str) -> bool:
    """Verifica se uma URL é um deeplink Awin válido."""
    # Primeiro verifica se o formato básico está correto
    if not AWIN_DEEPLINK_PATTERN.match(url):
        return False

    # Extrai e valida o parâmetro UED
    from urllib.parse import parse_qs, urlparse

    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        ued_value = query_params.get("ued", [""])[0]

        # Se o UED começa com http/https, deve ser uma URL válida
        if ued_value.startswith(("http://", "https://")):
            return True

        # Se contém caracteres de codificação percentual, provavelmente é válido
        if "%" in ued_value:
            return True

        # Se contém caracteres típicos de URL (/, ?, #, etc.), provavelmente é válido
        if any(char in ued_value for char in "/?#"):
            return True

        # Se é apenas texto simples sem caracteres especiais, rejeita
        return False

    except Exception:
        return False


def is_valid_mercadolivre_product(url: str) -> bool:
    """Verifica se uma URL é um produto do Mercado Livre válido."""
    return bool(ML_PRODUCT_PATTERN.match(url))


def is_valid_shopee_product(url: str) -> bool:
    """Verifica se uma URL é um produto da Shopee válido."""
    return bool(SHOPEE_PRODUCT_PATTERN.match(url))


def is_valid_magalu_vitrine(url: str) -> bool:
    """Verifica se uma URL é uma vitrine do Magazine Luiza válida."""
    return bool(MAGALU_VITRINE_PATTERN.match(url))


def is_valid_amazon_product(url: str) -> bool:
    """Verifica se uma URL é um produto da Amazon válido."""
    return bool(AMAZON_PRODUCT_PATTERN.match(url))


def is_valid_aliexpress_product(url: str) -> bool:
    """Verifica se uma URL é um produto do AliExpress válido."""
    return bool(ALIEXPRESS_PRODUCT_PATTERN.match(url))


def extract_amazon_asin(url: str) -> str | None:
    """
    Extrai o ASIN de uma URL da Amazon.

    Args:
        url: URL da Amazon

    Returns:
        ASIN extraído ou None se não encontrado
    """
    match = AMAZON_PRODUCT_PATTERN.match(url)
    if match:
        return match.group(1)
    return None


def extract_mercadolivre_id(url: str) -> str | None:
    """
    Extrai o ID do produto do Mercado Livre.

    Args:
        url: URL do Mercado Livre

    Returns:
        ID extraído ou None se não encontrado
    """
    match = re.search(r"/p/(MLB\d+)", url)
    if match:
        return match.group(1)
    return None


def extract_shopee_ids(url: str) -> tuple[str | None, str | None]:
    """
    Extrai os IDs da Shopee (seller e item).

    Args:
        url: URL da Shopee

    Returns:
        Tupla com (seller_id, item_id) ou (None, None) se não encontrados
    """
    match = re.search(r"/i\.(\d+)\.(\d+)", url)
    if match:
        return match.group(1), match.group(2)
    return None, None
