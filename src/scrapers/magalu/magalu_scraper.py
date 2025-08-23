# shim temporário — será removido depois
import warnings

warnings.warn(
    "Use 'src.scrapers.magalu.magalu_scraper' instead of 'magalu_scraper'",
    DeprecationWarning,
)

try:
    from src.scrapers.magalu.magalu_scraper import *
except ImportError:
    # Fallback para compatibilidade
    pass
