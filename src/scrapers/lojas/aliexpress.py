# shim temporário — será removido depois
import warnings

warnings.warn(
    "Use 'src.scrapers.aliexpress.aliexpress_scraper' instead of 'aliexpress_scraper'",
    DeprecationWarning,
)

try:
    from src.scrapers.aliexpress.aliexpress_scraper import *
except ImportError:
    # Fallback para compatibilidade
    pass
