"""
Configurações tipadas do sistema Garimpeiro Geek.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
from .models import Theme, UIDensity, LogLevel


@dataclass
class DashboardSettings:
    """Configurações da interface do dashboard."""

    tema: Theme = Theme.SYSTEM
    densidade_ui: UIDensity = UIDensity.COMFORTABLE
    janela_padrao: str = "24h"
    pasta_logs: Path = field(default_factory=lambda: Path("./logs"))
    pasta_exportacao: Path = field(default_factory=lambda: Path("./export"))
    limite_ofertas_tabela: int = 1000
    lojas_ignoradas: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validação pós-inicialização."""
        if self.limite_ofertas_tabela < 100:
            raise ValueError("Limite de ofertas deve ser pelo menos 100")

        # Garantir que as pastas existam
        self.pasta_logs.mkdir(parents=True, exist_ok=True)
        self.pasta_exportacao.mkdir(parents=True, exist_ok=True)


@dataclass
class ScraperConfig:
    """Configurações do sistema de scraping."""

    timeout: int = 30
    retries: int = 3
    intervalo_requisicoes: int = 1000
    max_concorrencia: int = 5
    user_agent_rotation: bool = True
    user_agent_custom: Optional[str] = None
    proxies: List[str] = field(default_factory=list)
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


@dataclass
class BotConfig:
    """Configurações do bot do Telegram."""

    token: str = ""
    chat_id: Optional[str] = None
    usar_job_queue: bool = True
    intervalo_jobs: int = 300  # 5 minutos

    def __post_init__(self):
        """Validação pós-inicialização."""
        if self.intervalo_jobs < 60:
            raise ValueError("Intervalo de jobs deve ser pelo menos 60 segundos")


@dataclass
class RunnerConfig:
    """Configurações do sistema de coleta."""

    runner_enabled: bool = True
    enabled_sources: Dict[str, bool] = field(default_factory=dict)
    intervalo_coleta: int = 10  # segundos

    def __post_init__(self):
        """Validação pós-inicialização."""
        if self.intervalo_coleta < 5:
            raise ValueError("Intervalo de coleta deve ser pelo menos 5 segundos")


@dataclass
class SystemConfig:
    """Configuração completa do sistema."""

    dashboard: DashboardSettings = field(default_factory=DashboardSettings)
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    bot: BotConfig = field(default_factory=BotConfig)
    runner: RunnerConfig = field(default_factory=RunnerConfig)
    nivel_log: LogLevel = LogLevel.INFO

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização."""
        return {
            "dashboard": {
                "tema": self.dashboard.tema.value,
                "densidade_ui": self.dashboard.densidade_ui.value,
                "janela_padrao": self.dashboard.janela_padrao,
                "pasta_logs": str(self.dashboard.pasta_logs),
                "pasta_exportacao": str(self.dashboard.pasta_exportacao),
                "limite_ofertas_tabela": self.dashboard.limite_ofertas_tabela,
                "lojas_ignoradas": self.dashboard.lojas_ignoradas,
            },
            "scraper": {
                "timeout": self.scraper.timeout,
                "retries": self.scraper.retries,
                "intervalo_requisicoes": self.scraper.intervalo_requisicoes,
                "max_concorrencia": self.scraper.max_concorrencia,
                "user_agent_rotation": self.scraper.user_agent_rotation,
                "user_agent_custom": self.scraper.user_agent_custom,
                "proxies": self.scraper.proxies,
                "salvar_html_debug": self.scraper.salvar_html_debug,
            },
            "bot": {
                "token": self.bot.token,
                "chat_id": self.bot.chat_id,
                "usar_job_queue": self.bot.usar_job_queue,
                "intervalo_jobs": self.bot.intervalo_jobs,
            },
            "runner": {
                "runner_enabled": self.runner.runner_enabled,
                "enabled_sources": self.runner.enabled_sources,
                "intervalo_coleta": self.runner.intervalo_coleta,
            },
            "nivel_log": self.nivel_log.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemConfig":
        """Cria instância a partir de dicionário."""
        try:
            return cls(
                dashboard=DashboardSettings(
                    tema=Theme(data["dashboard"]["tema"]),
                    densidade_ui=UIDensity(data["dashboard"]["densidade_ui"]),
                    janela_padrao=data["dashboard"]["janela_padrao"],
                    pasta_logs=Path(data["dashboard"]["pasta_logs"]),
                    pasta_exportacao=Path(data["dashboard"]["pasta_exportacao"]),
                    limite_ofertas_tabela=data["dashboard"]["limite_ofertas_tabela"],
                    lojas_ignoradas=data["dashboard"]["lojas_ignoradas"],
                ),
                scraper=ScraperConfig(
                    timeout=data["scraper"]["timeout"],
                    retries=data["scraper"]["retries"],
                    intervalo_requisicoes=data["scraper"]["intervalo_requisicoes"],
                    max_concorrencia=data["scraper"]["max_concorrencia"],
                    user_agent_rotation=data["scraper"]["user_agent_rotation"],
                    user_agent_custom=data["scraper"]["user_agent_custom"],
                    proxies=data["scraper"]["proxies"],
                    salvar_html_debug=data["scraper"]["salvar_html_debug"],
                ),
                bot=BotConfig(
                    token=data["bot"]["token"],
                    chat_id=data["bot"]["chat_id"],
                    usar_job_queue=data["bot"]["usar_job_queue"],
                    intervalo_jobs=data["bot"]["intervalo_jobs"],
                ),
                runner=RunnerConfig(
                    runner_enabled=data.get("runner", {}).get("runner_enabled", True),
                    enabled_sources=data.get("runner", {}).get("enabled_sources", {}),
                    intervalo_coleta=data.get("runner", {}).get("intervalo_coleta", 10),
                ),
                nivel_log=LogLevel(data["nivel_log"]),
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Erro ao carregar configuração: {e}")

    @classmethod
    def get_defaults(cls) -> "SystemConfig":
        """Retorna configuração padrão do sistema."""
        return cls()
