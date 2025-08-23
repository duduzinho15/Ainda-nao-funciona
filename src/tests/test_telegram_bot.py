#!/usr/bin/env python3
"""
Testes Automatizados - Bot Telegram
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Adicionar src ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.app.bot.telegram_bot import TelegramBot

class TestTelegramBot(unittest.TestCase):
    """Testes para o bot Telegram"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.bot = TelegramBot("test_token")
        
    def test_bot_initialization(self):
        """Testa inicialização do bot"""
        self.assertEqual(self.bot.token, "test_token")
        self.assertIsNotNone(self.bot.affiliate_converter)
        self.assertIsNotNone(self.bot.preferences)
        self.assertIsNotNone(self.bot.database)
        self.assertIsInstance(self.bot.active_users, dict)
        
    def test_get_offers(self):
        """Testa obtenção de ofertas"""
        offers = self.bot.get_offers()
        
        self.assertIsInstance(offers, list)
        self.assertGreater(len(offers), 0)
        
        # Verificar estrutura das ofertas
        for offer in offers:
            self.assertIn("id", offer)
            self.assertIn("title", offer)
            self.assertIn("price", offer)
            self.assertIn("original_price", offer)
            self.assertIn("discount", offer)
            self.assertIn("store", offer)
            self.assertIn("url", offer)
            self.assertIn("category", offer)
            
    def test_convert_offers_to_affiliate(self):
        """Testa conversão de ofertas para links de afiliado"""
        offers = self.bot.get_offers()
        affiliate_offers = self.bot.convert_offers_to_affiliate(offers)
        
        self.assertEqual(len(affiliate_offers), len(offers))
        
        # Verificar se as URLs foram convertidas
        for i, offer in enumerate(affiliate_offers):
            original_url = offers[i]["url"]
            affiliate_url = offer.get("affiliate_url", offer["url"])
            
            # Pelo menos uma URL deve ter sido convertida
            if "amazon" in original_url or "magazineluiza" in original_url:
                self.assertNotEqual(original_url, affiliate_url)
                
    def test_get_stats(self):
        """Testa obtenção de estatísticas"""
        stats = self.bot.get_stats()
        
        self.assertIn("active_users", stats)
        self.assertIn("total_offers", stats)
        self.assertIn("affiliate_conversions", stats)
        self.assertIn("revenue_today", stats)
        
        self.assertIsInstance(stats["active_users"], int)
        self.assertIsInstance(stats["total_offers"], int)
        self.assertIsInstance(stats["affiliate_conversions"], int)
        self.assertIsInstance(stats["revenue_today"], float)
        
    def test_config_structure(self):
        """Testa estrutura da configuração do bot"""
        required_keys = ["auto_posting", "posting_interval", "max_offers_per_message", 
                        "enable_notifications", "language"]
        
        for key in required_keys:
            self.assertIn(key, self.bot.config)
            
        # Verificar tipos de dados
        self.assertIsInstance(self.bot.config["auto_posting"], bool)
        self.assertIsInstance(self.bot.config["posting_interval"], int)
        self.assertIsInstance(self.bot.config["max_offers_per_message"], int)
        self.assertIsInstance(self.bot.config["enable_notifications"], bool)
        self.assertIsInstance(self.bot.config["language"], str)
        
    def test_affiliate_converter_integration(self):
        """Testa integração com o conversor de afiliados"""
        # Testar conversão direta
        test_url = "https://amazon.com.br/test-product"
        converted_url = self.bot.affiliate_converter.convert_to_affiliate(test_url)
        
        self.assertIsInstance(converted_url, str)
        self.assertNotEqual(test_url, converted_url)
        
    def test_preferences_storage_integration(self):
        """Testa integração com o sistema de preferências"""
        # Testar se o sistema de preferências está funcionando
        self.assertIsNotNone(self.bot.preferences)
        
    def test_database_integration(self):
        """Testa integração com o banco de dados"""
        # Testar se o banco de dados está funcionando
        self.assertIsNotNone(self.bot.database)
        
    def test_active_users_management(self):
        """Testa gerenciamento de usuários ativos"""
        # Adicionar usuário de teste
        test_user_id = 12345
        test_user_data = {
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "subscribed": True
        }
        
        self.bot.active_users[test_user_id] = test_user_data
        
        # Verificar se foi adicionado
        self.assertIn(test_user_id, self.bot.active_users)
        self.assertEqual(self.bot.active_users[test_user_id]["username"], "test_user")
        
        # Verificar estatísticas
        stats = self.bot.get_stats()
        self.assertGreaterEqual(stats["active_users"], 1)
        
    def test_config_validation(self):
        """Testa validação de configurações"""
        # Verificar valores válidos
        self.assertGreater(self.bot.config["posting_interval"], 0)
        self.assertGreater(self.bot.config["max_offers_per_message"], 0)
        self.assertIn(self.bot.config["language"], ["pt_BR", "en_US"])
        
    def test_error_handling(self):
        """Testa tratamento de erros"""
        # Testar com token inválido
        try:
            invalid_bot = TelegramBot("")
            # Não deve falhar na criação
            self.assertIsNotNone(invalid_bot)
        except Exception as e:
            self.fail(f"Bot não deveria falhar com token vazio: {e}")
            
    def test_methods_return_types(self):
        """Testa tipos de retorno dos métodos"""
        # get_offers deve retornar lista
        offers = self.bot.get_offers()
        self.assertIsInstance(offers, list)
        
        # get_stats deve retornar dicionário
        stats = self.bot.get_stats()
        self.assertIsInstance(stats, dict)
        
        # convert_offers_to_affiliate deve retornar lista
        affiliate_offers = self.bot.convert_offers_to_affiliate(offers)
        self.assertIsInstance(affiliate_offers, list)

def run_tests():
    """Executa todos os testes"""
    print("🧪 Executando testes do Bot Telegram...")
    
    # Criar suite de testes
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestTelegramBot)
    
    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Resumo dos resultados
    print(f"\n📊 Resumo dos Testes:")
    print(f"✅ Testes executados: {result.testsRun}")
    print(f"❌ Falhas: {len(result.failures)}")
    print(f"⚠️ Erros: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ Falhas encontradas:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
            
    if result.errors:
        print(f"\n⚠️ Erros encontrados:")
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

