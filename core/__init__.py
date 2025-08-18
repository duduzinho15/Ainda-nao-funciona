"""
Módulo core do sistema Garimpeiro Geek.
Contém modelos, configurações, métricas e utilitários principais.
"""

from .models import Oferta, MetricsSnapshot, ScraperSettings
from .settings import DashboardSettings, ScraperConfig, BotConfig
from .metrics import MetricsAggregator
from .storage import ConfigStorage
from .logging_setup import setup_logging

__all__ = [
    "Oferta",
    "MetricsSnapshot",
    "ScraperSettings",
    "DashboardSettings",
    "ScraperConfig",
    "BotConfig",
    "MetricsAggregator",
    "ConfigStorage",
    "setup_logging",
]
