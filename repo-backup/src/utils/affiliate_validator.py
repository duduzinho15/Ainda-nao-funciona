"""
Validador centralizado de links de afiliado para Garimpeiro Geek.

Implementa validações para todas as plataformas de afiliado baseadas
nos exemplos dos arquivos de referência.
"""

import logging
import re
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

# Padrões de validação para cada plataforma
AFFILIATE_PATTERNS = {
    "awin": {
        "pattern": (
            r"https?://(?:www\.)?awin1\.com/cread\.php\?.*?awinmid="
            r"(23377|51277|33061|17729|106765|25539).*?awinaffid="
            r"(2370719|2510157).*?ued="
        ),
        "required_params": ["awinmid", "awinaffid", "ued"],
        "description": "Deeplink Awin com MIDs válidos (Comfy, Trocafy, LG, KaBuM, Ninja, Samsung) e AFFIDs corretos",
        "valid_mids": [23377, 51277, 33061, 17729, 106765, 25539],
        "valid_affids": [2370719, 2510157],
    },
    "mercadolivre": {
        "pattern": (
            r"mercadolivre\.com\.br.*MLB[U]?|mercadolivre\.com/sec/|"
            r"mercadolivre\.com\.br/sec/|mercadolivre\.com\.br/social/garimpeirogeek"
        ),
        "required_params": [],
        "description": "Link Mercado Livre com etiqueta garimpeirogeek, shortlink /sec/, ou estrutura de produto MLB/MLBU",
    },
    "amazon": {
        "pattern": r"https?://(?:www\.)?amazon\.com\.br/",
        "required_params": ["tag"],
        "description": "Link Amazon com ASIN válido e tag=garimpeirogee-20",
        "validate_asin": True,
    },
    "shopee": {
        "pattern": r"https?://(?:www\.)?shopee\.com\.br/|https?://s\.shopee\.com\.br/",
        "required_params": [],
        "description": "URL do Shopee (qualquer formato) ou shortlink s.shopee.com.br/",
    },
    "aliexpress": {
        "pattern": r"https?://s\.click\.aliexpress\.com/e/[A-Za-z0-9_-]+",
        "required_params": [],
        "description": "Shortlink AliExpress s.click.aliexpress.com/e/",
    },
    "magazineluiza": {
        "pattern": r"https?://(?:www\.)?magazinevoce\.com\.br/magazinegarimpeirogeek/.*?/p/\d+",
        "required_params": [],
        "description": "Link Magazine Luiza com vitrine magazinegarimpeirogeek e estrutura de produto",
    },
}


