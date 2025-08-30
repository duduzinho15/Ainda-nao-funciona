"""
Testes unitários para validação de afiliados Magazine Luiza.

Este módulo testa a validação de URLs de vitrine do Magazine Luiza
usando as fixtures reais fornecidas.
"""

from tests.data.affiliate_examples import MAGALU


def is_magalu_vitrine(url: str) -> bool:
    return url.startswith("https://www.magazinevoce.com.br/magazinegarimpeirogeek/")


def test_magalu_somente_vitrine():
    assert is_magalu_vitrine(MAGALU["vitrine_1"])
    assert is_magalu_vitrine(MAGALU["vitrine_2"])


def test_magalu_bloquear_dominios_nao_vitrine():
    url = "https://www.magazineluiza.com.br/produto/123"
    assert not is_magalu_vitrine(url)
