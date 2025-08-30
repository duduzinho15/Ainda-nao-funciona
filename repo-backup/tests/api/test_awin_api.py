import urllib.parse as up


def test_awin_generate_link_mock():
    advertiser_id = "17729"
    url = "https://www.kabum.com.br/"
    deeplink = f"https://www.awin1.com/cread.php?awinmid={advertiser_id}&awinaffid=2370719&ued={up.quote(url, safe='')}"
    parsed = up.urlparse(deeplink)
    qs = dict(up.parse_qsl(parsed.query))
    assert qs["awinmid"] == advertiser_id
    assert qs["awinaffid"] == "2370719"
    assert up.unquote(qs["ued"]).startswith("https://www.kabum.com.br")
