# shim temporário — será removido depois
import warnings
warnings.warn("Use 'src.scrapers.americanas.americanas_scraper' instead of 'americanas_scraper'", DeprecationWarning)

try:
    from src.scrapers.americanas.americanas_scraper import *
except ImportError:
    # Fallback para compatibilidade
    pass
