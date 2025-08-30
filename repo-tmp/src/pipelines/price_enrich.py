"""
Pipeline de enriquecimento externo de preços.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List

from src.core.matchers import ProductMatcher
from src.scrapers.precos.buscape import BuscapeScraper
from src.scrapers.precos.zoom import ZoomScraper
from src.utils.sqlite_helpers import execute, get_conn, get_many

logger = logging.getLogger(__name__)


class PriceEnrichmentPipeline:
    """Pipeline para enriquecimento de preços externos"""

    def __init__(self):
        self.matcher = ProductMatcher()
        self.zoom_scraper = ZoomScraper()
        self.buscape_scraper = BuscapeScraper()

    async def run(self, limit: int = 100) -> Dict[str, int]:
        """
        Executa o pipeline de enriquecimento

        Args:
            limit: Número máximo de produtos para processar

        Returns:
            Estatísticas da execução
        """
        logger.info(f"🔍 Iniciando enriquecimento de preços (limite: {limit})")

        stats = {
            "products_processed": 0,
            "zoom_matches": 0,
            "buscape_matches": 0,
            "external_prices_added": 0,
            "errors": 0,
        }

        try:
            # Buscar produtos para enriquecer
            products = await self._get_products_to_enrich(limit)
            logger.info(f"📦 {len(products)} produtos encontrados para enriquecimento")

            # Processar cada produto
            for product in products:
                try:
                    await self._enrich_product(product, stats)
                    stats["products_processed"] += 1

                    # Pequeno delay para evitar sobrecarga
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Erro ao enriquecer produto {product['id']}: {e}")
                    stats["errors"] += 1
                    continue

            logger.info(f"✅ Enriquecimento concluído: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Erro no pipeline de enriquecimento: {e}")
            stats["errors"] += 1
            return stats

    async def _get_products_to_enrich(self, limit: int) -> List[Dict]:
        """Busca produtos que precisam de enriquecimento"""
        query = """
        SELECT DISTINCT p.id, p.title, p.platform, p.store, p.canonical_url
        FROM products p
        WHERE p.last_seen_at >= datetime('now', '-7 days')
        AND NOT EXISTS (
            SELECT 1 FROM external_product_map epm
            WHERE epm.internal_product_id = p.id
            AND epm.updated_at >= datetime('now', '-1 day')
        )
        ORDER BY p.last_seen_at DESC
        LIMIT ?
        """

        with get_conn("analytics") as conn:
            return get_many(conn, query, (limit,))

    async def _enrich_product(self, product: Dict, stats: Dict[str, int]):
        """Enriquece um produto específico"""
        product_id = product["id"]
        title = product["title"]

        logger.debug(f"🔍 Enriquecendo produto: {title}")

        # Buscar no Zoom
        zoom_results = await self._search_zoom(title)
        if zoom_results:
            best_match = self.matcher.choose_best_match(title, zoom_results)
            if best_match:
                await self._save_external_match(product_id, best_match, "zoom")
                stats["zoom_matches"] += 1
                stats["external_prices_added"] += 1

        # Buscar no Buscapé
        buscape_results = await self._search_buscape(title)
        if buscape_results:
            best_match = self.matcher.choose_best_match(title, buscape_results)
            if best_match:
                await self._save_external_match(product_id, best_match, "buscape")
                stats["buscape_matches"] += 1
                stats["external_prices_added"] += 1

    async def _search_zoom(self, title: str) -> List[Dict]:
        """Busca produto no Zoom"""
        try:
            results = await self.zoom_scraper.search_products(title, max_results=3)
            return [
                {
                    "title": result.get("title", ""),
                    "price": result.get("price", 0),
                    "url": result.get("url", ""),
                    "source": "zoom",
                }
                for result in results
            ]
        except Exception as e:
            logger.debug(f"Erro na busca Zoom: {e}")
            return []

    async def _search_buscape(self, title: str) -> List[Dict]:
        """Busca produto no Buscapé"""
        try:
            results = await self.buscape_scraper.search_products(title, max_results=3)
            return [
                {
                    "title": result.get("title", ""),
                    "price": result.get("price", 0),
                    "url": result.get("url", ""),
                    "source": "buscape",
                }
                for result in results
            ]
        except Exception as e:
            logger.debug(f"Erro na busca Buscapé: {e}")
            return []

    async def _save_external_match(self, product_id: int, match: Dict, source: str):
        """Salva match externo no banco"""
        try:
            # Salvar mapeamento
            mapping_query = """
            INSERT OR REPLACE INTO external_product_map (
                internal_product_id, external_source, external_title,
                external_url, match_type, match_confidence, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            # Salvar preço externo
            price_query = """
            INSERT INTO external_price_history (
                internal_product_id, external_source, price,
                external_url, collected_at
            ) VALUES (?, ?, ?, ?, ?)
            """

            now = datetime.now()

            with get_conn("analytics") as conn:
                # Salvar mapeamento
                execute(
                    conn,
                    mapping_query,
                    (
                        product_id,
                        source,
                        match.get("title", ""),
                        match.get("url", ""),
                        match.get("match_type", "title"),
                        match.get("confidence", 0.5),
                        now,
                    ),
                )

                # Salvar preço
                execute(
                    conn,
                    price_query,
                    (
                        product_id,
                        source,
                        float(match.get("price", 0)),
                        match.get("url", ""),
                        now,
                    ),
                )

                logger.debug(
                    f"💾 Match salvo: {source} -> {match.get('title', '')[:50]}"
                )

        except Exception as e:
            logger.error(f"Erro ao salvar match externo: {e}")


async def main():
    """Execução principal do pipeline"""
    logging.basicConfig(level=logging.INFO)

    pipeline = PriceEnrichmentPipeline()
    stats = await pipeline.run(limit=50)

    print("📊 Estatísticas do enriquecimento:")
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
