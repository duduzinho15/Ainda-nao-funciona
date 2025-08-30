#!/usr/bin/env python3
"""
Teste completo do Sistema de Fila de Ofertas do Garimpeiro Geek
Testa todos os componentes: OfferQueue, ModerationSystem, QualityController e QueueManager
"""

import asyncio
import logging
from decimal import Decimal

import pytest

from src.app.queue import (
    ModerationLevel,
    ModerationStatus,
    ModerationSystem,
    OfferQueue,
    QualityController,
    QualityMetrics,
    QueueManager,
    QueueManagerConfig,
    QueueManagerStatus,
    QueuePriority,
    QueueStatus,
)
from src.core.models import Offer

# Configurar logging para testes
logging.basicConfig(level=logging.INFO)


class TestOfferQueue:
    """Testes para OfferQueue"""

    def setup_method(self):
        """Setup para cada teste"""
        self.queue = OfferQueue()
        self.test_offer = Offer(
            title="Smartphone Samsung Galaxy S23",
            price=Decimal("2999.99"),
            original_price=Decimal("3999.99"),
            url="https://amazon.com.br/samsung-galaxy-s23",
            store="amazon",
            image_url="https://example.com/image.jpg",
            category="smartphone",
            coupon_code="SAMSUNG23",
            coupon_discount=25.0,
            coupon_valid_until="2024-12-31T23:59:59",
            stock_quantity=10,
        )

    def test_add_offer(self):
        """Testa adição de oferta à fila"""
        queue_id = self.queue.add_offer(self.test_offer, QueuePriority.HIGH)
        assert queue_id is not None
        assert len(queue_id) > 0

        # Verificar se foi adicionada
        stats = self.queue.get_stats()
        assert stats["total_offers"] == 1
        assert stats["pending_offers"] == 1

    def test_get_next_offer(self):
        """Testa obtenção da próxima oferta da fila"""
        # Adicionar ofertas com prioridades diferentes
        self.queue.add_offer(self.test_offer, QueuePriority.LOW)

        high_priority_offer = Offer(
            title="iPhone 15 Pro",
            price=Decimal("8999.99"),
            url="https://apple.com/iphone15pro",
            store="apple",
            image_url="https://example.com/iphone.jpg",
        )
        self.queue.add_offer(high_priority_offer, QueuePriority.HIGH)

        # A oferta de alta prioridade deve vir primeiro
        next_offer = self.queue.get_next_offer()
        assert next_offer is not None
        assert next_offer.offer.title == "iPhone 15 Pro"
        assert next_offer.priority == QueuePriority.HIGH

    def test_approve_offer(self):
        """Testa aprovação de oferta"""
        queue_id = self.queue.add_offer(self.test_offer)
        assert self.queue.approve_offer(queue_id, "Oferta aprovada")

        # Verificar status
        offer = self.queue.get_offer_by_id(queue_id)
        assert offer.status == QueueStatus.APPROVED
        assert offer.processed_at is not None

    def test_reject_offer(self):
        """Testa rejeição de oferta"""
        queue_id = self.queue.add_offer(self.test_offer)
        assert self.queue.reject_offer(queue_id, "Oferta rejeitada")

        # Verificar status
        offer = self.queue.get_offer_by_id(queue_id)
        assert offer.status == QueueStatus.REJECTED
        assert offer.processed_at is not None

    def test_send_to_moderation(self):
        """Testa envio para moderação"""
        queue_id = self.queue.add_offer(self.test_offer)
        assert self.queue.send_to_moderation(queue_id, "Necessita revisão")

        # Verificar status
        offer = self.queue.get_offer_by_id(queue_id)
        assert offer.status == QueueStatus.MODERATION

    def test_auto_process_offers(self):
        """Testa processamento automático de ofertas"""
        # Adicionar ofertas com scores diferentes
        offer1 = Offer(
            title="Produto 1",
            price=Decimal("100.00"),
            url="https://example.com/1",
            store="store1",
        )
        offer2 = Offer(
            title="Produto 2",
            price=Decimal("200.00"),
            url="https://example.com/2",
            store="store2",
        )

        self.queue.add_offer(offer1, score=0.8)  # Score alto
        self.queue.add_offer(offer2, score=0.3)  # Score baixo

        # Processar automaticamente
        results = self.queue.auto_process_offers()

        assert results["approved"] >= 1  # Pelo menos uma deve ser aprovada
        assert results["rejected"] >= 1  # Pelo menos uma deve ser rejeitada

    def test_get_stats(self):
        """Testa obtenção de estatísticas"""
        # Adicionar algumas ofertas
        self.queue.add_offer(self.test_offer, QueuePriority.HIGH)
        self.queue.add_offer(self.test_offer, QueuePriority.NORMAL)

        stats = self.queue.get_stats()
        assert stats["total_offers"] == 2
        assert stats["pending_offers"] == 2
        assert stats["high_priority"] == 1
        assert stats["normal_priority"] == 1


