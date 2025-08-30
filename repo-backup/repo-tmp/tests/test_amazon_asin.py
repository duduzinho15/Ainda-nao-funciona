"""
Testes para o módulo de normalização Amazon ASIN.

Cobre extração de ASIN de URLs, HTML, conversão para URLs de afiliado
e canonização de URLs da Amazon.
"""

import pytest

from src.affiliate.amazon import (
    ASIN_REGEX,
    canonicalize_amazon,
    extract_asin_from_html,
    extract_asin_from_url,
    get_amazon_domain_from_url,
    is_valid_amazon_url,
    to_affiliate_url,
)


class TestAsinExtractionFromUrl:
    """Testa extração de ASIN de diferentes formatos de URL da Amazon."""

    def test_extract_asin_dp_format(self):
        """Testa extração de ASIN do formato /dp/ASIN."""
        url = "https://www.amazon.com.br/dp/B08N5WRWNW"
        asin = extract_asin_from_url(url)
        assert asin == "B08N5WRWNW"

    def test_extract_asin_gp_product_format(self):
        """Testa extração de ASIN do formato /gp/product/ASIN."""
        url = "https://www.amazon.com/gp/product/B08N5WRWNW"
        asin = extract_asin_from_url(url)
        assert asin == "B08N5WRWNW"

    def test_extract_asin_gp_aw_d_format(self):
        """Testa extração de ASIN do formato /gp/aw/d/ASIN (mobile)."""
        url = "https://www.amazon.com/gp/aw/d/B08N5WRWNW"
        asin = extract_asin_from_url(url)
        assert asin == "B08N5WRWNW"

    def test_extract_asin_query_param(self):
        """Testa extração de ASIN do parâmetro ?asin=ASIN."""
        url = "https://www.amazon.com.br/product?asin=B08N5WRWNW&ref=test"
        asin = extract_asin_from_url(url)
        assert asin == "B08N5WRWNW"

    def test_extract_asin_case_insensitive(self):
        """Testa que ASINs são extraídos independente de maiúsculas/minúsculas."""
        url = "https://www.amazon.com.br/dp/b08n5wrwnw"
        asin = extract_asin_from_url(url)
        assert asin == "B08N5WRWNW"  # Sempre retorna em maiúsculas

    def test_extract_asin_with_extra_path(self):
        """Testa extração de ASIN com caminhos adicionais na URL."""
        url = "https://www.amazon.com.br/dp/B08N5WRWNW/ref=sr_1_1?keywords=test"
        asin = extract_asin_from_url(url)
        assert asin == "B08N5WRWNW"

    def test_extract_asin_multiple_domains(self):
        """Testa extração de ASIN de diferentes domínios Amazon."""
        urls = [
            "https://www.amazon.com/dp/B08N5WRWNW",
            "https://amazon.ca/dp/B08N5WRWNW",
            "https://amazon.co.uk/dp/B08N5WRWNW",
            "https://amazon.de/dp/B08N5WRWNW",
        ]

        for url in urls:
            asin = extract_asin_from_url(url)
            assert asin == "B08N5WRWNW"

    def test_extract_asin_not_found(self):
        """Testa que None é retornado quando ASIN não é encontrado."""
        url = "https://www.amazon.com.br/product/12345"
        asin = extract_asin_from_url(url)
        assert asin is None

    def test_extract_asin_invalid_url(self):
        """Testa que None é retornado para URLs inválidas."""
        url = "not-a-valid-url"
        asin = extract_asin_from_url(url)
        assert asin is None

    def test_extract_asin_non_amazon_domain(self):
        """Testa que None é retornado para domínios não-Amazon."""
        url = "https://www.otherstore.com/dp/B08N5WRWNW"
        # Primeiro verificar se é URL da Amazon
        from src.utils.url_utils import is_amazon_url

        assert not is_amazon_url(url)

        # Se não for Amazon, não deve extrair ASIN
        asin = extract_asin_from_url(url)
        assert asin is None


