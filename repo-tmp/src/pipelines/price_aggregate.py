"""
Pipeline de agregação diária de preços.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from src.utils.sqlite_helpers import execute

logger = logging.getLogger(__name__)


class PriceAggregationPipeline:
    """Pipeline para agregação diária de preços"""

    def __init__(self):
        pass

    async def run(self, days_back: int = 7) -> Dict[str, int]:
        """
        Executa agregação de preços dos últimos N dias

        Args:
            days_back: Número de dias para processar

        Returns:
            Estatísticas da execução
        """
        logger.info(f"📊 Iniciando agregação de preços ({days_back} dias)")

        stats = {
            "native_days_processed": 0,
            "external_days_processed": 0,
            "native_records_created": 0,
            "external_records_created": 0,
            "errors": 0,
        }

        try:
            # Processar agregações nativas
            for days_ago in range(days_back):
                target_date = datetime.now().date() - timedelta(days=days_ago)

                try:
                    native_count = await self._aggregate_native_prices(target_date)
                    external_count = await self._aggregate_external_prices(target_date)

                    if native_count > 0:
                        stats["native_days_processed"] += 1
                        stats["native_records_created"] += native_count

                    if external_count > 0:
                        stats["external_days_processed"] += 1
                        stats["external_records_created"] += external_count

                except Exception as e:
                    logger.error(f"Erro ao agregar data {target_date}: {e}")
                    stats["errors"] += 1

            logger.info(f"✅ Agregação concluída: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Erro no pipeline de agregação: {e}")
            stats["errors"] += 1
            return stats

    async def _aggregate_native_prices(self, target_date) -> int:
        """Agrega preços nativos para uma data específica"""
        try:
            # Query para agregação de preços nativos (incluindo ASIN quando disponível)
            aggregate_query = """
            INSERT OR REPLACE INTO price_daily (
                product_id, date, min_price, max_price, avg_price,
                price_count, first_seen_price, last_seen_price
            )
            SELECT
                ph.product_id,
                DATE(ph.collected_at) as date,
                MIN(ph.price) as min_price,
                MAX(ph.price) as max_price,
                AVG(ph.price) as avg_price,
                COUNT(*) as price_count,
                (SELECT ph2.price FROM price_history ph2
                 WHERE ph2.product_id = ph.product_id
                 AND DATE(ph2.collected_at) = DATE(ph.collected_at)
                 ORDER BY ph2.collected_at ASC LIMIT 1) as first_seen_price,
                (SELECT ph3.price FROM price_history ph3
                 WHERE ph3.product_id = ph.product_id
                 AND DATE(ph3.collected_at) = DATE(ph.collected_at)
                 ORDER BY ph3.collected_at DESC LIMIT 1) as last_seen_price
            FROM price_history ph
            JOIN products p ON ph.product_id = p.id
            WHERE DATE(ph.collected_at) = ?
            GROUP BY ph.product_id, DATE(ph.collected_at)
            """

            # Executar agregação usando o caminho do banco
            result = execute("analytics", aggregate_query, (target_date,))
            count = len(result) if result else 0

            logger.debug(f"📊 Agregados {count} registros nativos para {target_date}")
            return count

        except Exception as e:
            logger.error(f"Erro na agregação nativa para {target_date}: {e}")
            return 0

    async def _aggregate_external_prices(self, target_date) -> int:
        """Agrega preços externos para uma data específica"""
        try:
            # Query para agregação de preços externos
            aggregate_query = """
            INSERT OR REPLACE INTO external_price_daily (
                internal_product_id, external_source, date,
                min_price, max_price, avg_price, price_count
            )
            SELECT
                internal_product_id,
                external_source,
                DATE(collected_at) as date,
                MIN(price) as min_price,
                MAX(price) as max_price,
                AVG(price) as avg_price,
                COUNT(*) as price_count
            FROM external_price_history
            WHERE DATE(collected_at) = ?
            GROUP BY internal_product_id, external_source, DATE(collected_at)
            """

            # Executar agregação usando o caminho do banco
            result = execute("analytics", aggregate_query, (target_date,))
            count = len(result) if result else 0

            logger.debug(f"📊 Agregados {count} registros externos para {target_date}")
            return count

        except Exception as e:
            logger.error(f"Erro na agregação externa para {target_date}: {e}")
            return 0

    def get_aggregation_stats(self, days: int = 30) -> Dict[str, Any]:
        """Retorna estatísticas de agregação dos últimos N dias"""
        try:
            stats_query = f"""
            SELECT
                'native' as type,
                COUNT(*) as total_records,
                COUNT(DISTINCT product_id) as unique_products,
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                AVG(avg_price) as overall_avg_price
            FROM price_daily
            WHERE date >= date('now', '-{days} days')

            UNION ALL

            SELECT
                'external' as type,
                COUNT(*) as total_records,
                COUNT(DISTINCT internal_product_id) as unique_products,
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                AVG(avg_price) as overall_avg_price
            FROM external_price_daily
            WHERE date >= date('now', '-{days} days')
            """

            # Executar query de estatísticas usando o caminho do banco
            results = execute("analytics", stats_query)

            stats = {}
            for row in results:
                stats[row["type"]] = {
                    "total_records": row["total_records"],
                    "unique_products": row["unique_products"],
                    "earliest_date": row["earliest_date"],
                    "latest_date": row["latest_date"],
                    "overall_avg_price": row["overall_avg_price"],
                }

            return stats

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {"error": str(e)}


async def main():
    """Execução principal do pipeline"""
    logging.basicConfig(level=logging.INFO)

    pipeline = PriceAggregationPipeline()

    # Executar agregação
    stats = await pipeline.run(days_back=7)

    print("📊 Estatísticas da agregação:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Mostrar estatísticas gerais
    print("\n📈 Estatísticas gerais (últimos 30 dias):")
    general_stats = pipeline.get_aggregation_stats(30)

    if "error" in general_stats:
        print(f"   ❌ Erro: {general_stats['error']}")
    else:
        for data_type, data in general_stats.items():
            print(f"   {data_type.upper()}:")
            for key, value in data.items():
                print(f"     {key}: {value}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
