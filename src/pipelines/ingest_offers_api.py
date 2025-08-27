"""
Pipeline de ingestão de ofertas via APIs oficiais
Coleta ofertas de AliExpress, Rakuten, Shopee e Awin via APIs
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.affiliate.aliexpress_api_client import get_aliexpress_client
from src.affiliate.awin_api import get_awin_client
from src.affiliate.rakuten_api import get_rakuten_client
from src.affiliate.shopee_api import get_shopee_client

logger = logging.getLogger(__name__)


@dataclass
class APIOffer:
    """Estrutura de oferta coletada via API"""

    id: str
    title: str
    price: float
    original_price: Optional[float]
    discount: Optional[float]
    image_url: Optional[str]
    product_url: str
    affiliate_url: Optional[str]
    store: Optional[str]
    category: Optional[str]
    source: str  # API_ALIEXPRESS, API_RAKUTEN, API_SHOPEE, API_AWIN
    collected_at: datetime
    metadata: Dict[str, Any]


class APIOfferIngestionPipeline:
    """Pipeline para ingestão de ofertas via APIs oficiais"""

    def __init__(self):
        """Inicializa o pipeline de ingestão"""
        self.clients = {}
        self.ingestion_stats = {
            "total_offers": 0,
            "offers_by_source": {},
            "errors_by_source": {},
            "last_run": None,
        }

        # Inicializar clientes das APIs
        self._init_api_clients()

    def _init_api_clients(self):
        """Inicializa clientes das APIs disponíveis"""
        try:
            # AliExpress
            aliexpress_client = get_aliexpress_client()
            if aliexpress_client:
                self.clients["aliexpress"] = aliexpress_client
                logger.info("Cliente AliExpress API inicializado")

            # Rakuten
            rakuten_client = get_rakuten_client()
            if rakuten_client:
                self.clients["rakuten"] = rakuten_client
                logger.info("Cliente Rakuten API inicializado")

            # Shopee
            shopee_client = get_shopee_client()
            if shopee_client:
                self.clients["shopee"] = shopee_client
                logger.info("Cliente Shopee API inicializado")

            # Awin
            awin_client = get_awin_client()
            if awin_client:
                self.clients["awin"] = awin_client
                logger.info("Cliente Awin API inicializado")

            logger.info(f"Total de {len(self.clients)} clientes de API inicializados")

        except Exception as e:
            logger.error(f"Erro ao inicializar clientes de API: {e}")

    async def ingest_aliexpress_offers(
        self, queries: List[str], limit_per_query: int = 20
    ) -> List[APIOffer]:
        """
        Ingesta ofertas do AliExpress via API

        Args:
            queries: Lista de termos de busca
            limit_per_query: Limite de resultados por query

        Returns:
            Lista de ofertas coletadas
        """
        offers = []

        if "aliexpress" not in self.clients:
            logger.warning("Cliente AliExpress não disponível")
            return offers

        try:
            client = self.clients["aliexpress"]

            for query in queries:
                try:
                    # Buscar produtos
                    products = await client.search_products(
                        query=query,
                        limit=limit_per_query,
                        ship_to_country="BR",
                        currency="BRL",
                        language="pt",
                    )

                    # Converter para APIOffer
                    for product in products:
                        try:
                            # Gerar link de afiliado
                            affiliate_url = await client.generate_affiliate_link(
                                url=product.get("product_url", ""),
                                tracking_id="telegram",
                            )

                            offer = APIOffer(
                                id=product.get("product_id", ""),
                                title=product.get("title", ""),
                                price=float(product.get("price", 0)),
                                original_price=(
                                    float(product.get("original_price", 0))
                                    if product.get("original_price")
                                    else None
                                ),
                                discount=(
                                    float(product.get("discount", 0))
                                    if product.get("discount")
                                    else None
                                ),
                                image_url=product.get("image_url"),
                                product_url=product.get("product_url", ""),
                                affiliate_url=affiliate_url,
                                store=product.get("store_name"),
                                category=product.get("category"),
                                source="API_ALIEXPRESS",
                                collected_at=datetime.now(),
                                metadata={
                                    "query": query,
                                    "ship_to_country": "BR",
                                    "currency": "BRL",
                                },
                            )

                            offers.append(offer)

                        except Exception as e:
                            logger.error(f"Erro ao processar produto AliExpress: {e}")
                            continue

                    logger.info(f"Query '{query}' retornou {len(products)} produtos")

                except Exception as e:
                    logger.error(f"Erro na busca AliExpress para '{query}': {e}")
                    continue

            # Atualizar estatísticas
            self.ingestion_stats["offers_by_source"]["API_ALIEXPRESS"] = len(offers)
            self.ingestion_stats["total_offers"] += len(offers)

        except Exception as e:
            logger.error(f"Erro na ingestão AliExpress: {e}")
            self.ingestion_stats["errors_by_source"]["API_ALIEXPRESS"] = str(e)

        return offers

    async def ingest_rakuten_offers(
        self, queries: List[str], limit_per_query: int = 20
    ) -> List[APIOffer]:
        """
        Ingesta ofertas do Rakuten via API

        Args:
            queries: Lista de termos de busca
            limit_per_query: Limite de resultados por query

        Returns:
            Lista de ofertas coletadas
        """
        offers = []

        if "rakuten" not in self.clients:
            logger.warning("Cliente Rakuten não disponível")
            return offers

        try:
            client = self.clients["rakuten"]

            # Obter anunciantes que permitem deep links
            await client.list_advertisers(deep_links=True)

            for query in queries:
                try:
                    # Buscar produtos
                    products = await client.search_products(
                        query=query, limit=limit_per_query
                    )

                    # Converter para APIOffer
                    for product in products:
                        try:
                            # Gerar deep link
                            affiliate_url = await client.build_deeplink(
                                advertiser_id=product.get("advertiser_id", ""),
                                url=product.get("product_url", ""),
                                sub_id="telegram",
                            )

                            offer = APIOffer(
                                id=product.get("product_id", ""),
                                title=product.get("title", ""),
                                price=float(product.get("price", 0)),
                                original_price=(
                                    float(product.get("original_price", 0))
                                    if product.get("original_price")
                                    else None
                                ),
                                discount=(
                                    float(product.get("discount", 0))
                                    if product.get("discount")
                                    else None
                                ),
                                image_url=product.get("image_url"),
                                product_url=product.get("product_url", ""),
                                affiliate_url=affiliate_url,
                                store=product.get("store_name"),
                                category=product.get("category"),
                                source="API_RAKUTEN",
                                collected_at=datetime.now(),
                                metadata={
                                    "query": query,
                                    "advertiser_id": product.get("advertiser_id"),
                                    "deep_link_enabled": True,
                                },
                            )

                            offers.append(offer)

                        except Exception as e:
                            logger.error(f"Erro ao processar produto Rakuten: {e}")
                            continue

                    logger.info(f"Query '{query}' retornou {len(products)} produtos")

                except Exception as e:
                    logger.error(f"Erro na busca Rakuten para '{query}': {e}")
                    continue

            # Atualizar estatísticas
            self.ingestion_stats["offers_by_source"]["API_RAKUTEN"] = len(offers)
            self.ingestion_stats["total_offers"] += len(offers)

        except Exception as e:
            logger.error(f"Erro na ingestão Rakuten: {e}")
            self.ingestion_stats["errors_by_source"]["API_RAKUTEN"] = str(e)

        return offers

    async def ingest_shopee_offers(
        self, queries: List[str], limit_per_query: int = 20
    ) -> List[APIOffer]:
        """
        Ingesta ofertas do Shopee via API

        Args:
            queries: Lista de termos de busca
            limit_per_query: Limite de resultados por query

        Returns:
            Lista de ofertas coletadas
        """
        offers = []

        if "shopee" not in self.clients:
            logger.warning("Cliente Shopee não disponível")
            return offers

        try:
            client = self.clients["shopee"]

            for query in queries:
                try:
                    # Buscar ofertas
                    shopee_offers = await client.get_offers(
                        offer_type="product",
                        filters={"keyword": query},
                        limit=limit_per_query,
                    )

                    # Converter para APIOffer
                    for shopee_offer in shopee_offers:
                        try:
                            # Criar shortlink
                            affiliate_url = await client.create_shortlink(
                                url=shopee_offer.get("productUrl", ""),
                                sub_id="telegram",
                            )

                            offer = APIOffer(
                                id=shopee_offer.get("id", ""),
                                title=shopee_offer.get("title", ""),
                                price=float(shopee_offer.get("price", 0)),
                                original_price=(
                                    float(shopee_offer.get("originalPrice", 0))
                                    if shopee_offer.get("originalPrice")
                                    else None
                                ),
                                discount=(
                                    float(shopee_offer.get("discount", 0))
                                    if shopee_offer.get("discount")
                                    else None
                                ),
                                image_url=shopee_offer.get("imageUrl"),
                                product_url=shopee_offer.get("productUrl", ""),
                                affiliate_url=affiliate_url,
                                store=(
                                    shopee_offer.get("store", {}).get("name")
                                    if shopee_offer.get("store")
                                    else None
                                ),
                                category=shopee_offer.get("category"),
                                source="API_SHOPEE",
                                collected_at=datetime.now(),
                                metadata={
                                    "query": query,
                                    "store_rating": (
                                        shopee_offer.get("store", {}).get("rating")
                                        if shopee_offer.get("store")
                                        else None
                                    ),
                                    "tags": shopee_offer.get("tags", []),
                                },
                            )

                            offers.append(offer)

                        except Exception as e:
                            logger.error(f"Erro ao processar oferta Shopee: {e}")
                            continue

                    logger.info(
                        f"Query '{query}' retornou {len(shopee_offers)} ofertas"
                    )

                except Exception as e:
                    logger.error(f"Erro na busca Shopee para '{query}': {e}")
                    continue

            # Atualizar estatísticas
            self.ingestion_stats["offers_by_source"]["API_SHOPEE"] = len(offers)
            self.ingestion_stats["total_offers"] += len(offers)

        except Exception as e:
            logger.error(f"Erro na ingestão Shopee: {e}")
            self.ingestion_stats["errors_by_source"]["API_SHOPEE"] = str(e)

        return offers

    async def ingest_awin_offers(
        self, advertiser_ids: List[str], limit_per_advertiser: int = 20
    ) -> List[APIOffer]:
        """
        Ingesta ofertas do Awin via API

        Args:
            advertiser_ids: Lista de IDs de anunciantes
            limit_per_advertiser: Limite de produtos por anunciante

        Returns:
            Lista de ofertas coletadas
        """
        offers = []

        if "awin" not in self.clients:
            logger.warning("Cliente Awin não disponível")
            return offers

        try:
            client = self.clients["awin"]

            for advertiser_id in advertiser_ids:
                try:
                    # Obter feed de produtos
                    products = await client.get_product_feed(
                        advertiser_id=advertiser_id, feed_type="product"
                    )

                    # Limitar número de produtos
                    products = products[:limit_per_advertiser]

                    # Converter para APIOffer
                    for product in products:
                        try:
                            # Gerar link de afiliado
                            affiliate_url = await client.generate_link(
                                advertiser_id=advertiser_id,
                                url=product.get("url", ""),
                                sub_id="telegram",
                            )

                            offer = APIOffer(
                                id=product.get("id", ""),
                                title=product.get("title", ""),
                                price=float(product.get("price", 0)),
                                original_price=(
                                    float(product.get("original_price", 0))
                                    if product.get("original_price")
                                    else None
                                ),
                                discount=(
                                    float(product.get("discount", 0))
                                    if product.get("discount")
                                    else None
                                ),
                                image_url=product.get("image_url"),
                                product_url=product.get("url", ""),
                                affiliate_url=affiliate_url,
                                store=product.get("store_name"),
                                category=product.get("category"),
                                source="API_AWIN",
                                collected_at=datetime.now(),
                                metadata={
                                    "advertiser_id": advertiser_id,
                                    "feed_type": "product",
                                    "product_id": product.get("product_id"),
                                },
                            )

                            offers.append(offer)

                        except Exception as e:
                            logger.error(f"Erro ao processar produto Awin: {e}")
                            continue

                    logger.info(
                        f"Anunciante {advertiser_id} retornou {len(products)} produtos"
                    )

                except Exception as e:
                    logger.error(
                        f"Erro no feed Awin para anunciante {advertiser_id}: {e}"
                    )
                    continue

            # Atualizar estatísticas
            self.ingestion_stats["offers_by_source"]["API_AWIN"] = len(offers)
            self.ingestion_stats["total_offers"] += len(offers)

        except Exception as e:
            logger.error(f"Erro na ingestão Awin: {e}")
            self.ingestion_stats["errors_by_source"]["API_AWIN"] = str(e)

        return offers

    async def run_full_ingestion(
        self, queries: List[str] = None, advertiser_ids: List[str] = None
    ) -> List[APIOffer]:
        """
        Executa ingestão completa de todas as APIs disponíveis

        Args:
            queries: Lista de termos de busca (para AliExpress, Rakuten, Shopee)
            advertiser_ids: Lista de IDs de anunciantes (para Awin)

        Returns:
            Lista completa de ofertas coletadas
        """
        if queries is None:
            queries = ["smartphone", "notebook", "headphone", "smartwatch"]

        if advertiser_ids is None:
            advertiser_ids = ["17729", "23377", "33061"]  # KaBuM, Comfy, LG

        logger.info("Iniciando ingestão completa via APIs")
        start_time = datetime.now()

        all_offers = []

        # Executar ingestões em paralelo
        tasks = []

        # AliExpress
        if "aliexpress" in self.clients:
            tasks.append(self.ingest_aliexpress_offers(queries))

        # Rakuten
        if "rakuten" in self.clients:
            tasks.append(self.ingest_rakuten_offers(queries))

        # Shopee
        if "shopee" in self.clients:
            tasks.append(self.ingest_shopee_offers(queries))

        # Awin
        if "awin" in self.clients:
            tasks.append(self.ingest_awin_offers(advertiser_ids))

        # Executar todas as tarefas
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Erro na tarefa {i}: {result}")
                elif isinstance(result, list):
                    all_offers.extend(result)

        # Atualizar estatísticas finais
        self.ingestion_stats["last_run"] = start_time
        duration = datetime.now() - start_time

        logger.info(f"Ingestão completa concluída em {duration.total_seconds():.2f}s")
        logger.info(f"Total de ofertas coletadas: {len(all_offers)}")
        logger.info(f"Ofertas por fonte: {self.ingestion_stats['offers_by_source']}")

        if self.ingestion_stats["errors_by_source"]:
            logger.warning(
                f"Erros encontrados: {self.ingestion_stats['errors_by_source']}"
            )

        return all_offers

    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da ingestão"""
        return self.ingestion_stats.copy()

    def get_available_sources(self) -> List[str]:
        """Retorna lista de fontes de API disponíveis"""
        return list(self.clients.keys())

    def is_source_available(self, source: str) -> bool:
        """Verifica se uma fonte de API está disponível"""
        return source in self.clients


# Função de conveniência
async def run_api_ingestion(
    queries: List[str] = None, advertiser_ids: List[str] = None
) -> List[APIOffer]:
    """
    Executa ingestão via APIs de forma simplificada

    Args:
        queries: Lista de termos de busca
        advertiser_ids: Lista de IDs de anunciantes

    Returns:
        Lista de ofertas coletadas
    """
    pipeline = APIOfferIngestionPipeline()
    return await pipeline.run_full_ingestion(queries, advertiser_ids)
