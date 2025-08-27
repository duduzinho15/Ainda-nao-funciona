#!/usr/bin/env python3
"""
Sistema de Fila de Ofertas do Garimpeiro Geek
Gerencia fila de processamento com priorização e controle de qualidade
"""

import heapq
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from src.core.models import Offer


class QueueStatus(Enum):
    """Status de uma oferta na fila"""

    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODERATION = "moderation"
    SCHEDULED = "scheduled"
    ERROR = "error"


class QueuePriority(Enum):
    """Prioridade de uma oferta na fila"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class QueuedOffer:
    """Representa uma oferta na fila"""

    id: str
    offer: Offer
    status: QueueStatus = QueueStatus.PENDING
    priority: QueuePriority = QueuePriority.NORMAL
    score: float = 0.0
    added_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    scheduled_for: Optional[datetime] = None
    moderation_notes: str = ""
    quality_score: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        """Comparação para heap de prioridade (maior prioridade primeiro)"""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value

        # Se prioridade igual, usar score
        if self.score != other.score:
            return self.score > other.score

        # Se score igual, usar tempo de adição (FIFO)
        return self.added_at < other.added_at


class OfferQueue:
    """
    Sistema de fila de ofertas com priorização e controle de qualidade
    """

    def __init__(self, max_queue_size: int = 1000):
        self.logger = logging.getLogger("queue.offer_queue")
        self.max_queue_size = max_queue_size

        # Fila principal (heap de prioridade)
        self.queue: List[QueuedOffer] = []

        # Cache de ofertas por ID
        self.offers_by_id: Dict[str, QueuedOffer] = {}

        # Estatísticas
        self.stats = {
            "total_added": 0,
            "total_processed": 0,
            "total_approved": 0,
            "total_rejected": 0,
            "total_moderated": 0,
            "current_size": 0,
            "avg_processing_time": 0.0,
            "avg_quality_score": 0.0,
        }

        # Callbacks
        self.on_offer_added: Optional[Callable[[QueuedOffer], None]] = None
        self.on_offer_processed: Optional[Callable[[QueuedOffer], None]] = None
        self.on_offer_approved: Optional[Callable[[QueuedOffer], None]] = None
        self.on_offer_rejected: Optional[Callable[[QueuedOffer], None]] = None

        # Configurações
        self.auto_approve_threshold = 0.8  # Score mínimo para aprovação automática
        self.auto_reject_threshold = 0.3  # Score máximo para rejeição automática
        self.max_processing_time = 300  # 5 minutos

        self.logger.info("OfferQueue inicializado")

    def add_offer(
        self,
        offer: Offer,
        priority: QueuePriority = QueuePriority.NORMAL,
        score: float = 0.0,
        source: str = "unknown",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Adiciona uma oferta à fila

        Args:
            offer: Oferta a ser adicionada
            priority: Prioridade da oferta
            score: Score de qualidade (0.0 a 1.0)
            source: Fonte da oferta
            tags: Tags para categorização
            metadata: Metadados adicionais

        Returns:
            ID da oferta na fila
        """
        if len(self.queue) >= self.max_queue_size:
            self.logger.warning(
                f"Fila cheia ({self.max_queue_size}), removendo oferta de menor prioridade"
            )
            self._remove_lowest_priority_offer()

        # Gerar ID único
        queue_id = str(uuid.uuid4())

        # Criar oferta na fila
        queued_offer = QueuedOffer(
            id=queue_id,
            offer=offer,
            priority=priority,
            score=score,
            tags=tags or [],
            metadata=metadata or {},
        )

        # Adicionar à fila
        heapq.heappush(self.queue, queued_offer)
        self.offers_by_id[queue_id] = queued_offer

        # Atualizar estatísticas
        self.stats["total_added"] += 1
        self.stats["current_size"] = len(self.queue)

        self.logger.info(
            f"Oferta adicionada à fila: {queue_id} (prioridade: {priority.name}, score: {score:.2f})"
        )

        # Executar callback
        if self.on_offer_added:
            try:
                self.on_offer_added(queued_offer)
            except Exception as e:
                self.logger.error(f"Erro no callback on_offer_added: {e}")

        return queue_id

    def get_next_offer(self) -> Optional[QueuedOffer]:
        """
        Obtém a próxima oferta da fila (maior prioridade)

        Returns:
            Próxima oferta ou None se fila vazia
        """
        if not self.queue:
            return None

        # Obter oferta de maior prioridade
        queued_offer = heapq.heappop(self.queue)

        # Atualizar status
        queued_offer.status = QueueStatus.PROCESSING
        queued_offer.processed_at = datetime.now()

        self.logger.info(
            f"Oferta removida da fila para processamento: {queued_offer.id}"
        )

        return queued_offer

    def return_offer_to_queue(self, queued_offer: QueuedOffer) -> None:
        """
        Retorna uma oferta à fila após processamento

        Args:
            queued_offer: Oferta a ser retornada
        """
        # Verificar se deve ser retornada à fila
        if queued_offer.retry_count < queued_offer.max_retries:
            queued_offer.retry_count += 1
            queued_offer.status = QueueStatus.PENDING

            # Recalcular prioridade baseado no retry
            if queued_offer.retry_count > 1:
                queued_offer.priority = QueuePriority.LOW

            # Adicionar de volta à fila
            heapq.heappush(self.queue, queued_offer)

            self.logger.info(
                f"Oferta retornada à fila: {queued_offer.id} (retry: {queued_offer.retry_count})"
            )
        else:
            # Máximo de tentativas atingido
            queued_offer.status = QueueStatus.ERROR
            queued_offer.moderation_notes = (
                f"Máximo de tentativas ({queued_offer.max_retries}) atingido"
            )

            self.logger.warning(
                f"Oferta com erro após máximo de tentativas: {queued_offer.id}"
            )

    def approve_offer(self, queue_id: str, notes: str = "") -> bool:
        """
        Aprova uma oferta

        Args:
            queue_id: ID da oferta na fila
            notes: Notas de aprovação

        Returns:
            True se aprovada com sucesso
        """
        if queue_id not in self.offers_by_id:
            self.logger.warning(f"Oferta não encontrada: {queue_id}")
            return False

        queued_offer = self.offers_by_id[queue_id]
        queued_offer.status = QueueStatus.APPROVED
        queued_offer.moderation_notes = notes

        # Atualizar estatísticas
        self.stats["total_processed"] += 1
        self.stats["total_approved"] += 1
        self.stats["current_size"] = len(self.queue)

        self.logger.info(f"Oferta aprovada: {queue_id}")

        # Executar callback
        if self.on_offer_approved:
            try:
                self.on_offer_approved(queued_offer)
            except Exception as e:
                self.logger.error(f"Erro no callback on_offer_approved: {e}")

        return True

    def reject_offer(self, queue_id: str, reason: str) -> bool:
        """
        Rejeita uma oferta

        Args:
            queue_id: ID da oferta na fila
            reason: Motivo da rejeição

        Returns:
            True se rejeitada com sucesso
        """
        if queue_id not in self.offers_by_id:
            self.logger.warning(f"Oferta não encontrada: {queue_id}")
            return False

        queued_offer = self.offers_by_id[queue_id]
        queued_offer.status = QueueStatus.REJECTED
        queued_offer.moderation_notes = reason

        # Atualizar estatísticas
        self.stats["total_processed"] += 1
        self.stats["total_rejected"] += 1
        self.stats["current_size"] = len(self.queue)

        self.logger.info(f"Oferta rejeitada: {queue_id} - {reason}")

        # Executar callback
        if self.on_offer_rejected:
            try:
                self.on_offer_rejected(queued_offer)
            except Exception as e:
                self.logger.error(f"Erro no callback on_offer_rejected: {e}")

        return True

    def send_to_moderation(self, queue_id: str, reason: str = "") -> bool:
        """
        Envia uma oferta para moderação manual

        Args:
            queue_id: ID da oferta na fila
            reason: Motivo para moderação

        Returns:
            True se enviada para moderação com sucesso
        """
        if queue_id not in self.offers_by_id:
            self.logger.warning(f"Oferta não encontrada: {queue_id}")
            return False

        queued_offer = self.offers_by_id[queue_id]
        queued_offer.status = QueueStatus.MODERATION
        queued_offer.moderation_notes = reason or "Enviada para moderação manual"

        # Atualizar estatísticas
        self.stats["total_moderated"] += 1

        self.logger.info(f"Oferta enviada para moderação: {queue_id} - {reason}")

        return True

    def schedule_offer(self, queue_id: str, scheduled_time: datetime) -> bool:
        """
        Agenda uma oferta para publicação futura

        Args:
            queue_id: ID da oferta na fila
            scheduled_time: Horário agendado

        Returns:
            True se agendada com sucesso
        """
        if queue_id not in self.offers_by_id:
            self.logger.warning(f"Oferta não encontrada: {queue_id}")
            return False

        queued_offer = self.offers_by_id[queue_id]
        queued_offer.status = QueueStatus.SCHEDULED
        queued_offer.scheduled_for = scheduled_time

        self.logger.info(f"Oferta agendada: {queue_id} para {scheduled_time}")

        return True

    def get_offer(self, queue_id: str) -> Optional[QueuedOffer]:
        """
        Obtém uma oferta específica da fila

        Args:
            queue_id: ID da oferta

        Returns:
            Oferta ou None se não encontrada
        """
        return self.offers_by_id.get(queue_id)

    def get_offers_by_status(self, status: QueueStatus) -> List[QueuedOffer]:
        """
        Obtém ofertas por status

        Args:
            status: Status desejado

        Returns:
            Lista de ofertas com o status especificado
        """
        return [offer for offer in self.offers_by_id.values() if offer.status == status]

    def get_offers_by_priority(self, priority: QueuePriority) -> List[QueuedOffer]:
        """
        Obtém ofertas por prioridade

        Args:
            priority: Prioridade desejada

        Returns:
            Lista de ofertas com a prioridade especificada
        """
        return [
            offer for offer in self.offers_by_id.values() if offer.priority == priority
        ]

    def get_offers_by_tag(self, tag: str) -> List[QueuedOffer]:
        """
        Obtém ofertas por tag

        Args:
            tag: Tag para filtrar

        Returns:
            Lista de ofertas com a tag
        """
        return [offer for offer in self.offers_by_id.values() if tag in offer.tags]

    def get_offer_by_id(self, queue_id: str) -> Optional[QueuedOffer]:
        """
        Obtém uma oferta específica por ID

        Args:
            queue_id: ID da oferta na fila

        Returns:
            Oferta ou None se não encontrada
        """
        return self.offers_by_id.get(queue_id)

    def get_queue_size(self) -> int:
        """Retorna o tamanho atual da fila"""
        return len(self.queue)

    def get_total_offers(self) -> int:
        """Retorna o total de ofertas (incluindo processadas)"""
        return len(self.offers_by_id)

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da fila"""
        # Calcular estatísticas em tempo real
        if self.stats["total_processed"] > 0:
            self.stats["avg_processing_time"] = self._calculate_avg_processing_time()
            self.stats["avg_quality_score"] = self._calculate_avg_quality_score()

        # Adicionar estatísticas adicionais
        stats = self.stats.copy()

        # Contadores por prioridade
        priority_counts = {}
        for queued_offer in self.offers_by_id.values():
            priority_name = queued_offer.priority.name.lower()
            priority_counts[priority_name] = priority_counts.get(priority_name, 0) + 1

        stats.update(priority_counts)

        # Contadores por status
        status_counts = {}
        for queued_offer in self.offers_by_id.values():
            status_name = queued_offer.status.name.lower()
            status_counts[f"{status_name}_offers"] = (
                status_counts.get(f"{status_name}_offers", 0) + 1
            )

        stats.update(status_counts)

        # Estatísticas básicas
        stats.update(
            {
                "total_offers": len(self.offers_by_id),
                "pending_offers": len(
                    [
                        o
                        for o in self.offers_by_id.values()
                        if o.status == QueueStatus.PENDING
                    ]
                ),
                "approved_offers": len(
                    [
                        o
                        for o in self.offers_by_id.values()
                        if o.status == QueueStatus.APPROVED
                    ]
                ),
                "rejected_offers": len(
                    [
                        o
                        for o in self.offers_by_id.values()
                        if o.status == QueueStatus.REJECTED
                    ]
                ),
                "moderation_offers": len(
                    [
                        o
                        for o in self.offers_by_id.values()
                        if o.status == QueueStatus.MODERATION
                    ]
                ),
            }
        )

        return stats

    def clear_processed_offers(self, max_age_hours: int = 24) -> int:
        """
        Remove ofertas processadas antigas

        Args:
            max_age_hours: Idade máxima em horas

        Returns:
            Número de ofertas removidas
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        removed_count = 0

        # Ofertas a serem removidas
        to_remove = []

        for queue_id, queued_offer in self.offers_by_id.items():
            if (
                queued_offer.status
                in [QueueStatus.APPROVED, QueueStatus.REJECTED, QueueStatus.ERROR]
                and queued_offer.processed_at
                and queued_offer.processed_at < cutoff_time
            ):
                to_remove.append(queue_id)

        # Remover ofertas
        for queue_id in to_remove:
            del self.offers_by_id[queue_id]
            removed_count += 1

        self.logger.info(f"Removidas {removed_count} ofertas processadas antigas")
        return removed_count

    def _remove_lowest_priority_offer(self) -> None:
        """Remove a oferta de menor prioridade da fila"""
        if not self.queue:
            return

        # Encontrar oferta de menor prioridade
        lowest_priority_offer = min(
            self.queue, key=lambda x: (x.priority.value, -x.score, x.added_at)
        )

        # Remover da fila
        self.queue.remove(lowest_priority_offer)
        heapq.heapify(self.queue)  # Reorganizar heap

        # Remover do cache
        if lowest_priority_offer.id in self.offers_by_id:
            del self.offers_by_id[lowest_priority_offer.id]

        self.logger.info(
            f"Oferta de menor prioridade removida: {lowest_priority_offer.id}"
        )

    def _calculate_avg_processing_time(self) -> float:
        """Calcula tempo médio de processamento"""
        processing_times = []

        for queued_offer in self.offers_by_id.values():
            if (
                queued_offer.processed_at
                and queued_offer.added_at
                and queued_offer.status in [QueueStatus.APPROVED, QueueStatus.REJECTED]
            ):
                processing_time = (
                    queued_offer.processed_at - queued_offer.added_at
                ).total_seconds()
                processing_times.append(processing_time)

        if processing_times:
            return sum(processing_times) / len(processing_times)
        return 0.0

    def _calculate_avg_quality_score(self) -> float:
        """Calcula score médio de qualidade"""
        scores = [
            offer.score for offer in self.offers_by_id.values() if offer.score > 0
        ]

        if scores:
            return sum(scores) / len(scores)
        return 0.0

    def auto_process_offers(self) -> Dict[str, int]:
        """
        Processa automaticamente ofertas baseado no score

        Returns:
            Estatísticas do processamento automático
        """
        auto_approved = 0
        auto_rejected = 0
        sent_to_moderation = 0

        # Processar ofertas pendentes
        pending_offers = self.get_offers_by_status(QueueStatus.PENDING)

        for queued_offer in pending_offers:
            if queued_offer.score >= self.auto_approve_threshold:
                # Aprovação automática
                self.approve_offer(queued_offer.id, "Aprovação automática - score alto")
                auto_approved += 1

            elif queued_offer.score <= self.auto_reject_threshold:
                # Rejeição automática
                self.reject_offer(queued_offer.id, "Rejeição automática - score baixo")
                auto_rejected += 1

            else:
                # Enviar para moderação
                self.send_to_moderation(
                    queued_offer.id, "Score intermediário - requer moderação"
                )
                sent_to_moderation += 1

        self.logger.info(
            f"Processamento automático: {auto_approved} aprovadas, "
            f"{auto_rejected} rejeitadas, {sent_to_moderation} para moderação"
        )

        return {
            "approved": auto_approved,
            "rejected": auto_rejected,
            "sent_to_moderation": sent_to_moderation,
            "auto_approved": auto_approved,
            "auto_rejected": auto_rejected,
        }
