"""
Sistema de Reviews para Produtos
Gerencia avaliações, comentários e classificações de produtos pelos usuários
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Dict, Optional, Tuple
from statistics import mean, median
import hashlib
import re

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReviewStatus(Enum):
    """Status de uma review"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SPAM = "spam"

class ReviewType(Enum):
    """Tipo de review"""
    VERIFIED_PURCHASE = "verified_purchase"
    UNVERIFIED = "unverified"
    EXPERT = "expert"
    INFLUENCER = "influencer"

class ReviewCategory(Enum):
    """Categorias de avaliação"""
    QUALIDADE = "qualidade"
    PREÇO = "preco"
    ENTREGA = "entrega"
    ATENDIMENTO = "atendimento"
    DURABILIDADE = "durabilidade"
    FUNCIONALIDADE = "funcionalidade"
    DESIGN = "design"
    GERAL = "geral"

@dataclass
class ProductReview:
    """Representa uma review de produto"""
    id: Optional[int]
    user_id: int
    product_id: str
    store: str
    rating: int  # 1-5 estrelas
    title: str
    comment: str
    review_type: ReviewType
    status: ReviewStatus
    helpful_votes: int
    unhelpful_votes: int
    verified_purchase: bool
    purchase_date: Optional[datetime]
    review_date: datetime
    last_updated: datetime
    language: str
    source: str
    metadata: Dict

@dataclass
class ReviewMetrics:
    """Métricas agregadas de reviews"""
    product_id: str
    store: str
    total_reviews: int
    avg_rating: float
    rating_distribution: Dict[int, int]  # rating -> count
    verified_reviews: int
    recent_reviews_30d: int
    helpful_reviews: int
    sentiment_score: float
    last_calculated: datetime

@dataclass
class ReviewAnalysis:
    """Análise detalhada de reviews"""
    product_id: str
    store: str
    overall_score: float
    quality_score: float
    price_score: float
    delivery_score: float
    service_score: float
    durability_score: float
    functionality_score: float
    design_score: float
    trust_score: float
    review_count: int
    verified_percentage: float
    recent_trend: str
    sentiment_analysis: Dict[str, float]
    top_keywords: List[str]

