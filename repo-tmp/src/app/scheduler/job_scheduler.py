#!/usr/bin/env python3
"""
Job Scheduler para o Sistema Garimpeiro Geek
Interface simplificada para agendamento de tarefas
"""

import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from .cron_manager import CronManager, JobPriority, JobStatus, ScheduledJob


class JobScheduler:
    """
    Interface simplificada para agendamento de jobs
    """

    def __init__(self, cron_manager: Optional[CronManager] = None):
        self.logger = logging.getLogger("scheduler.job_scheduler")
        self.cron_manager = cron_manager or CronManager()

        # Decoradores para funções
        self.scheduled_functions: Dict[str, Callable] = {}

        self.logger.info("JobScheduler inicializado")

    async def start(self) -> None:
        """Inicia o scheduler"""
        await self.cron_manager.start()
        self.logger.info("JobScheduler iniciado")

    async def stop(self) -> None:
        """Para o scheduler"""
        await self.cron_manager.stop()
        self.logger.info("JobScheduler parado")

    async def pause(self) -> None:
        """Pausa o scheduler"""
        await self.cron_manager.pause()
        self.logger.info("JobScheduler pausado")

    async def resume(self) -> None:
        """Resume o scheduler"""
        await self.cron_manager.resume()
        self.logger.info("JobScheduler resumido")

    def schedule(
        self,
        schedule: str,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> Callable:
        """
        Decorador para agendar uma função

        Args:
            schedule: Intervalo de execução (ex: 'every_90s', 'every_15m')
            priority: Prioridade do job
            max_retries: Número máximo de tentativas
            description: Descrição do job
            tags: Tags para categorização
        """

        def decorator(func: Callable) -> Callable:
            # Gerar ID único baseado no nome da função
            job_id = f"{func.__module__}.{func.__name__}"

            # Criar job
            job = ScheduledJob(
                id=job_id,
                name=func.__name__,
                function=job_id,
                schedule=schedule,
                priority=priority,
                max_retries=max_retries,
                description=description or f"Job {func.__name__}",
                tags=tags or [],
            )

            # Registrar função
            self.cron_manager.register_function(job_id, func)
            self.scheduled_functions[job_id] = func

            # Agendar job
            self.cron_manager.schedule_job(job)

            self.logger.info(f"Função {func.__name__} agendada para {schedule}")

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def schedule_function(
        self,
        func: Callable,
        schedule: str,
        job_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        description: str = "",
        tags: Optional[List[str]] = None,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Agenda uma função específica

        Args:
            func: Função a ser executada
            schedule: Intervalo de execução
            job_id: ID único do job (opcional)
            priority: Prioridade do job
            max_retries: Número máximo de tentativas
            description: Descrição do job
            tags: Tags para categorização
            args: Argumentos posicionais para a função
            kwargs: Argumentos nomeados para a função

        Returns:
            ID do job criado
        """
        if job_id is None:
            job_id = f"{func.__module__}.{func.__name__}"

        # Criar job
        job = ScheduledJob(
            id=job_id,
            name=func.__name__,
            function=job_id,
            schedule=schedule,
            args=args or [],
            kwargs=kwargs or {},
            priority=priority,
            max_retries=max_retries,
            description=description or f"Job {func.__name__}",
            tags=tags or [],
        )

        # Registrar função
        self.cron_manager.register_function(job_id, func)
        self.scheduled_functions[job_id] = func

        # Agendar job
        self.cron_manager.schedule_job(job)

        self.logger.info(
            f"Função {func.__name__} agendada para {schedule} com ID {job_id}"
        )
        return job_id

    def schedule_interval(
        self,
        interval_seconds: int,
        func: Callable,
        job_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        description: str = "",
        tags: Optional[List[str]] = None,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Agenda uma função para execução em intervalos específicos

        Args:
            interval_seconds: Intervalo em segundos
            func: Função a ser executada
            job_id: ID único do job (opcional)
            priority: Prioridade do job
            max_retries: Número máximo de tentativas
            description: Descrição do job
            tags: Tags para categorização
            args: Argumentos posicionais para a função
            kwargs: Argumentos nomeados para a função

        Returns:
            ID do job criado
        """
        # Converter para formato de schedule
        if interval_seconds < 60:
            schedule = f"every_{interval_seconds}s"
        elif interval_seconds < 3600:
            minutes = interval_seconds // 60
            schedule = f"every_{minutes}m"
        elif interval_seconds < 86400:
            hours = interval_seconds // 3600
            schedule = f"every_{hours}h"
        else:
            days = interval_seconds // 86400
            schedule = f"every_{days}d"

        return self.schedule_function(
            func=func,
            schedule=schedule,
            job_id=job_id,
            priority=priority,
            max_retries=max_retries,
            description=description,
            tags=tags,
            args=args,
            kwargs=kwargs,
        )

    def schedule_daily(
        self,
        hour: int = 0,
        minute: int = 0,
        func: Callable = None,
        job_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        description: str = "",
        tags: Optional[List[str]] = None,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Union[str, Callable]:
        """
        Agenda uma função para execução diária em horário específico

        Args:
            hour: Hora (0-23)
            minute: Minuto (0-59)
            func: Função a ser executada (se usado como decorador)
            job_id: ID único do job (opcional)
            priority: Prioridade do job
            max_retries: Número máximo de tentativas
            description: Descrição do job
            tags: Tags para categorização
            args: Argumentos posicionais para a função
            kwargs: Argumentos nomeados para a função

        Returns:
            ID do job criado ou decorador
        """
        schedule = f"daily_{hour:02d}:{minute:02d}"

        if func is None:
            # Usado como decorador
            return self.schedule(
                schedule=schedule,
                priority=priority,
                max_retries=max_retries,
                description=description,
                tags=tags,
            )(func)
        else:
            # Usado como função
            return self.schedule_function(
                func=func,
                schedule=schedule,
                job_id=job_id,
                priority=priority,
                max_retries=max_retries,
                description=description,
                tags=tags,
                args=args,
                kwargs=kwargs,
            )

    def schedule_weekly(
        self,
        day_of_week: int,  # 0=Segunda, 6=Domingo
        hour: int = 0,
        minute: int = 0,
        func: Callable = None,
        job_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        description: str = "",
        tags: Optional[List[str]] = None,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Union[str, Callable]:
        """
        Agenda uma função para execução semanal em dia e horário específicos

        Args:
            day_of_week: Dia da semana (0=Segunda, 6=Domingo)
            hour: Hora (0-23)
            minute: Minuto (0-59)
            func: Função a ser executada (se usado como decorador)
            job_id: ID único do job (opcional)
            priority: Prioridade do job
            max_retries: Número máximo de tentativas
            description: Descrição do job
            tags: Tags para categorização
            args: Argumentos posicionais para a função
            kwargs: Argumentos nomeados para a função

        Returns:
            ID do job criado ou decorador
        """
        days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        schedule = f"weekly_{days[day_of_week]}_{hour:02d}:{minute:02d}"

        if func is None:
            # Usado como decorador
            return self.schedule(
                schedule=schedule,
                priority=priority,
                max_retries=max_retries,
                description=description,
                tags=tags,
            )(func)
        else:
            # Usado como função
            return self.schedule_function(
                func=func,
                schedule=schedule,
                job_id=job_id,
                priority=priority,
                max_retries=max_retries,
                description=description,
                tags=tags,
                args=args,
                kwargs=kwargs,
            )

    def unschedule_job(self, job_id: str) -> bool:
        """Remove um job agendado"""
        return self.cron_manager.unschedule_job(job_id)

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Retorna um job específico"""
        return self.cron_manager.get_job(job_id)

    def get_all_jobs(self) -> List[ScheduledJob]:
        """Retorna todos os jobs"""
        return self.cron_manager.get_all_jobs()

    def get_jobs_by_status(self, status: JobStatus) -> List[ScheduledJob]:
        """Retorna jobs por status"""
        return self.cron_manager.get_jobs_by_status(status)

    def get_jobs_by_tag(self, tag: str) -> List[ScheduledJob]:
        """Retorna jobs por tag"""
        return self.cron_manager.get_jobs_by_tag(tag)

    def enable_job(self, job_id: str) -> bool:
        """Habilita um job"""
        return self.cron_manager.enable_job(job_id)

    def disable_job(self, job_id: str) -> bool:
        """Desabilita um job"""
        return self.cron_manager.disable_job(job_id)

    def get_status(self) -> Dict[str, Any]:
        """Retorna status do scheduler"""
        return self.cron_manager.get_status()

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do scheduler"""
        return self.cron_manager.get_metrics()

    # Atalhos para agendamentos comuns
    def every_90s(self, func: Callable = None, **kwargs) -> Union[str, Callable]:
        """Agenda função para execução a cada 90 segundos"""
        if func is None:
            return self.schedule("every_90s", **kwargs)
        else:
            return self.schedule_function(func, "every_90s", **kwargs)

    def every_15m(self, func: Callable = None, **kwargs) -> Union[str, Callable]:
        """Agenda função para execução a cada 15 minutos"""
        if func is None:
            return self.schedule("every_15m", **kwargs)
        else:
            return self.schedule_function(func, "every_15m", **kwargs)

    def every_30m(self, func: Callable = None, **kwargs) -> Union[str, Callable]:
        """Agenda função para execução a cada 30 minutos"""
        if func is None:
            return self.schedule("every_30m", **kwargs)
        else:
            return self.schedule_function(func, "every_30m", **kwargs)

    def every_45s(self, func: Callable = None, **kwargs) -> Union[str, Callable]:
        """Agenda função para execução a cada 45 segundos"""
        if func is None:
            return self.schedule("every_45s", **kwargs)
        else:
            return self.schedule_function(func, "every_45s", **kwargs)

    def every_hour(self, func: Callable = None, **kwargs) -> Union[str, Callable]:
        """Agenda função para execução a cada hora"""
        if func is None:
            return self.schedule("every_1h", **kwargs)
        else:
            return self.schedule_function(func, "every_1h", **kwargs)

    def every_6h(self, func: Callable = None, **kwargs) -> Union[str, Callable]:
        """Agenda função para execução a cada 6 horas"""
        if func is None:
            return self.schedule("every_6h", **kwargs)
        else:
            return self.schedule_function(func, "every_6h", **kwargs)

    def every_12h(self, func: Callable = None, **kwargs) -> Union[str, Callable]:
        """Agenda função para execução a cada 12 horas"""
        if func is None:
            return self.schedule("every_12h", **kwargs)
        else:
            return self.schedule_function(func, "every_12h", **kwargs)

    def every_day(self, func: Callable = None, **kwargs) -> Union[str, Callable]:
        """Agenda função para execução a cada dia"""
        if func is None:
            return self.schedule("every_1d", **kwargs)
        else:
            return self.schedule_function(func, "every_1d", **kwargs)
