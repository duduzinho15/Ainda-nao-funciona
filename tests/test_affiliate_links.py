import pytest
from affiliate import AffiliateLinkConverter


def test_detectar_loja_amazon():
    converter = AffiliateLinkConverter()
    loja = converter.detectar_loja("https://www.amazon.com.br/produto/dp/B0ABC123")
    assert loja == "Amazon"


def test_gerar_link_amazon_sync():
    converter = AffiliateLinkConverter()
    original = "https://www.amazon.com.br/dp/B0CHX1Q1FY"
    affiliate = converter._gerar_link_afiliado_sync(original, "Amazon")
    expected = f"https://www.amazon.com.br/dp/B0CHX1Q1FY?tag={converter.amazon_associate_tag}"
    assert affiliate == expected
