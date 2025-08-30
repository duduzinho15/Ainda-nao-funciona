"""
Scheduler de Postagem Automática para o sistema Garimpeiro Geek.
Gerencia jobs de coleta, enriquecimento e postagem de ofertas.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import time

from src.core.models import Offer
from src.posting.message_formatter import message_formatter


class JobStatus(Enum):
    """Status de um job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """Prioridade de um job."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ScheduledJob:
    """Job agendado para execução."""
    id: str
    name: str
    function: Callable
    interval_seconds: int
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.PENDING
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PostScheduler:
    """Scheduler para postagem automática de ofertas."""
    
    def __init__(self):
        """Inicializa o scheduler."""
        self.jobs: Dict[str, ScheduledJob] = {}
        self.running = False
        self.logger = logging.getLogger(__name__)
        
        # Configurações padrão
        self.default_jobs = {
            "collect_offers": {
                "interval": 90,  # 90 segundos
                "priority": JobPriority.HIGH,
                "function": self._collect_offers_job
            },
            "enrich_prices": {
                "interval": 900,  # 15 minutos
                "priority": JobPriority.NORMAL,
                "function": self._enrich_prices_job
            },
            "post_queue": {
                "interval": 45,  # 45 segundos
                "priority": JobPriority.CRITICAL,
                "function": self._post_queue_job
            },
            "price_aggregate": {
                "interval": 1800,  # 30 minutos
                "priority": JobPriority.NORMAL,
                "function": self._price_aggregate_job
            }
        }
        
        # Inicializar jobs padrão
        self._initialize_default_jobs()
    
    def _initialize_default_jobs(self):
        """Inicializa jobs padrão do sistema."""
        for job_name, config in self.default_jobs.items():
            self.add_job(
                id=job_name,
                name=job_name.replace("_", " ").title(),
                function=config["function"],
                interval_seconds=config["interval"],
                priority=config["priority"]
            )
    
    def add_job(self, id: str, name: str, function: Callable, 
                interval_seconds: int, priority: JobPriority = JobPriority.NORMAL,
                metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Adiciona um novo job ao scheduler.
        
        Args:
            id: Identificador único do job
            name: Nome descritivo do job
            function: Função a ser executada
            interval_seconds: Intervalo entre execuções em segundos
            priority: Prioridade do job
            metadata: Metadados adicionais
            
        Returns:
            ID do job criado
        """
        if id in self.jobs:
            raise ValueError(f"Job com ID '{id}' já existe")
        
        job = ScheduledJob(
            id=id,
            name=name,
            function=function,
            interval_seconds=interval_seconds,
            priority=priority,
            metadata=metadata or {}
        )
        
        # Calcular próxima execução
        job.next_run = datetime.now() + timedelta(seconds=interval_seconds)
        
        self.jobs[id] = job
        self.logger.info(f"Job '{name}' adicionado com intervalo de {interval_seconds}s")
        
        return id
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove um job do scheduler.
        
        Args:
            job_id: ID do job a ser removido
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        if job_id in self.jobs:
            job = self.jobs.pop(job_id)
            self.logger.info(f"Job '{job.name}' removido")
            return True
        return False
    
    def start(self):
        """Inicia o scheduler."""
        if self.running:
            self.logger.warning("Scheduler já está rodando")
            return
        
        self.running = True
        self.logger.info("Scheduler iniciado")
        
        # Iniciar loop principal
        asyncio.create_task(self._main_loop())
    
    def stop(self):
        """Para o scheduler."""
        self.running = False
        self.logger.info("Scheduler parado")
    
    async def _main_loop(self):
        """Loop principal do scheduler."""
        while self.running:
            try:
                # Verificar jobs pendentes
                await self._check_pending_jobs()
                
                # Aguardar próximo ciclo
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Erro no loop principal: {e}")
                await asyncio.sleep(5)  # Aguardar antes de tentar novamente
    
    async def _check_pending_jobs(self):
        """Verifica e executa jobs pendentes."""
        now = datetime.now()
        
        # Filtrar jobs prontos para execução
        ready_jobs = [
            job for job in self.jobs.values()
            if job.status == JobStatus.PENDING and job.next_run <= now
        ]
        
        # Ordenar por prioridade (maior primeiro)
        ready_jobs.sort(key=lambda j: j.priority.value, reverse=True)
        
        # Executar jobs prontos
        for job in ready_jobs:
            await self._execute_job(job)
    
    async def _execute_job(self, job: ScheduledJob):
        """Executa um job específico."""
        try:
            # Marcar como executando
            job.status = JobStatus.RUNNING
            job.last_run = datetime.now()
            
            self.logger.info(f"Executando job '{job.name}'")
            
            # Executar função do job
            if asyncio.iscoroutinefunction(job.function):
                result = await job.function()
            else:
                result = job.function()
            
            # Marcar como concluído
            job.status = JobStatus.COMPLETED
            job.run_count += 1
            job.last_error = None
            
            # Calcular próxima execução
            job.next_run = datetime.now() + timedelta(seconds=job.interval_seconds)
            
            self.logger.info(f"Job '{job.name}' executado com sucesso")
            
        except Exception as e:
            # Marcar como falhado
            job.status = JobStatus.FAILED
            job.error_count += 1
            job.last_error = str(e)
            
            self.logger.error(f"Erro ao executar job '{job.name}': {e}")
            
            # Calcular próxima execução (com backoff exponencial)
            backoff_seconds = min(job.interval_seconds * (2 ** min(job.error_count, 5)), 3600)
            job.next_run = datetime.now() + timedelta(seconds=backoff_seconds)
    
    async def _collect_offers_job(self):
        """Job para coleta de ofertas."""
        self.logger.info("🔄 Coletando ofertas...")
        
        # Simular coleta de ofertas
        # Em produção, isso chamaria scrapers reais
        await asyncio.sleep(2)
        
        self.logger.info("✅ Ofertas coletadas com sucesso")
        return {"offers_collected": 10}
    
    async def _enrich_prices_job(self):
        """Job para enriquecimento de preços."""
        self.logger.info("💰 Enriquecendo preços...")
        
        # Simular enriquecimento de preços
        # Em produção, isso chamaria APIs de preços
        await asyncio.sleep(5)
        
        self.logger.info("✅ Preços enriquecidos com sucesso")
        return {"prices_enriched": 25}
    
    async def _post_queue_job(self):
        """Job para postagem na fila."""
        self.logger.info("📝 Processando fila de postagem...")
        
        # Simular processamento da fila
        # Em produção, isso postaria ofertas no Telegram
        await asyncio.sleep(1)
        
        self.logger.info("✅ Fila de postagem processada")
        return {"offers_posted": 3}
    
    async def _price_aggregate_job(self):
        """Job para agregação de preços."""
        self.logger.info("📊 Agregando preços...")
        
        # Simular agregação de preços
        # Em produção, isso analisaria histórico de preços
        await asyncio.sleep(3)
        
        self.logger.info("✅ Preços agregados com sucesso")
        return {"price_analysis": "completed"}
    
    def get_job_status(self, job_id: str) -> Optional[ScheduledJob]:
        """Retorna status de um job específico."""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[ScheduledJob]:
        """Retorna todos os jobs."""
        return list(self.jobs.values())
    
    def get_jobs_by_status(self, status: JobStatus) -> List[ScheduledJob]:
        """Retorna jobs filtrados por status."""
        return [job for job in self.jobs.values() if job.status == status]
    
    def pause_job(self, job_id: str) -> bool:
        """Pausa um job específico."""
        if job_id in self.jobs:
            self.jobs[job_id].status = JobStatus.CANCELLED
            self.logger.info(f"Job '{self.jobs[job_id].name}' pausado")
            return True
        return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume um job pausado."""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if job.status == JobStatus.CANCELLED:
                job.status = JobStatus.PENDING
                job.next_run = datetime.now()
                self.logger.info(f"Job '{job.name}' resumido")
                return True
        return False
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do scheduler."""
        total_jobs = len(self.jobs)
        running_jobs = len(self.get_jobs_by_status(JobStatus.RUNNING))
        completed_jobs = len(self.get_jobs_by_status(JobStatus.COMPLETED))
        failed_jobs = len(self.get_jobs_by_status(JobStatus.FAILED))
        
        total_runs = sum(job.run_count for job in self.jobs.values())
        total_errors = sum(job.error_count for job in self.jobs.values())
        
        return {
            "total_jobs": total_jobs,
            "running_jobs": running_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "total_runs": total_runs,
            "total_errors": total_errors,
            "success_rate": (total_runs - total_errors) / total_runs if total_runs > 0 else 0
        }


# Instância global do scheduler
post_scheduler = PostScheduler()

