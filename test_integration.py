#!/usr/bin/env python3
"""
Script de Teste de Integração para o Sistema de Recomendações de Ofertas Telegram
Testa todos os módulos implementados e suas funcionalidades
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTester:
    """Classe para testar a integração de todos os sistemas"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
    
    async def test_cache_system(self):
        """Testa o sistema de cache"""
        try:
            logger.info("🧪 Testando Sistema de Cache...")
            
            import cache_system
            
            # Testa cache básico
            cache_system.cache.set("test_key", "test_value", 10)
            result = cache_system.cache.get("test_key")
            
            if result == "test_value":
                logger.info("✅ Cache básico funcionando")
                self.test_results['cache_basic'] = True
            else:
                logger.error("❌ Cache básico falhou")
                self.test_results['cache_basic'] = False
            
            # Testa decorator de cache
            @cache_system.cached(ttl=60, key_prefix="test")
            def test_function(x, y):
                return x + y
            
            result1 = test_function(1, 2)
            result2 = test_function(1, 2)  # Deve vir do cache
            
            if result1 == result2 == 3:
                logger.info("✅ Decorator de cache funcionando")
                self.test_results['cache_decorator'] = True
            else:
                logger.error("❌ Decorator de cache falhou")
                self.test_results['cache_decorator'] = False
            
            # Testa estatísticas
            stats = cache_system.cache.get_stats()
            if isinstance(stats, dict):
                logger.info("✅ Estatísticas de cache funcionando")
                self.test_results['cache_stats'] = True
            else:
                logger.error("❌ Estatísticas de cache falharam")
                self.test_results['cache_stats'] = False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste do sistema de cache: {e}")
            self.test_results['cache_system'] = False
    
    async def test_rate_limiter(self):
        """Testa o sistema de rate limiting"""
        try:
            logger.info("🧪 Testando Sistema de Rate Limiting...")
            
            import rate_limiter
            
            # Testa rate limiter básico
            limiter = rate_limiter.IntelligentRateLimiter()
            
            # Testa se as estratégias foram configuradas
            if len(limiter.strategies) > 0:
                logger.info("✅ Rate limiting básico funcionando")
                self.test_results['rate_limiter_basic'] = True
            else:
                logger.error("❌ Rate limiting básico falhou")
                self.test_results['rate_limiter_basic'] = False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste do rate limiter: {e}")
            self.test_results['rate_limiter'] = False
    
    async def test_health_monitor(self):
        """Testa o sistema de monitoramento de saúde"""
        try:
            logger.info("🧪 Testando Sistema de Monitoramento de Saúde...")
            
            import health_monitor
            
            # Testa health checker básico
            checker = health_monitor.HealthChecker(
                name="test_service",
                service_type=health_monitor.ServiceType.API,
                check_function=lambda: True,
                interval=5
            )
            
            if checker.name == "test_service":
                logger.info("✅ Health checker básico funcionando")
                self.test_results['health_checker'] = True
            else:
                logger.error("❌ Health checker básico falhou")
                self.test_results['health_checker'] = False
            
            # Testa health monitor
            monitor = health_monitor.HealthMonitor()
            monitor.add_checker("test_checker", health_monitor.ServiceType.API, lambda: True)
            
            if len(monitor.checkers) == 1:
                logger.info("✅ Health monitor funcionando")
                self.test_results['health_monitor'] = True
            else:
                logger.error("❌ Health monitor falhou")
                self.test_results['health_monitor'] = False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste do health monitor: {e}")
            self.test_results['health_monitor'] = False
    
    async def test_performance_metrics(self):
        """Testa o sistema de métricas de performance"""
        try:
            logger.info("🧪 Testando Sistema de Métricas de Performance...")
            
            import performance_metrics
            
            # Testa métricas básicas
            performance_metrics.record_metric("test.counter", 1, {"test": "value"})
            performance_metrics.record_metric("test.gauge", 100, {"test": "value"})
            
            # Testa dashboard
            dashboard = performance_metrics.get_metrics_dashboard()
            if isinstance(dashboard, dict):
                logger.info("✅ Dashboard de métricas funcionando")
                self.test_results['performance_dashboard'] = True
            else:
                logger.error("❌ Dashboard de métricas falhou")
                self.test_results['performance_dashboard'] = False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste das métricas de performance: {e}")
            self.test_results['performance_metrics'] = False
    
    async def test_user_categories(self):
        """Testa o sistema de categorias de usuários"""
        try:
            logger.info("🧪 Testando Sistema de Categorias de Usuários...")
            
            import user_categories
            
            # Testa adição de categoria
            success = user_categories.add_user_category(12345, "test_category", 5)
            if success:
                logger.info("✅ Adição de categoria funcionando")
                self.test_results['user_categories_add'] = True
            else:
                logger.error("❌ Adição de categoria falhou")
                self.test_results['user_categories_add'] = False
            
            # Testa obtenção de categorias
            categories = user_categories.get_user_categories(12345)
            if isinstance(categories, list):
                logger.info("✅ Obtenção de categorias funcionando")
                self.test_results['user_categories_get'] = True
            else:
                logger.error("❌ Obtenção de categorias falhou")
                self.test_results['user_categories_get'] = False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste das categorias de usuários: {e}")
            self.test_results['user_categories'] = False
    
    async def test_price_history(self):
        """Testa o sistema de histórico de preços"""
        try:
            logger.info("🧪 Testando Sistema de Histórico de Preços...")
            
            import price_history
            
            # Testa adição de ponto de preço
            success = price_history.price_history_manager.add_price_point(
                "test_product", "test_store", 100.0, "test_url"
            )
            if success:
                logger.info("✅ Adição de ponto de preço funcionando")
                self.test_results['price_history_add'] = True
            else:
                logger.error("❌ Adição de ponto de preço falhou")
                self.test_results['price_history_add'] = False
            
            # Testa obtenção de histórico
            history = price_history.price_history_manager.get_price_history("test_product", "test_store")
            if isinstance(history, list):
                logger.info("✅ Obtenção de histórico funcionando")
                self.test_results['price_history_get'] = True
            else:
                logger.error("❌ Obtenção de histórico falhou")
                self.test_results['price_history_get'] = False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste do histórico de preços: {e}")
            self.test_results['price_history'] = False
    
    async def test_price_comparator(self):
        """Testa o sistema comparador de preços"""
        try:
            logger.info("🧪 Testando Sistema Comparador de Preços...")
            
            import price_comparator
            
            # Testa adição de oferta
            success = price_comparator.price_comparator.add_product_offer(
                "test_product", "store1", 100.0, "test_url1"
            )
            if success:
                logger.info("✅ Adição de oferta funcionando")
                self.test_results['price_comparator_add'] = True
            else:
                logger.error("❌ Adição de oferta falhou")
                self.test_results['price_comparator_add'] = False
            
            # Testa comparação de preços
            comparison = price_comparator.price_comparator.compare_prices("test_product", "test_category", [])
            if isinstance(comparison, dict):
                logger.info("✅ Comparação de preços funcionando")
                self.test_results['price_comparator_compare'] = True
            else:
                logger.error("❌ Comparação de preços falhou")
                self.test_results['price_comparator_compare'] = False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste do comparador de preços: {e}")
            self.test_results['price_comparator'] = False
    
    async def test_product_reviews(self):
        """Testa o sistema de reviews de produtos"""
        try:
            logger.info("🧪 Testando Sistema de Reviews de Produtos...")
            
            import product_reviews
            
            # Testa adição de review
            success = await product_reviews.add_product_review(
                12345, "https://test.com/product", 5, "Excelente produto!", "test_user"
            )
            if success:
                logger.info("✅ Adição de review funcionando")
                self.test_results['product_reviews_add'] = True
            else:
                logger.error("❌ Adição de review falhou")
                self.test_results['product_reviews_add'] = False
            
            # Testa obtenção de reviews
            reviews = await product_reviews.get_product_reviews("https://test.com/product")
            if isinstance(reviews, list):
                logger.info("✅ Obtenção de reviews funcionando")
                self.test_results['product_reviews_get'] = True
            else:
                logger.error("❌ Obtenção de reviews falhou")
                self.test_results['product_reviews_get'] = False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste das reviews de produtos: {e}")
            self.test_results['product_reviews'] = False
    
    async def test_main_integration(self):
        """Testa a integração principal no main.py"""
        try:
            logger.info("🧪 Testando Integração Principal (main.py)...")
            
            import main
            
            # Verifica se as flags estão definidas
            flags = [
                'REVIEW_SYSTEM_AVAILABLE',
                'USER_CATEGORIES_AVAILABLE',
                'NOTIFICATION_SYSTEM_AVAILABLE'
            ]
            
            for flag in flags:
                if hasattr(main, flag):
                    logger.info(f"✅ Flag {flag} definida: {getattr(main, flag)}")
                    self.test_results[f'flag_{flag}'] = True
                else:
                    logger.error(f"❌ Flag {flag} não definida")
                    self.test_results[f'flag_{flag}'] = False
            
            # Verifica se os comandos estão definidos
            if hasattr(main, 'BOT_COMMANDS') and len(main.BOT_COMMANDS) > 0:
                logger.info(f"✅ Comandos do bot definidos: {len(main.BOT_COMMANDS)} comandos")
                self.test_results['bot_commands'] = True
            else:
                logger.error("❌ Comandos do bot não definidos")
                self.test_results['bot_commands'] = False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste da integração principal: {e}")
            self.test_results['main_integration'] = False
    
    async def run_all_tests(self):
        """Executa todos os testes"""
        logger.info("🚀 Iniciando Testes de Integração...")
        
        # Executa todos os testes
        await self.test_cache_system()
        await self.test_rate_limiter()
        await self.test_health_monitor()
        await self.test_performance_metrics()
        await self.test_user_categories()
        await self.test_price_history()
        await self.test_price_comparator()
        await self.test_product_reviews()
        await self.test_main_integration()
        
        # Gera relatório
        self.generate_report()
    
    def generate_report(self):
        """Gera relatório dos testes"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        logger.info("\n" + "="*60)
        logger.info("📊 RELATÓRIO DOS TESTES DE INTEGRAÇÃO")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        logger.info(f"⏱️  Duração total: {duration:.2f} segundos")
        logger.info(f"🧪 Total de testes: {total_tests}")
        logger.info(f"✅ Testes aprovados: {passed_tests}")
        logger.info(f"❌ Testes falharam: {failed_tests}")
        logger.info(f"📈 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
        
        logger.info("\n📋 DETALHES DOS TESTES:")
        for test_name, result in self.test_results.items():
            status = "✅ PASSOU" if result else "❌ FALHOU"
            logger.info(f"  {test_name}: {status}")
        
        if failed_tests == 0:
            logger.info("\n🎉 TODOS OS TESTES PASSARAM! Sistema pronto para produção.")
        else:
            logger.info(f"\n⚠️  {failed_tests} TESTES FALHARAM. Verifique os erros acima.")
        
        logger.info("="*60)

async def main():
    """Função principal"""
    tester = IntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