def validate_affiliate_link(
    url: str, expected_platform: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Valida se uma URL é um link de afiliado válido.

    Args:
        url: URL para validar
        expected_platform: Plataforma esperada (opcional)

    Returns:
        Tuple (is_valid, detected_platform, error_message)
    """
    if not url:
        return False, "unknown", "URL vazia"

    # Detectar plataforma automaticamente
    detected_platform = detect_platform(url)

    if not detected_platform:
        return False, "unknown", "Plataforma não reconhecida"

    # Se uma plataforma específica foi esperada, validar
    if expected_platform and expected_platform.lower() != detected_platform:
        return (
            False,
            detected_platform,
            f"Plataforma esperada: {expected_platform}, detectada: {detected_platform}",
        )

    # Validar conforme a plataforma detectada
    if detected_platform == "awin":
        return validate_awin_specific(url)
    elif detected_platform == "amazon":
        return validate_amazon_specific(url)
    elif detected_platform == "mercadolivre":
        return validate_mercadolivre_specific(url)
    elif detected_platform == "shopee":
        return validate_shopee_specific(url)
    elif detected_platform == "aliexpress":
        return validate_aliexpress_specific(url)
    elif detected_platform == "magazineluiza":
        return validate_magazineluiza_specific(url)

    return (
        False,
        detected_platform,
        f"Validação não implementada para {detected_platform}",
    )


def detect_platform(url: str) -> Optional[str]:
    """Detecta a plataforma de afiliado baseada na URL"""
    for platform, config in AFFILIATE_PATTERNS.items():
        if re.search(config["pattern"], url, re.IGNORECASE):
            return platform
    return None


def validate_awin_specific(url: str) -> Tuple[bool, str, Optional[str]]:
    """Validação específica para Awin com MIDs e AFFIDs válidos"""
    try:
        parsed = urlparse(url)

        # Validar domínio
        if parsed.netloc not in ["www.awin1.com", "awin1.com"]:
            return False, "awin", "Domínio inválido para Awin"

        # Validar path
        if parsed.path != "/cread.php":
            return False, "awin", "Path inválido para Awin"

        # Validar parâmetros
        query_params = parse_qs(parsed.query)

        # Verificar parâmetros obrigatórios
        required_params = ["awinmid", "awinaffid", "ued"]
        for param in required_params:
            if param not in query_params:
                return False, "awin", f"Parâmetro obrigatório ausente: {param}"

        # Validar MID
        try:
            mid = int(query_params["awinmid"][0])
            if mid not in AFFILIATE_PATTERNS["awin"]["valid_mids"]:
                return False, "awin", f"MID inválido: {mid}"
        except (ValueError, IndexError):
            return False, "awin", "MID deve ser um número inteiro"

        # Validar AFFID
        try:
            affid = int(query_params["awinaffid"][0])
            if affid not in AFFILIATE_PATTERNS["awin"]["valid_affids"]:
                return False, "awin", f"AFFID inválido: {affid}"
        except (ValueError, IndexError):
            return False, "awin", "AFFID deve ser um número inteiro"

        # Validar UED
        ued = query_params["ued"][0]
        if not ued.startswith("http"):
            return False, "awin", "Parâmetro UED deve ser uma URL válida"

        return True, "awin", None

    except Exception as e:
        return False, "awin", f"Erro ao validar Awin: {e}"


def validate_amazon_specific(url: str) -> Tuple[bool, str, Optional[str]]:
    """Validação específica para Amazon com ASIN válido"""
    try:
        from src.utils.url_utils import extract_asin_from_url
    except ImportError:
        # Fallback para quando executado como script standalone
        import os
        import sys

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from src.utils.url_utils import extract_asin_from_url

    # Extrair ASIN da URL
    asin = extract_asin_from_url(url)
    if not asin:
        return False, "amazon", "ASIN não encontrado na URL Amazon"

    # Validar formato do ASIN
    if not validate_amazon_asin_format(asin):
        return False, "amazon", f"Formato de ASIN inválido: {asin}"

    # Verificar tag de afiliado
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    if "tag" not in query_params:
        return False, "amazon", "Tag de afiliado ausente"

    tag = query_params["tag"][0]
    if tag != "garimpeirogee-20":
        return (
            False,
            "amazon",
            f"Tag de afiliado incorreta: {tag}. Esperado: garimpeirogee-20",
        )

    # Verificar parâmetro language
    if "language" not in query_params:
        return False, "amazon", "Parâmetro 'language=pt_BR' é obrigatório"

    language = query_params["language"][0]
    if language != "pt_BR":
        return False, "amazon", f"Language incorreto: {language}. Esperado: pt_BR"

    return True, "amazon", None


def validate_mercadolivre_specific(url: str) -> Tuple[bool, str, Optional[str]]:
    """Validação específica para Mercado Livre - APENAS SHORTLINKS E PÁGINAS SOCIAIS"""
    # Verificar se é shortlink válido (formato aceito)
    if re.match(
        r"^https?://(?:www\.)?mercadolivre\.com(?:\.br)?/sec/[A-Za-z0-9]+$", url
    ):
        return True, "mercadolivre", None

    # Verificar se é link social válido (formato aceito)
    if re.match(
        r"^https?://(?:www\.)?mercadolivre\.com\.br/social/garimpeirogeek\?.*matt_word=garimpeirogeek",
        url,
    ):
        return True, "mercadolivre", None

    # Verificar se é página de categoria/busca/perfil (sempre rejeitar)
    parsed = urlparse(url)
    path_lower = parsed.path.lower()
    if any(
        x in path_lower
        for x in ["/categoria", "/search", "/profile", "/user", "/seller", "/browse"]
    ):
        return (
            False,
            "mercadolivre",
            "Página de categoria/busca/perfil não é válida para afiliação",
        )

    # Verificar se é produto bruto (deve ser convertido primeiro)
    product_patterns = [
        r"/MLB[U]?-\d+",  # Formato: /MLB-123456789 ou /MLBU-123456789
        r"/p/MLB[U]?\d+",  # Formato: /p/MLB123456789 ou /p/MLBU123456789
        r"/item/MLB[U]?\d+",  # Formato: /item/MLB123456789 ou /item/MLBU123456789
        r"/produto/MLB[U]?\d+",  # Formato: /produto/MLB123456789 ou /produto/MLBU123456789
        r"/up/MLB[U]?\d+",  # Formato: /up/MLB123456789 ou /up/MLBU123456789
        r"MLB[U]?\d+",  # Formato: MLB123456789 ou MLBU123456789
    ]

    # Verificar se é produto bruto (deve ser convertido para shortlink ou social primeiro)
    for pattern in product_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return (
                False,
                "mercadolivre",
                "Produto bruto ML deve ser convertido para shortlink /sec/ ou página social primeiro",
            )

    return (
        False,
        "mercadolivre",
        "Apenas shortlinks /sec/ ou páginas sociais garimpeirogeek são aceitos para ML",
    )


def validate_shopee_specific(url: str) -> Tuple[bool, str, Optional[str]]:
    """Validação específica para Shopee - APENAS SHORTLINKS SÃO ACEITOS"""
    # Verificar se é shortlink válido (ÚNICO formato aceito)
    # Deve ter entre 4 e 20 caracteres alfanuméricos
    shortlink_pattern = r"^https?://s\.shopee\.com\.br/[A-Za-z0-9]{4,20}$"
    if re.match(shortlink_pattern, url):
        return True, "shopee", None

    # Verificar se é página de categoria (sempre rejeitar)
    parsed = urlparse(url)
    path_lower = parsed.path.lower()
    if any(
        x in path_lower for x in ["/cat.", "/search", "/profile", "/user", "/seller"]
    ):
        return (
            False,
            "shopee",
            "Página de categoria/busca/perfil não é válida para afiliação",
        )

    # Verificar se é produto bruto (deve ser convertido para shortlink primeiro)
    product_patterns = [
        r"i\.\d+\.\d+",  # Formato: i.{SELLER_ID}.{ITEM_ID}
        r"/product/\d+/\d+",  # Formato: product/{SELLER_ID}/{ITEM_ID}
    ]

    for pattern in product_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return (
                False,
                "shopee",
                "Produto bruto Shopee deve ser convertido para shortlink primeiro",
            )

    return False, "shopee", "Apenas shortlinks s.shopee.com.br são aceitos para Shopee"


def validate_aliexpress_specific(url: str) -> Tuple[bool, str, Optional[str]]:
    """Validação específica para AliExpress - APENAS SHORTLINKS SÃO ACEITOS"""
    # Verificar se é shortlink válido (ÚNICO formato aceito)
    # Deve ter pelo menos 6 caracteres no código do shortlink
    if re.match(r"^https?://s\.click\.aliexpress\.com/e/[A-Za-z0-9_-]{6,}$", url):
        return True, "aliexpress", None

    # Verificar se é produto bruto (deve ser convertido para shortlink primeiro)
    product_patterns = [
        r"pt\.aliexpress\.com/item/\d+\.html",  # Formato: pt.aliexpress.com/item/123456789.html
        r"aliexpress\.com/item/\d+\.html",  # Formato: aliexpress.com/item/123456789.html
        r"pt\.aliexpress\.com/store/",  # Loja
        r"aliexpress\.com/store/",  # Loja
        r"pt\.aliexpress\.com/category/",  # Categoria
        r"aliexpress\.com/category/",  # Categoria
    ]

    for pattern in product_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return (
                False,
                "aliexpress",
                "Produto bruto AliExpress deve ser convertido para shortlink primeiro",
            )

    return (
        False,
        "aliexpress",
        "Apenas shortlinks s.click.aliexpress.com/e/ são aceitos para AliExpress",
    )


def validate_magazineluiza_specific(url: str) -> Tuple[bool, str, Optional[str]]:
    """Validação específica para Magazine Luiza"""
    if re.match(
        r"^https?://(?:www\.)?magazinevoce\.com\.br/magazinegarimpeirogeek/.*?/p/\d+",
        url,
    ):
        return True, "magazineluiza", None

    return False, "magazineluiza", "Formato de link Magazine Luiza inválido"


def validate_amazon_asin_format(asin: str) -> bool:
    """Valida formato do ASIN Amazon"""
    # ASIN deve ter 10 caracteres alfanuméricos
    if not re.match(r"^[A-Z0-9]{10}$", asin):
        return False

    # Geralmente começa com B0
    if not asin.startswith("B0"):
        return False

    return True


def get_validation_summary() -> Dict[str, Any]:
    """Retorna resumo das validações disponíveis"""
    return {
        "platforms": list(AFFILIATE_PATTERNS.keys()),
        "patterns_count": len(AFFILIATE_PATTERNS),
        "descriptions": {k: v["description"] for k, v in AFFILIATE_PATTERNS.items()},
    }


# Teste dos exemplos do arquivo de referência
if __name__ == "__main__":
    print("🧪 TESTANDO VALIDADOR CENTRALIZADO COM EXEMPLOS DO ARQUIVO")
    print("=" * 75)

    # Exemplos do arquivo "Informações base de geração de link.txt"
    test_cases = [
        # Awin
        "https://www.awin1.com/cread.php?awinmid=23377&awinaffid=2370719&ued=https%3A%2F%2Fwww.comfy.com.br%2F",
        # Mercado Livre
        "https://www.mercadolivre.com.br/social/garimpeirogeek?matt_word=garimpeirogeek&matt_tool=82173227&forceInApp=true&ref=test",
        "https://mercadolivre.com/sec/1vt6gtj",
        # Amazon
        "https://www.amazon.com.br/Apple-iPhone-13-256-GB-das-estrelas/dp/B09T4WC9GN?tag=garimpeirogee-20&language=pt_BR",
        # Shopee
        "https://s.shopee.com.br/3LGfnEjEXu",
        # AliExpress
        "https://s.click.aliexpress.com/e/_opftn1L",
        # Magazine Luiza
        "https://www.magazinevoce.com.br/magazinegarimpeirogeek/apple-iphone-14-128gb-estelar-61-12mp-ios-5g/p/237184100/te/ip14/",
        # URLs inválidas
        "https://exemplo-invalido.com/produto",
        "https://www.amazon.com.br/produto-sem-tag",
        "https://www.awin1.com/cread.php?awinmid=99999&awinaffid=999999&ued=https://exemplo.com",
    ]

    for url in test_cases:
        print(f"\n🔍 Testando: {url}")

        is_valid, platform, error = validate_affiliate_link(url)

        if is_valid:
            print(f"   ✅ VÁLIDO - {platform.upper()}")
        else:
            print(f"   ❌ INVÁLIDO - {platform.upper()}: {error}")

    # Resumo das validações
    print("\n📊 RESUMO DAS VALIDAÇÕES:")
    summary = get_validation_summary()
    for platform, description in summary["descriptions"].items():
        print(f"   {platform.upper()}: {description}")
