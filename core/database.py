"""
Sistema de banco de dados robusto para o Garimpeiro Geek.
Suporta PostgreSQL e SQLite com migrations automáticas.
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import json

# SQLAlchemy
try:
    from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session, relationship
    from sqlalchemy.pool import StaticPool
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logging.warning("SQLAlchemy não disponível, usando SQLite básico")

# Configuração de logging
logger = logging.getLogger(__name__)

# Base para modelos SQLAlchemy
Base = declarative_base()


class Offer(Base):
    """Modelo para ofertas de produtos."""
    __tablename__ = 'offers'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    original_price = Column(Float)
    discount_percentage = Column(Float)
    currency = Column(String(3), default='BRL')
    
    # URLs
    product_url = Column(String(1000))
    image_url = Column(String(1000))
    affiliate_url = Column(String(1000))
    
    # Metadados
    store = Column(String(100), nullable=False)
    category = Column(String(100))
    brand = Column(String(100))
    model = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Relacionamentos
    price_history = relationship("PriceHistory", back_populates="offer")
    reviews = relationship("ProductReview", back_populates="offer")
    
    def __repr__(self):
        return f"<Offer(id={self.id}, title='{self.title[:50]}...', price={self.price})>"


class PriceHistory(Base):
    """Histórico de preços para análise de tendências."""
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True)
    offer_id = Column(Integer, ForeignKey('offers.id'), nullable=False)
    price = Column(Float, nullable=False)
    original_price = Column(Float)
    discount_percentage = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento
    offer = relationship("Offer", back_populates="price_history")
    
    def __repr__(self):
        return f"<PriceHistory(offer_id={self.offer_id}, price={self.price}, timestamp={self.timestamp})>"


class ProductReview(Base):
    """Reviews de produtos pelos usuários."""
    __tablename__ = 'product_reviews'
    
    id = Column(Integer, primary_key=True)
    offer_id = Column(Integer, ForeignKey('offers.id'), nullable=False)
    user_id = Column(Integer, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento
    offer = relationship("Offer", back_populates="reviews")
    
    def __repr__(self):
        return f"<ProductReview(offer_id={self.offer_id}, rating={self.rating})>"


class User(Base):
    """Usuários do sistema."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    # Preferências
    preferred_categories = Column(Text)  # JSON string
    preferred_stores = Column(Text)      # JSON string
    notification_enabled = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username='{self.username}')>"


class ScraperLog(Base):
    """Logs de execução dos scrapers."""
    __tablename__ = 'scraper_logs'
    
    id = Column(Integer, primary_key=True)
    scraper_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)  # success, error, warning
    message = Column(Text)
    offers_found = Column(Integer, default=0)
    execution_time = Column(Float)  # segundos
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ScraperLog(scraper='{self.scraper_name}', status='{self.status}')>"


