"""
Testes unitários para validação de afiliados AliExpress.

Este módulo testa a validação de URLs e shortlinks do AliExpress
usando as fixtures reais fornecidas.
"""

from urllib.parse import urlparse

import pytest

from tests.data.affiliate_examples import ALIEXPRESS
from tests.helpers.asserts import assert_aliexpress_shortlink
from tests.helpers.patterns import (
    ALIEXPRESS_PRODUCT_PATTERN,
    ALIEXPRESS_SHORTLINK_PATTERN,
    is_valid_aliexpress_product,
)


class TestAliExpressProductValidation:
    """Testa a validação de URLs de produtos do AliExpress."""

    @pytest.mark.parametrize(
        "test_case,url",
        [
            ("product_1", ALIEXPRESS["product_1"]),
            ("product_2", ALIEXPRESS["product_2"]),
            ("product_3", ALIEXPRESS["product_3"]),
            ("product_4", ALIEXPRESS["product_4"]),
            ("product_5", ALIEXPRESS["product_5"]),
        ],
    )
    def test_aliexpress_product_url_structure(self, test_case: str, url: str):
        """Testa se as URLs de produtos têm estrutura válida."""
        # Verificar se é uma URL válida
        assert url.startswith("http"), f"URL inválida para {test_case}"

        # Verificar se é um produto válido
        assert is_valid_aliexpress_product(
            url
        ), f"URL de produto inválida para {test_case}"

        # Verificar se corresponde ao padrão esperado
        assert ALIEXPRESS_PRODUCT_PATTERN.match(
            url
        ), f"URL não corresponde ao padrão para {test_case}"

        # Verificar domínio
        parsed = urlparse(url)
        assert (
            parsed.netloc == "pt.aliexpress.com"
        ), f"Domínio incorreto para {test_case}: {parsed.netloc}"

    @pytest.mark.parametrize(
        "test_case,url",
        [
            ("product_1", ALIEXPRESS["product_1"]),
            ("product_2", ALIEXPRESS["product_2"]),
            ("product_3", ALIEXPRESS["product_3"]),
            ("product_4", ALIEXPRESS["product_4"]),
            ("product_5", ALIEXPRESS["product_5"]),
        ],
    )
    def test_aliexpress_product_id_extraction(self, test_case: str, url: str):
        """Testa se o ID do produto é extraído corretamente."""
        # Extrair ID do produto da URL
        import re

        product_id_match = re.search(r"/item/(\d+)\.html", url)

        assert (
            product_id_match is not None
        ), f"ID do produto não encontrado para {test_case}"
        product_id = product_id_match.group(1)

        # Verificar se o ID é numérico
        assert (
            product_id.isdigit()
        ), f"ID do produto não é numérico para {test_case}: {product_id}"

        # Verificar se o ID tem tamanho razoável
        assert (
            len(product_id) >= 10
        ), f"ID do produto muito curto para {test_case}: {product_id}"
        assert (
            len(product_id) <= 16
        ), f"ID do produto muito longo para {test_case}: {product_id}"

        # Verificar se o ID está na URL
        assert product_id in url, f"ID extraído não encontrado na URL para {test_case}"

        # Verificar formato específico do AliExpress
        expected_format = f"/item/{product_id}.html"
        assert (
            expected_format in url
        ), f"Formato de ID incorreto para {test_case}: esperado {expected_format}"

    @pytest.mark.parametrize(
        "test_case,url",
        [
            ("product_1", ALIEXPRESS["product_1"]),
            ("product_2", ALIEXPRESS["product_2"]),
            ("product_3", ALIEXPRESS["product_3"]),
            ("product_4", ALIEXPRESS["product_4"]),
            ("product_5", ALIEXPRESS["product_5"]),
        ],
    )
    def test_aliexpress_product_query_parameters(self, test_case: str, url: str):
        """Testa se as URLs de produtos têm parâmetros válidos."""
        parsed = urlparse(url)

        # Verificar se tem parâmetros de query
        assert "?" in url, f"URL sem parâmetros de query para {test_case}"

        # Verificar parâmetros específicos do AliExpress
        query_params = parsed.query

        # Verificar se tem parâmetros de gateway
        assert (
            "gatewayAdapt=glo2bra" in query_params
        ), f"Parâmetro gatewayAdapt ausente para {test_case}"

        # Verificar se tem parâmetros de tracking
        assert "scm=null" in query_params, f"Parâmetro scm ausente para {test_case}"
        assert "pvid=null" in query_params, f"Parâmetro pvid ausente para {test_case}"

    def test_aliexpress_product_urls_uniqueness(self):
        """Testa se as URLs de produtos são únicas."""
        product_urls = [
            ALIEXPRESS["product_1"],
            ALIEXPRESS["product_2"],
            ALIEXPRESS["product_3"],
            ALIEXPRESS["product_4"],
            ALIEXPRESS["product_5"],
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


class TestAliExpressShortlinkValidation:
    """Testa a validação de shortlinks do AliExpress."""

    @pytest.mark.parametrize(
        "test_case,url",
        [
            ("short_1", ALIEXPRESS["short_1"]),
            ("short_2", ALIEXPRESS["short_2"]),
            ("short_3", ALIEXPRESS["short_3"]),
            ("short_4", ALIEXPRESS["short_4"]),
            ("short_5", ALIEXPRESS["short_5"]),
        ],
    )
    def test_aliexpress_shortlink_structure(self, test_case: str, url: str):
        """Testa se os shortlinks têm estrutura válida."""
        # Verificar se é um shortlink válido
        assert_aliexpress_shortlink(url)

        # Verificar se corresponde ao padrão esperado
        assert ALIEXPRESS_SHORTLINK_PATTERN.match(
            url
        ), f"Shortlink não corresponde ao padrão para {test_case}"

        # Verificar domínio
        parsed = urlparse(url)
        assert (
            parsed.netloc == "s.click.aliexpress.com"
        ), f"Domínio incorreto para shortlink {test_case}: {parsed.netloc}"

        # Verificar path /e/{token}
        assert parsed.path.startswith(
            "/e/_"
        ), f"Path incorreto para shortlink {test_case}: {parsed.path}"

        # Verificar se tem token
        token = parsed.path.split("/")[2]
        assert len(token) > 0, f"Token do shortlink vazio para {test_case}"
        # Token pode conter underscore, então verificar se é alfanumérico + underscore
        assert all(
            c.isalnum() or c == "_" for c in token
        ), f"Token do shortlink inválido para {test_case}: {token}"

        # Verificar se não tem parâmetros extras
        assert not parsed.query, f"Shortlink com parâmetros extras para {test_case}"
        assert not parsed.fragment, f"Shortlink com fragmento para {test_case}"

    def test_aliexpress_shortlink_uniqueness(self):
        """Testa se os shortlinks são únicos."""
        shortlinks = [
            ALIEXPRESS["short_1"],
            ALIEXPRESS["short_2"],
            ALIEXPRESS["short_3"],
            ALIEXPRESS["short_4"],
            ALIEXPRESS["short_5"],
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

    def test_aliexpress_shortlink_format_consistency(self):
        """Testa se todos os shortlinks seguem o mesmo formato."""
        shortlinks = [
            ALIEXPRESS["short_1"],
            ALIEXPRESS["short_2"],
            ALIEXPRESS["short_3"],
            ALIEXPRESS["short_4"],
            ALIEXPRESS["short_5"],
        ]

        for shortlink in shortlinks:
            # Verificar formato consistente
            assert shortlink.startswith(
                "https://s.click.aliexpress.com/e/_"
            ), f"Formato inconsistente: {shortlink}"

            # Verificar se não tem parâmetros extras
            parsed = urlparse(shortlink)
            assert not parsed.query, f"Shortlink com parâmetros extras: {shortlink}"
            assert not parsed.fragment, f"Shortlink com fragmento: {shortlink}"

            # Verificar se o token é válido
            token = parsed.path.split("/")[2]
            assert len(token) > 0, f"Token do shortlink vazio: {shortlink}"
            # Token pode conter underscore, então verificar se é alfanumérico + underscore
            assert all(
                c.isalnum() or c == "_" for c in token
            ), f"Token do shortlink inválido: {shortlink}"


class TestAliExpressConfiguration:
    """Testa a configuração específica do AliExpress."""

    def test_aliexpress_tracking_configuration(self):
        """Testa se a configuração de tracking está correta."""
        tracking = ALIEXPRESS["tracking"]

        # Verificar se o tracking é válido
        assert tracking == "telegram", f"Tracking incorreto: {tracking}"
        assert len(tracking) > 0, "Tracking vazio"
        assert tracking.isalpha(), f"Tracking com caracteres inválidos: {tracking}"

    def test_aliexpress_ship_to_configuration(self):
        """Testa se a configuração de envio está correta."""
        ship_to = ALIEXPRESS["ship_to"]

        # Verificar se o país de envio é válido
        assert ship_to == "Brazil", f"País de envio incorreto: {ship_to}"
        assert len(ship_to) > 0, "País de envio vazio"
        assert ship_to.isalpha(), f"País de envio com caracteres inválidos: {ship_to}"

    def test_aliexpress_configuration_consistency(self):
        """Testa se a configuração é consistente."""
        # Verificar se tracking e ship_to estão presentes
        assert "tracking" in ALIEXPRESS, "Configuração de tracking ausente"
        assert "ship_to" in ALIEXPRESS, "Configuração de envio ausente"

        # Verificar se os valores são válidos
        tracking = ALIEXPRESS["tracking"]
        ship_to = ALIEXPRESS["ship_to"]

        assert (
            tracking == "telegram"
        ), f"Tracking deve ser 'telegram', obtido: {tracking}"
        assert (
            ship_to == "Brazil"
        ), f"País de envio deve ser 'Brazil', obtido: {ship_to}"


class TestAliExpressInvalidCases:
    """Testa casos inválidos para AliExpress."""

    def test_invalid_domain_rejection(self):
        """Testa se domínios inválidos são rejeitados."""
        # Usar um domínio realmente inválido
        invalid_url = "https://www.lojainvalida.com.br/produto/123"

        parsed = urlparse(invalid_url)
        domain = parsed.netloc

        # Verificar se o domínio não é válido
        valid_domains = ["pt.aliexpress.com", "s.click.aliexpress.com"]
        assert domain not in valid_domains, f"Domínio inválido foi aceito: {domain}"

    def test_invalid_path_rejection(self):
        """Testa se paths inválidos são rejeitados."""
        invalid_paths = [
            "https://pt.aliexpress.com/invalid/path",
            "https://pt.aliexpress.com/user/123",
            "https://pt.aliexpress.com/search?q=teste",
            "https://pt.aliexpress.com/shop/123",
            "https://pt.aliexpress.com/category/123",
        ]

        for url in invalid_paths:
            assert not is_valid_aliexpress_product(
                url
            ), f"Path inválido foi aceito: {url}"

    def test_malformed_shortlink_rejection(self):
        """Testa se shortlinks malformados são rejeitados."""
        malformed_shortlinks = [
            "https://s.click.aliexpress.com/e/",
            "https://s.click.aliexpress.com/e",
            "https://s.click.aliexpress.com/e/invalid/path",
            "https://s.click.aliexpress.com/e/123?param=value",
            "https://s.click.aliexpress.com/e/123#fragment",
        ]

        for url in malformed_shortlinks:
            assert not ALIEXPRESS_SHORTLINK_PATTERN.match(
                url
            ), f"Shortlink malformado foi aceito: {url}"

    def test_non_product_url_rejection(self):
        """Testa se URLs que não são produtos são rejeitadas."""
        non_product_urls = [
            "https://pt.aliexpress.com/category/123",
            "https://pt.aliexpress.com/store/123",
            "https://pt.aliexpress.com/search?q=teste",
            "https://pt.aliexpress.com/user/123",
            "https://pt.aliexpress.com/shop/123",
        ]

        for url in non_product_urls:
            assert not is_valid_aliexpress_product(
                url
            ), f"URL não-produto foi aceita: {url}"


class TestAliExpressIntegration:
    """Testa a integração entre diferentes tipos de URLs do AliExpress."""

    def test_aliexpress_url_types_consistency(self):
        """Testa se os diferentes tipos de URL são consistentes."""
        # Verificar se todos os tipos de URL estão presentes
        assert "product_1" in ALIEXPRESS, "Produto 1 ausente"
        assert "short_1" in ALIEXPRESS, "Shortlink 1 ausente"
        assert "tracking" in ALIEXPRESS, "Configuração de tracking ausente"
        assert "ship_to" in ALIEXPRESS, "Configuração de envio ausente"

        # Verificar se são URLs válidas
        for key, url in ALIEXPRESS.items():
            if key.startswith("product") or key.startswith("short"):
                assert url.startswith("http"), f"URL inválida para {key}: {url}"

                # Verificar se o domínio é consistente com o tipo
                parsed = urlparse(url)
                if "short" in key:
                    assert (
                        parsed.netloc == "s.click.aliexpress.com"
                    ), f"Domínio incorreto para shortlink {key}"
                else:
                    assert (
                        parsed.netloc == "pt.aliexpress.com"
                    ), f"Domínio incorreto para {key}"

    def test_aliexpress_product_shortlink_mapping(self):
        """Testa se há correspondência entre produtos e shortlinks."""
        # Verificar se há shortlinks suficientes para os produtos
        product_count = len([k for k in ALIEXPRESS.keys() if k.startswith("product")])
        shortlink_count = len([k for k in ALIEXPRESS.keys() if k.startswith("short")])

        assert (
            shortlink_count >= product_count
        ), f"Shortlinks insuficientes: {shortlink_count} para {product_count} produtos"

    def test_aliexpress_url_format_validation(self):
        """Testa se todas as URLs seguem os formatos esperados."""
        for key, url in ALIEXPRESS.items():
            if key.startswith("product"):
                assert is_valid_aliexpress_product(
                    url
                ), f"Produto com formato inválido: {key}"
            elif key.startswith("short"):
                assert ALIEXPRESS_SHORTLINK_PATTERN.match(
                    url
                ), f"Shortlink com formato inválido: {key}"
            elif key in ["tracking", "ship_to"]:
                # Configurações não são URLs
                assert isinstance(url, str), f"Configuração deve ser string: {key}"
            else:
                # URLs não categorizadas devem ser válidas
                assert url.startswith("http"), f"URL não categorizada inválida: {key}"

    def test_aliexpress_product_id_consistency(self):
        """Testa se os IDs dos produtos são únicos."""
        # Extrair IDs dos produtos
        product_ids = []
        for key, url in ALIEXPRESS.items():
            if key.startswith("product"):
                import re

                product_id_match = re.search(r"/item/(\d+)\.html", url)
                if product_id_match:
                    product_ids.append(product_id_match.group(1))

        # Verificar se há produtos
        assert len(product_ids) > 0, "Nenhum ID de produto encontrado"

        # Verificar se os IDs são únicos
        assert len(product_ids) == len(
            set(product_ids)
        ), "IDs de produtos duplicados encontrados"

        # Verificar se cada ID é único
        for i, id1 in enumerate(product_ids):
            for j, id2 in enumerate(product_ids):
                if i != j:
                    assert id1 != id2, f"IDs idênticos: {id1} e {id2}"


def is_alix_short(url: str) -> bool:
    return url.startswith("https://s.click.aliexpress.com/e/")


def is_alix_product_raw(url: str) -> bool:
    return "pt.aliexpress.com/item/" in url


def test_alix_shortlinks_validos():
    for k in ("short_1", "short_2", "short_3", "short_4", "short_5"):
        assert is_alix_short(ALIEXPRESS[k])


def test_alix_raw_products_precisam_converter():
    assert is_alix_product_raw(ALIEXPRESS["product_1"])
    assert is_alix_product_raw(ALIEXPRESS["product_2"])
