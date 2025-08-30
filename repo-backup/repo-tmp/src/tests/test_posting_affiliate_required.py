"""
Testes para validação obrigatória de links de afiliado.
"""

from decimal import Decimal
from unittest.mock import patch

import pytest

from src.core.models import Offer
from src.posting.posting_manager import (
    PostingManager,
    validate_affiliate_url,
)


class TestPostingAffiliateRequired:
    """Testes para validação obrigatória de afiliação"""

    def setup_method(self):
        """Setup para cada teste"""
        self.posting_manager = PostingManager()

        # Oferta de exemplo válida
        self.valid_offer = Offer(
            title='Monitor Gamer LG 34"',
            price=Decimal("1299.99"),
            original_price=Decimal("1599.99"),
            store="KaBuM!",
            url="https://www.kabum.com.br/produto/123",
            affiliate_url="https://www.awin1.com/cread.php?awinmid=17729&awinaffid=2370719&ued=https%3A%2F%2Fwww.kabum.com.br%2Fproduto%2F123",
        )

        # Oferta sem link de afiliado
        self.no_affiliate_offer = Offer(
            title="Produto sem Afiliado",
            price=Decimal("99.99"),
            original_price=Decimal("129.99"),
            store="Loja Teste",
            url="https://exemplo.com/produto",
            affiliate_url=None,
        )

    def test_validate_awin_deeplink_valid(self):
        """Testa validação de deeplink Awin válido"""
        url = "https://www.awin1.com/cread.php?awinmid=17729&awinaffid=2370719&ued=https%3A%2F%2Fwww.kabum.com.br%2Fproduto%2F123"

        result = validate_affiliate_url(url, "awin")

        assert result.is_valid is True
        assert result.platform == "awin"
        assert result.affiliate_url == url
        assert len(result.validation_errors) == 0
        assert result.blocked_reason is None

    def test_validate_awin_deeplink_invalid(self):
        """Testa validação de deeplink Awin inválido"""
        url = "https://www.kabum.com.br/produto/123"  # URL bruta da loja

        result = validate_affiliate_url(url, "awin")

        assert result.is_valid is False
        assert result.platform == "awin"
        assert result.affiliate_url == url
        assert len(result.validation_errors) > 0
        assert result.blocked_reason == "url_bruta_loja"

    def test_validate_shopee_shortlink_valid(self):
        """Testa validação de shortlink Shopee válido"""
        url = "https://s.shopee.com.br/3LGfnEjEXu"

        result = validate_affiliate_url(url, "shopee")

        assert result.is_valid is True
        assert result.platform == "shopee"
        assert result.affiliate_url == url
        assert len(result.validation_errors) == 0

    def test_validate_shopee_shortlink_invalid(self):
        """Testa validação de shortlink Shopee inválido"""
        url = "https://shopee.com.br/produto/123"  # URL bruta da loja

        result = validate_affiliate_url(url, "shopee")

        assert result.is_valid is False
        assert result.blocked_reason == "url_bruta_loja"

    def test_validate_aliexpress_shortlink_valid(self):
        """Testa validação de shortlink AliExpress válido"""
        url = "https://s.click.aliexpress.com/e/_opftn1L"

        result = validate_affiliate_url(url, "aliexpress")

        assert result.is_valid is True
        assert result.platform == "aliexpress"
        assert result.affiliate_url == url
        assert len(result.validation_errors) == 0

    def test_validate_aliexpress_shortlink_invalid(self):
        """Testa validação de shortlink AliExpress inválido"""
        url = "https://pt.aliexpress.com/item/123"  # URL bruta da loja

        result = validate_affiliate_url(url, "aliexpress")

        assert result.is_valid is False
        assert result.blocked_reason == "url_bruta_loja"

    def test_validate_mercadolivre_shortlink_valid(self):
        """Testa validação de shortlink Mercado Livre válido"""
        url = "https://mercadolivre.com/sec/1vt6gtj"

        result = validate_affiliate_url(url, "mercadolivre")

        assert result.is_valid is True
        assert result.platform == "mercadolivre"
        assert result.affiliate_url == url
        assert len(result.validation_errors) == 0

    def test_validate_mercadolivre_social_valid(self):
        """Testa validação de link social Mercado Livre válido"""
        url = "https://www.mercadolivre.com.br/social/garimpeirogeek?matt_word=garimpeirogeek"

        result = validate_affiliate_url(url, "mercadolivre")

        assert result.is_valid is True
        assert result.platform == "mercadolivre"
        assert result.affiliate_url == url
        assert len(result.validation_errors) == 0

    def test_validate_amazon_tag_valid(self):
        """Testa validação de link Amazon com tag válida"""
        url = "https://www.amazon.com.br/produto/dp/123?tag=garimpeirogee-20&ref=link"

        result = validate_affiliate_url(url, "amazon")

        assert result.is_valid is True
        assert result.platform == "amazon"
        assert result.affiliate_url == url
        assert len(result.validation_errors) == 0

    def test_validate_amazon_tag_invalid(self):
        """Testa validação de link Amazon sem tag válida"""
        url = "https://www.amazon.com.br/produto/dp/123"  # Sem tag

        result = validate_affiliate_url(url, "amazon")

        assert result.is_valid is False
        assert result.blocked_reason == "url_bruta_loja"

    def test_validate_magalu_vitrine_valid(self):
        """Testa validação de vitrine Magazine Luiza válida"""
        url = "https://www.magazinevoce.com.br/magazinegarimpeirogeek/produto/123"

        result = validate_affiliate_url(url, "magalu")

        assert result.is_valid is True
        assert result.platform == "magalu"
        assert result.affiliate_url == url
        assert len(result.validation_errors) == 0

    def test_validate_magalu_vitrine_invalid(self):
        """Testa validação de vitrine Magazine Luiza inválida"""
        url = "https://www.magazinevoce.com.br/produto/123"  # Sem vitrine personalizada

        result = validate_affiliate_url(url, "magalu")

        assert result.is_valid is False
        assert result.blocked_reason == "url_bruta_loja"

    def test_validate_empty_affiliate_url(self):
        """Testa validação de link de afiliado vazio"""
        result = validate_affiliate_url("", "awin")

        assert result.is_valid is False
        assert result.blocked_reason == "link_vazio"

    def test_validate_none_affiliate_url(self):
        """Testa validação de link de afiliado None"""
        result = validate_affiliate_url(None, "awin")  # type: ignore

        assert result.is_valid is False
        assert result.blocked_reason == "link_vazio"

    def test_validate_unsupported_platform(self):
        """Testa validação de plataforma não suportada"""
        result = validate_affiliate_url("https://exemplo.com", "plataforma_inexistente")

        assert result.is_valid is False
        assert result.blocked_reason == "plataforma_nao_suportada"

    def test_validate_offer_with_affiliate_url(self):
        """Testa validação de oferta com link de afiliado válido"""
        result = self.posting_manager.validate_offer_for_posting(self.valid_offer)

        assert result.is_valid is True
        assert result.platform == "awin"
        assert len(result.validation_errors) == 0

    def test_validate_offer_without_affiliate_url(self):
        """Testa validação de oferta sem link de afiliado"""
        result = self.posting_manager.validate_offer_for_posting(
            self.no_affiliate_offer
        )

        assert result.is_valid is False
        assert result.blocked_reason == "sem_link_afiliado"
        assert "não possui link de afiliado" in result.validation_errors[0]

    def test_detect_platform_by_store(self):
        """Testa detecção de plataforma por store"""
        # Awin stores
        assert (
            self.posting_manager._detect_platform(
                Offer(
                    title="Teste",
                    price=Decimal("99.99"),
                    store="KaBuM!",
                    url="https://exemplo.com",
                    affiliate_url="",
                )
            )
            == "awin"
        )
        assert (
            self.posting_manager._detect_platform(
                Offer(
                    title="Teste",
                    price=Decimal("99.99"),
                    store="Comfy BR",
                    affiliate_url="",
                    url="https://exemplo.com",
                )
            )
            == "awin"
        )
        assert (
            self.posting_manager._detect_platform(
                Offer(
                    title="Teste",
                    price=Decimal("99.99"),
                    store="LG Brasil",
                    affiliate_url="",
                    url="https://exemplo.com",
                )
            )
            == "awin"
        )

        # Outras plataformas
        assert (
            self.posting_manager._detect_platform(
                Offer(
                    title="Teste",
                    price=Decimal("99.99"),
                    store="Mercado Livre",
                    affiliate_url="",
                    url="https://exemplo.com",
                )
            )
            == "mercadolivre"
        )
        assert (
            self.posting_manager._detect_platform(
                Offer(
                    title="Teste",
                    price=Decimal("99.99"),
                    store="Magazine Luiza",
                    affiliate_url="",
                    url="https://exemplo.com",
                )
            )
            == "magalu"
        )
        assert (
            self.posting_manager._detect_platform(
                Offer(
                    title="Teste",
                    price=Decimal("99.99"),
                    store="Amazon",
                    affiliate_url="",
                    url="https://exemplo.com",
                )
            )
            == "amazon"
        )
        assert (
            self.posting_manager._detect_platform(
                Offer(
                    title="Teste",
                    price=Decimal("99.99"),
                    store="Shopee",
                    affiliate_url="",
                    url="https://exemplo.com",
                )
            )
            == "shopee"
        )
        assert (
            self.posting_manager._detect_platform(
                Offer(
                    title="Teste",
                    price=Decimal("99.99"),
                    store="AliExpress",
                    affiliate_url="",
                    url="https://exemplo.com",
                )
            )
            == "aliexpress"
        )

    def test_detect_platform_by_url(self):
        """Testa detecção de plataforma por URL"""
        # Awin
        offer = Offer(
            title="Teste",
            price=Decimal("99.99"),
            store="Teste",
            url="https://exemplo.com",
            affiliate_url="https://www.awin1.com/cread.php?awinmid=17729&awinaffid=2370719&ued=...",
        )
        assert self.posting_manager._detect_platform(offer) == "awin"

        # Mercado Livre
        offer = Offer(
            title="Teste",
            price=Decimal("99.99"),
            store="Teste",
            url="https://exemplo.com",
            affiliate_url="https://mercadolivre.com/sec/1vt6gtj",
        )
        assert self.posting_manager._detect_platform(offer) == "mercadolivre"

        # Magazine Luiza
        offer = Offer(
            title="Teste",
            price=Decimal("99.99"),
            store="Teste",
            url="https://exemplo.com",
            affiliate_url="https://www.magazinevoce.com.br/magazinegarimpeirogeek/produto/123",
        )
        assert self.posting_manager._detect_platform(offer) == "magalu"

        # Amazon
        offer = Offer(
            title="Teste",
            price=Decimal("99.99"),
            store="Teste",
            url="https://exemplo.com",
            affiliate_url="https://www.amazon.com.br/produto?tag=garimpeirogee-20",
        )
        assert self.posting_manager._detect_platform(offer) == "amazon"

        # Shopee
        offer = Offer(
            title="Teste",
            price=Decimal("99.99"),
            store="Teste",
            url="https://exemplo.com",
            affiliate_url="https://s.shopee.com.br/3LGfnEjEXu",
        )
        assert self.posting_manager._detect_platform(offer) == "shopee"

        # AliExpress
        offer = Offer(
            title="Teste",
            price=Decimal("99.99"),
            store="Teste",
            url="https://exemplo.com",
            affiliate_url="https://s.click.aliexpress.com/e/_opftn1L",
        )
        assert self.posting_manager._detect_platform(offer) == "aliexpress"

    def test_post_offer_valid(self):
        """Testa postagem de oferta válida"""
        with patch.object(self.posting_manager, "_log_successful_posting") as mock_log:
            result = self.posting_manager.post_offer(self.valid_offer, "channel123")

            assert result is True
            mock_log.assert_called_once()

    def test_post_offer_invalid(self):
        """Testa postagem de oferta inválida"""
        with patch.object(self.posting_manager, "_log_blocked_posting") as mock_log:
            with patch.object(
                self.posting_manager, "_send_admin_warning"
            ) as mock_warning:
                result = self.posting_manager.post_offer(
                    self.no_affiliate_offer, "channel123"
                )

                assert result is False
                mock_log.assert_called_once()
                mock_warning.assert_called_once()

    def test_raw_store_url_detection(self):
        """Testa detecção de URLs brutas de lojas"""
        # Awin - URLs brutas devem ser detectadas
        assert (
            self.posting_manager._is_raw_store_url(
                "https://kabum.com.br/produto", "awin"
            )
            is True
        )
        assert (
            self.posting_manager._is_raw_store_url(
                "https://comfy.com.br/produto", "awin"
            )
            is True
        )
        assert (
            self.posting_manager._is_raw_store_url("https://lg.com/produto", "awin")
            is True
        )

        # Awin - Deeplinks válidos NÃO devem ser detectados como brutos
        assert (
            self.posting_manager._is_raw_store_url(
                "https://www.awin1.com/cread.php?awinmid=17729&awinaffid=2370719&ued=...",
                "awin",
            )
            is False
        )

        # Shopee - URLs brutas devem ser detectadas
        assert (
            self.posting_manager._is_raw_store_url(
                "https://shopee.com.br/produto", "shopee"
            )
            is True
        )

        # Shopee - Shortlinks válidos NÃO devem ser detectados como brutos
        assert (
            self.posting_manager._is_raw_store_url(
                "https://s.shopee.com.br/3LGfnEjEXu", "shopee"
            )
            is False
        )

        # AliExpress - URLs brutas devem ser detectadas
        assert (
            self.posting_manager._is_raw_store_url(
                "https://pt.aliexpress.com/item/123", "aliexpress"
            )
            is True
        )

        # AliExpress - Shortlinks válidos NÃO devem ser detectados como brutos
        assert (
            self.posting_manager._is_raw_store_url(
                "https://s.click.aliexpress.com/e/_opftn1L", "aliexpress"
            )
            is False
        )


