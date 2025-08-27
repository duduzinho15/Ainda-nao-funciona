#!/usr/bin/env python3
"""
Cron Manager para o Sistema Garimpeiro Geek
Gerencia agendamento de tarefas e postagens automáticas
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from src.core.database import Database


class JobStatus(Enum):
    """Status de um job"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class JobPriority(Enum):
    """Prioridade de um job"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ScheduledJob:
    """Representa um job agendado"""

    id: str
    name: str
    function: str  # Nome da função a ser executada
    schedule: str  # Expressão cron ou intervalo
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.PENDING
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    max_retries: int = 3
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    enabled: bool = True
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "id": self.id,
            "name": self.name,
            "function": self.function,
            "schedule": self.schedule,
            "args": self.args,
            "kwargs": self.kwargs,
            "priority": self.priority.value,
            "status": self.status.value,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "enabled": self.enabled,
            "description": self.description,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledJob":
        """Cria a partir de dicionário"""
        job = cls(
            id=data["id"],
            name=data["name"],
            function=data["function"],
            schedule=data["schedule"],
            args=data.get("args", []),
            kwargs=data.get("kwargs", {}),
            priority=JobPriority(data.get("priority", 2)),
            status=JobStatus(data.get("status", "pending")),
            max_retries=data.get("max_retries", 3),
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )

        if data.get("last_run"):
            job.last_run = datetime.fromisoformat(data["last_run"])
        if data.get("next_run"):
            job.next_run = datetime.fromisoformat(data["next_run"])
        if data.get("created_at"):
            job.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            job.updated_at = datetime.fromisoformat(data["updated_at"])

        job.run_count = data.get("run_count", 0)
        job.retry_count = data.get("retry_count", 0)
        job.enabled = data.get("enabled", True)

        return job


class CronManager:
    """
    Gerenciador principal de agendamento de tarefas
    """

    def __init__(self, db_manager: Optional[Database] = None):
        self.logger = logging.getLogger("scheduler.cron_manager")
        self.db_manager = db_manager or Database()

        # Jobs agendados
        self.scheduled_jobs: Dict[str, ScheduledJob] = {}

        # Funções registradas
        self.registered_functions: Dict[str, Callable] = {}

        # Status do scheduler
        self.is_running = False
        self.is_paused = False

        # Configurações
        self.max_concurrent_jobs = 5
        self.job_timeout = 300  # 5 minutos
        self.retry_delay = 60  # 1 minuto

        # Loop principal
        self.main_loop: Optional[asyncio.Task] = None
        self.job_tasks: Dict[str, asyncio.Task] = {}

        # Métricas
        self.metrics = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "running_jobs": 0,
            "pending_jobs": 0,
        }

        self.logger.info("CronManager inicializado")

    async def start(self) -> None:
        """Inicia o scheduler"""
        if self.is_running:
            self.logger.warning("Scheduler já está rodando")
            return

        self.logger.info("Iniciando CronManager...")
        self.is_running = True
        self.is_paused = False

        # Carregar jobs salvos
        await self._load_saved_jobs()

        # Iniciar loop principal
        self.main_loop = asyncio.create_task(self._main_loop())

        self.logger.info("CronManager iniciado com sucesso")

    async def stop(self) -> None:
        """Para o scheduler"""
        if not self.is_running:
            self.logger.warning("Scheduler não está rodando")
            return

        self.logger.info("Parando CronManager...")
        self.is_running = False

        # Cancelar loop principal
        if self.main_loop:
            self.main_loop.cancel()
            try:
                await self.main_loop
            except asyncio.CancelledError:
                pass

        # Cancelar jobs em execução
        for task in self.job_tasks.values():
            task.cancel()

        # Aguardar cancelamento
        if self.job_tasks:
            await asyncio.gather(*self.job_tasks.values(), return_exceptions=True)

        self.logger.info("CronManager parado com sucesso")

    async def pause(self) -> None:
        """Pausa o scheduler"""
        if not self.is_running:
            self.logger.warning("Scheduler não está rodando")
            return

        self.logger.info("Pausando CronManager...")
        self.is_paused = True
        self.logger.info("CronManager pausado")

    async def resume(self) -> None:
        """Resume o scheduler"""
        if not self.is_running:
            self.logger.warning("Scheduler não está rodando")
            return

        if not self.is_paused:
            self.logger.warning("Scheduler não está pausado")
            return

        self.logger.info("Resumindo CronManager...")
        self.is_paused = False
        self.logger.info("CronManager resumido")

    def register_function(self, name: str, func: Callable) -> None:
        """Registra uma função para ser executada pelos jobs"""
        self.registered_functions[name] = func
        self.logger.info(f"Função registrada: {name}")

    def schedule_job(self, job: ScheduledJob) -> None:
        """Agenda um novo job"""
        if job.id in self.scheduled_jobs:
            self.logger.warning(f"Job {job.id} já existe, atualizando...")

        self.scheduled_jobs[job.id] = job
        self._update_metrics()
        self.logger.info(f"Job agendado: {job.name} ({job.id})")

        # Salvar no banco
        asyncio.create_task(self._save_job(job))

    def unschedule_job(self, job_id: str) -> bool:
        """Remove um job agendado"""
        if job_id not in self.scheduled_jobs:
            self.logger.warning(f"Job {job_id} não encontrado")
            return False

        job = self.scheduled_jobs.pop(job_id)

        # Cancelar se estiver rodando
        if job_id in self.job_tasks:
            self.job_tasks[job_id].cancel()
            del self.job_tasks[job_id]

        self._update_metrics()
        self.logger.info(f"Job removido: {job.name} ({job_id})")

        # Remover do banco
        asyncio.create_task(self._delete_job(job_id))
        return True

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Retorna um job específico"""
        return self.scheduled_jobs.get(job_id)

    def get_all_jobs(self) -> List[ScheduledJob]:
        """Retorna todos os jobs"""
        return list(self.scheduled_jobs.values())

    def get_jobs_by_status(self, status: JobStatus) -> List[ScheduledJob]:
        """Retorna jobs por status"""
        return [job for job in self.scheduled_jobs.values() if job.status == status]

    def get_jobs_by_tag(self, tag: str) -> List[ScheduledJob]:
        """Retorna jobs por tag"""
        return [job for job in self.scheduled_jobs.values() if tag in job.tags]

    def update_job(self, job_id: str, **kwargs) -> bool:
        """Atualiza um job existente"""
        if job_id not in self.scheduled_jobs:
            self.logger.warning(f"Job {job_id} não encontrado")
            return False

        job = self.scheduled_jobs[job_id]

        # Atualizar campos
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)

        job.updated_at = datetime.now()

        # Salvar no banco
        asyncio.create_task(self._save_job(job))

        self.logger.info(f"Job atualizado: {job.name} ({job_id})")
        return True

    def enable_job(self, job_id: str) -> bool:
        """Habilita um job"""
        return self.update_job(job_id, enabled=True)

    def disable_job(self, job_id: str) -> bool:
        """Desabilita um job"""
        return self.update_job(job_id, enabled=False)

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do scheduler"""
        return self.metrics.copy()

    async def _main_loop(self) -> None:
        """Loop principal do scheduler"""
        self.logger.info("Loop principal iniciado")

        while self.is_running:
            try:
                if not self.is_paused:
                    await self._process_jobs()

                # Aguardar próximo ciclo
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                self.logger.info("Loop principal cancelado")
                break
            except Exception as e:
                self.logger.error(f"Erro no loop principal: {e}")
                await asyncio.sleep(5)  # Aguardar antes de continuar

        self.logger.info("Loop principal finalizado")

    async def _process_jobs(self) -> None:
        """Processa jobs pendentes"""
        now = datetime.now()

        for job in self.scheduled_jobs.values():
            if not job.enabled or job.status != JobStatus.PENDING:
                continue

            # Verificar se é hora de executar
            if job.next_run and now >= job.next_run:
                if len(self.job_tasks) < self.max_concurrent_jobs:
                    await self._execute_job(job)
                else:
                    self.logger.warning(
                        "Limite de jobs concorrentes atingido, aguardando..."
                    )

    async def _execute_job(self, job: ScheduledJob) -> None:
        """Executa um job"""
        self.logger.info(f"Executando job: {job.name} ({job.id})")

        # Atualizar status
        job.status = JobStatus.RUNNING
        job.last_run = datetime.now()
        job.run_count += 1

        # Criar task para execução
        task = asyncio.create_task(self._run_job_with_timeout(job))
        self.job_tasks[job.id] = task

        # Atualizar métricas
        self._update_metrics()

        # Salvar no banco
        await self._save_job(job)

    async def _run_job_with_timeout(self, job: ScheduledJob) -> None:
        """Executa job com timeout"""
        try:
            # Executar função
            if job.function in self.registered_functions:
                func = self.registered_functions[job.function]

                if asyncio.iscoroutinefunction(func):
                    await asyncio.wait_for(
                        func(*job.args, **job.kwargs), timeout=self.job_timeout
                    )
                else:
                    # Função síncrona em thread separada
                    loop = asyncio.get_event_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(None, func, *job.args, **job.kwargs),
                        timeout=self.job_timeout,
                    )

                # Sucesso
                job.status = JobStatus.COMPLETED
                job.retry_count = 0
                self.logger.info(f"Job executado com sucesso: {job.name} ({job.id})")

            else:
                raise ValueError(f"Função {job.function} não registrada")

        except asyncio.TimeoutError:
            job.status = JobStatus.FAILED
            self.logger.error(f"Job timeout: {job.name} ({job.id})")

        except Exception as e:
            job.status = JobStatus.FAILED
            job.retry_count += 1
            self.logger.error(f"Erro na execução do job {job.name} ({job.id}): {e}")

            # Tentar novamente se não excedeu limite
            if job.retry_count < job.max_retries:
                job.status = JobStatus.PENDING
                job.next_run = datetime.now() + timedelta(seconds=self.retry_delay)
                self.logger.info(
                    f"Job {job.name} será executado novamente em {self.retry_delay}s"
                )

        finally:
            # Calcular próxima execução
            job.next_run = self._calculate_next_run(job)

            # Remover da lista de tasks
            if job.id in self.job_tasks:
                del self.job_tasks[job.id]

            # Atualizar métricas
            self._update_metrics()

            # Salvar no banco
            await self._save_job(job)

    def _calculate_next_run(self, job: ScheduledJob) -> datetime:
        """Calcula próxima execução baseado no schedule"""
        now = datetime.now()

        # Por enquanto, implementação simples de intervalos
        # TODO: Implementar parser de expressões cron
        if job.schedule.startswith("every_"):
            interval = job.schedule.replace("every_", "")

            if interval == "90s":
                return now + timedelta(seconds=90)
            elif interval == "15m":
                return now + timedelta(minutes=15)
            elif interval == "30m":
                return now + timedelta(minutes=30)
            elif interval == "45s":
                return now + timedelta(seconds=45)
            elif interval == "1h":
                return now + timedelta(hours=1)
            elif interval == "6h":
                return now + timedelta(hours=6)
            elif interval == "12h":
                return now + timedelta(hours=12)
            elif interval == "1d":
                return now + timedelta(days=1)

        # Padrão: 1 hora
        return now + timedelta(hours=1)

    def _update_metrics(self) -> None:
        """Atualiza métricas do scheduler"""
        self.metrics["total_jobs"] = len(self.scheduled_jobs)
        self.metrics["running_jobs"] = len(self.job_tasks)
        self.metrics["pending_jobs"] = len(
            [j for j in self.scheduled_jobs.values() if j.status == JobStatus.PENDING]
        )
        self.metrics["completed_jobs"] = len(
            [j for j in self.scheduled_jobs.values() if j.status == JobStatus.COMPLETED]
        )
        self.metrics["failed_jobs"] = len(
            [j for j in self.scheduled_jobs.values() if j.status == JobStatus.FAILED]
        )

    async def _load_saved_jobs(self) -> None:
        """Carrega jobs salvos do banco de dados"""
        try:
            # TODO: Implementar carregamento do banco
            self.logger.info("Carregando jobs salvos...")

            # Jobs padrão do sistema
            default_jobs = [
                ScheduledJob(
                    id="collect_offers",
                    name="Coletar Ofertas",
                    function="collect_offers",
                    schedule="every_90s",
                    description="Coleta ofertas dos scrapers a cada 90 segundos",
                    tags=["scraping", "offers"],
                    priority=JobPriority.HIGH,
                ),
                ScheduledJob(
                    id="enrich_prices",
                    name="Enriquecer Preços",
                    function="enrich_prices",
                    schedule="every_15m",
                    description="Enriquece dados de preços a cada 15 minutos",
                    tags=["prices", "enrichment"],
                    priority=JobPriority.NORMAL,
                ),
                ScheduledJob(
                    id="post_queue",
                    name="Postar Fila",
                    function="post_queue",
                    schedule="every_45s",
                    description="Processa fila de postagens a cada 45 segundos",
                    tags=["posting", "telegram"],
                    priority=JobPriority.HIGH,
                ),
                ScheduledJob(
                    id="price_aggregate",
                    name="Agregar Preços",
                    function="price_aggregate",
                    schedule="every_30m",
                    description="Agrega dados de preços a cada 30 minutos",
                    tags=["prices", "analytics"],
                    priority=JobPriority.NORMAL,
                ),
            ]

            for job in default_jobs:
                self.scheduled_jobs[job.id] = job

            self.logger.info(f"Carregados {len(default_jobs)} jobs padrão")

        except Exception as e:
            self.logger.error(f"Erro ao carregar jobs salvos: {e}")

    async def _save_job(self, job: ScheduledJob) -> None:
        """Salva job no banco de dados"""
        try:
            # TODO: Implementar salvamento no banco
            pass
        except Exception as e:
            self.logger.error(f"Erro ao salvar job {job.id}: {e}")

    async def _delete_job(self, job_id: str) -> None:
        """Remove job do banco de dados"""
        try:
            # TODO: Implementar remoção do banco
            pass
        except Exception as e:
            self.logger.error(f"Erro ao remover job {job_id}: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Retorna status completo do scheduler"""
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "total_jobs": len(self.scheduled_jobs),
            "enabled_jobs": len([j for j in self.scheduled_jobs.values() if j.enabled]),
            "running_jobs": len(self.job_tasks),
            "pending_jobs": len(
                [
                    j
                    for j in self.scheduled_jobs.values()
                    if j.status == JobStatus.PENDING
                ]
            ),
            "completed_jobs": len(
                [
                    j
                    for j in self.scheduled_jobs.values()
                    if j.status == JobStatus.COMPLETED
                ]
            ),
            "failed_jobs": len(
                [
                    j
                    for j in self.scheduled_jobs.values()
                    if j.status == JobStatus.FAILED
                ]
            ),
            "metrics": self.metrics.copy(),
        }
