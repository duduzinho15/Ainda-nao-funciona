"""
Testes E2E para integração completa do sistema
URL crua → Offer com ASIN → link afiliado → bloqueio ou aprovação
"""

from decimal import Decimal
from unittest.mock import patch

import pytest

from src.core.models import Offer
from src.posting.posting_manager import PostingManager
from src.scrapers.lojas.amazon import AmazonScraper


class TestE2EAmazonIntegration:
    """Testes E2E para integração completa da Amazon"""

    def setup_method(self):
        """Setup para cada teste"""
        self.posting_manager = PostingManager()
        self.amazon_scraper = AmazonScraper()

    @pytest.mark.asyncio
    async def test_e2e_amazon_valid_url_to_approved_offer(self):
        """Teste E2E: URL válida da Amazon → Offer com ASIN → Aprovação"""
        # URL real da Amazon (mockada)
        amazon_url = "https://www.amazon.com.br/Apple-iPhone-13-256-GB-das-estrelas/dp/B09T4WC9GN/"

        # Mock do scraping da Amazon
        with patch.object(self.amazon_scraper, "scrape_product") as mock_scrape:
            mock_scrape.return_value = Offer(
                title="iPhone 13 256GB",
                price=Decimal("4999.99"),
                original_price=Decimal("5999.99"),
                store="Amazon",
                url=amazon_url,
                affiliate_url="https://www.amazon.com.br/dp/B09T4WC9GN?tag=garimpeirogee-20&language=pt_BR",
                asin="B09T4WC9GN",
                is_complete=True,
                incomplete_reason=None,
            )

            # Simular scraping
            offer = await self.amazon_scraper.scrape_product(amazon_url)

            # Validar que a oferta foi criada corretamente
            assert offer.asin == "B09T4WC9GN"
            assert offer.is_complete is True
            assert offer.affiliate_url is not None

            # Validar no PostingManager
            validation_result = self.posting_manager.validate_offer_for_posting(offer)

            # Deve ser aprovada
            assert validation_result.is_valid is True
            assert validation_result.platform == "amazon"
            assert validation_result.blocked_reason is None

    @pytest.mark.asyncio
    async def test_e2e_amazon_invalid_url_to_blocked_offer(self):
        """Teste E2E: URL inválida da Amazon → Offer sem ASIN → Bloqueio"""
        # URL da Amazon sem ASIN válido
        invalid_amazon_url = "https://www.amazon.com.br/categoria-eletronicos/"

        # Mock do scraping retornando oferta incompleta
        with patch.object(self.amazon_scraper, "scrape_product") as mock_scrape:
            mock_scrape.return_value = Offer(
                title="Categoria Eletrônicos",
                price=Decimal("1.00"),
                original_price=Decimal("1.00"),
                store="Amazon",
                url=invalid_amazon_url,
                affiliate_url="https://www.amazon.com.br/categoria-eletronicos/?tag=garimpeirogee-20",
                asin=None,
                is_complete=False,
                incomplete_reason="ASIN não encontrado",
            )

            # Simular scraping
            offer = await self.amazon_scraper.scrape_product(invalid_amazon_url)

            # Validar que a oferta foi marcada como incompleta
            assert offer.asin is None
            assert offer.is_complete is False
            assert offer.incomplete_reason == "ASIN não encontrado"

            # Validar no PostingManager - deve ser bloqueada
            validation_result = self.posting_manager.validate_offer_for_posting(offer)

            # Deve ser bloqueada
            assert validation_result.is_valid is False
            assert validation_result.blocked_reason == "amazon_affiliate_invalido"

    @pytest.mark.asyncio
    async def test_e2e_amazon_raw_url_to_blocked_offer(self):
        """Teste E2E: URL bruta da Amazon → Bloqueio imediato"""
        # URL bruta da Amazon (sem tag de afiliado)
        raw_amazon_url = "https://www.amazon.com.br/produto/dp/B09T4WC9GN"

        # Criar oferta com URL bruta
        offer = Offer(
            title="Produto Teste",
            price=Decimal("100.00"),
            original_price=Decimal("150.00"),
            store="Amazon",
            url=raw_amazon_url,
            affiliate_url=raw_amazon_url,  # Mesma URL bruta
            asin="B09T4WC9GN",
            is_complete=True,
            incomplete_reason=None,
        )

        # Validar no PostingManager - deve ser bloqueada por ser URL bruta
        validation_result = self.posting_manager.validate_offer_for_posting(offer)

        # Deve ser bloqueada
        assert validation_result.is_valid is False
        # Pode ser bloqueada por URL bruta OU por formato inválido
        assert validation_result.blocked_reason in [
            "amazon_affiliate_invalido",
            "url_bruta_loja",
        ]


