"""
Testes unitários para validação de afiliados Shopee.

Este módulo testa a validação de URLs e shortlinks da Shopee
usando as fixtures reais fornecidas.
"""

from tests.data.affiliate_examples import SHOPEE


def is_shopee_product(url: str) -> bool:
    return ("/i." in url) or ("/product/" in url)


def is_shopee_short(url: str) -> bool:
    return url.startswith("https://s.shopee.com.br/")


def is_shopee_category(url: str) -> bool:
    return ".-cat." in url or "cat." in url


def test_shopee_product_urls_validas():
    assert is_shopee_product(SHOPEE["product_1"])
    assert is_shopee_product(SHOPEE["product_2"])


def test_shopee_category_bloqueada():
    assert is_shopee_category(SHOPEE["cat"])


def test_shopee_shortlinks_validos():
    assert is_shopee_short(SHOPEE["short_1"])
    assert is_shopee_short(SHOPEE["short_2"])
    assert is_shopee_short(SHOPEE["short_3"])
