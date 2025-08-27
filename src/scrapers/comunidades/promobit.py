# shim temporário — será removido depois
import warnings

warnings.warn(
    "Use 'src.scrapers.promobit.promobit_scraper' instead of 'promobit_scraper'",
    DeprecationWarning,
    stacklevel=2,
)

try:
    from src.scrapers.promobit.promobit_scraper import PromobitScraper
except ImportError:
    # Fallback para compatibilidade
    PromobitScraper = None
