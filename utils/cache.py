# -*- coding: utf-8 -*-
"""
Sistema de Cache TTL Assíncrono com Coalescência para Garimpeiro Geek

Este módulo implementa um cache inteligente que:
- Gerencia TTL (Time To Live) para entradas
- Implementa coalescência para evitar requisições duplicadas
- Suporta operações assíncronas
- Fornece decorator @cached para funções
"""

import asyncio
import time
import hashlib
import logging
from typing import Any, Callable, Dict, Optional, Union, TypeVar
from functools import wraps
from dataclasses import dataclass
from collections import OrderedDict

logger = logging.getLogger(__name__)

# Type variables para generics
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

@dataclass
class CacheEntry:
    """Entrada individual do cache com TTL e dados"""
    value: Any
    timestamp: float
    ttl: float
    access_count: int = 0
    last_accessed: float = 0.0

class AsyncTTLCache:
    """
    Cache TTL assíncrono com coalescência para evitar requisições duplicadas
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0):
        """
        Inicializa o cache
        
        Args:
            max_size: Número máximo de entradas no cache
            default_ttl: TTL padrão em segundos (5 minutos)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()
        
        logger.info(f"🔄 Cache TTL inicializado: max_size={max_size}, default_ttl={default_ttl}s")
    
    def _generate_key(self, *args, **kwargs) -> str:
        """
        Gera chave única para os argumentos da função
        
        Args:
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados
            
        Returns:
            Chave hash única
        """
        # Converte argumentos para string e gera hash
        key_parts = []
        
        # Adiciona argumentos posicionais
        for arg in args:
            key_parts.append(str(arg))
        
        # Adiciona argumentos nomeados ordenados
        for key in sorted(kwargs.keys()):
            key_parts.append(f"{key}={kwargs[key]}")
        
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """
        Verifica se uma entrada do cache expirou
        
        Args:
            entry: Entrada do cache
            
        Returns:
            True se expirou, False caso contrário
        """
        return time.time() - entry.timestamp > entry.ttl
    
    def _cleanup_expired(self):
        """Remove entradas expiradas do cache"""
        expired_keys = []
        current_time = time.time()
        
        for key, entry in self._cache.items():
            if current_time - entry.timestamp > entry.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"🧹 Cache cleanup: {len(expired_keys)} entradas expiradas removidas")
    
    def _evict_lru(self):
        """Remove entradas menos recentemente usadas se o cache estiver cheio"""
        if len(self._cache) >= self.max_size:
            # Remove a entrada mais antiga (LRU)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"🗑️ Cache eviction: entrada mais antiga removida")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Obtém valor do cache se não expirou
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor do cache ou None se não existir/expirou
        """
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                if self._is_expired(entry):
                    # Remove entrada expirada
                    del self._cache[key]
                    logger.debug(f"⏰ Cache miss (expired): {key}")
                    return None
                
                # Atualiza estatísticas de acesso
                entry.access_count += 1
                entry.last_accessed = time.time()
                
                # Move para o final (LRU)
                self._cache.move_to_end(key)
                
                logger.debug(f"✅ Cache hit: {key} (acessos: {entry.access_count})")
                return entry.value
            
            logger.debug(f"❌ Cache miss: {key}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Define valor no cache com TTL
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            ttl: TTL em segundos (usa default se None)
        """
        async with self._lock:
            ttl = ttl or self.default_ttl
            current_time = time.time()
            
            # Limpa entradas expiradas
            self._cleanup_expired()
            
            # Evita entrada se o cache estiver cheio
            self._evict_lru()
            
            # Cria nova entrada
            entry = CacheEntry(
                value=value,
                timestamp=current_time,
                ttl=ttl,
                access_count=1,
                last_accessed=current_time
            )
            
            # Remove entrada existente se houver
            if key in self._cache:
                del self._cache[key]
            
            # Adiciona nova entrada
            self._cache[key] = entry
            
            logger.debug(f"💾 Cache set: {key} (TTL: {ttl}s)")
    
    async def delete(self, key: str) -> bool:
        """
        Remove entrada do cache
        
        Args:
            key: Chave a ser removida
            
        Returns:
            True se removida, False se não existia
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"🗑️ Cache delete: {key}")
                return True
            return False
    
    async def clear(self) -> None:
        """Limpa todo o cache"""
        async with self._lock:
            self._cache.clear()
            self._pending_requests.clear()
            logger.info("🧹 Cache completamente limpo")
    
    async def stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache
        
        Returns:
            Dicionário com estatísticas
        """
        async with self._lock:
            current_time = time.time()
            total_entries = len(self._cache)
            expired_entries = sum(1 for entry in self._cache.values() 
                               if self._is_expired(entry))
            active_entries = total_entries - expired_entries
            
            # Calcula estatísticas de acesso
            total_accesses = sum(entry.access_count for entry in self._cache.values())
            avg_accesses = total_accesses / total_entries if total_entries > 0 else 0
            
            # Encontra entrada mais acessada
            most_accessed = max(self._cache.values(), key=lambda x: x.access_count) if self._cache else None
            
            return {
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "pending_requests": len(self._pending_requests),
                "total_accesses": total_accesses,
                "average_accesses": round(avg_accesses, 2),
                "most_accessed_key": most_accessed.access_count if most_accessed else 0,
                "cache_size_bytes": sum(len(str(entry.value)) for entry in self._cache.values()),
                "memory_usage_mb": round(sum(len(str(entry.value)) for entry in self._cache.values()) / 1024 / 1024, 2)
            }
    
    async def cached_async(self, func: Callable[..., Any], ttl: Optional[float] = None) -> Callable[..., Any]:
        """
        Decorator para cache de funções assíncronas com coalescência
        
        Args:
            func: Função a ser cacheada
            ttl: TTL específico para esta função
            
        Returns:
            Função wrapper com cache
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gera chave única para os argumentos
            cache_key = self._generate_key(func.__name__, *args, **kwargs)
            
            # Verifica se já existe uma requisição pendente para esta chave
            if cache_key in self._pending_requests:
                logger.debug(f"🔄 Coalescing request: {cache_key}")
                try:
                    # Aguarda a requisição pendente
                    result = await self._pending_requests[cache_key]
                    logger.debug(f"✅ Coalesced result: {cache_key}")
                    return result
                except Exception as e:
                    # Remove requisição falhada
                    if cache_key in self._pending_requests:
                        del self._pending_requests[cache_key]
                    raise e
            
            # Verifica cache primeiro
            cached_value = await self.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Cria futura para esta requisição
            future = asyncio.Future()
            self._pending_requests[cache_key] = future
            
            try:
                # Executa a função
                result = await func(*args, **kwargs)
                
                # Armazena no cache
                await self.set(cache_key, result, ttl)
                
                # Resolve a futura
                future.set_result(result)
                
                logger.debug(f"🚀 New request completed: {cache_key}")
                return result
                
            except Exception as e:
                # Marca a futura como falhada
                future.set_exception(e)
                raise e
            finally:
                # Remove da lista de pendentes
                if cache_key in self._pending_requests:
                    del self._pending_requests[cache_key]
        
        return wrapper

# Instância global do cache
_cache_instance: Optional[AsyncTTLCache] = None

def get_cache() -> AsyncTTLCache:
    """
    Retorna instância global do cache
    
    Returns:
        Instância do cache
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = AsyncTTLCache()
    return _cache_instance

