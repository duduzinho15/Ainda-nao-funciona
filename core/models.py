"""
Data models for Garimpeiro Geek system
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class Periodo(Enum):
    """Períodos de filtro disponíveis"""
    DIA_24H = "24h"
    SEMANA_7D = "7d"
    MES_30D = "30d"
    TODOS = "all"

@dataclass
class Oferta:
    """Modelo de uma oferta de produto"""
    titulo: str
    loja: str
    preco: Optional[float]
    preco_original: Optional[float]
    url: str
    imagem_url: Optional[str]
    created_at: datetime
    fonte: str
    
    def preco_formatado(self) -> str:
        """Retorna preço formatado em pt-BR"""
        if self.preco is None:
            return "N/A"
        return f"R$ {self.preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    def preco_original_formatado(self) -> str:
        """Retorna preço original formatado em pt-BR"""
        if self.preco_original is None:
            return "N/A"
        return f"R$ {self.preco_original:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@dataclass
class ScraperSettings:
    """Configurações para scrapers"""
    timeout: int = 30
    retries: int = 3
    interval_ms: int = 1000
    max_concurrency: int = 5
    user_agent_rotation: bool = True
    custom_user_agent: Optional[str] = None
    proxies: List[str] = None
    save_html_debug: bool = False

@dataclass
class MetricsSnapshot:
    """Snapshot de métricas do dashboard"""
    total_ofertas: int
    lojas_ativas: int
    preco_medio: Optional[float]
    periodo: Periodo
    timestamp: datetime
    distribuicao_lojas: dict[str, int]
    
    def preco_medio_formatado(self) -> str:
        """Retorna preço médio formatado"""
        if self.preco_medio is None:
            return "R$ 0,00"
        return f"R$ {self.preco_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
