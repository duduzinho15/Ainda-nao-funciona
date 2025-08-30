import pytest


@pytest.mark.asyncio
async def test_rakuten_deeplink_mock():
    class DummyRkt:
        async def build_deeplink(
            self, advertiser_id: str, url: str, u1: str | None = None
        ):
            assert advertiser_id.isdigit()
            assert url.startswith("https://")
            return {
                "deep_link": f"https://click.linksynergy.com/deeplink?id=AFF&mid={advertiser_id}&murl={url}"
            }

    cli = DummyRkt()
    res = await cli.build_deeplink("12345", "https://www.loja.com/produto/1", "tg")
    assert "linksynergy" in res["deep_link"]
    assert "mid=12345" in res["deep_link"]
