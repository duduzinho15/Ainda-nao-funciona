"""
Teste de Validação do Sistema Garimpeiro Geek.
Valida todas as funcionalidades implementadas.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.models import Offer
from posting.message_formatter import message_formatter
from app.scheduler.post_scheduler import post_scheduler
from telegram_bot.bot_manager import TelegramBot, BotConfig
from scrapers.comunidades.promobit import PromobitScraper
from scrapers.precos.zoom import ZoomScraper
from core.cache.redis_manager import redis_manager
from core.monitoring.system_monitor import system_monitor


async def test_message_formatter():
    """Testa o message formatter."""
    print("\n🧪 Testando Message Formatter...")
    
    try:
        # Criar oferta de teste
        test_offer = Offer(
            title="Smartphone Samsung Galaxy S23",
            price=Decimal("2999.99"),
            original_price=Decimal("3999.99"),
            url="https://amazon.com.br/smartphone-s23",
            store="Amazon",
            category="Smartphones",
            affiliate_url="https://amazon.com.br/smartphone-s23",
            coupon_code="SAMSUNG25",
            coupon_discount=25,
            stock_quantity=10
        )
        
        # Formatar mensagem
        message = message_formatter.format_offer(test_offer)
        
        # Validar formatação
        assert "Smartphone Samsung Galaxy S23" in message
        assert "R$ 2999,99" in message
        assert "25%" in message
        assert "CUPOM" in message
        assert "amazon.com.br" in message
        
        print("  ✅ Message Formatter funcionando corretamente")
        print(f"  📝 Mensagem gerada: {len(message)} caracteres")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erro no Message Formatter: {e}")
        return False


async def test_post_scheduler():
    """Testa o scheduler de postagem."""
    print("\n🧪 Testando Post Scheduler...")
    
    try:
        # Verificar jobs configurados
        jobs = post_scheduler.get_all_jobs()
        assert len(jobs) > 0, "Nenhum job configurado"
        
        # Verificar job de postagem
        posting_job = post_scheduler.get_job_status("post_queue")
        assert posting_job is not None, "Job de postagem não encontrado"
        
        # Verificar estatísticas
        stats = post_scheduler.get_scheduler_stats()
        assert "total_jobs" in stats
        
        print("  ✅ Post Scheduler funcionando corretamente")
        print(f"  📊 Jobs configurados: {len(jobs)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erro no Post Scheduler: {e}")
        return False


async def test_telegram_bot():
    """Testa o bot do Telegram."""
    print("\n🧪 Testando Telegram Bot...")
    
    try:
        # Criar configuração de teste
        config = BotConfig(
            bot_token="test_token",
            channel_id="test_channel",
            admin_user_ids=[123456789],
            dry_run=True
        )
        
        # Criar bot
        bot = TelegramBot(config)
        
        # Testar status
        status = await bot.get_status()
        assert "status" in status
        assert "posting_mode" in status
        
        # Testar modo DRY_RUN
        await bot.set_dry_run(True)
        assert bot.status.value == "dry_run"
        
        print("  ✅ Telegram Bot funcionando corretamente")
        print(f"  🤖 Status: {status['status']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erro no Telegram Bot: {e}")
        return False


async def test_promobit_scraper():
    """Testa o scraper do Promobit."""
    print("\n🧪 Testando Promobit Scraper...")
    
    try:
        # Criar instância do scraper
        scraper = PromobitScraper()
        
        # Testar coleta de ofertas
        offers = await scraper.scrape_offers(max_offers=5)
        
        # Verificar se retornou ofertas
        assert len(offers) > 0, "Nenhuma oferta coletada"
        
        # Verificar estrutura das ofertas
        for offer in offers:
            assert offer.title, "Título da oferta ausente"
            assert offer.affiliate_url, "URL de afiliado ausente"
            assert offer.price > 0, "Preço inválido"
        
        # Verificar estatísticas
        stats = scraper.get_stats()
        assert "total_scraped" in stats
        
        print("  ✅ Promobit Scraper funcionando corretamente")
        print(f"  🕷️ Ofertas coletadas: {len(offers)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erro no Promobit Scraper: {e}")
        return False


async def test_zoom_scraper():
    """Testa o scraper do Zoom."""
    print("\n🧪 Testando Zoom Scraper...")
    
    try:
        # Criar instância do scraper
        scraper = ZoomScraper()
        
        # Testar coleta de histórico
        test_url = "https://exemplo.com/produto-teste"
        history = await scraper.collect_price_history(test_url)
        
        # Verificar se retornou histórico
        assert history is not None, "Histórico não coletado"
        assert history.product_name, "Nome do produto ausente"
        assert len(history.price_history) > 0, "Histórico de preços vazio"
        
        # Testar análise de tendências
        analysis = await scraper.analyze_price_trends(history)
        assert "trend" in analysis
        assert "confidence" in analysis
        
        # Verificar estatísticas
        stats = scraper.get_stats()
        assert "total_products" in stats
        
        print("  ✅ Zoom Scraper funcionando corretamente")
        print(f"  📊 Tendência: {analysis['trend']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erro no Zoom Scraper: {e}")
        return False


async def test_redis_manager():
    """Testa o gerenciador Redis."""
    print("\n🧪 Testando Redis Manager...")
    
    try:
        # Testar operações básicas
        test_key = "test_key"
        test_value = {"test": "data", "timestamp": datetime.now().isoformat()}
        
        # Definir valor
        success = await redis_manager.set(test_key, test_value, 60)
        assert success, "Falha ao definir valor no cache"
        
        # Obter valor
        retrieved_value = await redis_manager.get(test_key)
        assert retrieved_value is not None, "Valor não encontrado no cache"
        assert retrieved_value["test"] == "data", "Valor incorreto"
        
        # Verificar existência
        exists = await redis_manager.exists(test_key)
        assert exists, "Chave não existe no cache"
        
        # Limpar
        await redis_manager.delete(test_key)
        
        # Verificar estatísticas
        stats = redis_manager.get_stats()
        assert "total_requests" in stats
        
        print("  ✅ Redis Manager funcionando corretamente")
        print(f"  💾 Total de requisições: {stats['total_requests']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erro no Redis Manager: {e}")
        return False


async def test_system_monitor():
    """Testa o monitor do sistema."""
    print("\n🧪 Testando System Monitor...")
    
    try:
        # Iniciar monitoramento
        await system_monitor.start_monitoring()
        
        # Aguardar uma verificação
        await asyncio.sleep(2)
        
        # Verificar métricas
        metrics = system_monitor.get_health_metrics()
        assert len(metrics) > 0, "Nenhuma métrica disponível"
        
        # Verificar alertas
        alerts = system_monitor.get_active_alerts()
        # Pode ter alertas ou não, dependendo do estado do sistema
        
        # Verificar estatísticas
        stats = system_monitor.get_system_stats()
        assert "last_check" in stats
        
        print("  ✅ System Monitor funcionando corretamente")
        print(f"  📊 Métricas disponíveis: {len(metrics)}")
        print(f"  🚨 Alertas ativos: {len(alerts)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erro no System Monitor: {e}")
        return False


async def run_all_tests():
    """Executa todos os testes."""
    print("🚀 INICIANDO VALIDAÇÃO COMPLETA DO SISTEMA GARIMPEIRO GEEK")
    print("=" * 60)
    
    test_results = []
    
    # Executar testes
    tests = [
        ("Message Formatter", test_message_formatter),
        ("Post Scheduler", test_post_scheduler),
        ("Telegram Bot", test_telegram_bot),
        ("Promobit Scraper", test_promobit_scraper),
        ("Zoom Scraper", test_zoom_scraper),
        ("Redis Manager", test_redis_manager),
        ("System Monitor", test_system_monitor)
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ Erro fatal no teste {test_name}: {e}")
            test_results.append((test_name, False))
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {test_name}: {status}")
        if result:
            passed_tests += 1
    
    print(f"\n🎯 RESULTADO: {passed_tests}/{total_tests} testes passaram")
    
    if passed_tests == total_tests:
        print("🎉 SISTEMA 100% FUNCIONAL!")
        return True
    else:
        print("⚠️ ALGUNS TESTES FALHARAM - VERIFICAR IMPLEMENTAÇÃO")
        return False


if __name__ == "__main__":
    # Executar testes
    try:
        result = asyncio.run(run_all_tests())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erro fatal: {e}")
        sys.exit(1)

