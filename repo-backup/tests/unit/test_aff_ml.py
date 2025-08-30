"""
Testes unitários para validação de afiliados Mercado Livre.

Este módulo testa a validação de URLs e shortlinks do Mercado Livre
usando as fixtures reais fornecidas.
"""

from urllib.parse import parse_qs, urlparse

import pytest

from tests.data.affiliate_examples import MERCADO_LIVRE
from tests.helpers.asserts import assert_mercadolivre_shortlink
from tests.helpers.patterns import (
    ML_PRODUCT_PATTERN,
    ML_SHORTLINK_PATTERN,
    ML_SOCIAL_PATTERN,
    extract_mercadolivre_id,
    is_valid_mercadolivre_product,
)

PRODUCT_DOMAINS = ("www.mercadolivre.com.br", "produto.mercadolivre.com.br")


def is_ml_product(url: str) -> bool:
    return any(d in url for d in PRODUCT_DOMAINS) and (
        "/p/MLB" in url or "/MLB-" in url
    )


def is_ml_short(url: str) -> bool:
    return url.startswith("https://mercadolivre.com/sec/")


def is_ml_social(url: str) -> bool:
    return "mercadolivre.com.br/social/garimpeirogeek" in url


def test_ml_product_variants():
    assert is_ml_product(MERCADO_LIVRE["produto_1"])
    assert is_ml_product(MERCADO_LIVRE["produto_2"])
    assert is_ml_product(MERCADO_LIVRE["produto_3"])


def test_ml_shortlinks_validos():
    assert is_ml_short(MERCADO_LIVRE["short_1"])
    assert is_ml_short(MERCADO_LIVRE["short_2"])
    assert is_ml_short(MERCADO_LIVRE["short_3"])


def test_ml_social_page_valida():
    assert is_ml_social(MERCADO_LIVRE["social_1"])
    assert is_ml_social(MERCADO_LIVRE["social_2"])
    assert is_ml_social(MERCADO_LIVRE["social_3"])


class TestMercadoLivreProductValidation:
    """Testa a validação de URLs de produtos do Mercado Livre."""

    @pytest.mark.parametrize(
        "test_case,url",
        [
            ("produto_1", MERCADO_LIVRE["produto_1"]),
            ("produto_2", MERCADO_LIVRE["produto_2"]),
            ("produto_3", MERCADO_LIVRE["produto_3"]),
        ],
    )
    def test_ml_product_url_structure(self, test_case: str, url: str):
        """Testa se as URLs de produtos têm estrutura válida."""
        # Verificar se é uma URL válida
        assert url.startswith("http"), f"URL inválida para {test_case}"

        # Verificar se é um produto válido
        assert is_valid_mercadolivre_product(
            url
        ), f"URL de produto inválida para {test_case}"

        # Verificar se corresponde ao padrão esperado
        assert ML_PRODUCT_PATTERN.match(
            url
        ), f"URL não corresponde ao padrão para {test_case}"

        # Verificar domínio
        parsed = urlparse(url)
        assert parsed.netloc in [
            "www.mercadolivre.com.br",
            "produto.mercadolivre.com.br",
        ], f"Domínio inválido para {test_case}: {parsed.netloc}"

    @pytest.mark.parametrize(
        "test_case,url",
        [
            ("produto_1", MERCADO_LIVRE["produto_1"]),
            ("produto_2", MERCADO_LIVRE["produto_2"]),
            ("produto_3", MERCADO_LIVRE["produto_3"]),
        ],
    )
    def test_ml_product_id_extraction(self, test_case: str, url: str):
        """Testa se o ID do produto é extraído corretamente."""
        product_id = extract_mercadolivre_id(url)

        assert product_id is not None, f"ID do produto não extraído para {test_case}"
        assert product_id.startswith(
            "MLB"
        ), f"ID do produto não começa com MLB para {test_case}: {product_id}"
        assert (
            len(product_id) > 3
        ), f"ID do produto muito curto para {test_case}: {product_id}"

        # Verificar se o ID está na URL
        assert product_id in url, f"ID extraído não encontrado na URL para {test_case}"

    @pytest.mark.parametrize(
        "test_case,url",
        [
            ("produto_1", MERCADO_LIVRE["produto_1"]),
            ("produto_2", MERCADO_LIVRE["produto_2"]),
            ("produto_3", MERCADO_LIVRE["produto_3"]),
        ],
    )
    def test_ml_product_query_parameters(self, test_case: str, url: str):
        """Testa se as URLs de produtos têm parâmetros válidos."""
        parsed = urlparse(url)

        # Verificar se tem fragmento (após #)
        assert "#" in url, f"URL sem fragmento para {test_case}"

        # Verificar se tem parâmetros de query
        assert "?" in url, f"URL sem parâmetros de query para {test_case}"

        # Verificar se tem parâmetros específicos
        query_params = parse_qs(parsed.query)

        # Verificar se tem parâmetros de tracking
        tracking_params = ["tracking_id", "wid", "sid"]
        has_tracking = any(param in query_params for param in tracking_params)
        assert has_tracking, f"URL sem parâmetros de tracking para {test_case}"

    def test_ml_product_urls_uniqueness(self):
        """Testa se as URLs de produtos são únicas."""
        product_urls = [
            MERCADO_LIVRE["produto_1"],
            MERCADO_LIVRE["produto_2"],
            MERCADO_LIVRE["produto_3"],
        ]

        # Verificar se não há duplicatas
        assert len(product_urls) == len(
            set(product_urls)
        ), "URLs de produtos duplicadas encontradas"

        # Verificar se cada URL é única
        for i, url1 in enumerate(product_urls):
            for j, url2 in enumerate(product_urls):
                if i != j:
                    assert url1 != url2, f"URLs idênticas: {url1} e {url2}"


