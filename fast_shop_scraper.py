# shim temporário — será removido depois
import warnings
warnings.warn("Use 'src.scrapers.fast_shop.fast_shop_scraper' instead of 'fast_shop_scraper'", DeprecationWarning)

try:
    from src.scrapers.fast_shop.fast_shop_scraper import *
except ImportError:
    # Fallback para compatibilidade
    pass
