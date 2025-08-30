#!/usr/bin/env python3
"""
Testes Automatizados - Sistema de Conversão de Links de Afiliado
"""

import os
import sys
import unittest

# Adicionar src ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.affiliate_converter import AffiliateConverter


class TestAffiliateConverter(unittest.TestCase):
    """Testes para o sistema de conversão de links de afiliado"""

    def setUp(self):
        """Configuração inicial para cada teste"""
        self.converter = AffiliateConverter()

    def test_identify_store_amazon(self):
        """Testa identificação de loja Amazon"""
        url = "https://amazon.com.br/smartphone-samsung"
        store = self.converter.identify_store(url)
        self.assertEqual(store, "amazon")

    def test_identify_store_magalu(self):
        """Testa identificação de loja Magazine Luiza"""
        url = "https://magazineluiza.com.br/fone-jbl"
        store = self.converter.identify_store(url)
        self.assertEqual(store, "magalu")

    def test_identify_store_unknown(self):
        """Testa identificação de loja desconhecida"""
        url = "https://lojadesconhecida.com.br/produto"
        store = self.converter.identify_store(url)
        self.assertIsNone(store)

    def test_convert_to_affiliate_amazon(self):
        """Testa conversão para link de afiliado Amazon"""
        url = "https://amazon.com.br/smartphone-samsung"
        affiliate_url = self.converter.convert_to_affiliate(url)

        self.assertIn("tag=garimpeirogeek-20", affiliate_url)
        self.assertNotEqual(url, affiliate_url)

    def test_convert_to_affiliate_magalu(self):
        """Testa conversão para link de afiliado Magazine Luiza"""
        url = "https://magazineluiza.com.br/fone-jbl"
        affiliate_url = self.converter.convert_to_affiliate(url)

        self.assertIn("partner_id=garimpeirogeek", affiliate_url)
        self.assertNotEqual(url, affiliate_url)

    def test_convert_to_affiliate_disabled_store(self):
        """Testa conversão para loja desabilitada"""
        # Desabilitar Amazon temporariamente
        self.converter.affiliate_configs["amazon"]["enabled"] = False

        url = "https://amazon.com.br/smartphone-samsung"
        affiliate_url = self.converter.convert_to_affiliate(url)

        # Deve retornar URL original se desabilitado
        self.assertEqual(url, affiliate_url)

        # Reabilitar para outros testes
        self.converter.affiliate_configs["amazon"]["enabled"] = True

    def test_convert_offers_batch(self):
        """Testa conversão em lote de ofertas"""
        offers = [
            {
                "id": 1,
                "title": "Smartphone Samsung",
                "url": "https://amazon.com.br/smartphone",
                "price": 1299.99,
            },
            {
                "id": 2,
                "title": "Fone JBL",
                "url": "https://magazineluiza.com.br/fone",
                "price": 199.99,
            },
        ]

        converted_offers = self.converter.convert_offers_batch(offers)

        self.assertEqual(len(converted_offers), 2)
        self.assertIn("affiliate_url", converted_offers[0])
        self.assertIn("affiliate_url", converted_offers[1])
        self.assertIn("original_url", converted_offers[0])
        self.assertIn("original_url", converted_offers[1])

    def test_update_affiliate_config(self):
        """Testa atualização de configuração de afiliado"""
        new_config = {"enabled": False, "tag": "novo-tag"}

        self.converter.update_affiliate_config("amazon", new_config)

        self.assertFalse(self.converter.affiliate_configs["amazon"]["enabled"])
        self.assertEqual(self.converter.affiliate_configs["amazon"]["tag"], "novo-tag")

    def test_get_affiliate_stats(self):
        """Testa obtenção de estatísticas de afiliados"""
        stats = self.converter.get_affiliate_stats()

        self.assertIn("total_stores", stats)
        self.assertIn("enabled_stores", stats)
        self.assertIn("disabled_stores", stats)
        self.assertIn("stores", stats)

        self.assertGreater(stats["total_stores"], 0)
        self.assertGreaterEqual(stats["enabled_stores"], 0)

    def test_test_conversion(self):
        """Testa função de teste de conversão"""
        url = "https://amazon.com.br/smartphone-samsung"
        result = self.converter.test_conversion(url)

        self.assertIn("original_url", result)
        self.assertIn("affiliate_url", result)
        self.assertIn("store", result)
        self.assertIn("converted", result)
        self.assertIn("config", result)

        self.assertEqual(result["original_url"], url)
        self.assertEqual(result["store"], "amazon")
        self.assertTrue(result["converted"])

    def test_invalid_url_handling(self):
        """Testa tratamento de URLs inválidas"""
        invalid_urls = ["not-a-url", "ftp://invalid-protocol.com", "", None]

        for url in invalid_urls:
            if url:
                store = self.converter.identify_store(url)
                self.assertIsNone(store)

                affiliate_url = self.converter.convert_to_affiliate(url)
                self.assertEqual(affiliate_url, url)

    def test_store_configuration_integrity(self):
        """Testa integridade das configurações de lojas"""
        required_keys = ["enabled", "tag", "domains", "param_name"]

        for store, config in self.converter.affiliate_configs.items():
            for key in required_keys:
                self.assertIn(
                    key, config, f"Chave '{key}' ausente na configuração de '{store}'"
                )

            # Verificar tipos de dados
            self.assertIsInstance(config["enabled"], bool)
            self.assertIsInstance(config["tag"], str)
            self.assertIsInstance(config["domains"], list)
            self.assertIsInstance(config["param_name"], str)

            # Verificar valores válidos
            self.assertGreater(len(config["tag"]), 0)
            self.assertGreater(len(config["domains"]), 0)
            self.assertGreater(len(config["param_name"]), 0)


def run_tests():
    """Executa todos os testes"""
    print("🧪 Executando testes do Sistema de Conversão de Links de Afiliado...")

    # Criar suite de testes
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestAffiliateConverter)

    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Resumo dos resultados
    print("\n📊 Resumo dos Testes:")
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
        print("\n🎉 Todos os testes passaram com sucesso!")
        return True
    else:
        print("\n💥 Alguns testes falharam!")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
