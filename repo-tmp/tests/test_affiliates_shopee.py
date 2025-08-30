"""
Testes específicos para validação de afiliados Shopee.

Cobre todos os cenários de validação:
- URL produto válida
- Com query extra
- Com %20 escaped
- Com fragmento
- Categoria (rejeita)
- Perfil (rejeita)
- Shortlink válido
- Shortlink inválido
- Redirects simulados
"""

import sys
from pathlib import Path

import pytest

# Adicionar o diretório raiz ao Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.affiliate.shopee import generate_shopee_shortlink, validate_shopee_url
from src.utils.affiliate_validator import validate_affiliate_link


class TestShopeeValidation:
    """Testes de validação para Shopee"""

    def test_valid_shortlinks(self):
        """Testa shortlinks válidos do Shopee"""
        valid_shortlinks = [
            "https://s.shopee.com.br/3LGfnEjEXu",
            "https://s.shopee.com.br/3Va5zXibCx",
            "https://s.shopee.com.br/4L9Cz4fQW8",
            "https://s.shopee.com.br/abc123",
            "https://s.shopee.com.br/XYZ789",
        ]

        for url in valid_shortlinks:
            is_valid, error = validate_shopee_url(url)
            assert is_valid, f"Shortlink válido rejeitado: {url} - {error}"

            # Testar no validador centralizado
            is_valid_central, platform, error_central = validate_affiliate_link(url)
            assert is_valid_central, f"Validador centralizado rejeitou: {url}"
            assert platform == "shopee", f"Plataforma incorreta: {platform}"

    def test_valid_product_urls(self):
        """Testa URLs de produto válidas do Shopee"""
        valid_product_urls = [
            "https://shopee.com.br/iPhone-16-Pro-Max-256GB-5G-eSIM-XDR-OLED-6-9-Polegadas-C%C3%A2mera-48MP-HDR-Inteligente-5-Tit%C3%A2nio-i.337570318.22498324413",
            "https://shopee.com.br/REDMAGIC-Astra-Gaming-Tablet-para-Jogos-9.06''-OLED-8200mAh-Snapdragon-8-Elite-12GB-256GB-16GB-512GB-24GB-1TB-i.1339225555.22298729139",
            "https://shopee.com.br/product/337570318/22498324413",
            "https://www.shopee.com.br/Produto-Teste-i.123456.789012",
        ]

        for url in valid_product_urls:
            is_valid, error = validate_shopee_url(url)
            assert is_valid, f"URL de produto válida rejeitada: {url} - {error}"

    def test_product_urls_with_query_strings(self):
        """Testa URLs de produto com query strings (aceitar após normalização)"""
        urls_with_query = [
            "https://shopee.com.br/iPhone-16-Pro-Max-256GB-5G-eSIM-XDR-OLED-6-9-Polegadas-C%C3%A2mera-48MP-HDR-Inteligente-5-Tit%C3%A2nio-i.337570318.22498324413?utm_source=google&utm_medium=cpc&utm_campaign=shopping",
            "https://shopee.com.br/REDMAGIC-Astra-Gaming-Tablet-para-Jogos-9.06''-OLED-8200mAh-Snapdragon-8-Elite-12GB-256GB-16GB-512GB-24GB-1TB-i.1339225555.22298729139?src=search&pvid=12345",
            "https://shopee.com.br/Produto-Teste-i.123456.789012?ref=homepage&tracking=123",
        ]

        for url in urls_with_query:
            is_valid, error = validate_shopee_url(url)
            assert is_valid, f"URL com query válida rejeitada: {url} - {error}"

    def test_product_urls_with_fragments(self):
        """Testa URLs de produto com fragmentos (aceitar)"""
        urls_with_fragments = [
            "https://shopee.com.br/iPhone-16-Pro-Max-256GB-5G-eSIM-XDR-OLED-6-9-Polegadas-C%C3%A2mera-48MP-HDR-Inteligente-5-Tit%C3%A2nio-i.337570318.22498324413#specs",
            "https://shopee.com.br/Produto-Teste-i.123456.789012#description",
            "https://shopee.com.br/Produto-Teste-i.123456.789012?utm_source=google#reviews",
        ]

        for url in urls_with_fragments:
            is_valid, error = validate_shopee_url(url)
            assert is_valid, f"URL com fragmento válida rejeitada: {url} - {error}"

    def test_product_urls_with_encoded_spaces(self):
        """Testa URLs de produto com espaços codificados (aceitar)"""
        urls_with_encoded_spaces = [
            "https://shopee.com.br/iPhone%2016%20Pro%20Max%20i.337570318.22498324413",
            "https://shopee.com.br/Produto%20Com%20Espa%C3%A7os%20i.123456.789012",
            "https://shopee.com.br/Produto%20Teste%20i.123456.789012?utm_source=google",
        ]

        for url in urls_with_encoded_spaces:
            is_valid, error = validate_shopee_url(url)
            assert is_valid, f"URL com espaços codificados rejeitada: {url} - {error}"

    def test_category_pages_rejected(self):
        """Testa que páginas de categoria são rejeitadas"""
        category_urls = [
            "https://shopee.com.br/oficial/Celulares-e-Dispositivos-cat.11059988",
            "https://shopee.com.br/search?keyword=iphone",
            "https://shopee.com.br/cat.11059988",
            "https://shopee.com.br/category/eletronicos",
            "https://shopee.com.br/browse?category=123",
        ]

        for url in category_urls:
            is_valid, error = validate_shopee_url(url)
            assert not is_valid, f"Página de categoria aceita incorretamente: {url}"
            assert (
                "categoria" in error.lower()
                or "busca" in error.lower()
                or "perfil" in error.lower()
            ), f"Erro incorreto: {error}"

    def test_profile_pages_rejected(self):
        """Testa que páginas de perfil são rejeitadas"""
        profile_urls = [
            "https://shopee.com.br/user/profile/12345",
            "https://shopee.com.br/seller/67890",
            "https://shopee.com.br/profile/user123",
            "https://shopee.com.br/seller/profile/456",
            "https://shopee.com.br/user/12345",
        ]

        for url in profile_urls:
            is_valid, error = validate_shopee_url(url)
            assert not is_valid, f"Página de perfil aceita incorretamente: {url}"
            assert (
                "perfil" in error.lower()
                or "categoria" in error.lower()
                or "busca" in error.lower()
            ), f"Erro incorreto: {error}"

    def test_invalid_shortlinks_rejected(self):
        """Testa que shortlinks inválidos são rejeitados"""
        invalid_shortlinks = [
            "https://s.shopee.com.br/",
            "https://s.shopee.com.br",
            "https://s.shopee.com.br/invalid-format",
            "https://s.shopee.com.br/123/456",
            "https://s.shopee.com.br/abc@def",
        ]

        for url in invalid_shortlinks:
            is_valid, error = validate_shopee_url(url)
            assert not is_valid, f"Shortlink inválido aceito incorretamente: {url}"

    def test_redirects_simulated(self):
        """Testa URLs que simulam redirecionamentos"""
        redirect_urls = [
            "https://shopee.com.br/redirect?url=https://shopee.com.br/Produto-i.123456.789012",
            "https://shopee.com.br/go?target=Produto-i.123456.789012",
            "https://shopee.com.br/link?dest=Produto-i.123456.789012",
        ]

        for url in redirect_urls:
            is_valid, error = validate_shopee_url(url)
            assert not is_valid, f"URL de redirecionamento aceita incorretamente: {url}"

    def test_invalid_domains_rejected(self):
        """Testa que domínios inválidos são rejeitados"""
        invalid_domains = [
            "https://exemplo-invalido.com/produto",
            "https://www.amazon.com.br/produto",
            "https://shopee.com/produto-sem-br",
            "https://shopee.com.br.invalid/produto",
            "https://fake-shopee.com.br/produto",
        ]

        for url in invalid_domains:
            is_valid, error = validate_shopee_url(url)
            assert not is_valid, f"Domínio inválido aceito incorretamente: {url}"

    def test_generate_shortlink_success(self):
        """Testa geração bem-sucedida de shortlink"""
        valid_product_url = "https://shopee.com.br/iPhone-16-Pro-Max-256GB-5G-eSIM-XDR-OLED-6-9-Polegadas-C%C3%A2mera-48MP-HDR-Inteligente-5-Tit%C3%A2nio-i.337570318.22498324413"

        success, shortlink, error = generate_shopee_shortlink(valid_product_url)

        assert success, f"Falha ao gerar shortlink: {error}"
        assert shortlink.startswith(
            "https://s.shopee.com.br/"
        ), f"Formato de shortlink incorreto: {shortlink}"
        assert (
            len(shortlink.split("/")[-1]) >= 8
        ), f"ID do shortlink muito curto: {shortlink}"

    def test_generate_shortlink_invalid_url(self):
        """Testa falha na geração de shortlink para URL inválida"""
        invalid_urls = [
            "https://shopee.com.br/oficial/Celulares-e-Dispositivos-cat.11059988",
            "https://exemplo-invalido.com/produto",
            "https://shopee.com.br/invalid-format",
        ]

        for url in invalid_urls:
            success, shortlink, error = generate_shopee_shortlink(url)
            assert not success, f"Shortlink gerado para URL inválida: {url}"
            assert "inválida" in error.lower(), f"Erro incorreto: {error}"

    def test_validation_integration(self):
        """Testa integração com o validador centralizado"""
        test_cases = [
            # URLs válidas
            ("https://s.shopee.com.br/3LGfnEjEXu", True, "shopee"),
            ("https://shopee.com.br/Produto-Teste-i.123456.789012", True, "shopee"),
            # URLs inválidas
            (
                "https://shopee.com.br/oficial/Celulares-e-Dispositivos-cat.11059988",
                False,
                "shopee",
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
