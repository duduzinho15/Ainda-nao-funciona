# shim temporário — será removido depois
import warnings

warnings.warn(
    "Use 'src.scrapers.casas_bahia.casas_bahia_scraper' instead of 'casas_bahia_scraper'",
    DeprecationWarning,
)

try:
    from src.scrapers.casas_bahia.casas_bahia_scraper import *
except ImportError:
    # Fallback para compatibilidade
    pass
