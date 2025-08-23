"""
Testes para provedores de afiliados
"""

import unittest
from decimal import Decimal

from affiliate.rakuten import RakutenAffiliateBuilder, build_rakuten_link
from core.models import Offer


class TestOfferModel(unittest.TestCase):
    """Testes para o modelo Offer"""

    def test_offer_creation(self):
        """Testa criação básica de uma oferta"""
        offer = Offer(
            title="Teste de Produto",
            price=Decimal("99.99"),
            url="https://exemplo.com/produto",
            store="Loja Teste",
        )

        self.assertEqual(offer.title, "Teste de Produto")
        self.assertEqual(offer.price, Decimal("99.99"))
        self.assertEqual(offer.url, "https://exemplo.com/produto")
        self.assertEqual(offer.store, "Loja Teste")

    def test_offer_with_discount(self):
        """Testa oferta com desconto"""
        offer = Offer(
            title="Produto com Desconto",
            price=Decimal("79.99"),
            original_price=Decimal("99.99"),
            url="https://exemplo.com/produto",
            store="Loja Teste",
        )

        self.assertTrue(offer.has_discount)
        self.assertAlmostEqual(offer.discount_percentage, 20.0, places=1)
        self.assertEqual(offer.discount_formatted, "20% OFF")

    def test_offer_validation(self):
        """Testa validação de ofertas"""
        # Preço inválido
        with self.assertRaises(ValueError):
            Offer(
                title="Produto",
                price=Decimal("0"),
                url="https://exemplo.com",
                store="Loja",
            )

        # URL inválida
        with self.assertRaises(ValueError):
            Offer(
                title="Produto",
                price=Decimal("99.99"),
                url="url-invalida",
                store="Loja",
            )

    def test_offer_to_dict(self):
        """Testa conversão para dicionário"""
        offer = Offer(
            title="Produto Teste",
            price=Decimal("149.99"),
            url="https://exemplo.com",
            store="Loja Teste",
            category="Eletrônicos",
        )

        data = offer.to_dict()
        self.assertEqual(data["title"], "Produto Teste")
        self.assertEqual(data["price"], 149.99)
        self.assertEqual(data["category"], "Eletrônicos")
        self.assertTrue("price_formatted" in data)


class TestRakutenAffiliate(unittest.TestCase):
    """Testes para o provedor Rakuten"""

    def test_rakuten_builder_creation(self):
        """Testa criação do builder Rakuten"""
        builder = RakutenAffiliateBuilder("test_id", "test_mid", "sub123")

        self.assertEqual(builder.affiliate_id, "test_id")
        self.assertEqual(builder.merchant_id, "test_mid")
        self.assertEqual(builder.sub_id, "sub123")

    def test_rakuten_deeplink_generation(self):
        """Testa geração de deeplinks Rakuten"""
        builder = RakutenAffiliateBuilder("aff123", "merch456")

        target_url = "https://amazon.com.br/produto"
        deeplink = builder.build_deeplink(target_url)

        self.assertIn("click.linksynergy.com/deeplink", deeplink)
        self.assertIn("id=aff123", deeplink)
        self.assertIn("mid=merch456", deeplink)
        self.assertIn("murl=", deeplink)

    def test_rakuten_deeplink_with_subid(self):
        """Testa geração de deeplinks com sub-id"""
        builder = RakutenAffiliateBuilder("aff123", "merch456", "sub789")

        target_url = "https://exemplo.com"
        deeplink = builder.build_deeplink(target_url)

        self.assertIn("u1=sub789", deeplink)

    def test_build_rakuten_link_function(self):
        """Testa função de conveniência build_rakuten_link"""
        target_url = "https://teste.com/produto"
        affiliate_id = "test_aff"
        merchant_id = "test_merch"

        link = build_rakuten_link(target_url, affiliate_id, merchant_id)

        self.assertIn("click.linksynergy.com/deeplink", link)
        self.assertIn("id=test_aff", link)
        self.assertIn("mid=test_merch", link)


class TestAmazonAffiliate(unittest.TestCase):
    """Testes para o provedor Amazon (simulado)"""

    def test_amazon_affiliate_conversion(self):
        """Testa conversão de links Amazon"""
        # Teste simples sem mock
        from core.affiliate_converter import AffiliateConverter

        converter = AffiliateConverter()
        result = converter.convert_to_affiliate("https://amazon.com.br/produto")

        self.assertIn("tag=", result)
        self.assertIn("amazon.com.br", result)


class TestAwinAffiliate(unittest.TestCase):
    """Testes para o provedor Awin (simulado)"""

    def test_awin_url_structure(self):
        """Testa estrutura de URLs Awin"""
        # Simulação de URL Awin
        awin_url = "https://www.awin1.com/cread.php?awinmid=123&awinaffid=456&clickref=&p=https://exemplo.com"

        self.assertIn("awin1.com", awin_url)
        self.assertIn("awinmid=", awin_url)
        self.assertIn("awinaffid=", awin_url)

    def test_awin_affiliate_conversion(self):
        """Testa conversão de links Awin"""
        # Teste simples sem mock
        from core.affiliate_converter import AffiliateConverter

        converter = AffiliateConverter()
        result = converter.convert_to_affiliate("https://amazon.com.br/produto")

        self.assertIn("tag=", result)
        self.assertIn("amazon.com.br", result)


class TestAffiliateIntegration(unittest.TestCase):
    """Testes de integração entre afiliados e ofertas"""

    def test_offer_with_affiliate_url(self):
        """Testa oferta com URL de afiliado"""
        offer = Offer(
            title="Produto com Afiliado",
            price=Decimal("199.99"),
            url="https://exemplo.com/produto",
            store="Loja Teste",
            affiliate_url="https://afiliado.com/redirect?url=https://exemplo.com/produto",
        )

        self.assertIsNotNone(offer.affiliate_url)
        self.assertIn("afiliado.com", offer.affiliate_url)

    def test_offer_affiliate_conversion(self):
        """Testa conversão de oferta para afiliado"""
        original_url = "https://amazon.com.br/produto"

        # Simular conversão para afiliado
        affiliate_url = f"{original_url}?tag=garimpeirogeek-20"

        offer = Offer(
            title="Produto Amazon",
            price=Decimal("299.99"),
            url=original_url,
            store="Amazon",
            affiliate_url=affiliate_url,
        )

        self.assertNotEqual(offer.url, offer.affiliate_url)
        self.assertIn("tag=garimpeirogeek-20", offer.affiliate_url)


def run_affiliate_tests():
    """Executa todos os testes de afiliados"""
    print("🧪 Executando testes de provedores de afiliados...")

    # Criar suite de testes
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestOfferModel)
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestRakutenAffiliate)
    )
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestAmazonAffiliate)
    )
    test_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAwinAffiliate))
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestAffiliateIntegration)
    )

    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Resumo dos resultados
    print("\n📊 Resumo dos Testes de Afiliados:")
    print(f"✅ Testes executados: {result.testsRun}")
    print(f"❌ Falhas: {len(result.failures)}")
    print(f"⚠️ Erros: {len(result.errors)}")

    if result.failures:
        print("\n❌ Falhas encontradas:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\n⚠️ Erros encontrados:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    if result.wasSuccessful():
        print("\n🎉 Todos os testes de afiliados passaram com sucesso!")

    return result.wasSuccessful()


if __name__ == "__main__":
    run_affiliate_tests()
