# shim temporário — será removido depois
import warnings

warnings.warn(
    "Use 'src.scrapers.promobit.promobit_scraper' instead of 'promobit_scraper'",
    DeprecationWarning,
)

try:
    from src.scrapers.promobit.promobit_scraper import *
except ImportError:
    # Fallback para compatibilidade
    pass
