"""
Gerenciador Redis para cache distribuído do sistema Garimpeiro Geek.
Implementa cache inteligente com TTL dinâmico e fallback.
"""

import asyncio
import logging
import json
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import hashlib

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisManager:
    """Gerenciador de cache Redis."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 db: int = 0, password: Optional[str] = None):
        """Inicializa o gerenciador Redis."""
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.logger = logging.getLogger(__name__)
        
        # Cliente Redis
        self.redis_client = None
        self.connected = False
        
        # Cache local como fallback
        self.local_cache = {}
        self.local_cache_ttl = {}
        
        # Estatísticas
        self.stats = {
            "redis_hits": 0,
            "redis_misses": 0,
            "local_hits": 0,
            "local_misses": 0,
            "total_requests": 0
        }
    
    async def connect(self) -> bool:
        """Conecta ao Redis."""
        if not REDIS_AVAILABLE:
            self.logger.warning("Redis não disponível, usando cache local")
            return False
        
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            
            # Testar conexão
            await self.redis_client.ping()
            self.connected = True
            
            self.logger.info(f"✅ Conectado ao Redis: {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao conectar ao Redis: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Desconecta do Redis."""
        if self.redis_client and self.connected:
            await self.redis_client.close()
            self.connected = False
            self.logger.info("🔌 Desconectado do Redis")
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """
        Define um valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            ttl_seconds: Tempo de vida em segundos
            
        Returns:
            True se armazenado com sucesso
        """
        try:
            # Serializar valor
            serialized_value = json.dumps(value, default=str)
            
            if self.connected and self.redis_client:
                # Armazenar no Redis
                await self.redis_client.setex(key, ttl_seconds, serialized_value)
                return True
            else:
                # Fallback para cache local
                self.local_cache[key] = serialized_value
                self.local_cache_ttl[key] = datetime.now() + timedelta(seconds=ttl_seconds)
                return True
                
        except Exception as e:
            self.logger.error(f"Erro ao definir cache: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Obtém um valor do cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor armazenado ou None se não encontrado
        """
        self.stats["total_requests"] += 1
        
        try:
            if self.connected and self.redis_client:
                # Tentar Redis primeiro
                value = await self.redis_client.get(key)
                if value:
                    self.stats["redis_hits"] += 1
                    return json.loads(value)
                else:
                    self.stats["redis_misses"] += 1
            
            # Fallback para cache local
            if key in self.local_cache:
                # Verificar TTL
                if key in self.local_cache_ttl:
                    if datetime.now() < self.local_cache_ttl[key]:
                        self.stats["local_hits"] += 1
                        return json.loads(self.local_cache[key])
                    else:
                        # Expirou, remover
                        del self.local_cache[key]
                        del self.local_cache_ttl[key]
                
                self.stats["local_misses"] += 1
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao obter cache: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """
        Remove uma chave do cache.
        
        Args:
            key: Chave a ser removida
            
        Returns:
            True se removida com sucesso
        """
        try:
            if self.connected and self.redis_client:
                await self.redis_client.delete(key)
            
            # Remover do cache local também
            if key in self.local_cache:
                del self.local_cache[key]
            if key in self.local_cache_ttl:
                del self.local_cache_ttl[key]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao remover cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Verifica se uma chave existe no cache.
        
        Args:
            key: Chave a ser verificada
            
        Returns:
            True se existe
        """
        try:
            if self.connected and self.redis_client:
                return await self.redis_client.exists(key) > 0
            
            return key in self.local_cache
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar existência: {e}")
            return False
    
    async def set_hash(self, key: str, field: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """
        Define um campo de hash no cache.
        
        Args:
            key: Chave do hash
            field: Campo do hash
            value: Valor a ser armazenado
            ttl_seconds: Tempo de vida em segundos
            
        Returns:
            True se armazenado com sucesso
        """
        try:
            serialized_value = json.dumps(value, default=str)
            
            if self.connected and self.redis_client:
                await self.redis_client.hset(key, field, serialized_value)
                await self.redis_client.expire(key, ttl_seconds)
                return True
            else:
                # Fallback para cache local
                hash_key = f"{key}:{field}"
                self.local_cache[hash_key] = serialized_value
                self.local_cache_ttl[hash_key] = datetime.now() + timedelta(seconds=ttl_seconds)
                return True
                
        except Exception as e:
            self.logger.error(f"Erro ao definir hash: {e}")
            return False
    
    async def get_hash(self, key: str, field: str) -> Optional[Any]:
        """
        Obtém um campo de hash do cache.
        
        Args:
            key: Chave do hash
            field: Campo do hash
            
        Returns:
            Valor do campo ou None se não encontrado
        """
        try:
            if self.connected and self.redis_client:
                value = await self.redis_client.hget(key, field)
                if value:
                    return json.loads(value)
            
            # Fallback para cache local
            hash_key = f"{key}:{field}"
            if hash_key in self.local_cache:
                if hash_key in self.local_cache_ttl:
                    if datetime.now() < self.local_cache_ttl[hash_key]:
                        return json.loads(self.local_cache[hash_key])
                    else:
                        del self.local_cache[hash_key]
                        del self.local_cache_ttl[hash_key]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao obter hash: {e}")
            return None
    
    async def increment(self, key: str, amount: int = 1, ttl_seconds: int = 3600) -> Optional[int]:
        """
        Incrementa um contador no cache.
        
        Args:
            key: Chave do contador
            amount: Quantidade a incrementar
            ttl_seconds: Tempo de vida em segundos
            
        Returns:
            Novo valor do contador ou None se falhar
        """
        try:
            if self.connected and self.redis_client:
                value = await self.redis_client.incrby(key, amount)
                await self.redis_client.expire(key, ttl_seconds)
                return value
            else:
                # Fallback para cache local
                current_value = await self.get(key) or 0
                new_value = current_value + amount
                await self.set(key, new_value, ttl_seconds)
                return new_value
                
        except Exception as e:
            self.logger.error(f"Erro ao incrementar contador: {e}")
            return None
    
    async def get_all_keys(self, pattern: str = "*") -> List[str]:
        """
        Obtém todas as chaves que correspondem a um padrão.
        
        Args:
            pattern: Padrão de busca
            
        Returns:
            Lista de chaves encontradas
        """
        try:
            if self.connected and self.redis_client:
                return await self.redis_client.keys(pattern)
            else:
                # Fallback para cache local
                import fnmatch
                return [key for key in self.local_cache.keys() if fnmatch.fnmatch(key, pattern)]
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar chaves: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        stats = self.stats.copy()
        
        # Adicionar informações do Redis
        stats["redis_connected"] = self.connected
        stats["local_cache_size"] = len(self.local_cache)
        
        # Calcular hit rates
        total_hits = stats["redis_hits"] + stats["local_hits"]
        total_misses = stats["redis_misses"] + stats["local_misses"]
        
        if total_hits + total_misses > 0:
            stats["hit_rate"] = total_hits / (total_hits + total_misses)
        else:
            stats["hit_rate"] = 0
        
        return stats
    
    def clear_local_cache(self):
        """Limpa o cache local."""
        self.local_cache.clear()
        self.local_cache_ttl.clear()
        self.logger.info("🗑️ Cache local limpo")
    
    async def health_check(self) -> bool:
        """Verifica saúde do Redis."""
        try:
            if self.connected and self.redis_client:
                await self.redis_client.ping()
                return True
            else:
                # Testar cache local
                test_key = "health_check_test"
                await self.set(test_key, "test", 10)
                value = await self.get(test_key)
                await self.delete(test_key)
                return value == "test"
                
        except Exception as e:
            self.logger.error(f"Health check falhou: {e}")
            return False


# Instância global do gerenciador Redis
redis_manager = RedisManager()