class TestAsinExtractionFromHtml:
    """Testa extração de ASIN de conteúdo HTML."""

    def test_extract_asin_from_input_id(self):
        """Testa extração de ASIN de input com id='ASIN'."""
        html = '<input id="ASIN" value="B08N5WRWNW">'
        asin = extract_asin_from_html(html)
        assert asin == "B08N5WRWNW"

    def test_extract_asin_from_input_name(self):
        """Testa extração de ASIN de input com name='ASIN'."""
        html = '<input name="ASIN" value="B08N5WRWNW">'
        asin = extract_asin_from_html(html)
        assert asin == "B08N5WRWNW"

    def test_extract_asin_from_data_asin(self):
        """Testa extração de ASIN de data-asin."""
        html = '<div data-asin="B08N5WRWNW">Product</div>'
        asin = extract_asin_from_html(html)
        assert asin == "B08N5WRWNW"

    def test_extract_asin_from_og_url(self):
        """Testa extração de ASIN de meta og:url."""
        html = '<meta property="og:url" content="https://amazon.com/dp/B08N5WRWNW">'
        asin = extract_asin_from_html(html)
        assert asin == "B08N5WRWNW"

    def test_extract_asin_from_json_ld(self):
        """Testa extração de ASIN de JSON-LD."""
        html = """
        <script type="application/ld+json">
        {"@type": "Product", "asin": "B08N5WRWNW"}
        </script>
        """
        asin = extract_asin_from_html(html)
        assert asin == "B08N5WRWNW"

    def test_extract_asin_case_insensitive_html(self):
        """Testa que ASINs são extraídos independente de maiúsculas/minúsculas no HTML."""
        html = '<input id="asin" value="b08n5wrwnw">'
        asin = extract_asin_from_html(html)
        assert asin == "B08N5WRWNW"

    def test_extract_asin_not_found_html(self):
        """Testa que None é retornado quando ASIN não é encontrado no HTML."""
        html = "<div>No ASIN here</div>"
        asin = extract_asin_from_html(html)
        assert asin is None

    def test_extract_asin_empty_html(self):
        """Testa que None é retornado para HTML vazio."""
        asin = extract_asin_from_html("")
        assert asin is None

    def test_extract_asin_none_html(self):
        """Testa que None é retornado para HTML None."""
        asin = extract_asin_from_html(None)
        assert asin is None


class TestAffiliateUrlGeneration:
    """Testa geração de URLs de afiliado."""

    def test_to_affiliate_url_default(self):
        """Testa geração de URL de afiliado com valores padrão."""
        asin = "B08N5WRWNW"
        url = to_affiliate_url(asin)
        expected = "https://www.amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogee-20&language=pt_BR"
        assert url == expected

    def test_to_affiliate_url_custom_domain(self):
        """Testa geração de URL de afiliado com domínio customizado."""
        asin = "B08N5WRWNW"
        url = to_affiliate_url(asin, domain="com")
        expected = (
            "https://www.amazon.com/dp/B08N5WRWNW?tag=garimpeirogee-20&language=pt_BR"
        )
        assert url == expected

    def test_to_affiliate_url_custom_tag(self):
        """Testa geração de URL de afiliado com tag customizada."""
        asin = "B08N5WRWNW"
        url = to_affiliate_url(asin, tag="my-tag-20")
        expected = (
            "https://www.amazon.com.br/dp/B08N5WRWNW?tag=my-tag-20&language=pt_BR"
        )
        assert url == expected

    def test_to_affiliate_url_custom_language(self):
        """Testa geração de URL de afiliado com idioma customizado."""
        asin = "B08N5WRWNW"
        url = to_affiliate_url(asin, language="en_US")
        expected = "https://www.amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogee-20&language=en_US"
        assert url == expected

    def test_to_affiliate_url_invalid_asin(self):
        """Testa que ValueError é levantado para ASIN inválido."""
        with pytest.raises(ValueError, match="ASIN é obrigatório"):
            to_affiliate_url("")

    def test_to_affiliate_url_none_asin(self):
        """Testa que ValueError é levantado para ASIN None."""
        with pytest.raises(ValueError, match="ASIN é obrigatório"):
            to_affiliate_url(None)


class TestCanonicalization:
    """Testa canonização de URLs da Amazon."""

    def test_canonicalize_amazon_simple(self):
        """Testa canonização de URL simples da Amazon."""
        url = "https://amazon.com.br/dp/B08N5WRWNW"
        asin, canonical_url = canonicalize_amazon(url)

        assert asin == "B08N5WRWNW"
        assert (
            canonical_url
            == "https://www.amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogee-20&language=pt_BR"
        )

    def test_canonicalize_amazon_with_html(self):
        """Testa canonização usando HTML quando URL não contém ASIN."""
        url = "https://amazon.com.br/product/12345"
        html = '<input id="ASIN" value="B08N5WRWNW">'

        asin, canonical_url = canonicalize_amazon(url, html)

        assert asin == "B08N5WRWNW"
        assert (
            canonical_url
            == "https://www.amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogee-20&language=pt_BR"
        )

    def test_canonicalize_amazon_no_asin(self):
        """Testa que None é retornado quando ASIN não é encontrado."""
        url = "https://amazon.com.br/product/12345"
        html = "<div>No ASIN here</div>"

        asin, canonical_url = canonicalize_amazon(url, html)

        assert asin is None
        assert canonical_url is None

    def test_canonicalize_amazon_different_domain(self):
        """Testa canonização preservando domínio original."""
        url = "https://amazon.com/dp/B08N5WRWNW"
        asin, canonical_url = canonicalize_amazon(url)

        assert asin == "B08N5WRWNW"
        assert "amazon.com" in canonical_url
        assert "tag=garimpeirogee-20" in canonical_url

    def test_canonicalize_amazon_invalid_url(self):
        """Testa que None é retornado para URLs inválidas."""
        url = "not-a-valid-url"
        asin, canonical_url = canonicalize_amazon(url)

        assert asin is None
        assert canonical_url is None


