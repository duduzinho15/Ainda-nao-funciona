import pytest
from promobit_scraper import extract_ofertas_from_html, extract_price_value


def test_extract_ofertas_from_html_basic():
    html = (
        '<a href="/oferta/produto-123">'
        '<span class="line-clamp-2">Produto 123</span>'
        '<span class="text-primary-400">R$ 10,99</span>'
        '<span class="font-bold text-sm">Loja X</span>'
        '<img src="https://example.com/img.jpg" />'
        '</a>'
    )
    ofertas = extract_ofertas_from_html(html)
    assert len(ofertas) == 1
    oferta = ofertas[0]
    assert oferta["titulo"] == "Produto 123"
    assert oferta["preco"] == "R$ 10,99"
    assert oferta["url_produto"].endswith("/oferta/produto-123")


def test_extract_price_value():
    assert extract_price_value("R$ 1234,56") == pytest.approx(1234.56)
    assert extract_price_value(None) is None