class ProductReviewManager:
    """Gerencia o sistema de reviews de produtos"""
    
    def __init__(self, db_path: str = "product_reviews.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializa o banco de dados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabela principal de reviews
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS product_reviews (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        product_id TEXT NOT NULL,
                        product_url TEXT NOT NULL,
                        store TEXT NOT NULL,
                        rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                        title TEXT,
                        comment TEXT NOT NULL,
                        review_type TEXT DEFAULT 'unverified',
                        status TEXT DEFAULT 'pending',
                        helpful_votes INTEGER DEFAULT 0,
                        unhelpful_votes INTEGER DEFAULT 0,
                        verified_purchase BOOLEAN DEFAULT FALSE,
                        purchase_date TEXT,
                        review_date TEXT NOT NULL,
                        last_updated TEXT NOT NULL,
                        language TEXT DEFAULT 'pt-BR',
                        source TEXT DEFAULT 'telegram_bot',
                        metadata TEXT,
                        username TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                
                # Tabela de histórico de mudanças
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS review_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        review_id INTEGER NOT NULL,
                        action TEXT NOT NULL,
                        old_value TEXT,
                        new_value TEXT,
                        admin_id INTEGER,
                        timestamp TEXT NOT NULL,
                        reason TEXT,
                        FOREIGN KEY (review_id) REFERENCES product_reviews (id)
                    )
                """)
                
                # Tabela de métricas de produtos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS product_ratings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id TEXT NOT NULL,
                        product_url TEXT NOT NULL,
                        store TEXT NOT NULL,
                        total_reviews INTEGER DEFAULT 0,
                        avg_rating REAL DEFAULT 0.0,
                        rating_distribution TEXT,
                        verified_reviews INTEGER DEFAULT 0,
                        recent_reviews_30d INTEGER DEFAULT 0,
                        helpful_reviews INTEGER DEFAULT 0,
                        sentiment_score REAL DEFAULT 0.0,
                        last_calculated TEXT NOT NULL,
                        UNIQUE(product_id, store)
                    )
                """)
                
                # Índices para performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_product ON product_reviews(product_id, store)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_user ON product_reviews(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_status ON product_reviews(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_rating ON product_reviews(rating)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_date ON product_reviews(review_date)")
                
                conn.commit()
                logger.info("Banco de dados de reviews inicializado com sucesso")
                
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise
    
    def add_review(self, user_id: int, product_url: str, rating: int, comment: str, 
                   title: str = "", username: str = "", store: str = "unknown") -> bool:
        """
        Adiciona uma nova review
        
        Args:
            user_id: ID do usuário
            product_url: URL do produto
            rating: Nota de 1-5
            comment: Comentário da review
            title: Título da review (opcional)
            username: Nome do usuário
            store: Nome da loja
        
        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            if not 1 <= rating <= 5:
                logger.error(f"Rating inválido: {rating}")
                return False
            
            # Gera ID único do produto baseado na URL
            product_id = hashlib.md5(product_url.encode()).hexdigest()[:16]
            
            now = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO product_reviews (
                        user_id, product_id, product_url, store, rating, title, comment,
                        review_type, status, review_date, last_updated, username, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, product_id, product_url, store, rating, title, comment,
                    ReviewType.UNVERIFIED.value, ReviewStatus.PENDING.value, now, now, username, now
                ))
                
                review_id = cursor.lastrowid
                
                # Registra na história
                cursor.execute("""
                    INSERT INTO review_history (review_id, action, new_value, timestamp)
                    VALUES (?, 'created', ?, ?)
                """, (review_id, f"Review criada com rating {rating}", now))
                
                # Atualiza métricas do produto
                self._update_product_metrics(product_id, store)
                
                conn.commit()
                logger.info(f"Review adicionada com sucesso: ID {review_id}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao adicionar review: {e}")
            return False
    
    def get_reviews_for_product(self, product_url: str, status: ReviewStatus = ReviewStatus.APPROVED) -> List[Dict]:
        """
        Obtém reviews de um produto específico
        
        Args:
            product_url: URL do produto
            status: Status das reviews a retornar
        
        Returns:
            List[Dict]: Lista de reviews
        """
        try:
            product_id = hashlib.md5(product_url.encode()).hexdigest()[:16]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, user_id, rating, title, comment, review_type, status,
                           helpful_votes, unhelpful_votes, verified_purchase,
                           review_date, username, created_at
                    FROM product_reviews
                    WHERE product_id = ? AND status = ?
                    ORDER BY review_date DESC
                """, (product_id, status.value))
                
                reviews = []
                for row in cursor.fetchall():
                    reviews.append({
                        'id': row[0],
                        'user_id': row[1],
                        'rating': row[2],
                        'title': row[3],
                        'comment': row[4],
                        'review_type': row[5],
                        'status': row[6],
                        'helpful_votes': row[7],
                        'unhelpful_votes': row[8],
                        'verified_purchase': bool(row[9]),
                        'review_date': row[10],
                        'username': row[11],
                        'created_at': row[12]
                    })
                
                return reviews
                
        except Exception as e:
            logger.error(f"Erro ao buscar reviews do produto: {e}")
            return []
    
    def get_user_reviews(self, user_id: int) -> List[Dict]:
        """
        Obtém todas as reviews de um usuário
        
        Args:
            user_id: ID do usuário
        
        Returns:
            List[Dict]: Lista de reviews do usuário
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, product_url, store, rating, title, comment, status,
                           review_date, created_at
                    FROM product_reviews
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
                
                reviews = []
                for row in cursor.fetchall():
                    reviews.append({
                        'id': row[0],
                        'product_url': row[1],
                        'store': row[2],
                        'rating': row[3],
                        'title': row[4],
                        'comment': row[5],
                        'status': row[6],
                        'review_date': row[7],
                        'created_at': row[8]
                    })
                
                return reviews
                
        except Exception as e:
            logger.error(f"Erro ao buscar reviews do usuário: {e}")
            return []
    
    def update_review(self, review_id: int, **kwargs) -> bool:
        """
        Atualiza uma review existente
        
        Args:
            review_id: ID da review
            **kwargs: Campos a atualizar
        
        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            allowed_fields = ['rating', 'title', 'comment', 'helpful_votes', 'unhelpful_votes']
            update_fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if not update_fields:
                logger.warning("Nenhum campo válido para atualização")
                return False
            
            values.append(datetime.now().isoformat())  # last_updated
            values.append(review_id)  # WHERE clause
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = f"""
                    UPDATE product_reviews 
                    SET {', '.join(update_fields)}, last_updated = ?
                    WHERE id = ?
                """
                
                cursor.execute(query, values)
                
                if cursor.rowcount > 0:
                    # Registra na história
                    cursor.execute("""
                        INSERT INTO review_history (review_id, action, new_value, timestamp)
                        VALUES (?, 'updated', ?, ?)
                    """, (review_id, f"Review atualizada: {', '.join(update_fields)}", datetime.now().isoformat()))
                    
                    conn.commit()
                    logger.info(f"Review {review_id} atualizada com sucesso")
                    return True
                else:
                    logger.warning(f"Review {review_id} não encontrada")
                    return False
                
        except Exception as e:
            logger.error(f"Erro ao atualizar review: {e}")
            return False
    
    def delete_review(self, review_id: int, user_id: int) -> bool:
        """
        Deleta uma review (apenas o próprio usuário pode deletar)
        
        Args:
            review_id: ID da review
            user_id: ID do usuário que está deletando
        
        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verifica se a review pertence ao usuário
                cursor.execute("""
                    SELECT id FROM product_reviews 
                    WHERE id = ? AND user_id = ?
                """, (review_id, user_id))
                
                if not cursor.fetchone():
                    logger.warning(f"Review {review_id} não pertence ao usuário {user_id}")
                    return False
                
                # Deleta a review
                cursor.execute("DELETE FROM product_reviews WHERE id = ?", (review_id,))
                
                if cursor.rowcount > 0:
                    # Registra na história
                    cursor.execute("""
                        INSERT INTO review_history (review_id, action, timestamp)
                        VALUES (?, 'deleted', ?)
                    """, (review_id, datetime.now().isoformat()))
                    
                    conn.commit()
                    logger.info(f"Review {review_id} deletada com sucesso")
                    return True
                else:
                    return False
                
        except Exception as e:
            logger.error(f"Erro ao deletar review: {e}")
            return False
    
    def moderate_review(self, review_id: int, action: str, admin_id: int, reason: str = "") -> bool:
        """
        Modera uma review (apenas administradores)
        
        Args:
            review_id: ID da review
            action: Ação (approve, reject, spam)
            admin_id: ID do administrador
            reason: Motivo da ação
        
        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            if action not in ['approve', 'reject', 'spam']:
                logger.error(f"Ação de moderação inválida: {action}")
                return False
            
            # Mapeia ação para status
            status_map = {
                'approve': ReviewStatus.APPROVED.value,
                'reject': ReviewStatus.REJECTED.value,
                'spam': ReviewStatus.SPAM.value
            }
            
            new_status = status_map[action]
            now = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Atualiza status da review
                cursor.execute("""
                    UPDATE product_reviews 
                    SET status = ?, last_updated = ?
                    WHERE id = ?
                """, (new_status, now, review_id))
                
                if cursor.rowcount > 0:
                    # Registra na história
                    cursor.execute("""
                        INSERT INTO review_history (
                            review_id, action, old_value, new_value, admin_id, timestamp, reason
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (review_id, f"moderated_{action}", "pending", new_status, admin_id, now, reason))
                    
                    # Obtém informações da review para atualizar métricas
                    cursor.execute("""
                        SELECT product_id, store FROM product_reviews WHERE id = ?
                    """, (review_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        self._update_product_metrics(row[0], row[1])
                    
                    conn.commit()
                    logger.info(f"Review {review_id} moderada: {action}")
                    return True
                else:
                    logger.warning(f"Review {review_id} não encontrada")
                    return False
                
        except Exception as e:
            logger.error(f"Erro ao moderar review: {e}")
            return False
    
    def get_average_rating(self, product_url: str) -> Optional[float]:
        """
        Obtém a média de rating de um produto
        
        Args:
            product_url: URL do produto
        
        Returns:
            Optional[float]: Média de rating ou None se não houver reviews
        """
        try:
            product_id = hashlib.md5(product_url.encode()).hexdigest()[:16]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT AVG(rating), COUNT(*) 
                    FROM product_reviews 
                    WHERE product_id = ? AND status = 'approved'
                """, (product_id,))
                
                row = cursor.fetchone()
                if row and row[1] > 0:
                    return round(row[0], 2)
                return None
                
        except Exception as e:
            logger.error(f"Erro ao calcular média de rating: {e}")
            return None
    
    def get_review_distribution(self, product_url: str) -> Dict[int, int]:
        """
        Obtém a distribuição de ratings de um produto
        
        Args:
            product_url: URL do produto
        
        Returns:
            Dict[int, int]: Distribuição de ratings (rating -> count)
        """
        try:
            product_id = hashlib.md5(product_url.encode()).hexdigest()[:16]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT rating, COUNT(*) 
                    FROM product_reviews 
                    WHERE product_id = ? AND status = 'approved'
                    GROUP BY rating
                    ORDER BY rating
                """, (product_id,))
                
                distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                for row in cursor.fetchall():
                    distribution[row[0]] = row[1]
                
                return distribution
                
        except Exception as e:
            logger.error(f"Erro ao obter distribuição de ratings: {e}")
            return {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    def get_recent_reviews(self, days: int = 30) -> List[Dict]:
        """
        Obtém reviews recentes
        
        Args:
            days: Número de dias para trás
        
        Returns:
            List[Dict]: Lista de reviews recentes
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, product_url, store, rating, comment, username, created_at
                    FROM product_reviews
                    WHERE created_at >= ? AND status = 'approved'
                    ORDER BY created_at DESC
                    LIMIT 50
                """, (cutoff_date,))
                
                reviews = []
                for row in cursor.fetchall():
                    reviews.append({
                        'id': row[0],
                        'product_url': row[1],
                        'store': row[2],
                        'rating': row[3],
                        'comment': row[4],
                        'username': row[5],
                        'created_at': row[6]
                    })
                
                return reviews
                
        except Exception as e:
            logger.error(f"Erro ao buscar reviews recentes: {e}")
            return []
    
    def get_flagged_reviews(self) -> List[Dict]:
        """
        Obtém reviews que podem precisar de atenção (muitos votos negativos, etc.)
        
        Returns:
            List[Dict]: Lista de reviews sinalizadas
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, product_url, store, rating, comment, username,
                           helpful_votes, unhelpful_votes, created_at
                    FROM product_reviews
                    WHERE status = 'approved' AND unhelpful_votes > helpful_votes
                    ORDER BY unhelpful_votes DESC
                    LIMIT 20
                """)
                
                flagged = []
                for row in cursor.fetchall():
                    flagged.append({
                        'id': row[0],
                        'product_url': row[1],
                        'store': row[2],
                        'rating': row[3],
                        'comment': row[4],
                        'username': row[5],
                        'helpful_votes': row[6],
                        'unhelpful_votes': row[7],
                        'created_at': row[8]
                    })
                
                return flagged
                
        except Exception as e:
            logger.error(f"Erro ao buscar reviews sinalizadas: {e}")
            return []
    
    def _update_product_metrics(self, product_id: str, store: str):
        """Atualiza métricas de um produto"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calcula métricas básicas
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        AVG(rating) as avg_rating,
                        COUNT(CASE WHEN verified_purchase = 1 THEN 1 END) as verified,
                        COUNT(CASE WHEN created_at >= date('now', '-30 days') THEN 1 END) as recent_30d,
                        COUNT(CASE WHEN helpful_votes > unhelpful_votes THEN 1 END) as helpful
                    FROM product_reviews
                    WHERE product_id = ? AND store = ? AND status = 'approved'
                """, (product_id, store))
                
                row = cursor.fetchone()
                if row:
                    total, avg_rating, verified, recent_30d, helpful = row
                    
                    # Obtém distribuição de ratings
                    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                    
                    # Calcula score de sentimento (simplificado)
                    sentiment_score = (avg_rating - 3) / 2 if avg_rating else 0
                    
                    now = datetime.now().isoformat()
                    
                    # Insere ou atualiza métricas
                    cursor.execute("""
                        INSERT OR REPLACE INTO product_ratings (
                            product_id, store, total_reviews, avg_rating, rating_distribution,
                            verified_reviews, recent_reviews_30d, helpful_reviews,
                            sentiment_score, last_calculated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product_id, store, total, avg_rating or 0.0, json.dumps(distribution),
                        verified, recent_30d, helpful, sentiment_score, now
                    ))
                    
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Erro ao atualizar métricas do produto: {e}")
    
    def get_review_stats(self) -> Dict:
        """
        Obtém estatísticas gerais do sistema de reviews
        
        Returns:
            Dict: Estatísticas do sistema
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total de reviews
                cursor.execute("SELECT COUNT(*) FROM product_reviews")
                total_reviews = cursor.fetchone()[0]
                
                # Reviews por status
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM product_reviews 
                    GROUP BY status
                """)
                status_counts = dict(cursor.fetchall())
                
                # Média geral de ratings
                cursor.execute("""
                    SELECT AVG(rating) 
                    FROM product_reviews 
                    WHERE status = 'approved'
                """)
                avg_rating = cursor.fetchone()[0] or 0.0
                
                # Reviews por loja
                cursor.execute("""
                    SELECT store, COUNT(*) 
                    FROM product_reviews 
                    GROUP BY store 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 10
                """)
                store_counts = dict(cursor.fetchall())
                
                # Reviews recentes (últimos 7 dias)
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM product_reviews 
                    WHERE created_at >= date('now', '-7 days')
                """)
                recent_reviews = cursor.fetchone()[0]
                
                return {
                    'total_reviews': total_reviews,
                    'status_distribution': status_counts,
                    'average_rating': round(avg_rating, 2),
                    'top_stores': store_counts,
                    'recent_reviews_7d': recent_reviews,
                    'pending_moderation': status_counts.get('pending', 0)
                }
                
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def _log_review_action(self, review_id: int, action: str, details: str):
        """Registra uma ação em uma review"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO review_history (review_id, action, new_value, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (review_id, action, details, datetime.now().isoformat()))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Erro ao registrar ação da review: {e}")

