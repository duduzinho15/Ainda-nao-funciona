# flet_app/compatibility.py
"""
Arquivo de compatibilidade para resolver problemas de versão do Flet.
Centraliza todas as importações e fallbacks para diferentes versões.
"""

import flet as ft

# ===== CORES =====
def get_error_colors():
    """Retorna cores de erro compatíveis com todas as versões do Flet."""
    # Sempre usar cores padrão - ft.colors não existe em versões antigas
    return {
        'ERROR': '#ffebee',  # Vermelho claro
        'ON_ERROR': '#c62828',  # Vermelho escuro
    }

def get_outline_color(page: ft.Page, fallback='#e0e0e0'):
    """Retorna cor de outline com fallback seguro."""
    try:
        cs = page.theme.color_scheme
        if cs and hasattr(cs, 'outline'):
            return cs.outline
        return fallback
    except:
        return fallback

# ===== ÍCONES =====
def get_theme_icon(is_dark: bool):
    """Retorna ícone de tema compatível com todas as versões."""
    # Sempre usar strings - ft.icons não existe em versões antigas
    if is_dark:
        return "light_mode"
    else:
        return "dark_mode"

# ===== TEMA =====
def safe_theme_colors(page: ft.Page):
    """Retorna cores do tema com fallbacks seguros."""
    try:
        cs = page.theme.color_scheme
        if cs is None:
            return get_default_colors()
        
        return {
            'background': getattr(cs, 'background', '#ffffff'),
            'surface': getattr(cs, 'surface', '#f5f5f5'),
            'on_surface': getattr(cs, 'on_surface', '#000000'),
            'primary': getattr(cs, 'primary', '#1976d2'),
            'on_primary': getattr(cs, 'on_primary', '#ffffff'),
            'outline': getattr(cs, 'outline', '#e0e0e0'),
        }
    except Exception:
        return get_default_colors()

def get_default_colors():
    """Cores padrão caso o tema falhe."""
    return {
        'background': '#ffffff',
        'surface': '#f5f5f5',
        'on_surface': '#000000',
        'primary': '#1976d2',
        'on_primary': '#ffffff',
        'outline': '#e0e0e0',
    }

# ===== CANVAS =====
# Canvas não é suportado em versões antigas do Flet
# Usando containers simples como alternativa

# ===== VERIFICAÇÃO DE VERSÃO =====
def get_flet_version():
    """Retorna a versão do Flet instalada."""
    try:
        return ft.__version__
    except AttributeError:
        return "versão desconhecida"

def check_compatibility():
    """Verifica compatibilidade e retorna avisos."""
    warnings = []
    
    version = get_flet_version()
    if version != "versão desconhecida":
        try:
            major, minor, patch = map(int, version.split('.')[:3])
            if major < 0 or (major == 0 and minor < 20):
                warnings.append(f"Flet {version} pode ter problemas de compatibilidade. Recomendado: >=0.20.0")
        except:
            pass
    
    return warnings
