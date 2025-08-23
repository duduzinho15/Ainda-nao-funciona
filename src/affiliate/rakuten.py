"""
Rakuten Affiliate Link Builder
Converte URLs para links de afiliado Rakuten usando Linksynergy
"""

from typing import Optional
from urllib.parse import quote


class RakutenAffiliateBuilder:
    """Builder para links de afiliado Rakuten"""

    def __init__(
        self, affiliate_id: str, merchant_id: str, sub_id: Optional[str] = None
    ):
        """
        Inicializa o builder

        Args:
            affiliate_id: ID do afiliado Rakuten
            merchant_id: ID do merchant/loja
            sub_id: Sub-ID opcional para tracking
        """
        self.affiliate_id = affiliate_id
        self.merchant_id = merchant_id
        self.sub_id = sub_id or ""

    def build_deeplink(self, target_url: str) -> str:
        """
        Constrói o link de afiliado Rakuten

        Args:
            target_url: URL de destino da oferta

        Returns:
            Link de afiliado completo
        """
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


# Função de conveniência
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
    """
    builder = RakutenAffiliateBuilder(affiliate_id, merchant_id, sub_id)
    return builder.build_deeplink(target_url)
