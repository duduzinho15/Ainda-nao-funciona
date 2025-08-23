# shim temporário — será removido depois
import warnings

warnings.warn(
    "Use 'src.scrapers.ricardo_eletro.ricardo_eletro_scraper' instead of 'ricardo_eletro_scraper'",
    DeprecationWarning,
)

try:
    from src.scrapers.ricardo_eletro.ricardo_eletro_scraper import *
except ImportError:
    # Fallback para compatibilidade
    pass
