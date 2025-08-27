"""
Sistema de Conversão de Links de Afiliado
Converte URLs de produtos em links de afiliado
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from .affiliate_cache import AffiliateCache
from .affiliate_validator import AffiliateValidator, ValidationResult


class AffiliateConverter:
    """Converte URLs de produtos em links de afiliado"""

    def __init__(self, cache_url: str = "redis://localhost:6379"):
        self.logger = logging.getLogger("affiliate_converter")

        # Sistema de cache
        self.cache = AffiliateCache(cache_url)

        # Sistema de validação
        self.validator = AffiliateValidator()

        # Configurações de afiliados por loja
        self.affiliate_configs = {
            "amazon": {
                "enabled": True,
                "tag": "garimpeirogeek-20",  # Seu tag de afiliado Amazon
                "domains": ["amazon.com.br", "amazon.com", "amazon.com.mx"],
                "param_name": "tag",
            },
            "magalu": {
                "enabled": True,
                "tag": "garimpeirogeek",  # Seu ID de afiliado Magazine Luiza
                "domains": ["magazineluiza.com.br"],
                "param_name": "partner_id",
            },
            "americanas": {
                "enabled": True,
                "tag": "garimpeirogeek",  # Seu ID de afiliado Americanas
                "domains": ["americanas.com.br"],
                "param_name": "afiliado",
            },
            "submarino": {
                "enabled": True,
                "tag": "garimpeirogeek",  # Seu ID de afiliado Submarino
                "domains": ["submarino.com.br"],
                "param_name": "afiliado",
            },
            "casasbahia": {
                "enabled": True,
                "tag": "garimpeirogeek",  # Seu ID de afiliado Casas Bahia
                "domains": ["casasbahia.com.br"],
                "param_name": "afiliado",
            },
            "extra": {
                "enabled": True,
                "tag": "garimpeirogeek",  # Seu ID de afiliado Extra
                "domains": ["extra.com.br"],
                "param_name": "afiliado",
            },
            "shoptime": {
                "enabled": True,
                "tag": "garimpeirogeek",  # Seu ID de afiliado Shoptime
                "domains": ["shoptime.com.br"],
                "param_name": "afiliado",
            },
            "ponto": {
                "enabled": True,
                "tag": "garimpeirogeek",  # Seu ID de afiliado Ponto
                "domains": ["ponto.com.br"],
                "param_name": "afiliado",
            },
        }

    def identify_store(self, url: str) -> Optional[str]:
        """
        Identifica a loja baseada na URL

        Args:
            url: URL do produto

        Returns:
            Nome da loja ou None se não reconhecida
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            for store, config in self.affiliate_configs.items():
                if any(store_domain in domain for store_domain in config["domains"]):
                    return store

            return None

        except Exception as e:
            self.logger.error(f"Erro ao identificar loja da URL {url}: {e}")
            return None

    async def convert_to_affiliate(self, url: str, store: Optional[str] = None) -> str:
        """
        Converte uma URL em link de afiliado

        Args:
            url: URL original do produto
            store: Nome da loja (opcional, será detectado automaticamente)

        Returns:
            URL convertida para afiliado
        """
        if not store:
            store = self.identify_store(url)

        if not store or store not in self.affiliate_configs:
            self.logger.warning(f"Loja não suportada para conversão: {store}")
            return url

        config = self.affiliate_configs[store]
        if not config["enabled"]:
            self.logger.info(f"Conversão de afiliado desabilitada para {store}")
            return url

        # Verificar cache primeiro
        cached_result = await self.cache.get(store, url)
        if cached_result:
            self.logger.debug(f"Cache hit para {store}: {url[:50]}...")
            return cached_result["affiliate_url"]

        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)

            # Adicionar parâmetro de afiliado
            query_params[config["param_name"]] = [config["tag"]]

            # Reconstruir URL
            new_query = urlencode(query_params, doseq=True)
            new_url = urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment,
                )
            )

            # Armazenar no cache
            await self.cache.set(store, url, new_url, metadata={"store": store})

            self.logger.info(f"URL convertida para afiliado: {store} -> {new_url}")
            return new_url

        except Exception as e:
            self.logger.error(f"Erro ao converter URL para afiliado: {e}")
            return url

    async def convert_offers_batch(self, offers: list) -> list:
        """
        Converte um lote de ofertas para links de afiliado

        Args:
            offers: Lista de ofertas

        Returns:
            Lista de ofertas com URLs convertidas
        """
        converted_offers = []

        for offer in offers:
            if "url" in offer and offer["url"]:
                original_url = offer["url"]
                affiliate_url = await self.convert_to_affiliate(original_url)

                # Criar cópia da oferta com URL convertida
                converted_offer = offer.copy()
                converted_offer["affiliate_url"] = affiliate_url
                converted_offer["original_url"] = original_url

                converted_offers.append(converted_offer)
            else:
                converted_offers.append(offer)

        self.logger.info(
            f"Convertidas {len(converted_offers)} ofertas para links de afiliado"
        )
        return converted_offers

    def update_affiliate_config(self, store: str, config: Dict[str, Any]):
        """
        Atualiza configuração de afiliado para uma loja

        Args:
            store: Nome da loja
            config: Nova configuração
        """
        if store in self.affiliate_configs:
            self.affiliate_configs[store].update(config)
            self.logger.info(f"Configuração de afiliado atualizada para {store}")
        else:
            self.logger.warning(f"Loja {store} não encontrada para atualização")

    def get_affiliate_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos afiliados configurados"""
        stats = {
            "total_stores": len(self.affiliate_configs),
            "enabled_stores": sum(
                1 for config in self.affiliate_configs.values() if config["enabled"]
            ),
            "disabled_stores": sum(
                1 for config in self.affiliate_configs.values() if not config["enabled"]
            ),
            "stores": {},
        }

        for store, config in self.affiliate_configs.items():
            stats["stores"][store] = {
                "enabled": config["enabled"],
                "tag": config["tag"],
                "domains": config["domains"],
            }

        return stats

    async def validate_conversion(
        self, original_url: str, affiliate_url: str
    ) -> ValidationResult:
        """
        Valida uma conversão específica

        Args:
            original_url: URL original
            affiliate_url: URL de afiliado

        Returns:
            Resultado da validação
        """
        return self.validator.validate_conversion(original_url, affiliate_url)

    async def validate_batch(
        self, conversions: List[Dict[str, str]]
    ) -> List[ValidationResult]:
        """
        Valida um lote de conversões

        Args:
            conversions: Lista de conversões para validar

        Returns:
            Lista de resultados de validação
        """
        return self.validator.validate_batch(conversions)

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        return await self.cache.get_stats()

    async def clear_cache(self, platform: Optional[str] = None) -> int:
        """
        Limpa cache

        Args:
            platform: Plataforma específica ou None para limpar tudo

        Returns:
            Número de itens removidos
        """
        if platform:
            return await self.cache.clear_platform(platform)
        else:
            return await self.cache.clear_all()

    async def connect_cache(self) -> bool:
        """Conecta ao sistema de cache"""
        return await self.cache.connect()

    async def disconnect_cache(self):
        """Desconecta do sistema de cache"""
        await self.cache.disconnect()

    async def test_conversion(self, url: str) -> Dict[str, Any]:
        """
        Testa a conversão de uma URL específica

        Args:
            url: URL para testar

        Returns:
            Dicionário com resultados do teste
        """
        store = self.identify_store(url)
        original_url = url
        affiliate_url = await self.convert_to_affiliate(url, store)

        # Validar conversão
        validation_result = self.validator.validate_conversion(
            original_url, affiliate_url, store
        )

        return {
            "original_url": original_url,
            "affiliate_url": affiliate_url,
            "store": store,
            "converted": original_url != affiliate_url,
            "config": self.affiliate_configs.get(store, {}) if store else None,
            "validation": {
                "status": validation_result.status.value,
                "message": validation_result.message,
                "score": validation_result.score,
                "details": validation_result.details,
            },
        }
