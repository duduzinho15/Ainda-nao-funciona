"""
Testes para integração Rakuten com feature flag.
"""

from unittest.mock import patch

import pytest

from src.affiliate.rakuten import (
    FeatureDisabledError,
    RakutenAffiliateBuilder,
    RakutenClient,
    get_rakuten_client,
)


class TestRakutenFeatureFlag:
    """Testes para feature flag do Rakuten"""

    def test_rakuten_disabled_by_default(self):
        """Testa se Rakuten está desabilitado por padrão"""
        from src.core.settings import Settings

        # Por padrão, deve estar desabilitado
        assert Settings.RAKUTEN_ENABLED is False

    def test_rakuten_client_disabled_raises_error(self):
        """Testa se cliente Rakuten desabilitado gera erro"""
        # Mock para desabilitar Rakuten
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", False):
            with pytest.raises(FeatureDisabledError, match="Rakuten está desabilitado"):
                client = RakutenClient("token1", "token2")
                client.build_deeplink("https://exemplo.com")

    def test_rakuten_affiliate_builder_disabled_raises_error(self):
        """Testa se builder Rakuten desabilitado gera erro"""
        # Mock para desabilitar Rakuten
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", False):
            with pytest.raises(FeatureDisabledError, match="Rakuten está desabilitado"):
                builder = RakutenAffiliateBuilder("id1", "mid1")
                builder.build_deeplink("https://exemplo.com")

    def test_rakuten_build_link_disabled_raises_error(self):
        """Testa se função build_rakuten_link desabilitada gera erro"""
        from src.affiliate.rakuten import build_rakuten_link

        # Mock para desabilitar Rakuten
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", False):
            with pytest.raises(FeatureDisabledError, match="Rakuten está desabilitado"):
                build_rakuten_link("https://exemplo.com", "id1", "mid1")

    def test_rakuten_enabled_works_correctly(self):
        """Testa se Rakuten habilitado funciona corretamente"""
        # Mock para habilitar Rakuten
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", True):
            client = RakutenClient("webservice_token", "security_token")

            # Deve funcionar sem erro
            deeplink = client.build_deeplink("https://exemplo.com")

            # Verificar formato do deeplink
            assert deeplink.startswith("https://click.linksynergy.com/deeplink")
            assert "id=" in deeplink
            assert "mid=" in deeplink
            assert "murl=" in deeplink
            assert "u1=" in deeplink

    def test_rakuten_healthcheck_disabled(self):
        """Testa se healthcheck retorna False quando desabilitado"""
        # Mock para desabilitar Rakuten
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", False):
            client = RakutenClient("token1", "token2")
            assert client.healthcheck() is False

    def test_rakuten_healthcheck_enabled_no_tokens(self):
        """Testa se healthcheck retorna False quando habilitado mas sem tokens"""
        # Mock para habilitar Rakuten mas sem tokens
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", True):
            client = RakutenClient("", "")  # Tokens vazios
            assert client.healthcheck() is False

    def test_rakuten_healthcheck_enabled_with_tokens(self):
        """Testa se healthcheck funciona quando habilitado com tokens"""
        # Mock para habilitar Rakuten com tokens
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", True):
            client = RakutenClient("webservice_token", "security_token")

            # Mock para API acessível
            with patch.object(client, "_is_api_accessible", return_value=True):
                assert client.healthcheck() is True

    def test_rakuten_get_client_disabled(self):
        """Testa se get_rakuten_client retorna None quando desabilitado"""
        # Mock para desabilitar Rakuten
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", False):
            client = get_rakuten_client()
            assert client is None

    def test_rakuten_get_client_enabled_no_tokens(self):
        """Testa se get_rakuten_client retorna None quando sem tokens"""
        # Mock para habilitar Rakuten mas sem tokens
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", True):
            with patch("src.core.settings.Settings.RAKUTEN_WEBSERVICE_TOKEN", ""):
                with patch("src.core.settings.Settings.RAKUTEN_SECURITY_TOKEN", ""):
                    client = get_rakuten_client()
                    assert client is None

    def test_rakuten_get_client_enabled_with_tokens(self):
        """Testa se get_rakuten_client retorna cliente quando configurado"""
        # Mock para habilitar Rakuten com tokens
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", True):
            with patch(
                "src.core.settings.Settings.RAKUTEN_WEBSERVICE_TOKEN",
                "webservice_token",
            ):
                with patch(
                    "src.core.settings.Settings.RAKUTEN_SECURITY_TOKEN",
                    "security_token",
                ):
                    client = get_rakuten_client()
                    assert client is not None
                    assert isinstance(client, RakutenClient)
                    assert client.webservice_token == "webservice_token"
                    assert client.security_token == "security_token"


