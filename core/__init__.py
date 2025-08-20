"""
Core module for Garimpeiro Geek system
"""
from .models import Oferta, ScraperSettings, Periodo
from .data_service import DataService
from .storage import PreferencesStorage, preferences_storage
from .csv_exporter import CSVExporter
from .live_logs import live_log_reader
from .metrics import MetricsAggregator

# Instâncias globais
csv_exporter = CSVExporter()

__all__ = [
    "Oferta", "ScraperSettings", "Periodo", "DataService", 
    "PreferencesStorage", "preferences_storage", "csv_exporter", "live_log_reader",
    "MetricsAggregator"
]
