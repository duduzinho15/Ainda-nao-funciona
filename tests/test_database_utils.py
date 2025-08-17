from database import extrair_dominio_loja


def test_extrair_dominio_loja():
    url = "https://www.amazon.com.br/gp/product/B0ABC123"
    assert extrair_dominio_loja(url) == "amazon.com.br"
    assert extrair_dominio_loja("not a url") == ""
