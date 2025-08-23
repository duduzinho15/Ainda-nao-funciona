# shim temporário — será removido depois
import warnings
warnings.warn("Use 'src.scrapers.submarino.submarino_scraper' instead of 'submarino_scraper'", DeprecationWarning)

try:
    from src.scrapers.submarino.submarino_scraper import *
except ImportError:
    # Fallback para compatibilidade
    pass