class TestMercadoLivreShortlinkValidation:
    """Testa a validação de shortlinks do Mercado Livre."""

    @pytest.mark.parametrize(
        "test_case,url",
        [
            ("short_1", MERCADO_LIVRE["short_1"]),
            ("short_2", MERCADO_LIVRE["short_2"]),
            ("short_3", MERCADO_LIVRE["short_3"]),
        ],
    )
    def test_ml_shortlink_structure(self, test_case: str, url: str):
        """Testa se os shortlinks têm estrutura válida."""
        # Verificar se é um shortlink válido
        assert_mercadolivre_shortlink(url)

        # Verificar se corresponde ao padrão esperado
        assert ML_SHORTLINK_PATTERN.match(
            url
        ), f"Shortlink não corresponde ao padrão para {test_case}"

        # Verificar domínio
        parsed = urlparse(url)
        assert (
            parsed.netloc == "mercadolivre.com"
        ), f"Domínio incorreto para shortlink {test_case}: {parsed.netloc}"

        # Verificar path /sec/{token}
        assert parsed.path.startswith(
            "/sec/"
        ), f"Path incorreto para shortlink {test_case}: {parsed.path}"

        # Verificar se tem token
        token = parsed.path.split("/")[2]
        assert len(token) > 0, f"Token do shortlink vazio para {test_case}"
        assert token.isalnum(), f"Token do shortlink inválido para {test_case}: {token}"

    def test_ml_shortlink_uniqueness(self):
        """Testa se os shortlinks são únicos."""
        shortlinks = [
            MERCADO_LIVRE["short_1"],
            MERCADO_LIVRE["short_2"],
            MERCADO_LIVRE["short_3"],
        ]

        # Verificar se não há duplicatas
        assert len(shortlinks) == len(
            set(shortlinks)
        ), "Shortlinks duplicados encontrados"

        # Verificar se cada shortlink é único
        for i, shortlink1 in enumerate(shortlinks):
            for j, shortlink2 in enumerate(shortlinks):
                if i != j:
                    assert (
                        shortlink1 != shortlink2
                    ), f"Shortlinks idênticos: {shortlink1} e {shortlink2}"

    def test_ml_shortlink_format_consistency(self):
        """Testa se todos os shortlinks seguem o mesmo formato."""
        shortlinks = [
            MERCADO_LIVRE["short_1"],
            MERCADO_LIVRE["short_2"],
            MERCADO_LIVRE["short_3"],
        ]

        for shortlink in shortlinks:
            # Verificar formato consistente
            assert shortlink.startswith(
                "https://mercadolivre.com/sec/"
            ), f"Formato inconsistente: {shortlink}"

            # Verificar se não tem parâmetros extras
            parsed = urlparse(shortlink)
            assert not parsed.query, f"Shortlink com parâmetros extras: {shortlink}"
            assert not parsed.fragment, f"Shortlink com fragmento: {shortlink}"


