# shim temporário — será removido depois
import warnings
warnings.warn("Use 'src.scrapers.meupc.meupc_scraper' instead of 'meupc_scraper'", DeprecationWarning)

try:
    from src.scrapers.meupc.meupc_scraper import *
except ImportError:
    # Fallback para compatibilidade
    pass
