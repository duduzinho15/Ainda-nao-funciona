#!/usr/bin/env python3
"""
Teste do Sistema de Scheduler do Garimpeiro Geek
Valida todas as funcionalidades de agendamento e execução de tarefas
"""

import asyncio
import logging
import os
import sys

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.app.scheduler import CronManager, JobScheduler, TaskRunner
from src.app.scheduler.cron_manager import JobStatus

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def test_scheduler_system():
    """Testa todo o sistema de scheduler"""
    print("🧪 Testando Sistema de Scheduler...")

    # Teste 1: CronManager
    print("\n1️⃣ Testando CronManager...")
    cron_manager = CronManager()

    # Verificar estrutura
    assert hasattr(cron_manager, "scheduled_jobs"), "scheduled_jobs não encontrado"
    assert hasattr(
        cron_manager, "registered_functions"
    ), "registered_functions não encontrado"
    assert hasattr(cron_manager, "is_running"), "is_running não encontrado"
    assert hasattr(cron_manager, "metrics"), "metrics não encontrado"
    print("✅ Estrutura do CronManager validada")

    # Verificar jobs padrão
    await cron_manager._load_saved_jobs()
    default_jobs = cron_manager.get_all_jobs()
    assert (
        len(default_jobs) == 4
    ), f"Esperados 4 jobs padrão, encontrados {len(default_jobs)}"

    expected_job_ids = [
        "collect_offers",
        "enrich_prices",
        "post_queue",
        "price_aggregate",
    ]
    for job_id in expected_job_ids:
        job = cron_manager.get_job(job_id)
        assert job is not None, f"Job {job_id} não encontrado"
        assert job.enabled, f"Job {job_id} não está habilitado"

    print("✅ Jobs padrão carregados corretamente")

    # Teste 2: JobScheduler
    print("\n2️⃣ Testando JobScheduler...")
    job_scheduler = JobScheduler(cron_manager)

    # Verificar estrutura
    assert hasattr(job_scheduler, "cron_manager"), "cron_manager não encontrado"
    assert hasattr(
        job_scheduler, "scheduled_functions"
    ), "scheduled_functions não encontrado"
    print("✅ Estrutura do JobScheduler validada")

    # Teste 3: TaskRunner
    print("\n3️⃣ Testando TaskRunner...")
    task_runner = TaskRunner()

    # Verificar estrutura
    assert hasattr(task_runner, "db_manager"), "db_manager não encontrado"
    assert hasattr(task_runner, "posting_manager"), "posting_manager não encontrado"
    assert hasattr(task_runner, "message_builder"), "message_builder não encontrado"
    print("✅ Estrutura do TaskRunner validada")

    # Teste 4: Execução de tarefas
    print("\n4️⃣ Testando execução de tarefas...")

    # Testar collect_offers
    collect_result = await task_runner.collect_offers()
    assert (
        collect_result["status"] == "success"
    ), f"collect_offers falhou: {collect_result}"
    assert "collected_offers" in collect_result, "Resultado não contém collected_offers"
    assert "new_offers" in collect_result, "Resultado não contém new_offers"
    print("✅ collect_offers executado com sucesso")

    # Testar enrich_prices
    enrich_result = await task_runner.enrich_prices()
    assert (
        enrich_result["status"] == "success"
    ), f"enrich_prices falhou: {enrich_result}"
    assert "enriched_offers" in enrich_result, "Resultado não contém enriched_offers"
    print("✅ enrich_prices executado com sucesso")

    # Testar post_queue
    post_result = await task_runner.post_queue()
    assert post_result["status"] == "success", f"post_queue falhou: {post_result}"
    assert "posted_offers" in post_result, "Resultado não contém posted_offers"
    print("✅ post_queue executado com sucesso")

    # Testar price_aggregate
    aggregate_result = await task_runner.price_aggregate()
    assert (
        aggregate_result["status"] == "success"
    ), f"price_aggregate falhou: {aggregate_result}"
    assert (
        "processed_products" in aggregate_result
    ), "Resultado não contém processed_products"
    print("✅ price_aggregate executado com sucesso")

    # Testar health_check
    health_result = await task_runner.health_check()
    assert health_result["status"] == "success", f"health_check falhou: {health_result}"
    assert "overall_status" in health_result, "Resultado não contém overall_status"
    print("✅ health_check executado com sucesso")

    # Testar cleanup_old_data
    cleanup_result = await task_runner.cleanup_old_data()
    assert (
        cleanup_result["status"] == "success"
    ), f"cleanup_old_data falhou: {cleanup_result}"
    assert "cleaned_records" in cleanup_result, "Resultado não contém cleaned_records"
    print("✅ cleanup_old_data executado com sucesso")

    # Teste 5: Agendamento de jobs
    print("\n5️⃣ Testando agendamento de jobs...")

    # Função de teste
    async def test_function():
        await asyncio.sleep(0.1)
        return "test_completed"

    # Agendar função
    job_id = job_scheduler.schedule_function(
        func=test_function,
        schedule="every_1h",
        description="Função de teste",
        tags=["test"],
    )

    assert job_id is not None, "Job ID não retornado"
    job = job_scheduler.get_job(job_id)
    assert job is not None, "Job agendado não encontrado"
    assert job.function == job_id, "Function ID incorreto"
    assert job.schedule == "every_1h", "Schedule incorreto"
    assert "test" in job.tags, "Tags não aplicadas"
    print("✅ Função agendada com sucesso")

    # Teste 6: Status e métricas
    print("\n6️⃣ Testando status e métricas...")

    # Status do scheduler
    status = job_scheduler.get_status()
    assert "is_running" in status, "Status não contém is_running"
    assert "total_jobs" in status, "Status não contém total_jobs"
    assert (
        status["total_jobs"] >= 5
    ), f"Esperados pelo menos 5 jobs, encontrados {status['total_jobs']}"
    print("✅ Status do scheduler validado")

    # Métricas do scheduler
    metrics = job_scheduler.get_metrics()
    assert "total_jobs" in metrics, "Métricas não contém total_jobs"
    assert "pending_jobs" in metrics, "Métricas não contém pending_jobs"
    print("✅ Métricas do scheduler validadas")

    # Teste 7: Controle de jobs
    print("\n7️⃣ Testando controle de jobs...")

    # Desabilitar job
    success = job_scheduler.disable_job(job_id)
    assert success, "Falha ao desabilitar job"

    job = job_scheduler.get_job(job_id)
    assert not job.enabled, "Job não foi desabilitado"
    print("✅ Job desabilitado com sucesso")

    # Habilitar job
    success = job_scheduler.enable_job(job_id)
    assert success, "Falha ao habilitar job"

    job = job_scheduler.get_job(job_id)
    assert job.enabled, "Job não foi habilitado"
    print("✅ Job habilitado com sucesso")

    # Remover job
    success = job_scheduler.unschedule_job(job_id)
    assert success, "Falha ao remover job"

    job = job_scheduler.get_job(job_id)
    assert job is None, "Job não foi removido"
    print("✅ Job removido com sucesso")

    # Teste 8: Filtros de jobs
    print("\n8️⃣ Testando filtros de jobs...")

    # Jobs por status
    pending_jobs = job_scheduler.get_jobs_by_status(JobStatus.PENDING)
    assert isinstance(pending_jobs, list), "get_jobs_by_status não retorna lista"

    # Jobs por tag
    scraping_jobs = job_scheduler.get_jobs_by_tag("scraping")
    assert isinstance(scraping_jobs, list), "get_jobs_by_tag não retorna lista"
    assert len(scraping_jobs) >= 1, "Esperado pelo menos 1 job com tag 'scraping'"
    print("✅ Filtros de jobs funcionando")

    print("\n🎉 TODOS OS TESTES DO SCHEDULER PASSARAM COM SUCESSO!")
    print("✅ Sistema de Scheduler está funcionando perfeitamente!")

    return True


