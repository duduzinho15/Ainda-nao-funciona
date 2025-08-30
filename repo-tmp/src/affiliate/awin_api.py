"""
Cliente API oficial do Awin Publisher
Implementa Link Builder API e Product Feed para geração de deeplinks
"""

import json
import logging
from typing import Any, Dict, List, Optional

from src.affiliate.base_api import BaseAPI

logger = logging.getLogger(__name__)


class AwinAPIClient(BaseAPI):
    """Cliente para API oficial do Awin Publisher"""

    def __init__(self, publisher_id: str, access_token: str):
        """
        Inicializa cliente Awin API

        Args:
            publisher_id: ID do publisher
            access_token: Token de acesso
        """
        super().__init__("Awin", "https://api.awin.com", access_token)
        self.publisher_id = publisher_id
        self.access_token = access_token

        # Configurações específicas
        self.api_version = "v1"
        self.base_url = "https://api.awin.com"

        # Headers específicos
        self.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
        )

    async def generate_link(
        self, advertiser_id: str, url: str, sub_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Gera link de afiliado via Link Builder API

        Args:
            advertiser_id: ID do anunciante
            url: URL de destino
            sub_id: Sub-ID para tracking (opcional)

        Returns:
            Link de afiliado ou None se falhar
        """
        try:
            endpoint = f"{self.base_url}/generateLink"

            # Parâmetros da requisição
            params = {
                "publisherId": self.publisher_id,
                "advertiserId": advertiser_id,
                "url": url,
            }

            if sub_id:
                params["subId"] = sub_id

            async with self.session.post(
                endpoint, json=params, headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "affiliateUrl" in data:
                        affiliate_url = data["affiliateUrl"]
                        logger.info(f"Link Awin gerado: {affiliate_url[:80]}...")
                        return affiliate_url
                    else:
                        logger.error(f"Link não encontrado na resposta: {data}")
                        return None
                else:
                    logger.error(f"Erro ao gerar link: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Erro ao gerar link Awin: {e}")
            return None

    async def generate_batch_links(
        self, links: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Gera múltiplos links de afiliado em lote

        Args:
            links: Lista de links para gerar
                [{"advertiserId": "123", "url": "https://...", "subId": "optional"}]

        Returns:
            Lista de resultados com links gerados
        """
        try:
            endpoint = f"{self.base_url}/generateBatchLinks"

            # Preparar dados para lote
            batch_data = {"publisherId": self.publisher_id, "links": links}

            async with self.session.post(
                endpoint, json=batch_data, headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "results" in data:
                        results = data["results"]
                        logger.info(
                            f"Lote de {len(links)} links processado: {len(results)} sucessos"
                        )
                        return results
                    else:
                        logger.error(f"Resultados não encontrados na resposta: {data}")
                        return []
                else:
                    logger.error(f"Erro no lote de links: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Erro no lote de links: {e}")
            return []

    async def get_product_feed(
        self, advertiser_id: str, feed_type: str = "product"
    ) -> List[Dict[str, Any]]:
        """
        Obtém feed de produtos do anunciante

        Args:
            advertiser_id: ID do anunciante
            feed_type: Tipo de feed (product, category, etc.)

        Returns:
            Lista de produtos do feed
        """
        try:
            endpoint = f"{self.base_url}/feeds/{advertiser_id}"

            params = {"type": feed_type, "publisherId": self.publisher_id}

            async with self.session.get(
                endpoint, params=params, headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "products" in data:
                        products = data["products"]
                        logger.info(f"Feed retornou {len(products)} produtos")
                        return products
                    else:
                        logger.error(f"Produtos não encontrados no feed: {data}")
                        return []
                else:
                    logger.error(f"Erro ao obter feed: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Erro ao obter feed: {e}")
            return []

    async def download_product_feed(
        self, advertiser_id: str, feed_url: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Faz download de feed de produtos via URL

        Args:
            advertiser_id: ID do anunciante
            feed_url: URL do feed para download

        Returns:
            Lista de produtos do feed ou None se falhar
        """
        try:
            # Fazer download do feed
            async with self.session.get(feed_url) as response:
                if response.status == 200:
                    content = await response.text()

                    # Tentar parse como JSON primeiro
                    try:
                        data = json.loads(content)
                        if "products" in data:
                            products = data["products"]
                            logger.info(f"Feed baixado: {len(products)} produtos")
                            return products
                    except json.JSONDecodeError:
                        # Tentar parse como CSV ou XML se necessário
                        logger.info("Feed não é JSON, tentando outros formatos...")
                        # Implementar parse de outros formatos se necessário
                        return []
                else:
                    logger.error(f"Erro ao baixar feed: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Erro ao baixar feed: {e}")
            return None

    async def list_advertisers(self) -> List[Dict[str, Any]]:
        """
        Lista anunciantes disponíveis para o publisher

        Returns:
            Lista de anunciantes
        """
        try:
            endpoint = f"{self.base_url}/advertisers"

            params = {"publisherId": self.publisher_id}

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

    async def get_publisher_performance(
        self, start_date: str, end_date: str, granularity: str = "daily"
    ) -> List[Dict[str, Any]]:
        """
        Obtém relatório de performance do publisher

        Args:
            start_date: Data de início (YYYY-MM-DD)
            end_date: Data de fim (YYYY-MM-DD)
            granularity: Granularidade (daily, weekly, monthly)

        Returns:
            Lista de relatórios de performance
        """
        try:
            endpoint = f"{self.base_url}/reports/publisher/performance"

            params = {
                "publisherId": self.publisher_id,
                "startDate": start_date,
                "endDate": end_date,
                "granularity": granularity,
            }

            async with self.session.get(
                endpoint, params=params, headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "performance" in data:
                        performance = data["performance"]
                        logger.info(
                            f"Relatório de performance retornado: {len(performance)} registros"
                        )
                        return performance
                    else:
                        logger.error(f"Performance não encontrada na resposta: {data}")
                        return []
                else:
                    logger.error(f"Erro no relatório: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Erro ao obter performance: {e}")
            return []

    async def get_advertiser_performance(
        self, advertiser_id: str, start_date: str, end_date: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém relatório de performance de um anunciante específico

        Args:
            advertiser_id: ID do anunciante
            start_date: Data de início (YYYY-MM-DD)
            end_date: Data de fim (YYYY-MM-DD)

        Returns:
            Relatório de performance ou None se falhar
        """
        try:
            endpoint = f"{self.base_url}/reports/advertiser/{advertiser_id}/performance"

            params = {
                "publisherId": self.publisher_id,
                "startDate": start_date,
                "endDate": end_date,
            }

            async with self.session.get(
                endpoint, params=params, headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "performance" in data:
                        performance = data["performance"]
                        logger.info(
                            f"Performance do anunciante obtida: {advertiser_id}"
                        )
                        return performance
                    else:
                        logger.error(f"Performance não encontrada na resposta: {data}")
                        return None
                else:
                    logger.error(f"Erro no relatório do anunciante: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Erro ao obter performance do anunciante: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da API com informações específicas"""
        base_stats = super().get_stats()
        base_stats.update(
            {
                "publisher_id": self.publisher_id,
                "access_token_valid": bool(self.access_token),
                "api_version": self.api_version,
            }
        )
        return base_stats


# Função de conveniência
def get_awin_client() -> Optional[AwinAPIClient]:
    """
    Retorna instância do cliente Awin se configurado

    Returns:
        AwinAPIClient ou None se não configurado
    """
    import os

    publisher_id = os.getenv("AWIN_PUBLISHER_ID")
    access_token = os.getenv("AWIN_ACCESS_TOKEN")

    if not publisher_id or not access_token:
        logger.warning("Credenciais Awin não configuradas")
        return None

    return AwinAPIClient(publisher_id, access_token)
