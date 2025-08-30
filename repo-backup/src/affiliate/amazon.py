"""
Módulo de afiliação para Amazon com pipeline ASIN-first.

Implementa estratégia de extração de ASIN em ordem de prioridade:
1. URL direta (sem baixar página)
2. HTML leve (regex simples)
3. Playwright como fallback (quando necessário)

Fornece funções para extrair ASINs, converter para URLs de afiliado
canônicas e validar formatos.
"""

import logging
import re
from typing import Optional, Tuple

from src.utils.url_utils import (
    extract_asin_from_url as url_extract_asin,
)
from src.utils.url_utils import (
    get_amazon_domain_from_url,
    is_amazon_url,
    normalize_amazon_dp_url,
)

logger = logging.getLogger(__name__)

# Regex para extrair ASIN da Amazon (formato B0 + 8 caracteres alfanuméricos)
ASIN_REGEX = re.compile(r"\b(B0[A-Z0-9]{8})\b", re.IGNORECASE)

# Tag de afiliado padrão
DEFAULT_AFFILIATE_TAG = "garimpeirogeek-20"

# Idioma padrão para Brasil
DEFAULT_LANGUAGE = "pt_BR"

# Estratégias de extração de ASIN
EXTRACTION_STRATEGIES = {
    "url": "Extração direta da URL",
    "html": "Extração via HTML leve",
    "playwright": "Extração via Playwright (fallback)",
}


def extract_asin_from_url(url: str) -> Optional[str]:
    """
    Extrai o ASIN de uma URL da Amazon usando o utilitário de URL.

    Args:
        url: URL da Amazon para extrair o ASIN

    Returns:
        ASIN extraído ou None se não encontrado
    """
    return url_extract_asin(url)


def extract_asin_from_html(html_content: str) -> Optional[str]:
    """
    Extrai o ASIN do conteúdo HTML da página da Amazon.

    Busca em múltiplos locais:
    - input#ASIN / name=ASIN
    - data-asin no container
    - meta og:url com /dp/
    - JSON-LD contendo ASIN

    Args:
        html_content: Conteúdo HTML da página da Amazon

    Returns:
        ASIN extraído ou None se não encontrado

    Examples:
        >>> extract_asin_from_html('<input id="ASIN" value="B08N5WRWNW">')
        'B08N5WRWNW'
        >>> extract_asin_from_html('<div data-asin="B08N5WRWNW">')
        'B08N5WRWNW'
    """
    if not html_content:
        return None

    try:
        # Buscar em input com id="ASIN" ou name="ASIN"
        asin_input_pattern = (
            r'<input[^>]*(?:id|name)=["\']ASIN["\'][^>]*value=["\']([^"\']+)["\']'
        )
        asin_input_match = re.search(asin_input_pattern, html_content, re.IGNORECASE)
        if asin_input_match:
            asin = asin_input_match.group(1)
            if ASIN_REGEX.match(asin):
                return asin.upper()

        # Buscar em data-asin
        data_asin_pattern = r'data-asin=["\']([^"\']+)["\']'
        data_asin_match = re.search(data_asin_pattern, html_content, re.IGNORECASE)
        if data_asin_match:
            asin = data_asin_match.group(1)
            if ASIN_REGEX.match(asin):
                return asin.upper()

        # Buscar em meta og:url
        og_url_pattern = (
            r'<meta[^>]*property=["\']og:url["\'][^>]*content=["\']([^"\']+)["\']'
        )
        og_url_match = re.search(og_url_pattern, html_content, re.IGNORECASE)
        if og_url_match:
            og_url = og_url_match.group(1)
            asin = extract_asin_from_url(og_url)
            if asin:
                return asin

        # Buscar em JSON-LD
        json_ld_pattern = (
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        )
        json_ld_matches = re.findall(
            json_ld_pattern, html_content, re.IGNORECASE | re.DOTALL
        )

        for json_ld in json_ld_matches:
            # Buscar por "asin" ou "@id" contendo ASIN
            asin_in_json = ASIN_REGEX.search(json_ld)
            if asin_in_json:
                return asin_in_json.group(1).upper()

        # Busca geral por ASIN no HTML
        asin_match = ASIN_REGEX.search(html_content)
        if asin_match:
            return asin_match.group(1).upper()

        return None

    except Exception as e:
        logger.warning(f"Erro ao extrair ASIN do HTML: {e}")
        return None


def to_affiliate_url(
    asin: str, domain: str = "com.br", tag: str = None, language: str = None
) -> str:
    """
    Converte um ASIN para uma URL de afiliado da Amazon.

    Args:
        asin: ASIN do produto
        domain: Domínio da Amazon (padrão: com.br)
        tag: Tag de afiliado (padrão: garimpeirogee-20)
        language: Idioma (padrão: pt_BR)

    Returns:
        URL de afiliado completa

    Examples:
        >>> to_affiliate_url('B08N5WRWNW')
        'https://www.amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogee-20&language=pt_BR'
    """
    if not asin:
        raise ValueError("ASIN é obrigatório")

    # Usar valores padrão se não fornecidos
    tag = tag or DEFAULT_AFFILIATE_TAG
    language = language or DEFAULT_LANGUAGE

    # Construir parâmetros extras
    extra_query = {"tag": tag, "language": language}

    # Usar o utilitário de URL
    return normalize_amazon_dp_url(asin, domain, extra_query)


def canonicalize_amazon(
    url: str, html_content: str = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Canoniza uma URL da Amazon, extraindo o ASIN e convertendo para formato padrão.

    Args:
        url: URL da Amazon para canonizar
        html_content: Conteúdo HTML opcional para extração adicional de ASIN

    Returns:
        Tupla (asin, canonical_url) onde:
        - asin: ASIN extraído ou None
        - canonical_url: URL canônica ou None se ASIN não encontrado

    Examples:
        >>> canonicalize_amazon("https://amazon.com.br/dp/B08N5WRWNW")
        ('B08N5WRWNW', 'https://www.amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogee-20&language=pt_BR')
    """
    if not url:
        return None, None

    # Tentar extrair ASIN da URL primeiro (estratégia 1: URL direta)
    asin = extract_asin_from_url(url)
    strategy_used = "url"

    # Se não encontrou na URL e temos HTML, tentar do HTML (estratégia 2: HTML leve)
    if not asin and html_content:
        asin = extract_asin_from_html(html_content)
        strategy_used = "html"

    if not asin:
        logger.warning(f"ASIN não encontrado para URL: {url}")
        return None, None

    try:
        # Determinar domínio da URL original
        domain = get_amazon_domain_from_url(url)

        # Gerar URL canônica
        canonical_url = to_affiliate_url(asin, domain)

        logger.info(
            f"URL canonizada via {strategy_used}: {url} -> {canonical_url} (ASIN: {asin})"
        )
        return asin, canonical_url

    except Exception as e:
        logger.error(f"Erro ao canonizar URL {url}: {e}")
        return asin, None


def is_valid_amazon_url(url: str) -> bool:
    """
    Verifica se uma URL é uma URL válida da Amazon.

    Args:
        url: URL para verificar

    Returns:
        True se for uma URL válida da Amazon

    Examples:
        >>> is_valid_amazon_url("https://www.amazon.com.br/dp/B08N5WRWNW")
        True
        >>> is_valid_amazon_url("https://www.google.com")
        False
    """
    return is_amazon_url(url)


# Função removida - usando a importada de url_utils
