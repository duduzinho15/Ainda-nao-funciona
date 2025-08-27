"""
Testes para validação de guardrails de afiliação.
"""

import re

import pytest

from src.affiliate.aliexpress import build_aliexpress_short
from src.affiliate.awin import build_awin_deeplink
from src.affiliate.shopee import build_shopee_short


class TestAffiliateGuardrails:
    """Testes para validação de formatos de links de afiliado"""

    # Regex de validação por plataforma
    VALIDATION_REGEX = {
        "awin": r"^https?://(www\.)?awin1\.com/cread\.php\?(.+)$",
        "mercadolivre": r"^https?://(www\.)?mercadolivre\.com(\.br)?/sec/.+|^https?://www\.mercadolivre\.com\.br/social/garimpeirogeek.+$",
        "magalu": r"^https?://www\.magazinevoce\.com\.br/magazinegarimpeirogeek/.+$",
        "amazon": r"^https?://(www\.)?amazon\.com\.br/.+(\?|&)tag=garimpeirogee-20(&|$).+$",
        "shopee": r"^https?://s\.shopee\.com\.br/.+$",
        "aliexpress": r"^https?://s\.click\.aliexpress\.com/e/.+$",
    }

    # URLs de teste para cada plataforma
    TEST_URLS = {
        "awin": {
            "comfy": "https://www.comfy.com.br/cadeira-ergonomica.html",
            "kabum": "https://www.kabum.com.br/produto/123/monitor-gamer.html",
            "lg": "https://www.lg.com/br/lavanderia/washtower/",
            "samsung": "https://www.samsung.com/br/smartphones/galaxy-s24/",
        },
        "shopee": "https://shopee.com.br/iPhone-16-Pro-Max-256GB-5G-i.337570318.22498324413",
        "aliexpress": "https://pt.aliexpress.com/item/1005006756452012.html",
    }

    def test_awin_deeplink_format(self):
        """Testa se todos os deeplinks Awin seguem o formato correto"""
        for loja, url in self.TEST_URLS["awin"].items():
            deeplink = build_awin_deeplink(url, loja)

            # Verificar regex
            assert re.match(
                self.VALIDATION_REGEX["awin"], deeplink
            ), f"Deeplink Awin para {loja} não segue o formato esperado: {deeplink}"

            # Verificar elementos obrigatórios
            assert "/cread.php" in deeplink
            assert "awinmid=" in deeplink
            assert "awinaffid=" in deeplink
            assert "ued=" in deeplink

    def test_shopee_shortlink_format(self):
        """Testa se shortlinks Shopee seguem o formato correto"""
        url = self.TEST_URLS["shopee"]
        shortlink = build_shopee_short(url)

        # Verificar regex
        assert re.match(
            self.VALIDATION_REGEX["shopee"], shortlink
        ), f"Shortlink Shopee não segue o formato esperado: {shortlink}"

        # Verificar elementos obrigatórios
        assert shortlink.startswith("https://s.shopee.com.br/")
        assert len(shortlink.split("/")[-1]) > 0  # Deve ter código

    def test_aliexpress_shortlink_format(self):
        """Testa se shortlinks AliExpress seguem o formato correto"""
        url = self.TEST_URLS["aliexpress"]
        shortlink = build_aliexpress_short(url)

        # Verificar regex
        assert re.match(
            self.VALIDATION_REGEX["aliexpress"], shortlink
        ), f"Shortlink AliExpress não segue o formato esperado: {shortlink}"

        # Verificar elementos obrigatórios
        assert shortlink.startswith("https://s.click.aliexpress.com/e/")
        assert len(shortlink.split("/")[-1]) > 0  # Deve ter código

    def test_no_raw_store_urls_in_awin(self):
        """Testa se nenhum link Awin contém URLs diretas das lojas (exceto no parâmetro UED)"""
        raw_store_domains = [
            "kabum.com.br",
            "comfy.com.br",
            "lg.com",
            "samsung.com",
            "trocafy.com.br",
            "ninja.com.br",
        ]

        for loja, url in self.TEST_URLS["awin"].items():
            deeplink = build_awin_deeplink(url, loja)

            # Verificar que NÃO contém domínios diretos das lojas na URL principal
            # (o domínio pode estar no parâmetro UED, que é correto)
            deeplink_base = deeplink.split("?")[
                0
            ]  # Apenas a parte base, sem parâmetros

            for domain in raw_store_domains:
                assert (
                    domain not in deeplink_base
                ), f"Deeplink Awin para {loja} contém domínio direto na URL base: {domain}"

            # Deve conter apenas awin1.com na URL base
            assert "awin1.com" in deeplink_base

            # O parâmetro UED deve conter a URL original (isso é correto)
            assert "ued=" in deeplink

    def test_awin_parameter_validation(self):
        """Testa se parâmetros Awin estão corretos"""
        for loja, url in self.TEST_URLS["awin"].items():
            deeplink = build_awin_deeplink(url, loja)

            # Parsear parâmetros
            from urllib.parse import parse_qs, urlparse

            parsed = urlparse(deeplink)
            query_params = parse_qs(parsed.query)

            # Verificar parâmetros obrigatórios
            assert "awinmid" in query_params
            assert "awinaffid" in query_params
            assert "ued" in query_params

            # Verificar se UED contém a URL original
            ued_value = query_params["ued"][0]
            from urllib.parse import unquote

            decoded_url = unquote(ued_value)
            assert decoded_url == url

    def test_shopee_cache_functionality(self):
        """Testa se o cache Shopee funciona corretamente"""
        url = self.TEST_URLS["shopee"]

        # Primeira chamada - deve gerar novo shortlink
        shortlink1 = build_shopee_short(url)

        # Segunda chamada - deve retornar do cache
        shortlink2 = build_shopee_short(url)

        # Deve ser idêntico (cache funcionando)
        assert shortlink1 == shortlink2

    def test_aliexpress_tracking_config(self):
        """Testa se AliExpress mantém configuração de tracking"""
        from src.affiliate.aliexpress import aliexpress_builder

        tracking_info = aliexpress_builder.get_tracking_info()

        assert tracking_info["tracking_id"] == "telegram"
        assert tracking_info["ship_to"] == "Brazil"
        assert "s.click.aliexpress.com/e" in tracking_info["base_url"]

    def test_affiliate_url_idempotency(self):
        """Testa se URLs de afiliado são idempotentes"""
        # Awin
        for loja, url in self.TEST_URLS["awin"].items():
            deeplink1 = build_awin_deeplink(url, loja)
            deeplink2 = build_awin_deeplink(url, loja)
            assert deeplink1 == deeplink2

        # Shopee
        url_shopee = self.TEST_URLS["shopee"]
        shortlink1 = build_shopee_short(url_shopee)
        shortlink2 = build_shopee_short(url_shopee)
        assert shortlink1 == shortlink2

        # AliExpress
        url_aliexpress = self.TEST_URLS["aliexpress"]
        shortlink1 = build_aliexpress_short(url_aliexpress)
        shortlink2 = build_aliexpress_short(url_aliexpress)
        assert shortlink1 == shortlink2

    def test_invalid_urls_rejected(self):
        """Testa se URLs inválidas são rejeitadas ou retornam fallback"""
        invalid_urls = ["url-invalida", "http://", "https://", "", None]

        # Shopee
        for invalid_url in invalid_urls:
            if invalid_url is None:
                # None deve retornar None como fallback (capturado pela validação)
                result = build_shopee_short(invalid_url)  # type: ignore
                assert result is None
            else:
                # URLs inválidas devem retornar a URL original como fallback
                result = build_shopee_short(invalid_url)
                assert result == invalid_url

        # AliExpress
        for invalid_url in invalid_urls:
            if invalid_url is None:
                # None deve retornar None como fallback (capturado pela validação)
                result = build_aliexpress_short(invalid_url)  # type: ignore
                assert result is None
            else:
                # URLs inválidas devem retornar a URL original como fallback
                result = build_aliexpress_short(invalid_url)
                assert result == invalid_url

    def test_platform_specific_validation(self):
        """Testa se cada plataforma valida URLs específicas"""
        # Shopee - deve aceitar apenas URLs Shopee
        shopee_url = self.TEST_URLS["shopee"]
        non_shopee_url = "https://amazon.com.br/produto"

        # URL Shopee válida deve funcionar
        shortlink = build_shopee_short(shopee_url)
        assert shortlink.startswith("https://s.shopee.com.br/")

        # URL não-Shopee deve retornar a URL original como fallback
        result = build_shopee_short(non_shopee_url)
        assert result == non_shopee_url

        # AliExpress - deve aceitar apenas URLs AliExpress
        aliexpress_url = self.TEST_URLS["aliexpress"]
        non_aliexpress_url = "https://mercadolivre.com.br/produto"

        # URL AliExpress válida deve funcionar
        shortlink = build_aliexpress_short(aliexpress_url)
        assert shortlink.startswith("https://s.click.aliexpress.com/e/")

        # URL não-AliExpress deve retornar a URL original como fallback
        result = build_aliexpress_short(non_aliexpress_url)
        assert result == non_aliexpress_url


class TestAffiliateRegexComprehensive:
    """Testes abrangentes para regex de validação"""

    def test_all_regex_patterns_valid(self):
        """Testa se todos os regex de validação são válidos"""
        from src.tests.test_affiliate_guardrails import TestAffiliateGuardrails

        for platform, regex in TestAffiliateGuardrails.VALIDATION_REGEX.items():
            try:
                re.compile(regex)
            except re.error as e:
                pytest.fail(f"Regex inválido para {platform}: {regex} - Erro: {e}")

    def test_regex_covers_all_platforms(self):
        """Testa se todos os regex cobrem todas as plataformas"""
        from src.tests.test_affiliate_guardrails import TestAffiliateGuardrails

        expected_platforms = [
            "awin",
            "mercadolivre",
            "magalu",
            "amazon",
            "shopee",
            "aliexpress",
        ]

        for platform in expected_platforms:
            assert (
                platform in TestAffiliateGuardrails.VALIDATION_REGEX
            ), f"Plataforma {platform} não tem regex de validação"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
