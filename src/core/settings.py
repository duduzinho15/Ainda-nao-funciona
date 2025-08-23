"""
Configurações do sistema Garimpeiro Geek
Carrega variáveis de ambiente do arquivo .env
"""

import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
ENV_FILE = Path(__file__).parent.parent.parent / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


class Settings:
    """Configurações centralizadas do sistema"""

    # Configurações do Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHANNEL_ID: str = os.getenv("TELEGRAM_CHANNEL_ID", "")
    TELEGRAM_ADMIN_USER_ID: str = os.getenv("TELEGRAM_ADMIN_USER_ID", "")

    # Configurações de banco de dados
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///garimpeiro_geek.db")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "src/db/garimpeiro_geek.db")

    # Configurações de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "src/logs/garimpeiro_geek.log")
    LOG_MAX_SIZE: int = int(os.getenv("LOG_MAX_SIZE", "10MB"))
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Configurações de scraping
    SCRAPING_TIMEOUT: int = int(os.getenv("SCRAPING_TIMEOUT", "30"))
    SCRAPING_RETRY_ATTEMPTS: int = int(os.getenv("SCRAPING_RETRY_ATTEMPTS", "3"))
    SCRAPING_DELAY: float = float(os.getenv("SCRAPING_DELAY", "1.0"))
    SCRAPING_MAX_CONCURRENT: int = int(os.getenv("SCRAPING_MAX_CONCURRENT", "5"))

    # Configurações de afiliados
    AFFILIATE_AMAZON_TAG: str = os.getenv("AFFILIATE_AMAZON_TAG", "garimpeirogeek-20")
    AFFILIATE_MAGALU_TAG: str = os.getenv("AFFILIATE_MAGALU_TAG", "")
    AFFILIATE_AWIN_PUBLISHER_ID: str = os.getenv("AFFILIATE_AWIN_PUBLISHER_ID", "")
    AFFILIATE_RAKUTEN_ID: str = os.getenv("AFFILIATE_RAKUTEN_ID", "")
    AFFILIATE_RAKUTEN_MERCHANT_ID: str = os.getenv("AFFILIATE_RAKUTEN_MERCHANT_ID", "")

    # Configurações de notificações
    NOTIFICATIONS_ENABLED: bool = (
        os.getenv("NOTIFICATIONS_ENABLED", "true").lower() == "true"
    )
    NOTIFICATION_INTERVAL: int = int(
        os.getenv("NOTIFICATION_INTERVAL", "3600")
    )  # segundos

    # Configurações de desenvolvimento
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    TESTING: bool = os.getenv("TESTING", "false").lower() == "true"

    # Configurações de cache
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # segundos

    # Configurações de rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # segundos

    # Configurações de monitoramento
    MONITORING_ENABLED: bool = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
    METRICS_COLLECTION_INTERVAL: int = int(
        os.getenv("METRICS_COLLECTION_INTERVAL", "300")
    )  # segundos

    # Configurações de backup
    BACKUP_ENABLED: bool = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
    BACKUP_INTERVAL: int = int(os.getenv("BACKUP_INTERVAL", "86400"))  # segundos (24h)
    BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))

    @classmethod
    def get_telegram_config(cls) -> Dict[str, Any]:
        """Retorna configurações do Telegram"""
        return {
            "bot_token": cls.TELEGRAM_BOT_TOKEN,
            "channel_id": cls.TELEGRAM_CHANNEL_ID,
            "admin_user_id": cls.TELEGRAM_ADMIN_USER_ID,
        }

    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Retorna configurações do banco de dados"""
        return {
            "url": cls.DATABASE_URL,
            "path": cls.DATABASE_PATH,
        }

    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """Retorna configurações de logging"""
        return {
            "level": cls.LOG_LEVEL,
            "file": cls.LOG_FILE,
            "max_size": cls.LOG_MAX_SIZE,
            "backup_count": cls.LOG_BACKUP_COUNT,
        }

    @classmethod
    def get_scraping_config(cls) -> Dict[str, Any]:
        """Retorna configurações de scraping"""
        return {
            "timeout": cls.SCRAPING_TIMEOUT,
            "retry_attempts": cls.SCRAPING_RETRY_ATTEMPTS,
            "delay": cls.SCRAPING_DELAY,
            "max_concurrent": cls.SCRAPING_MAX_CONCURRENT,
        }

    @classmethod
    def get_affiliate_config(cls) -> Dict[str, Any]:
        """Retorna configurações de afiliados"""
        return {
            "amazon_tag": cls.AFFILIATE_AMAZON_TAG,
            "magalu_tag": cls.AFFILIATE_MAGALU_TAG,
            "awin_publisher_id": cls.AFFILIATE_AWIN_PUBLISHER_ID,
            "rakuten_id": cls.AFFILIATE_RAKUTEN_ID,
            "rakuten_merchant_id": cls.AFFILIATE_RAKUTEN_MERCHANT_ID,
        }

    @classmethod
    def validate_required_settings(cls) -> bool:
        """Valida se as configurações obrigatórias estão definidas"""
        required_settings = [
            cls.TELEGRAM_BOT_TOKEN,
            cls.DATABASE_PATH,
        ]

        missing_settings = [setting for setting in required_settings if not setting]

        if missing_settings:
            print(f"❌ Configurações obrigatórias não definidas: {missing_settings}")
            return False

        return True

    @classmethod
    def print_current_config(cls) -> None:
        """Imprime a configuração atual (sem dados sensíveis)"""
        print("🔧 Configurações atuais do Garimpeiro Geek:")
        print(
            f"  📱 Telegram: {'✅ Configurado' if cls.TELEGRAM_BOT_TOKEN else '❌ Não configurado'}"
        )
        print(f"  🗄️  Banco: {cls.DATABASE_PATH}")
        print(f"  📝 Log: {cls.LOG_LEVEL} -> {cls.LOG_FILE}")
        print(
            f"  🕷️  Scraping: {cls.SCRAPING_TIMEOUT}s timeout, {cls.SCRAPING_RETRY_ATTEMPTS} retries"
        )
        print(f"  🔗 Afiliados: Amazon ({cls.AFFILIATE_AMAZON_TAG})")
        print(f"  🔔 Notificações: {'✅' if cls.NOTIFICATIONS_ENABLED else '❌'}")
        print(f"  🐛 Debug: {'✅' if cls.DEBUG else '❌'}")
        print(f"  📊 Monitoramento: {'✅' if cls.MONITORING_ENABLED else '❌'}")
        print(f"  💾 Backup: {'✅' if cls.BACKUP_ENABLED else '❌'}")


# Instância global das configurações
settings = Settings()


def get_settings() -> Settings:
    """Retorna a instância global das configurações"""
    return settings


def reload_settings() -> None:
    """Recarrega as configurações do arquivo .env"""
    global settings
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE, override=True)
    settings = Settings()


# Validação automática ao importar o módulo
if __name__ == "__main__":
    settings.print_current_config()
    if not settings.validate_required_settings():
        print("\n⚠️  Algumas configurações obrigatórias não estão definidas!")
        print(
            "   Crie um arquivo .env na raiz do projeto com as configurações necessárias."
        )
    else:
        print("\n✅ Todas as configurações obrigatórias estão definidas!")