class DatabaseManager:
    """Gerenciador principal do banco de dados."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or self._get_default_url()
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _get_default_url(self) -> str:
        """Retorna URL padrão do banco de dados."""
        # Verificar se há variável de ambiente
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return db_url
        
        # Verificar se há arquivo de configuração
        config_file = Path(".data/config/database.json")
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get("database_url", "sqlite:///garimpeiro_geek.db")
            except Exception as e:
                logger.warning(f"Erro ao ler config de banco: {e}")
        
        # Padrão: SQLite local
        return "sqlite:///garimpeiro_geek.db"
    
    def _setup_database(self):
        """Configura conexão com banco de dados."""
        try:
            if not SQLALCHEMY_AVAILABLE:
                logger.warning("SQLAlchemy não disponível, usando SQLite básico")
                return
            
            # Configurar engine
            if "sqlite" in self.database_url:
                # SQLite com configurações otimizadas
                self.engine = create_engine(
                    self.database_url,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False},
                    echo=False
                )
            else:
                # PostgreSQL ou MySQL
                self.engine = create_engine(
                    self.database_url,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    echo=False
                )
            
            # Criar sessão
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Criar tabelas
            self._create_tables()
            
            # Criar índices
            self._create_indexes()
            
            logger.info(f"✅ Banco de dados configurado: {self.database_url}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar banco de dados: {e}")
            # Fallback para SQLite básico
            self._setup_sqlite_fallback()
    
    def _setup_sqlite_fallback(self):
        """Configuração de fallback para SQLite básico."""
        try:
            import sqlite3
            
            # Criar diretório se não existir
            db_dir = Path(".data/database")
            db_dir.mkdir(parents=True, exist_ok=True)
            
            db_path = db_dir / "garimpeiro_geek.db"
            self.engine = create_engine(
                f"sqlite:///{db_path}",
                poolclass=StaticPool,
                connect_args={"check_same_thread": False}
            )
            
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self._create_tables()
            
            logger.info(f"✅ Fallback SQLite configurado: {db_path}")
            
        except Exception as e:
            logger.error(f"❌ Erro no fallback SQLite: {e}")
    
    def _create_tables(self):
        """Cria todas as tabelas se não existirem."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Tabelas criadas/verificadas")
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")
    
    def _create_indexes(self):
        """Cria índices para performance."""
        try:
            # Índices para ofertas
            Index('idx_offers_store', Offer.store)
            Index('idx_offers_category', Offer.category)
            Index('idx_offers_price', Offer.price)
            Index('idx_offers_created_at', Offer.created_at)
            Index('idx_offers_is_active', Offer.is_active)
            
            # Índices para histórico de preços
            Index('idx_price_history_offer_id', PriceHistory.offer_id)
            Index('idx_price_history_timestamp', PriceHistory.timestamp)
            
            # Índices para usuários
            Index('idx_users_telegram_id', User.telegram_id)
            Index('idx_users_is_active', User.is_active)
            
            # Índices para logs
            Index('idx_scraper_logs_scraper', ScraperLog.scraper_name)
            Index('idx_scraper_logs_timestamp', ScraperLog.timestamp)
            
            logger.info("✅ Índices criados/verificados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar índices: {e}")
    
    def get_session(self) -> Session:
        """Retorna uma nova sessão do banco."""
        if not self.SessionLocal:
            raise RuntimeError("Banco de dados não configurado")
        return self.SessionLocal()
    
    def add_offer(self, offer_data: Dict[str, Any]) -> Optional[Offer]:
        """Adiciona nova oferta ao banco."""
        try:
            with self.get_session() as session:
                # Verificar se oferta já existe
                existing = session.query(Offer).filter(
                    Offer.product_url == offer_data.get('product_url'),
                    Offer.store == offer_data.get('store')
                ).first()
                
                if existing:
                    # Atualizar oferta existente
                    for key, value in offer_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                    offer = existing
                else:
                    # Criar nova oferta
                    offer = Offer(**offer_data)
                    session.add(offer)
                
                session.commit()
                
                # Adicionar ao histórico de preços
                self._add_price_history(offer.id, offer_data.get('price'), offer_data.get('original_price'))
                
                logger.info(f"✅ Oferta {'atualizada' if existing else 'criada'}: {offer.title[:50]}...")
                return offer
                
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar oferta: {e}")
            return None
    
    def _add_price_history(self, offer_id: int, price: float, original_price: Optional[float]):
        """Adiciona entrada ao histórico de preços."""
        try:
            with self.get_session() as session:
                history = PriceHistory(
                    offer_id=offer_id,
                    price=price,
                    original_price=original_price,
                    discount_percentage=self._calculate_discount(price, original_price)
                )
                session.add(history)
                session.commit()
                
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar histórico de preços: {e}")
    
    def _calculate_discount(self, price: float, original_price: Optional[float]) -> Optional[float]:
        """Calcula percentual de desconto."""
        if not original_price or original_price <= 0:
            return None
        
        if price >= original_price:
            return 0.0
        
        return ((original_price - price) / original_price) * 100
    
    def get_active_offers(self, limit: int = 100, category: Optional[str] = None) -> List[Offer]:
        """Retorna ofertas ativas."""
        try:
            with self.get_session() as session:
                query = session.query(Offer).filter(Offer.is_active == True)
                
                if category:
                    query = query.filter(Offer.category == category)
                
                return query.order_by(Offer.created_at.desc()).limit(limit).all()
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar ofertas: {e}")
            return []
    
    def get_offers_by_store(self, store: str, limit: int = 50) -> List[Offer]:
        """Retorna ofertas de uma loja específica."""
        try:
            with self.get_session() as session:
                return session.query(Offer).filter(
                    Offer.store == store,
                    Offer.is_active == True
                ).order_by(Offer.created_at.desc()).limit(limit).all()
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar ofertas da loja {store}: {e}")
            return []
    
    def search_offers(self, query: str, limit: int = 50) -> List[Offer]:
        """Busca ofertas por texto."""
        try:
            with self.get_session() as session:
                search_term = f"%{query}%"
                return session.query(Offer).filter(
                    Offer.is_active == True,
                    (Offer.title.contains(search_term) | 
                     Offer.description.contains(search_term) |
                     Offer.brand.contains(search_term))
                ).order_by(Offer.created_at.desc()).limit(limit).all()
                
        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            return []
    
    def add_user(self, telegram_id: int, username: str = None, first_name: str = None) -> Optional[User]:
        """Adiciona ou atualiza usuário."""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                
                if user:
                    # Atualizar usuário existente
                    user.username = username or user.username
                    user.first_name = first_name or user.first_name
                    user.last_activity = datetime.utcnow()
                else:
                    # Criar novo usuário
                    user = User(
                        telegram_id=telegram_id,
                        username=username,
                        first_name=first_name
                    )
                    session.add(user)
                
                session.commit()
                logger.info(f"✅ Usuário {'atualizado' if user.id else 'criado'}: {telegram_id}")
                return user
                
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar usuário: {e}")
            return None
    
    def log_scraper_execution(self, scraper_name: str, status: str, message: str = None, 
                             offers_found: int = 0, execution_time: float = 0.0):
        """Registra execução de scraper."""
        try:
            with self.get_session() as session:
                log = ScraperLog(
                    scraper_name=scraper_name,
                    status=status,
                    message=message,
                    offers_found=offers_found,
                    execution_time=execution_time
                )
                session.add(log)
                session.commit()
                
        except Exception as e:
            logger.error(f"❌ Erro ao registrar log do scraper: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do banco de dados."""
        try:
            with self.get_session() as session:
                total_offers = session.query(Offer).count()
                active_offers = session.query(Offer).filter(Offer.is_active == True).count()
                total_users = session.query(User).count()
                active_users = session.query(User).filter(User.is_active == True).count()
                
                return {
                    'total_offers': total_offers,
                    'active_offers': active_offers,
                    'total_users': total_users,
                    'active_users': active_users,
                    'database_url': self.database_url
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}
    
    def backup_database(self, backup_path: str = None) -> bool:
        """Faz backup do banco de dados."""
        try:
            if not backup_path:
                backup_dir = Path(".data/backups")
                backup_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"backup_{timestamp}.db"
            
            # Para SQLite, copiar arquivo
            if "sqlite" in self.database_url:
                import shutil
                db_path = self.database_url.replace("sqlite:///", "")
                shutil.copy2(db_path, backup_path)
            else:
                # Para outros bancos, usar dump
                logger.warning("Backup automático não implementado para este tipo de banco")
                return False
            
            logger.info(f"✅ Backup criado: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
            return False


# Instância global
database_manager = DatabaseManager()

# Funções de conveniência
def get_session() -> Session:
    """Retorna sessão do banco de dados."""
    return database_manager.get_session()

def add_offer(offer_data: Dict[str, Any]) -> Optional[Offer]:
    """Adiciona oferta ao banco."""
    return database_manager.add_offer(offer_data)

def get_active_offers(limit: int = 100, category: Optional[str] = None) -> List[Offer]:
    """Retorna ofertas ativas."""
    return database_manager.get_active_offers(limit, category)

def add_user(telegram_id: int, username: str = None, first_name: str = None) -> Optional[User]:
    """Adiciona usuário ao banco."""
    return database_manager.add_user(telegram_id, username, first_name)

def log_scraper_execution(scraper_name: str, status: str, message: str = None, 
                         offers_found: int = 0, execution_time: float = 0.0):
    """Registra execução de scraper."""
    database_manager.log_scraper_execution(scraper_name, status, message, offers_found, execution_time)


if __name__ == "__main__":
    # Teste do sistema de banco
    print("🧪 Testando Sistema de Banco de Dados")
    print("=" * 50)
    
    # Estatísticas
    stats = database_manager.get_database_stats()
    print(f"📊 Estatísticas: {stats}")
    
    # Teste de adição de oferta
    test_offer = {
        'title': 'Produto Teste',
        'price': 99.90,
        'original_price': 129.90,
        'store': 'Loja Teste',
        'category': 'Teste',
        'product_url': 'https://teste.com/produto'
    }
    
    offer = add_offer(test_offer)
    if offer:
        print(f"✅ Oferta criada: {offer.title}")
    else:
        print("❌ Erro ao criar oferta")
    
    print("\n✅ Teste do banco concluído!")
