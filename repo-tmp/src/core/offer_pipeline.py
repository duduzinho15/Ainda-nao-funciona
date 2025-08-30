"""
Pipeline principal de processamento de ofertas com deduplicação e rate limiting.

Integra todos os componentes do sistema:
- Deduplicação de ofertas
- Rate limiting por fonte
- Validação de afiliados
- PostingManager
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from src.core.deduplication import DuplicationResult, offer_deduplicator
from src.core.models import Offer
from src.core.rate_limiter import RateLimit, rate_limiter
from src.posting.posting_manager import PostingManager
from src.utils.enhanced_metrics import enhanced_metrics

logger = logging.getLogger(__name__)


class ProcessingResult(Enum):
    """Resultados possíveis do processamento"""

    SUCCESS = "success"
    DUPLICATE = "duplicate"
    RATE_LIMITED = "rate_limited"
    VALIDATION_FAILED = "validation_failed"
    ERROR = "error"


@dataclass
class OfferProcessingResult:
    """Resultado do processamento de uma oferta"""

    result: ProcessingResult
    offer: Offer
    reason: Optional[str] = None
    duplicate_info: Optional[DuplicationResult] = None
    validation_errors: Optional[List[str]] = None
    processing_time_ms: Optional[int] = None


class OfferPipeline:
    """Pipeline principal de processamento de ofertas"""

    def __init__(self):
        self.posting_manager = PostingManager()
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "duplicates": 0,
            "rate_limited": 0,
            "validation_failed": 0,
            "errors": 0,
            "last_reset": datetime.now(),
        }

        # Configurar rate limits específicos do pipeline
        self._setup_pipeline_rate_limits()

    def _setup_pipeline_rate_limits(self):
        """Configurar rate limits específicos do pipeline"""
        # Rate limits por fonte de ofertas
        pipeline_limits = {
            "offer_processing": RateLimit(100, 60),  # 100 ofertas/min
            "validation_queue": RateLimit(200, 60),  # 200 validações/min
            "deduplication": RateLimit(500, 60),  # 500 checks/min
            "posting_queue": RateLimit(30, 60),  # 30 posts/min
        }

        for resource, limit in pipeline_limits.items():
            rate_limiter.update_platform_limit(resource, limit)

    async def process_offer(
        self, offer: Offer, source: str = "unknown"
    ) -> OfferProcessingResult:
        """
        Processar uma única oferta através do pipeline completo

        Args:
            offer: Oferta para processar
            source: Fonte da oferta (scraper, api, etc.)

        Returns:
            Resultado do processamento
        """
        start_time = datetime.now()

        try:
            self.stats["total_processed"] += 1

            # ETAPA 1: Rate Limiting
            rate_check = await rate_limiter.check_rate_limit("offer_processing")
            if not rate_check.allowed:
                self.stats["rate_limited"] += 1
                enhanced_metrics.log_rate_limit_hit("offer_processing", source)

                return OfferProcessingResult(
                    result=ProcessingResult.RATE_LIMITED,
                    offer=offer,
                    reason=f"Rate limit excedido: {rate_check.retry_after_seconds}s",
                    processing_time_ms=self._get_processing_time_ms(start_time),
                )

            # ETAPA 2: Deduplicação
            await rate_limiter.check_rate_limit("deduplication")
            duplicate_result = offer_deduplicator.check_duplicate(offer)

            if duplicate_result.is_duplicate:
                self.stats["duplicates"] += 1
                enhanced_metrics.log_offer_duplicate(
                    url=offer.url,
                    strategy=duplicate_result.deduplication_strategy,
                    similarity_score=duplicate_result.similarity_score,
                )

                return OfferProcessingResult(
                    result=ProcessingResult.DUPLICATE,
                    offer=offer,
                    reason=duplicate_result.reason,
                    duplicate_info=duplicate_result,
                    processing_time_ms=self._get_processing_time_ms(start_time),
                )

            # ETAPA 3: Validação de Afiliados
            await rate_limiter.check_rate_limit("validation_queue")

            if not offer.affiliate_url:
                validation_result = self.posting_manager.validate_affiliate_url(
                    offer.url, self._detect_platform_from_offer(offer)
                )
            else:
                validation_result = self.posting_manager.validate_affiliate_url(
                    offer.affiliate_url, self._detect_platform_from_offer(offer)
                )

            if not validation_result.is_valid:
                self.stats["validation_failed"] += 1
                enhanced_metrics.log_affiliate_validation_failure(
                    platform=validation_result.platform,
                    url=offer.affiliate_url or offer.url,
                    reason=validation_result.blocked_reason,
                )

                return OfferProcessingResult(
                    result=ProcessingResult.VALIDATION_FAILED,
                    offer=offer,
                    reason=f"Validação falhou: {validation_result.blocked_reason}",
                    validation_errors=validation_result.validation_errors,
                    processing_time_ms=self._get_processing_time_ms(start_time),
                )

            # ETAPA 4: Sucesso - Oferta válida e única
            self.stats["successful"] += 1
            enhanced_metrics.log_offer_processed_successfully(
                platform=validation_result.platform,
                source=source,
                processing_time_ms=self._get_processing_time_ms(start_time),
            )

            return OfferProcessingResult(
                result=ProcessingResult.SUCCESS,
                offer=offer,
                reason="Oferta processada com sucesso",
                processing_time_ms=self._get_processing_time_ms(start_time),
            )

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Erro ao processar oferta {offer.url}: {e}")
            enhanced_metrics.log_pipeline_error(
                component="offer_pipeline",
                error_type=type(e).__name__,
                error_message=str(e),
            )

            return OfferProcessingResult(
                result=ProcessingResult.ERROR,
                offer=offer,
                reason=f"Erro no processamento: {e}",
                processing_time_ms=self._get_processing_time_ms(start_time),
            )

    async def process_batch(
        self, offers: List[Offer], source: str = "batch"
    ) -> Dict[str, List[OfferProcessingResult]]:
        """
        Processar lote de ofertas

        Args:
            offers: Lista de ofertas
            source: Fonte do lote

        Returns:
            Resultados agrupados por tipo
        """
        logger.info(f"Processando lote de {len(offers)} ofertas de {source}")

        # Processar ofertas em paralelo (com limite de concorrência)
        semaphore = asyncio.Semaphore(10)  # Máximo 10 processamentos simultâneos

        async def process_with_semaphore(offer):
            async with semaphore:
                return await self.process_offer(offer, source)

        tasks = [process_with_semaphore(offer) for offer in offers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Agrupar resultados
        grouped_results = {
            "success": [],
            "duplicate": [],
            "rate_limited": [],
            "validation_failed": [],
            "error": [],
        }

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Exceção no processamento: {result}")
                continue

            result_type = result.result.value
            grouped_results[result_type].append(result)

        # Log do resumo
        summary = {k: len(v) for k, v in grouped_results.items()}
        logger.info(f"Lote processado: {summary}")

        return grouped_results

    async def process_with_retry(
        self, offer: Offer, source: str = "retry", max_retries: int = 3
    ) -> OfferProcessingResult:
        """
        Processar oferta com retry automático para rate limiting

        Args:
            offer: Oferta para processar
            source: Fonte da oferta
            max_retries: Número máximo de tentativas

        Returns:
            Resultado final do processamento
        """
        for attempt in range(max_retries + 1):
            result = await self.process_offer(offer, f"{source}_attempt_{attempt + 1}")

            if result.result != ProcessingResult.RATE_LIMITED:
                return result

            if attempt < max_retries:
                # Aguardar antes da próxima tentativa
                wait_time = min(2**attempt, 30)  # Backoff exponencial limitado a 30s
                logger.info(
                    f"Rate limited, aguardando {wait_time}s antes da tentativa {attempt + 2}"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.warning(f"Máximo de tentativas excedido para {offer.url}")

        return result

    def _detect_platform_from_offer(self, offer: Offer) -> str:
        """Detectar plataforma a partir da oferta"""
        url = offer.affiliate_url or offer.url

        if "amazon.com" in url:
            return "amazon"
        elif "shopee.com" in url:
            return "shopee"
        elif "mercadolivre.com" in url:
            return "mercadolivre"
        elif "aliexpress.com" in url:
            return "aliexpress"
        elif "magazinevoce.com" in url:
            return "magazineluiza"
        elif "awin1.com" in url or "tidd.ly" in url:
            return "awin"
        else:
            return "unknown"

    def _get_processing_time_ms(self, start_time: datetime) -> int:
        """Calcular tempo de processamento em milissegundos"""
        return int((datetime.now() - start_time).total_seconds() * 1000)

    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do pipeline"""
        return {
            **self.stats,
            "deduplication_stats": offer_deduplicator.get_cache_stats(),
            "rate_limiter_stats": rate_limiter.get_stats(),
            "success_rate": (
                self.stats["successful"] / self.stats["total_processed"] * 100
                if self.stats["total_processed"] > 0
                else 0
            ),
        }

    def reset_stats(self):
        """Resetar estatísticas"""
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "duplicates": 0,
            "rate_limited": 0,
            "validation_failed": 0,
            "errors": 0,
            "last_reset": datetime.now(),
        }

        offer_deduplicator.clear_cache()
        rate_limiter.reset_stats()
        logger.info("Estatísticas do pipeline resetadas")

    async def health_check(self) -> Dict[str, Any]:
        """Verificação de saúde do pipeline"""
        try:
            # Testar rate limiter
            rate_test = await rate_limiter.check_rate_limit("health_check")

            # Testar deduplicação
            test_offer = Offer(
                title="Health Check",
                price=1.00,
                url="https://test.com/health",
                store="TestStore",
            )
            offer_deduplicator.check_duplicate(test_offer)

            # Testar posting manager
            posting_test = self.posting_manager.validate_affiliate_url(
                "https://amazon.com.br/dp/B123456789?tag=garimpeirogee-20", "amazon"
            )

            return {
                "status": "healthy",
                "components": {
                    "rate_limiter": "ok" if rate_test.allowed else "limited",
                    "deduplicator": "ok",
                    "posting_manager": "ok" if posting_test.is_valid else "error",
                },
                "stats": self.get_stats(),
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "stats": self.get_stats()}


# Instância global do pipeline
offer_pipeline = OfferPipeline()
