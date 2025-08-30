"""
Testes E2E para validação completa do sistema de afiliados.
Valida fluxo completo: URL → conversor → validador → PostingManager
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.affiliate_validator import AffiliateValidator
from core.affiliate_converter import AffiliateConverter
from core.affiliate_cache import AffiliateCache
from core.models import Offer
from tests.data.affiliate_examples import (
    VALID_URLS,
    INVALID_URLS,
    SHOPEE_EXAMPLES,
    MERCADOLIVRE_EXAMPLES,
    AMAZON_EXAMPLES,
    MAGALU_EXAMPLES,
    ALIEXPRESS_EXAMPLES,
    AWIN_EXAMPLES,
    RAKUTEN_EXAMPLES
)


class TestAffiliatesE2E:
    """Testes E2E para validação completa do sistema de afiliados."""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup para todos os testes."""
        self.validator = AffiliateValidator()
        self.converter = AffiliateConverter()
        self.cache = AffiliateCache()
        
        # Conectar cache
        await self.cache.connect()
        
        yield
        
        # Cleanup
        await self.cache.disconnect()
    
    @pytest.mark.asyncio
    async def test_valid_urls_pass_validation(self):
        """Teste: URLs válidas devem passar na validação."""
        print("\n🔍 Testando URLs válidas...")
        
        for platform, urls in VALID_URLS.items():
            print(f"  📱 {platform}: {len(urls)} URLs")
            
            for url in urls:
                result = await self.validator.validate_url(url)
                
                assert result.is_valid, f"URL válida rejeitada: {url}"
                assert result.platform == platform, f"Plataforma incorreta para {url}"
                assert result.score >= 80, f"Score baixo para URL válida: {url} (score: {result.score})"
                
                print(f"    ✅ {url[:50]}... - Score: {result.score}")
        
        print("  🎯 Todas as URLs válidas passaram na validação!")
    
    @pytest.mark.asyncio
    async def test_invalid_urls_are_blocked(self):
        """Teste: URLs inválidas devem ser bloqueadas."""
        print("\n🚫 Testando bloqueio de URLs inválidas...")
        
        for platform, urls in INVALID_URLS.items():
            print(f"  📱 {platform}: {len(urls)} URLs inválidas")
            
            for url in urls:
                result = await self.validator.validate_url(url)
                
                assert not result.is_valid, f"URL inválida não foi bloqueada: {url}"
                assert result.score < 50, f"Score alto para URL inválida: {url} (score: {result.score})"
                
                print(f"    ❌ {url[:50]}... - Score: {result.score} - BLOQUEADA")
        
        print("  🎯 Todas as URLs inválidas foram bloqueadas!")
    
    @pytest.mark.asyncio
    async def test_shopee_blocking(self):
        """Teste: Shopee deve bloquear categorias inválidas."""
        print("\n🛒 Testando bloqueio Shopee...")
        
        for url in SHOPEE_EXAMPLES["blocked"]:
            result = await self.validator.validate_url(url)
            
            assert not result.is_valid, f"URL Shopee inválida não foi bloqueada: {url}"
            assert "categoria bloqueada" in result.reason.lower() or result.score < 30
            
            print(f"    ❌ {url[:50]}... - BLOQUEADA: {result.reason}")
        
        print("  🎯 Shopee bloqueando categorias inválidas corretamente!")
    
    @pytest.mark.asyncio
    async def test_mercadolivre_blocking(self):
        """Teste: Mercado Livre deve bloquear produtos brutos."""
        print("\n🛒 Testando bloqueio Mercado Livre...")
        
        for url in MERCADOLIVRE_EXAMPLES["blocked"]:
            result = await self.validator.validate_url(url)
            
            assert not result.is_valid, f"URL ML inválida não foi bloqueada: {url}"
            assert "produto bruto" in result.reason.lower() or result.score < 30
            
            print(f"    ❌ {url[:50]}... - BLOQUEADA: {result.reason}")
        
        print("  🎯 Mercado Livre bloqueando produtos brutos corretamente!")
    
    @pytest.mark.asyncio
    async def test_amazon_blocking(self):
        """Teste: Amazon deve bloquear URLs sem ASIN."""
        print("\n🛒 Testando bloqueio Amazon...")
        
        for url in AMAZON_EXAMPLES["blocked"]:
            result = await self.validator.validate_url(url)
            
            assert not result.is_valid, f"URL Amazon inválida não foi bloqueada: {url}"
            assert "asin" in result.reason.lower() or result.score < 30
            
            print(f"    ❌ {url[:50]}... - BLOQUEADA: {result.reason}")
        
        print("  🎯 Amazon bloqueando URLs sem ASIN corretamente!")
    
    @pytest.mark.asyncio
    async def test_conversion_flow(self):
        """Teste: Fluxo completo de conversão."""
        print("\n🔄 Testando fluxo completo de conversão...")
        
        for platform, urls in VALID_URLS.items():
            print(f"  📱 {platform}: testando conversão")
            
            for url in urls[:3]:  # Testar apenas 3 URLs por plataforma
                # 1. Validar URL
                validation = await self.validator.validate_url(url)
                assert validation.is_valid, f"URL falhou na validação: {url}"
                
                # 2. Converter para afiliado
                conversion = await self.converter.convert_to_affiliate(url)
                assert conversion.is_success, f"Conversão falhou: {url}"
                assert conversion.affiliate_url != url, f"URL não foi convertida: {url}"
                
                # 3. Validar conversão
                validation_result = await self.converter.validate_conversion(url, conversion.affiliate_url)
                assert validation_result.is_valid, f"Conversão inválida: {url}"
                
                print(f"    ✅ {url[:30]}... → {conversion.affiliate_url[:30]}...")
        
        print("  🎯 Fluxo completo de conversão funcionando!")
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """Teste: Cache deve funcionar corretamente."""
        print("\n💾 Testando funcionalidade do cache...")
        
        # Testar cache de validação
        test_url = list(VALID_URLS.values())[0][0]
        
        # Primeira validação (sem cache)
        result1 = await self.validator.validate_url(test_url)
        assert result1.is_valid
        
        # Segunda validação (com cache)
        result2 = await self.validator.validate_url(test_url)
        assert result2.is_valid
        assert result1.score == result2.score
        
        # Verificar estatísticas do cache
        stats = await self.cache.get_stats()
        assert stats["total_requests"] > 0
        assert stats["cache_hits"] > 0
        
        print(f"    ✅ Cache funcionando: {stats['cache_hits']}/{stats['total_requests']} hits")
        print("  🎯 Cache funcionando corretamente!")
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Teste: Rate limiting deve funcionar."""
        print("\n⏱️ Testando rate limiting...")
        
        # Simular múltiplas requisições rápidas
        test_urls = list(VALID_URLS.values())[0][:5]
        
        start_time = asyncio.get_event_loop().time()
        
        # Executar validações em paralelo
        tasks = [self.validator.validate_url(url) for url in test_urls]
        results = await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        # Todas devem ter sucesso
        assert all(r.is_valid for r in results)
        
        # Deve respeitar rate limiting (mínimo 0.1s entre requisições)
        expected_min_duration = len(test_urls) * 0.1
        assert duration >= expected_min_duration, f"Rate limiting não respeitado: {duration}s < {expected_min_duration}s"
        
        print(f"    ✅ Rate limiting respeitado: {duration:.2f}s para {len(test_urls)} URLs")
        print("  🎯 Rate limiting funcionando corretamente!")
    
    @pytest.mark.asyncio
    async def test_deduplication(self):
        """Teste: Deduplicação deve funcionar."""
        print("\n🔄 Testando deduplicação...")
        
        # URLs duplicadas
        duplicate_urls = [
            "https://www.amazon.com.br/product/123",
            "https://www.amazon.com.br/product/123",
            "https://www.amazon.com.br/product/123"
        ]
        
        results = []
        for url in duplicate_urls:
            result = await self.validator.validate_url(url)
            results.append(result)
        
        # Todas devem ter o mesmo resultado
        assert all(r.is_valid == results[0].is_valid for r in results)
        assert all(r.score == results[0].score for r in results)
        
        print("    ✅ Deduplicação funcionando: URLs duplicadas retornam mesmo resultado")
        print("  🎯 Deduplicação funcionando corretamente!")
    
    @pytest.mark.asyncio
    async def test_integration_all_modules(self):
        """Teste: Integração entre todos os módulos."""
        print("\n🔗 Testando integração entre módulos...")
        
        # Criar oferta de teste
        test_url = list(VALID_URLS.values())[0][0]
        
        # 1. Validar URL
        validation = await self.validator.validate_url(test_url)
        assert validation.is_valid
        
        # 2. Converter para afiliado
        conversion = await self.converter.convert_to_affiliate(test_url)
        assert conversion.is_success
        
        # 3. Criar oferta
        offer = Offer(
            title="Produto Teste",
            current_price=99.99,
            original_price=199.99,
            discount_percentage=50,
            affiliate_url=conversion.affiliate_url,
            platform=validation.platform,
            category="Teste",
            store="Loja Teste"
        )
        
        # 4. Validar oferta
        assert offer.title == "Produto Teste"
        assert offer.current_price == 99.99
        assert offer.affiliate_url == conversion.affiliate_url
        assert offer.platform == validation.platform
        
        print("    ✅ Todos os módulos integrados e funcionando")
        print("  🎯 Integração entre módulos funcionando perfeitamente!")
    
    @pytest.mark.asyncio
    async def test_performance_validation(self):
        """Teste: Performance da validação."""
        print("\n⚡ Testando performance da validação...")
        
        # Testar múltiplas URLs para medir performance
        all_urls = []
        for urls in VALID_URLS.values():
            all_urls.extend(urls[:5])  # 5 URLs por plataforma
        
        start_time = asyncio.get_event_loop().time()
        
        # Executar validações em paralelo
        tasks = [self.validator.validate_url(url) for url in all_urls]
        results = await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        # Calcular métricas
        total_urls = len(all_urls)
        successful_validations = sum(1 for r in results if r.is_valid)
        avg_time_per_url = duration / total_urls
        
        print(f"    📊 Total URLs: {total_urls}")
        print(f"    📊 Validações bem-sucedidas: {successful_validations}")
        print(f"    📊 Tempo total: {duration:.2f}s")
        print(f"    📊 Tempo médio por URL: {avg_time_per_url:.3f}s")
        
        # Critérios de performance
        assert duration < 10, f"Validação muito lenta: {duration}s > 10s"
        assert avg_time_per_url < 0.5, f"Tempo por URL muito alto: {avg_time_per_url}s > 0.5s"
        assert successful_validations / total_urls >= 0.95, "Taxa de sucesso muito baixa"
        
        print("  🎯 Performance da validação dentro dos padrões!")
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Teste: Tratamento de erros."""
        print("\n⚠️ Testando tratamento de erros...")
        
        # URLs malformadas
        malformed_urls = [
            "not_a_url",
            "http://",
            "https://invalid-domain.xyz",
            "ftp://invalid-protocol.com",
            ""
        ]
        
        for url in malformed_urls:
            try:
                result = await self.validator.validate_url(url)
                # Deve retornar resultado inválido, não gerar exceção
                assert not result.is_valid
                assert result.score == 0
                print(f"    ✅ {url} tratado corretamente (score: {result.score})")
            except Exception as e:
                pytest.fail(f"Exceção não tratada para {url}: {e}")
        
        print("  🎯 Tratamento de erros funcionando corretamente!")


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v", "-s"])
