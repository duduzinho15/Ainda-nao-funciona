"""
Data layer para métricas do Dashboard Flet
Funções que consultam as views SQL para fornecer dados ao dashboard
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)

# Caminho do banco analytics
DB_PATH = Path("analytics")


def q(sql: str, params: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    """
    Executa query SQL e retorna resultado como lista de dicionários

    Args:
        sql: Query SQL a ser executada
        params: Parâmetros para a query

    Returns:
        Lista de dicionários com os resultados
    """
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.execute(sql, params or [])
        results = [dict(r) for r in cur.fetchall()]
        con.close()
        return results
    except Exception as e:
        logger.error(f"Erro ao executar query: {e}")
        logger.debug(f"SQL: {sql}, Params: {params}")
        return []


def amazon_asin_quality_7d() -> dict[str, Any]:
    """
    Qualidade de ASIN Amazon nos últimos 7 dias

    Returns:
        Dict com with, without, total e percentual
    """
    try:
        rows = q("SELECT * FROM vw_amz_asin_quality_7d")
        if not rows:
            return {"with": 0, "without": 0, "total": 0, "pct": 0.0}

        row = rows[0]
        total = row["total"] or 0
        with_asin = row["with_asin"] or 0
        without_asin = row["without_asin"] or 0

        pct = (with_asin / total * 100.0) if total > 0 else 0.0

        return {
            "with": with_asin,
            "without": without_asin,
            "total": total,
            "pct": round(pct, 2),
        }
    except Exception as e:
        logger.error(f"Erro ao obter qualidade ASIN Amazon: {e}")
        return {"with": 0, "without": 0, "total": 0, "pct": 0.0}


def amazon_asin_quality_30d() -> dict[str, Any]:
    """
    Qualidade de ASIN Amazon nos últimos 30 dias

    Returns:
        Dict com with, without, total e percentual
    """
    try:
        rows = q("SELECT * FROM vw_amz_asin_quality_30d")
        if not rows:
            return {"with": 0, "without": 0, "total": 0, "pct": 0.0}

        row = rows[0]
        total = row["total"] or 0
        with_asin = row["with_asin"] or 0
        without_asin = row["without_asin"] or 0

        pct = (with_asin / total * 100.0) if total > 0 else 0.0

        return {
            "with": with_asin,
            "without": without_asin,
            "total": total,
            "pct": round(pct, 2),
        }
    except Exception as e:
        logger.error(f"Erro ao obter qualidade ASIN Amazon (30d): {e}")
        return {"with": 0, "without": 0, "total": 0, "pct": 0.0}


def amazon_asin_strategy_7d() -> list[dict[str, Any]]:
    """
    Distribuição de estratégias ASIN nos últimos 7 dias

    Returns:
        Lista com method e cnt para cada estratégia
    """
    try:
        results = q("SELECT method, cnt FROM vw_amz_asin_strategy_7d ORDER BY cnt DESC")

        # Garantir que todas as estratégias apareçam, mesmo com 0
        strategies = {"url": 0, "html": 0, "playwright": 0}

        for row in results:
            method = row["method"]
            if method in strategies:
                strategies[method] = row["cnt"]

        return [{"method": method, "cnt": cnt} for method, cnt in strategies.items()]
    except Exception as e:
        logger.error(f"Erro ao obter estratégias ASIN: {e}")
        return [
            {"method": "url", "cnt": 0},
            {"method": "html", "cnt": 0},
            {"method": "playwright", "cnt": 0},
        ]


def posts_blocked_7d() -> list[dict[str, Any]]:
    """
    Posts bloqueados por motivo/plataforma nos últimos 7 dias

    Returns:
        Lista com platform, reason e blocked
    """
    try:
        return q(
            "SELECT platform, reason, blocked FROM vw_posts_blocked_7d ORDER BY blocked DESC"
        )
    except Exception as e:
        logger.error(f"Erro ao obter posts bloqueados: {e}")
        return []


def posts_blocked_30d() -> list[dict[str, Any]]:
    """
    Posts bloqueados por motivo/plataforma nos últimos 30 dias

    Returns:
        Lista com platform, reason e blocked
    """
    try:
        return q(
            "SELECT platform, reason, blocked FROM vw_posts_blocked_30d ORDER BY blocked DESC"
        )
    except Exception as e:
        logger.error(f"Erro ao obter posts bloqueados (30d): {e}")
        return []


def deeplink_latency_7d() -> list[dict[str, Any]]:
    """
    Latência média por plataforma nos últimos 7 dias

    Returns:
        Lista com platform, avg_ms e samples
    """
    try:
        results = q(
            "SELECT platform, avg_ms, samples FROM vw_deeplink_latency_7d ORDER BY avg_ms DESC"
        )

        # Calcular p95 manualmente se necessário
        for result in results:
            # Buscar valores individuais para calcular p95
            platform = result["platform"]
            values = q(
                """
                SELECT value FROM perf
                WHERE component = ? AND metric = 'deeplink_latency_ms'
                AND occurred_at >= DATE('now','-7 day')
                ORDER BY value
            """,
                [platform],
            )

            if values:
                sorted_values = [v["value"] for v in values]
                p95_index = int(len(sorted_values) * 0.95)
                result["p95_ms"] = round(
                    (
                        sorted_values[p95_index]
                        if p95_index < len(sorted_values)
                        else sorted_values[-1]
                    ),
                    0,
                )
            else:
                result["p95_ms"] = result["avg_ms"]

        return results
    except Exception as e:
        logger.error(f"Erro ao obter latência deeplink: {e}")
        return []


def revenue_per_platform_7d() -> list[dict[str, Any]]:
    """
    Receita por plataforma nos últimos 7 dias

    Returns:
        Lista com platform, revenue, posts e revenue_per_post
    """
    try:
        return q(
            "SELECT platform, revenue, posts, revenue_per_post FROM vw_revenue_per_platform_7d ORDER BY revenue DESC"
        )
    except Exception as e:
        logger.error(f"Erro ao obter receita por plataforma: {e}")
        return []


def revenue_per_platform_30d() -> list[dict[str, Any]]:
    """
    Receita por plataforma nos últimos 30 dias

    Returns:
        Lista com platform, revenue, posts e revenue_per_post
    """
    try:
        return q(
            "SELECT platform, revenue, posts, revenue_per_post FROM vw_revenue_per_platform_30d ORDER BY revenue DESC"
        )
    except Exception as e:
        logger.error(f"Erro ao obter receita por plataforma (30d): {e}")
        return []


def badges_7d() -> list[dict[str, Any]]:
    """
    Uso de badges nos últimos 7 dias

    Returns:
        Lista com badge e used
    """
    try:
        results = q("SELECT badge, used FROM vw_badges_7d ORDER BY used DESC")

        # Mapear nomes dos badges para mais legibilidade
        badge_names = {
            "badge_90d_internal": "Menor Preço 90d (Interno)",
            "badge_90d_both": "Menor Preço 90d (Ambos)",
            "badge_30d_avg": "Abaixo da Média 30d",
        }

        for result in results:
            result["badge_name"] = badge_names.get(result["badge"], result["badge"])

        return results
    except Exception as e:
        logger.error(f"Erro ao obter uso de badges: {e}")
        return []


def price_freshness_7d() -> list[dict[str, Any]]:
    """
    Freshness de preços por plataforma

    Returns:
        Lista com platform, avg_age_internal_days e avg_age_external_days
    """
    try:
        results = q(
            "SELECT platform, avg_age_internal_days, avg_age_external_days "
            "FROM vw_price_freshness_7d ORDER BY avg_age_internal_days DESC"
        )

        # Adicionar alertas baseados na idade
        for result in results:
            internal_age = result["avg_age_internal_days"] or 0
            external_age = result["avg_age_external_days"] or 0

            # Alertas para freshness
            if internal_age > 3:
                result["internal_alert"] = "critical"
            elif internal_age > 1.5:
                result["internal_alert"] = "warning"
            else:
                result["internal_alert"] = "ok"

            if external_age > 7:
                result["external_alert"] = "critical"
            elif external_age > 3:
                result["external_alert"] = "warning"
            else:
                result["external_alert"] = "ok"

        return results
    except Exception as e:
        logger.error(f"Erro ao obter freshness de preços: {e}")
        return []


def source_fallback_7d() -> list[dict[str, Any]]:
    """
    Fallback por fonte nos últimos 7 dias

    Returns:
        Lista com platform, source_type e cnt
    """
    try:
        return q(
            "SELECT platform, source_type, cnt FROM vw_source_fallback_7d ORDER BY platform, cnt DESC"
        )
    except Exception as e:
        logger.error(f"Erro ao obter fallback por fonte: {e}")
        return []


def get_dashboard_summary(period: str = "7d") -> dict[str, Any]:
    """
    Resumo geral para o dashboard

    Args:
        period: Período para análise ("7d" ou "30d")

    Returns:
        Dicionário com resumo das métricas principais
    """
    try:
        if period == "30d":
            asin_quality = amazon_asin_quality_30d()
            blocked_posts = posts_blocked_30d()
            revenue_data = revenue_per_platform_30d()
        else:
            asin_quality = amazon_asin_quality_7d()
            blocked_posts = posts_blocked_7d()
            revenue_data = revenue_per_platform_7d()

        # Calcular totais
        total_blocked = sum(item["blocked"] for item in blocked_posts)
        total_revenue = sum(item["revenue"] for item in revenue_data)
        total_posts = sum(item["posts"] for item in revenue_data)

        # Estratégias ASIN (sempre 7d para ser atual)
        asin_strategies = amazon_asin_strategy_7d()
        playwright_usage = next(
            (s["cnt"] for s in asin_strategies if s["method"] == "playwright"), 0
        )
        total_asin_extractions = sum(s["cnt"] for s in asin_strategies)
        playwright_pct = (
            (playwright_usage / total_asin_extractions * 100.0)
            if total_asin_extractions > 0
            else 0.0
        )

        return {
            "period": period,
            "amazon_asin_pct": asin_quality["pct"],
            "total_blocked": total_blocked,
            "total_revenue": round(total_revenue, 2),
            "total_posts": total_posts,
            "avg_revenue_per_post": (
                round(total_revenue / total_posts, 2) if total_posts > 0 else 0
            ),
            "playwright_pct": round(playwright_pct, 2),
            "playwright_alert": playwright_pct > 10,  # Alerta se > 10%
            "asin_alert": asin_quality["pct"] < 95,  # Alerta se < 95%
            "blocked_alert": total_blocked > 0,  # Alerta se há bloqueios
        }
    except Exception as e:
        logger.error(f"Erro ao obter resumo do dashboard: {e}")
        return {
            "period": period,
            "amazon_asin_pct": 0,
            "total_blocked": 0,
            "total_revenue": 0,
            "total_posts": 0,
            "avg_revenue_per_post": 0,
            "playwright_pct": 0,
            "playwright_alert": False,
            "asin_alert": False,
            "blocked_alert": False,
        }


def get_recent_blocked_posts(limit: int = 10) -> list[dict[str, Any]]:
    """
    Últimos posts bloqueados para alertas

    Args:
        limit: Número máximo de registros

    Returns:
        Lista com detalhes dos posts bloqueados
    """
    try:
        return q(
            """
            SELECT component AS platform,
                   metric AS reason,
                   occurred_at,
                   meta_json
            FROM perf
            WHERE metric IN ('affiliate_format_invalid','amazon_asin_missing')
            ORDER BY occurred_at DESC
            LIMIT ?
        """,
            [limit],
        )
    except Exception as e:
        logger.error(f"Erro ao obter posts bloqueados recentes: {e}")
        return []


def health_check() -> dict[str, Any]:
    """
    Verificação de saúde do sistema de métricas

    Returns:
        Status das principais métricas
    """
    try:
        # Verificar se as views existem
        views_check = q(
            """
            SELECT name FROM sqlite_master
            WHERE type='view' AND name LIKE 'vw_%'
        """
        )

        # Verificar dados recentes
        recent_data = q(
            """
            SELECT COUNT(*) as count FROM perf
            WHERE occurred_at >= DATE('now','-1 day')
        """
        )

        return {
            "views_count": len(views_check),
            "expected_views": 11,  # Número de views que criamos
            "views_ok": len(views_check) >= 11,
            "recent_events": recent_data[0]["count"] if recent_data else 0,
            "data_fresh": (recent_data[0]["count"] if recent_data else 0) > 0,
            "status": "healthy" if len(views_check) >= 11 else "degraded",
        }
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return {
            "views_count": 0,
            "expected_views": 11,
            "views_ok": False,
            "recent_events": 0,
            "data_fresh": False,
            "status": "error",
        }
