"""
Sistema de Recomendações de Ofertas Telegram - Garimpeiro Geek
"""

__version__ = "2.0.0"
__author__ = "Garimpeiro Geek Team"
__description__ = "Sistema inteligente de busca e postagem de ofertas"

# Módulos principais
from . import core
from . import ui
from . import app

__all__ = ["core", "ui", "app"]