class TestPostingValidationEdgeCases:
    """Testes para casos extremos de validação"""

    def setup_method(self):
        """Setup para cada teste"""
        self.posting_manager = PostingManager()

    def test_validate_awin_with_special_characters(self):
        """Testa validação de deeplink Awin com caracteres especiais"""
        url = "https://www.awin1.com/cread.php?awinmid=17729&awinaffid=2370719&ued=https%3A%2F%2Fwww.kabum.com.br%2Fproduto%2F123%3Fparam%3Dvalor%26outro%3Dteste%23fragmento"

        result = validate_affiliate_url(url, "awin")

        assert result.is_valid is True
        assert result.platform == "awin"

    def test_validate_awin_with_unicode(self):
        """Testa validação de deeplink Awin com caracteres Unicode"""
        url = "https://www.awin1.com/cread.php?awinmid=17729&awinaffid=2370719&ued=https%3A%2F%2Fwww.comfy.com.br%2Fcadeira-ergonômica-para-escritório"

        result = validate_affiliate_url(url, "awin")

        assert result.is_valid is True
        assert result.platform == "awin"

    def test_validate_platform_case_insensitive(self):
        """Testa se validação é case-insensitive para plataforma"""
        url = "https://www.awin1.com/cread.php?awinmid=17729&awinaffid=2370719&ued=..."

        # Deve funcionar independente do case
        result1 = validate_affiliate_url(url, "AWIN")
        result2 = validate_affiliate_url(url, "awin")
        result3 = validate_affiliate_url(url, "Awin")

        assert result1.is_valid == result2.is_valid == result3.is_valid is True

    def test_validation_stats(self):
        """Testa se estatísticas de validação são retornadas"""
        stats = self.posting_manager.get_validation_stats()

        # Deve retornar dicionário com estatísticas
        assert isinstance(stats, dict)
        assert "blocked_posts" in stats
        assert "successful_posts" in stats
        assert "total_attempts" in stats
        assert "block_rate" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
