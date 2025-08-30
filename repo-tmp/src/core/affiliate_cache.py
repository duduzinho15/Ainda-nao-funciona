"""
Sistema de Cache Redis para Conversores de Afiliados
Gerencia cache distribuído com TTL configurável
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class AffiliateCache:
    """Sistema de cache Redis para conversores de afiliados"""

    def __init__(self, redis_url: str = "redis://localhost:6379", ttl: int = 86400):
        """
        Inicializa o cache Redis

        Args:
            redis_url: URL de conexão com Redis
            ttl: Tempo de vida padrão em segundos (24h por padrão)
        """
        self.redis_url = redis_url
        self.default_ttl = ttl
        self.redis_client = None
        self.is_connected = False

        if not REDIS_AVAILABLE:
            logger.warning("Redis não disponível, usando cache em memória")
            self._fallback_cache = {}
            self._fallback_timestamps = {}

    async def connect(self) -> bool:
        """Conecta ao Redis"""
        if not REDIS_AVAILABLE:
            return False

        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            self.is_connected = True
            logger.info("Conectado ao Redis com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Desconecta do Redis"""
        if self.redis_client and self.is_connected:
            await self.redis_client.close()
            self.is_connected = False
            logger.info("Desconectado do Redis")

    def _generate_cache_key(self, platform: str, original_url: str) -> str:
        """Gera chave de cache única"""
        url_hash = hashlib.md5(original_url.encode()).hexdigest()
        return f"affiliate:{platform}:{url_hash}"

    async def get(self, platform: str, original_url: str) -> Optional[Dict[str, Any]]:
        """
        Obtém item do cache

        Args:
            platform: Plataforma (amazon, mercadolivre, etc.)
            original_url: URL original do produto

        Returns:
            Dados do cache ou None se não encontrado
        """
        if not self.is_connected:
            return self._fallback_get(platform, original_url)

        try:
            cache_key = self._generate_cache_key(platform, original_url)
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Cache hit para {platform}: {original_url[:50]}...")
                return data

            logger.debug(f"Cache miss para {platform}: {original_url[:50]}...")
            return None

        except Exception as e:
            logger.error(f"Erro ao obter do cache Redis: {e}")
            return self._fallback_get(platform, original_url)

    async def set(
        self,
        platform: str,
        original_url: str,
        affiliate_url: str,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Armazena item no cache

        Args:
            platform: Plataforma
            original_url: URL original
            affiliate_url: URL de afiliado
            metadata: Metadados adicionais
            ttl: Tempo de vida em segundos

        Returns:
            True se armazenado com sucesso
        """
        if not self.is_connected:
            return self._fallback_set(
                platform, original_url, affiliate_url, metadata, ttl
            )

        try:
            cache_key = self._generate_cache_key(platform, original_url)

            cache_data = {
                "platform": platform,
                "original_url": original_url,
                "affiliate_url": affiliate_url,
                "created_at": datetime.now().isoformat(),
                "metadata": metadata or {},
            }

            ttl_seconds = ttl or self.default_ttl
            await self.redis_client.setex(
                cache_key, ttl_seconds, json.dumps(cache_data)
            )

            logger.debug(
                f"Item armazenado no cache: {platform}: {original_url[:50]}..."
            )
            return True

        except Exception as e:
            logger.error(f"Erro ao armazenar no cache Redis: {e}")
            return self._fallback_set(
                platform, original_url, affiliate_url, metadata, ttl
            )

    async def delete(self, platform: str, original_url: str) -> bool:
        """Remove item do cache"""
        if not self.is_connected:
            return self._fallback_delete(platform, original_url)

        try:
            cache_key = self._generate_cache_key(platform, original_url)
            await self.redis_client.delete(cache_key)
            logger.debug(f"Item removido do cache: {platform}: {original_url[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Erro ao remover do cache Redis: {e}")
            return self._fallback_delete(platform, original_url)

    async def exists(self, platform: str, original_url: str) -> bool:
        """Verifica se item existe no cache"""
        if not self.is_connected:
            return self._fallback_exists(platform, original_url)

        try:
            cache_key = self._generate_cache_key(platform, original_url)
            return await self.redis_client.exists(cache_key) > 0
        except Exception as e:
            logger.error(f"Erro ao verificar existência no cache Redis: {e}")
            return self._fallback_exists(platform, original_url)

    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        if not self.is_connected:
            return self._fallback_stats()

        try:
            # Contar chaves por plataforma
            platform_keys = {}
            total_keys = 0

            async for key in self.redis_client.scan_iter(match="affiliate:*"):
                total_keys += 1
                parts = key.decode().split(":")
                if len(parts) >= 3:
                    platform = parts[1]
                    platform_keys[platform] = platform_keys.get(platform, 0) + 1

            return {
                "total_keys": total_keys,
                "platforms": platform_keys,
                "redis_connected": True,
                "cache_type": "redis",
            }

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do Redis: {e}")
            return self._fallback_stats()

    async def clear_platform(self, platform: str) -> int:
        """Limpa cache de uma plataforma específica"""
        if not self.is_connected:
            return self._fallback_clear_platform(platform)

        try:
            deleted_count = 0
            async for key in self.redis_client.scan_iter(
                match=f"affiliate:{platform}:*"
            ):
                await self.redis_client.delete(key)
                deleted_count += 1

            logger.info(
                f"Cache limpo para plataforma {platform}: {deleted_count} itens removidos"
            )
            return deleted_count

        except Exception as e:
            logger.error(f"Erro ao limpar cache da plataforma {platform}: {e}")
            return self._fallback_clear_platform(platform)

    async def clear_all(self) -> int:
        """Limpa todo o cache"""
        if not self.is_connected:
            return self._fallback_clear_all()

        try:
            deleted_count = 0
            async for key in self.redis_client.scan_iter(match="affiliate:*"):
                await self.redis_client.delete(key)
                deleted_count += 1

            logger.info(f"Cache limpo completamente: {deleted_count} itens removidos")
            return deleted_count

        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return self._fallback_clear_all()

    # Métodos de fallback para quando Redis não está disponível
    def _fallback_get(
        self, platform: str, original_url: str
    ) -> Optional[Dict[str, Any]]:
        """Fallback para cache em memória"""
        cache_key = f"{platform}:{original_url}"
        if cache_key in self._fallback_cache:
            timestamp = self._fallback_timestamps[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.default_ttl):
                return self._fallback_cache[cache_key]
            else:
                # Expirou, remover
                del self._fallback_cache[cache_key]
                del self._fallback_timestamps[cache_key]
        return None

    def _fallback_set(
        self,
        platform: str,
        original_url: str,
        affiliate_url: str,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
    ) -> bool:
        """Fallback para cache em memória"""
        cache_key = f"{platform}:{original_url}"
        cache_data = {
            "platform": platform,
            "original_url": original_url,
            "affiliate_url": affiliate_url,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        self._fallback_cache[cache_key] = cache_data
        self._fallback_timestamps[cache_key] = datetime.now()
        return True

    def _fallback_delete(self, platform: str, original_url: str) -> bool:
        """Fallback para cache em memória"""
        cache_key = f"{platform}:{original_url}"
        if cache_key in self._fallback_cache:
            del self._fallback_cache[cache_key]
            del self._fallback_timestamps[cache_key]
            return True
        return False

    def _fallback_exists(self, platform: str, original_url: str) -> bool:
        """Fallback para cache em memória"""
        cache_key = f"{platform}:{original_url}"
        return cache_key in self._fallback_cache

    def _fallback_stats(self) -> Dict[str, Any]:
        """Fallback para estatísticas em memória"""
        platform_keys = {}
        for key in self._fallback_cache.keys():
            platform = key.split(":")[0]
            platform_keys[platform] = platform_keys.get(platform, 0) + 1

        return {
            "total_keys": len(self._fallback_cache),
            "platforms": platform_keys,
            "redis_connected": False,
            "cache_type": "memory",
        }

    def _fallback_clear_platform(self, platform: str) -> int:
        """Fallback para limpeza em memória"""
        deleted_count = 0
        keys_to_delete = []

        for key in self._fallback_cache.keys():
            if key.startswith(f"{platform}:"):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self._fallback_cache[key]
            del self._fallback_timestamps[key]
            deleted_count += 1

        return deleted_count

    def _fallback_clear_all(self) -> int:
        """Fallback para limpeza completa em memória"""
        deleted_count = len(self._fallback_cache)
        self._fallback_cache.clear()
        self._fallback_timestamps.clear()
        return deleted_count

    async def __aenter__(self):
        """Context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.disconnect()
