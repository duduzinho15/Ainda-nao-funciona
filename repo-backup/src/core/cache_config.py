"""
Configuração de Cache para Produção
Define TTLs apropriados por plataforma e configurações de produção
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class CacheStrategy(Enum):
    """Estratégias de cache disponíveis"""

    AGGRESSIVE = "aggressive"  # Cache por mais tempo
    BALANCED = "balanced"  # Cache equilibrado
    CONSERVATIVE = "conservative"  # Cache por menos tempo


@dataclass
class PlatformCacheConfig:
    """Configuração de cache para uma plataforma específica"""

    platform: str
    ttl_seconds: int
    max_retries: int
    strategy: CacheStrategy
    priority: int
    fallback_ttl: int
    compression: bool
    encryption: bool


class ProductionCacheConfig:
    """Configuração de cache para produção"""

    def __init__(self):
        # TTLs baseados em análise de comportamento das plataformas
        self.platform_configs = {
            "amazon": PlatformCacheConfig(
                platform="amazon",
                ttl_seconds=3600,  # 1 hora - preços mudam frequentemente
                max_retries=3,
                strategy=CacheStrategy.BALANCED,
                priority=1,
                fallback_ttl=1800,  # 30 min fallback
                compression=True,
                encryption=False,
            ),
            "mercadolivre": PlatformCacheConfig(
                platform="mercadolivre",
                ttl_seconds=7200,  # 2 horas - preços mais estáveis
                max_retries=3,
                strategy=CacheStrategy.BALANCED,
                priority=2,
                fallback_ttl=3600,  # 1 hora fallback
                compression=True,
                encryption=False,
            ),
            "shopee": PlatformCacheConfig(
                platform="shopee",
                ttl_seconds=5400,  # 1.5 horas - preços intermediários
                max_retries=3,
                strategy=CacheStrategy.BALANCED,
                priority=2,
                fallback_ttl=2700,  # 45 min fallback
                compression=True,
                encryption=False,
            ),
            "magazineluiza": PlatformCacheConfig(
                platform="magazineluiza",
                ttl_seconds=10800,  # 3 horas - preços muito estáveis
                max_retries=2,
                strategy=CacheStrategy.AGGRESSIVE,
                priority=3,
                fallback_ttl=5400,  # 1.5 horas fallback
                compression=True,
                encryption=False,
            ),
            "aliexpress": PlatformCacheConfig(
                platform="aliexpress",
                ttl_seconds=1800,  # 30 min - preços mudam muito
                max_retries=5,
                strategy=CacheStrategy.CONSERVATIVE,
                priority=1,
                fallback_ttl=900,  # 15 min fallback
                compression=True,
                encryption=False,
            ),
            "awin": PlatformCacheConfig(
                platform="awin",
                ttl_seconds=14400,  # 4 horas - links estáveis
                max_retries=2,
                strategy=CacheStrategy.AGGRESSIVE,
                priority=4,
                fallback_ttl=7200,  # 2 horas fallback
                compression=True,
                encryption=False,
            ),
            "rakuten": PlatformCacheConfig(
                platform="rakuten",
                ttl_seconds=14400,  # 4 horas - links estáveis
                max_retries=2,
                strategy=CacheStrategy.AGGRESSIVE,
                priority=4,
                fallback_ttl=7200,  # 2 horas fallback
                compression=True,
                encryption=False,
            ),
        }

        # Configurações globais de produção
        self.global_config = {
            "redis_url": "redis://localhost:6379",
            "redis_password": None,
            "redis_db": 0,
            "connection_pool_size": 20,
            "connection_timeout": 5.0,
            "socket_timeout": 5.0,
            "socket_connect_timeout": 5.0,
            "retry_on_timeout": True,
            "health_check_interval": 30,
            "max_connection_retries": 3,
            "circuit_breaker_threshold": 5,
            "circuit_breaker_timeout": 60,
            "compression_threshold": 1024,  # 1KB
            "encryption_enabled": False,
            "backup_enabled": True,
            "backup_interval": 3600,  # 1 hora
            "metrics_enabled": True,
            "metrics_interval": 60,  # 1 minuto
            "alerting_enabled": True,
            "alert_thresholds": {
                "cache_hit_rate": 0.8,  # 80%
                "response_time": 100,  # 100ms
                "error_rate": 0.05,  # 5%
                "memory_usage": 0.9,  # 90%
            },
        }

    def get_platform_config(self, platform: str) -> Optional[PlatformCacheConfig]:
        """Retorna configuração de cache para uma plataforma"""
        return self.platform_configs.get(platform.lower())

    def get_ttl_for_platform(self, platform: str) -> int:
        """Retorna TTL em segundos para uma plataforma"""
        config = self.get_platform_config(platform)
        if config:
            return config.ttl_seconds
        return self.global_config.get("default_ttl", 3600)

    def get_fallback_ttl_for_platform(self, platform: str) -> int:
        """Retorna TTL de fallback para uma plataforma"""
        config = self.get_platform_config(platform)
        if config:
            return config.fallback_ttl
        return self.global_config.get("default_fallback_ttl", 1800)

    def get_compression_enabled(self, platform: str) -> bool:
        """Retorna se compressão está habilitada para uma plataforma"""
        config = self.get_platform_config(platform)
        if config:
            return config.compression
        compression_threshold = self.global_config.get("compression_threshold", 1024)
        return (
            isinstance(compression_threshold, (int, float))
            and compression_threshold > 0
        )

    def get_encryption_enabled(self, platform: str) -> bool:
        """Retorna se criptografia está habilitada para uma plataforma"""
        config = self.get_platform_config(platform)
        if config:
            return config.encryption
        return self.global_config.get("encryption_enabled", False)

    def get_priority_for_platform(self, platform: str) -> int:
        """Retorna prioridade de cache para uma plataforma"""
        config = self.get_platform_config(platform)
        if config:
            return config.priority
        return 5  # Prioridade padrão

    def get_max_retries_for_platform(self, platform: str) -> int:
        """Retorna número máximo de tentativas para uma plataforma"""
        config = self.get_platform_config(platform)
        if config:
            return config.max_retries
        return 3  # Padrão

    def get_strategy_for_platform(self, platform: str) -> CacheStrategy:
        """Retorna estratégia de cache para uma plataforma"""
        config = self.get_platform_config(platform)
        if config:
            return config.strategy
        return CacheStrategy.BALANCED

    def get_global_config(self) -> Dict[str, Any]:
        """Retorna configuração global"""
        return self.global_config.copy()

    def update_global_config(self, updates: Dict[str, Any]) -> None:
        """Atualiza configuração global"""
        self.global_config.update(updates)

    def get_all_platforms(self) -> List[str]:
        """Retorna lista de todas as plataformas configuradas"""
        return list(self.platform_configs.keys())

    def get_cache_stats_config(self) -> Dict[str, Any]:
        """Retorna configuração para estatísticas de cache"""
        return {
            "enabled": self.global_config.get("metrics_enabled", True),
            "interval": self.global_config.get("metrics_interval", 60),
            "platforms": self.get_all_platforms(),
            "alert_thresholds": self.global_config.get("alert_thresholds", {}),
            "health_check_interval": self.global_config.get(
                "health_check_interval", 30
            ),
        }


# Instância global da configuração
production_cache_config = ProductionCacheConfig()
