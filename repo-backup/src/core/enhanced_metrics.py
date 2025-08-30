"""
Métricas aprimoradas para debug e observabilidade detalhada.

Implementa logging estruturado e métricas granulares para identificar
problemas específicos em afiliação, ASIN e qualidade de links.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from src.core.performance_logger import PerformanceLogger

logger = logging.getLogger(__name__)
perf_logger = PerformanceLogger()


class EnhancedMetrics:
    """Sistema de métricas aprimoradas para observabilidade"""

    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def log_affiliate_validation_failure(
        self,
        platform: str,
        url: str,
        reason: str,
        validation_details: Dict[str, Any] = None,
    ):
        """
        Registra falha na validação de link de afiliado com detalhes.

        Args:
            platform: Plataforma do link (amazon, awin, etc.)
            url: URL que falhou na validação
            reason: Motivo da falha
            validation_details: Detalhes específicos da validação
        """
        details = validation_details or {}
        details.update(
            {
                "url": url,
                "reason": reason,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

        perf_logger.log_event(
            component=platform,
            metric="affiliate_validation_failure",
            value=1,
            meta_json=json.dumps(details, ensure_ascii=False),
        )

        logger.warning(
            f"Validação de afiliado falhou - {platform}: {reason} | URL: {url[:100]}"
        )

    def log_asin_extraction_attempt(
        self,
        url: str,
        strategy: str,
        success: bool,
        asin: Optional[str] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ):
        """
        Registra tentativa de extração de ASIN com detalhes completos.

        Args:
            url: URL da Amazon processada
            strategy: Estratégia utilizada (url, html, playwright)
            success: Se a extração foi bem-sucedida
            asin: ASIN extraído (se bem-sucedido)
            error: Erro encontrado (se falhou)
            duration_ms: Duração da extração em milissegundos
        """
        details = {
            "url": url,
            "strategy": strategy,
            "success": success,
            "asin": asin,
            "error": error,
            "duration_ms": duration_ms,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
        }

        metric = "asin_extraction_success" if success else "asin_extraction_failure"

        perf_logger.log_event(
            component="amazon",
            metric=metric,
            value=1 if success else 0,
            meta_json=json.dumps(details, ensure_ascii=False),
        )

        if success:
            logger.info(
                f"ASIN extraído com sucesso via {strategy}: {asin} | URL: {url[:100]}"
            )
        else:
            logger.warning(
                f"Falha na extração ASIN via {strategy}: {error} | URL: {url[:100]}"
            )

    def log_posting_block(
        self,
        platform: str,
        url: str,
        block_reason: str,
        offer_details: Dict[str, Any] = None,
    ):
        """
        Registra bloqueio de postagem com contexto completo.

        Args:
            platform: Plataforma da oferta
            url: URL da oferta bloqueada
            block_reason: Motivo do bloqueio
            offer_details: Detalhes da oferta (título, preço, etc.)
        """
        details = offer_details or {}
        details.update(
            {
                "url": url,
                "block_reason": block_reason,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

        perf_logger.log_event(
            component=platform,
            metric="posting_blocked",
            value=1,
            meta_json=json.dumps(details, ensure_ascii=False),
        )

        logger.error(
            f"Postagem bloqueada - {platform}: {block_reason} | URL: {url[:100]}"
        )

    def log_quality_check(
        self,
        check_type: str,
        platform: str,
        passed: bool,
        details: Dict[str, Any] = None,
    ):
        """
        Registra verificação de qualidade (ASIN, afiliação, etc.).

        Args:
            check_type: Tipo de verificação (asin_format, affiliate_valid, etc.)
            platform: Plataforma verificada
            passed: Se passou na verificação
            details: Detalhes específicos da verificação
        """
        check_details = details or {}
        check_details.update(
            {
                "check_type": check_type,
                "passed": passed,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

        metric = f"quality_check_{check_type}"

        perf_logger.log_event(
            component=platform,
            metric=metric,
            value=1 if passed else 0,
            meta_json=json.dumps(check_details, ensure_ascii=False),
        )

        status = "PASSOU" if passed else "FALHOU"
        logger.info(f"Verificação de qualidade {check_type} - {platform}: {status}")

    def log_performance_degradation(
        self,
        component: str,
        metric_name: str,
        current_value: float,
        threshold: float,
        severity: str = "warning",
    ):
        """
        Registra degradação de performance quando métricas excedem limites.

        Args:
            component: Componente afetado
            metric_name: Nome da métrica
            current_value: Valor atual da métrica
            threshold: Limite configurado
            severity: Severidade (warning, error, critical)
        """
        details = {
            "metric_name": metric_name,
            "current_value": current_value,
            "threshold": threshold,
            "severity": severity,
            "degradation_pct": ((current_value - threshold) / threshold) * 100,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
        }

        perf_logger.log_event(
            component=component,
            metric="performance_degradation",
            value=current_value,
            meta_json=json.dumps(details, ensure_ascii=False),
        )

        logger.warning(
            f"Degradação de performance - {component}.{metric_name}: {current_value} > {threshold} ({severity})"
        )

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo das métricas da sessão atual.

        Returns:
            Dicionário com resumo das métricas registradas
        """
        from src.core.analytics_queries import q

        try:
            # Buscar métricas da sessão atual
            session_metrics = q(
                """
                SELECT
                    component,
                    metric,
                    COUNT(*) as count,
                    AVG(value) as avg_value,
                    MAX(value) as max_value,
                    MIN(value) as min_value
                FROM perf
                WHERE json_extract(meta_json, '$.session_id') = ?
                GROUP BY component, metric
                ORDER BY count DESC
            """,
                [self.session_id],
            )

            summary = {
                "session_id": self.session_id,
                "total_events": sum(m["count"] for m in session_metrics),
                "metrics_by_component": {},
                "top_issues": [],
            }

            for metric in session_metrics:
                component = metric["component"]
                if component not in summary["metrics_by_component"]:
                    summary["metrics_by_component"][component] = {}

                summary["metrics_by_component"][component][metric["metric"]] = {
                    "count": metric["count"],
                    "avg_value": metric["avg_value"],
                    "max_value": metric["max_value"],
                    "min_value": metric["min_value"],
                }

                # Identificar principais problemas
                if "failure" in metric["metric"] or "blocked" in metric["metric"]:
                    summary["top_issues"].append(
                        {
                            "component": component,
                            "metric": metric["metric"],
                            "count": metric["count"],
                        }
                    )

            # Ordenar problemas por frequência
            summary["top_issues"] = sorted(
                summary["top_issues"], key=lambda x: x["count"], reverse=True
            )[:10]

            return summary

        except Exception as e:
            logger.error(f"Erro ao gerar resumo da sessão: {e}")
            return {"session_id": self.session_id, "error": str(e)}


# Instância global para uso conveniente
enhanced_metrics = EnhancedMetrics()


# Funções de conveniência
def log_affiliate_failure(
    platform: str, url: str, reason: str, details: Dict[str, Any] = None
):
    """Função de conveniência para registrar falha de afiliação"""
    enhanced_metrics.log_affiliate_validation_failure(platform, url, reason, details)


def log_asin_attempt(url: str, strategy: str, success: bool, **kwargs):
    """Função de conveniência para registrar tentativa de ASIN"""
    enhanced_metrics.log_asin_extraction_attempt(url, strategy, success, **kwargs)


def log_post_blocked(
    platform: str, url: str, reason: str, details: Dict[str, Any] = None
):
    """Função de conveniência para registrar bloqueio de post"""
    enhanced_metrics.log_posting_block(platform, url, reason, details)


def log_quality_check(
    check_type: str, platform: str, passed: bool, details: Dict[str, Any] = None
):
    """Função de conveniência para registrar verificação de qualidade"""
    enhanced_metrics.log_quality_check(check_type, platform, passed, details)
