"""
Configurações para as Melhorias Técnicas do Bot Garimpeiro Geek

Este arquivo contém todas as configurações relacionadas aos sistemas de:
- Cache
- Rate Limiting
- Monitoramento de Saúde
- Métricas de Performance
"""

# Configurações do Sistema de Cache
CACHE_CONFIG = {
    # Cache principal
    "main_cache": {
        "max_size": 2000,
        "default_ttl": 1800,  # 30 minutos
        "cleanup_interval": 300,  # 5 minutos
        "enable_persistence": True,
        "persistence_file": "cache_backup.pkl",
    },
    # Cache para requisições HTTP
    "http_cache": {
        "max_size": 500,
        "default_ttl": 900,  # 15 minutos
        "cleanup_interval": 180,  # 3 minutos
        "enable_persistence": False,
    },
    # Cache para resultados de scrapers
    "scraper_cache": {
        "max_size": 1000,
        "default_ttl": 3600,  # 1 hora
        "cleanup_interval": 600,  # 10 minutos
        "enable_persistence": True,
        "persistence_file": "scraper_cache.pkl",
    },
}

# Configurações do Sistema de Rate Limiting
RATE_LIMITER_CONFIG = {
    # Estratégias padrão
    "strategies": {
        "default_api": {
            "type": "fixed_window",
            "max_requests": 100,
            "window_seconds": 3600,  # 100 req/hora
        },
        "scraper": {
            "type": "sliding_window",
            "max_requests": 30,
            "window_seconds": 300,  # 30 req/5min
        },
        "amazon": {
            "type": "adaptive",
            "initial_max_requests": 20,
            "window_seconds": 3600,
            "min_requests": 5,
            "max_requests": 50,
        },
        "aliexpress": {
            "type": "fixed_window",
            "max_requests": 50,
            "window_seconds": 3600,  # 50 req/hora
        },
        "magalu": {
            "type": "sliding_window",
            "max_requests": 20,
            "window_seconds": 300,  # 20 req/5min
        },
        "promobit": {
            "type": "adaptive",
            "initial_max_requests": 15,
            "window_seconds": 300,
            "min_requests": 3,
            "max_requests": 30,
        },
        "awin": {
            "type": "fixed_window",
            "max_requests": 200,
            "window_seconds": 3600,  # 200 req/hora
        },
    },
    # Configurações gerais
    "general": {
        "monitor_interval": 60,  # Verificação a cada minuto
        "cleanup_interval": 300,  # Limpeza a cada 5 minutos
        "alert_threshold": 3,  # Alertas após 3 falhas consecutivas
    },
}

# Configurações do Sistema de Monitoramento de Saúde
HEALTH_MONITOR_CONFIG = {
    # Verificadores padrão
    "default_checkers": {
        "system_resources": {
            "type": "system",
            "interval": 30,  # 30 segundos
            "timeout": 10,
            "retries": 2,
        },
        "internet_connectivity": {
            "type": "external_service",
            "interval": 60,  # 1 minuto
            "timeout": 15,
            "retries": 2,
        },
        "database_connection": {
            "type": "database",
            "interval": 120,  # 2 minutos
            "timeout": 10,
            "retries": 2,
        },
    },
    # Verificadores para scrapers
    "scraper_checkers": {
        "amazon_scraper": {
            "interval": 300,  # 5 minutos
            "timeout": 30,
            "retries": 3,
        },
        "aliexpress_scraper": {
            "interval": 300,  # 5 minutos
            "timeout": 30,
            "retries": 3,
        },
        "magalu_scraper": {
            "interval": 300,  # 5 minutos
            "timeout": 30,
            "retries": 3,
        },
        "promobit_scraper": {
            "interval": 300,  # 5 minutos
            "timeout": 30,
            "retries": 3,
        },
        "awin_api": {
            "interval": 120,  # 2 minutos
            "timeout": 20,
            "retries": 2,
        },
    },
    # Configurações gerais
    "general": {
        "check_interval": 60,  # Verificação principal a cada minuto
        "alert_threshold": 3,  # Alertas após 3 falhas consecutivas
        "db_path": "health_monitor.db",
    },
}

