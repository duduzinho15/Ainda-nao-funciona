"""
Core module for Garimpeiro Geek system
"""
from .models import Oferta, ScraperSettings, Periodo
from .data_service import DataService
from .storage import PreferencesStorage, preferences_storage

__all__ = [
    "Oferta", "ScraperSettings", "Periodo", "DataService", 
    "PreferencesStorage", "preferences_storage"
]
