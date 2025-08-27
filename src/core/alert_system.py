"""
Sistema de alertas para o Dashboard
Detecta problemas e gera alertas automáticos baseados nas métricas
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .analytics_queries import (
    amazon_asin_strategy_7d,
    deeplink_latency_7d,
    get_dashboard_summary,
    get_recent_blocked_posts,
    posts_blocked_7d,
    price_freshness_7d,
)

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """Estrutura de um alerta"""

    id: str
    title: str
    message: str
    severity: str  # "info", "warning", "error", "critical"
    category: str  # "amazon", "affiliation", "performance", "system"
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None
    action_required: bool = False
    auto_resolve: bool = True


class AlertSystem:
    """Sistema de detecção e geração de alertas"""

    def __init__(self):
        self.alert_thresholds = {
            "amazon_asin_pct_min": 95.0,
            "playwright_pct_max": 10.0,
            "blocked_posts_max": 0,
            "freshness_warning_days": 1.5,
            "freshness_critical_days": 3.0,
            "latency_warning_ms": 2000,
            "latency_critical_ms": 5000,
        }

    def check_all_alerts(self, period: str = "7d") -> List[Alert]:
        """
        Verifica todas as condições de alerta

        Args:
            period: Período para análise ("7d" ou "30d")

        Returns:
            Lista de alertas ativos
        """
        alerts = []

        try:
            # Alertas de qualidade Amazon ASIN
            alerts.extend(self._check_amazon_alerts(period))

            # Alertas de afiliação
            alerts.extend(self._check_affiliation_alerts(period))

            # Alertas de performance
            alerts.extend(self._check_performance_alerts())

            # Alertas de sistema
            alerts.extend(self._check_system_alerts())

        except Exception as e:
            logger.error(f"Erro ao verificar alertas: {e}")
            alerts.append(
                Alert(
                    id="alert_system_error",
                    title="Erro no Sistema de Alertas",
                    message=f"Falha ao verificar alertas: {str(e)}",
                    severity="error",
                    category="system",
                    timestamp=datetime.now(),
                    action_required=True,
                    auto_resolve=False,
                )
            )

        return alerts

    def _check_amazon_alerts(self, period: str) -> List[Alert]:
        """Verifica alertas relacionados à Amazon"""
        alerts = []

        try:
            # Verificar qualidade ASIN
            summary = get_dashboard_summary(period)
            asin_pct = summary.get("amazon_asin_pct", 0)

            if asin_pct < self.alert_thresholds["amazon_asin_pct_min"]:
                severity = "critical" if asin_pct < 85 else "warning"
                alerts.append(
                    Alert(
                        id="amazon_asin_low",
                        title="Qualidade ASIN Amazon Baixa",
                        message=(
                            f"Apenas {asin_pct:.1f}% das ofertas Amazon têm ASIN válido "
                            f"(meta: ≥{self.alert_thresholds['amazon_asin_pct_min']:.0f}%)"
                        ),
                        severity=severity,
                        category="amazon",
                        timestamp=datetime.now(),
                        data={"asin_pct": asin_pct, "period": period},
                        action_required=True,
                    )
                )

            # Verificar uso excessivo de Playwright
            playwright_pct = summary.get("playwright_pct", 0)
            if playwright_pct > self.alert_thresholds["playwright_pct_max"]:
                severity = "critical" if playwright_pct > 20 else "warning"
                alerts.append(
                    Alert(
                        id="playwright_high_usage",
                        title="Uso Alto de Playwright",
                        message=(
                            f"Playwright sendo usado em {playwright_pct:.1f}% dos casos "
                            f"(meta: ≤{self.alert_thresholds['playwright_pct_max']:.0f}%) - Possível anti-bot"
                        ),
                        severity=severity,
                        category="amazon",
                        timestamp=datetime.now(),
                        data={"playwright_pct": playwright_pct, "period": period},
                        action_required=True,
                    )
                )

            # Verificar distribuição de estratégias
            strategies = amazon_asin_strategy_7d()
            total_extractions = sum(s["cnt"] for s in strategies)

            if total_extractions > 0:
                url_pct = (
                    next((s["cnt"] for s in strategies if s["method"] == "url"), 0)
                    / total_extractions
                    * 100
                )

                if url_pct < 70:  # Esperamos que a maioria seja via URL
                    alerts.append(
                        Alert(
                            id="asin_url_extraction_low",
                            title="Extração ASIN via URL Baixa",
                            message=(
                                f"Apenas {url_pct:.1f}% das extrações são via URL "
                                f"(ideal: >70%) - URLs podem estar mal formadas"
                            ),
                            severity="warning",
                            category="amazon",
                            timestamp=datetime.now(),
                            data={"url_pct": url_pct, "strategies": strategies},
                        )
                    )

        except Exception as e:
            logger.error(f"Erro ao verificar alertas Amazon: {e}")

        return alerts

    def _check_affiliation_alerts(self, period: str) -> List[Alert]:
        """Verifica alertas relacionados à afiliação"""
        alerts = []

        try:
            # Verificar posts bloqueados
            blocked_posts = posts_blocked_7d()
            total_blocked = sum(post["blocked"] for post in blocked_posts)

            if total_blocked > self.alert_thresholds["blocked_posts_max"]:
                severity = "critical" if total_blocked > 10 else "error"

                # Detalhes dos bloqueios
                blocked_details = []
                for post in blocked_posts[:3]:  # Top 3
                    blocked_details.append(
                        f"{post['platform']}: {post['blocked']} ({post['reason']})"
                    )

                alerts.append(
                    Alert(
                        id="posts_blocked",
                        title="Posts Bloqueados por Afiliação",
                        message=f"{total_blocked} posts bloqueados ({period}): {', '.join(blocked_details)}",
                        severity=severity,
                        category="affiliation",
                        timestamp=datetime.now(),
                        data={"total_blocked": total_blocked, "details": blocked_posts},
                        action_required=True,
                    )
                )

            # Verificar posts bloqueados recentes
            recent_blocked = get_recent_blocked_posts(5)
            if recent_blocked:
                recent_count = len(recent_blocked)
                last_blocked = (
                    recent_blocked[0]["occurred_at"] if recent_blocked else None
                )

                alerts.append(
                    Alert(
                        id="recent_blocks",
                        title="Bloqueios Recentes Detectados",
                        message=f"{recent_count} posts bloqueados recentemente. Último: {last_blocked}",
                        severity="warning",
                        category="affiliation",
                        timestamp=datetime.now(),
                        data={"recent_blocks": recent_blocked},
                        action_required=False,
                    )
                )

        except Exception as e:
            logger.error(f"Erro ao verificar alertas de afiliação: {e}")

        return alerts

    def _check_performance_alerts(self) -> List[Alert]:
        """Verifica alertas relacionados à performance"""
        alerts = []

        try:
            # Verificar freshness de preços
            freshness_data = price_freshness_7d()

            for platform_data in freshness_data:
                platform = platform_data["platform"]
                internal_age = platform_data.get("avg_age_internal_days", 0) or 0
                external_age = platform_data.get("avg_age_external_days", 0) or 0

                # Alertas para dados internos
                if internal_age > self.alert_thresholds["freshness_critical_days"]:
                    alerts.append(
                        Alert(
                            id=f"freshness_critical_{platform}",
                            title=f"Dados {platform} Muito Desatualizados",
                            message=(
                                f"Preços internos com {internal_age:.1f} dias de idade "
                                f"(crítico: >{self.alert_thresholds['freshness_critical_days']:.1f}d)"
                            ),
                            severity="critical",
                            category="performance",
                            timestamp=datetime.now(),
                            data={"platform": platform, "age_days": internal_age},
                            action_required=True,
                        )
                    )
                elif internal_age > self.alert_thresholds["freshness_warning_days"]:
                    alerts.append(
                        Alert(
                            id=f"freshness_warning_{platform}",
                            title=f"Dados {platform} Desatualizados",
                            message=(
                                f"Preços internos com {internal_age:.1f} dias de idade "
                                f"(atenção: >{self.alert_thresholds['freshness_warning_days']:.1f}d)"
                            ),
                            severity="warning",
                            category="performance",
                            timestamp=datetime.now(),
                            data={"platform": platform, "age_days": internal_age},
                        )
                    )

                # Alertas para dados externos muito desatualizados
                if external_age > 7 and external_age > internal_age * 2:
                    alerts.append(
                        Alert(
                            id=f"external_freshness_{platform}",
                            title=f"Dados Externos {platform} Desatualizados",
                            message=f"Preços externos com {external_age:.1f} dias - Zoom/Buscapé podem estar falhando",
                            severity="warning",
                            category="performance",
                            timestamp=datetime.now(),
                            data={
                                "platform": platform,
                                "external_age": external_age,
                                "internal_age": internal_age,
                            },
                        )
                    )

            # Verificar latência de deeplinks
            latency_data = deeplink_latency_7d()

            for platform_data in latency_data:
                platform = platform_data["platform"]
                avg_ms = platform_data.get("avg_ms", 0) or 0
                p95_ms = platform_data.get("p95_ms", 0) or 0

                if p95_ms > self.alert_thresholds["latency_critical_ms"]:
                    alerts.append(
                        Alert(
                            id=f"latency_critical_{platform}",
                            title=f"Latência Crítica {platform}",
                            message=(
                                f"P95 de {p95_ms:.0f}ms para deeplinks "
                                f"(crítico: >{self.alert_thresholds['latency_critical_ms']:.0f}ms)"
                            ),
                            severity="critical",
                            category="performance",
                            timestamp=datetime.now(),
                            data={
                                "platform": platform,
                                "p95_ms": p95_ms,
                                "avg_ms": avg_ms,
                            },
                            action_required=True,
                        )
                    )
                elif avg_ms > self.alert_thresholds["latency_warning_ms"]:
                    alerts.append(
                        Alert(
                            id=f"latency_warning_{platform}",
                            title=f"Latência Alta {platform}",
                            message=(
                                f"Média de {avg_ms:.0f}ms para deeplinks "
                                f"(atenção: >{self.alert_thresholds['latency_warning_ms']:.0f}ms)"
                            ),
                            severity="warning",
                            category="performance",
                            timestamp=datetime.now(),
                            data={"platform": platform, "avg_ms": avg_ms},
                        )
                    )

        except Exception as e:
            logger.error(f"Erro ao verificar alertas de performance: {e}")

        return alerts

    def _check_system_alerts(self) -> List[Alert]:
        """Verifica alertas relacionados ao sistema"""
        alerts = []

        try:
            from .analytics_queries import health_check

            health = health_check()

            # Verificar views SQL
            if not health.get("views_ok", False):
                alerts.append(
                    Alert(
                        id="views_missing",
                        title="Views SQL Ausentes",
                        message=(
                            f"Apenas {health.get('views_count', 0)}/{health.get('expected_views', 11)} "
                            f"views encontradas - Dashboard pode não funcionar corretamente"
                        ),
                        severity="critical",
                        category="system",
                        timestamp=datetime.now(),
                        data=health,
                        action_required=True,
                        auto_resolve=False,
                    )
                )

            # Verificar dados recentes
            if not health.get("data_fresh", False):
                alerts.append(
                    Alert(
                        id="data_stale",
                        title="Dados Não Recentes",
                        message=(
                            f"Apenas {health.get('recent_events', 0)} eventos nas últimas 24h - "
                            f"Sistema pode estar parado"
                        ),
                        severity="warning",
                        category="system",
                        timestamp=datetime.now(),
                        data=health,
                        action_required=True,
                    )
                )

        except Exception as e:
            logger.error(f"Erro ao verificar alertas de sistema: {e}")

        return alerts

    def get_alert_summary(self, alerts: List[Alert]) -> Dict[str, Any]:
        """
        Gera resumo dos alertas por categoria e severidade

        Args:
            alerts: Lista de alertas

        Returns:
            Dicionário com resumo
        """
        summary = {
            "total": len(alerts),
            "by_severity": {"info": 0, "warning": 0, "error": 0, "critical": 0},
            "by_category": {
                "amazon": 0,
                "affiliation": 0,
                "performance": 0,
                "system": 0,
            },
            "action_required": 0,
            "most_critical": None,
        }

        critical_alerts = []

        for alert in alerts:
            # Contar por severidade
            summary["by_severity"][alert.severity] += 1

            # Contar por categoria
            if alert.category in summary["by_category"]:
                summary["by_category"][alert.category] += 1

            # Contar ação requerida
            if alert.action_required:
                summary["action_required"] += 1

            # Coletar alertas críticos
            if alert.severity == "critical":
                critical_alerts.append(alert)

        # Encontrar o alerta mais crítico
        if critical_alerts:
            summary["most_critical"] = critical_alerts[0]
        elif alerts:
            # Se não há críticos, pegar o primeiro erro ou warning
            error_alerts = [a for a in alerts if a.severity == "error"]
            warning_alerts = [a for a in alerts if a.severity == "warning"]

            if error_alerts:
                summary["most_critical"] = error_alerts[0]
            elif warning_alerts:
                summary["most_critical"] = warning_alerts[0]

        return summary

    def format_alert_for_display(self, alert: Alert) -> str:
        """
        Formata um alerta para exibição

        Args:
            alert: Alerta a ser formatado

        Returns:
            String formatada
        """
        severity_icons = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}

        icon = severity_icons.get(alert.severity, "📋")
        action_text = " [AÇÃO NECESSÁRIA]" if alert.action_required else ""

        return f"{icon} {alert.title}: {alert.message}{action_text}"


# Instância global do sistema de alertas
alert_system = AlertSystem()


def get_active_alerts(period: str = "7d") -> List[Alert]:
    """Função de conveniência para obter alertas ativos"""
    return alert_system.check_all_alerts(period)


def get_alerts_summary(period: str = "7d") -> Dict[str, Any]:
    """Função de conveniência para obter resumo de alertas"""
    alerts = get_active_alerts(period)
    return alert_system.get_alert_summary(alerts)
