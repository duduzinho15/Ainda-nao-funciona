"""
Helpers para operações SQLite seguras
Context managers, upsert e helpers de transação
"""

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class SQLiteConnectionError(Exception):
    """Erro de conexão com SQLite"""

    pass


@contextmanager
def get_conn(db_path: Union[str, Path]):
    """
    Context manager para conexões SQLite seguras

    Args:
        db_path: Caminho para o banco SQLite

    Yields:
        sqlite3.Connection: Conexão ativa

    Raises:
        SQLiteConnectionError: Se não conseguir conectar
    """
    conn = None
    try:
        # Garantir que o diretório existe
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Configurar para melhor performance
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")

        yield conn

    except sqlite3.Error as e:
        logger.error(f"Erro SQLite: {e}")
        raise SQLiteConnectionError(f"Falha na conexão com {db_path}: {e}") from e
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        raise SQLiteConnectionError(f"Erro inesperado: {e}") from e
    finally:
        if conn:
            try:
                conn.commit()
                conn.close()
            except Exception as e:
                logger.warning(f"Erro ao fechar conexão: {e}")


def execute(
    db_path: Union[str, Path], script: str, params: Optional[Tuple] = None
) -> List[Dict]:
    """
    Executa um script SQL e retorna resultados

    Args:
        db_path: Caminho para o banco
        script: Script SQL a executar
        params: Parâmetros para o script (opcional)

    Returns:
        Lista de resultados como dicionários

    Raises:
        SQLiteConnectionError: Se houver erro na execução
    """
    with get_conn(db_path) as conn:
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(script, params)
            else:
                cursor.execute(script)

            if script.strip().upper().startswith(("SELECT", "PRAGMA")):
                return [dict(row) for row in cursor.fetchall()]
            else:
                return []

        except sqlite3.Error as e:
            logger.error(f"Erro ao executar script: {e}")
            logger.error(f"Script: {script}")
            if params:
                logger.error(f"Parâmetros: {params}")
            raise SQLiteConnectionError(f"Falha na execução: {e}") from e


def execute_many(
    db_path: Union[str, Path], script: str, params_list: List[Tuple]
) -> None:
    """
    Executa um script SQL múltiplas vezes com diferentes parâmetros

    Args:
        db_path: Caminho para o banco
        script: Script SQL a executar
        params_list: Lista de tuplas de parâmetros

    Raises:
        SQLiteConnectionError: Se houver erro na execução
    """
    with get_conn(db_path) as conn:
        try:
            cursor = conn.cursor()
            cursor.executemany(script, params_list)

        except sqlite3.Error as e:
            logger.error(f"Erro ao executar script múltiplo: {e}")
            logger.error(f"Script: {script}")
            logger.error(f"Parâmetros: {params_list[:3]}...")  # Primeiros 3 para debug
            raise SQLiteConnectionError(f"Falha na execução múltipla: {e}") from e


def upsert(
    db_path: Union[str, Path],
    table: str,
    keys_dict: Dict[str, Any],
    values_dict: Dict[str, Any],
) -> int:
    """
    Insere ou atualiza registro (INSERT OR REPLACE)

    Args:
        db_path: Caminho para o banco
        table: Nome da tabela
        keys_dict: Chaves para identificação única
        values_dict: Valores a inserir/atualizar

    Returns:
        ID do registro inserido/atualizado

    Raises:
        SQLiteConnectionError: Se houver erro na operação
    """
    with get_conn(db_path) as conn:
        try:
            cursor = conn.cursor()

            # Combinar chaves e valores
            all_data = {**keys_dict, **values_dict}

            # Construir query INSERT OR REPLACE
            columns = list(all_data.keys())
            placeholders = ["?" for _ in columns]
            values = list(all_data.values())

            query = f"""
                INSERT OR REPLACE INTO {table}
                ({", ".join(columns)})
                VALUES ({", ".join(placeholders)})
            """

            cursor.execute(query, values)

            # Retornar ID do registro
            if cursor.lastrowid:
                return cursor.lastrowid
            else:
                # Se não tem lastrowid, buscar pelo registro
                where_clause = " AND ".join([f"{k} = ?" for k in keys_dict.keys()])
                select_query = f"SELECT id FROM {table} WHERE {where_clause}"
                cursor.execute(select_query, list(keys_dict.values()))
                row = cursor.fetchone()
                return row["id"] if row else 0

        except sqlite3.Error as e:
            logger.error(f"Erro no upsert: {e}")
            logger.error(f"Tabela: {table}, Chaves: {keys_dict}")
            raise SQLiteConnectionError(f"Falha no upsert: {e}") from e


