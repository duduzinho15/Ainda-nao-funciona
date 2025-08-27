"""
Testes específicos para validação de afiliados Mercado Livre.

Cobre todos os cenários de validação:
- Produto
- Catálogo (p/MLB)
- Shortlink válido
- Shortlink inválido
- Perfil social válido
- Redirects simulados
"""

import sys
from pathlib import Path

import pytest

# Adicionar o diretório raiz ao Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.affiliate.mercadolivre import (
    generate_ml_affiliate_url,
    validate_mercadolivre_url,
)
from src.utils.affiliate_validator import validate_affiliate_link


class TestMercadoLivreValidation:
    """Testes de validação para Mercado Livre"""

    def test_valid_shortlinks(self):
        """Testa shortlinks válidos do Mercado Livre"""
        valid_shortlinks = [
            "https://mercadolivre.com/sec/1vt6gtj",
            "https://mercadolivre.com/sec/2AsYJk3",
            "https://mercadolivre.com/sec/27Hhvsc",
            "https://www.mercadolivre.com.br/sec/abc123",
            "https://mercadolivre.com/sec/XYZ789",
        ]

        for url in valid_shortlinks:
            is_valid, error = validate_mercadolivre_url(url)
            assert is_valid, f"Shortlink válido rejeitado: {url} - {error}"

            # Testar no validador centralizado
            is_valid_central, platform, error_central = validate_affiliate_link(url)
            assert is_valid_central, f"Validador centralizado rejeitou: {url}"
            assert platform == "mercadolivre", f"Plataforma incorreta: {platform}"

    def test_valid_product_urls(self):
        """Testa URLs de produto válidas do Mercado Livre"""
        valid_product_urls = [
            "https://www.mercadolivre.com.br/case-hd-ssd-externo-usb-30-sata-2535-4tb-com-fonte-knup/up/MLBU2922204299",
            "https://www.mercadolivre.com.br/smartphone-motorola-moto-g35-5g-128gb-12gb-4gb-ram8gb-ram-boost-e-camera-50mp-com-ai-nfc-tela-67-com-superbrilho-grafite-vegan-leather/p/MLB41540844",
            "https://produto.mercadolivre.com.br/MLB-5390754452-fone-de-ouvido-atfly-j10-anc-enc-bluetooth-53-bateria-24h-_JM",
            "https://www.mercadolivre.com.br/produto-teste/p/MLB123456789",
            "https://mercadolivre.com.br/item/MLBU987654321",
        ]

        for url in valid_product_urls:
            is_valid, error = validate_mercadolivre_url(url)
            assert is_valid, f"URL de produto válida rejeitada: {url} - {error}"

    def test_valid_social_profile_urls(self):
        """Testa URLs de perfil social válidas do Mercado Livre"""
        valid_social_urls = [
            "https://www.mercadolivre.com.br/social/garimpeirogeek?matt_word=garimpeirogeek&matt_tool=82173227&forceInApp=true&ref=test",
            "https://mercadolivre.com.br/social/garimpeirogeek?matt_word=garimpeirogeek&matt_tool=82173227&ref=garimpeirogeek",
            "https://www.mercadolivre.com.br/social/garimpeirogeek?matt_word=garimpeirogeek&matt_tool=82173227&forceInApp=true&ref=BAeQLRQ4ZIyXtyt1DOSkUM8yMI1iHK6mKK3csiMKKY85m2kTS78zxYCutYKq3j09KM3d8qz60R2Qn8WAmZCWTh2gsTbB4JsRz9E96NAsxnLDO0XiduuDwJn38h%2BH5IxjK2m0jrC1D9UGGCwvlgBRDKyrgr2SaOlA0gy2jNXkRHOpH5MWeTDJYJFKfYfPvnmuwtZgyQ%3D%3D",
        ]

        for url in valid_social_urls:
            is_valid, error = validate_mercadolivre_url(url)
            assert is_valid, f"URL social válida rejeitada: {url} - {error}"

    def test_product_urls_with_query_strings(self):
        """Testa URLs de produto com query strings (aceitar após normalização)"""
        urls_with_query = [
            "https://www.mercadolivre.com.br/case-hd-ssd-externo-usb-30-sata-2535-4tb-com-fonte-knup/up/MLBU2922204299?pdp_filters=item_id:MLB5240881988&deal_print_id=9f852991-595f-4923-911a-b0941f218871&position=8&tracking_id=7c521182-e446-46a2-9bd9-73c9a76cd210&wid=MLB5240881988&sid=offers",
            "https://www.mercadolivre.com.br/smartphone-motorola-moto-g35-5g-128gb-12gb-4gb-ram8gb-ram-boost-e-camera-50mp-com-ai-nfc-tela-67-com-superbrilho-grafite-vegan-leather/p/MLB41540844?utm_source=google&utm_medium=cpc&utm_campaign=shopping",
            "https://produto.mercadolivre.com.br/MLB-5390754452-fone-de-ouvido-atfly-j10-anc-enc-bluetooth-53-bateria-24h-_JM?src=search&pvid=12345",
        ]

        for url in urls_with_query:
            is_valid, error = validate_mercadolivre_url(url)
            assert is_valid, f"URL com query válida rejeitada: {url} - {error}"

    def test_invalid_shortlinks_rejected(self):
        """Testa que shortlinks inválidos são rejeitados"""
        invalid_shortlinks = [
            "https://mercadolivre.com/sec/",
            "https://mercadolivre.com/sec",
            "https://mercadolivre.com/sec/invalid-format",
            "https://mercadolivre.com/sec/123/456",
            "https://mercadolivre.com/sec/abc@def",
        ]

        for url in invalid_shortlinks:
            is_valid, error = validate_mercadolivre_url(url)
            assert not is_valid, f"Shortlink inválido aceito incorretamente: {url}"

    def test_category_pages_rejected(self):
        """Testa que páginas de categoria são rejeitadas"""
        category_urls = [
            "https://www.mercadolivre.com.br/categoria/eletronicos",
            "https://mercadolivre.com.br/categoria/celulares",
            "https://www.mercadolivre.com.br/browse?category=123",
            "https://mercadolivre.com.br/categoria/informatica",
        ]

        for url in category_urls:
            is_valid, error = validate_mercadolivre_url(url)
            assert not is_valid, f"Página de categoria aceita incorretamente: {url}"
            assert (
                "categoria" in error.lower() or "busca" in error.lower()
            ), f"Erro incorreto: {error}"

    def test_search_pages_rejected(self):
        """Testa que páginas de busca são rejeitadas"""
        search_urls = [
            "https://www.mercadolivre.com.br/search?q=iphone",
            "https://mercadolivre.com.br/search?keyword=smartphone",
            "https://www.mercadolivre.com.br/search?category=MLB1000&q=laptop",
        ]

        for url in search_urls:
            is_valid, error = validate_mercadolivre_url(url)
            assert not is_valid, f"Página de busca aceita incorretamente: {url}"
            assert (
                "busca" in error.lower() or "categoria" in error.lower()
            ), f"Erro incorreto: {error}"

    def test_invalid_domains_rejected(self):
        """Testa que domínios inválidos são rejeitados"""
        invalid_domains = [
            "https://exemplo-invalido.com/produto",
            "https://www.amazon.com.br/produto",
            "https://mercadolivre.com/produto-sem-br",
            "https://mercadolivre.com.br.invalid/produto",
            "https://fake-mercadolivre.com.br/produto",
        ]

        for url in invalid_domains:
            is_valid, error = validate_mercadolivre_url(url)
            assert not is_valid, f"Domínio inválido aceito incorretamente: {url}"

    def test_generate_affiliate_url_success(self):
        """Testa geração bem-sucedida de URL de afiliado"""
        valid_product_url = "https://www.mercadolivre.com.br/produto/MLB-123456789"

        success, affiliate_url, error = generate_ml_affiliate_url(valid_product_url)

        assert success, f"Falha ao gerar URL de afiliado: {error}"
        # Deve gerar shortlink /sec/ ou URL social
        assert any(
            x in affiliate_url for x in ["/sec/", "social/garimpeirogeek"]
        ), f"Formato de URL incorreto: {affiliate_url}"

    def test_generate_affiliate_url_invalid_url(self):
        """Testa falha na geração de URL de afiliado para URL inválida"""
        invalid_urls = [
            "https://exemplo-invalido.com/produto",
            "https://www.mercadolivre.com.br/categoria/eletronicos",
            "https://mercadolivre.com.br/search?q=iphone",
        ]

        for url in invalid_urls:
            success, affiliate_url, error = generate_ml_affiliate_url(url)
            assert not success, f"URL de afiliado gerada para URL inválida: {url}"
            assert "inválida" in error.lower(), f"Erro incorreto: {error}"

    def test_generate_affiliate_url_already_valid(self):
        """Testa que URLs já válidas são retornadas como estão"""
        already_valid_urls = [
            "https://mercadolivre.com/sec/1vt6gtj",
            "https://www.mercadolivre.com.br/social/garimpeirogeek?matt_word=garimpeirogeek&matt_tool=82173227&forceInApp=true&ref=test",
        ]

        for url in already_valid_urls:
            success, affiliate_url, error = generate_ml_affiliate_url(url)
            assert success, f"Falha ao processar URL já válida: {error}"
            assert (
                affiliate_url == url
            ), f"URL válida foi modificada incorretamente: {affiliate_url}"

    def test_validation_integration(self):
        """Testa integração com o validador centralizado"""
        test_cases = [
            # URLs válidas
            ("https://mercadolivre.com/sec/1vt6gtj", True, "mercadolivre"),
            (
                "https://www.mercadolivre.com.br/produto/MLB-123456789",
                True,
                "mercadolivre",
            ),
            (
                "https://www.mercadolivre.com.br/social/garimpeirogeek?matt_word=garimpeirogeek&matt_tool=82173227&forceInApp=true&ref=test",
                True,
                "mercadolivre",
            ),
            # URLs inválidas
            (
                "https://www.mercadolivre.com.br/categoria/eletronicos",
                False,
                "mercadolivre",
            ),
            ("https://exemplo-invalido.com/produto", False, "unknown"),
        ]

        for url, expected_valid, expected_platform in test_cases:
            is_valid, platform, error = validate_affiliate_link(url)
            assert (
                is_valid == expected_valid
            ), f"Validação incorreta para {url}: esperado {expected_valid}, obtido {is_valid}"
            if expected_valid:
                assert (
                    platform == expected_platform
                ), f"Plataforma incorreta para {url}: esperado {expected_platform}, obtido {platform}"


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v"])
