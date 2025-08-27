# shim temporário — será removido depois
import warnings

warnings.warn(
    "Use 'src.providers.shopee_api.shopee_api' instead of 'shopee_api'",
    DeprecationWarning,
)

try:
    from src.providers.shopee_api.shopee_api import *
except ImportError:
    # Fallback para compatibilidade
    pass
