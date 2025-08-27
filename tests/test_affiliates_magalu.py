"""
Testes específicos para validação de afiliados Magazine Luiza.

Cobre todos os cenários de validação:
- Vitrine válida
- Vitrine com params
- Domínio errado (bloqueia)
- Encurtadores terceiros (bloqueia)
- Páginas institucionais (bloqueia)
"""

import sys
from pathlib import Path

import pytest

# Adicionar o diretório raiz ao Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.affiliate.magazineluiza import (
    generate_magazine_affiliate_url,
    validate_magazineluiza_url,
)
from src.utils.affiliate_validator import validate_affiliate_link


class TestMagazineLuizaValidation:
    """Testes de validação para Magazine Luiza"""

    def test_valid_vitrine_urls(self):
        """Testa URLs de vitrine válidas do Magazine Luiza"""
        valid_vitrine_urls = [
            "https://www.magazinevoce.com.br/magazinegarimpeirogeek/apple-iphone-14-128gb-estelar-61-12mp-ios-5g/p/237184100/te/ip14/",
            "https://www.magazinevoce.com.br/magazinegarimpeirogeek/apple-iphone-14-128gb-meia-noite-61-12mp-ios-5g/p/237184000/te/ip14/",
            "https://magazinevoce.com.br/magazinegarimpeirogeek/produto-teste/p/12345/te/teste",
            "https://www.magazinevoce.com.br/magazinegarimpeirogeek/outro-produto/p/67890/te/outro",
        ]

        for url in valid_vitrine_urls:
            is_valid, error = validate_magazineluiza_url(url)
            assert is_valid, f"Vitrine válida rejeitada: {url} - {error}"

            # Testar no validador centralizado
            is_valid_central, platform, error_central = validate_affiliate_link(url)
            assert is_valid_central, f"Validador centralizado rejeitou: {url}"
            assert platform == "magazineluiza", f"Plataforma incorreta: {platform}"

    def test_vitrine_with_params(self):
        """Testa URLs de vitrine com parâmetros (aceitar após normalização)"""
        vitrine_with_params = [
            "https://www.magazinevoce.com.br/magazinegarimpeirogeek/apple-iphone-14-128gb-estelar-61-12mp-ios-5g/p/237184100/te/ip14/?utm_source=google&utm_medium=cpc",
            "https://www.magazinevoce.com.br/magazinegarimpeirogeek/produto-teste/p/12345/te/teste?ref=homepage&tracking=123",
            "https://www.magazinevoce.com.br/magazinegarimpeirogeek/outro-produto/p/67890/te/outro?src=search&pvid=456",
        ]

        for url in vitrine_with_params:
            is_valid, error = validate_magazineluiza_url(url)
            assert is_valid, f"Vitrine com parâmetros rejeitada: {url} - {error}"

    def test_wrong_domain_blocked(self):
        """Testa que URLs com domínio errado são bloqueadas"""
        wrong_domain_urls = [
            "https://www.magazineluiza.com.br/apple-iphone-14-128gb-estelar-61-12mp-ios-5g/p/237184100/te/ip14/",
            "https://magazineluiza.com.br/produto-teste/p/12345/te/teste",
            "https://www.magazineluiza.com.br/produto-sem-vitrine",
            "https://magazineluiza.com.br/categoria/eletronicos",
        ]

        for url in wrong_domain_urls:
            is_valid, error = validate_magazineluiza_url(url)
            assert not is_valid, f"Domínio errado aceito incorretamente: {url}"
            assert (
                "magazineluiza.com.br não é válido" in error
            ), f"Erro incorreto: {error}"

    def test_third_party_shorteners_blocked(self):
        """Testa que encurtadores terceiros são bloqueados"""
        shortener_urls = [
            "https://bit.ly/abc123",
            "https://tinyurl.com/xyz789",
            "https://goo.gl/def456",
            "https://t.co/ghi789",
        ]

        for url in shortener_urls:
            is_valid, error = validate_magazineluiza_url(url)
            assert not is_valid, f"Encurtador terceiro aceito incorretamente: {url}"

    def test_institutional_pages_blocked(self):
        """Testa que páginas institucionais são bloqueadas"""
        institutional_urls = [
            "https://www.magazinevoce.com.br/sobre-nos",
            "https://www.magazinevoce.com.br/contato",
            "https://www.magazinevoce.com.br/ajuda",
            "https://www.magazinevoce.com.br/politica-privacidade",
            "https://www.magazinevoce.com.br/termos-uso",
        ]

        for url in institutional_urls:
            is_valid, error = validate_magazineluiza_url(url)
            assert not is_valid, f"Página institucional aceita incorretamente: {url}"

    def test_invalid_vitrine_structure(self):
        """Testa que URLs sem estrutura de vitrine válida são rejeitadas"""
        invalid_vitrine_urls = [
            "https://www.magazinevoce.com.br/magazinegarimpeirogeek/produto-sem-estrutura",
            "https://www.magazinevoce.com.br/magazinegarimpeirogeek/",
            "https://www.magazinevoce.com.br/magazinegarimpeirogeek/categoria/eletronicos",
            "https://www.magazinevoce.com.br/magazinegarimpeirogeek/search?q=iphone",
        ]

        for url in invalid_vitrine_urls:
            is_valid, error = validate_magazineluiza_url(url)
            assert (
                not is_valid
            ), f"Estrutura de vitrine inválida aceita incorretamente: {url}"

    def test_invalid_domains_rejected(self):
        """Testa que domínios inválidos são rejeitados"""
        invalid_domains = [
            "https://exemplo-invalido.com/produto",
            "https://www.amazon.com.br/produto",
            "https://magazinevoce.com/produto-sem-br",
            "https://magazinevoce.com.br.invalid/produto",
            "https://fake-magazinevoce.com.br/produto",
        ]

        for url in invalid_domains:
            is_valid, error = validate_magazineluiza_url(url)
            assert not is_valid, f"Domínio inválido aceito incorretamente: {url}"

    def test_generate_affiliate_url_success(self):
        """Testa geração bem-sucedida de URL de afiliado"""
        valid_product_url = "https://www.magazineluiza.com.br/apple-iphone-14-128gb-estelar-61-12mp-ios-5g/p/237184100/te/ip14/"

        success, affiliate_url, error = generate_magazine_affiliate_url(
            valid_product_url
        )

        assert success, f"Falha ao gerar URL de afiliado: {error}"
        assert affiliate_url.startswith(
            "https://www.magazinevoce.com.br/magazinegarimpeirogeek/"
        ), f"Formato de URL incorreto: {affiliate_url}"
        assert (
            "magazinegarimpeirogeek" in affiliate_url
        ), f"Vitrine não encontrada na URL: {affiliate_url}"

    def test_generate_affiliate_url_invalid_url(self):
        """Testa falha na geração de URL de afiliado para URL inválida"""
        invalid_urls = [
            "https://exemplo-invalido.com/produto",
            "https://www.magazinevoce.com.br/produto-sem-estrutura",
            "https://www.magazineluiza.com.br/produto-sem-estrutura",
        ]

        for url in invalid_urls:
            success, affiliate_url, error = generate_magazine_affiliate_url(url)
            assert not success, f"URL de afiliado gerada para URL inválida: {url}"
            assert "inválida" in error.lower(), f"Erro incorreto: {error}"

    def test_generate_affiliate_url_already_valid(self):
        """Testa que URLs já válidas são retornadas como estão"""
        already_valid_url = "https://www.magazinevoce.com.br/magazinegarimpeirogeek/apple-iphone-14-128gb-estelar-61-12mp-ios-5g/p/237184100/te/ip14/"

        success, affiliate_url, error = generate_magazine_affiliate_url(
            already_valid_url
        )

        assert success, f"Falha ao processar URL já válida: {error}"
        assert (
            affiliate_url == already_valid_url
        ), f"URL válida foi modificada incorretamente: {affiliate_url}"

    def test_validation_integration(self):
        """Testa integração com o validador centralizado"""
        test_cases = [
            # URLs válidas
            (
                "https://www.magazinevoce.com.br/magazinegarimpeirogeek/apple-iphone-14-128gb-estelar-61-12mp-ios-5g/p/237184100/te/ip14/",
                True,
                "magazineluiza",
            ),
            (
                "https://magazinevoce.com.br/magazinegarimpeirogeek/produto-teste/p/12345/te/teste",
                True,
                "magazineluiza",
            ),
            # URLs inválidas
            (
                "https://www.magazineluiza.com.br/produto-sem-vitrine",
                False,
                "magazineluiza",
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
