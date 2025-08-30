"""
Utilitários para manipulação de URLs, especialmente para extração de ASINs da Amazon.
"""

import re
from urllib.parse import urlparse, urlunparse

# Regex robusta para ASIN: 10 caracteres alfanuméricos (geralmente começa com B0)
# Padrões expandidos para cobrir mais formatos de URL da Amazon
ASIN_RE = re.compile(
    r"(?:dp|product|aw/d|gp/product|s|d)/([A-Z0-9]{10})(?:[/?]|$)", re.IGNORECASE
)
ASIN_QUERY_RE = re.compile(r"\b(?:ASIN|asin)=([A-Z0-9]{10})\b", re.IGNORECASE)


def strip_tracking_params(url: str) -> str:
    """
    Remove parâmetros comuns de tracking da Amazon, preservando caminho básico.

    Args:
        url: URL da Amazon com parâmetros de tracking

    Returns:
        URL limpa sem parâmetros de tracking
    """
    parsed = urlparse(url)

    # Drop query inteira (strategy simples e segura p/ maximizar match de ASIN no path)
    cleaned = parsed._replace(query="", fragment="")

    return urlunparse(cleaned)


def extract_asin_from_url(url: str) -> str | None:
    """
    Tenta extrair ASIN direto do URL (dp, gp/product, ASIN=).

    Args:
        url: URL da Amazon

    Returns:
        ASIN extraído ou None se não encontrado
    """
    if not url:
        return None

    # Verificar se é uma URL da Amazon antes de extrair
    if not is_amazon_url(url):
        return None

    # Primeiro, tentar extrair do path (formato mais comum)
    m = ASIN_RE.search(url)
    if m:
        return m.group(1).upper()

    # Se não encontrou no path, tentar parâmetro ASIN na query
    m = ASIN_QUERY_RE.search(url)
    if m:
        return m.group(1).upper()

    # Se ainda não encontrou, tentar com URL limpa
    cleaned_url = strip_tracking_params(url)
    if cleaned_url != url:
        m = ASIN_RE.search(cleaned_url)
        if m:
            return m.group(1).upper()

    return None


def normalize_amazon_dp_url(
    asin: str, domain: str = "com.br", extra_query: dict[str, str] | None = None
) -> str:
    """
    Normaliza URL da Amazon para formato canônico /dp/{ASIN}.

    Args:
        asin: ASIN do produto
        domain: Domínio da Amazon (com.br, com, etc.)
        extra_query: Parâmetros adicionais para query string

    Returns:
        URL canônica da Amazon
    """
    base = f"https://www.amazon.{domain}/dp/{asin}"

    query = ""
    if extra_query:
        # Monta query simples, sem dupla codificação
        query = "?" + "&".join(
            f"{k}={v}" for k, v in extra_query.items() if v is not None
        )

    return base + query


def is_amazon_url(url: str) -> bool:
    """
    Verifica se a URL é da Amazon.

    Args:
        url: URL para verificar

    Returns:
        True se for URL da Amazon
    """
    if not url:
        return False

    amazon_domains = [
        "amazon.com.br",
        "amazon.com",
        "amazon.co.uk",
        "amazon.de",
        "amazon.fr",
        "amazon.it",
        "amazon.es",
        "amazon.ca",
        "amazon.com.mx",
        "amazon.com.au",
        "amazon.in",
        "amazon.co.jp",
    ]

    try:
        parsed = urlparse(url.lower())
        return any(domain in parsed.netloc for domain in amazon_domains)
    except Exception:
        return False


def get_amazon_domain_from_url(url: str) -> str:
    """
    Extrai o domínio da Amazon de uma URL.

    Args:
        url: URL da Amazon

    Returns:
        Domínio extraído (ex: com.br, com)
    """
    if not is_amazon_url(url):
        return "com.br"  # Padrão para Brasil

    try:
        parsed = urlparse(url.lower())
        netloc = parsed.netloc

        # Extrair domínio principal
        if "amazon.com.br" in netloc:
            return "com.br"
        elif "amazon.com" in netloc:
            return "com"
        elif "amazon.co.uk" in netloc:
            return "co.uk"
        elif "amazon.de" in netloc:
            return "de"
        elif "amazon.fr" in netloc:
            return "fr"
        elif "amazon.it" in netloc:
            return "it"
        elif "amazon.es" in netloc:
            return "es"
        elif "amazon.ca" in netloc:
            return "ca"
        elif "amazon.com.mx" in netloc:
            return "com.mx"
        elif "amazon.com.au" in netloc:
            return "com.au"
        elif "amazon.in" in netloc:
            return "in"
        elif "amazon.co.jp" in netloc:
            return "co.jp"
        else:
            return "com.br"  # Padrão

    except Exception:
        return "com.br"  # Padrão em caso de erro
