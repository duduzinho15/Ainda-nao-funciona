"""
Sistema de Categorias para Usuários do Bot Garimpeiro Geek

Este módulo implementa:
- Gerenciamento de categorias de produtos
- Preferências personalizadas por usuário
- Notificações baseadas em categorias
- Análise de interesses dos usuários
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

class CategoryType(Enum):
    """Tipos de categorias disponíveis."""
    ELETRONICOS = "eletronicos"
    INFORMATICA = "informatica"
    CASA_COZINHA = "casa_cozinha"
    MODA_ACESSORIOS = "moda_acessorios"
    ESPORTES_LAZER = "esportes_lazer"
    LIVROS_MIDIA = "livros_midia"
    AUTOMOVEIS = "automoveis"
    SAUDE_BELEZA = "saude_beleza"
    BRINQUEDOS_JOGOS = "brinquedos_jogos"
    OUTROS = "outros"

@dataclass
class UserCategory:
    """Categoria de usuário com preferências."""
    user_id: int
    category: str
    priority: int  # 1-5, onde 5 é mais alta
    notification_enabled: bool
    price_range_min: Optional[float]
    price_range_max: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

@dataclass
class CategoryStats:
    """Estatísticas de uma categoria."""
    category: str
    total_users: int
    active_users: int
    avg_priority: float
    total_notifications: int
    last_activity: datetime

class UserCategoryManager:
    """Gerenciador de categorias de usuários."""
    
    def __init__(self, db_path: str = "user_categories.db"):
        self.db_path = db_path
        self._init_database()
        self._load_default_categories()
    
    def _init_database(self):
        """Inicializa banco de dados."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Tabela de categorias de usuários
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_categories (
                        user_id INTEGER NOT NULL,
                        category TEXT NOT NULL,
                        priority INTEGER DEFAULT 3,
                        notification_enabled BOOLEAN DEFAULT 1,
                        price_range_min REAL,
                        price_range_max REAL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        PRIMARY KEY (user_id, category)
                    )
                """)
                
                # Tabela de histórico de categorias
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS category_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        category TEXT NOT NULL,
                        action TEXT NOT NULL,
                        old_value TEXT,
                        new_value TEXT,
                        timestamp TEXT NOT NULL
                    )
                """)
                
                # Tabela de notificações por categoria
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS category_notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        category TEXT NOT NULL,
                        product_id TEXT NOT NULL,
                        price REAL NOT NULL,
                        old_price REAL,
                        discount_percent REAL,
                        sent_at TEXT NOT NULL,
                        read_at TEXT
                    )
                """)
                
                # Índices para performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_categories_user ON user_categories(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_categories_category ON user_categories(category)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_category_history_user ON category_history(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_category_notifications_user ON category_notifications(user_id)")
                
                conn.commit()
                logger.info("Banco de dados de categorias inicializado")
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
    
    def _load_default_categories(self):
        """Carrega categorias padrão se não existirem."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Verifica se já existem categorias
                cursor = conn.execute("SELECT COUNT(*) FROM user_categories LIMIT 1")
                if cursor.fetchone()[0] == 0:
                    logger.info("Carregando categorias padrão...")
        except Exception as e:
            logger.error(f"Erro ao carregar categorias padrão: {e}")
    
    def add_user_category(self, user_id: int, category: str, priority: int = 3,
                         notification_enabled: bool = True, price_range_min: Optional[float] = None,
                         price_range_max: Optional[float] = None) -> bool:
        """Adiciona ou atualiza categoria para usuário."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                now = datetime.now()
                
                # Verifica se já existe
                cursor = conn.execute(
                    "SELECT priority, notification_enabled, price_range_min, price_range_max FROM user_categories WHERE user_id = ? AND category = ?",
                    (user_id, category)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Atualiza existente
                    old_values = {
                        'priority': existing[0],
                        'notification_enabled': existing[1],
                        'price_range_min': existing[2],
                        'price_range_max': existing[3]
                    }
                    
                    conn.execute("""
                        UPDATE user_categories 
                        SET priority = ?, notification_enabled = ?, price_range_min = ?, price_range_max = ?, updated_at = ?
                        WHERE user_id = ? AND category = ?
                    """, (priority, notification_enabled, price_range_min, price_range_max, now.isoformat(), user_id, category))
                    
                    # Registra histórico
                    self._log_category_change(conn, user_id, category, "update", old_values, {
                        'priority': priority,
                        'notification_enabled': notification_enabled,
                        'price_range_min': price_range_min,
                        'price_range_max': price_range_max
                    })
                else:
                    # Insere novo
                    conn.execute("""
                        INSERT INTO user_categories 
                        (user_id, category, priority, notification_enabled, price_range_min, price_range_max, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (user_id, category, priority, notification_enabled, price_range_min, price_range_max, now.isoformat(), now.isoformat()))
                    
                    # Registra histórico
                    self._log_category_change(conn, user_id, category, "create", None, {
                        'priority': priority,
                        'notification_enabled': notification_enabled,
                        'price_range_min': price_range_min,
                        'price_range_max': price_range_max
                    })
                
                conn.commit()
                logger.info(f"Categoria {category} adicionada/atualizada para usuário {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao adicionar categoria: {e}")
            return False
    
    def remove_user_category(self, user_id: int, category: str) -> bool:
        """Remove categoria de usuário."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Obtém valores antigos para histórico
                cursor = conn.execute(
                    "SELECT priority, notification_enabled, price_range_min, price_range_max FROM user_categories WHERE user_id = ? AND category = ?",
                    (user_id, category)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Registra histórico antes de remover
                    self._log_category_change(conn, user_id, category, "delete", {
                        'priority': existing[0],
                        'notification_enabled': existing[1],
                        'price_range_min': existing[2],
                        'price_range_max': existing[3]
                    }, None)
                    
                    # Remove categoria
                    conn.execute(
                        "DELETE FROM user_categories WHERE user_id = ? AND category = ?",
                        (user_id, category)
                    )
                    
                    conn.commit()
                    logger.info(f"Categoria {category} removida do usuário {user_id}")
                    return True
                else:
                    logger.warning(f"Categoria {category} não encontrada para usuário {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao remover categoria: {e}")
            return False
    
    def get_user_categories(self, user_id: int) -> List[UserCategory]:
        """Obtém todas as categorias de um usuário."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT user_id, category, priority, notification_enabled, price_range_min, price_range_max, created_at, updated_at
                    FROM user_categories 
                    WHERE user_id = ?
                    ORDER BY priority DESC, category
                """, (user_id,))
                
                categories = []
                for row in cursor.fetchall():
                    category = UserCategory(
                        user_id=row[0],
                        category=row[1],
                        priority=row[2],
                        notification_enabled=bool(row[3]),
                        price_range_min=row[4],
                        price_range_max=row[5],
                        created_at=datetime.fromisoformat(row[6]),
                        updated_at=datetime.fromisoformat(row[7])
                    )
                    categories.append(category)
                
                return categories
                
        except Exception as e:
            logger.error(f"Erro ao obter categorias do usuário: {e}")
            return []
    
    def get_users_by_category(self, category: str, min_priority: int = 1) -> List[int]:
        """Obtém usuários interessados em uma categoria específica."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT user_id FROM user_categories 
                    WHERE category = ? AND priority >= ? AND notification_enabled = 1
                    ORDER BY priority DESC
                """, (category, min_priority))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Erro ao obter usuários por categoria: {e}")
            return []
    
    def update_category_priority(self, user_id: int, category: str, new_priority: int) -> bool:
        """Atualiza prioridade de uma categoria."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Obtém valor antigo
                cursor = conn.execute(
                    "SELECT priority FROM user_categories WHERE user_id = ? AND category = ?",
                    (user_id, category)
                )
                old_priority = cursor.fetchone()
                
                if old_priority:
                    # Atualiza prioridade
                    conn.execute("""
                        UPDATE user_categories 
                        SET priority = ?, updated_at = ?
                        WHERE user_id = ? AND category = ?
                    """, (new_priority, datetime.now().isoformat(), user_id, category))
                    
                    # Registra histórico
                    self._log_category_change(conn, user_id, category, "priority_change", 
                                           {'priority': old_priority[0]}, {'priority': new_priority})
                    
                    conn.commit()
                    logger.info(f"Prioridade da categoria {category} atualizada para {new_priority}")
                    return True
                else:
                    logger.warning(f"Categoria {category} não encontrada para usuário {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao atualizar prioridade: {e}")
            return False
    
    def toggle_notifications(self, user_id: int, category: str) -> bool:
        """Alterna notificações para uma categoria."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Obtém valor atual
                cursor = conn.execute(
                    "SELECT notification_enabled FROM user_categories WHERE user_id = ? AND category = ?",
                    (user_id, category)
                )
                current = cursor.fetchone()
                
                if current:
                    new_value = not current[0]
                    
                    # Atualiza notificações
                    conn.execute("""
                        UPDATE user_categories 
                        SET notification_enabled = ?, updated_at = ?
                        WHERE user_id = ? AND category = ?
                    """, (new_value, datetime.now().isoformat(), user_id, category))
                    
                    # Registra histórico
                    self._log_category_change(conn, user_id, category, "notification_toggle", 
                                           {'notification_enabled': current[0]}, {'notification_enabled': new_value})
                    
                    conn.commit()
                    logger.info(f"Notificações para categoria {category} alteradas para {new_value}")
                    return True
                else:
                    logger.warning(f"Categoria {category} não encontrada para usuário {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao alternar notificações: {e}")
            return False
    
    def get_category_stats(self) -> List[CategoryStats]:
        """Obtém estatísticas de todas as categorias."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        category,
                        COUNT(*) as total_users,
                        SUM(CASE WHEN notification_enabled = 1 THEN 1 ELSE 0 END) as active_users,
                        AVG(priority) as avg_priority,
                        COUNT(*) as total_notifications,
                        MAX(updated_at) as last_activity
                    FROM user_categories 
                    GROUP BY category
                    ORDER BY total_users DESC
                """)
                
                stats = []
                for row in cursor.fetchall():
                    stat = CategoryStats(
                        category=row[0],
                        total_users=row[1],
                        active_users=row[2],
                        avg_priority=round(row[3], 2) if row[3] else 0.0,
                        total_notifications=row[4],
                        last_activity=datetime.fromisoformat(row[5]) if row[5] else datetime.now()
                    )
                    stats.append(stat)
                
                return stats
                
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de categorias: {e}")
            return []
    
    def _log_category_change(self, conn: sqlite3.Connection, user_id: int, category: str, 
                           action: str, old_value: Optional[Dict], new_value: Optional[Dict]):
        """Registra mudança de categoria no histórico."""
        try:
            conn.execute("""
                INSERT INTO category_history (user_id, category, action, old_value, new_value, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, 
                category, 
                action, 
                json.dumps(old_value) if old_value else None,
                json.dumps(new_value) if new_value else None,
                datetime.now().isoformat()
            ))
        except Exception as e:
            logger.error(f"Erro ao registrar histórico de categoria: {e}")
    
    def get_user_category_history(self, user_id: int, days: int = 30) -> List[Dict]:
        """Obtém histórico de mudanças de categorias de um usuário."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                cursor = conn.execute("""
                    SELECT category, action, old_value, new_value, timestamp
                    FROM category_history 
                    WHERE user_id = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """, (user_id, cutoff_date.isoformat()))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'category': row[0],
                        'action': row[1],
                        'old_value': json.loads(row[2]) if row[2] else None,
                        'new_value': json.loads(row[3]) if row[3] else None,
                        'timestamp': row[4]
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Erro ao obter histórico de categorias: {e}")
            return []
    
    def get_recommended_categories(self, user_id: int, limit: int = 5) -> List[str]:
        """Obtém categorias recomendadas baseadas no comportamento do usuário."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Busca categorias populares entre usuários similares
                cursor = conn.execute("""
                    SELECT c.category, COUNT(*) as popularity
                    FROM user_categories c
                    WHERE c.user_id IN (
                        SELECT DISTINCT uc.user_id 
                        FROM user_categories uc 
                        WHERE uc.user_id != ? 
                        AND uc.category IN (
                            SELECT category FROM user_categories WHERE user_id = ?
                        )
                    )
                    AND c.category NOT IN (
                        SELECT category FROM user_categories WHERE user_id = ?
                    )
                    GROUP BY c.category
                    ORDER BY popularity DESC
                    LIMIT ?
                """, (user_id, user_id, user_id, limit))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Erro ao obter categorias recomendadas: {e}")
            return []

