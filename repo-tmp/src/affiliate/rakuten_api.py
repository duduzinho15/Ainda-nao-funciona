"""
Cliente API oficial do Rakuten Advertising
Implementa OAuth2, deep links, busca de produtos e relatórios
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from src.affiliate.base_api import BaseAPI

logger = logging.getLogger(__name__)


class RakutenAPIClient(BaseAPI):
    """Cliente para API oficial do Rakuten Advertising"""

    def __init__(self, client_id: str, client_secret: str, access_token: str = None):
        """
        Inicializa cliente Rakuten API

        Args:
            client_id: Client ID do OAuth2
            client_secret: Client Secret do OAuth2
            access_token: Token de acesso (opcional)
        """
        super().__init__("Rakuten", "https://api.rakutenmarketing.com", client_id)
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.token_expires_at = None

        # Configurações específicas
        self.api_version = "v2"
        self.base_url = f"https://api.rakutenmarketing.com/{self.api_version}"

        # Headers específicos
        self.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

        if access_token:
            self.headers["Authorization"] = f"Bearer {access_token}"

    async def get_access_token(self) -> Optional[str]:
        """
        Obtém token de acesso via OAuth2 Client Credentials

        Returns:
            Token de acesso ou None se falhar
        """
        try:
            auth_url = "https://api.rakutenmarketing.com/oauth2/token"

            auth_data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            async with self.session.post(
                auth_url,
                data=urlencode(auth_data),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "access_token" in data:
                        self.access_token = data["access_token"]
                        expires_in = data.get("expires_in", 3600)  # 1h padrão
                        self.token_expires_at = datetime.now() + timedelta(
                            seconds=expires_in
                        )

                        # Atualizar header de autorização
                        self.headers["Authorization"] = f"Bearer {self.access_token}"

                        logger.info("Token de acesso Rakuten obtido com sucesso")
                        return self.access_token
                    else:
                        logger.error(f"Token não encontrado na resposta: {data}")
                        return None
                else:
                    logger.error(f"Erro ao obter token: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Erro ao obter token de acesso: {e}")
            return None

    async def refresh_token(self) -> bool:
        """
        Renova token de acesso

        Returns:
            True se renovado com sucesso
        """
        try:
            if not self.access_token:
                return await self.get_access_token() is not None

            # Verificar se token expirou
            if self.token_expires_at and datetime.now() >= self.token_expires_at:
                logger.info("Token expirado, renovando...")
                return await self.get_access_token() is not None

            return True

        except Exception as e:
            logger.error(f"Erro ao renovar token: {e}")
            return False

    async def build_deeplink(
        self, advertiser_id: str, url: str, sub_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Gera deep link via API oficial

        Args:
            advertiser_id: ID do anunciante
            url: URL de destino
            sub_id: Sub-ID para tracking (opcional)

        Returns:
            Deep link ou None se falhar
        """
        try:
            # Verificar/renovar token
            if not await self.refresh_token():
                return None

            deeplink_url = "https://click.linksynergy.com/deeplink"

            # Parâmetros do deep link
            params = {"id": self.client_id, "mid": advertiser_id, "murl": url}

            if sub_id:
                params["u1"] = sub_id

            # Construir URL do deep link
            query_string = urlencode(params)
            deeplink = f"{deeplink_url}?{query_string}"

            logger.info(f"Deep link Rakuten gerado: {deeplink[:80]}...")
            return deeplink

        except Exception as e:
            logger.error(f"Erro ao gerar deep link: {e}")
            return None

    async def search_products(
        self, query: str, advertiser_id: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Busca produtos via API oficial

        Args:
            query: Termo de busca
            advertiser_id: ID do anunciante (opcional)
            limit: Número máximo de resultados

        Returns:
            Lista de produtos encontrados
        """
        try:
            # Verificar/renovar token
            if not await self.refresh_token():
                return []

            endpoint = f"{self.base_url}/productsearch"

            # Parâmetros da busca
            params = {
                "keyword": query,
                "limit": min(limit, 100),  # Máximo 100 por página
            }

            if advertiser_id:
                params["advertiser_id"] = advertiser_id

            async with self.session.get(
                endpoint, params=params, headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "products" in data:
                        products = data["products"]
                        logger.info(f"Busca retornou {len(products)} produtos")
                        return products
                    else:
                        logger.error(f"Produtos não encontrados na resposta: {data}")
                        return []
                else:
                    logger.error(f"Erro na busca: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Erro na busca de produtos: {e}")
            return []

    async def list_advertisers(self, deep_links: bool = True) -> List[Dict[str, Any]]:
        """
        Lista anunciantes disponíveis

        Args:
            deep_links: Filtrar apenas anunciantes que permitem deep links

        Returns:
            Lista de anunciantes
        """
        try:
            # Verificar/renovar token
            if not await self.refresh_token():
                return []

            endpoint = f"{self.base_url}/advertisers"

            # Parâmetros da busca
            params = {}
            if deep_links:
                params["deep_links"] = "true"

            async with self.session.get(
                endpoint, params=params, headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "advertisers" in data:
                        advertisers = data["advertisers"]
                        logger.info(f"Lista retornou {len(advertisers)} anunciantes")
                        return advertisers
                    else:
                        logger.error(f"Anunciantes não encontrados na resposta: {data}")
                        return []
                else:
                    logger.error(f"Erro ao listar anunciantes: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Erro ao listar anunciantes: {e}")
            return []

    async def get_conversion_reports(
        self, start_date: str, end_date: str, granularity: str = "daily"
    ) -> List[Dict[str, Any]]:
        """
        Obtém relatórios de conversão

        Args:
            start_date: Data de início (YYYY-MM-DD)
            end_date: Data de fim (YYYY-MM-DD)
            granularity: Granularidade (daily, weekly, monthly)

        Returns:
            Lista de relatórios de conversão
        """
        try:
            # Verificar/renovar token
            if not await self.refresh_token():
                return []

            endpoint = f"{self.base_url}/reports/conversions"

            # Parâmetros do relatório
            params = {
                "start_date": start_date,
                "end_date": end_date,
                "granularity": granularity,
            }

            async with self.session.get(
                endpoint, params=params, headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "conversions" in data:
                        conversions = data["conversions"]
                        logger.info(f"Relatório retornou {len(conversions)} conversões")
                        return conversions
                    else:
                        logger.error(f"Conversões não encontradas na resposta: {data}")
                        return []
                else:
                    logger.error(f"Erro no relatório: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Erro ao obter relatório de conversão: {e}")
            return []

    async def get_events(
        self, start_date: str, end_date: str, event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém eventos de tracking

        Args:
            start_date: Data de início (YYYY-MM-DD)
            end_date: Data de fim (YYYY-MM-DD)
            event_type: Tipo de evento (opcional)

        Returns:
            Lista de eventos
        """
        try:
            # Verificar/renovar token
            if not await self.refresh_token():
                return []

            endpoint = f"{self.base_url}/events"

            # Parâmetros da busca
            params = {"start_date": start_date, "end_date": end_date}

            if event_type:
                params["event_type"] = event_type

            async with self.session.get(
                endpoint, params=params, headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "events" in data:
                        events = data["events"]
                        logger.info(f"Eventos retornados: {len(events)}")
                        return events
                    else:
                        logger.error(f"Eventos não encontrados na resposta: {data}")
                        return []
                else:
                    logger.error(f"Erro ao obter eventos: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Erro ao obter eventos: {e}")
            return []

    async def get_coupons(
        self, advertiser_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém cupons disponíveis

        Args:
            advertiser_id: ID do anunciante (opcional)

        Returns:
            Lista de cupons
        """
        try:
            # Verificar/renovar token
            if not await self.refresh_token():
                return []

            endpoint = f"{self.base_url}/coupons"

            # Parâmetros da busca
            params = {}
            if advertiser_id:
                params["advertiser_id"] = advertiser_id

            async with self.session.get(
                endpoint, params=params, headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "coupons" in data:
                        coupons = data["coupons"]
                        logger.info(f"Cupons retornados: {len(coupons)}")
                        return coupons
                    else:
                        logger.error(f"Cupons não encontrados na resposta: {data}")
                        return []
                else:
                    logger.error(f"Erro ao obter cupons: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Erro ao obter cupons: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da API com informações específicas"""
        base_stats = super().get_stats()
        base_stats.update(
            {
                "client_id_configured": bool(self.client_id),
                "client_secret_configured": bool(self.client_secret),
                "access_token_valid": bool(
                    self.access_token
                    and (
                        not self.token_expires_at
                        or datetime.now() < self.token_expires_at
                    )
                ),
                "api_version": self.api_version,
            }
        )
        return base_stats


# Função de conveniência
def get_rakuten_client() -> Optional[RakutenAPIClient]:
    """
    Retorna instância do cliente Rakuten se configurado

    Returns:
        RakutenAPIClient ou None se não configurado
    """
    import os

    client_id = os.getenv("RKTN_CLIENT_ID")
    client_secret = os.getenv("RKTN_CLIENT_SECRET")
    access_token = os.getenv("RKTN_ACCESS_TOKEN")

    if not client_id or not client_secret:
        logger.warning("Credenciais Rakuten não configuradas")
        return None

    return RakutenAPIClient(client_id, client_secret, access_token)
