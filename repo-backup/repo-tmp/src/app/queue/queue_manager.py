#!/usr/bin/env python3
"""
Gerenciador de Fila do Garimpeiro Geek
Coordena todos os componentes do sistema de fila de ofertas
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from src.core.models import Offer

from .moderation_system import (
    ModerationSystem,
)
from .offer_queue import OfferQueue, QueuePriority, QueueStatus
from .quality_controller import QualityController


class QueueManagerStatus(Enum):
    """Status do gerenciador de fila"""

    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class QueueManagerConfig:
    """Configuração do gerenciador de fila"""

    # Configurações de processamento
    auto_process_enabled: bool = True
    auto_process_interval: int = 30  # segundos
    auto_process_threshold: float = 0.7  # Score mínimo para aprovação automática

    # Configurações de moderação
    moderation_enabled: bool = True
    auto_assign_enabled: bool = True
    auto_assign_interval: int = 60  # segundos

    # Configurações de qualidade
    quality_evaluation_enabled: bool = True
    min_quality_score: float = 0.4  # Score mínimo para entrar na fila

    # Configurações de limpeza
    cleanup_enabled: bool = True
    cleanup_interval: int = 3600  # segundos (1 hora)
    max_queue_age_hours: int = 24  # Idade máxima das ofertas na fila

    # Configurações de notificação
    notifications_enabled: bool = True
    notification_callbacks: List[Callable] = field(default_factory=list)


class QueueManager:
    """
    Gerenciador principal que coordena todos os componentes do sistema de fila
    """

    def __init__(self, config: Optional[QueueManagerConfig] = None):
        self.logger = logging.getLogger("queue.manager")

        # Configuração
        self.config = config or QueueManagerConfig()

        # Componentes
        self.offer_queue = OfferQueue()
        self.moderation_system = ModerationSystem(self.offer_queue)
        self.quality_controller = QualityController()

        # Status e controle
        self.status = QueueManagerStatus.STOPPED
        self.is_running = False
        self.tasks: List[asyncio.Task] = []

        # Métricas e estatísticas
        self.stats = {
            "total_offers_processed": 0,
            "offers_approved": 0,
            "offers_rejected": 0,
            "offers_sent_to_moderation": 0,
            "moderation_tasks_completed": 0,
            "quality_evaluations": 0,
            "errors": 0,
            "last_activity": None,
        }

        # Callbacks de eventos
        self.event_callbacks: Dict[str, List[Callable]] = {
            "offer_added": [],
            "offer_approved": [],
            "offer_rejected": [],
            "offer_sent_to_moderation": [],
            "moderation_completed": [],
            "quality_evaluated": [],
            "error_occurred": [],
        }

        # Histórico de atividades
        self.activity_log: List[Dict[str, Any]] = []

        self.logger.info("QueueManager inicializado")

    async def start(self) -> bool:
        """
        Inicia o gerenciador de fila

        Returns:
            True se iniciado com sucesso
        """
        try:
            if self.is_running:
                self.logger.warning("QueueManager já está rodando")
                return True

            self.logger.info("Iniciando QueueManager...")

            # Iniciar tarefas em background
            self.tasks = [
                asyncio.create_task(self._auto_process_loop()),
                asyncio.create_task(self._auto_assign_loop()),
                asyncio.create_task(self._cleanup_loop()),
                asyncio.create_task(self._stats_update_loop()),
            ]

            self.is_running = True
            self.status = QueueManagerStatus.RUNNING
            self.stats["last_activity"] = datetime.now()

            self.logger.info("QueueManager iniciado com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao iniciar QueueManager: {e}")
            self.status = QueueManagerStatus.ERROR
            self.stats["errors"] += 1
            return False

    async def stop(self) -> bool:
        """
        Para o gerenciador de fila

        Returns:
            True se parado com sucesso
        """
        try:
            if not self.is_running:
                self.logger.warning("QueueManager não está rodando")
                return True

            self.logger.info("Parando QueueManager...")

            # Cancelar tarefas
            for task in self.tasks:
                if not task.done():
                    task.cancel()

            # Aguardar cancelamento
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)

            self.tasks.clear()
            self.is_running = False
            self.status = QueueManagerStatus.STOPPED
            self.stats["last_activity"] = datetime.now()

            self.logger.info("QueueManager parado com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao parar QueueManager: {e}")
            self.status = QueueManagerStatus.ERROR
            self.stats["errors"] += 1
            return False

    async def pause(self) -> bool:
        """
        Pausa o gerenciador de fila

        Returns:
            True se pausado com sucesso
        """
        try:
            if not self.is_running:
                self.logger.warning("QueueManager não está rodando")
                return False

            self.logger.info("Pausando QueueManager...")
            self.status = QueueManagerStatus.PAUSED
            self.stats["last_activity"] = datetime.now()

            self.logger.info("QueueManager pausado")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao pausar QueueManager: {e}")
            self.status = QueueManagerStatus.ERROR
            self.stats["errors"] += 1
            return False

    async def resume(self) -> bool:
        """
        Resume o gerenciador de fila

        Returns:
            True se resumido com sucesso
        """
        try:
            if not self.is_running:
                self.logger.warning("QueueManager não está rodando")
                return False

            if self.status != QueueManagerStatus.PAUSED:
                self.logger.warning("QueueManager não está pausado")
                return False

            self.logger.info("Resumindo QueueManager...")
            self.status = QueueManagerStatus.RUNNING
            self.stats["last_activity"] = datetime.now()

            self.logger.info("QueueManager resumido")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao resumir QueueManager: {e}")
            self.status = QueueManagerStatus.ERROR
            self.stats["errors"] += 1
            return False

    async def add_offer(
        self,
        offer: Offer,
        priority: Optional[QueuePriority] = None,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Adiciona uma oferta à fila

        Args:
            offer: Oferta a ser adicionada
            priority: Prioridade da oferta
            source: Fonte da oferta
            metadata: Metadados adicionais

        Returns:
            ID da oferta na fila
        """
        try:
            self.logger.info(f"Adicionando oferta à fila: {offer.title[:50]}...")

            # Avaliar qualidade se habilitado
            if self.config.quality_evaluation_enabled:
                quality_metrics = await self.quality_controller.evaluate_offer(offer)

                # Verificar score mínimo
                if quality_metrics.overall_score < self.config.min_quality_score:
                    self.logger.warning(
                        f"Oferta rejeitada por score baixo: {quality_metrics.overall_score:.2f}"
                    )
                    self.stats["offers_rejected"] += 1
                    self._log_activity(
                        "offer_rejected",
                        {
                            "offer_title": offer.title,
                            "reason": "score_baixo",
                            "score": quality_metrics.overall_score,
                        },
                    )
                    return ""

                # Usar prioridade baseada na qualidade se não especificada
                if priority is None:
                    priority = self.quality_controller.get_priority_recommendation(
                        quality_metrics
                    )

                # Adicionar metadados de qualidade
                if metadata is None:
                    metadata = {}
                metadata["quality_metrics"] = quality_metrics
                metadata["quality_score"] = quality_metrics.overall_score

                self.stats["quality_evaluations"] += 1
                self._trigger_event(
                    "quality_evaluated", {"offer": offer, "metrics": quality_metrics}
                )

            # Adicionar à fila
            queue_id = self.offer_queue.add_offer(
                offer=offer,
                priority=priority or QueuePriority.NORMAL,
                source=source,
                metadata=metadata,
            )

            if queue_id:
                self.stats["total_offers_processed"] += 1
                self.stats["last_activity"] = datetime.now()

                self._log_activity(
                    "offer_added",
                    {
                        "queue_id": queue_id,
                        "offer_title": offer.title,
                        "priority": priority.name if priority else "NORMAL",
                        "source": source,
                    },
                )

                self._trigger_event(
                    "offer_added",
                    {
                        "queue_id": queue_id,
                        "offer": offer,
                        "priority": priority,
                        "source": source,
                    },
                )

                self.logger.info(f"Oferta adicionada à fila com ID: {queue_id}")
            else:
                self.logger.error("Falha ao adicionar oferta à fila")
                self.stats["errors"] += 1

            return queue_id

        except Exception as e:
            self.logger.error(f"Erro ao adicionar oferta: {e}")
            self.stats["errors"] += 1
            self._trigger_event(
                "error_occurred",
                {"error": str(e), "operation": "add_offer", "offer": offer},
            )
            return ""

    async def process_offer(
        self,
        queue_id: str,
        action: str,
        moderator_id: Optional[str] = None,
        notes: str = "",
    ) -> bool:
        """
        Processa uma oferta da fila

        Args:
            queue_id: ID da oferta na fila
            action: Ação a ser executada ('approve', 'reject', 'moderate')
            moderator_id: ID do moderador (se aplicável)
            notes: Notas sobre a ação

        Returns:
            True se processado com sucesso
        """
        try:
            self.logger.info(f"Processando oferta {queue_id} com ação: {action}")

            if action == "approve":
                success = self.offer_queue.approve_offer(queue_id, notes)
                if success:
                    self.stats["offers_approved"] += 1
                    self._trigger_event(
                        "offer_approved",
                        {
                            "queue_id": queue_id,
                            "moderator_id": moderator_id,
                            "notes": notes,
                        },
                    )

            elif action == "reject":
                success = self.offer_queue.reject_offer(queue_id, notes)
                if success:
                    self.stats["offers_rejected"] += 1
                    self._trigger_event(
                        "offer_rejected",
                        {
                            "queue_id": queue_id,
                            "moderator_id": moderator_id,
                            "notes": notes,
                        },
                    )

            elif action == "moderate":
                success = self.offer_queue.send_to_moderation(queue_id, notes)
                if success:
                    self.stats["offers_sent_to_moderation"] += 1
                    self._trigger_event(
                        "offer_sent_to_moderation",
                        {"queue_id": queue_id, "notes": notes},
                    )

            else:
                self.logger.error(f"Ação inválida: {action}")
                return False

            if success:
                self.stats["last_activity"] = datetime.now()
                self._log_activity(
                    f"offer_{action}",
                    {
                        "queue_id": queue_id,
                        "moderator_id": moderator_id,
                        "notes": notes,
                    },
                )

            return success

        except Exception as e:
            self.logger.error(f"Erro ao processar oferta: {e}")
            self.stats["errors"] += 1
            self._trigger_event(
                "error_occurred",
                {"error": str(e), "operation": "process_offer", "queue_id": queue_id},
            )
            return False

    async def get_queue_status(self) -> Dict[str, Any]:
        """
        Obtém status atual da fila

        Returns:
            Status da fila
        """
        try:
            queue_stats = self.offer_queue.get_stats()
            moderation_stats = self.moderation_system.get_stats()

            return {
                "manager_status": self.status.value,
                "is_running": self.is_running,
                "queue_stats": queue_stats,
                "moderation_stats": moderation_stats,
                "quality_stats": {
                    "total_evaluations": self.stats["quality_evaluations"],
                    "min_quality_score": self.config.min_quality_score,
                },
                "manager_stats": self.stats,
                "config": {
                    "auto_process_enabled": self.config.auto_process_enabled,
                    "moderation_enabled": self.config.moderation_enabled,
                    "quality_evaluation_enabled": self.config.quality_evaluation_enabled,
                },
                "last_activity": (
                    self.stats["last_activity"].isoformat()
                    if self.stats["last_activity"]
                    else None
                ),
            }

        except Exception as e:
            self.logger.error(f"Erro ao obter status da fila: {e}")
            return {"error": str(e)}

    async def get_offer_details(self, queue_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de uma oferta na fila

        Args:
            queue_id: ID da oferta

        Returns:
            Detalhes da oferta ou None se não encontrada
        """
        try:
            queued_offer = self.offer_queue.get_offer_by_id(queue_id)
            if not queued_offer:
                return None

            # Obter métricas de qualidade se disponíveis
            quality_info = None
            if "quality_metrics" in queued_offer.metadata:
                quality_info = self.quality_controller.get_quality_summary(
                    queued_offer.metadata["quality_metrics"]
                )

            # Obter tarefa de moderação se existir
            moderation_task = None
            if queued_offer.status == QueueStatus.MODERATION:
                moderation_task = self.moderation_system.get_task_by_offer_id(queue_id)

            return {
                "queue_id": queued_offer.id,
                "offer": queued_offer.offer,
                "status": queued_offer.status.value,
                "priority": queued_offer.priority.value,
                "score": queued_offer.score,
                "added_at": queued_offer.added_at.isoformat(),
                "processed_at": (
                    queued_offer.processed_at.isoformat()
                    if queued_offer.processed_at
                    else None
                ),
                "scheduled_for": (
                    queued_offer.scheduled_for.isoformat()
                    if queued_offer.scheduled_for
                    else None
                ),
                "moderation_notes": queued_offer.moderation_notes,
                "quality_score": queued_offer.quality_score,
                "retry_count": queued_offer.retry_count,
                "tags": queued_offer.tags,
                "metadata": queued_offer.metadata,
                "quality_info": quality_info,
                "moderation_task": moderation_task,
            }

        except Exception as e:
            self.logger.error(f"Erro ao obter detalhes da oferta: {e}")
            return None

    def add_event_callback(self, event: str, callback: Callable) -> None:
        """
        Adiciona callback para eventos

        Args:
            event: Nome do evento
            callback: Função callback
        """
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
        else:
            self.logger.warning(f"Evento desconhecido: {event}")

    def remove_event_callback(self, event: str, callback: Callable) -> None:
        """
        Remove callback de eventos

        Args:
            event: Nome do evento
            callback: Função callback
        """
        if event in self.event_callbacks and callback in self.event_callbacks[event]:
            self.event_callbacks[event].remove(callback)

    def _trigger_event(self, event: str, data: Dict[str, Any]) -> None:
        """Dispara um evento para todos os callbacks registrados"""
        try:
            if event in self.event_callbacks:
                for callback in self.event_callbacks[event]:
                    try:
                        callback(data)
                    except Exception as e:
                        self.logger.error(f"Erro no callback do evento {event}: {e}")
        except Exception as e:
            self.logger.error(f"Erro ao disparar evento {event}: {e}")

    def _log_activity(self, activity_type: str, data: Dict[str, Any]) -> None:
        """Registra atividade no log"""
        try:
            activity = {
                "timestamp": datetime.now().isoformat(),
                "type": activity_type,
                "data": data,
            }
            self.activity_log.append(activity)

            # Manter apenas as últimas 1000 atividades
            if len(self.activity_log) > 1000:
                self.activity_log = self.activity_log[-1000:]

        except Exception as e:
            self.logger.error(f"Erro ao registrar atividade: {e}")

    async def _auto_process_loop(self) -> None:
        """Loop de processamento automático"""
        while self.is_running:
            try:
                if (
                    self.status == QueueManagerStatus.RUNNING
                    and self.config.auto_process_enabled
                ):

                    # Processar ofertas automaticamente
                    results = self.offer_queue.auto_process_offers()

                    if results:
                        self.logger.info(f"Processamento automático: {results}")

                        # Atualizar estatísticas
                        self.stats["offers_approved"] += results.get("approved", 0)
                        self.stats["offers_rejected"] += results.get("rejected", 0)
                        self.stats["last_activity"] = datetime.now()

                await asyncio.sleep(self.config.auto_process_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no loop de processamento automático: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(5)  # Aguardar antes de tentar novamente

    async def _auto_assign_loop(self) -> None:
        """Loop de atribuição automática de tarefas"""
        while self.is_running:
            try:
                if (
                    self.status == QueueManagerStatus.RUNNING
                    and self.config.auto_assign_enabled
                ):

                    # Atribuir tarefas automaticamente
                    results = self.moderation_system.auto_assign_tasks()

                    if results:
                        self.logger.info(f"Atribuição automática: {results}")
                        self.stats["last_activity"] = datetime.now()

                await asyncio.sleep(self.config.auto_assign_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no loop de atribuição automática: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(5)

    async def _cleanup_loop(self) -> None:
        """Loop de limpeza"""
        while self.is_running:
            try:
                if (
                    self.status == QueueManagerStatus.RUNNING
                    and self.config.cleanup_enabled
                ):

                    # Limpar histórico de avaliações
                    removed_evaluations = (
                        self.quality_controller.clear_evaluation_history()
                    )
                    if removed_evaluations > 0:
                        self.logger.info(
                            f"Removidas {removed_evaluations} avaliações antigas"
                        )

                    # Limpar log de atividades
                    if len(self.activity_log) > 1000:
                        self.activity_log = self.activity_log[-500:]
                        self.logger.info("Log de atividades limpo")

                    self.stats["last_activity"] = datetime.now()

                await asyncio.sleep(self.config.cleanup_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no loop de limpeza: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(60)

    async def _stats_update_loop(self) -> None:
        """Loop de atualização de estatísticas"""
        while self.is_running:
            try:
                # Atualizar estatísticas da fila
                queue_stats = self.offer_queue.get_stats()
                moderation_stats = self.moderation_system.get_stats()

                # Atualizar estatísticas gerais
                self.stats.update(
                    {
                        "queue_size": queue_stats.get("total_offers", 0),
                        "pending_offers": queue_stats.get("pending_offers", 0),
                        "moderation_tasks": moderation_stats.get("total_tasks", 0),
                        "pending_moderation": moderation_stats.get("pending_tasks", 0),
                    }
                )

                await asyncio.sleep(30)  # Atualizar a cada 30 segundos

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no loop de estatísticas: {e}")
                await asyncio.sleep(60)

    def export_config(self) -> Dict[str, Any]:
        """Exporta configuração atual"""
        return {
            "auto_process_enabled": self.config.auto_process_enabled,
            "auto_process_interval": self.config.auto_process_interval,
            "auto_process_threshold": self.config.auto_process_threshold,
            "moderation_enabled": self.config.moderation_enabled,
            "auto_assign_enabled": self.config.auto_assign_enabled,
            "auto_assign_interval": self.config.auto_assign_interval,
            "quality_evaluation_enabled": self.config.quality_evaluation_enabled,
            "min_quality_score": self.config.min_quality_score,
            "cleanup_enabled": self.config.cleanup_enabled,
            "cleanup_interval": self.config.cleanup_interval,
            "max_queue_age_hours": self.config.max_queue_age_hours,
            "notifications_enabled": self.config.notifications_enabled,
        }

    def import_config(self, config_data: Dict[str, Any]) -> bool:
        """Importa configuração"""
        try:
            for key, value in config_data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            self.logger.info("Configuração importada com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao importar configuração: {e}")
            return False

    def get_activity_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtém log de atividades"""
        return self.activity_log[-limit:] if limit > 0 else self.activity_log

    def clear_activity_log(self) -> int:
        """Limpa log de atividades"""
        count = len(self.activity_log)
        self.activity_log.clear()
        return count
