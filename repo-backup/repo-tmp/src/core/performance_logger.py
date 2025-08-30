"""
Sistema de logging de performance padronizado
Registra eventos na tabela perf do analytics.sqlite
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from src.utils.sqlite_helpers import execute

logger = logging.getLogger(__name__)


class PerformanceLogger:
    """Logger padronizado para eventos de performance"""

    def __init__(self):
        self.db_name = "analytics"

    def log_event(
        self,
        component: str,
        metric: str,
        value: float,
        meta_json: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Registra um evento de performance

        Args:
            component: Componente do sistema (amazon, awin, posting, etc.)
            metric: Nome da métrica (affiliate_format_invalid, amazon_asin.method, etc.)
            value: Valor numérico da métrica
            meta_json: Dados adicionais em JSON

        Returns:
            True se registrado com sucesso
        """
        try:
            meta_str = json.dumps(meta_json) if meta_json else None

            execute(
                self.db_name,
                """
                INSERT INTO perf (component, metric, value, occurred_at, meta_json)
                VALUES (?, ?, ?, datetime('now'), ?)
            """,
                [component, metric, value, meta_str],
            )

            logger.debug(f"Performance event logged: {component}.{metric} = {value}")
            return True

        except Exception as e:
            logger.error(f"Erro ao registrar evento de performance: {e}")
            return False

    def log_affiliate_format_invalid(self, platform: str, url: str, reason: str):
        """Log para formato de afiliado inválido"""
        self.log_event(
            component=platform,
            metric="affiliate_format_invalid",
            value=1,
            meta_json={
                "url": url[:100],  # Limitar tamanho
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_amazon_asin_method(self, method: str, asin: str, url: str):
        """
        Log para método de extração de ASIN da Amazon

        Args:
            method: 'url', 'html', ou 'playwright'
            asin: ASIN extraído
            url: URL original
        """
        method_values = {"url": 0, "html": 1, "playwright": 2}

        self.log_event(
            component="amazon",
            metric="amazon_asin.method",
            value=method_values.get(method, 99),
            meta_json={
                "method": method,
                "asin": asin,
                "url": url[:100],
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_amazon_asin_missing(self, url: str, strategies_tried: list):
        """Log para ASIN da Amazon não encontrado"""
        self.log_event(
            component="amazon",
            metric="amazon_asin_missing",
            value=1,
            meta_json={
                "url": url[:100],
                "strategies_tried": strategies_tried,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_deeplink_latency(
        self, platform: str, latency_ms: float, success: bool = True
    ):
        """Log para latência de geração de deeplink"""
        self.log_event(
            component=platform,
            metric="deeplink_latency_ms",
            value=latency_ms,
            meta_json={"success": success, "timestamp": datetime.now().isoformat()},
        )

    def log_badge_used(
        self, badge_type: str, product_id: int, price_context: Dict[str, Any]
    ):
        """
        Log para uso de badges

        Args:
            badge_type: 'badge_90d_internal', 'badge_90d_both', 'badge_30d_avg'
            product_id: ID do produto
            price_context: Contexto de preços
        """
        self.log_event(
            component="pricing",
            metric=badge_type,
            value=1,
            meta_json={
                "product_id": product_id,
                "price_context": price_context,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_source_type(
        self, platform: str, source_type: str, product_id: Optional[int] = None
    ):
        """
        Log para tipo de fonte utilizada

        Args:
            platform: Plataforma da fonte
            source_type: 'FEED', 'API_LIKE', ou 'SCRAPER'
            product_id: ID do produto (opcional)
        """
        source_values = {"FEED": 0, "API_LIKE": 1, "SCRAPER": 2}

        self.log_event(
            component=platform,
            metric="source_type",
            value=source_values.get(source_type, 99),
            meta_json={
                "source_type": source_type,
                "product_id": product_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_posting_success(
        self, platform: str, offer_id: str, channel: str = "telegram"
    ):
        """Log para postagem bem-sucedida"""
        self.log_event(
            component="posting",
            metric="post_success",
            value=1,
            meta_json={
                "platform": platform,
                "offer_id": offer_id,
                "channel": channel,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_posting_blocked(
        self, platform: str, reason: str, offer_data: Dict[str, Any]
    ):
        """Log para postagem bloqueada"""
        self.log_event(
            component="posting",
            metric="post_blocked",
            value=1,
            meta_json={
                "platform": platform,
                "reason": reason,
                "offer_title": offer_data.get("title", "")[:50],
                "offer_price": offer_data.get("price"),
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_scraper_performance(
        self,
        platform: str,
        store: str,
        duration_ms: float,
        success: bool,
        products_found: int = 0,
    ):
        """Log para performance de scrapers"""
        self.log_event(
            component=f"{platform}_scraper",
            metric="scraper_duration_ms",
            value=duration_ms,
            meta_json={
                "platform": platform,
                "store": store,
                "success": success,
                "products_found": products_found,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_cache_hit(self, cache_type: str, platform: str, hit: bool):
        """Log para hits/misses de cache"""
        self.log_event(
            component="cache",
            metric=f"{cache_type}_cache_hit",
            value=1 if hit else 0,
            meta_json={
                "cache_type": cache_type,
                "platform": platform,
                "hit": hit,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_api_call(
        self, api_name: str, endpoint: str, duration_ms: float, status_code: int
    ):
        """Log para chamadas de API"""
        self.log_event(
            component=f"{api_name}_api",
            metric="api_call_duration_ms",
            value=duration_ms,
            meta_json={
                "api_name": api_name,
                "endpoint": endpoint,
                "status_code": status_code,
                "success": 200 <= status_code < 300,
                "timestamp": datetime.now().isoformat(),
            },
        )


# Instância global do logger
perf_logger = PerformanceLogger()


# Funções de conveniência
def log_affiliate_invalid(platform: str, url: str, reason: str):
    """Função de conveniência para log de afiliado inválido"""
    perf_logger.log_affiliate_format_invalid(platform, url, reason)


def log_amazon_asin_extraction(method: str, asin: str, url: str):
    """Função de conveniência para log de extração ASIN"""
    perf_logger.log_amazon_asin_method(method, asin, url)


def log_amazon_asin_missing(url: str, strategies_tried: list):
    """Função de conveniência para log de ASIN não encontrado"""
    perf_logger.log_amazon_asin_missing(url, strategies_tried)


def log_deeplink_timing(platform: str, latency_ms: float, success: bool = True):
    """Função de conveniência para log de timing de deeplink"""
    perf_logger.log_deeplink_latency(platform, latency_ms, success)


def log_badge_usage(badge_type: str, product_id: int, price_context: Dict[str, Any]):
    """Função de conveniência para log de uso de badges"""
    perf_logger.log_badge_used(badge_type, product_id, price_context)


def log_source_fallback(
    platform: str, source_type: str, product_id: Optional[int] = None
):
    """Função de conveniência para log de fallback de fonte"""
    perf_logger.log_source_type(platform, source_type, product_id)


def log_post_success(platform: str, offer_id: str, channel: str = "telegram"):
    """Função de conveniência para log de postagem bem-sucedida"""
    perf_logger.log_posting_success(platform, offer_id, channel)


def log_post_blocked(platform: str, reason: str, offer_data: Dict[str, Any]):
    """Função de conveniência para log de postagem bloqueada"""
    perf_logger.log_posting_blocked(platform, reason, offer_data)
