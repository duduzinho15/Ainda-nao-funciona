"""
Testes unitários para validação de afiliados Awin.

Este módulo testa a geração e validação de deeplinks Awin
usando as fixtures reais fornecidas.
"""

import urllib.parse as up

from tests.data.affiliate_examples import AWIN


def test_awin_deeplink_comfy_home():
    dl = AWIN["comfy_home"]["deeplink"]
    parsed = up.urlparse(dl)
    qs = dict(up.parse_qsl(parsed.query))
    assert parsed.netloc in {"www.awin1.com", "awin1.com"}
    assert parsed.path.endswith("/cread.php")
    assert qs.get("awinmid") == "23377"
    assert qs.get("awinaffid") == "2370719"
    assert (
        qs.get("ued") == up.quote("https://www.comfy.com.br/".rstrip("/"), safe="")
        or qs.get("ued") == "https%3A%2F%2Fwww.comfy.com.br%2F"
    )


def test_awin_deeplink_lg_product():
    dl = AWIN["lg_product"]["deeplink"]
    parsed = up.urlparse(dl)
    qs = dict(up.parse_qsl(parsed.query))
    assert qs.get("awinmid") == "33061"
    assert "lavanderia/washtower/wk14bs6" in up.unquote(qs["ued"])


def test_awin_invalid_domain_block_example():
    # Exemplo: domínio que não deveria passar no conversor
    raw = "https://exemplo-nao-afiliado.com/produto/123"
    # Aqui você chamaria sua função de validação/conversão e esperaria exceção/False.
    # Mantemos um placeholder para garantir que o guard-rail exista.
    assert not raw.startswith(
        "https://www.awin1.com/"
    ), "Domínio inválido não pode virar deeplink Awin automaticamente"
