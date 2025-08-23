# shim temporário — será removido depois
import warnings

warnings.warn(
    "Use 'src.scrapers.amazon.amazon_scraper' instead of 'amazon_scraper'",
    DeprecationWarning,
)

try:
    from src.scrapers.amazon.amazon_scraper import *
except ImportError:
    # Fallback para compatibilidade
    pass
