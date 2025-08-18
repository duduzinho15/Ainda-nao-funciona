"""
Modelos de dados para o sistema Garimpeiro Geek.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum


class LogLevel(str, Enum):
    """Níveis de log disponíveis."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Theme(str, Enum):
    """Temas disponíveis para o dashboard."""

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class UIDensity(str, Enum):
    """Densidades de interface disponíveis."""

    COMFORTABLE = "comfortable"
    COMPACT = "compact"


@dataclass
class Oferta:
    """Modelo de uma oferta encontrada pelo scraper."""

    titulo: str
    loja: str
    preco: Optional[float]
    preco_original: Optional[float]
    url: str
    imagem_url: Optional[str]
    created_at: datetime
    fonte: str

    def __post_init__(self):
        """Validação pós-inicialização."""
        if not self.titulo or not self.loja or not self.url:
            raise ValueError("Título, loja e URL são obrigatórios")

        if self.preco is not None and self.preco < 0:
            raise ValueError("Preço não pode ser negativo")

        if self.preco_original is not None and self.preco_original < 0:
            raise ValueError("Preço original não pode ser negativo")


@dataclass
class MetricsSnapshot:
    """Snapshot das métricas calculadas."""

    total_ofertas: int
    lojas_ativas: int
    preco_medio: Optional[float]
    periodo: str
    distribucao_lojas: Dict[str, int]
    timestamp: datetime

    def __post_init__(self):
        """Validação pós-inicialização."""
        if self.total_ofertas < 0:
            raise ValueError("Total de ofertas não pode ser negativo")

        if self.lojas_ativas < 0:
            raise ValueError("Lojas ativas não pode ser negativo")

        if self.preco_medio is not None and self.preco_medio < 0:
            raise ValueError("Preço médio não pode ser negativo")


@dataclass
class ScraperSettings:
    """Configurações do scraper."""

    timeout: int = 30
    retries: int = 3
    intervalo_requisicoes: int = 1000
    max_concorrencia: int = 5
    user_agent_rotation: bool = True
    user_agent_custom: Optional[str] = None
    proxies: List[str] = None
    salvar_html_debug: bool = False

    def __post_init__(self):
        """Validação pós-inicialização."""
        if self.timeout < 1:
            raise ValueError("Timeout deve ser pelo menos 1 segundo")

        if self.retries < 0:
            raise ValueError("Retries não pode ser negativo")

        if self.intervalo_requisicoes < 0:
            raise ValueError("Intervalo entre requisições não pode ser negativo")

        if self.max_concorrencia < 1:
            raise ValueError("Máximo de concorrência deve ser pelo menos 1")

        if self.proxies is None:
            self.proxies = []