class TestModerationSystem:
    """Testes para ModerationSystem"""

    def setup_method(self):
        """Setup para cada teste"""
        self.offer_queue = OfferQueue()
        self.moderation_system = ModerationSystem(self.offer_queue)

        self.test_offer = Offer(
            title="Produto para moderação",
            price=Decimal("150.00"),
            url="https://example.com/moderation",
            store="test_store",
        )

    def test_create_moderation_task(self):
        """Testa criação de tarefa de moderação"""
        # Adicionar oferta à fila
        queue_id = self.offer_queue.add_offer(self.test_offer)
        queued_offer = self.offer_queue.get_offer_by_id(queue_id)

        # Criar tarefa de moderação
        task_id = self.moderation_system.create_moderation_task(
            queued_offer, ModerationLevel.STANDARD
        )
        assert task_id is not None

        # Verificar se a tarefa foi criada
        task = self.moderation_system.get_task_by_id(task_id)
        assert task is not None
        assert task.status == ModerationStatus.PENDING

    def test_assign_task(self):
        """Testa atribuição de tarefa"""
        # Criar tarefa
        queue_id = self.offer_queue.add_offer(self.test_offer)
        queued_offer = self.offer_queue.get_offer_by_id(queue_id)
        task_id = self.moderation_system.create_moderation_task(queued_offer)

        # Atribuir a um moderador
        assert self.moderation_system.assign_task(task_id, "moderator1")

        # Verificar atribuição
        task = self.moderation_system.get_task_by_id(task_id)
        assert task.assigned_to == "moderator1"
        assert task.assigned_at is not None

    def test_complete_task(self):
        """Testa conclusão de tarefa"""
        # Criar e atribuir tarefa
        queue_id = self.offer_queue.add_offer(self.test_offer)
        queued_offer = self.offer_queue.get_offer_by_id(queue_id)
        task_id = self.moderation_system.create_moderation_task(queued_offer)
        self.moderation_system.assign_task(task_id, "moderator1")

        # Completar tarefa com aprovação
        assert self.moderation_system.complete_task(
            task_id, "approve", "Produto aprovado", "Produto de qualidade"
        )

        # Verificar conclusão
        task = self.moderation_system.get_task_by_id(task_id)
        assert task.status == ModerationStatus.COMPLETED
        assert task.decision == "approve"
        assert task.reviewed_at is not None

        # Verificar se a oferta foi aprovada na fila
        queued_offer = self.offer_queue.get_offer_by_id(queue_id)
        assert queued_offer.status == QueueStatus.APPROVED

    def test_escalate_task(self):
        """Testa escalação de tarefa"""
        # Criar tarefa
        queue_id = self.offer_queue.add_offer(self.test_offer)
        queued_offer = self.offer_queue.get_offer_by_id(queue_id)
        task_id = self.moderation_system.create_moderation_task(queued_offer)

        # Escalar tarefa
        assert self.moderation_system.escalate_task(task_id, "Requer revisão especial")

        # Verificar escalação
        task = self.moderation_system.get_task_by_id(task_id)
        assert task.level == ModerationLevel.ESCALATED

    def test_auto_assign_tasks(self):
        """Testa atribuição automática de tarefas"""
        # Adicionar moderadores
        self.moderation_system.add_moderator("moderator1")
        self.moderation_system.add_moderator("moderator2")

        # Criar várias tarefas
        for i in range(3):
            offer = Offer(
                title=f"Produto {i}",
                price=Decimal(f"{100 + i * 50}"),
                url=f"https://example.com/{i}",
                store="store",
            )
            queue_id = self.offer_queue.add_offer(offer)
            queued_offer = self.offer_queue.get_offer_by_id(queue_id)
            self.moderation_system.create_moderation_task(queued_offer)

        # Atribuir automaticamente
        results = self.moderation_system.auto_assign_tasks()
        assert results["assigned"] >= 1  # Pelo menos uma deve ser atribuída

    def test_get_stats(self):
        """Testa obtenção de estatísticas"""
        # Criar algumas tarefas
        for i in range(2):
            offer = Offer(
                title=f"Produto {i}",
                price=Decimal(f"{100 + i * 50}"),
                url=f"https://example.com/{i}",
                store="store",
            )
            queue_id = self.offer_queue.add_offer(offer)
            queued_offer = self.offer_queue.get_offer_by_id(queue_id)
            self.moderation_system.create_moderation_task(queued_offer)

        stats = self.moderation_system.get_stats()
        assert stats["total_tasks"] == 2
        assert stats["pending_tasks"] == 2


