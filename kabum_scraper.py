# shim temporário — será removido depois
import warnings
warnings.warn("Use 'src.scrapers.kabum.kabum_scraper' instead of 'kabum_scraper'", DeprecationWarning)

try:
    from src.scrapers.kabum.kabum_scraper import *
except ImportError:
    # Fallback para compatibilidade
    pass
