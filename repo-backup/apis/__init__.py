"""
Módulo de APIs do Garimpeiro Geek
Integração com APIs externas de e-commerce
"""

__version__ = "2.0.0"
__author__ = "Eduardo Vitorino"

from .base_api import BaseAPI
from .api_manager import APIManager
from .rate_limiter import RateLimiter

__all__ = [
    "BaseAPI",
    "APIManager",
    "RateLimiter"
]

