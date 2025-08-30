"""
Módulo de Scrapers do Garimpeiro Geek
Sistema de coleta de ofertas de múltiplas fontes
"""

__version__ = "2.0.0"
__author__ = "Eduardo Vitorino"

from .base_scraper import BaseScraper
from .scraper_registry import ScraperRegistry
from .scraper_manager import ScraperManager

__all__ = [
    "BaseScraper",
    "ScraperRegistry", 
    "ScraperManager"
]
