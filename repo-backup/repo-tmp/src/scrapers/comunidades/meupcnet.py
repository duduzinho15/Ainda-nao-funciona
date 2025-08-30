# shim temporário — será removido depois
import warnings

warnings.warn(
    "Use 'src.scrapers.meupc.meupc_scraper' instead of 'meupc_scraper'",
    DeprecationWarning,
    stacklevel=2,
)

try:
    from src.scrapers.meupc.meupc_scraper import MeuPCScraper
except ImportError:
    # Fallback para compatibilidade
    MeuPCScraper = None
