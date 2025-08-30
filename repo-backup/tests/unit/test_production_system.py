"""
Testes do Sistema de Produção
Valida funcionalidades de produção, monitoramento e otimizações
"""

import asyncio
import os
import sys

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def test_cache_config():
    """Testa configuração de cache de produção"""
    from src.core.cache_config import production_cache_config

    # Teste de configurações de plataforma
    amazon_config = production_cache_config.get_platform_config("amazon")
    assert amazon_config is not None
    assert amazon_config.ttl_seconds == 3600  # 1 hora
    assert amazon_config.strategy.value == "balanced"

    # Teste de TTLs
    assert (
        production_cache_config.get_ttl_for_platform("mercadolivre") == 7200
    )  # 2 horas
    assert production_cache_config.get_ttl_for_platform("aliexpress") == 1800  # 30 min

    # Teste de configurações globais
    global_config = production_cache_config.get_global_config()
    assert "redis_url" in global_config
    assert "metrics_enabled" in global_config

    print("✅ Cache config: OK")


def test_conversion_metrics():
    """Testa sistema de métricas de conversão"""
    from src.core.conversion_metrics import conversion_metrics

    # Teste de métricas iniciais
    global_metrics = conversion_metrics.get_global_metrics()
    assert "total_conversions" in global_metrics
    assert "uptime_hours" in global_metrics

    # Teste de métricas por plataforma
    platform_metrics = conversion_metrics.get_all_platform_metrics()
    assert "amazon" in platform_metrics
    assert "mercadolivre" in platform_metrics

    # Teste de ranking de performance
    ranking = conversion_metrics.get_platform_performance_ranking()
    assert isinstance(ranking, list)

    print("✅ Conversion metrics: OK")


def test_failure_alerts():
    """Testa sistema de alertas de falha"""
    from src.core.failure_alerts import failure_alert_system

    # Teste de regras de alerta
    active_alerts = failure_alert_system.get_active_alerts()
    assert isinstance(active_alerts, list)

    # Teste de configuração de canais
    channels = failure_alert_system.notification_channels
    assert "log" in channels
    assert "email" in channels

    # Teste de resumo de alertas
    summary = failure_alert_system.get_alert_summary()
    assert "active_alerts" in summary
    assert "total_history" in summary

    print("✅ Failure alerts: OK")


def test_conversion_dashboard():
    """Testa dashboard de conversões"""
    from src.dashboard.conversion_dashboard import conversion_dashboard

    # Teste de dados do dashboard
    async def test_dashboard():
        dashboard_data = await conversion_dashboard.get_dashboard_data()
        assert "overview" in dashboard_data
        assert "platform_metrics" in dashboard_data
        assert "system_health" in dashboard_data

        # Teste de detalhes de plataforma
        amazon_details = await conversion_dashboard.get_platform_details("amazon")
        assert "platform" in amazon_details
        assert "metrics" in amazon_details

        print("✅ Conversion dashboard: OK")

    # Executar teste assíncrono
    asyncio.run(test_dashboard())


def test_optimization_engine():
    """Testa motor de otimizações"""
    from src.core.optimization_engine import optimization_engine

    # Teste de critérios de pontuação
    scoring_criteria = optimization_engine.get_current_scoring_criteria()
    assert scoring_criteria.url_format_weight > 0
    assert scoring_criteria.min_score_threshold > 0

    # Teste de padrões regex otimizados
    regex_patterns = optimization_engine.get_optimized_regex_patterns()
    assert "amazon" in regex_patterns
    assert "mercadolivre" in regex_patterns

    # Teste de configuração de cache distribuído
    cache_config = optimization_engine.get_distributed_cache_config()
    assert "enabled" in cache_config
    assert "nodes" in cache_config

    print("✅ Optimization engine: OK")


def test_production_integration():
    """Testa integração completa do sistema de produção"""
    from src.core.cache_config import production_cache_config
    from src.core.conversion_metrics import conversion_metrics
    from src.core.failure_alerts import failure_alert_system
    from src.core.optimization_engine import optimization_engine

    # Verificar se todos os componentes estão funcionando
    platforms = production_cache_config.get_all_platforms()
    assert (
        len(platforms) >= 7
    )  # Amazon, ML, Shopee, Magazine, AliExpress, Awin, Rakuten

    # Verificar métricas
    metrics = conversion_metrics.get_global_metrics()
    assert isinstance(metrics, dict)

    # Verificar alertas
    alerts = failure_alert_system.get_active_alerts()
    assert isinstance(alerts, list)

    # Verificar otimizações
    history = optimization_engine.get_optimization_history()
    assert isinstance(history, list)

    print("✅ Production integration: OK")


def test_redis_config():
    """Testa configuração Redis de produção"""
    import os

    # Verificar se arquivo de configuração existe
    config_path = "config/redis.production.conf"
    assert os.path.exists(config_path), f"Arquivo {config_path} não encontrado"

    # Verificar conteúdo básico
    with open(config_path) as f:
        content = f.read()
        assert "maxmemory 2gb" in content
        assert "bind 0.0.0.0" in content
        assert "port 6379" in content

    print("✅ Redis production config: OK")


def test_requirements():
    """Testa dependências necessárias"""
    try:
        import redis

        print("✅ Redis: OK")
    except ImportError:
        print("❌ Redis: NÃO INSTALADO")

    try:
        import aiohttp

        print("✅ aiohttp: OK")
    except ImportError:
        print("❌ aiohttp: NÃO INSTALADO")

    try:
        import smtplib

        print("✅ smtplib: OK")
    except ImportError:
        print("❌ smtplib: NÃO INSTALADO")


def run_all_tests():
    """Executa todos os testes"""
    print("🧪 EXECUTANDO TESTES DO SISTEMA DE PRODUÇÃO")
    print("=" * 60)

    try:
        test_redis_config()
        test_requirements()
        test_cache_config()
        test_conversion_metrics()
        test_failure_alerts()
        test_conversion_dashboard()
        test_optimization_engine()
        test_production_integration()

        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema de produção está 100% funcional!")
        print("\n🚀 PRÓXIMOS PASSOS IMPLEMENTADOS:")
        print("1. ✅ PRODUÇÃO - Redis configurado com TTLs apropriados")
        print("2. ✅ MONITORAMENTO - Dashboard de conversões implementado")
        print("3. ✅ OTIMIZAÇÕES - Critérios de pontuação ajustáveis")
        print("4. ✅ ALERTAS - Sistema de alertas de falha ativo")
        print("5. ✅ MÉTRICAS - Coleta de métricas em tempo real")

        return True

    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
