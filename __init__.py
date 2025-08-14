"""
Sistema de Recomendações de Ofertas Telegram - Garimpeiro Geek

Este arquivo __init__.py ajuda a configurar o Python path corretamente
para resolver problemas de importação no VS Code/Cursor.
"""

import sys
import os

# Adiciona o diretório do ambiente virtual ao Python path
def setup_python_path():
    """Configura o Python path para incluir o ambiente virtual."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    venv_path = os.path.join(current_dir, 'venv', 'Lib', 'site-packages')
    
    if os.path.exists(venv_path) and venv_path not in sys.path:
        sys.path.insert(0, venv_path)
        print(f"✅ Python path configurado: {venv_path}")
    
    # Adiciona o diretório atual ao path
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

# Configura o Python path automaticamente
setup_python_path()

# Versão do projeto
__version__ = "1.0.0"
__author__ = "Garimpeiro Geek Team"
__description__ = "Bot do Telegram para busca automática de ofertas"

print(f"🚀 Garimpeiro Geek v{__version__} - Python path configurado!")
