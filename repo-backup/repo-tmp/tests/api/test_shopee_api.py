import hashlib
import json

import pytest


def shopee_signature(app_id: str, secret: str, payload: dict, ts: int) -> str:
    base = f"{app_id}{ts}{json.dumps(payload, separators=(',',':'), ensure_ascii=False)}{secret}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def test_shopee_signature_ok():
    app_id = "demo_app"
    secret = "demo_secret"
    payload = {
        "query": "GetShortLink",
        "variables": {"origin_url": "https://shopee.com.br/i.1.2"},
    }
    ts = 1700000000
    sig = shopee_signature(app_id, secret, payload, ts)
    assert len(sig) == 64
    # sua função real deve gerar a MESMA assinatura para o mesmo input


@pytest.mark.asyncio
async def test_shopee_get_shortlink_mock(aiohttp_client, monkeypatch):
    # Exemplo: mock do método do seu cliente para retornar shortlink
    class Dummy:
        async def create_shortlink(self, url: str, sub_id: str | None = None):
            assert url.startswith("https://shopee.com.br/")
            return "https://s.shopee.com.br/XYZ"

    cli = Dummy()
    got = await cli.create_shortlink("https://shopee.com.br/i.1.2", "tg")
    assert got.startswith("https://s.shopee.com.br/")
