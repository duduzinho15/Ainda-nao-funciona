"""
Teste E2E para pipeline KaBuM! -> Offer -> Afiliado Awin
"""

import asyncio
import unittest
from decimal import Decimal

from src.core.models import Offer
from src.scrapers.lojas.kabum import kabum_scraper


class TestE2EKabum(unittest.TestCase):
    """Teste end-to-end do pipeline KaBuM!"""

    def test_kabum_scraper_returns_offers(self):
        """Testa se o scraper KaBuM! retorna objetos Offer válidos"""
        # Executar scraping
        offers = asyncio.run(kabum_scraper.scrape(query="monitor", max_results=5))

        # Verificar se retornou ofertas
        self.assertIsInstance(offers, list)
        self.assertGreater(len(offers), 0)

        # Verificar se cada oferta é um objeto Offer válido
        for offer in offers:
            self.assertIsInstance(offer, Offer)
            self.assertIsInstance(offer.title, str)
            self.assertIsInstance(offer.price, Decimal)
            self.assertIsInstance(offer.url, str)
            self.assertEqual(offer.store, "KaBuM!")

            # Verificar se tem URL de afiliado
            self.assertIsInstance(offer.affiliate_url, str)
            self.assertIn("awin1.com", offer.affiliate_url)
            self.assertIn("awinmid=17729", offer.affiliate_url)
            self.assertIn("awinaffid=2370719", offer.affiliate_url)

    def test_affiliate_url_structure(self):
        """Testa se a URL de afiliado Awin está correta"""
        # URL de exemplo do KaBuM!
        test_url = (
            "https://www.kabum.com.br/produto/472908/monitor-gamer-curvo-lg-ultragear"
        )

        # Gerar URL de afiliado
        affiliate_url = kabum_scraper.get_affiliate_url(test_url)

        # Verificar estrutura
        self.assertIn("https://www.awin1.com/cread.php", affiliate_url)
        self.assertIn("awinmid=17729", affiliate_url)
        self.assertIn("awinaffid=2370719", affiliate_url)
        self.assertIn("ued=", affiliate_url)

        # Verificar se a URL original está codificada (pode variar a codificação)
        self.assertIn("kabum.com.br", affiliate_url)
        self.assertIn("produto", affiliate_url)

    def test_offer_data_integrity(self):
        """Testa integridade dos dados das ofertas"""
        offers = asyncio.run(kabum_scraper.scrape(max_results=2))

        for offer in offers:
            # Verificar campos obrigatórios
            self.assertTrue(offer.title)
            self.assertGreater(offer.price, 0)
            self.assertTrue(offer.url)

            # Verificar campos opcionais
            if offer.original_price:
                self.assertGreater(offer.original_price, offer.price)

            if offer.discount_percentage:
                self.assertGreaterEqual(offer.discount_percentage, 0)
                self.assertLessEqual(offer.discount_percentage, 100)

            # Verificar se tem imagem
            if offer.image_url:
                self.assertIn("images.kabum.com.br", offer.image_url)

    def test_no_archived_scrapers_referenced(self):
        """Testa se nenhum scraper arquivado é referenciado"""
        # Verificar que o scraper KaBuM! não importa scrapers arquivados
        scraper_module = kabum_scraper.__class__.__module__

        # Lista de scrapers arquivados
        archived_scrapers = [
            "americanas_scraper",
            "submarino_scraper",
            "casas_bahia_scraper",
            "fast_shop_scraper",
            "ricardo_eletro_scraper",
        ]

        # Verificar que nenhum scraper arquivado é importado
        for archived in archived_scrapers:
            self.assertNotIn(archived, str(scraper_module))


if __name__ == "__main__":
    unittest.main()
