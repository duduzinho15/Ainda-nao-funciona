#!/usr/bin/env python3
"""
Script de Teste Simples de Integração
Verifica se todos os módulos podem ser importados e inicializados
"""

import sys
import logging
from datetime import datetime

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_module_imports():
    """Testa se todos os módulos podem ser importados"""
    logger.info("🧪 Testando Importações de Módulos...")
    
    test_results = {}
    
    # Testa importação do cache
    try:
        import cache_system
        logger.info("✅ cache_system importado com sucesso")
        test_results['cache_system'] = True
    except Exception as e:
        logger.error(f"❌ Erro ao importar cache_system: {e}")
        test_results['cache_system'] = False
    
    # Testa importação do rate limiter
    try:
        import rate_limiter
        logger.info("✅ rate_limiter importado com sucesso")
        test_results['rate_limiter'] = True
    except Exception as e:
        logger.error(f"❌ Erro ao importar rate_limiter: {e}")
        test_results['rate_limiter'] = False
    
    # Testa importação do health monitor
    try:
        import health_monitor
        logger.info("✅ health_monitor importado com sucesso")
        test_results['health_monitor'] = True
    except Exception as e:
        logger.error(f"❌ Erro ao importar health_monitor: {e}")
        test_results['health_monitor'] = False
    
    # Testa importação das métricas de performance
    try:
        import performance_metrics
        logger.info("✅ performance_metrics importado com sucesso")
        test_results['performance_metrics'] = True
    except Exception as e:
        logger.error(f"❌ Erro ao importar performance_metrics: {e}")
        test_results['performance_metrics'] = False
    
    # Testa importação das categorias de usuários
    try:
        import user_categories
        logger.info("✅ user_categories importado com sucesso")
        test_results['user_categories'] = True
    except Exception as e:
        logger.error(f"❌ Erro ao importar user_categories: {e}")
        test_results['user_categories'] = False
    
    # Testa importação do histórico de preços
    try:
        import price_history
        logger.info("✅ price_history importado com sucesso")
        test_results['price_history'] = True
    except Exception as e:
        logger.error(f"❌ Erro ao importar price_history: {e}")
        test_results['price_history'] = False
    
    # Testa importação do comparador de preços
    try:
        import price_comparator
        logger.info("✅ price_comparator importado com sucesso")
        test_results['price_comparator'] = True
    except Exception as e:
        logger.error(f"❌ Erro ao importar price_comparator: {e}")
        test_results['price_comparator'] = False
    
    # Testa importação das reviews de produtos
    try:
        import product_reviews
        logger.info("✅ product_reviews importado com sucesso")
        test_results['product_reviews'] = True
    except Exception as e:
        logger.error(f"❌ Erro ao importar product_reviews: {e}")
        test_results['product_reviews'] = False
    
    # Testa importação do sistema de notificações
    try:
        import notification_system
        logger.info("✅ notification_system importado com sucesso")
        test_results['notification_system'] = True
    except Exception as e:
        logger.error(f"❌ Erro ao importar notification_system: {e}")
        test_results['notification_system'] = False
    
    # Testa importação do main
    try:
        import main
        logger.info("✅ main.py importado com sucesso")
        test_results['main'] = True
    except Exception as e:
        logger.error(f"❌ Erro ao importar main.py: {e}")
        test_results['main'] = False
    
    return test_results

