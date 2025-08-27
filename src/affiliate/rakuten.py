"""
Módulo para integração com Rakuten Advertising.
"""

import hashlib
import logging
from typing import Optional
from urllib.parse import quote, urlparse

from src.core.settings import Settings

logger = logging.getLogger(__name__)


class FeatureDisabledError(Exception):
    """Exceção lançada quando Rakuten está desabilitado"""

    pass


class RakutenClient:
    """Cliente Rakuten com feature flag e configurações do .env"""

    def __init__(
        self, webservice_token: str, security_token: str, sid: Optional[str] = None
    ):
        """
        Inicializa o cliente Rakuten

        Args:
            webservice_token: Token de webservice do .env
            security_token: Token de segurança do .env
            sid: SID opcional por loja/programa
        """
        self.webservice_token = webservice_token
        self.security_token = security_token
        self.sid = sid
        self.base_url = "https://click.linksynergy.com/deeplink"
        self.session = None  # Será inicializado quando necessário

        # Configurações de endpoints (configuráveis via docstring)
        self.endpoints = {
            "deeplink": "https://click.linksynergy.com/deeplink",
            "api_base": "https://api.rakutenmarketing.com",  # Placeholder
            "healthcheck": "https://api.rakutenmarketing.com/health",  # Placeholder
        }

    def build_deeplink(
        self, url: str, advertiser_id: Optional[str] = None, mid: Optional[str] = None
    ) -> str:
        """
        Retorna deeplink pronto para postagem

        Args:
            url: URL de destino
            advertiser_id: ID do anunciante (opcional)
            mid: Merchant ID (opcional)

        Returns:
            Deeplink Rakuten ou fallback local

        Raises:
            FeatureDisabledError: Se RAKUTEN_ENABLED=false
        """
        # Verificar feature flag
        if not Settings.RAKUTEN_ENABLED:
            raise FeatureDisabledError(
                "Rakuten está desabilitado. Configure RAKUTEN_ENABLED=true no .env"
            )

        try:
            # Tentar usar API real (endpoints configuráveis)
            if self._is_api_accessible():
                return self._build_api_deeplink(url, advertiser_id, mid)
            else:
                # Fallback para construtor local
                logger.warning("API Rakuten não acessível, usando construtor local")
                return self._build_local_deeplink(url, advertiser_id, mid)

        except Exception as e:
            logger.error(f"Erro ao gerar deeplink Rakuten: {e}")
            # Fallback final
            return self._build_local_deeplink(url, advertiser_id, mid)

    def healthcheck(self) -> bool:
        """
        Verifica saúde do cliente Rakuten

        Returns:
            True se saudável, False caso contrário
        """
        if not Settings.RAKUTEN_ENABLED:
            return False

        try:
            # Verificar se tokens estão configurados
            if not self.webservice_token or not self.security_token:
                logger.warning("Tokens Rakuten não configurados")
                return False

            # Verificar se API está acessível
            return self._is_api_accessible()

        except Exception as e:
            logger.error(f"Erro no healthcheck Rakuten: {e}")
            return False

    def _is_api_accessible(self) -> bool:
        """Verifica se a API Rakuten está acessível"""
        # Placeholder - em produção faria uma chamada real
        # Por enquanto, sempre retorna False para usar fallback local
        return False

    def _build_api_deeplink(
        self, url: str, advertiser_id: Optional[str], mid: Optional[str]
    ) -> str:
        """Constrói deeplink via API Rakuten real"""
        # Placeholder para implementação futura
        # Por enquanto, usa fallback local
        return self._build_local_deeplink(url, advertiser_id, mid)

    def _build_local_deeplink(
        self, url: str, advertiser_id: Optional[str], mid: Optional[str]
    ) -> str:
        """Constrói deeplink local como fallback"""
        # Validar URL
        if not self._is_valid_url(url):
            raise ValueError(f"URL inválida: {url}")

        # Usar IDs configurados ou gerar hash
        if not advertiser_id:
            advertiser_id = (
                self.webservice_token[:8] if self.webservice_token else "default"
            )

        if not mid:
            mid = self.security_token[:8] if self.security_token else "default"

        # Gerar sub-id único baseado na URL
        sub_id = hashlib.md5(url.encode()).hexdigest()[:8]

        # Construir deeplink
        params = {
            "id": advertiser_id,
            "mid": mid,
            "murl": quote(url, safe=""),
            "u1": sub_id,
        }

        # Remove parâmetros vazios
        params = {k: v for k, v in params.items() if v}

        # Constrói a query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])

        deeplink = f"{self.base_url}?{query_string}"

        logger.info(f"Deeplink Rakuten local gerado: {deeplink}")
        return deeplink

    def _is_valid_url(self, url: str) -> bool:
        """Valida se a URL é válida"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def get_config_info(self) -> dict:
        """Retorna informações de configuração"""
        return {
            "enabled": Settings.RAKUTEN_ENABLED,
            "webservice_token_configured": bool(self.webservice_token),
            "security_token_configured": bool(self.security_token),
            "sid_configured": bool(self.sid),
            "endpoints": self.endpoints,
        }


class RakutenAffiliateBuilder:
    """Builder para links de afiliado Rakuten (compatibilidade)"""

    def __init__(
        self, affiliate_id: str, merchant_id: str, sub_id: Optional[str] = None
    ):
        """
        Inicializa o builder (mantido para compatibilidade)

        Args:
            affiliate_id: ID do afiliado Rakuten
            merchant_id: ID do merchant/loja
            sub_id: Sub-ID opcional para tracking
        """
        self.affiliate_id = affiliate_id
        self.merchant_id = merchant_id
        self.sub_id = sub_id or ""

        # Verificar feature flag
        if not Settings.RAKUTEN_ENABLED:
            logger.warning(
                "Rakuten está desabilitado. Use RakutenClient para funcionalidade completa."
            )

    def build_deeplink(self, target_url: str) -> str:
        """
        Constrói o link de afiliado Rakuten

        Args:
            target_url: URL de destino da oferta

        Returns:
            Link de afiliado completo

        Raises:
            FeatureDisabledError: Se RAKUTEN_ENABLED=false
        """
        if not Settings.RAKUTEN_ENABLED:
            raise FeatureDisabledError(
                "Rakuten está desabilitado. Configure RAKUTEN_ENABLED=true no .env"
            )

        base_url = "https://click.linksynergy.com/deeplink"

        params = {
            "id": self.affiliate_id,
            "mid": self.merchant_id,
            "murl": quote(target_url, safe=""),
            "u1": self.sub_id,
        }

        # Remove parâmetros vazios
        params = {k: v for k, v in params.items() if v}

        # Constrói a query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])

        return f"{base_url}?{query_string}"

    def __str__(self) -> str:
        return (
            f"RakutenAffiliateBuilder(id={self.affiliate_id}, mid={self.merchant_id})"
        )


def get_rakuten_client() -> Optional[RakutenClient]:
    """
    Retorna instância do cliente Rakuten se configurado

    Returns:
        RakutenClient ou None se não configurado
    """
    if not Settings.RAKUTEN_ENABLED:
        return None

    webservice_token = Settings.RAKUTEN_WEBSERVICE_TOKEN
    security_token = Settings.RAKUTEN_SECURITY_TOKEN
    sid = Settings.RAKUTEN_SID

    if not webservice_token or not security_token:
        logger.warning("Tokens Rakuten não configurados")
        return None

    return RakutenClient(webservice_token, security_token, sid)


# Função de conveniência (mantida para compatibilidade)
def build_rakuten_link(
    target_url: str, affiliate_id: str, merchant_id: str, sub_id: Optional[str] = None
) -> str:
    """
    Função de conveniência para construir links Rakuten

    Args:
        target_url: URL de destino
        affiliate_id: ID do afiliado
        merchant_id: ID do merchant
        sub_id: Sub-ID opcional

    Returns:
        Link de afiliado Rakuten

    Raises:
        FeatureDisabledError: Se RAKUTEN_ENABLED=false
    """
    if not Settings.RAKUTEN_ENABLED:
        raise FeatureDisabledError(
            "Rakuten está desabilitado. Configure RAKUTEN_ENABLED=true no .env"
        )

    builder = RakutenAffiliateBuilder(affiliate_id, merchant_id, sub_id)
    return builder.build_deeplink(target_url)


__all__ = [
    "RakutenClient",
    "RakutenAffiliateBuilder",
    "FeatureDisabledError",
    "get_rakuten_client",
    "build_rakuten_link",
]