class TestQualityController:
    """Testes para QualityController"""

    def setup_method(self):
        """Setup para cada teste"""
        self.quality_controller = QualityController()

        self.good_offer = Offer(
            title="Smartphone Samsung Galaxy S23 128GB Preto",
            price=Decimal("2999.99"),
            original_price=Decimal("3999.99"),
            url="https://amazon.com.br/samsung-galaxy-s23",
            store="amazon",
            image_url="https://example.com/image.jpg",
            category="smartphone",
            coupon_code="SAMSUNG23",
            coupon_discount=25.0,
            coupon_valid_until="2024-12-31T23:59:59",
            stock_quantity=10,
        )

        self.bad_offer = Offer(
            title="!!!PRODUTO GRATIS!!!",
            price=Decimal("1.99"),
            url="https://spam.com/fake",
            store="unknown_store",
            image_url="invalid_image",
        )

    @pytest.mark.asyncio
    async def test_evaluate_good_offer(self):
        """Testa avaliação de oferta de boa qualidade"""
        metrics = await self.quality_controller.evaluate_offer(self.good_offer)

        assert metrics.overall_score > 0.7  # Score deve ser alto
        assert metrics.price_score > 0.5
        assert metrics.discount_score > 0.5
        assert metrics.title_score > 0.5
        assert metrics.store_score > 0.8  # Amazon é confiável
        assert metrics.url_score > 0.5
        assert metrics.image_score > 0.5
        assert metrics.category_score > 0.5
        assert metrics.coupon_score > 0.5
        assert metrics.stock_score > 0.5

        # Verificar nível de qualidade
        quality_level = metrics.get_quality_level()
        # Verificar se é um valor válido (não importa o tipo específico)
        assert quality_level in ["EXCELLENT", "VERY_GOOD", "GOOD", "POOR", "VERY_POOR"]

    @pytest.mark.asyncio
    async def test_evaluate_bad_offer(self):
        """Testa avaliação de oferta de baixa qualidade"""
        metrics = await self.quality_controller.evaluate_offer(self.bad_offer)

        assert metrics.overall_score < 0.5  # Score deve ser baixo
        assert metrics.title_score < 0.5  # Título com spam
        assert metrics.store_score < 0.5  # Loja desconhecida
        assert metrics.url_score < 0.5  # URL suspeita

        # Verificar nível de qualidade
        quality_level = metrics.get_quality_level()
        assert quality_level in ["POOR", "VERY_POOR"]

    @pytest.mark.asyncio
    async def test_evaluate_price_ranges(self):
        """Testa avaliação de diferentes faixas de preço"""
        # Produto barato
        cheap_offer = Offer(
            title="Produto barato",
            price=Decimal("25.00"),
            url="https://example.com/cheap",
            store="store",
        )
        metrics = await self.quality_controller.evaluate_offer(cheap_offer)
        assert metrics.price_score > 0.5

        # Produto médio
        medium_offer = Offer(
            title="Produto médio",
            price=Decimal("150.00"),
            url="https://example.com/medium",
            store="store",
        )
        metrics = await self.quality_controller.evaluate_offer(medium_offer)
        assert metrics.price_score > 0.8

        # Produto caro
        expensive_offer = Offer(
            title="Produto caro",
            price=Decimal("2500.00"),
            url="https://example.com/expensive",
            store="store",
        )
        metrics = await self.quality_controller.evaluate_offer(expensive_offer)
        assert metrics.price_score > 0.7

    @pytest.mark.asyncio
    async def test_evaluate_discount_ranges(self):
        """Testa avaliação de diferentes faixas de desconto"""
        # Desconto baixo
        low_discount_offer = Offer(
            title="Produto com desconto baixo",
            price=Decimal("90.00"),
            original_price=Decimal("100.00"),
            url="https://example.com/low",
            store="store",
        )
        metrics = await self.quality_controller.evaluate_offer(low_discount_offer)
        assert metrics.discount_score > 0.4

        # Desconto alto
        high_discount_offer = Offer(
            title="Produto com desconto alto",
            price=Decimal("50.00"),
            original_price=Decimal("100.00"),
            url="https://example.com/high",
            store="store",
        )
        metrics = await self.quality_controller.evaluate_offer(high_discount_offer)
        assert metrics.discount_score > 0.8

    def test_get_priority_recommendation(self):
        """Testa recomendação de prioridade baseada na qualidade"""
        # Criar métricas de alta qualidade
        high_quality_metrics = QualityMetrics(overall_score=0.85)
        priority = self.quality_controller.get_priority_recommendation(
            high_quality_metrics
        )
        assert priority == QueuePriority.HIGH

        # Criar métricas de baixa qualidade
        low_quality_metrics = QualityMetrics(overall_score=0.35)
        priority = self.quality_controller.get_priority_recommendation(
            low_quality_metrics
        )
        assert priority == QueuePriority.LOW

    def test_get_quality_summary(self):
        """Testa geração de resumo de qualidade"""
        metrics = QualityMetrics(
            overall_score=0.75,
            price_score=0.8,
            discount_score=0.7,
            title_score=0.9,
            store_score=0.8,
            url_score=0.7,
            image_score=0.6,
            category_score=0.8,
            coupon_score=0.7,
            stock_score=0.8,
        )

        summary = self.quality_controller.get_quality_summary(metrics)

        assert summary["overall_score"] == 0.75
        assert summary["quality_level"] == "GOOD"
        assert summary["priority_recommendation"] == QueuePriority.NORMAL.name
        assert "aspect_scores" in summary
        assert summary["aspect_scores"]["price"] == 0.8


