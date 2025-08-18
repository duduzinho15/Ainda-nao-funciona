# services/metrics.py
import sqlite3
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MetricsService:
    def __init__(self, db_path: str = "ofertas.db"):
        self.db_path = db_path
        self.db_exists = Path(db_path).exists()
        
        if not self.db_exists:
            logger.warning(f"Banco de dados {db_path} não encontrado. Usando dados mock.")
        else:
            # Garante que o schema está correto
            self._ensure_schema()
    
    def _ensure_schema(self):
        """Garante que o schema do banco está correto"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verifica se a tabela ofertas existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ofertas'")
            if not cursor.fetchone():
                logger.warning("Tabela 'ofertas' não encontrada. Criando...")
                self._create_ofertas_table(cursor)
            else:
                # Verifica e adiciona colunas ausentes
                self._add_missing_columns(cursor)
            
            # Cria índices se não existirem
            self._create_indexes(cursor)
            
            conn.commit()
            logger.info("Schema do banco verificado e atualizado")
            
        except Exception as e:
            logger.error(f"Erro ao verificar schema: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _create_ofertas_table(self, cursor):
        """Cria tabela de ofertas com schema completo"""
        cursor.execute('''
        CREATE TABLE ofertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asin TEXT,
            url_produto TEXT NOT NULL,
            titulo TEXT NOT NULL,
            preco TEXT NOT NULL,
            preco_original TEXT,
            loja TEXT NOT NULL,
            fonte TEXT NOT NULL,
            url_fonte TEXT,
            url_afiliado TEXT,
            imagem_url TEXT,
            offer_hash TEXT,
            data_postagem TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TEXT DEFAULT (datetime('now')),
            store_name TEXT,
            price REAL,
            discount REAL,
            commission REAL,
            lowest_price_ever REAL,
            UNIQUE(url_produto),
            UNIQUE(asin),
            UNIQUE(offer_hash)
        )
        ''')
    
    def _add_missing_columns(self, cursor):
        """Adiciona colunas ausentes na tabela existente"""
        columns_to_add = [
            ('created_at', 'TEXT'),
            ('store_name', 'TEXT'),
            ('price', 'REAL'),
            ('discount', 'REAL'),
            ('commission', 'REAL'),
            ('lowest_price_ever', 'REAL'),
        ]
        
        for col_name, col_def in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE ofertas ADD COLUMN {col_name} {col_def}")
                logger.info(f"Coluna {col_name} adicionada")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    logger.warning(f"Erro ao adicionar coluna {col_name}: {e}")
    
    def _create_indexes(self, cursor):
        """Cria índices para melhorar performance"""
        # Primeiro verifica quais colunas existem
        cursor.execute("PRAGMA table_info(ofertas)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        indexes = []
        
        # Índices para colunas que sempre existem
        indexes.append("CREATE INDEX IF NOT EXISTS idx_ofertas_loja ON ofertas(loja)")
        indexes.append("CREATE INDEX IF NOT EXISTS idx_ofertas_data_postagem ON ofertas(data_postagem)")
        
        # Índices para colunas que podem não existir
        if 'created_at' in existing_columns:
            indexes.append("CREATE INDEX IF NOT EXISTS idx_ofertas_created_at ON ofertas(created_at)")
        if 'store_name' in existing_columns:
            indexes.append("CREATE INDEX IF NOT EXISTS idx_ofertas_store ON ofertas(store_name)")
        if 'price' in existing_columns:
            indexes.append("CREATE INDEX IF NOT EXISTS idx_ofertas_price ON ofertas(price)")
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                logger.warning(f"Erro ao criar índice: {e}")
    
    def _get_db_connection(self) -> Optional[sqlite3.Connection]:
        """Tenta conectar ao banco de dados"""
        if not self.db_exists:
            return None
            
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco: {e}")
            return None
    
    def _get_time_filter(self, window: str) -> str:
        """Converte filtro de tempo em condição SQL compatível"""
        now = datetime.now()
        
        # Tenta usar created_at primeiro, depois data_postagem como fallback
        if window == "24h":
            return "(created_at >= datetime('now', '-1 day') OR data_postagem >= datetime('now', '-1 day'))"
        elif window == "7d":
            return "(created_at >= datetime('now', '-7 days') OR data_postagem >= datetime('now', '-7 days'))"
        elif window == "30d":
            return "(created_at >= datetime('now', '-30 days') OR data_postagem >= datetime('now', '-30 days'))"
        else:  # "all"
            return "1=1"
    
    def get_metrics(self, window: str = "24h") -> dict:
        """Retorna todas as métricas do período em uma única chamada"""
        try:
            conn = self._get_db_connection()
            if not conn:
                # Dados mock baseados no período
                mock_data = {
                    "24h": {"total": 127, "stores": 5, "avg": 89.50, "chart": [("Amazon", 45), ("AliExpress", 38), ("Magazine Luiza", 22), ("Mercado Livre", 18), ("Shopee", 4)]},
                    "7d": {"total": 892, "stores": 5, "avg": 92.30, "chart": [("Amazon", 320), ("AliExpress", 280), ("Magazine Luiza", 150), ("Mercado Livre", 120), ("Shopee", 22)]},
                    "30d": {"total": 3421, "stores": 5, "avg": 87.45, "chart": [("Amazon", 1200), ("AliExpress", 980), ("Magazine Luiza", 650), ("Mercado Livre", 450), ("Shopee", 141)]},
                    "all": {"total": 15678, "stores": 5, "avg": 91.20, "chart": [("Amazon", 5200), ("AliExpress", 4200), ("Magazine Luiza", 2800), ("Mercado Livre", 2500), ("Shopee", 978)]}
                }
                data = mock_data.get(window, {"total": 0, "stores": 0, "avg": 0.0, "chart": []})
                data["empty"] = False
                return data
            
            time_filter = self._get_time_filter(window)
            
            # Total de ofertas
            cursor = conn.execute(f"SELECT COUNT(*) as total FROM ofertas WHERE {time_filter}")
            total_result = cursor.fetchone()
            total = total_result['total'] if total_result else 0
            
            # Lojas ativas
            query = f"""
                SELECT COALESCE(store_name, loja) as store, COUNT(*) as total 
                FROM ofertas 
                WHERE {time_filter}
                GROUP BY COALESCE(store_name, loja)
                ORDER BY total DESC
                LIMIT 10
            """
            cursor = conn.execute(query)
            stores_data = [(row['store'], row['total']) for row in cursor.fetchall()]
            stores_count = len(stores_data)
            
            # Preço médio
            price_query = f"""
                SELECT AVG(COALESCE(price, CAST(REPLACE(REPLACE(preco, 'R$', ''), ',', '.') AS REAL))) as media
                FROM ofertas 
                WHERE {time_filter} AND (price IS NOT NULL OR preco IS NOT NULL)
            """
            cursor = conn.execute(price_query)
            price_result = cursor.fetchone()
            avg_price = float(price_result['media']) if price_result and price_result['media'] else 0.0
            
            return {
                "total": total,
                "stores": stores_count,
                "avg": avg_price,
                "chart": stores_data,
                "empty": total == 0
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar métricas: {e}")
            return {
                "total": 0,
                "stores": 0,
                "avg": 0.0,
                "chart": [],
                "empty": True
            }
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_ultimas_ofertas(self, limit: int = 10) -> List[dict]:
        """Retorna últimas ofertas para logs"""
        conn = self._get_db_connection()
        if not conn:
            # Dados mock
            return [
                {"loja": "Amazon", "produto": "Smartphone XYZ", "preco": 1299.99, "created_at": "2025-08-17 14:30:00"},
                {"loja": "AliExpress", "produto": "Fone Bluetooth", "preco": 89.90, "created_at": "2025-08-17 14:25:00"},
                {"loja": "Magazine Luiza", "produto": "Notebook Gaming", "preco": 3499.99, "created_at": "2025-08-17 14:20:00"},
            ]
        
        try:
            query = """
                SELECT loja, produto, preco, created_at
                FROM ofertas 
                ORDER BY created_at DESC 
                LIMIT ?
            """
            cursor = conn.execute(query, (limit,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Erro ao buscar últimas ofertas: {e}")
            return []
        finally:
            conn.close()

# Instância global
metrics_service = MetricsService()
