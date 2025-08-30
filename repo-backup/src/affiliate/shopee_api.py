"""
Cliente API oficial do Shopee Affiliate Open API
Implementa GraphQL com assinatura SHA256 para geração de shortlinks e ofertas
"""

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional

from src.affiliate.base_api import BaseAPI

logger = logging.getLogger(__name__)


class ShopeeAPIClient(BaseAPI):
    """Cliente para API oficial do Shopee Affiliate Open API"""

    def __init__(self, app_id: str, secret: str, access_token: str = None):
        """
        Inicializa cliente Shopee API

        Args:
            app_id: App ID do Open API
            secret: Secret do Open API
            access_token: Token de acesso (opcional)
        """
        super().__init__("Shopee", "https://open-api.affiliate.shopee.com.br", app_id)
        self.app_id = app_id
        self.secret = secret
        self.access_token = access_token

        # Configurações específicas
        self.api_version = "v1"
        self.base_url = "https://open-api.affiliate.shopee.com.br"

        # Headers específicos
        self.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

        if access_token:
            self.headers["Authorization"] = f"Bearer {access_token}"

    def _generate_signature(self, payload: str, timestamp: int) -> str:
        """
        Gera assinatura SHA256 conforme especificação Shopee

        Args:
            payload: Payload da requisição
            timestamp: Timestamp Unix

        Returns:
            Assinatura SHA256
        """
        try:
            # String base: AppId + Timestamp + Payload + Secret
            base_string = f"{self.app_id}{timestamp}{payload}{self.secret}"

            # Gerar SHA256
            signature = hashlib.sha256(base_string.encode("utf-8")).hexdigest()

            logger.debug(f"Assinatura gerada: {signature[:16]}...")
            return signature

        except Exception as e:
            logger.error(f"Erro ao gerar assinatura: {e}")
            raise

    def _prepare_auth_headers(self, payload: str) -> Dict[str, str]:
        """
        Prepara headers de autenticação com assinatura

        Args:
            payload: Payload da requisição

        Returns:
            Headers de autenticação
        """
        timestamp = int(time.time())
        signature = self._generate_signature(payload, timestamp)

        auth_header = f"SHA256 Credential={self.app_id},Timestamp={timestamp},Signature={signature}"

        return {"Authorization": auth_header, "Content-Type": "application/json"}

    async def _make_graphql_request(
        self, query: str, variables: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Faz requisição GraphQL com autenticação

        Args:
            query: Query GraphQL
            variables: Variáveis da query (opcional)

        Returns:
            Resposta da API ou None se falhar
        """
        try:
            # Preparar payload
            payload_data = {"query": query}

            if variables:
                payload_data["variables"] = variables

            payload = json.dumps(payload_data, separators=(",", ":"))

            # Preparar headers de autenticação
            auth_headers = self._prepare_auth_headers(payload)

            # Fazer requisição
            async with self.session.post(
                f"{self.base_url}/graphql", data=payload, headers=auth_headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "errors" in data:
                        logger.error(f"Erro GraphQL: {data['errors']}")
                        return None
                    return data
                else:
                    logger.error(f"Erro na requisição GraphQL: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Erro na requisição GraphQL: {e}")
            return None

    async def create_shortlink(
        self, url: str, sub_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Cria shortlink via API oficial

        Args:
            url: URL do produto
            sub_id: Sub-ID para tracking (opcional)

        Returns:
            Shortlink ou None se falhar
        """
        try:
            # Query GraphQL para criação de shortlink
            query = """
            mutation CreateShortLink($input: CreateShortLinkInput!) {
                createShortLink(input: $input) {
                    shortLink
                    originalUrl
                    subId
                }
            }
            """

            variables = {"input": {"url": url}}

            if sub_id:
                variables["input"]["subId"] = sub_id

            result = await self._make_graphql_request(query, variables)

            if result and "data" in result:
                shortlink_data = result["data"]["createShortLink"]
                shortlink = shortlink_data["shortLink"]
                logger.info(f"Shortlink criado: {shortlink}")
                return shortlink
            else:
                logger.error("Falha ao criar shortlink")
                return None

        except Exception as e:
            logger.error(f"Erro ao criar shortlink: {e}")
            return None

    async def get_offers(
        self,
        offer_type: str = "product",
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Obtém lista de ofertas

        Args:
            offer_type: Tipo de oferta (product, brand, general)
            filters: Filtros aplicados
            limit: Número máximo de resultados

        Returns:
            Lista de ofertas
        """
        try:
            # Query GraphQL para listar ofertas
            query = """
            query GetOffers($type: OfferType!, $filters: OfferFilters, $limit: Int!) {
                offers(type: $type, filters: $filters, limit: $limit) {
                    id
                    title
                    price
                    originalPrice
                    discount
                    imageUrl
                    productUrl
                    store {
                        name
                        rating
                    }
                    category
                    tags
                }
            }
            """

            variables = {
                "type": offer_type.upper(),
                "limit": min(limit, 100),  # Máximo 100 por página
            }

            if filters:
                variables["filters"] = filters

            result = await self._make_graphql_request(query, variables)

            if result and "data" in result:
                offers = result["data"]["offers"]
                logger.info(f"Ofertas retornadas: {len(offers)}")
                return offers
            else:
                logger.error("Falha ao obter ofertas")
                return []

        except Exception as e:
            logger.error(f"Erro ao obter ofertas: {e}")
            return []

    async def get_product_offers(self, product_id: str) -> List[Dict[str, Any]]:
        """
        Obtém ofertas de um produto específico

        Args:
            product_id: ID do produto

        Returns:
            Lista de ofertas do produto
        """
        try:
            # Query GraphQL para ofertas de produto
            query = """
            query GetProductOffers($productId: String!) {
                productOffers(productId: $productId) {
                    id
                    title
                    price
                    originalPrice
                    discount
                    imageUrl
                    productUrl
                    store {
                        name
                        rating
                    }
                    availability
                    shippingInfo
                }
            }
            """

            variables = {"productId": product_id}

            result = await self._make_graphql_request(query, variables)

            if result and "data" in result:
                offers = result["data"]["productOffers"]
                logger.info(f"Ofertas do produto retornadas: {len(offers)}")
                return offers
            else:
                logger.error("Falha ao obter ofertas do produto")
                return []

        except Exception as e:
            logger.error(f"Erro ao obter ofertas do produto: {e}")
            return []

    async def get_brand_offers(
        self, brand_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtém ofertas de uma marca específica

        Args:
            brand_id: ID da marca
            limit: Número máximo de resultados

        Returns:
            Lista de ofertas da marca
        """
        try:
            # Query GraphQL para ofertas de marca
            query = """
            query GetBrandOffers($brandId: String!, $limit: Int!) {
                brandOffers(brandId: $brandId, limit: $limit) {
                    id
                    title
                    price
                    originalPrice
                    discount
                    imageUrl
                    productUrl
                    store {
                        name
                        rating
                    }
                    category
                }
            }
            """

            variables = {"brandId": brand_id, "limit": min(limit, 100)}

            result = await self._make_graphql_request(query, variables)

            if result and "data" in result:
                offers = result["data"]["brandOffers"]
                logger.info(f"Ofertas da marca retornadas: {len(offers)}")
                return offers
            else:
                logger.error("Falha ao obter ofertas da marca")
                return []

        except Exception as e:
            logger.error(f"Erro ao obter ofertas da marca: {e}")
            return []

    async def get_conversion_reports(
        self, start_date: str, end_date: str, period: str = "daily"
    ) -> List[Dict[str, Any]]:
        """
        Obtém relatórios de conversão

        Args:
            start_date: Data de início (YYYY-MM-DD)
            end_date: Data de fim (YYYY-MM-DD)
            period: Período (daily, weekly, monthly)

        Returns:
            Lista de relatórios de conversão
        """
        try:
            # Query GraphQL para relatórios de conversão
            query = """
            query GetConversionReports($startDate: String!, $endDate: String!, $period: String!) {
                conversionReports(startDate: $startDate, endDate: $endDate, period: $period) {
                    date
                    conversions
                    revenue
                    clicks
                    impressions
                    ctr
                    cpc
                    cpm
                }
            }
            """

            variables = {"startDate": start_date, "endDate": end_date, "period": period}

            result = await self._make_graphql_request(query, variables)

            if result and "data" in result:
                reports = result["data"]["conversionReports"]
                logger.info(f"Relatórios de conversão retornados: {len(reports)}")
                return reports
            else:
                logger.error("Falha ao obter relatórios de conversão")
                return []

        except Exception as e:
            logger.error(f"Erro ao obter relatórios de conversão: {e}")
            return []

    async def get_validation_reports(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Obtém relatórios de validação

        Args:
            start_date: Data de início (YYYY-MM-DD)
            end_date: Data de fim (YYYY-MM-DD)

        Returns:
            Lista de relatórios de validação
        """
        try:
            # Query GraphQL para relatórios de validação
            query = """
            query GetValidationReports($startDate: String!, $endDate: String!) {
                validationReports(startDate: $startDate, endDate: $endDate) {
                    date
                    validClicks
                    invalidClicks
                    validationRate
                    reasons
                }
            }
            """

            variables = {"startDate": start_date, "endDate": end_date}

            result = await self._make_graphql_request(query, variables)

            if result and "data" in result:
                reports = result["data"]["validationReports"]
                logger.info(f"Relatórios de validação retornados: {len(reports)}")
                return reports
            else:
                logger.error("Falha ao obter relatórios de validação")
                return []

        except Exception as e:
            logger.error(f"Erro ao obter relatórios de validação: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da API com informações específicas"""
        base_stats = super().get_stats()
        base_stats.update(
            {
                "app_id_configured": bool(self.app_id),
                "secret_configured": bool(self.secret),
                "access_token_valid": bool(self.access_token),
                "api_version": self.api_version,
            }
        )
        return base_stats


# Função de conveniência
def get_shopee_client() -> Optional[ShopeeAPIClient]:
    """
    Retorna instância do cliente Shopee se configurado

    Returns:
        ShopeeAPIClient ou None se não configurado
    """
    import os

    app_id = os.getenv("SHOPEE_APP_ID")
    secret = os.getenv("SHOPEE_SECRET")
    access_token = os.getenv("SHOPEE_ACCESS_TOKEN")

    if not app_id or not secret:
        logger.warning("Credenciais Shopee não configuradas")
        return None

    return ShopeeAPIClient(app_id, secret, access_token)
