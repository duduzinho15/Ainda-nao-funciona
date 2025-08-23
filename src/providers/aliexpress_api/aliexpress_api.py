# shim temporário — será removido depois
import warnings
warnings.warn("Use 'src.providers.aliexpress_api.aliexpress_api' instead of 'aliexpress_api'", DeprecationWarning)

try:
    from src.providers.aliexpress_api.aliexpress_api import *
except ImportError:
    # Fallback para compatibilidade
    pass