# Instância global do gerenciador de reviews
review_manager = ProductReviewManager()

# Funções auxiliares para uso no bot
async def add_product_review(user_id: int, product_url: str, rating: int, 
                           comment: str, username: str = "") -> bool:
    """Função auxiliar para adicionar review via bot"""
    return review_manager.add_review(user_id, product_url, rating, comment, username=username)

async def get_product_reviews(product_url: str) -> List[Dict]:
    """Função auxiliar para obter reviews de um produto"""
    return review_manager.get_reviews_for_product(product_url)

async def get_user_reviews(user_id: int) -> List[Dict]:
    """Função auxiliar para obter reviews de um usuário"""
    return review_manager.get_user_reviews(user_id)

async def update_review_status(review_id: int, action: str) -> bool:
    """Função auxiliar para atualizar status de uma review"""
    # Mapeia ação para formato esperado
    action_map = {
        'aprovar': 'approve',
        'rejeitar': 'reject',
        'spam': 'spam'
    }
    
    mapped_action = action_map.get(action, action)
    return review_manager.moderate_review(review_id, mapped_action, admin_id=1)

async def get_review_stats() -> Dict:
    """Função auxiliar para obter estatísticas de reviews"""
    return review_manager.get_review_stats()

async def get_pending_reviews() -> List[Dict]:
    """Função auxiliar para obter reviews pendentes"""
    return review_manager.get_reviews_for_product("", ReviewStatus.PENDING)

async def get_product_average_rating(product_url: str) -> Optional[float]:
    """Função auxiliar para obter rating médio de um produto"""
    return review_manager.get_average_rating(product_url)

if __name__ == "__main__":
    # Teste do sistema
    import asyncio
    
    async def test_reviews():
        # Adiciona algumas reviews de teste
        success1 = await add_product_review(
            user_id=123, 
            product_url="https://amazon.com/produto1", 
            rating=5, 
            comment="Produto excelente!", 
            username="usuario1"
        )
        
        success2 = await add_product_review(
            user_id=456, 
            product_url="https://amazon.com/produto1", 
            rating=4, 
            comment="Muito bom produto", 
            username="usuario2"
        )
        
        print(f"Reviews adicionadas: {success1}, {success2}")
        
        # Obtém reviews do produto
        reviews = await get_product_reviews("https://amazon.com/produto1")
        print(f"Reviews encontradas: {len(reviews)}")
        
        # Obtém estatísticas
        stats = await get_review_stats()
        print(f"Estatísticas: {stats}")
    
    asyncio.run(test_reviews())