@contextmanager
def transaction(db_path: Union[str, Path]):
    """
    Context manager para transações SQLite

    Args:
        db_path: Caminho para o banco

    Yields:
        sqlite3.Connection: Conexão em modo transação
    """
    with get_conn(db_path) as conn:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def table_exists(db_path: Union[str, Path], table_name: str) -> bool:
    """
    Verifica se uma tabela existe

    Args:
        db_path: Caminho para o banco
        table_name: Nome da tabela

    Returns:
        True se a tabela existe, False caso contrário
    """
    try:
        result = execute(
            db_path,
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        return len(result) > 0
    except Exception:
        return False


def get_table_info(db_path: Union[str, Path], table_name: str) -> List[Dict]:
    """
    Obtém informações sobre a estrutura de uma tabela

    Args:
        db_path: Caminho para o banco
        table_name: Nome da tabela

    Returns:
        Lista com informações das colunas
    """
    try:
        return execute(db_path, f"PRAGMA table_info({table_name})")
    except Exception:
        return []


def vacuum_db(db_path: Union[str, Path]) -> None:
    """
    Executa VACUUM no banco para otimizar espaço

    Args:
        db_path: Caminho para o banco
    """
    try:
        execute(db_path, "VACUUM")
        logger.info(f"VACUUM executado em {db_path}")
    except Exception as e:
        logger.warning(f"VACUUM falhou: {e}")


def backup_db(source_path: Union[str, Path], backup_path: Union[str, Path]) -> None:
    """
    Cria backup de um banco SQLite

    Args:
        source_path: Caminho do banco original
        backup_path: Caminho do backup

    Raises:
        SQLiteConnectionError: Se houver erro no backup
    """
    try:
        with get_conn(source_path) as source_conn:
            with get_conn(backup_path) as backup_conn:
                source_conn.backup(backup_conn)
        logger.info(f"Backup criado: {backup_path}")
    except Exception as e:
        logger.error(f"Erro no backup: {e}")
        raise SQLiteConnectionError(f"Falha no backup: {e}") from e


# Funções de conveniência para operações comuns
def insert_one(db_path: Union[str, Path], table: str, data: Dict[str, Any]) -> int:
    """Insere um registro e retorna o ID"""
    return upsert(db_path, table, {}, data)


def get_one(
    db_path: Union[str, Path], table: str, where_dict: Dict[str, Any]
) -> Optional[Dict]:
    """Busca um registro específico"""
    where_clause = " AND ".join([f"{k} = ?" for k in where_dict.keys()])
    query = f"SELECT * FROM {table} WHERE {where_clause} LIMIT 1"

    try:
        result = execute(db_path, query, tuple(where_dict.values()))
        return result[0] if result else None
    except Exception:
        return None


def get_many(
    db_path: Union[str, Path],
    table: str,
    where_dict: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
    order_by: Optional[str] = None,
) -> List[Dict]:
    """Busca múltiplos registros"""
    query = f"SELECT * FROM {table}"
    params = []

    if where_dict:
        where_clause = " AND ".join([f"{k} = ?" for k in where_dict.keys()])
        query += f" WHERE {where_clause}"
        params.extend(where_dict.values())

    if order_by:
        query += f" ORDER BY {order_by}"

    if limit:
        query += f" LIMIT {limit}"

    try:
        return execute(db_path, query, tuple(params) if params else None)
    except Exception:
        return []