class TestMercadoLivreSocialValidation:
    """Testa a validação de URLs sociais do Mercado Livre."""

    @pytest.mark.parametrize(
        "test_case,url",
        [
            ("social_1", MERCADO_LIVRE["social_1"]),
            ("social_2", MERCADO_LIVRE["social_2"]),
            ("social_3", MERCADO_LIVRE["social_3"]),
        ],
    )
    def test_ml_social_url_structure(self, test_case: str, url: str):
        """Testa se as URLs sociais têm estrutura válida."""
        # Verificar se é uma URL válida
        assert url.startswith("http"), f"URL inválida para {test_case}"

        # Verificar se corresponde ao padrão esperado
        assert ML_SOCIAL_PATTERN.match(
            url
        ), f"URL social não corresponde ao padrão para {test_case}"

        # Verificar domínio
        parsed = urlparse(url)
        assert (
            parsed.netloc == "www.mercadolivre.com.br"
        ), f"Domínio incorreto para {test_case}: {parsed.netloc}"

        # Verificar path
        assert (
            parsed.path == "/social/garimpeirogeek"
        ), f"Path incorreto para {test_case}: {parsed.path}"

    @pytest.mark.parametrize(
        "test_case,url",
        [
            ("social_1", MERCADO_LIVRE["social_1"]),
            ("social_2", MERCADO_LIVRE["social_2"]),
            ("social_3", MERCADO_LIVRE["social_3"]),
        ],
    )
    def test_ml_social_query_parameters(self, test_case: str, url: str):
        """Testa se as URLs sociais têm parâmetros obrigatórios."""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        # Verificar parâmetros obrigatórios
        required_params = ["matt_word", "matt_tool", "forceInApp", "ref"]

        for param in required_params:
            assert (
                param in query_params
            ), f"Parâmetro obrigatório ausente para {test_case}: {param}"

        # Verificar valores específicos
        assert (
            query_params["matt_word"][0] == "garimpeirogeek"
        ), f"matt_word incorreto para {test_case}"
        assert (
            query_params["matt_tool"][0] == "82173227"
        ), f"matt_tool incorreto para {test_case}"
        assert (
            query_params["forceInApp"][0] == "true"
        ), f"forceInApp incorreto para {test_case}"

        # Verificar se ref é um token válido
        ref_token = query_params["ref"][0]
        assert len(ref_token) > 0, f"Token ref vazio para {test_case}"
        assert (
            ref_token.isalnum()
            or "+" in ref_token
            or "/" in ref_token
            or "=" in ref_token
        ), f"Token ref inválido para {test_case}: {ref_token}"

    def test_ml_social_urls_uniqueness(self):
        """Testa se as URLs sociais são únicas."""
        social_urls = [
            MERCADO_LIVRE["social_1"],
            MERCADO_LIVRE["social_2"],
            MERCADO_LIVRE["social_3"],
        ]

        # Verificar se não há duplicatas
        assert len(social_urls) == len(
            set(social_urls)
        ), "URLs sociais duplicadas encontradas"

        # Verificar se cada URL é única
        for i, url1 in enumerate(social_urls):
            for j, url2 in enumerate(social_urls):
                if i != j:
                    assert url1 != url2, f"URLs sociais idênticas: {url1} e {url2}"


