"""
Sistema de cache para ASINs da Amazon
Integrado com aff_cache.sqlite para evitar reprocessamento
"""

import hashlib
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AsinCache:
    """Cache para ASINs da Amazon com TTL e persistência"""

    def __init__(self, cache_db_path: str = "aff_cache"):
        self.cache_db_path = Path(cache_db_path)

        # Se o caminho for um arquivo existente, usar diretamente
        if self.cache_db_path.exists() and self.cache_db_path.is_file():
            # É um arquivo, usar como está
            pass
        elif self.cache_db_path.exists() and self.cache_db_path.is_dir():
            # Se for diretório, criar arquivo SQLite dentro
            self.cache_db_path = self.cache_db_path / "aff_cache.sqlite"
        else:
            # Criar diretório pai se não existir
            try:
                self.cache_db_path.parent.mkdir(parents=True, exist_ok=True)
            except FileExistsError:
                # Ignorar erro se o diretório já existir
                pass

        self._init_cache_db()

    def _init_cache_db(self):
        """Inicializa o banco de cache se não existir"""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()

                # Tabela para cache de ASINs
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS asin_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url_hash TEXT UNIQUE NOT NULL,
                        original_url TEXT NOT NULL,
                        asin TEXT NOT NULL,
                        strategy_used TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        expires_at DATETIME NOT NULL,
                        metadata TEXT
                    )
                """
                )

                # Índices para performance
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_asin_cache_url_hash
                    ON asin_cache(url_hash)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_asin_cache_expires
                    ON asin_cache(expires_at)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_asin_cache_asin
                    ON asin_cache(asin)
                """
                )

                conn.commit()
                logger.info("Banco de cache ASIN inicializado")

        except Exception as e:
            logger.error(f"Erro ao inicializar cache ASIN: {e}")

    def _hash_url(self, url: str) -> str:
        """Gera hash único para a URL"""
        return hashlib.sha256(url.encode()).hexdigest()

    def get_cached_asin(
        self, url: str, ttl_hours: int = 24
    ) -> Optional[Dict[str, Any]]:
        """
        Busca ASIN em cache

        Args:
            url: URL da Amazon
            ttl_hours: Tempo de vida do cache em horas

        Returns:
            Dicionário com ASIN e metadados, ou None se não encontrado/expirado
        """
        try:
            url_hash = self._hash_url(url)

            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()

                # Buscar ASIN válido (não expirado)
                cursor.execute(
                    """
                    SELECT asin, strategy_used, created_at, metadata
                    FROM asin_cache
                    WHERE url_hash = ? AND expires_at > datetime('now')
                """,
                    (url_hash,),
                )

                result = cursor.fetchone()
                if result:
                    asin, strategy, created_at, metadata = result

                    logger.debug(
                        f"ASIN encontrado em cache: {asin} (estratégia: {strategy})"
                    )

                    return {
                        "asin": asin,
                        "strategy_used": strategy,
                        "cached_at": created_at,
                        "metadata": metadata,
                        "from_cache": True,
                    }

                return None

        except Exception as e:
            logger.error(f"Erro ao buscar ASIN em cache: {e}")
            return None

    def cache_asin(
        self,
        url: str,
        asin: str,
        strategy_used: str,
        ttl_hours: int = 24,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Armazena ASIN no cache

        Args:
            url: URL da Amazon
            asin: ASIN extraído
            strategy_used: Estratégia utilizada (url, html, playwright)
            ttl_hours: Tempo de vida do cache em horas
            metadata: Metadados adicionais
        """
        try:
            url_hash = self._hash_url(url)
            expires_at = datetime.now() + timedelta(hours=ttl_hours)

            # Serializar metadados
            metadata_json = None
            if metadata:
                import json

                metadata_json = json.dumps(metadata)

            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()

                # Inserir ou atualizar cache
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO asin_cache
                    (url_hash, original_url, asin, strategy_used, expires_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (url_hash, url, asin, strategy_used, expires_at, metadata_json),
                )

                conn.commit()
                logger.debug(
                    f"ASIN {asin} armazenado em cache (estratégia: {strategy_used})"
                )

        except Exception as e:
            logger.error(f"Erro ao armazenar ASIN em cache: {e}")

    def invalidate_cache(self, url: str = None, asin: str = None):
        """
        Invalida entradas do cache

        Args:
            url: URL específica para invalidar (opcional)
            asin: ASIN específico para invalidar (opcional)
        """
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()

                if url:
                    url_hash = self._hash_url(url)
                    cursor.execute(
                        "DELETE FROM asin_cache WHERE url_hash = ?", (url_hash,)
                    )
                    logger.info(f"Cache invalidado para URL: {url}")
                elif asin:
                    cursor.execute("DELETE FROM asin_cache WHERE asin = ?", (asin,))
                    logger.info(f"Cache invalidado para ASIN: {asin}")
                else:
                    # Limpar todo o cache
                    cursor.execute("DELETE FROM asin_cache")
                    logger.info("Todo o cache ASIN foi limpo")

                conn.commit()

        except Exception as e:
            logger.error(f"Erro ao invalidar cache: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()

                # Total de entradas
                cursor.execute("SELECT COUNT(*) FROM asin_cache")
                total_entries = cursor.fetchone()[0]

                # Entradas válidas (não expiradas)
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM asin_cache
                    WHERE expires_at > datetime('now')
                """
                )
                valid_entries = cursor.fetchone()[0]

                # Entradas expiradas
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM asin_cache
                    WHERE expires_at <= datetime('now')
                """
                )
                expired_entries = cursor.fetchone()[0]

                # Estratégias utilizadas
                cursor.execute(
                    """
                    SELECT strategy_used, COUNT(*)
                    FROM asin_cache
                    WHERE expires_at > datetime('now')
                    GROUP BY strategy_used
                """
                )
                strategy_counts = dict(cursor.fetchall())

                # ASINs únicos
                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT asin)
                    FROM asin_cache
                    WHERE expires_at > datetime('now')
                """
                )
                unique_asins = cursor.fetchone()[0]

                return {
                    "total_entries": total_entries,
                    "valid_entries": valid_entries,
                    "expired_entries": expired_entries,
                    "unique_asins": unique_asins,
                    "strategy_counts": strategy_counts,
                    "cache_size_mb": self._get_cache_size_mb(),
                }

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do cache: {e}")
            return {}

    def _get_cache_size_mb(self) -> float:
        """Retorna tamanho do arquivo de cache em MB"""
        try:
            if self.cache_db_path.exists():
                size_bytes = self.cache_db_path.stat().st_size
                return round(size_bytes / (1024 * 1024), 2)
            return 0.0
        except Exception:
            return 0.0

    def cleanup_expired(self):
        """Remove entradas expiradas do cache"""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "DELETE FROM asin_cache WHERE expires_at <= datetime('now')"
                )
                deleted_count = cursor.rowcount

                conn.commit()

                if deleted_count > 0:
                    logger.info(
                        f"Removidas {deleted_count} entradas expiradas do cache ASIN"
                    )

        except Exception as e:
            logger.error(f"Erro ao limpar cache expirado: {e}")


# Instância global do cache
asin_cache = AsinCache()


def get_cached_asin(url: str, ttl_hours: int = 24) -> Optional[Dict[str, Any]]:
    """Função de conveniência para buscar ASIN em cache"""
    return asin_cache.get_cached_asin(url, ttl_hours)


def cache_asin(
    url: str,
    asin: str,
    strategy_used: str,
    ttl_hours: int = 24,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Função de conveniência para armazenar ASIN em cache"""
    asin_cache.cache_asin(url, asin, strategy_used, ttl_hours, metadata)


def get_cache_stats() -> Dict[str, Any]:
    """Função de conveniência para obter estatísticas do cache"""
    return asin_cache.get_cache_stats()
