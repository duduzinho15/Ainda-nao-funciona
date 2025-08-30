"""
Testes do Sistema de Conversores de Afiliados
Valida funcionalidades básicas sem dependências complexas
"""

import os
import sys

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_amazon_converter():
    """Testa conversor Amazon"""
    from affiliate.amazon import extract_asin_from_url, to_affiliate_url

    # Teste de extração de ASIN
    asin = extract_asin_from_url("https://amazon.com.br/produto/dp/B08N5WRWNW")
    assert asin == "B08N5WRWNW"

    # Teste de conversão para afiliado
    affiliate_url = to_affiliate_url("B08N5WRWNW", "com.br", "garimpeirogeek-20")
    assert "tag=garimpeirogeek-20" in affiliate_url
    assert "amazon.com.br" in affiliate_url

    print("✅ Amazon converter: OK")


def test_mercadolivre_converter():
    """Testa conversor Mercado Livre"""
    from affiliate.mercadolivre import generate_ml_shortlink, validate_ml_url

    # Teste de validação - URLs de produto são bloqueadas (precisam conversão)
    is_valid, error = validate_ml_url("https://mercadolivre.com.br/produto/p/MLB123")
    assert not is_valid  # Deve ser bloqueada
    assert "shortlink /sec/ ou social" in error

    # Teste de geração de shortlink
    success, shortlink, error = generate_ml_shortlink(
        "https://mercadolivre.com.br/produto/p/MLB123"
    )
    assert success
    assert "mercadolivre.com/sec/" in shortlink

    print("✅ Mercado Livre converter: OK")


def test_shopee_converter():
    """Testa conversor Shopee"""
    from affiliate.shopee import generate_shopee_shortlink, validate_shopee_url

    # Teste de validação
    is_valid, error = validate_shopee_url(
        "https://shopee.com.br/iPhone-i.337570318.22498324413"
    )
    assert is_valid

    # Teste de geração de shortlink
    success, shortlink, error = generate_shopee_shortlink(
        "https://shopee.com.br/iPhone-i.337570318.22498324413"
    )
    assert success
    assert "s.shopee.com.br/" in shortlink

    print("✅ Shopee converter: OK")


def test_magazineluiza_converter():
    """Testa conversor Magazine Luiza"""
    from affiliate.magazineluiza import (
        generate_magazine_affiliate_url,
        validate_magazine_url,
    )

    # Teste de validação
    is_valid, error = validate_magazine_url(
        "https://magazinevoce.com.br/magazinegarimpeirogeek/produto/p/123"
    )
    assert is_valid

    # Teste de geração de URL de afiliado
    success, affiliate_url, error = generate_magazine_affiliate_url(
        "https://magazinevoce.com.br/magazinegarimpeirogeek/produto/p/123"
    )
    assert success
    assert "magazinevoce.com.br/magazinegarimpeirogeek" in affiliate_url

    print("✅ Magazine Luiza converter: OK")


def test_aliexpress_converter():
    """Testa conversor AliExpress"""
    from affiliate.aliexpress import (
        generate_aliexpress_shortlink,
        validate_aliexpress_url,
    )

    # Teste de validação
    is_valid, error = validate_aliexpress_url(
        "https://pt.aliexpress.com/item/1005006756452012.html"
    )
    assert is_valid

    # Teste de geração de shortlink
    success, shortlink, error = generate_aliexpress_shortlink(
        "https://pt.aliexpress.com/item/1005006756452012.html"
    )
    assert success
    assert "s.click.aliexpress.com/e/" in shortlink

    print("✅ AliExpress converter: OK")


def test_awin_converter():
    """Testa conversor Awin"""
    from affiliate.awin import validate_store_domain

    # Teste de validação
    is_valid, store, error = validate_store_domain("https://comfy.com.br/produto")
    assert is_valid
    assert store == "comfy"

    # Teste de loja não permitida
    is_valid, store, error = validate_store_domain("https://loja-invalida.com/produto")
    assert not is_valid

    print("✅ Awin converter: OK")


def test_affiliate_validator():
    """Testa validador de afiliados"""
    from core.affiliate_validator import AffiliateValidator, ValidationStatus

    validator = AffiliateValidator()

    # Teste de identificação de plataforma
    platform = validator.identify_platform("https://amazon.com.br/produto")
    assert platform == "amazon"

    # Teste de validação
    result = validator.validate_conversion(
        "https://amazon.com.br/produto",
        "https://amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogeek-20",
    )
    assert result.status in [ValidationStatus.VALID, ValidationStatus.WARNING]
    assert result.score > 0.5

    print("✅ Affiliate validator: OK")


def test_affiliate_cache():
    """Testa cache de afiliados"""
    from core.affiliate_cache import AffiliateCache

    cache = AffiliateCache()

    # Teste de operações básicas
    success = cache._fallback_set("test_platform", "test_url", "test_affiliate")
    assert success

    cached = cache._fallback_get("test_platform", "test_url")
    assert cached is not None
    assert cached["affiliate_url"] == "test_affiliate"

    exists = cache._fallback_exists("test_platform", "test_url")
    assert exists

    deleted = cache._fallback_delete("test_platform", "test_url")
    assert deleted

    print("✅ Affiliate cache: OK")


def test_affiliate_converter():
    """Testa conversor principal"""
    from core.affiliate_converter import AffiliateConverter

    converter = AffiliateConverter()

    # Teste de identificação de loja
    store = converter.identify_store("https://amazon.com.br/produto")
    assert store == "amazon"

    # Teste de configurações
    assert len(converter.affiliate_configs) > 0
    assert "amazon" in converter.affiliate_configs
    assert "magalu" in converter.affiliate_configs

    print("✅ Affiliate converter: OK")


def run_all_tests():
    """Executa todos os testes"""
    print("🧪 EXECUTANDO TESTES DOS CONVERSORES DE AFILIADOS")
    print("=" * 60)

    try:
        test_amazon_converter()
        test_mercadolivre_converter()
        test_shopee_converter()
        test_magazineluiza_converter()
        test_aliexpress_converter()
        test_awin_converter()
        test_affiliate_validator()
        test_affiliate_cache()
        test_affiliate_converter()

        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema de conversores de afiliados está 100% funcional!")

    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