class TestRakutenClientFunctionality:
    """Testes para funcionalidade do cliente Rakuten"""

    def test_rakuten_client_config_info(self):
        """Testa se informações de configuração são retornadas corretamente"""
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", True):
            client = RakutenClient("webservice_token", "security_token", "sid123")

            config_info = client.get_config_info()

            assert config_info["enabled"] is True
            assert config_info["webservice_token_configured"] is True
            assert config_info["security_token_configured"] is True
            assert config_info["sid_configured"] is True
            assert "endpoints" in config_info

    def test_rakuten_client_url_validation(self):
        """Testa se validação de URL funciona corretamente"""
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", True):
            client = RakutenClient("token1", "token2")

            # URLs válidas
            assert client._is_valid_url("https://exemplo.com") is True
            assert client._is_valid_url("http://teste.com.br/produto") is True

            # URLs inválidas
            assert client._is_valid_url("url-invalida") is False
            assert client._is_valid_url("") is False
            assert client._is_valid_url(None) is False

    def test_rakuten_client_local_deeplink_generation(self):
        """Testa se geração de deeplink local funciona"""
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", True):
            client = RakutenClient("webservice_token", "security_token")

            url = "https://exemplo.com/produto"
            deeplink = client._build_local_deeplink(url, None, None)

            # Verificar formato
            assert deeplink.startswith("https://click.linksynergy.com/deeplink")
            assert "id=" in deeplink
            assert "mid=" in deeplink
            assert "murl=" in deeplink
            assert "u1=" in deeplink

            # Verificar se murl contém a URL original
            from urllib.parse import parse_qs, urlparse

            parsed = urlparse(deeplink)
            query_params = parse_qs(parsed.query)
            assert "murl" in query_params

    def test_rakuten_client_with_custom_ids(self):
        """Testa se cliente funciona com IDs customizados"""
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", True):
            client = RakutenClient("webservice_token", "security_token")

            url = "https://exemplo.com/produto"
            deeplink = client.build_deeplink(
                url, advertiser_id="custom_id", mid="custom_mid"
            )

            # Verificar se IDs customizados foram usados
            from urllib.parse import parse_qs, urlparse

            parsed = urlparse(deeplink)
            query_params = parse_qs(parsed.query)

            assert query_params["id"][0] == "custom_id"
            assert query_params["mid"][0] == "custom_mid"


class TestRakutenErrorHandling:
    """Testes para tratamento de erros do Rakuten"""

    def test_rakuten_invalid_url_raises_error(self):
        """Testa se URL inválida gera erro"""
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", True):
            client = RakutenClient("token1", "token2")

            with pytest.raises(ValueError, match="URL inválida"):
                client._build_local_deeplink("url-invalida", None, None)

    def test_rakuten_api_fallback_works(self):
        """Testa se fallback para API local funciona quando API real falha"""
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", True):
            client = RakutenClient("webservice_token", "security_token")

            # Mock para API não acessível
            with patch.object(client, "_is_api_accessible", return_value=False):
                deeplink = client.build_deeplink("https://exemplo.com")

                # Deve retornar deeplink local
                assert deeplink.startswith("https://click.linksynergy.com/deeplink")

    def test_rakuten_exception_fallback_works(self):
        """Testa se fallback funciona quando há exceção"""
        with patch("src.core.settings.Settings.RAKUTEN_ENABLED", True):
            client = RakutenClient("webservice_token", "security_token")

            # Mock para gerar exceção
            with patch.object(
                client, "_build_api_deeplink", side_effect=Exception("API Error")
            ):
                deeplink = client.build_deeplink("https://exemplo.com")

                # Deve retornar deeplink local mesmo com erro
                assert deeplink.startswith("https://click.linksynergy.com/deeplink")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
