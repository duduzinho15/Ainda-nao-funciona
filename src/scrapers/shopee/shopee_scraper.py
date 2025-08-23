# shim temporário — será removido depois
import warnings

warnings.warn(
    "Use 'src.scrapers.shopee.shopee_scraper' instead of 'shopee_scraper'",
    DeprecationWarning,
)

try:
    from src.scrapers.shopee.shopee_scraper import *
except ImportError:
    # Fallback para compatibilidade
    pass
