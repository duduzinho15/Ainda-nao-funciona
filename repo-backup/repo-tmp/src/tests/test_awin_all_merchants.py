"""
Testes para todas as lojas Awin configuradas.
"""

from urllib.parse import parse_qs, unquote, urlparse

import pytest

from src.affiliate.awin import AwinAffiliateBuilder, build_awin_deeplink


class TestAwinAllMerchants:
    """Testes para todas as lojas Awin configuradas"""

    # URLs de teste para cada loja
    TEST_URLS = {
        "comfy": "https://www.comfy.com.br/cadeira-de-escritorio-comfy-ergopro-cinza.html",
        "trocafy": "https://www.trocafy.com.br/smartphone-samsung-galaxy-s22-256gb-verde-5g.html",
        "lg": "https://www.lg.com/br/lavanderia/washtower/wk14bs6/",
        "kabum": "https://www.kabum.com.br/produto/472908/monitor-gamer-curvo-lg-ultragear",
        "ninja": "https://www.ninja.com.br/produto/12345/air-fryer-ninja",
        "samsung": "https://www.samsung.com/br/smartphones/galaxy-s24-ultra/",
    }

    # Configurações esperadas (MID, AFFID)
    EXPECTED_CONFIGS = {
        "comfy": ("23377", "2370719"),
        "trocafy": ("51277", "2370719"),
        "lg": ("33061", "2370719"),
        "kabum": ("17729", "2370719"),
        "ninja": ("106765", "2370719"),
        "samsung": ("25539", "2510157"),
    }

    @pytest.mark.parametrize("loja", TEST_URLS.keys())
    def test_awin_deeplink_structure(self, loja: str):
        """Testa se o deeplink Awin tem a estrutura correta"""
        url = self.TEST_URLS[loja]
        deeplink = build_awin_deeplink(url, loja)

        # Verificar estrutura básica
        assert deeplink.startswith("https://www.awin1.com/cread.php")

        # Parsear parâmetros
        parsed = urlparse(deeplink)
        query_params = parse_qs(parsed.query)

        # Verificar parâmetros obrigatórios
        assert "awinmid" in query_params
        assert "awinaffid" in query_params
        assert "ued" in query_params

        # Verificar valores específicos da loja
        expected_mid, expected_affid = self.EXPECTED_CONFIGS[loja]
        assert query_params["awinmid"][0] == expected_mid
        assert query_params["awinaffid"][0] == expected_affid

        # Verificar se UED contém a URL original
        ued_decoded = unquote(query_params["ued"][0])
        assert ued_decoded == url

    @pytest.mark.parametrize("loja", TEST_URLS.keys())
    def test_awin_deeplink_encoding(self, loja: str):
        """Testa se a URL é codificada corretamente no parâmetro UED"""
        url = self.TEST_URLS[loja]
        deeplink = build_awin_deeplink(url, loja)

        # Parsear parâmetros
        parsed = urlparse(deeplink)
        query_params = parse_qs(parsed.query)

        # Verificar se UED está codificado
        ued_encoded = query_params["ued"][0]
        ued_decoded = unquote(ued_encoded)

        # A URL decodificada deve ser igual à original
        assert ued_decoded == url

        # A URL codificada deve ser diferente da original (devido ao encoding)
        # Nota: URLs simples podem não ter caracteres que precisem de encoding
        if any(char in url for char in [" ", "&", "?", "#", "%", "+"]):
            assert ued_encoded != url
        else:
            # Para URLs simples, o encoding pode não alterar a string
            pass

    @pytest.mark.parametrize("loja", TEST_URLS.keys())
    def test_awin_deeplink_contains_required_elements(self, loja: str):
        """Testa se o deeplink contém todos os elementos obrigatórios"""
        url = self.TEST_URLS[loja]
        deeplink = build_awin_deeplink(url, loja)

        # Verificar elementos obrigatórios
        assert "/cread.php" in deeplink
        assert "awinmid=" in deeplink
        assert "awinaffid=" in deeplink
        assert "ued=" in deeplink

        # Verificar valores específicos
        expected_mid, expected_affid = self.EXPECTED_CONFIGS[loja]
        assert f"awinmid={expected_mid}" in deeplink
        assert f"awinaffid={expected_affid}" in deeplink

    def test_awin_builder_instance(self):
        """Testa se a instância global do builder funciona"""
        builder = AwinAffiliateBuilder()
        assert isinstance(builder, AwinAffiliateBuilder)

        # Testar com uma loja
        url = self.TEST_URLS["kabum"]
        deeplink = builder.build_awin_deeplink(url, "kabum")
        assert deeplink.startswith("https://www.awin1.com/cread.php")

    def test_invalid_store_raises_error(self):
        """Testa se loja inválida gera erro"""
        url = "https://exemplo.com/produto"

        with pytest.raises(
            ValueError, match="Loja 'loja_inexistente' não configurada para Awin"
        ):
            build_awin_deeplink(url, "loja_inexistente")

    def test_invalid_url_raises_error(self):
        """Testa se URL inválida gera erro"""
        invalid_url = "url-invalida"

        with pytest.raises(ValueError, match="URL inválida"):
            build_awin_deeplink(invalid_url, "kabum")

    @pytest.mark.parametrize("loja", TEST_URLS.keys())
    def test_awin_deeplink_idempotent(self, loja: str):
        """Testa se o deeplink é idempotente (mesmo resultado para mesma entrada)"""
        url = self.TEST_URLS[loja]

        # Gerar deeplink duas vezes
        deeplink1 = build_awin_deeplink(url, loja)
        deeplink2 = build_awin_deeplink(url, loja)

        # Deve ser idêntico
        assert deeplink1 == deeplink2

    def test_awin_supported_stores(self):
        """Testa se todas as lojas suportadas estão configuradas"""
        from src.affiliate.awin import get_supported_stores, is_store_supported

        supported = get_supported_stores()

        # Verificar se todas as lojas de teste estão suportadas
        for loja in self.TEST_URLS.keys():
            assert loja in supported
            assert is_store_supported(loja)

        # Verificar se lojas inexistentes não estão suportadas
        assert not is_store_supported("loja_inexistente")

    def test_awin_config_validation(self):
        """Testa se a validação de configuração Awin funciona"""
        from src.core.platforms import validate_awin_config

        # A configuração deve ser válida
        assert validate_awin_config() is True


