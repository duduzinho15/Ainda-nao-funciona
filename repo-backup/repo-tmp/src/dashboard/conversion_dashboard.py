"""
Dashboard de Conversões por Plataforma
Interface para monitoramento de performance e métricas de conversão
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.core.cache_config import production_cache_config
from src.core.conversion_metrics import conversion_metrics
from src.core.failure_alerts import failure_alert_system

logger = logging.getLogger(__name__)


class ConversionDashboard:
    """Dashboard de conversões por plataforma"""

    def __init__(self):
        self.metrics_collector = conversion_metrics
        self.alert_system = failure_alert_system
        self.cache_config = production_cache_config
        self.refresh_interval = 30  # Segundos
        self.last_refresh = datetime.min  # Forçar primeira atualização
        self._cached_data = {}  # Inicializar cache vazio

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Retorna dados completos do dashboard"""
        try:
            current_time = datetime.now()

            # Verificar se precisa atualizar
            if (
                current_time - self.last_refresh
            ).total_seconds() < self.refresh_interval:
                # Retornar dados em cache se disponível
                return self._cached_data

            # Coletar dados atualizados
            overview = await self._get_overview_data()
            platform_metrics = await self._get_platform_metrics()
            performance_ranking = await self._get_performance_ranking()
            cache_performance = await self._get_cache_performance()
            error_summary = await self._get_error_summary()
            active_alerts = await self._get_active_alerts()
            system_health = await self._get_system_health()
            trends = await self._get_trends_data()

            dashboard_data = {
                "timestamp": current_time.isoformat(),
                "refresh_interval": self.refresh_interval,
                "overview": overview,
                "platform_metrics": platform_metrics,
                "performance_ranking": performance_ranking,
                "cache_performance": cache_performance,
                "error_summary": error_summary,
                "active_alerts": active_alerts,
                "system_health": system_health,
                "trends": trends,
            }

            # Cache dos dados
            self._cached_data = dashboard_data
            self.last_refresh = current_time

            return dashboard_data

        except Exception as e:
            logger.error(f"Erro ao obter dados do dashboard: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _get_overview_data(self) -> Dict[str, Any]:
        """Retorna dados de visão geral"""
        try:
            global_metrics = self.metrics_collector.get_global_metrics()

            return {
                "total_conversions": global_metrics.get("total_conversions", 0),
                "successful_conversions": global_metrics.get("total_successful", 0),
                "failed_conversions": global_metrics.get("total_failed", 0),
                "overall_success_rate": global_metrics.get("overall_success_rate", 0.0),
                "uptime_hours": global_metrics.get("uptime_hours", 0.0),
                "last_reset": global_metrics.get(
                    "last_reset", datetime.now()
                ).isoformat(),
                "platforms_count": len(self.cache_config.get_all_platforms()),
                "active_alerts_count": len(self.alert_system.get_active_alerts()),
            }

        except Exception as e:
            logger.error(f"Erro ao obter dados de visão geral: {e}")
            return {}

    async def _get_platform_metrics(self) -> Dict[str, Any]:
        """Retorna métricas detalhadas por plataforma"""
        try:
            platform_data = {}
            all_metrics = self.metrics_collector.get_all_platform_metrics()

            for platform, metrics in all_metrics.items():
                platform_config = self.cache_config.get_platform_config(platform)

                platform_data[platform] = {
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
                    "config": (
                        {
                            "ttl_seconds": (
                                platform_config.ttl_seconds if platform_config else 3600
                            ),
                            "strategy": (
                                platform_config.strategy.value
                                if platform_config
                                else "balanced"
                            ),
                            "priority": (
                                platform_config.priority if platform_config else 5
                            ),
                            "compression": (
                                platform_config.compression if platform_config else True
                            ),
                            "encryption": (
                                platform_config.encryption if platform_config else False
                            ),
                        }
                        if platform_config
                        else {}
                    ),
                }

            return platform_data

        except Exception as e:
            logger.error(f"Erro ao obter métricas de plataforma: {e}")
            return {}

    async def _get_performance_ranking(self) -> List[Dict[str, Any]]:
        """Retorna ranking de performance das plataformas"""
        try:
            ranking = self.metrics_collector.get_platform_performance_ranking()
            ranking_data = []

            for i, (platform, score) in enumerate(ranking, 1):
                platform_metrics = self.metrics_collector.get_platform_metrics(platform)

                ranking_data.append(
                    {
                        "position": i,
                        "platform": platform,
                        "score": round(score, 4),
                        "success_rate": (
                            platform_metrics.success_rate if platform_metrics else 0.0
                        ),
                        "response_time": (
                            platform_metrics.average_response_time
                            if platform_metrics
                            else 0.0
                        ),
                        "cache_hit_rate": (
                            platform_metrics.cache_hit_rate if platform_metrics else 0.0
                        ),
                        "total_conversions": (
                            platform_metrics.total_conversions
                            if platform_metrics
                            else 0
                        ),
                    }
                )

            return ranking_data

        except Exception as e:
            logger.error(f"Erro ao obter ranking de performance: {e}")
            return []

    async def _get_cache_performance(self) -> Dict[str, Any]:
        """Retorna dados de performance do cache"""
        try:
            cache_summary = self.metrics_collector.get_cache_performance_summary()
            cache_config = self.cache_config.get_cache_stats_config()

            # Calcular métricas agregadas do cache
            total_hits = sum(
                platform["cache_hits"] for platform in cache_summary.values()
            )
            total_misses = sum(
                platform["cache_misses"] for platform in cache_summary.values()
            )
            total_ops = total_hits + total_misses
            overall_hit_rate = total_hits / total_ops if total_ops > 0 else 0.0

            return {
                "overall_performance": {
                    "total_operations": total_ops,
                    "total_hits": total_hits,
                    "total_misses": total_misses,
                    "overall_hit_rate": round(overall_hit_rate, 4),
                },
                "platform_performance": cache_summary,
                "configuration": cache_config,
            }

        except Exception as e:
            logger.error(f"Erro ao obter performance do cache: {e}")
            return {}

    async def _get_error_summary(self) -> Dict[str, Any]:
        """Retorna resumo de erros por plataforma"""
        try:
            error_summary = self.metrics_collector.get_error_summary()

            # Calcular estatísticas agregadas
            total_errors = sum(
                sum(error_counts.values()) for error_counts in error_summary.values()
            )

            # Top erros por frequência
            all_errors = {}
            for platform, errors in error_summary.items():
                for error_msg, count in errors.items():
                    if error_msg not in all_errors:
                        all_errors[error_msg] = {"count": 0, "platforms": []}
                    all_errors[error_msg]["count"] += count
                    all_errors[error_msg]["platforms"].append(platform)

            # Ordenar por frequência
            top_errors = sorted(
                all_errors.items(), key=lambda x: x[1]["count"], reverse=True
            )[
                :10
            ]  # Top 10

            return {
                "total_errors": total_errors,
                "platforms_with_errors": len(error_summary),
                "error_distribution": error_summary,
                "top_errors": [
                    {
                        "error_message": error_msg,
                        "total_count": error_data["count"],
                        "affected_platforms": error_data["platforms"],
                    }
                    for error_msg, error_data in top_errors
                ],
            }

        except Exception as e:
            logger.error(f"Erro ao obter resumo de erros: {e}")
            return {}

    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Retorna alertas ativos"""
        try:
            active_alerts = self.alert_system.get_active_alerts()

            return [
                {
                    "id": alert.id,
                    "rule_name": alert.rule_name,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "status": alert.status.value,
                    "occurrences": alert.occurrences,
                    "metadata": alert.metadata,
                }
                for alert in active_alerts
            ]

        except Exception as e:
            logger.error(f"Erro ao obter alertas ativos: {e}")
            return []

    async def _get_system_health(self) -> Dict[str, Any]:
        """Retorna status de saúde do sistema"""
        try:
            # Verificar métricas de saúde
            global_metrics = self.metrics_collector.get_global_metrics()

            # Calcular indicadores de saúde
            overall_success_rate = global_metrics.get("overall_success_rate", 1.0)
            uptime_hours = global_metrics.get("uptime_hours", 0.0)

            # Determinar status geral
            if overall_success_rate >= 0.95 and uptime_hours > 1:
                overall_status = "healthy"
                status_color = "green"
            elif overall_success_rate >= 0.8 and uptime_hours > 0.5:
                overall_status = "warning"
                status_color = "yellow"
            else:
                overall_status = "critical"
                status_color = "red"

            # Verificar saúde por plataforma
            platform_health = {}
            for platform in self.cache_config.get_all_platforms():
                metrics = self.metrics_collector.get_platform_metrics(platform)
                if metrics and metrics.total_conversions > 0:
                    if metrics.success_rate >= 0.9:
                        platform_health[platform] = "healthy"
                    elif metrics.success_rate >= 0.7:
                        platform_health[platform] = "warning"
                    else:
                        platform_health[platform] = "critical"
                else:
                    platform_health[platform] = "unknown"

            return {
                "overall_status": overall_status,
                "status_color": status_color,
                "overall_success_rate": overall_success_rate,
                "uptime_hours": uptime_hours,
                "platform_health": platform_health,
                "active_alerts_count": len(self.alert_system.get_active_alerts()),
                "last_check": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Erro ao obter saúde do sistema: {e}")
            return {"overall_status": "unknown", "error": str(e)}

    async def _get_trends_data(self) -> Dict[str, Any]:
        """Retorna dados de tendências (simulado por enquanto)"""
        try:
            # Por enquanto, retorna dados simulados
            # Em produção, isso seria baseado em dados históricos reais
            current_time = datetime.now()

            # Simular tendências das últimas 24 horas
            trends = {
                "conversion_trend": {
                    "labels": [
                        (current_time - timedelta(hours=23 - i)).strftime("%H:00")
                        for i in range(24)
                    ],
                    "data": [
                        # Simular dados de conversão por hora
                        max(0, 100 + (i * 10) + (hash(f"hour_{i}") % 50))
                        for i in range(24)
                    ],
                },
                "success_rate_trend": {
                    "labels": [
                        (current_time - timedelta(hours=23 - i)).strftime("%H:00")
                        for i in range(24)
                    ],
                    "data": [
                        # Simular taxa de sucesso por hora
                        max(0.7, min(1.0, 0.85 + (hash(f"success_{i}") % 30) / 100))
                        for i in range(24)
                    ],
                },
                "response_time_trend": {
                    "labels": [
                        (current_time - timedelta(hours=23 - i)).strftime("%H:00")
                        for i in range(24)
                    ],
                    "data": [
                        # Simular tempo de resposta por hora
                        max(50, min(500, 150 + (hash(f"response_{i}") % 300)))
                        for i in range(24)
                    ],
                },
            }

            return trends

        except Exception as e:
            logger.error(f"Erro ao obter dados de tendências: {e}")
            return {}

    async def get_platform_details(self, platform: str) -> Dict[str, Any]:
        """Retorna detalhes específicos de uma plataforma"""
        try:
            metrics = self.metrics_collector.get_platform_metrics(platform)
            platform_config = self.cache_config.get_platform_config(platform)

            if not metrics:
                return {"error": f"Plataforma {platform} não encontrada"}

            # Obter alertas específicos da plataforma
            platform_alerts = [
                alert
                for alert in self.alert_system.get_active_alerts()
                if platform in alert.metadata.get("platform", "")
            ]

            return {
                "platform": platform,
                "metrics": {
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
                },
                "configuration": (
                    {
                        "ttl_seconds": (
                            platform_config.ttl_seconds if platform_config else 3600
                        ),
                        "strategy": (
                            platform_config.strategy.value
                            if platform_config
                            else "balanced"
                        ),
                        "priority": platform_config.priority if platform_config else 5,
                        "max_retries": (
                            platform_config.max_retries if platform_config else 3
                        ),
                        "compression": (
                            platform_config.compression if platform_config else True
                        ),
                        "encryption": (
                            platform_config.encryption if platform_config else False
                        ),
                    }
                    if platform_config
                    else {}
                ),
                "active_alerts": [
                    {
                        "id": alert.id,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "occurrences": alert.occurrences,
                    }
                    for alert in platform_alerts
                ],
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Erro ao obter detalhes da plataforma {platform}: {e}")
            return {"error": str(e)}

    async def export_dashboard_data(self, format: str = "json") -> str:
        """Exporta dados do dashboard"""
        try:
            dashboard_data = await self.get_dashboard_data()

            if format.lower() == "json":
                return json.dumps(dashboard_data, indent=2, default=str)
            else:
                raise ValueError(f"Formato não suportado: {format}")

        except Exception as e:
            logger.error(f"Erro ao exportar dados do dashboard: {e}")
            return "{}"

    def set_refresh_interval(self, seconds: int) -> None:
        """Define intervalo de atualização do dashboard"""
        self.refresh_interval = max(10, seconds)  # Mínimo 10 segundos
        logger.info(
            f"Intervalo de atualização do dashboard definido para {self.refresh_interval} segundos"
        )

    async def force_refresh(self) -> Dict[str, Any]:
        """Força atualização dos dados do dashboard"""
        self.last_refresh = datetime.min  # Forçar atualização
        return await self.get_dashboard_data()


# Instância global do dashboard
conversion_dashboard = ConversionDashboard()