async def test_scheduler_integration():
    """Testa integração entre componentes do scheduler"""
    print("\n🔗 Testando integração do scheduler...")

    # Criar instâncias
    cron_manager = CronManager()
    JobScheduler(cron_manager)
    task_runner = TaskRunner()

    # Registrar funções do TaskRunner
    cron_manager.register_function("collect_offers", task_runner.collect_offers)
    cron_manager.register_function("enrich_prices", task_runner.enrich_prices)
    cron_manager.register_function("post_queue", task_runner.post_queue)
    cron_manager.register_function("price_aggregate", task_runner.price_aggregate)

    # Verificar funções registradas
    assert (
        "collect_offers" in cron_manager.registered_functions
    ), "collect_offers não registrada"
    assert (
        "enrich_prices" in cron_manager.registered_functions
    ), "enrich_prices não registrada"
    assert (
        "post_queue" in cron_manager.registered_functions
    ), "post_queue não registrada"
    assert (
        "price_aggregate" in cron_manager.registered_functions
    ), "price_aggregate não registrada"

    print("✅ Funções registradas corretamente")

    # Verificar jobs padrão
    jobs = cron_manager.get_all_jobs()
    for job in jobs:
        assert (
            job.function in cron_manager.registered_functions
        ), f"Função {job.function} não registrada para job {job.id}"

    print("✅ Jobs padrão têm funções registradas")

    print("✅ Integração do scheduler validada")


if __name__ == "__main__":
    try:
        # Executar testes
        asyncio.run(test_scheduler_system())
        asyncio.run(test_scheduler_integration())

        print("\n🚀 Sistema de Scheduler está pronto para produção!")

    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
