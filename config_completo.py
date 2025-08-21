"""
Configuração Completa do Sistema Garimpeiro Geek.
Integra todos os novos sistemas implementados.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/garimpeiro_geek.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class Config:
    """Configuração centralizada do sistema."""
    
    # ===== CONFIGURAÇÕES BÁSICAS =====
    APP_NAME = "Garimpeiro Geek"
    APP_VERSION = "2.0.0"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # ===== DIRETÓRIOS =====
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / ".data"
    LOGS_DIR = BASE_DIR / "logs"
    BACKUPS_DIR = BASE_DIR / "backups"
    MODELS_DIR = BASE_DIR / ".data" / "models"
    
    # Criar diretórios se não existirem
    for directory in [DATA_DIR, LOGS_DIR, BACKUPS_DIR, MODELS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # ===== TELEGRAM =====
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "")
    
    # ===== BANCO DE DADOS =====
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///garimpeiro_geek.db")
    DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    
    # ===== REDIS =====
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    
    # ===== AUTENTICAÇÃO =====
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # ===== MACHINE LEARNING =====
    ML_MODEL_PATH = MODELS_DIR / "recommendation_model.json"
    ML_MIN_INTERACTIONS = int(os.getenv("ML_MIN_INTERACTIONS", "3"))
    ML_SIMILARITY_THRESHOLD = float(os.getenv("ML_SIMILARITY_THRESHOLD", "0.3"))
    ML_CACHE_TTL_HOURS = int(os.getenv("ML_CACHE_TTL_HOURS", "1"))
    
    # ===== ANÁLISE DE PREÇOS =====
    PRICE_ANALYSIS_MIN_DATA_POINTS = int(os.getenv("PRICE_ANALYSIS_MIN_DATA_POINTS", "10"))
    PRICE_ANALYSIS_ANOMALY_THRESHOLD = float(os.getenv("PRICE_ANALYSIS_ANOMALY_THRESHOLD", "0.95"))
    PRICE_ANALYSIS_TREND_CONFIDENCE = float(os.getenv("PRICE_ANALYSIS_TREND_CONFIDENCE", "0.8"))
    PRICE_ANALYSIS_CACHE_TTL_HOURS = int(os.getenv("PRICE_ANALYSIS_CACHE_TTL_HOURS", "2"))
    
    # ===== API =====
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8080"))
    API_WORKERS = int(os.getenv("API_WORKERS", "4"))
    API_MAX_REQUESTS = int(os.getenv("API_MAX_REQUESTS", "1000"))
    API_MAX_REQUESTS_PER_MINUTE = int(os.getenv("API_MAX_REQUESTS_PER_MINUTE", "60"))
    
    # ===== SCRAPERS =====
    SCRAPERS_CONFIG_FILE = DATA_DIR / "config" / "scrapers.json"
    SCRAPERS_DEFAULT_ENABLED = os.getenv("SCRAPERS_DEFAULT_ENABLED", "true").lower() == "true"
    SCRAPERS_RATE_LIMIT_DELAY = float(os.getenv("SCRAPERS_RATE_LIMIT_DELAY", "1.0"))
    
    # ===== NOTIFICAÇÕES =====
    NOTIFICATIONS_ENABLED = os.getenv("NOTIFICATIONS_ENABLED", "true").lower() == "true"
    NOTIFICATIONS_EMAIL = os.getenv("NOTIFICATIONS_EMAIL", "")
    NOTIFICATIONS_SMTP_SERVER = os.getenv("NOTIFICATIONS_SMTP_SERVER", "")
    NOTIFICATIONS_SMTP_PORT = int(os.getenv("NOTIFICATIONS_SMTP_PORT", "587"))
    
    # ===== MONITORAMENTO =====
    MONITORING_ENABLED = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
    MONITORING_PROMETHEUS_PORT = int(os.getenv("MONITORING_PROMETHEUS_PORT", "9090"))
    MONITORING_GRAFANA_PORT = int(os.getenv("MONITORING_GRAFANA_PORT", "3000"))
    
    # ===== BACKUP =====
    BACKUP_ENABLED = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
    BACKUP_SCHEDULE = os.getenv("BACKUP_SCHEDULE", "0 2 * * *")  # 2 AM diariamente
    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    
    # ===== COMPLIANCE E CI =====
    GG_SEED = os.getenv("GG_SEED", "")
    GG_FREEZE_TIME = os.getenv("GG_FREEZE_TIME", "")
    GG_ALLOW_SCRAPING = os.getenv("GG_ALLOW_SCRAPING", "1") == "1"
    GG_REPORT = os.getenv("GG_REPORT", "false").lower() == "true"
    GG_STRICT = os.getenv("GG_STRICT", "false").lower() == "true"
    
    # ===== VALIDAÇÕES =====
    @classmethod
    def validate(cls) -> Dict[str, str]:
        """Valida se as configurações essenciais estão presentes."""
        errors = []
        
        # Validações básicas
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN não configurado")
        
        if not cls.TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID não configurado")
        
        if not cls.ADMIN_USER_ID:
            errors.append("ADMIN_USER_ID não configurado")
        
        # Validações de banco
        if "sqlite" not in cls.DATABASE_URL and "postgresql" not in cls.DATABASE_URL:
            errors.append("DATABASE_URL deve ser SQLite ou PostgreSQL")
        
        # Validações de segurança
        if not cls.JWT_SECRET_KEY:
            errors.append("JWT_SECRET_KEY não configurado")
        
        return errors
    
    @classmethod
    def is_ci_mode(cls) -> bool:
        """Verifica se está em modo CI."""
        return bool(cls.GG_SEED or cls.GG_FREEZE_TIME)
    
    @classmethod
    def is_production(cls) -> bool:
        """Verifica se está em produção."""
        return not cls.DEBUG and not cls.is_ci_mode()
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Retorna configuração do banco de dados."""
        if "sqlite" in cls.DATABASE_URL:
            return {
                "url": cls.DATABASE_URL,
                "poolclass": "StaticPool",
                "connect_args": {"check_same_thread": False}
            }
        else:
            return {
                "url": cls.DATABASE_URL,
                "pool_pre_ping": True,
                "pool_recycle": 300,
                "pool_size": cls.DATABASE_POOL_SIZE,
                "max_overflow": cls.DATABASE_MAX_OVERFLOW
            }
    
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """Retorna configuração do Redis."""
        return {
            "url": cls.REDIS_URL,
            "password": cls.REDIS_PASSWORD if cls.REDIS_PASSWORD else None,
            "db": cls.REDIS_DB,
            "decode_responses": True
        }
    
    @classmethod
    def print_status(cls):
        """Imprime status das configurações."""
        print("🔧 CONFIGURAÇÕES DO SISTEMA GARIMPEIRO GEEK 2.0")
        print("=" * 60)
        
        # Informações básicas
        print(f"📱 Aplicação: {cls.APP_NAME} v{cls.APP_VERSION}")
        print(f"🐛 Debug: {'✅ ATIVO' if cls.DEBUG else '❌ DESABILITADO'}")
        print(f"🏭 Modo: {'🔄 CI' if cls.is_ci_mode() else '🚀 PRODUÇÃO' if cls.is_production() else '🛠️ DESENVOLVIMENTO'}")
        
        # Telegram
        print(f"\n📱 Telegram:")
        print(f"  Bot Token: {'✅ Configurado' if cls.TELEGRAM_BOT_TOKEN else '❌ Não configurado'}")
        print(f"  Chat ID: {'✅ Configurado' if cls.TELEGRAM_CHAT_ID else '❌ Não configurado'}")
        print(f"  Admin ID: {'✅ Configurado' if cls.ADMIN_USER_ID else '❌ Não configurado'}")
        
        # Banco de dados
        print(f"\n🗄️ Banco de Dados:")
        db_type = "PostgreSQL" if "postgresql" in cls.DATABASE_URL else "SQLite"
        print(f"  Tipo: {db_type}")
        print(f"  URL: {cls.DATABASE_URL}")
        
        # Redis
        print(f"\n🔴 Redis:")
        print(f"  URL: {cls.REDIS_URL}")
        print(f"  Status: {'✅ Configurado' if cls.REDIS_URL != 'redis://localhost:6379' else '⚠️ Padrão local'}")
        
        # Machine Learning
        print(f"\n🧠 Machine Learning:")
        print(f"  Modelo: {'✅ Configurado' if cls.ML_MODEL_PATH.exists() else '❌ Não treinado'}")
        print(f"  Interações mínimas: {cls.ML_MIN_INTERACTIONS}")
        print(f"  Threshold similaridade: {cls.ML_SIMILARITY_THRESHOLD}")
        
        # API
        print(f"\n🌐 API:")
        print(f"  Host: {cls.API_HOST}")
        print(f"  Porta: {cls.API_PORT}")
        print(f"  Workers: {cls.API_WORKERS}")
        
        # Scrapers
        print(f"\n🕷️ Scrapers:")
        print(f"  Config: {'✅ Configurado' if cls.SCRAPERS_CONFIG_FILE.exists() else '❌ Não configurado'}")
        print(f"  Padrão habilitado: {'✅ Sim' if cls.SCRAPERS_DEFAULT_ENABLED else '❌ Não'}")
        
        # Monitoramento
        print(f"\n📊 Monitoramento:")
        print(f"  Habilitado: {'✅ Sim' if cls.MONITORING_ENABLED else '❌ Não'}")
        print(f"  Prometheus: Porta {cls.MONITORING_PROMETHEUS_PORT}")
        print(f"  Grafana: Porta {cls.MONITORING_GRAFANA_PORT}")
        
        # Backup
        print(f"\n💾 Backup:")
        print(f"  Habilitado: {'✅ Sim' if cls.BACKUP_ENABLED else '❌ Não'}")
        print(f"  Agendamento: {cls.BACKUP_SCHEDULE}")
        print(f"  Retenção: {cls.BACKUP_RETENTION_DAYS} dias")
        
        # Compliance
        print(f"\n🔒 Compliance:")
        print(f"  GG_SEED: {'✅ Configurado' if cls.GG_SEED else '❌ Não configurado'}")
        print(f"  GG_FREEZE_TIME: {'✅ Configurado' if cls.GG_FREEZE_TIME else '❌ Não configurado'}")
        print(f"  GG_ALLOW_SCRAPING: {'✅ Sim' if cls.GG_ALLOW_SCRAPING else '❌ Não'}")
        
        print("\n" + "=" * 60)
        
        # Validações
        errors = cls.validate()
        if errors:
            print("❌ ERROS DE CONFIGURAÇÃO:")
            for error in errors:
                print(f"  • {error}")
        else:
            print("✅ Todas as configurações estão válidas!")
        
        print("=" * 60)

# Instância global
config = Config()

# Funções de conveniência
def get_config() -> Config:
    """Retorna instância da configuração."""
    return config

def is_ci_mode() -> bool:
    """Verifica se está em modo CI."""
    return config.is_ci_mode()

def is_production() -> bool:
    """Verifica se está em produção."""
    return config.is_production()

def print_config_status():
    """Imprime status das configurações."""
    config.print_status()

if __name__ == "__main__":
    # Testar configuração
    print_config_status()
