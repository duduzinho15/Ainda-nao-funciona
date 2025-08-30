# shim temporário — será removido depois
import warnings

warnings.warn(
    "Use 'src.providers.mercadolivre.mercadolivre_api' instead of 'mercadolivre_api'",
    DeprecationWarning,
)

try:
    from src.providers.mercadolivre.mercadolivre_api import *
except ImportError:
    # Fallback para compatibilidade
    pass