class TestUrlValidation:
    """Testa validação de URLs da Amazon."""

    def test_is_valid_amazon_url_valid(self):
        """Testa que URLs válidas da Amazon retornam True."""
        valid_urls = [
            "https://www.amazon.com.br/dp/B08N5WRWNW",
            "https://amazon.com/gp/product/B08N5WRWNW",
            "https://amazon.co.uk/dp/B08N5WRWNW",
        ]

        for url in valid_urls:
            assert is_valid_amazon_url(url) is True

    def test_is_valid_amazon_url_invalid(self):
        """Testa que URLs inválidas retornam False."""
        invalid_urls = [
            "https://www.otherstore.com/dp/B08N5WRWNW",
            "not-a-url",
            "",
            None,
        ]

        for url in invalid_urls:
            assert is_valid_amazon_url(url) is False

    def test_get_amazon_domain_from_url(self):
        """Testa extração de domínio de URLs válidas."""
        test_cases = [
            ("https://www.amazon.com.br/dp/B08N5WRWNW", "com.br"),
            ("https://amazon.com/dp/B08N5WRWNW", "com"),
            ("https://amazon.co.uk/dp/B08N5WRWNW", "co.uk"),
        ]

        for url, expected_domain in test_cases:
            domain = get_amazon_domain_from_url(url)
            assert domain == expected_domain

    def test_get_amazon_domain_from_url_invalid(self):
        """Testa que domínio padrão é retornado para URLs inválidas."""
        invalid_urls = [
            "https://www.otherstore.com/dp/B08N5WRWNW",
            "not-a-url",
            "",
            None,
        ]

        for url in invalid_urls:
            domain = get_amazon_domain_from_url(url)
            assert domain == "com.br"  # Domínio padrão


class TestAsinRegex:
    """Testa o regex de validação de ASIN."""

    def test_asin_regex_valid(self):
        """Testa que ASINs válidos são aceitos pelo regex."""
        valid_asins = ["B08N5WRWNW", "B0ABCD1234", "B0XYZ98765"]

        for asin in valid_asins:
            assert ASIN_REGEX.match(asin) is not None

    def test_asin_regex_invalid(self):
        """Testa que ASINs inválidos são rejeitados pelo regex."""
        invalid_asins = [
            "A08N5WRWNW",  # Não começa com B0
            "B08N5WRWN",  # Muito curto
            "B08N5WRWNWX",  # Muito longo
            "B08N5WRWNW1",  # Termina com número
            "B08N5WRWNWA",  # Termina com letra
            "INVALID",
        ]

        for asin in invalid_asins:
            assert ASIN_REGEX.match(asin) is None


class TestAmazonDomains:
    """Testa a lista de domínios Amazon suportados."""

    def test_amazon_domains_comprehensive(self):
        """Testa que todos os domínios principais da Amazon estão incluídos."""
        expected_domains = {
            "com.br",  # Brasil
            "com",  # EUA
            "ca",  # Canadá
            "co.uk",  # Reino Unido
            "de",  # Alemanha
            "fr",  # França
            "it",  # Itália
            "es",  # Espanha
            "co.jp",  # Japão
            "in",  # Índia
            "com.au",  # Austrália
        }

        # Testar alguns domínios principais
        test_urls = [
            "https://www.amazon.com.br/dp/B08N5WRWNW",
            "https://amazon.com/dp/B08N5WRWNW",
            "https://amazon.co.uk/dp/B08N5WRWNW",
        ]

        for url in test_urls:
            domain = get_amazon_domain_from_url(url)
            assert domain in expected_domains

    def test_amazon_domains_format(self):
        """Testa que todos os domínios seguem o formato correto."""
        test_urls = [
            "https://www.amazon.com.br/dp/B08N5WRWNW",
            "https://amazon.com/dp/B08N5WRWNW",
            "https://amazon.co.uk/dp/B08N5WRWNW",
        ]

        for url in test_urls:
            domain = get_amazon_domain_from_url(url)
            # Domínios podem ter ponto (com.br, co.uk) ou não (com)
            assert len(domain) >= 2
            # Verificar se é um domínio válido
            assert domain in ["com.br", "com", "co.uk"]
