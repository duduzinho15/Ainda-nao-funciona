#!/usr/bin/env python3
"""
Sistema de Moderação do Garimpeiro Geek
Gerencia revisão manual de ofertas e controle de qualidade
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .offer_queue import QueuedOffer, QueuePriority, QueueStatus


class ModerationStatus(Enum):
    """Status de moderação"""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"
    ESCALATED = "escalated"


class ModerationLevel(Enum):
    """Nível de moderação"""

    BASIC = "basic"  # Moderação básica
    STANDARD = "standard"  # Moderação padrão
    STRICT = "strict"  # Moderação rigorosa
    EXPERT = "expert"  # Moderação especializada


@dataclass
class ModerationTask:
    """Tarefa de moderação"""

    id: str
    queued_offer: QueuedOffer
    status: ModerationStatus = ModerationStatus.PENDING
    level: ModerationLevel = ModerationLevel.STANDARD
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewer_notes: str = ""
    decision: Optional[str] = None
    decision_reason: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    priority: QueuePriority = QueuePriority.NORMAL
    tags: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)

    def is_overdue(self, max_hours: int = 24) -> bool:
        """Verifica se a tarefa está atrasada"""
        if self.assigned_at:
            return datetime.now() - self.assigned_at > timedelta(hours=max_hours)
        return datetime.now() - self.created_at > timedelta(hours=max_hours)


class ModerationSystem:
    """
    Sistema de moderação para revisão manual de ofertas
    """

    def __init__(self, offer_queue=None):
        self.logger = logging.getLogger("queue.moderation_system")
        self.offer_queue = offer_queue

        # Tarefas de moderação
        self.moderation_tasks: Dict[str, ModerationTask] = {}

        # Moderadores disponíveis
        self.moderators: Dict[str, Dict[str, Any]] = {}

        # Configurações
        self.auto_escalation_hours = 48  # Escalar após 48 horas
        self.max_concurrent_tasks = 10  # Máximo de tarefas por moderador
        self.quality_thresholds = {
            ModerationLevel.BASIC: 0.6,
            ModerationLevel.STANDARD: 0.7,
            ModerationLevel.STRICT: 0.8,
            ModerationLevel.EXPERT: 0.9,
        }

        # Estatísticas
        self.stats = {
            "total_tasks": 0,
            "pending_tasks": 0,
            "in_review": 0,
            "completed_tasks": 0,
            "avg_review_time": 0.0,
            "escalated_tasks": 0,
        }

        # Callbacks
        self.on_task_created: Optional[Callable[[ModerationTask], None]] = None
        self.on_task_assigned: Optional[Callable[[ModerationTask], None]] = None
        self.on_task_completed: Optional[Callable[[ModerationTask], None]] = None
        self.on_task_escalated: Optional[Callable[[ModerationTask], None]] = None

        self.logger.info("ModerationSystem inicializado")

    def create_moderation_task(
        self,
        queued_offer: QueuedOffer,
        level: ModerationLevel = ModerationLevel.STANDARD,
        priority: QueuePriority = QueuePriority.NORMAL,
        tags: Optional[List[str]] = None,
        flags: Optional[List[str]] = None,
    ) -> str:
        """
        Cria uma nova tarefa de moderação

        Args:
            queued_offer: Oferta na fila
            level: Nível de moderação
            priority: Prioridade da tarefa
            tags: Tags para categorização
            flags: Flags especiais

        Returns:
            ID da tarefa de moderação
        """
        # Gerar ID único
        task_id = str(uuid.uuid4())

        # Criar tarefa
        task = ModerationTask(
            id=task_id,
            queued_offer=queued_offer,
            level=level,
            priority=priority,
            tags=tags or [],
            flags=flags or [],
        )

        # Adicionar à lista de tarefas
        self.moderation_tasks[task_id] = task

        # Atualizar estatísticas
        self.stats["total_tasks"] += 1
        self.stats["pending_tasks"] += 1

        self.logger.info(
            f"Tarefa de moderação criada: {task_id} (nível: {level.name}, prioridade: {priority.name})"
        )

        # Executar callback
        if self.on_task_created:
            try:
                self.on_task_created(task)
            except Exception as e:
                self.logger.error(f"Erro no callback on_task_created: {e}")

        return task_id

    def assign_task(self, task_id: str, moderator_id: str) -> bool:
        """
        Atribui uma tarefa a um moderador

        Args:
            task_id: ID da tarefa
            moderator_id: ID do moderador

        Returns:
            True se atribuída com sucesso
        """
        if task_id not in self.moderation_tasks:
            self.logger.warning(f"Tarefa não encontrada: {task_id}")
            return False

        if moderator_id not in self.moderators:
            self.logger.warning(f"Moderador não encontrado: {moderator_id}")
            return False

        task = self.moderation_tasks[task_id]

        # Verificar se moderador pode receber mais tarefas
        current_tasks = self.get_moderator_tasks(moderator_id)
        if len(current_tasks) >= self.max_concurrent_tasks:
            self.logger.warning(f"Moderador {moderator_id} atingiu limite de tarefas")
            return False

        # Atribuir tarefa
        task.assigned_to = moderator_id
        task.assigned_at = datetime.now()
        task.status = ModerationStatus.IN_REVIEW
        task.updated_at = datetime.now()

        # Atualizar estatísticas
        self.stats["pending_tasks"] -= 1
        self.stats["in_review"] += 1

        self.logger.info(f"Tarefa {task_id} atribuída ao moderador {moderator_id}")

        # Executar callback
        if self.on_task_assigned:
            try:
                self.on_task_assigned(task)
            except Exception as e:
                self.logger.error(f"Erro no callback on_task_assigned: {e}")

        return True

    def complete_task(
        self, task_id: str, decision: str, reason: str, notes: str = ""
    ) -> bool:
        """
        Completa uma tarefa de moderação

        Args:
            task_id: ID da tarefa
            decision: Decisão tomada (approve/reject/needs_changes)
            reason: Motivo da decisão
            notes: Notas adicionais

        Returns:
            True se completada com sucesso
        """
        if task_id not in self.moderation_tasks:
            self.logger.warning(f"Tarefa não encontrada: {task_id}")
            return False

        task = self.moderation_tasks[task_id]
        task.status = ModerationStatus.COMPLETED
        task.decision = decision
        task.decision_reason = reason
        task.reviewer_notes = notes
        task.reviewed_at = datetime.now()
        task.updated_at = datetime.now()

        # Atualizar estatísticas
        self.stats["in_review"] -= 1
        self.stats["completed_tasks"] += 1

        # Aplicar decisão na fila de ofertas
        if self.offer_queue:
            if decision == "approve":
                self.offer_queue.approve_offer(
                    task.queued_offer.id, f"Moderado por {task.assigned_to}: {reason}"
                )
            elif decision == "reject":
                self.offer_queue.reject_offer(
                    task.queued_offer.id, f"Rejeitado por {task.assigned_to}: {reason}"
                )
            elif decision == "needs_changes":
                # Retornar à fila com status de moderação
                task.queued_offer.status = QueueStatus.MODERATION
                task.queued_offer.moderation_notes = f"Alterações necessárias: {reason}"

        self.logger.info(f"Tarefa {task_id} completada: {decision} - {reason}")

        # Executar callback
        if self.on_task_completed:
            try:
                self.on_task_completed(task)
            except Exception as e:
                self.logger.error(f"Erro no callback on_task_completed: {e}")

        return True

    def escalate_task(self, task_id: str, reason: str = "") -> bool:
        """
        Escala uma tarefa para nível superior

        Args:
            task_id: ID da tarefa
            reason: Motivo da escalação

        Returns:
            True se escalada com sucesso
        """
        if task_id not in self.moderation_tasks:
            self.logger.warning(f"Tarefa não encontrada: {task_id}")
            return False

        task = self.moderation_tasks[task_id]

        # Escalar nível de moderação
        if task.level == ModerationLevel.BASIC:
            task.level = ModerationLevel.STANDARD
        elif task.level == ModerationLevel.STANDARD:
            task.level = ModerationLevel.STRICT
        elif task.level == ModerationLevel.STRICT:
            task.level = ModerationLevel.EXPERT
        else:
            # Já no nível máximo
            self.logger.warning(
                f"Tarefa {task_id} já está no nível máximo de moderação"
            )
            return False

        # Resetar atribuição
        task.assigned_to = None
        task.assigned_at = None
        task.status = ModerationStatus.PENDING

        # Atualizar estatísticas
        self.stats["in_review"] -= 1
        self.stats["pending_tasks"] += 1
        self.stats["escalated_tasks"] += 1

        self.logger.info(
            f"Tarefa {task_id} escalada para nível {task.level.name}: {reason}"
        )

        # Executar callback
        if self.on_task_escalated:
            try:
                self.on_task_escalated(task)
            except Exception as e:
                self.logger.error(f"Erro no callback on_task_escalated: {e}")

        return True

    def add_moderator(
        self,
        name: str,
        moderator_id: Optional[str] = None,
        level: ModerationLevel = ModerationLevel.STANDARD,
        skills: Optional[List[str]] = None,
        max_tasks: Optional[int] = None,
    ) -> None:
        """
        Adiciona um moderador ao sistema

        Args:
            name: Nome do moderador
            moderator_id: ID único do moderador (opcional, usa nome se None)
            level: Nível de moderação
            skills: Habilidades específicas
            max_tasks: Limite de tarefas (usa padrão se None)
        """
        if moderator_id is None:
            moderator_id = name.lower().replace(" ", "_")

        self.moderators[moderator_id] = {
            "name": name,
            "level": level,
            "skills": skills or [],
            "max_tasks": max_tasks or self.max_concurrent_tasks,
            "active_tasks": 0,
            "total_reviewed": 0,
            "avg_review_time": 0.0,
            "joined_at": datetime.now(),
        }

        self.logger.info(
            f"Moderador adicionado: {name} (ID: {moderator_id}, nível: {level.name})"
        )

    def remove_moderator(self, moderator_id: str) -> bool:
        """
        Remove um moderador do sistema

        Args:
            moderator_id: ID do moderador

        Returns:
            True se removido com sucesso
        """
        if moderator_id not in self.moderators:
            self.logger.warning(f"Moderador não encontrado: {moderator_id}")
            return False

        # Verificar se há tarefas ativas
        active_tasks = self.get_moderator_tasks(moderator_id)
        if active_tasks:
            self.logger.warning(
                f"Moderador {moderator_id} tem {len(active_tasks)} tarefas ativas"
            )
            return False

        # Remover moderador
        moderator_name = self.moderators[moderator_id]["name"]
        del self.moderators[moderator_id]

        self.logger.info(f"Moderador removido: {moderator_name} (ID: {moderator_id})")
        return True

    def get_available_moderators(
        self, level: Optional[ModerationLevel] = None
    ) -> List[str]:
        """
        Obtém lista de moderadores disponíveis

        Args:
            level: Nível de moderação específico (opcional)

        Returns:
            Lista de IDs de moderadores disponíveis
        """
        available = []

        for moderator_id, moderator in self.moderators.items():
            # Verificar nível
            if level and moderator["level"].value < level.value:
                continue

            # Verificar se pode receber mais tarefas
            current_tasks = len(self.get_moderator_tasks(moderator_id))
            if current_tasks < moderator["max_tasks"]:
                available.append(moderator_id)

        return available

    def get_moderator_tasks(self, moderator_id: str) -> List[ModerationTask]:
        """
        Obtém tarefas de um moderador específico

        Args:
            moderator_id: ID do moderador

        Returns:
            Lista de tarefas do moderador
        """
        return [
            task
            for task in self.moderation_tasks.values()
            if task.assigned_to == moderator_id
            and task.status == ModerationStatus.IN_REVIEW
        ]

    def get_task(self, task_id: str) -> Optional[ModerationTask]:
        """
        Obtém uma tarefa específica

        Args:
            task_id: ID da tarefa

        Returns:
            Tarefa ou None se não encontrada
        """
        return self.moderation_tasks.get(task_id)

    def get_tasks_by_status(self, status: ModerationStatus) -> List[ModerationTask]:
        """
        Obtém tarefas por status

        Args:
            status: Status desejado

        Returns:
            Lista de tarefas com o status especificado
        """
        return [
            task for task in self.moderation_tasks.values() if task.status == status
        ]

    def get_tasks_by_level(self, level: ModerationLevel) -> List[ModerationTask]:
        """
        Obtém tarefas por nível de moderação

        Args:
            level: Nível desejado

        Returns:
            Lista de tarefas com o nível especificado
        """
        return [task for task in self.moderation_tasks.values() if task.level == level]

    def get_overdue_tasks(self, max_hours: int = 24) -> List[ModerationTask]:
        """
        Obtém tarefas atrasadas

        Args:
            max_hours: Horas máximas antes de considerar atrasada

        Returns:
            Lista de tarefas atrasadas
        """
        return [
            task
            for task in self.moderation_tasks.values()
            if task.is_overdue(max_hours)
        ]

    def auto_assign_tasks(self) -> Dict[str, int]:
        """
        Atribui automaticamente tarefas pendentes aos moderadores

        Returns:
            Estatísticas da atribuição automática
        """
        assigned = 0
        skipped = 0
        escalated = 0

        # Obter tarefas pendentes ordenadas por prioridade
        pending_tasks = sorted(
            self.get_tasks_by_status(ModerationStatus.PENDING),
            key=lambda x: (x.priority.value, x.created_at),
            reverse=True,
        )

        for task in pending_tasks:
            # Verificar se tarefa está muito antiga
            if task.is_overdue(self.auto_escalation_hours):
                self.escalate_task(task.id, "Escalação automática por tempo limite")
                escalated += 1
                continue

            # Encontrar moderador disponível
            available_moderators = self.get_available_moderators(task.level)

            if available_moderators:
                # Atribuir ao primeiro moderador disponível
                moderator_id = available_moderators[0]
                if self.assign_task(task.id, moderator_id):
                    assigned += 1
                else:
                    skipped += 1
            else:
                # Nenhum moderador disponível
                skipped += 1

        self.logger.info(
            f"Atribuição automática: {assigned} atribuídas, {skipped} ignoradas, {escalated} escaladas"
        )

        return {"assigned": assigned, "skipped": skipped, "escalated": escalated}

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema de moderação"""
        # Calcular estatísticas em tempo real
        if self.stats["completed_tasks"] > 0:
            self.stats["avg_review_time"] = self._calculate_avg_review_time()

        return self.stats.copy()

    def get_moderator_stats(self, moderator_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém estatísticas de um moderador específico

        Args:
            moderator_id: ID do moderador

        Returns:
            Estatísticas do moderador ou None se não encontrado
        """
        if moderator_id not in self.moderators:
            return None

        moderator = self.moderators[moderator_id]
        active_tasks = len(self.get_moderator_tasks(moderator_id))

        return {
            "id": moderator_id,
            "name": moderator["name"],
            "level": moderator["level"].name,
            "skills": moderator["skills"],
            "active_tasks": active_tasks,
            "max_tasks": moderator["max_tasks"],
            "total_reviewed": moderator["total_reviewed"],
            "avg_review_time": moderator["avg_review_time"],
            "joined_at": moderator["joined_at"].isoformat(),
            "utilization": (
                (active_tasks / moderator["max_tasks"]) * 100
                if moderator["max_tasks"] > 0
                else 0
            ),
        }

    def _calculate_avg_review_time(self) -> float:
        """Calcula tempo médio de revisão"""
        review_times = []

        for task in self.moderation_tasks.values():
            if (
                task.reviewed_at
                and task.assigned_at
                and task.status == ModerationStatus.COMPLETED
            ):
                review_time = (task.reviewed_at - task.assigned_at).total_seconds()
                review_times.append(review_time)

        if review_times:
            return sum(review_times) / len(review_times)
        return 0.0

    def cleanup_old_tasks(self, max_age_days: int = 30) -> int:
        """
        Remove tarefas antigas completadas

        Args:
            max_age_days: Idade máxima em dias

        Returns:
            Número de tarefas removidas
        """
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        removed_count = 0

        # Tarefas a serem removidas
        to_remove = []

        for task_id, task in self.moderation_tasks.items():
            if (
                task.status == ModerationStatus.COMPLETED
                and task.reviewed_at
                and task.reviewed_at < cutoff_time
            ):
                to_remove.append(task_id)

        # Remover tarefas
        for task_id in to_remove:
            del self.moderation_tasks[task_id]
            removed_count += 1

        self.logger.info(f"Removidas {removed_count} tarefas antigas")
        return removed_count