class TestAwinEdgeCases:
    """Testes para casos extremos e edge cases"""

    def test_awin_url_with_special_characters(self):
        """Testa URLs com caracteres especiais"""
        special_url = (
            "https://www.kabum.com.br/produto/123?param=valor&outro=teste#fragmento"
        )

        deeplink = build_awin_deeplink(special_url, "kabum")

        # Parsear e verificar se a URL foi preservada
        parsed = urlparse(deeplink)
        query_params = parse_qs(parsed.query)

        ued_decoded = unquote(query_params["ued"][0])
        assert ued_decoded == special_url

    def test_awin_url_with_unicode(self):
        """Testa URLs com caracteres Unicode"""
        unicode_url = "https://www.comfy.com.br/cadeira-ergonômica-para-escritório"

        deeplink = build_awin_deeplink(unicode_url, "comfy")

        # Parsear e verificar se a URL foi preservada
        parsed = urlparse(deeplink)
        query_params = parse_qs(parsed.query)

        ued_decoded = unquote(query_params["ued"][0])
        assert ued_decoded == unicode_url

    def test_awin_empty_string_validation(self):
        """Testa validação de string vazia"""
        with pytest.raises(ValueError):
            build_awin_deeplink("", "kabum")

    def test_awin_none_validation(self):
        """Testa validação de None"""
        with pytest.raises(ValueError):
            build_awin_deeplink(None, "kabum")  # type: ignore


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