def test_basic_functionality():
    """Testa funcionalidades básicas dos módulos"""
    logger.info("🧪 Testando Funcionalidades Básicas...")
    
    test_results = {}
    
    # Testa cache básico
    try:
        import cache_system
        cache_system.cache.set("test_key", "test_value", 10)
        result = cache_system.cache.get("test_key")
        if result == "test_value":
            logger.info("✅ Cache básico funcionando")
            test_results['cache_basic'] = True
        else:
            logger.error("❌ Cache básico falhou")
            test_results['cache_basic'] = False
    except Exception as e:
        logger.error(f"❌ Erro no teste do cache: {e}")
        test_results['cache_basic'] = False
    
    # Testa rate limiter básico
    try:
        import rate_limiter
        limiter = rate_limiter.IntelligentRateLimiter()
        if len(limiter.strategies) > 0:
            logger.info("✅ Rate limiter básico funcionando")
            test_results['rate_limiter_basic'] = True
        else:
            logger.error("❌ Rate limiter básico falhou")
            test_results['rate_limiter_basic'] = False
    except Exception as e:
        logger.error(f"❌ Erro no teste do rate limiter: {e}")
        test_results['rate_limiter_basic'] = False
    
    # Testa health monitor básico
    try:
        import health_monitor
        monitor = health_monitor.HealthMonitor()
        if hasattr(monitor, 'checkers'):
            logger.info("✅ Health monitor básico funcionando")
            test_results['health_monitor_basic'] = True
        else:
            logger.error("❌ Health monitor básico falhou")
            test_results['health_monitor_basic'] = False
    except Exception as e:
        logger.error(f"❌ Erro no teste do health monitor: {e}")
        test_results['health_monitor_basic'] = False
    
    # Testa métricas básicas
    try:
        import performance_metrics
        dashboard = performance_metrics.get_metrics_dashboard()
        if isinstance(dashboard, dict):
            logger.info("✅ Métricas básicas funcionando")
            test_results['metrics_basic'] = True
        else:
            logger.error("❌ Métricas básicas falharam")
            test_results['metrics_basic'] = False
    except Exception as e:
        logger.error(f"❌ Erro no teste das métricas: {e}")
        test_results['metrics_basic'] = False
    
    # Testa categorias básicas
    try:
        import user_categories
        if hasattr(user_categories, 'category_manager'):
            logger.info("✅ Categorias básicas funcionando")
            test_results['categories_basic'] = True
        else:
            logger.error("❌ Categorias básicas falharam")
            test_results['categories_basic'] = False
    except Exception as e:
        logger.error(f"❌ Erro no teste das categorias: {e}")
        test_results['categories_basic'] = False
    
    # Testa histórico de preços básico
    try:
        import price_history
        if hasattr(price_history, 'price_history_manager'):
            logger.info("✅ Histórico de preços básico funcionando")
            test_results['price_history_basic'] = True
        else:
            logger.error("❌ Histórico de preços básico falhou")
            test_results['price_history_basic'] = False
    except Exception as e:
        logger.error(f"❌ Erro no teste do histórico de preços: {e}")
        test_results['price_history_basic'] = False
    
    # Testa comparador de preços básico
    try:
        import price_comparator
        if hasattr(price_comparator, 'price_comparator'):
            logger.info("✅ Comparador de preços básico funcionando")
            test_results['price_comparator_basic'] = True
        else:
            logger.error("❌ Comparador de preços básico falhou")
            test_results['price_comparator_basic'] = False
    except Exception as e:
        logger.error(f"❌ Erro no teste do comparador de preços: {e}")
        test_results['price_comparator_basic'] = False
    
    # Testa reviews básico
    try:
        import product_reviews
        if hasattr(product_reviews, 'review_manager'):
            logger.info("✅ Reviews básico funcionando")
            test_results['reviews_basic'] = True
        else:
            logger.error("❌ Reviews básico falhou")
            test_results['reviews_basic'] = False
    except Exception as e:
        logger.error(f"❌ Erro no teste das reviews: {e}")
        test_results['reviews_basic'] = False
    
    return test_results

def generate_report(import_results, functionality_results):
    """Gera relatório dos testes"""
    logger.info("\n" + "="*60)
    logger.info("📊 RELATÓRIO DOS TESTES DE INTEGRAÇÃO")
    logger.info("="*60)
    
    # Estatísticas de importação
    total_imports = len(import_results)
    successful_imports = sum(1 for result in import_results.values() if result)
    failed_imports = total_imports - successful_imports
    
    logger.info(f"📦 IMPORTAÇÕES:")
    logger.info(f"   Total: {total_imports}")
    logger.info(f"   ✅ Sucessos: {successful_imports}")
    logger.info(f"   ❌ Falhas: {failed_imports}")
    logger.info(f"   📈 Taxa de sucesso: {(successful_imports/total_imports)*100:.1f}%")
    
    # Estatísticas de funcionalidade
    total_functionality = len(functionality_results)
    successful_functionality = sum(1 for result in functionality_results.values() if result)
    failed_functionality = total_functionality - successful_functionality
    
    logger.info(f"\n🔧 FUNCIONALIDADES:")
    logger.info(f"   Total: {total_functionality}")
    logger.info(f"   ✅ Sucessos: {successful_functionality}")
    logger.info(f"   ❌ Falhas: {failed_functionality}")
    logger.info(f"   📈 Taxa de sucesso: {(successful_functionality/total_functionality)*100:.1f}%")
    
    # Status geral
    total_tests = total_imports + total_functionality
    total_successes = successful_imports + successful_functionality
    overall_success_rate = (total_successes / total_tests) * 100
    
    logger.info(f"\n🎯 STATUS GERAL:")
    logger.info(f"   Total de testes: {total_tests}")
    logger.info(f"   Total de sucessos: {total_successes}")
    logger.info(f"   Taxa de sucesso geral: {overall_success_rate:.1f}%")
    
    if overall_success_rate >= 90:
        logger.info("🎉 EXCELENTE! Sistema pronto para produção.")
    elif overall_success_rate >= 80:
        logger.info("✅ BOM! Sistema funcional com pequenos ajustes necessários.")
    elif overall_success_rate >= 60:
        logger.info("⚠️  REGULAR! Sistema funcional mas precisa de correções.")
    else:
        logger.error("❌ PROBLEMÁTICO! Sistema precisa de correções significativas.")
    
    logger.info("="*60)

def main():
    """Função principal"""
    logger.info("🚀 Iniciando Testes de Integração Simples...")
    
    # Testa importações
    import_results = test_module_imports()
    
    # Testa funcionalidades básicas
    functionality_results = test_basic_functionality()
    
    # Gera relatório
    generate_report(import_results, functionality_results)

if __name__ == "__main__":
    main()
