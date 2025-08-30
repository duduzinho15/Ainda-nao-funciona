"""
Pipeline de coleta de preços nativos
Coleta preços dos scrapers de lojas ativas e armazena no banco
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.core.models import Offer
from src.utils.sqlite_helpers import get_one, insert_one, upsert

logger = logging.getLogger(__name__)


class PriceCollectionPipeline:
    """Pipeline para coleta de preços nativos"""

    def __init__(self, analytics_db_path: str = "src/db/analytics.sqlite"):
        self.analytics_db_path = Path(analytics_db_path)
        self.logger = logging.getLogger(f"{__name__}.PriceCollectionPipeline")

        # Configurações
        self.batch_size = 50
        self.max_retries = 3

        self.logger.info("PriceCollectionPipeline inicializado")

    async def process_offers(
        self, offers: List[Offer], source: str = "scraper_loja"
    ) -> Dict:
        """
        Processa ofertas e coleta preços

        Args:
            offers: Lista de ofertas dos scrapers
            source: Fonte dos dados (scraper_loja, comunidade, etc.)

        Returns:
            Dicionário com estatísticas do processamento
        """
        if not offers:
            self.logger.warning("Nenhuma oferta para processar")
            return {
                "processed": 0,
                "products_created": 0,
                "prices_collected": 0,
                "errors": 0,
            }

        self.logger.info(f"Iniciando processamento de {len(offers)} ofertas")

        stats = {
            "processed": 0,
            "products_created": 0,
            "prices_collected": 0,
            "errors": 0,
        }

        # Processar ofertas em lotes
        for i in range(0, len(offers), self.batch_size):
            batch = offers[i : i + self.batch_size]
            batch_stats = await self._process_batch(batch, source)

            # Acumular estatísticas
            for key in stats:
                stats[key] += batch_stats[key]

            # Log de progresso
            processed = min(i + self.batch_size, len(offers))
            self.logger.info(
                f"Progresso: {processed}/{len(offers)} ofertas processadas"
            )

        self.logger.info(f"Processamento concluído: {stats}")
        return stats

    async def _process_batch(self, offers: List[Offer], source: str) -> Dict:
        """Processa um lote de ofertas"""
        batch_stats = {
            "processed": 0,
            "products_created": 0,
            "prices_collected": 0,
            "errors": 0,
        }

        for offer in offers:
            try:
                # Processar oferta individual
                result = await self._process_single_offer(offer, source)

                if result["success"]:
                    batch_stats["products_created"] += result["product_created"]
                    batch_stats["prices_collected"] += result["price_collected"]
                else:
                    batch_stats["errors"] += 1

                batch_stats["processed"] += 1

            except Exception as e:
                self.logger.error(f"Erro ao processar oferta: {e}")
                batch_stats["errors"] += 1
                continue

        return batch_stats

    async def _process_single_offer(self, offer: Offer, source: str) -> Dict:
        """Processa uma oferta individual"""
        try:
            # 1. Upsert produto
            product_id = await self._upsert_product(offer)
            product_created = product_id > 0

            # 2. Inserir ponto de preço
            price_id = await self._insert_price_point(offer, product_id, source)
            price_collected = price_id > 0

            # 3. Registrar métricas de performance
            await self._record_performance_metrics("price_collect", "success", 1)

            return {
                "success": True,
                "product_created": 1 if product_created else 0,
                "price_collected": 1 if price_collected else 0,
                "product_id": product_id,
                "price_id": price_id,
            }

        except Exception as e:
            self.logger.error(f"Erro ao processar oferta {offer.title}: {e}")
            await self._record_performance_metrics("price_collect", "error", 1)

            return {
                "success": False,
                "product_created": 0,
                "price_collected": 0,
                "error": str(e),
            }

    async def _upsert_product(self, offer: Offer) -> int:
        """Insere ou atualiza produto no banco"""
        try:
            # Determinar plataforma baseado na URL
            platform = self._extract_platform_from_url(offer.url)
            store = self._extract_store_from_url(offer.url)

            # Dados do produto
            product_data = {
                "platform": platform,
                "store": store,
                "canonical_url": offer.url,
                "sku": getattr(offer, "sku", None),
                "title": offer.title,
                "last_seen_at": datetime.now().isoformat(),
            }

            # Chaves para identificação única
            keys = {"platform": platform, "canonical_url": offer.url}

            # Valores para inserir/atualizar
            values = {
                "store": store,
                "sku": getattr(offer, "sku", None),
                "title": offer.title,
                "last_seen_at": datetime.now().isoformat(),
            }

            # Upsert
            product_id = upsert(self.analytics_db_path, "products", keys, values)

            if product_id:
                self.logger.debug(f"Produto upsert: {product_id}")
            else:
                # Se não retornou ID, buscar pelo produto existente
                existing = get_one(self.analytics_db_path, "products", keys)
                if existing:
                    product_id = existing["id"]
                else:
                    # Inserir novo produto
                    product_id = insert_one(
                        self.analytics_db_path, "products", product_data
                    )

            return product_id

        except Exception as e:
            self.logger.error(f"Erro no upsert do produto: {e}")
            raise

    async def _insert_price_point(
        self, offer: Offer, product_id: int, source: str
    ) -> int:
        """Insere ponto de preço no banco"""
        try:
            # Converter preço para centavos
            price_cents = int(float(offer.price) * 100)
            price_before_cents = (
                int(float(offer.original_price) * 100) if offer.original_price else None
            )

            # Dados do ponto de preço
            price_data = {
                "product_id": product_id,
                "collected_at": datetime.now().isoformat(),
                "price_cents": price_cents,
                "price_before_cents": price_before_cents,
                "in_stock": 1 if offer.available else 0,
                "source": source,
                "extra_json": json.dumps(
                    {
                        "discount_percentage": getattr(
                            offer, "discount_percentage", None
                        ),
                        "image_url": getattr(offer, "image_url", None),
                        "affiliate_url": getattr(offer, "affiliate_url", None),
                    }
                ),
            }

            # Inserir ponto de preço
            price_id = insert_one(self.analytics_db_path, "price_history", price_data)

            if price_id:
                self.logger.debug(f"Ponto de preço inserido: {price_id}")

            return price_id

        except Exception as e:
            self.logger.error(f"Erro ao inserir ponto de preço: {e}")
            raise

    def _extract_platform_from_url(self, url: str) -> str:
        """Extrai plataforma da URL"""
        if not url:
            return "unknown"

        url_lower = url.lower()

        if "kabum.com.br" in url_lower:
            return "kabum"
        elif "amazon.com.br" in url_lower:
            return "amazon"
        elif "shopee.com.br" in url_lower:
            return "shopee"
        elif "aliexpress.com" in url_lower:
            return "aliexpress"
        elif "mercadolivre.com.br" in url_lower:
            return "mercadolivre"
        elif "magazineluiza.com.br" in url_lower:
            return "magalu"
        elif "comfy.com.br" in url_lower:
            return "comfy"
        elif "trocafy.com.br" in url_lower:
            return "trocafy"
        elif "lg.com" in url_lower:
            return "lg"
        elif "ninja.com.br" in url_lower:
            return "ninja"
        elif "samsung.com.br" in url_lower:
            return "samsung"
        else:
            return "other"

    def _extract_store_from_url(self, url: str) -> Optional[str]:
        """Extrai nome da loja da URL"""
        if not url:
            return None

        url_lower = url.lower()

        # Mapear URLs para nomes de lojas
        store_mapping = {
            "kabum.com.br": "KaBuM!",
            "amazon.com.br": "Amazon",
            "shopee.com.br": "Shopee",
            "aliexpress.com": "AliExpress",
            "mercadolivre.com.br": "Mercado Livre",
            "magazineluiza.com.br": "Magazine Luiza",
            "comfy.com.br": "Comfy",
            "trocafy.com.br": "Trocafy",
            "lg.com": "LG",
            "ninja.com.br": "Ninja",
            "samsung.com.br": "Samsung",
        }

        for domain, store_name in store_mapping.items():
            if domain in url_lower:
                return store_name

        return None

    async def _record_performance_metrics(
        self, component: str, metric: str, value: float
    ):
        """Registra métricas de performance"""
        try:
            perf_data = {
                "component": component,
                "metric": metric,
                "value": value,
                "occurred_at": datetime.now().isoformat(),
            }

            insert_one(self.analytics_db_path, "perf", perf_data)

        except Exception as e:
            self.logger.warning(f"Erro ao registrar métrica: {e}")

    async def get_recent_products(self, days: int = 7) -> List[Dict]:
        """
        Obtém produtos vistos recentemente

        Args:
            days: Número de dias para trás

        Returns:
            Lista de produtos
        """
        try:
            # Query para produtos vistos nos últimos N dias
            query = f"""
                SELECT DISTINCT p.*
                FROM products p
                WHERE p.last_seen_at >= datetime('now', '-{days} days')
                ORDER BY p.last_seen_at DESC
            """

            from utils.sqlite_helpers import execute

            products = execute(self.analytics_db_path, query)

            return products

        except Exception as e:
            self.logger.error(f"Erro ao buscar produtos recentes: {e}")
            return []

    async def get_price_history(self, product_id: int, days: int = 30) -> List[Dict]:
        """
        Obtém histórico de preços de um produto

        Args:
            product_id: ID do produto
            days: Número de dias para trás

        Returns:
            Lista de pontos de preço
        """
        try:
            from utils.sqlite_helpers import execute

            query = f"""
                SELECT * FROM price_history
                WHERE product_id = ?
                AND collected_at >= datetime('now', '-{days} days')
                ORDER BY collected_at DESC
            """

            history = execute(self.analytics_db_path, query, (product_id,))

            return history

        except Exception as e:
            self.logger.error(f"Erro ao buscar histórico de preços: {e}")
            return []


# Função de conveniência para uso direto
async def collect_prices_from_offers(
    offers: List[Offer], source: str = "scraper_loja"
) -> Dict:
    """Coleta preços de uma lista de ofertas"""
    pipeline = PriceCollectionPipeline()
    return await pipeline.process_offers(offers, source)


async def get_recent_products_for_enrichment(days: int = 7) -> List[Dict]:
    """Obtém produtos recentes para enriquecimento"""
    pipeline = PriceCollectionPipeline()
    return await pipeline.get_recent_products(days)