class TestMercadoLivreInvalidCases:
    """Testa casos inválidos para Mercado Livre."""

    def test_invalid_domain_rejection(self):
        """Testa se domínios inválidos são rejeitados."""
        invalid_url = "https://www.mercadolivre.com/invalid/path"

        parsed = urlparse(invalid_url)
        domain = parsed.netloc

        # Verificar se o domínio não é válido
        valid_domains = [
            "www.mercadolivre.com.br",
            "produto.mercadolivre.com.br",
            "mercadolivre.com",
        ]
        assert domain not in valid_domains, f"Domínio inválido foi aceito: {domain}"

    def test_invalid_path_rejection(self):
        """Testa se paths inválidos são rejeitados."""
        invalid_paths = [
            "https://www.mercadolivre.com.br/invalid/path",
            "https://www.mercadolivre.com.br/categoria/123",
            "https://www.mercadolivre.com.br/busca?q=teste",
        ]

        for url in invalid_paths:
            assert not is_valid_mercadolivre_product(
                url
            ), f"Path inválido foi aceito: {url}"

    def test_malformed_shortlink_rejection(self):
        """Testa se shortlinks malformados são rejeitados."""
        malformed_shortlinks = [
            "https://mercadolivre.com/sec/",
            "https://mercadolivre.com/sec",
            "https://mercadolivre.com/sec/invalid/path",
            "https://mercadolivre.com/sec/123?param=value",
        ]

        for url in malformed_shortlinks:
            assert not ML_SHORTLINK_PATTERN.match(
                url
            ), f"Shortlink malformado foi aceito: {url}"

    def test_malformed_social_rejection(self):
        """Testa se URLs sociais malformadas são rejeitadas."""
        malformed_social = [
            "https://www.mercadolivre.com.br/social/outro_usuario",
            "https://www.mercadolivre.com.br/social/garimpeirogeek",
            "https://www.mercadolivre.com.br/social/garimpeirogeek?param=value",
        ]

        for url in malformed_social:
            assert not ML_SOCIAL_PATTERN.match(
                url
            ), f"URL social malformada foi aceita: {url}"


class TestMercadoLivreIntegration:
    """Testa a integração entre diferentes tipos de URLs do Mercado Livre."""

    def test_ml_url_types_consistency(self):
        """Testa se os diferentes tipos de URL são consistentes."""
        # Verificar se todos os tipos de URL estão presentes
        assert "produto_1" in MERCADO_LIVRE, "Produto 1 ausente"
        assert "short_1" in MERCADO_LIVRE, "Shortlink 1 ausente"
        assert "social_1" in MERCADO_LIVRE, "URL social 1 ausente"

        # Verificar se são URLs válidas
        for key, url in MERCADO_LIVRE.items():
            assert url.startswith("http"), f"URL inválida para {key}: {url}"

            # Verificar se o domínio é consistente com o tipo
            parsed = urlparse(url)
            if "short" in key:
                assert (
                    parsed.netloc == "mercadolivre.com"
                ), f"Domínio incorreto para shortlink {key}"
            elif "social" in key:
                assert (
                    parsed.netloc == "www.mercadolivre.com.br"
                ), f"Domínio incorreto para social {key}"
            else:
                assert parsed.netloc in [
                    "www.mercadolivre.com.br",
                    "produto.mercadolivre.com.br",
                ], f"Domínio incorreto para produto {key}"

    def test_ml_etiqueta_consistency(self):
        """Testa se a etiqueta garimpeirogeek é consistente em todas as URLs sociais."""
        social_urls = [
            MERCADO_LIVRE["social_1"],
            MERCADO_LIVRE["social_2"],
            MERCADO_LIVRE["social_3"],
        ]

        for url in social_urls:
            assert (
                "garimpeirogeek" in url
            ), f"Etiqueta garimpeirogeek não encontrada em: {url}"
            assert (
                "matt_word=garimpeirogeek" in url
            ), f"Parâmetro matt_word incorreto em: {url}"
