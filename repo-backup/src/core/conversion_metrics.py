"""
Sistema de Métricas de Conversão
Monitora performance de conversão por plataforma em tempo real
"""

import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .cache_config import production_cache_config

logger = logging.getLogger(__name__)


@dataclass
class ConversionEvent:
    """Evento de conversão individual"""

    timestamp: datetime
    platform: str
    original_url: str
    affiliate_url: str
    success: bool
    response_time_ms: float
    cache_hit: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlatformMetrics:
    """Métricas agregadas por plataforma"""

    platform: str
    total_conversions: int = 0
    successful_conversions: int = 0
    failed_conversions: int = 0
    total_response_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    last_conversion: Optional[datetime] = None
    error_counts: Dict[str, int] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Taxa de sucesso de conversão"""
        if self.total_conversions == 0:
            return 0.0
        return self.successful_conversions / self.total_conversions

    @property
    def average_response_time(self) -> float:
        """Tempo médio de resposta em ms"""
        if self.total_conversions == 0:
            return 0.0
        return self.total_response_time / self.total_conversions

    @property
    def cache_hit_rate(self) -> float:
        """Taxa de acerto do cache"""
        total_cache_ops = self.cache_hits + self.cache_misses
        if total_cache_ops == 0:
            return 0.0
        return self.cache_hits / total_cache_ops


class ConversionMetricsCollector:
    """Coletor de métricas de conversão"""

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.events: deque = deque(maxlen=10000)  # Limite de eventos em memória
        self.platform_metrics: Dict[str, PlatformMetrics] = defaultdict(PlatformMetrics)
        self.global_metrics = {
            "total_conversions": 0,
            "total_successful": 0,
            "total_failed": 0,
            "start_time": datetime.now(),
            "last_reset": datetime.now(),
        }

        # Configurações de alertas
        self.alert_thresholds = production_cache_config.global_config.get(
            "alert_thresholds", {}
        )
        self.alert_callbacks: List[callable] = []

        # Inicializar métricas por plataforma
        for platform in production_cache_config.get_all_platforms():
            self.platform_metrics[platform] = PlatformMetrics(platform=platform)

    def record_conversion(self, event: ConversionEvent) -> None:
        """Registra um evento de conversão"""
        try:
            # Adicionar evento à fila
            self.events.append(event)

            # Atualizar métricas globais
            self.global_metrics["total_conversions"] += 1
            if event.success:
                self.global_metrics["total_successful"] += 1
            else:
                self.global_metrics["total_failed"] += 1

            # Atualizar métricas da plataforma
            platform_metrics = self.platform_metrics[event.platform]
            platform_metrics.total_conversions += 1
            platform_metrics.total_response_time += event.response_time_ms
            platform_metrics.last_conversion = event.timestamp

            if event.success:
                platform_metrics.successful_conversions += 1
            else:
                platform_metrics.failed_conversions += 1
                if event.error_message:
                    platform_metrics.error_counts[event.error_message] = (
                        platform_metrics.error_counts.get(event.error_message, 0) + 1
                    )

            if event.cache_hit:
                platform_metrics.cache_hits += 1
            else:
                platform_metrics.cache_misses += 1

            # Verificar alertas
            self._check_alerts(event.platform, platform_metrics)

            logger.debug(
                f"Métrica registrada: {event.platform} - {'SUCCESS' if event.success else 'FAILED'}"
            )

        except Exception as e:
            logger.error(f"Erro ao registrar métrica: {e}")

    def _check_alerts(self, platform: str, metrics: PlatformMetrics) -> None:
        """Verifica se há alertas para disparar"""
        try:
            # Alerta de taxa de sucesso baixa
            if metrics.success_rate < self.alert_thresholds.get("success_rate", 0.8):
                self._trigger_alert(
                    "LOW_SUCCESS_RATE",
                    f"Taxa de sucesso baixa para {platform}: {metrics.success_rate:.2%}",
                    {"platform": platform, "success_rate": metrics.success_rate},
                )

            # Alerta de tempo de resposta alto
            if metrics.average_response_time > self.alert_thresholds.get(
                "response_time", 100
            ):
                self._trigger_alert(
                    "HIGH_RESPONSE_TIME",
                    f"Tempo de resposta alto para {platform}: {metrics.average_response_time:.2f}ms",
                    {
                        "platform": platform,
                        "response_time": metrics.average_response_time,
                    },
                )

            # Alerta de taxa de cache baixa
            if metrics.cache_hit_rate < self.alert_thresholds.get(
                "cache_hit_rate", 0.8
            ):
                self._trigger_alert(
                    "LOW_CACHE_HIT_RATE",
                    f"Taxa de cache baixa para {platform}: {metrics.cache_hit_rate:.2%}",
                    {"platform": platform, "cache_hit_rate": metrics.cache_hit_rate},
                )

        except Exception as e:
            logger.error(f"Erro ao verificar alertas: {e}")

    def _trigger_alert(
        self, alert_type: str, message: str, data: Dict[str, Any]
    ) -> None:
        """Dispara um alerta"""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }

        logger.warning(f"ALERTA: {message}")

        # Executar callbacks de alerta
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Erro no callback de alerta: {e}")

    def add_alert_callback(self, callback: callable) -> None:
        """Adiciona callback para alertas"""
        self.alert_callbacks.append(callback)

    def get_platform_metrics(self, platform: str) -> Optional[PlatformMetrics]:
        """Retorna métricas de uma plataforma específica"""
        return self.platform_metrics.get(platform)

    def get_all_platform_metrics(self) -> Dict[str, PlatformMetrics]:
        """Retorna métricas de todas as plataformas"""
        return dict(self.platform_metrics)

    def get_global_metrics(self) -> Dict[str, Any]:
        """Retorna métricas globais"""
        metrics = self.global_metrics.copy()

        # Calcular métricas derivadas
        total = metrics["total_conversions"]
        if total > 0:
            metrics["overall_success_rate"] = metrics["total_successful"] / total
            metrics["overall_failure_rate"] = metrics["total_failed"] / total

        # Calcular uptime
        uptime = datetime.now() - metrics["start_time"]
        metrics["uptime_seconds"] = uptime.total_seconds()
        metrics["uptime_hours"] = uptime.total_seconds() / 3600

        return metrics

    def get_platform_performance_ranking(self) -> List[Tuple[str, float]]:
        """Retorna ranking de performance das plataformas"""
        rankings = []

        for platform, metrics in self.platform_metrics.items():
            if metrics.total_conversions > 0:
                # Score baseado em sucesso, velocidade e cache
                score = (
                    metrics.success_rate * 0.4
                    + (1.0 - min(metrics.average_response_time / 1000, 1.0)) * 0.3
                    + metrics.cache_hit_rate * 0.3
                )
                rankings.append((platform, score))

        # Ordenar por score (maior primeiro)
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings

    def get_error_summary(self) -> Dict[str, Dict[str, int]]:
        """Retorna resumo de erros por plataforma"""
        error_summary = {}

        for platform, metrics in self.platform_metrics.items():
            if metrics.error_counts:
                error_summary[platform] = dict(metrics.error_counts)

        return error_summary

    def get_cache_performance_summary(self) -> Dict[str, Dict[str, Any]]:
        """Retorna resumo de performance do cache por plataforma"""
        cache_summary = {}

        for platform, metrics in self.platform_metrics.items():
            cache_summary[platform] = {
                "cache_hit_rate": metrics.cache_hit_rate,
                "cache_hits": metrics.cache_hits,
                "cache_misses": metrics.cache_misses,
                "total_cache_ops": metrics.cache_hits + metrics.cache_misses,
            }

        return cache_summary

    def reset_metrics(self, platform: Optional[str] = None) -> None:
        """Reseta métricas (todas ou de uma plataforma específica)"""
        if platform:
            if platform in self.platform_metrics:
                self.platform_metrics[platform] = PlatformMetrics(platform=platform)
                logger.info(f"Métricas resetadas para plataforma: {platform}")
        else:
            # Reset global
            for platform in self.platform_metrics:
                self.platform_metrics[platform] = PlatformMetrics(platform=platform)

            self.global_metrics.update(
                {
                    "total_conversions": 0,
                    "total_successful": 0,
                    "total_failed": 0,
                    "last_reset": datetime.now(),
                }
            )

            logger.info("Todas as métricas foram resetadas")

    def cleanup_old_events(self) -> None:
        """Remove eventos antigos baseado na retenção configurada"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

        # Remover eventos antigos
        while self.events and self.events[0].timestamp < cutoff_time:
            self.events.popleft()

        logger.debug(f"Cleanup realizado: {len(self.events)} eventos mantidos")

    def export_metrics(self, format: str = "json") -> str:
        """Exporta métricas em diferentes formatos"""
        try:
            data = {
                "global_metrics": self.get_global_metrics(),
                "platform_metrics": {
                    platform: {
                        "total_conversions": metrics.total_conversions,
                        "successful_conversions": metrics.successful_conversions,
                        "failed_conversions": metrics.failed_conversions,
                        "success_rate": metrics.success_rate,
                        "average_response_time": metrics.average_response_time,
                        "cache_hit_rate": metrics.cache_hit_rate,
                        "cache_hits": metrics.cache_hits,
                        "cache_misses": metrics.cache_misses,
                        "last_conversion": (
                            metrics.last_conversion.isoformat()
                            if metrics.last_conversion
                            else None
                        ),
                        "error_counts": dict(metrics.error_counts),
                    }
                    for platform, metrics in self.platform_metrics.items()
                },
                "performance_ranking": self.get_platform_performance_ranking(),
                "error_summary": self.get_error_summary(),
                "cache_performance": self.get_cache_performance_summary(),
                "export_timestamp": datetime.now().isoformat(),
            }

            if format.lower() == "json":
                return json.dumps(data, indent=2, default=str)
            else:
                raise ValueError(f"Formato não suportado: {format}")

        except Exception as e:
            logger.error(f"Erro ao exportar métricas: {e}")
            return "{}"


# Instância global do coletor de métricas
conversion_metrics = ConversionMetricsCollector()