# Configurações do Sistema de Métricas de Performance
PERFORMANCE_METRICS_CONFIG = {
    # Métricas do sistema
    "system_metrics": {
        "cpu_usage": {
            "type": "gauge",
            "unit": "percent",
            "collection_interval": 10,  # 10 segundos
            "retention_hours": 24,
        },
        "memory_usage": {
            "type": "gauge",
            "unit": "percent",
            "collection_interval": 10,
            "retention_hours": 24,
        },
        "disk_usage": {
            "type": "gauge",
            "unit": "percent",
            "collection_interval": 30,  # 30 segundos
            "retention_hours": 24,
        },
        "network_io": {
            "type": "gauge",
            "unit": "bytes",
            "collection_interval": 10,
            "retention_hours": 24,
        },
    },
    # Métricas da aplicação
    "app_metrics": {
        "requests_total": {"type": "counter", "unit": "count", "retention_hours": 24},
        "requests_success": {"type": "counter", "unit": "count", "retention_hours": 24},
        "requests_failed": {"type": "counter", "unit": "count", "retention_hours": 24},
        "response_time": {
            "type": "histogram",
            "unit": "milliseconds",
            "retention_hours": 24,
        },
        "success_rate": {
            "type": "gauge",
            "unit": "success_rate",
            "retention_hours": 24,
        },
    },
    # Configurações gerais
    "general": {
        "collection_interval": 10,  # Coleta a cada 10 segundos
        "anomaly_detection_enabled": True,
        "anomaly_threshold": 2.0,  # Desvio padrão para detecção
        "db_path": "performance_metrics.db",
        "max_points_per_metric": 1000,
    },
}

# Configurações de Jobs Agendados
SCHEDULED_JOBS_CONFIG = {
    "health_monitoring": {
        "enabled": True,
        "start_delay": 60,  # Inicia após 1 minuto
    },
    "metrics_collection": {
        "enabled": True,
        "start_delay": 30,  # Inicia após 30 segundos
    },
    "cache_cleanup": {
        "enabled": True,
        "interval": 21600,  # 6 horas
        "start_delay": 900,  # 15 minutos
    },
    "metrics_backup": {
        "enabled": True,
        "interval": 43200,  # 12 horas
        "start_delay": 1200,  # 20 minutos
    },
    "rate_limited_verifications": {
        "awin": {
            "enabled": True,
            "interval": 7200,  # 2 horas
            "start_delay": 300,  # 5 minutos
        },
        "aliexpress": {
            "enabled": True,
            "interval": 10800,  # 3 horas
            "start_delay": 600,  # 10 minutos
        },
    },
}

# Configurações de Alertas
ALERTS_CONFIG = {
    "health_alerts": {
        "enabled": True,
        "critical_notification": True,  # Notifica admin em caso crítico
        "telegram_notification": True,
        "log_level": "WARNING",
    },
    "performance_alerts": {
        "enabled": True,
        "anomaly_notification": True,
        "threshold_alerts": True,
        "log_level": "WARNING",
    },
    "rate_limit_alerts": {
        "enabled": True,
        "block_notification": True,
        "log_level": "INFO",
    },
}

# Configurações de Logging
LOGGING_CONFIG = {
    "cache_system": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
    "rate_limiter": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
    "health_monitor": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
    "performance_metrics": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
}

# Configurações de Persistência
PERSISTENCE_CONFIG = {
    "enabled": True,
    "backup_interval": 3600,  # 1 hora
    "max_backup_files": 7,  # Mantém 7 backups
    "compression": True,
    "encryption": False,  # Para produção, considerar True
}

# Configurações de Performance
PERFORMANCE_CONFIG = {
    "max_concurrent_checks": 10,
    "max_concurrent_metrics": 5,
    "thread_pool_size": 4,
    "async_timeout": 30,  # 30 segundos
    "retry_delay": 5,  # 5 segundos
    "max_retries": 3,
}

# Configurações de Segurança
SECURITY_CONFIG = {
    "admin_only_commands": ["status", "metrics", "cache", "health", "buscar", "oferta"],
    "rate_limit_admin_commands": False,  # Admin não tem rate limit
    "log_sensitive_data": False,
    "encrypt_persistence": False,  # Para produção, considerar True
}
