"""
Testes Completos do Sistema de Conversores de Afiliados
Valida todos os conversores, validação e cache
"""

import os
import sys

import pytest

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from affiliate.aliexpress import validate_aliexpress_url
from affiliate.amazon import extract_asin_from_url
from affiliate.awin import validate_store_domain
from affiliate.magazineluiza import (
    validate_magazine_url,
)
from affiliate.mercadolivre import validate_ml_url
from affiliate.shopee import validate_shopee_url
from core.affiliate_cache import AffiliateCache
from core.affiliate_converter import AffiliateConverter
from core.affiliate_validator import AffiliateValidator, ValidationStatus


class TestAffiliateSystemComplete:
    """Testes completos do sistema de afiliados"""

    @pytest.fixture
    async def converter(self):
        """Fixture para o conversor principal"""
        converter = AffiliateConverter()
        await converter.connect_cache()
        yield converter
        await converter.disconnect_cache()

    @pytest.fixture
    async def validator(self):
        """Fixture para o validador"""
        return AffiliateValidator()

    @pytest.fixture
    async def cache(self):
        """Fixture para o cache"""
        cache = AffiliateCache()
        await cache.connect()
        yield cache
        await cache.disconnect()

    # ============================================================================
    # TESTES DO CONVERSOR PRINCIPAL
    # ============================================================================

    @pytest.mark.asyncio
    async def test_converter_initialization(self, converter):
        """Testa inicialização do conversor principal"""
        assert converter is not None
        assert converter.cache is not None
        assert converter.validator is not None
        assert len(converter.affiliate_configs) > 0

    @pytest.mark.asyncio
    async def test_converter_store_identification(self, converter):
        """Testa identificação de lojas"""
        # Amazon
        store = converter.identify_store("https://amazon.com.br/produto")
        assert store == "amazon"

        # Magazine Luiza
        store = converter.identify_store("https://magazineluiza.com.br/produto")
        assert store == "magalu"

        # Loja não suportada
        store = converter.identify_store("https://loja-invalida.com/produto")
        assert store is None

    @pytest.mark.asyncio
    async def test_converter_amazon_conversion(self, converter):
        """Testa conversão Amazon"""
        url = "https://amazon.com.br/produto/dp/B08N5WRWNW"
        affiliate_url = await converter.convert_to_affiliate(url)

        assert affiliate_url != url
        assert "tag=garimpeirogeek-20" in affiliate_url
        assert "amazon.com.br" in affiliate_url

    @pytest.mark.asyncio
    async def test_converter_magalu_conversion(self, converter):
        """Testa conversão Magazine Luiza"""
        url = "https://magazineluiza.com.br/produto/p/123"
        affiliate_url = await converter.convert_to_affiliate(url)

        assert affiliate_url != url
        assert "partner_id=garimpeirogeek" in affiliate_url
        assert "magazineluiza.com.br" in affiliate_url

    @pytest.mark.asyncio
    async def test_converter_batch_conversion(self, converter):
        """Testa conversão em lote"""
        offers = [
            {"url": "https://amazon.com.br/produto/dp/B08N5WRWNW"},
            {"url": "https://magazineluiza.com.br/produto/p/123"},
        ]

        converted = await converter.convert_offers_batch(offers)

        assert len(converted) == 2
        assert "affiliate_url" in converted[0]
        assert "affiliate_url" in converted[1]
        assert "original_url" in converted[0]
        assert "original_url" in converted[1]

    # ============================================================================
    # TESTES DO VALIDADOR
    # ============================================================================

    @pytest.mark.asyncio
    async def test_validator_initialization(self, validator):
        """Testa inicialização do validador"""
        assert validator is not None
        assert len(validator.validation_patterns) > 0
        assert len(validator.scoring_criteria) > 0

    @pytest.mark.asyncio
    async def test_validator_platform_identification(self, validator):
        """Testa identificação de plataformas"""
        # Amazon
        platform = validator.identify_platform("https://amazon.com.br/produto")
        assert platform == "amazon"

        # Mercado Livre
        platform = validator.identify_platform("https://mercadolivre.com.br/produto")
        assert platform == "mercadolivre"

        # Shopee
        platform = validator.identify_platform("https://shopee.com.br/produto")
        assert platform == "shopee"

        # AliExpress
        platform = validator.identify_platform("https://aliexpress.com/item/123")
        assert platform == "aliexpress"

        # Awin
        platform = validator.identify_platform("https://comfy.com.br/produto")
        assert platform == "awin"

    @pytest.mark.asyncio
    async def test_validator_amazon_validation(self, validator):
        """Testa validação Amazon"""
        # URL válida
        result = validator.validate_conversion(
            "https://amazon.com.br/produto",
            "https://amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogeek-20",
        )
        assert result.status in [ValidationStatus.VALID, ValidationStatus.WARNING]
        assert result.score > 0.5

        # URL inválida (sem tag)
        result = validator.validate_conversion(
            "https://amazon.com.br/produto", "https://amazon.com.br/dp/B08N5WRWNW"
        )
        assert result.status == ValidationStatus.INVALID
        assert result.score < 0.5

    @pytest.mark.asyncio
    async def test_validator_mercadolivre_validation(self, validator):
        """Testa validação Mercado Livre"""
        # Shortlink válido
        result = validator.validate_conversion(
            "https://mercadolivre.com.br/produto",
            "https://mercadolivre.com/sec/1vt6gtj",
        )
        assert result.status == ValidationStatus.VALID
        assert result.score > 0.9

        # URL de afiliado válida
        result = validator.validate_conversion(
            "https://mercadolivre.com.br/produto",
            "https://mercadolivre.com.br/social/garimpeirogeek?matt_word=garimpeirogeek",
        )
        assert result.status in [ValidationStatus.VALID, ValidationStatus.WARNING]
        assert result.score > 0.7

    @pytest.mark.asyncio
    async def test_validator_batch_validation(self, validator):
        """Testa validação em lote"""
        conversions = [
            {
                "original_url": "https://amazon.com.br/produto",
                "affiliate_url": "https://amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogeek-20",
            },
            {
                "original_url": "https://mercadolivre.com.br/produto",
                "affiliate_url": "https://mercadolivre.com/sec/1vt6gtj",
            },
        ]

        results = validator.validate_batch(conversions)

        assert len(results) == 2
        # Verificar se os resultados são válidos (não importa o tipo específico)
        assert all(hasattr(r, 'is_valid') for r in results)

    @pytest.mark.asyncio
    async def test_validator_stats(self, validator):
        """Testa estatísticas de validação"""
        conversions = [
            {
                "original_url": "https://amazon.com.br/produto",
                "affiliate_url": "https://amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogeek-20",
            },
            {
                "original_url": "https://mercadolivre.com.br/produto",
                "affiliate_url": "https://mercadolivre.com/sec/1vt6gtj",
            },
        ]

        results = validator.validate_batch(conversions)
        stats = validator.get_validation_stats(results)

        assert stats["total_conversions"] == 2
        assert "success_rate" in stats
        assert "average_score" in stats

    # ============================================================================
    # TESTES DO CACHE
    # ============================================================================

    @pytest.mark.asyncio
    async def test_cache_initialization(self, cache):
        """Testa inicialização do cache"""
        assert cache is not None
        assert hasattr(cache, "redis_url")
        assert hasattr(cache, "default_ttl")

    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache):
        """Testa operações básicas de cache"""
        # Armazenar
        success = await cache.set(
            "amazon",
            "https://amazon.com.br/produto",
            "https://amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogeek-20",
        )
        assert success

        # Buscar
        cached = await cache.get("amazon", "https://amazon.com.br/produto")
        assert cached is not None
        assert (
            cached["affiliate_url"]
            == "https://amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogeek-20"
        )
        assert cached["platform"] == "amazon"

    @pytest.mark.asyncio
    async def test_cache_exists_delete(self, cache):
        """Testa verificação de existência e remoção"""
        # Armazenar
        await cache.set(
            "shopee", "https://shopee.com.br/produto", "https://s.shopee.com.br/abc123"
        )

        # Verificar existência
        exists = await cache.exists("shopee", "https://shopee.com.br/produto")
        assert exists

        # Remover
        deleted = await cache.delete("shopee", "https://shopee.com.br/produto")
        assert deleted

        # Verificar que foi removido
        exists = await cache.exists("shopee", "https://shopee.com.br/produto")
        assert not exists

    @pytest.mark.asyncio
    async def test_cache_stats(self, cache):
        """Testa estatísticas do cache"""
        # Armazenar alguns itens
        await cache.set("amazon", "url1", "affiliate1")
        await cache.set("mercadolivre", "url2", "affiliate2")
        await cache.set("shopee", "url3", "affiliate3")

        stats = await cache.get_stats()

        assert "total_keys" in stats
        assert "platforms" in stats
        assert "cache_type" in stats

    @pytest.mark.asyncio
    async def test_cache_clear_platform(self, cache):
        """Testa limpeza de plataforma específica"""
        # Armazenar itens de diferentes plataformas
        await cache.set("amazon", "url1", "affiliate1")
        await cache.set("amazon", "url2", "affiliate2")
        await cache.set("mercadolivre", "url3", "affiliate3")

        # Limpar apenas Amazon
        deleted = await cache.clear_platform("amazon")
        assert deleted == 2

        # Verificar que Amazon foi limpa
        exists_amazon = await cache.exists("amazon", "url1")
        assert not exists_amazon

        # Verificar que Mercado Livre ainda existe
        exists_ml = await cache.exists("mercadolivre", "url3")
        assert exists_ml

    # ============================================================================
    # TESTES DOS CONVERSORES ESPECÍFICOS
    # ============================================================================

    def test_amazon_asin_extraction(self):
        """Testa extração de ASIN Amazon"""
        # URL com ASIN
        asin = extract_asin_from_url("https://amazon.com.br/produto/dp/B08N5WRWNW")
        assert asin == "B08N5WRWNW"

        # URL sem ASIN
        asin = extract_asin_from_url("https://amazon.com.br/produto")
        assert asin is None

    def test_mercadolivre_validation(self):
        """Testa validação Mercado Livre"""
        # URL válida
        is_valid, error = validate_ml_url(
            "https://mercadolivre.com.br/produto/p/MLB123"
        )
        assert is_valid

        # URL inválida
        is_valid, error = validate_ml_url("https://mercadolivre.com.br/categoria")
        assert not is_valid

    def test_shopee_validation(self):
        """Testa validação Shopee"""
        # URL válida
        is_valid, error = validate_shopee_url(
            "https://shopee.com.br/iPhone-i.337570318.22498324413"
        )
        assert is_valid

        # URL de categoria (deve ser bloqueada)
        is_valid, error = validate_shopee_url(
            "https://shopee.com.br/oficial/Celulares-cat.11059988"
        )
        assert not is_valid

    def test_magazineluiza_validation(self):
        """Testa validação Magazine Luiza"""
        # URL de vitrine válida
        is_valid, error = validate_magazine_url(
            "https://magazinevoce.com.br/magazinegarimpeirogeek/produto/p/123"
        )
        assert is_valid

        # URL sem vitrine (deve ser bloqueada)
        is_valid, error = validate_magazine_url(
            "https://magazineluiza.com.br/produto/p/123"
        )
        assert not is_valid

    def test_aliexpress_validation(self):
        """Testa validação AliExpress"""
        # URL válida
        is_valid, error = validate_aliexpress_url(
            "https://pt.aliexpress.com/item/1005006756452012.html"
        )
        assert is_valid

        # Shortlink válido
        is_valid, error = validate_aliexpress_url(
            "https://s.click.aliexpress.com/e/_opftn1L"
        )
        assert is_valid

    def test_awin_validation(self):
        """Testa validação Awin"""
        # Loja permitida
        is_valid, store, error = validate_store_domain("https://comfy.com.br/produto")
        assert is_valid
        assert store == "comfy"

        # Loja não permitida
        is_valid, store, error = validate_store_domain(
            "https://loja-invalida.com/produto"
        )
        assert not is_valid

    # ============================================================================
    # TESTES DE INTEGRAÇÃO
    # ============================================================================

    @pytest.mark.asyncio
    async def test_complete_conversion_flow(self, converter, validator):
        """Testa fluxo completo de conversão e validação"""
        # URL de teste
        original_url = "https://amazon.com.br/produto/dp/B08N5WRWNW"

        # Converter
        affiliate_url = await converter.convert_to_affiliate(original_url)
        assert affiliate_url != original_url

        # Validar conversão
        validation = await converter.validate_conversion(original_url, affiliate_url)
        assert validation.status in [ValidationStatus.VALID, ValidationStatus.WARNING]
        assert validation.score > 0.5

    @pytest.mark.asyncio
    async def test_cache_integration(self, converter):
        """Testa integração com cache"""
        # Primeira conversão (sem cache)
        url1 = "https://amazon.com.br/produto/dp/B08N5WRWNW"
        affiliate1 = await converter.convert_to_affiliate(url1)

        # Segunda conversão (deve usar cache)
        affiliate2 = await converter.convert_to_affiliate(url1)

        assert affiliate1 == affiliate2

        # Verificar estatísticas do cache
        stats = await converter.get_cache_stats()
        assert stats["total_keys"] > 0

    @pytest.mark.asyncio
    async def test_batch_processing_with_validation(self, converter):
        """Testa processamento em lote com validação"""
        offers = [
            {"url": "https://amazon.com.br/produto/dp/B08N5WRWNW"},
            {"url": "https://magazineluiza.com.br/produto/p/123"},
            {"url": "https://mercadolivre.com.br/produto/p/MLB123"},
        ]

        # Converter
        converted = await converter.convert_offers_batch(offers)

        # Preparar para validação
        conversions = [
            {"original_url": offer["url"], "affiliate_url": offer["affiliate_url"]}
            for offer in converted
        ]

        # Validar
        validation_results = await converter.validate_batch(conversions)

        assert len(validation_results) == 3
        assert all(r.status != ValidationStatus.ERROR for r in validation_results)

    # ============================================================================
    # TESTES DE PERFORMANCE
    # ============================================================================

    @pytest.mark.asyncio
    async def test_cache_performance(self, cache):
        """Testa performance do cache"""
        import time

        # Teste de escrita
        start_time = time.time()
        for i in range(100):
            await cache.set("test_platform", f"url_{i}", f"affiliate_{i}")
        write_time = time.time() - start_time

        # Teste de leitura
        start_time = time.time()
        for i in range(100):
            await cache.get("test_platform", f"url_{i}")
        read_time = time.time() - start_time

        # Limpar
        await cache.clear_platform("test_platform")

        # Verificar que os tempos são razoáveis
        assert write_time < 5.0  # Máximo 5 segundos para 100 escritas
        assert read_time < 2.0  # Máximo 2 segundos para 100 leituras

    @pytest.mark.asyncio
    async def test_converter_performance(self, converter):
        """Testa performance do conversor"""
        import time

        urls = [
            "https://amazon.com.br/produto/dp/B08N5WRWNW",
            "https://magazineluiza.com.br/produto/p/123",
            "https://mercadolivre.com.br/produto/p/MLB123",
            "https://shopee.com.br/iPhone-i.337570318.22498324413",
            "https://pt.aliexpress.com/item/1005006756452012.html",
        ]

        start_time = time.time()
        for url in urls:
            await converter.convert_to_affiliate(url)
        conversion_time = time.time() - start_time

        # Verificar que a conversão é rápida
        assert conversion_time < 10.0  # Máximo 10 segundos para 5 conversões


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v"])
