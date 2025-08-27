"""
Configurações do sistema Garimpeiro Geek

Este arquivo contém todas as configurações necessárias para o funcionamento
do sistema, incluindo tokens do Telegram, IDs de canais e configurações de admin.
"""

import os

# ============================================================================
# CONFIGURAÇÕES DO TELEGRAM
# ============================================================================

# Token do bot (obter via @BotFather)
TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN", "SEU_TOKEN_AQUI"  # Substitua pelo token real
)

# ID do canal principal para postagem de ofertas
TELEGRAM_CHANNEL_ID = os.getenv(
    "TELEGRAM_CHANNEL_ID", "@garimpeirogeek_ofertas"  # Substitua pelo ID real do canal
)

# IDs dos administradores (usuários que podem usar comandos do bot)
TELEGRAM_ADMIN_IDS = [
    int(admin_id)
    for admin_id in os.getenv(
        "TELEGRAM_ADMIN_IDS",
        "123456789,987654321",  # Substitua pelos IDs reais dos admins
    ).split(",")
]

# ============================================================================
# CONFIGURAÇÕES DO SISTEMA
# ============================================================================

# Modo de execução
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Intervalo de verificação de posts agendados (em segundos)
SCHEDULED_POSTS_CHECK_INTERVAL = int(os.getenv("SCHEDULED_POSTS_CHECK_INTERVAL", "60"))

# Máximo de ofertas na fila
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "100"))

# Máximo de posts agendados
MAX_SCHEDULED_POSTS = int(os.getenv("MAX_SCHEDULED_POSTS", "50"))

# ============================================================================
# CONFIGURAÇÕES DE LOGGING
# ============================================================================

# Nível de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Arquivo de log
LOG_FILE = os.getenv("LOG_FILE", "logs/garimpeirogeek.log")

# ============================================================================
# CONFIGURAÇÕES DE MÉTRICAS
# ============================================================================

# Habilitar métricas
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "True").lower() == "true"

# Intervalo de coleta de métricas (em segundos)
METRICS_COLLECTION_INTERVAL = int(os.getenv("METRICS_COLLECTION_INTERVAL", "300"))

# ============================================================================
# CONFIGURAÇÕES DE VALIDAÇÃO
# ============================================================================

# Timeout para validação de URLs (em segundos)
URL_VALIDATION_TIMEOUT = int(os.getenv("URL_VALIDATION_TIMEOUT", "10"))

# Máximo de tentativas de validação
MAX_VALIDATION_ATTEMPTS = int(os.getenv("MAX_VALIDATION_ATTEMPTS", "3"))

# ============================================================================
# CONFIGURAÇÕES DE SEGURANÇA
# ============================================================================

# Chave secreta para assinatura de webhooks
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "sua_chave_secreta_aqui")

# Lista de IPs permitidos para webhooks
ALLOWED_WEBHOOK_IPS = os.getenv("ALLOWED_WEBHOOK_IPS", "127.0.0.1,::1").split(",")

# ============================================================================
# CONFIGURAÇÕES DE BANCO DE DADOS
# ============================================================================

# URL do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///garimpeirogeek.db")

# Pool de conexões
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))

# ============================================================================
# CONFIGURAÇÕES DE CACHE
# ============================================================================

# Tempo de vida do cache (em segundos)
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))

# Tamanho máximo do cache
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))

# ============================================================================
# CONFIGURAÇÕES DE NOTIFICAÇÕES
# ============================================================================

# Habilitar notificações de erro
ENABLE_ERROR_NOTIFICATIONS = (
    os.getenv("ENABLE_ERROR_NOTIFICATIONS", "True").lower() == "true"
)

# Chat ID para notificações de erro
ERROR_NOTIFICATION_CHAT_ID = os.getenv(
    "ERROR_NOTIFICATION_CHAT_ID", TELEGRAM_CHANNEL_ID
)

# ============================================================================
# VALIDAÇÃO DE CONFIGURAÇÕES
# ============================================================================


def validate_config():
    """Valida se todas as configurações obrigatórias estão definidas"""
    required_configs = [
        ("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
        ("TELEGRAM_CHANNEL_ID", TELEGRAM_CHANNEL_ID),
        ("TELEGRAM_ADMIN_IDS", TELEGRAM_ADMIN_IDS),
    ]

    missing_configs = []

    for config_name, config_value in required_configs:
        if not config_value or config_value == "SEU_TOKEN_AQUI":
            missing_configs.append(config_name)

    if missing_configs:
        raise ValueError(
            f"Configurações obrigatórias não definidas: {', '.join(missing_configs)}\n"
            "Configure as variáveis de ambiente ou edite o arquivo config.py"
        )

    return True


# ============================================================================
# CONFIGURAÇÕES DE DESENVOLVIMENTO
# ============================================================================

if DEBUG:
    # Configurações específicas para desenvolvimento
    LOG_LEVEL = "DEBUG"
    ENABLE_METRICS = True
    CACHE_TTL = 60  # Cache menor para desenvolvimento

# ============================================================================
# EXPORTAÇÃO DAS CONFIGURAÇÕES
# ============================================================================

__all__ = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHANNEL_ID",
    "TELEGRAM_ADMIN_IDS",
    "DEBUG",
    "SCHEDULED_POSTS_CHECK_INTERVAL",
    "MAX_QUEUE_SIZE",
    "MAX_SCHEDULED_POSTS",
    "LOG_LEVEL",
    "LOG_FILE",
    "ENABLE_METRICS",
    "METRICS_COLLECTION_INTERVAL",
    "URL_VALIDATION_TIMEOUT",
    "MAX_VALIDATION_ATTEMPTS",
    "WEBHOOK_SECRET",
    "ALLOWED_WEBHOOK_IPS",
    "DATABASE_URL",
    "DATABASE_POOL_SIZE",
    "CACHE_TTL",
    "CACHE_MAX_SIZE",
    "ENABLE_ERROR_NOTIFICATIONS",
    "ERROR_NOTIFICATION_CHAT_ID",
    "validate_config",
]