def cached(ttl: Optional[float] = None):
    """
    Decorator para cache de funções assíncronas
    
    Args:
        ttl: TTL específico para a função
        
    Returns:
        Decorator de cache
    """
    def decorator(func: F) -> F:
        cache_instance = get_cache()
        return cache_instance.cached_async(func, ttl)
    return decorator

# Funções de conveniência para cache síncrono
def cached_sync(ttl: Optional[float] = None):
    """
    Decorator para cache de funções síncronas
    
    Args:
        ttl: TTL específico para a função
        
    Returns:
        Decorator de cache síncrono
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cache_instance = get_cache()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gera chave única
            cache_key = cache_instance._generate_key(func.__name__, *args, **kwargs)
            
            # Verifica cache (síncrono)
            if cache_key in cache_instance._cache:
                entry = cache_instance._cache[cache_key]
                if not cache_instance._is_expired(entry):
                    entry.access_count += 1
                    entry.last_accessed = time.time()
                    cache_instance._cache.move_to_end(cache_key)
                    return entry.value
            
            # Executa função e armazena no cache
            result = func(*args, **kwargs)
            
            # Usa asyncio.run para operações assíncronas do cache
            try:
                asyncio.create_task(cache_instance.set(cache_key, result, ttl))
            except RuntimeError:
                # Se não há loop de eventos, executa síncrono
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(cache_instance.set(cache_key, result, ttl))
                finally:
                    loop.close()
            
            return result
        
        return wrapper
    return decorator

# Função para limpeza periódica do cache
async def cleanup_cache_periodically(interval: float = 60.0):
    """
    Executa limpeza periódica do cache
    
    Args:
        interval: Intervalo entre limpezas em segundos
    """
    cache = get_cache()
    while True:
        try:
            await asyncio.sleep(interval)
            async with cache._lock:
                cache._cleanup_expired()
                logger.debug("🧹 Limpeza periódica do cache executada")
        except Exception as e:
            logger.error(f"❌ Erro na limpeza periódica do cache: {e}")

# Função para estatísticas periódicas
async def log_cache_stats_periodically(interval: float = 300.0):
    """
    Loga estatísticas do cache periodicamente
    
    Args:
        interval: Intervalo entre logs em segundos
    """
    cache = get_cache()
    while True:
        try:
            await asyncio.sleep(interval)
            stats = await cache.stats()
            logger.info(f"📊 Cache Stats: {stats['active_entries']}/{stats['total_entries']} "
                       f"entradas ativas, {stats['pending_requests']} requisições pendentes, "
                       f"{stats['memory_usage_mb']}MB de uso")
        except Exception as e:
            logger.error(f"❌ Erro ao logar estatísticas do cache: {e}")

if __name__ == "__main__":
    # Teste do cache
    async def test_cache():
        cache = AsyncTTLCache(max_size=10, default_ttl=5.0)
        
        # Teste básico
        await cache.set("test", "value", 2.0)
        value = await cache.get("test")
        print(f"Teste básico: {value}")
        
        # Teste TTL
        await asyncio.sleep(3.0)
        value = await cache.get("test")
        print(f"Após TTL: {value}")
        
        # Teste estatísticas
        stats = await cache.stats()
        print(f"Estatísticas: {stats}")
    
    asyncio.run(test_cache())
