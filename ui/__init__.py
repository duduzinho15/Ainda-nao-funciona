"""
Módulo de interface do usuário do sistema Garimpeiro Geek.
Contém componentes reutilizáveis e abas do dashboard.
"""

from .config_tab import create_config_tab
from .controls_tab import create_controls_tab

__all__ = ["create_config_tab", "create_controls_tab"]
