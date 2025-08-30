"""
Módulo Core do Garimpeiro Geek
Sistema de Recomendações de Ofertas via Telegram
"""

__version__ = "2.0.0"
__author__ = "Eduardo Vitorino"

# Importar componentes principais
from .storage import PreferencesStorage
from .database import Database
from .metrics import MetricsCollector
from .live_logs import LiveLogReader
from .logging_setup import setup_logging
from .affiliate_converter import AffiliateConverter

__all__ = [
    "PreferencesStorage",
    "Database", 
    "MetricsCollector",
    "LiveLogReader",
    "setup_logging",
    "AffiliateConverter"
]
