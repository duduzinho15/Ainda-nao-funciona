"""
Cliente API oficial do AliExpress Open Platform
Implementa autenticação, geração de links de afiliado e busca de produtos
"""

import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from src.affiliate.base_api import BaseAPI

logger = logging.getLogger(__name__)


class AliExpressAPIClient(BaseAPI):
    """Cliente para API oficial do AliExpress Open Platform"""

    def __init__(self, app_key: str, app_secret: str, access_token: str = None):
        """
        Inicializa cliente AliExpress API

        Args:
            app_key: App Key do Open Platform
            app_secret: App Secret do Open Platform
            access_token: Token de acesso (opcional)
        """
        super().__init__("AliExpress", "https://api.aliexpress.com", app_key)
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token
        self.token_expires_at = None

        # Configurações específicas
        self.api_version = "2.0"
        self.sign_method = "sha256"
        self.timestamp_format = "yyyy-MM-dd HH:mm:ss"

        # Headers específicos
        self.headers.update(
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }
        )

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Gera assinatura HMAC-SHA256 conforme Open Platform

        Args:
            params: Parâmetros da requisição

        Returns:
            Assinatura HMAC-SHA256
        """
        try:
            # Ordenar parâmetros alfabeticamente
            sorted_params = sorted(params.items())

            # Construir string base para assinatura
            base_string = self.app_secret
            for key, value in sorted_params:
                base_string += f"{key}{value}"
            base_string += self.app_secret

            # Gerar HMAC-SHA256
            signature = (
                hmac.new(
                    self.app_secret.encode("utf-8"),
                    base_string.encode("utf-8"),
                    hashlib.sha256,
                )
                .hexdigest()
                .upper()
            )

            logger.debug(f"Assinatura gerada: {signature[:16]}...")
            return signature

        except Exception as e:
            logger.error(f"Erro ao gerar assinatura: {e}")
            raise

    def _prepare_request_params(
        self, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepara parâmetros da requisição com assinatura

        Args:
            method: Método da API
            params: Parâmetros específicos

        Returns:
            Parâmetros completos com assinatura
        """
        # Parâmetros base
        request_params = {
            "method": method,
            "app_key": self.app_key,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "format": "json",
            "v": self.api_version,
            "sign_method": self.sign_method,
        }

        # Adicionar parâmetros específicos
        request_params.update(params)

        # Gerar assinatura
        request_params["sign"] = self._generate_signature(request_params)

        return request_params

    async def get_access_token(self) -> Optional[str]:
        """
        Obtém token de acesso via System Tool

        Returns:
            Token de acesso ou None se falhar
        """
        try:
            params = self._prepare_request_params(
                "system.oauth.token", {"grant_type": "client_credentials"}
            )

            async with self.session.post(
                f"{self.base_url}/system/oauth/token",
                data=urlencode(params),
                headers=self.headers,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "access_token" in data:
                        self.access_token = data["access_token"]
                        expires_in = data.get("expires_in", 7200)  # 2h padrão
                        self.token_expires_at = datetime.now() + timedelta(
                            seconds=expires_in
                        )

                        # Atualizar header de autorização
                        self.headers["Authorization"] = f"Bearer {self.access_token}"

                        logger.info("Token de acesso AliExpress obtido com sucesso")
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

    async def generate_affiliate_link(
        self, url: str, tracking_id: str = "telegram"
    ) -> Optional[str]:
        """
        Gera link de afiliado via API oficial

        Args:
            url: URL do produto
            tracking_id: ID de tracking

        Returns:
            Link de afiliado ou None se falhar
        """
        try:
            # Verificar/renovar token
            if not await self.refresh_token():
                return None

            params = self._prepare_request_params(
                "affiliate.link.generate",
                {"url": url, "tracking_id": tracking_id, "source": "api"},
            )

            async with self.session.post(
                f"{self.base_url}/affiliate/link/generate",
                data=urlencode(params),
                headers=self.headers,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "affiliate_url" in data:
                        affiliate_url = data["affiliate_url"]
                        logger.info(f"Link de afiliado gerado: {affiliate_url[:50]}...")
                        return affiliate_url
                    else:
                        logger.error(f"Link não encontrado na resposta: {data}")
                        return None
                else:
                    logger.error(f"Erro ao gerar link: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Erro ao gerar link de afiliado: {e}")
            return None

    async def search_products(
        self,
        query: str,
        limit: int = 50,
        ship_to_country: str = "BR",
        currency: str = "BRL",
        language: str = "pt",
    ) -> List[Dict[str, Any]]:
        """
        Busca produtos via API oficial

        Args:
            query: Termo de busca
            limit: Número máximo de resultados
            ship_to_country: País de entrega
            currency: Moeda
            language: Idioma

        Returns:
            Lista de produtos encontrados
        """
        try:
            # Verificar/renovar token
            if not await self.refresh_token():
                return []

            params = self._prepare_request_params(
                "product.search",
                {
                    "keywords": query,
                    "page_size": min(limit, 100),  # Máximo 100 por página
                    "ship_to_country": ship_to_country,
                    "currency": currency,
                    "language": language,
                },
            )

            async with self.session.post(
                f"{self.base_url}/product/search",
                data=urlencode(params),
                headers=self.headers,
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

    async def get_hot_products(
        self, category_id: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtém produtos em alta

        Args:
            category_id: ID da categoria (opcional)
            limit: Número máximo de resultados

        Returns:
            Lista de produtos em alta
        """
        try:
            # Verificar/renovar token
            if not await self.refresh_token():
                return []

            params = self._prepare_request_params(
                "product.hot", {"page_size": min(limit, 100)}
            )

            if category_id:
                params["category_id"] = category_id

            async with self.session.post(
                f"{self.base_url}/product/hot",
                data=urlencode(params),
                headers=self.headers,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "hot_products" in data:
                        products = data["hot_products"]
                        logger.info(f"Produtos em alta retornados: {len(products)}")
                        return products
                    else:
                        logger.error(f"Produtos em alta não encontrados: {data}")
                        return []
                else:
                    logger.error(f"Erro ao obter produtos em alta: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Erro ao obter produtos em alta: {e}")
            return []

    async def get_product_details(
        self, product_id: str, sku: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de um produto

        Args:
            product_id: ID do produto
            sku: SKU específico (opcional)

        Returns:
            Detalhes do produto ou None se falhar
        """
        try:
            # Verificar/renovar token
            if not await self.refresh_token():
                return None

            params = self._prepare_request_params(
                "product.detail", {"product_id": product_id}
            )

            if sku:
                params["sku"] = sku

            async with self.session.post(
                f"{self.base_url}/product/detail",
                data=urlencode(params),
                headers=self.headers,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "product" in data:
                        product = data["product"]
                        logger.info(
                            f"Detalhes do produto obtidos: {product.get('title', 'N/A')[:30]}..."
                        )
                        return product
                    else:
                        logger.error(f"Produto não encontrado na resposta: {data}")
                        return None
                else:
                    logger.error(f"Erro ao obter detalhes: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Erro ao obter detalhes do produto: {e}")
            return None

    async def get_smart_match_products(
        self, image_url: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Busca produtos similares via smart match

        Args:
            image_url: URL da imagem do produto
            limit: Número máximo de resultados

        Returns:
            Lista de produtos similares
        """
        try:
            # Verificar/renovar token
            if not await self.refresh_token():
                return []

            params = self._prepare_request_params(
                "product.smart_match",
                {"image_url": image_url, "page_size": min(limit, 50)},
            )

            async with self.session.post(
                f"{self.base_url}/product/smart_match",
                data=urlencode(params),
                headers=self.headers,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "similar_products" in data:
                        products = data["similar_products"]
                        logger.info(f"Smart match retornou {len(products)} produtos")
                        return products
                    else:
                        logger.error(f"Produtos similares não encontrados: {data}")
                        return []
                else:
                    logger.error(f"Erro no smart match: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Erro no smart match: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da API com informações específicas"""
        base_stats = super().get_stats()
        base_stats.update(
            {
                "app_key_configured": bool(self.app_key),
                "app_secret_configured": bool(self.app_secret),
                "access_token_valid": bool(
                    self.access_token
                    and (
                        not self.token_expires_at
                        or datetime.now() < self.token_expires_at
                    )
                ),
                "api_version": self.api_version,
                "sign_method": self.sign_method,
            }
        )
        return base_stats


# Função de conveniência
def get_aliexpress_client() -> Optional[AliExpressAPIClient]:
    """
    Retorna instância do cliente AliExpress se configurado

    Returns:
        AliExpressAPIClient ou None se não configurado
    """
    import os

    app_key = os.getenv("ALI_APP_KEY")
    app_secret = os.getenv("ALI_APP_SECRET")
    access_token = os.getenv("ALI_ACCESS_TOKEN")

    if not app_key or not app_secret:
        logger.warning("Credenciais AliExpress não configuradas")
        return None

    return AliExpressAPIClient(app_key, app_secret, access_token)
