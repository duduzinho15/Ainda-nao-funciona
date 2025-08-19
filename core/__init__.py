"""
Core module for Garimpeiro Geek system
"""
from .models import Oferta, ScraperSettings
from .data_service import DataService
from .storage import UserPreferences

__all__ = ["Oferta", "ScraperSettings", "DataService", "UserPreferences"]