# Instância global do gerenciador
category_manager = UserCategoryManager()

# Funções de conveniência
def add_user_category(user_id: int, category: str, priority: int = 3, **kwargs) -> bool:
    """Adiciona categoria para usuário."""
    return category_manager.add_user_category(user_id, category, priority, **kwargs)

def get_user_categories(user_id: int) -> List[UserCategory]:
    """Obtém categorias de um usuário."""
    return category_manager.get_user_categories(user_id)

def get_users_by_category(category: str, min_priority: int = 1) -> List[int]:
    """Obtém usuários interessados em uma categoria."""
    return category_manager.get_users_by_category(category, min_priority)

def get_category_stats() -> List[CategoryStats]:
    """Obtém estatísticas de categorias."""
    return category_manager.get_category_stats()

if __name__ == "__main__":
    # Teste do sistema de categorias
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testando Sistema de Categorias de Usuários...")
    
    # Testa adição de categorias
    user_id = 12345
    add_user_category(user_id, "eletronicos", 5, price_range_min=100, price_range_max=1000)
    add_user_category(user_id, "informatica", 4, price_range_min=50, price_range_max=500)
    
    # Obtém categorias do usuário
    categories = get_user_categories(user_id)
    print(f"Categorias do usuário {user_id}: {len(categories)}")
    
    # Testa estatísticas
    stats = get_category_stats()
    print(f"Estatísticas de categorias: {len(stats)} categorias")
    
    print("Teste concluído!")