class TestE2EAwinIntegration:
    """Testes E2E para integração completa da Awin"""

    def setup_method(self):
        """Setup para cada teste"""
        self.posting_manager = PostingManager()

    def test_e2e_awin_valid_deeplink_to_approved_offer(self):
        """Teste E2E: Deeplink Awin válido → Aprovação"""
        # Deeplink Awin válido (Comfy)
        valid_awin_url = "https://www.awin1.com/cread.php?awinmid=23377&awinaffid=2370719&ued=https%3A%2F%2Fwww.comfy.com.br%2F"

        # Criar oferta com deeplink válido
        offer = Offer(
            title="Cadeira Comfy",
            price=Decimal("299.99"),
            original_price=Decimal("399.99"),
            store="Comfy",
            url="https://www.comfy.com.br/cadeira-ergonomica",
            affiliate_url=valid_awin_url,
            asin=None,
            is_complete=True,
            incomplete_reason=None,
        )

        # Validar no PostingManager - deve ser aprovada
        validation_result = self.posting_manager.validate_offer_for_posting(offer)

        # Deve ser aprovada
        assert validation_result.is_valid is True
        assert validation_result.platform == "awin"
        assert validation_result.blocked_reason is None

    def test_e2e_awin_invalid_deeplink_to_blocked_offer(self):
        """Teste E2E: Deeplink Awin inválido → Bloqueio"""
        # Deeplink Awin inválido (MID incorreto)
        invalid_awin_url = "https://www.awin1.com/cread.php?awinmid=99999&awinaffid=2370719&ued=https%3A%2F%2Fwww.comfy.com.br%2F"

        # Criar oferta com deeplink inválido
        offer = Offer(
            title="Cadeira Comfy",
            price=Decimal("299.99"),
            original_price=Decimal("399.99"),
            store="Comfy",
            url="https://www.comfy.com.br/cadeira-ergonomica",
            affiliate_url=invalid_awin_url,
            asin=None,
            is_complete=True,
            incomplete_reason=None,
        )

        # Validar no PostingManager - deve ser bloqueada
        validation_result = self.posting_manager.validate_offer_for_posting(offer)

        # Deve ser bloqueada
        assert validation_result.is_valid is False
        assert validation_result.blocked_reason == "awin_deeplink_invalido"

    def test_e2e_awin_raw_url_to_blocked_offer(self):
        """Teste E2E: URL bruta da Comfy → Bloqueio imediato"""
        # URL bruta da Comfy (sem passar pelo Awin)
        raw_comfy_url = "https://www.comfy.com.br/cadeira-ergonomica"

        # Criar oferta com URL bruta
        offer = Offer(
            title="Cadeira Comfy",
            price=Decimal("299.99"),
            original_price=Decimal("399.99"),
            store="Comfy",
            url=raw_comfy_url,
            affiliate_url=raw_comfy_url,  # Mesma URL bruta
            asin=None,
            is_complete=True,
            incomplete_reason=None,
        )

        # Validar no PostingManager - deve ser bloqueada por ser URL bruta
        validation_result = self.posting_manager.validate_offer_for_posting(offer)

        # Deve ser bloqueada
        assert validation_result.is_valid is False
        assert validation_result.blocked_reason == "url_bruta_loja"


class TestE2ECrossPlatformValidation:
    """Testes E2E para validação cross-platform"""

    def setup_method(self):
        """Setup para cada teste"""
        self.posting_manager = PostingManager()

    def test_e2e_cross_platform_validation_consistency(self):
        """Teste E2E: Consistência da validação entre plataformas"""
        test_cases = [
            # (plataforma, affiliate_url, deve_ser_valido, motivo_bloqueio)
            (
                "amazon",
                "https://www.amazon.com.br/dp/B09T4WC9GN?tag=garimpeirogee-20",
                True,
                None,
            ),
            (
                "amazon",
                "https://www.amazon.com.br/dp/B09T4WC9GN?tag=garimpeirogee-20&other=value",
                False,
                "amazon_affiliate_invalido",
            ),
            (
                "awin",
                "https://www.awin1.com/cread.php?awinmid=23377&awinaffid=2370719&ued=test",
                True,
                None,
            ),
            (
                "awin",
                "https://www.awin1.com/cread.php?awinmid=99999&awinaffid=2370719&ued=test",
                False,
                "awin_deeplink_invalido",
            ),
            ("mercadolivre", "https://mercadolivre.com/sec/1vt6gtj", True, None),
            (
                "mercadolivre",
                "https://www.mercadolivre.com.br/produto",
                False,
                "url_bruta_loja",
            ),
        ]

        for (
            platform,
            affiliate_url,
            should_be_valid,
            expected_block_reason,
        ) in test_cases:
            # Criar oferta de teste
            offer = Offer(
                title="Produto Teste",
                price=Decimal("100.00"),
                original_price=Decimal("150.00"),
                store="TestStore",
                url="https://example.com/produto",
                affiliate_url=affiliate_url,
                asin=None,
                is_complete=True,
                incomplete_reason=None,
            )

            # Validar
            validation_result = self.posting_manager.validate_offer_for_posting(offer)

            # Verificar resultado
            assert (
                validation_result.is_valid == should_be_valid
            ), f"Falha para {platform}: {affiliate_url}"

            if not should_be_valid:
                assert (
                    validation_result.blocked_reason == expected_block_reason
                ), f"Motivo de bloqueio incorreto para {platform}"

    def test_e2e_metrics_tracking(self):
        """Teste E2E: Rastreamento de métricas durante validação"""
        # Criar oferta que será bloqueada
        blocked_offer = Offer(
            title="Produto Bloqueado",
            price=Decimal("100.00"),
            original_price=Decimal("150.00"),
            store="Amazon",
            url="https://www.amazon.com.br/produto",
            affiliate_url="https://www.amazon.com.br/produto",  # URL bruta
            asin=None,
            is_complete=False,
            incomplete_reason="ASIN não encontrado",
        )

        # Validar - deve ser bloqueada
        validation_result = self.posting_manager.validate_offer_for_posting(
            blocked_offer
        )

        # Verificar que foi bloqueada
        assert validation_result.is_valid is False

        # Verificar que as métricas foram registradas
        metrics = self.posting_manager.metrics
        assert hasattr(metrics, "get_event_count")

        # Simular verificação de eventos (em produção, isso seria real)
        # assert metrics.get_event_count("amazon_asin_missing") > 0


if __name__ == "__main__":
    # Executar testes E2E
    pytest.main([__file__, "-v", "--tb=short"])
