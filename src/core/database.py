"""
Sistema de banco de dados do Garimpeiro Geek
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class Database:
    """Gerencia o banco de dados SQLite"""

    def __init__(self, db_path: str = "garimpeiro_geek.db"):
        self.db_path = Path(db_path)
        self.connection = None
        self._init_database()

    def _init_database(self):
        """Inicializa o banco de dados"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self._create_tables()
            print(f"✅ Banco de dados inicializado: {self.db_path}")
        except Exception as e:
            print(f"❌ Erro ao inicializar banco: {e}")

    def _create_tables(self):
        """Cria as tabelas necessárias"""
        cursor = self.connection.cursor()

        # Tabela de ofertas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ofertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                preco REAL NOT NULL,
                preco_original REAL,
                desconto INTEGER,
                loja TEXT NOT NULL,
                url TEXT NOT NULL,
                imagem_url TEXT,
                categoria TEXT,
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ativo BOOLEAN DEFAULT 1
            )
        """)

        # Tabela de métricas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metricas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_ofertas INTEGER DEFAULT 0,
                lojas_ativas INTEGER DEFAULT 0,
                preco_medio REAL DEFAULT 0.0,
                desconto_medio REAL DEFAULT 0.0
            )
        """)

        # Tabela de logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                nivel TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                origem TEXT
            )
        """)

        self.connection.commit()

    def insert_oferta(self, oferta: Dict[str, Any]) -> int:
        """Insere uma nova oferta"""
        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO ofertas (titulo, preco, preco_original, desconto, loja, url, imagem_url, categoria)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                oferta.get("titulo", ""),
                oferta.get("preco", 0.0),
                oferta.get("preco_original", 0.0),
                oferta.get("desconto", 0),
                oferta.get("loja", ""),
                oferta.get("url", ""),
                oferta.get("imagem_url", ""),
                oferta.get("categoria", ""),
            ),
        )

        self.connection.commit()
        return cursor.lastrowid

    def get_ofertas(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Obtém ofertas do banco"""
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT * FROM ofertas 
            WHERE ativo = 1 
            ORDER BY data_coleta DESC 
            LIMIT ? OFFSET ?
        """,
            (limit, offset),
        )

        return [dict(row) for row in cursor.fetchall()]

    def get_ofertas_por_loja(self, loja: str) -> List[Dict[str, Any]]:
        """Obtém ofertas de uma loja específica"""
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT * FROM ofertas 
            WHERE loja = ? AND ativo = 1 
            ORDER BY data_coleta DESC
        """,
            (loja,),
        )

        return [dict(row) for row in cursor.fetchall()]

    def insert_metrica(self, metrica: Dict[str, Any]):
        """Insere uma nova métrica"""
        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO metricas (total_ofertas, lojas_ativas, preco_medio, desconto_medio)
            VALUES (?, ?, ?, ?)
        """,
            (
                metrica.get("total_ofertas", 0),
                metrica.get("lojas_ativas", 0),
                metrica.get("preco_medio", 0.0),
                metrica.get("desconto_medio", 0.0),
            ),
        )

        self.connection.commit()

    def get_ultima_metrica(self) -> Optional[Dict[str, Any]]:
        """Obtém a métrica mais recente"""
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT * FROM metricas 
            ORDER BY data DESC 
            LIMIT 1
        """)

        row = cursor.fetchone()
        return dict(row) if row else None

    def insert_log(self, nivel: str, mensagem: str, origem: str = "sistema"):
        """Insere um novo log"""
        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO logs (nivel, mensagem, origem)
            VALUES (?, ?, ?)
        """,
            (nivel, mensagem, origem),
        )

        self.connection.commit()

    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtém logs do banco"""
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT * FROM logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        """,
            (limit,),
        )

        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Fecha a conexão com o banco"""
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
