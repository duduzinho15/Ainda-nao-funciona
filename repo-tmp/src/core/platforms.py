"""
Configuração centralizada das plataformas ativas com afiliação válida

⚠️ IMPORTANTE: Este arquivo define TODAS as plataformas permitidas no pipeline.
   Scrapers arquivados (americanas, submarino, casas_bahia, fast_shop, ricardo_eletro)
   NÃO devem aparecer em nenhuma lista, cron ou agendador.

📋 PLATAFORMAS ATIVAS (com afiliação):
   - Awin: Comfy, Trocafy, LG, KaBuM!, Ninja, Samsung
   - Mercado Livre: shortlink + etiqueta garimpeirogeek
   - Magazine Luiza: vitrine Magazine Você
   - Amazon: tag garimpeirogee-20
   - Shopee: shortlink via painel + cache
   - AliExpress: shortlink via portal + cache

🚫 PLATAFORMAS ARQUIVADAS (sem afiliação):
   - Americanas/Submarino: mesmo grupo, sem afiliação
   - Casas Bahia: sem programa de afiliados
   - Fast Shop: sem programa de afiliados
   - Ricardo Eletro: sem programa de afiliados
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """Tipos de plataforma"""

    AWIN = "awin"
    MERCADO_LIVRE = "mercadolivre"
    MAGALU = "magalu"
    AMAZON = "amazon"
    SHOPEE = "shopee"
    ALIEXPRESS = "aliexpress"
    RAKUTEN = "rakuten"  # Placeholder para futuro


@dataclass
class PlatformConfig:
    """Configuração de uma plataforma"""

    name: str
    type: PlatformType
    active: bool
    affiliate_enabled: bool
    scraper_enabled: bool
    description: str
    affiliate_info: Optional[Dict] = None


# Configuração das plataformas ativas
PLATAFORMAS_ATIVAS: Dict[str, PlatformConfig] = {
    "awin": PlatformConfig(
        name="Awin (Comfy/Trocafy/LG/KaBuM!/Ninja/Samsung)",
        type=PlatformType.AWIN,
        active=True,
        affiliate_enabled=True,
        scraper_enabled=True,
        description="Plataforma Awin com deeplinks para múltiplas lojas",
        affiliate_info={
            "type": "deeplink",
            "format": "https://www.awin1.com/cread.php?awinmid={mid}&awinaffid={affid}&ued={url}",
            "stores": ["comfy", "trocafy", "lg", "kabum", "ninja", "samsung"],
            "attribution": "Lastclick Awin, 30 dias cookie",
            "payout": "CPA variável por loja (ex: Comfy 2.80%)",
            "rules": "Permitido: cupons, cashback, loyalty, email marketing, influenciadores",
        },
    ),
    "mercadolivre": PlatformConfig(
        name="Mercado Livre",
        type=PlatformType.MERCADO_LIVRE,
        active=True,
        affiliate_enabled=True,
        scraper_enabled=True,
        description="Shortlink com etiqueta garimpeirogeek",
        affiliate_info={
            "type": "shortlink",
            "format": "https://mercadolivre.com/sec/{code}",
            "tag": "garimpeirogeek",
            "attribution": "Lastclick, cookie de sessão",
            "payout": "Comissão por venda realizada",
            "rules": "Permitido: marketing digital, redes sociais, blogs",
        },
    ),
    "magalu": PlatformConfig(
        name="Magazine Luiza (Magazine Você)",
        type=PlatformType.MAGALU,
        active=True,
        affiliate_enabled=True,
        scraper_enabled=True,
        description="Link da vitrine Magazine Você",
        affiliate_info={
            "type": "vitrine",
            "format": "https://www.magazinevoce.com.br/magazinegarimpeirogeek/",
            "store": "magazinegarimpeirogeek",
        },
    ),
    "amazon": PlatformConfig(
        name="Amazon",
        type=PlatformType.AMAZON,
        active=True,
        affiliate_enabled=True,
        scraper_enabled=True,
        description="Link normalizado com tag garimpeirogee-20",
        affiliate_info={
            "type": "tag",
            "format": "https://amzn.to/{code}",
            "tag": "garimpeirogee-20",
            "attribution": "Lastclick, 24h cookie",
            "payout": "4% sobre produtos elegíveis",
            "rules": "Permitido: marketing digital, redes sociais, blogs, email",
        },
    ),
    "shopee": PlatformConfig(
        name="Shopee",
        type=PlatformType.SHOPEE,
        active=True,
        affiliate_enabled=True,
        scraper_enabled=True,
        description="Shortlink via painel + cache",
        affiliate_info={
            "type": "shortlink",
            "format": "https://s.shopee.com.br/{code}",
            "cache": True,
        },
    ),
    "aliexpress": PlatformConfig(
        name="AliExpress",
        type=PlatformType.ALIEXPRESS,
        active=True,
        affiliate_enabled=True,
        scraper_enabled=True,
        description="Shortlink via portal + cache",
        affiliate_info={
            "type": "shortlink",
            "format": "https://s.click.aliexpress.com/e/{code}",
            "tracking_id": "telegram",
            "ship_to": "Brazil",
            "cache": True,
        },
    ),
    "rakuten": PlatformConfig(
        name="Rakuten (LinkSynergy)",
        type=PlatformType.RAKUTEN,
        active=False,  # Controlado por RAKUTEN_ENABLED
        affiliate_enabled=False,  # Controlado por RAKUTEN_ENABLED
        scraper_enabled=False,
        description="Integração Rakuten com feature flag (desabilitado por padrão)",
        affiliate_info={
            "type": "deeplink",
            "format": "https://click.linksynergy.com/deeplink?id={id}&mid={mid}&murl={url}&u1={subid}",
            "status": "feature_flag_controlled",
            "feature_flag": "RAKUTEN_ENABLED",
            "tokens_required": ["RAKUTEN_WEBSERVICE_TOKEN", "RAKUTEN_SECURITY_TOKEN"],
        },
    ),
}


def get_active_platforms() -> List[str]:
    """Retorna lista de plataformas ativas"""
    return [name for name, config in PLATAFORMAS_ATIVAS.items() if config.active]


def get_affiliate_platforms() -> List[str]:
    """Retorna lista de plataformas com afiliação ativa"""
    return [
        name
        for name, config in PLATAFORMAS_ATIVAS.items()
        if config.active and config.affiliate_enabled
    ]


def get_scraper_platforms() -> List[str]:
    """Retorna lista de plataformas com scraper ativo"""
    return [
        name
        for name, config in PLATAFORMAS_ATIVAS.items()
        if config.active and config.scraper_enabled
    ]


def is_platform_active(platform_name: str) -> bool:
    """Verifica se uma plataforma está ativa"""
    return (
        platform_name in PLATAFORMAS_ATIVAS and PLATAFORMAS_ATIVAS[platform_name].active
    )


def get_platform_config(platform_name: str) -> Optional[PlatformConfig]:
    """Retorna configuração de uma plataforma"""
    return PLATAFORMAS_ATIVAS.get(platform_name)


# Configurações Awin específicas
AWIN_CONFIG = {
    "comfy": ("23377", "2370719"),  # Comfy BR - AFFID 2370719
    "trocafy": ("51277", "2370719"),  # Trocafy - AFFID 2370719
    "lg": ("33061", "2370719"),  # LG Brasil - AFFID 2370719
    "kabum": ("17729", "2370719"),  # KaBuM! - AFFID 2370719
    "ninja": ("106765", "2370719"),  # Ninja - AFFID 2370719
    "samsung": ("25539", "2510157"),  # Samsung - AFFID 2510157
}


def get_awin_config(loja: str) -> Optional[tuple[str, str]]:
    """
    Retorna configuração Awin para uma loja específica

    Args:
        loja: Nome da loja (ex: 'comfy', 'kabum', 'lg')

    Returns:
        Tupla (MID, AFFID) ou None se não configurada
    """
    return AWIN_CONFIG.get(loja.lower())


def get_awin_stores() -> list[str]:
    """Retorna lista de lojas configuradas no Awin"""
    return list(AWIN_CONFIG.keys())


def validate_awin_config() -> bool:
    """
    Valida se todas as lojas Awin ativas possuem MID e AFFID configurados

    Returns:
        True se todas as configurações estão válidas
    """
    try:
        # Verificar se todas as lojas Awin têm configuração
        for loja in AWIN_CONFIG:
            if not get_awin_config(loja):
                return False

        return True

    except Exception as e:
        logger.error(f"Erro ao validar configuração Awin: {e}")
        return False


def validate_rakuten_config() -> bool:
    """
    Valida se a configuração Rakuten está correta

    Returns:
        True se a configuração está válida
    """
    from src.core.settings import Settings

    try:
        # Se Rakuten não está habilitado, não precisa validar
        if not Settings.RAKUTEN_ENABLED:
            return True

        # Verificar se tokens obrigatórios estão configurados
        if not Settings.RAKUTEN_WEBSERVICE_TOKEN:
            logger.warning("RAKUTEN_WEBSERVICE_TOKEN não configurado")
            return False

        if not Settings.RAKUTEN_SECURITY_TOKEN:
            logger.warning("RAKUTEN_SECURITY_TOKEN não configurado")
            return False

        # Verificar saúde do cliente
        from src.affiliate.rakuten import get_rakuten_client

        client = get_rakuten_client()

        if client and client.healthcheck():
            return True
        else:
            logger.warning("Cliente Rakuten não está saudável")
            return False

    except Exception as e:
        logger.error(f"Erro ao validar configuração Rakuten: {e}")
        return False


# Listas de conveniência
PLATAFORMAS_COM_AFILIACAO = get_affiliate_platforms()
PLATAFORMAS_COM_SCRAPER = get_scraper_platforms()
PLATAFORMAS_ATIVAS_LIST = get_active_platforms()