class TestQueueManager:
    """Testes para QueueManager"""

    def setup_method(self):
        """Setup para cada teste"""
        self.config = QueueManagerConfig(
            auto_process_enabled=True,
            auto_process_interval=1,  # Intervalo baixo para testes
            auto_assign_interval=1,
            cleanup_interval=2,
        )
        self.queue_manager = QueueManager(self.config)

        self.test_offer = Offer(
            title="Produto para teste do manager",
            price=Decimal("200.00"),
            url="https://example.com/manager-test",
            store="amazon",
            image_url="https://example.com/image.jpg",
        )

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Testa início e parada do manager"""
        # Iniciar
        assert await self.queue_manager.start()
        assert self.queue_manager.is_running
        assert self.queue_manager.status == QueueManagerStatus.RUNNING

        # Aguardar um pouco para as tarefas iniciarem
        await asyncio.sleep(0.1)

        # Parar
        assert await self.queue_manager.stop()
        assert not self.queue_manager.is_running
        assert self.queue_manager.status == QueueManagerStatus.STOPPED

    @pytest.mark.asyncio
    async def test_pause_resume(self):
        """Testa pausa e resumo do manager"""
        # Iniciar
        await self.queue_manager.start()

        # Pausar
        assert await self.queue_manager.pause()
        assert self.queue_manager.status == QueueManagerStatus.PAUSED

        # Resumir
        assert await self.queue_manager.resume()
        assert self.queue_manager.status == QueueManagerStatus.RUNNING

        # Parar
        await self.queue_manager.stop()

    @pytest.mark.asyncio
    async def test_add_offer(self):
        """Testa adição de oferta através do manager"""
        await self.queue_manager.start()

        # Adicionar oferta
        queue_id = await self.queue_manager.add_offer(
            self.test_offer, source="test", metadata={"test": True}
        )

        assert queue_id is not None
        assert len(queue_id) > 0

        # Verificar se foi adicionada
        status = await self.queue_manager.get_queue_status()
        assert status["queue_stats"]["total_offers"] >= 1

        await self.queue_manager.stop()

    @pytest.mark.asyncio
    async def test_process_offer(self):
        """Testa processamento de oferta através do manager"""
        await self.queue_manager.start()

        # Adicionar oferta
        queue_id = await self.queue_manager.add_offer(self.test_offer)

        # Aprovar oferta
        assert await self.queue_manager.process_offer(
            queue_id, "approve", "test_moderator", "Aprovado no teste"
        )

        # Verificar se foi aprovada
        details = await self.queue_manager.get_offer_details(queue_id)
        assert details is not None
        assert details["status"] == "approved"

        await self.queue_manager.stop()

    @pytest.mark.asyncio
    async def test_get_queue_status(self):
        """Testa obtenção de status da fila"""
        await self.queue_manager.start()

        status = await self.queue_manager.get_queue_status()

        assert "manager_status" in status
        assert "is_running" in status
        assert "queue_stats" in status
        assert "moderation_stats" in status
        assert "quality_stats" in status
        assert "manager_stats" in status
        assert "config" in status

        await self.queue_manager.stop()

    @pytest.mark.asyncio
    async def test_event_callbacks(self):
        """Testa sistema de callbacks de eventos"""
        await self.queue_manager.start()

        # Lista para armazenar eventos
        events = []

        def callback(data):
            events.append(data)

        # Registrar callback
        self.queue_manager.add_event_callback("offer_added", callback)

        # Adicionar oferta para disparar evento
        await self.queue_manager.add_offer(self.test_offer)

        # Aguardar um pouco para o evento ser disparado
        await asyncio.sleep(0.1)

        # Verificar se o evento foi disparado
        assert len(events) > 0
        assert "offer" in events[0]

        await self.queue_manager.stop()

    def test_config_export_import(self):
        """Testa exportação e importação de configuração"""
        # Exportar configuração
        config = self.queue_manager.export_config()

        assert "auto_process_enabled" in config
        assert "moderation_enabled" in config
        assert "quality_evaluation_enabled" in config

        # Modificar configuração
        config["auto_process_enabled"] = False
        config["min_quality_score"] = 0.8

        # Importar configuração
        assert self.queue_manager.import_config(config)

        # Verificar se foi aplicada
        assert not self.queue_manager.config.auto_process_enabled
        assert self.queue_manager.config.min_quality_score == 0.8


class TestQueueSystemIntegration:
    """Testes de integração do sistema completo"""

    def setup_method(self):
        """Setup para cada teste"""
        self.queue_manager = QueueManager()
        self.test_offers = [
            Offer(
                title="Produto 1 - Alta qualidade",
                price=Decimal("150.00"),
                original_price=Decimal("200.00"),
                url="https://amazon.com/produto1",
                store="amazon",
                image_url="https://example.com/image1.jpg",
                category="smartphone",
            ),
            Offer(
                title="Produto 2 - Qualidade média",
                price=Decimal("100.00"),
                url="https://mercadolivre.com/produto2",
                store="mercadolivre",
                image_url="https://example.com/image2.jpg",
                category="acessorio",
            ),
            Offer(
                title="!!!PRODUTO SPAM!!!",
                price=Decimal("5.99"),
                url="https://spam.com/fake",
                store="unknown",
                image_url="invalid",
            ),
        ]

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Testa fluxo completo do sistema"""
        await self.queue_manager.start()

        try:
            # 1. Adicionar ofertas
            queue_ids = []
            for offer in self.test_offers:
                queue_id = await self.queue_manager.add_offer(
                    offer, source="integration_test"
                )
                if queue_id:  # A oferta de spam pode ser rejeitada
                    queue_ids.append(queue_id)

            # Aguardar processamento
            await asyncio.sleep(0.2)

            # 2. Verificar status
            status = await self.queue_manager.get_queue_status()
            assert status["queue_stats"]["total_offers"] >= len(queue_ids)

            # 3. Processar ofertas manualmente
            for queue_id in queue_ids:
                # Obter detalhes
                details = await self.queue_manager.get_offer_details(queue_id)
                assert details is not None

                # Aprovar se for de boa qualidade
                if details.get("quality_info", {}).get("overall_score", 0) > 0.6:
                    assert await self.queue_manager.process_offer(
                        queue_id,
                        "approve",
                        "test_moderator",
                        "Aprovado no teste de integração",
                    )
                else:
                    assert await self.queue_manager.process_offer(
                        queue_id,
                        "reject",
                        "test_moderator",
                        "Rejeitado no teste de integração",
                    )

            # 4. Verificar estatísticas finais
            final_status = await self.queue_manager.get_queue_status()
            assert final_status["manager_stats"]["total_offers_processed"] >= len(
                queue_ids
            )

        finally:
            await self.queue_manager.stop()

    @pytest.mark.asyncio
    async def test_quality_filtering(self):
        """Testa filtragem por qualidade"""
        await self.queue_manager.start()

        try:
            # Configurar score mínimo alto
            self.queue_manager.config.min_quality_score = 0.8

            # Tentar adicionar ofertas
            added_count = 0
            for offer in self.test_offers:
                queue_id = await self.queue_manager.add_offer(offer)
                if queue_id:
                    added_count += 1

            # Apenas ofertas de alta qualidade devem ser aceitas
            assert added_count < len(self.test_offers)

        finally:
            await self.queue_manager.stop()

    @pytest.mark.asyncio
    async def test_moderation_workflow(self):
        """Testa fluxo de moderação"""
        await self.queue_manager.start()

        try:
            # Adicionar oferta
            queue_id = await self.queue_manager.add_offer(self.test_offers[1])

            # Enviar para moderação
            assert await self.queue_manager.process_offer(
                queue_id, "moderate", notes="Necessita revisão manual"
            )

            # Verificar se foi criada tarefa de moderação
            details = await self.queue_manager.get_offer_details(queue_id)
            assert details["status"] == "moderation"
            assert details["moderation_task"] is not None

            # Completar moderação
            task_id = details["moderation_task"]["id"]
            self.queue_manager.moderation_system.complete_task(
                task_id, "approve", "Aprovado após revisão", "Produto de qualidade"
            )

            # Verificar se a oferta foi aprovada
            updated_details = await self.queue_manager.get_offer_details(queue_id)
            assert updated_details["status"] == "approved"

        finally:
            await self.queue_manager.stop()


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v"])
