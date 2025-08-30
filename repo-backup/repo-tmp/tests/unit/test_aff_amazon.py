"""
Testes unitários para validação de afiliados Amazon.

Este módulo testa a validação de URLs e links canônicos da Amazon
usando as fixtures reais fornecidas.
"""

import re
from urllib.parse import parse_qs, urlparse

from tests.data.affiliate_examples import AMAZON

ASIN_RE = re.compile(r"\b(B0[A-Z0-9]{8})\b")


def extract_asin(url: str) -> str | None:
    m = ASIN_RE.search(url)
    return m.group(1) if m else None


def has_tag(url: str) -> bool:
    qs = parse_qs(urlparse(url).query)
    return qs.get("tag", [""])[0] == "garimpeirogee-20"


def test_amazon_extrai_asin_dos_links():
    assert extract_asin(AMAZON["product_1"]) is not None
    assert extract_asin(AMAZON["product_2"]) is not None


def test_amazon_canonicos_com_tag():
    assert has_tag(AMAZON["canon_1"])
    assert has_tag(AMAZON["canon_2"])


def test_amazon_amzn_to_precisa_normalizar():
    assert AMAZON["short_1"].startswith("https://amzn.to/")
    assert AMAZON["short_2"].startswith("https://amzn.to/")
