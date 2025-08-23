"""
Módulo de Testes do Garimpeiro Geek
Testes automatizados para todas as funcionalidades
"""

__version__ = "2.0.0"
__author__ = "Eduardo Vitorino"

# Configuração de testes
import pytest
import sys
from pathlib import Path

# Adicionar diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

