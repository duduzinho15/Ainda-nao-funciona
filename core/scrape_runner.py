"""
Motor de coleta assíncrono para o sistema Garimpeiro Geek.
Executa loop de coleta de ofertas sem travar a UI.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

from .data_service import DataService
from .metrics import MetricsAggregator


@dataclass
class ScrapingStatus:
    """Status atual do motor de coleta."""
    running: bool = False
    last_run: Optional[str] = None
    total_ofertas: int = 0
    total_postadas: int = 0
    last_error: Optional[str] = None
    uptime_seconds: float = 0.0


class ScrapeRunner:
    """
    Motor de coleta assíncrono que executa em background.
    
    API:
    - start_scraping(periodo, interval_s) -> None
    - stop_scraping() -> None  
    - is_running() -> bool
    - status() -> dict
    """
    
    def __init__(self, data_service: DataService, metrics_collector: MetricsAggregator):
        self.data_service = data_service
        self.metrics_collector = metrics_collector
        self.status = ScrapingStatus()
        self._task: Optional[asyncio.Task] = None
        self._interval_s = 10.0
        self._start_time: Optional[datetime] = None
        self._system_enabled: bool = True  # NOVO: Toggle geral do sistema
        
        # Cache global de ofertas e métricas
        self._cached_ofertas: List[Any] = []
        self._cached_metrics: Optional[Any] = None
        
        # Configurar logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("✅ Motor de coleta inicializado")
    
    def _setup_logging(self):
        """Configura logging para arquivo específico."""
        try:
            # Criar diretório de logs se não existir
            log_dir = Path("./.data/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Configurar logger específico para o motor
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.INFO)
            
            # Handler para arquivo
            file_handler = logging.FileHandler(log_dir / "app.log", encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # Formato do log
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Adicionar handler se não existir
            if not logger.handlers:
                logger.addHandler(file_handler)
                
        except Exception as e:
            print(f"⚠️ Erro ao configurar logging: {e}")
    
    async def start_scraping(self, periodo: str, interval_s: float = 10.0) -> None:
        """
        Inicia o motor de coleta.
        
        Args:
            periodo: Período para coleta (24h, 7d, 30d, all)
            interval_s: Intervalo entre coletas em segundos
        """
        if self.status.running:
            self.logger.warning("⚠️ Motor já está rodando")
            return
        
        self.logger.info(f"🟢 Iniciando motor de coleta para período: {periodo}")
        
        # Atualizar status
        self.status.running = True
        self.status.last_error = None
        self._start_time = datetime.now(timezone.utc)
        self._interval_s = interval_s
        
        # Iniciar tarefa assíncrona
        self._task = asyncio.create_task(self._run_scraping_loop(periodo))
        
        self.logger.info(f"✅ Motor iniciado com intervalo de {interval_s}s")
    
    async def stop_scraping(self) -> None:
        """Para o motor de coleta."""
        if not self.status.running:
            self.logger.warning("⚠️ Motor não está rodando")
            return
        
        self.logger.info("🔴 Parando motor de coleta...")
        
        # Cancelar tarefa se existir
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Atualizar status
        self.status.running = False
        if self._start_time:
            uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()
            self.status.uptime_seconds = uptime
        
        self.logger.info("✅ Motor parado")
    
    def is_running(self) -> bool:
        """Verifica se o motor está rodando."""
        return self.status.running
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna status atual do motor.
        
        Returns:
            Dicionário com status: {running, last_run, total_ofertas, total_postadas}
        """
        return {
            'running': self.status.running,
            'last_run': self.status.last_run,
            'total_ofertas': self.status.total_ofertas,
            'total_postadas': self.status.total_postadas,
            'last_error': self.status.last_error,
            'uptime_seconds': self.status.uptime_seconds
        }
    
    def get_cached_ofertas(self) -> List[Any]:
        """Retorna ofertas atualmente em cache."""
        return self._cached_ofertas.copy()
    
    def get_cached_metrics(self) -> Optional[Any]:
        """Retorna métricas atualmente em cache."""
        return self._cached_metrics
    
    async def _run_scraping_loop(self, periodo: str):
        """Loop principal de coleta."""
        self.logger.info(f"🔄 Iniciando loop de coleta para período: {periodo}")
        
        try:
            while self.status.running:
                # Executar ciclo de coleta
                await self._execute_scraping_cycle(periodo)
                
                # Aguardar próximo ciclo
                await asyncio.sleep(self._interval_s)
                
        except asyncio.CancelledError:
            self.logger.info("🔄 Loop de coleta cancelado")
        except Exception as e:
            error_msg = f"❌ Erro no loop de coleta: {e}"
            self.logger.error(error_msg)
            self.status.last_error = error_msg
            self.status.running = False
    
    async def _execute_scraping_cycle(self, periodo: str):
        """Executa um ciclo de coleta."""
        try:
            self.logger.info(f"📡 Executando ciclo de coleta para período: {periodo}")
            
            # Verificar se o sistema está habilitado
            if not self._system_enabled:
                self.logger.warning("⚠️ Coleta desabilitada pelo sistema. Pulando ciclo.")
                return

            # Carregar ofertas via DataService
            ofertas = await self.data_service.load_ofertas(periodo, use_registry=True)
            
            if ofertas:
                # Atualizar cache
                self._cached_ofertas = ofertas
                self.status.total_ofertas = len(ofertas)
                
                # Atualizar métricas
                await self._update_dashboard_metrics(ofertas, periodo)
                
                # Atualizar timestamp da última execução
                self.status.last_run = datetime.now(timezone.utc).isoformat()
                
                self.logger.info(f"✅ Ciclo concluído: {len(ofertas)} ofertas coletadas")
            else:
                self.logger.warning("⚠️ Nenhuma oferta coletada neste ciclo")
                
        except Exception as e:
            error_msg = f"❌ Erro no ciclo de coleta: {e}"
            self.logger.error(error_msg)
            self.status.last_error = error_msg
    
    async def _update_dashboard_metrics(self, ofertas: List[Any], periodo: str):
        """Atualiza métricas do dashboard."""
        try:
            if self.metrics_collector:
                # Gerar snapshot de métricas
                metrics_snapshot = self.data_service.get_metrics_snapshot(ofertas, periodo)
                self._cached_metrics = metrics_snapshot
                
                # Atualizar métricas no coletor
                await self.metrics_collector.update_metrics(metrics_snapshot)
                
                self.logger.info("📊 Métricas do dashboard atualizadas")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao atualizar métricas: {e}")
    
    def set_interval(self, interval_s: float):
        """Define novo intervalo entre coletas."""
        if interval_s > 0:
            self._interval_s = interval_s
            self.logger.info(f"⏱️ Novo intervalo definido: {interval_s}s")
        else:
            self.logger.warning("⚠️ Intervalo deve ser maior que 0")
    
    async def force_refresh(self):
        """Força uma atualização imediata."""
        if self.status.running:
            self.logger.info("🔄 Forçando atualização imediata...")
            await self._execute_scraping_cycle("24h")  # Usar período padrão
        else:
            self.logger.warning("⚠️ Motor não está rodando, não é possível forçar atualização")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna resumo das métricas coletadas."""
        if not self._cached_metrics:
            return {
                'total_ofertas': 0,
                'lojas_ativas': 0,
                'preco_medio': None,
                'ultima_atualizacao': None
            }
        
        return {
            'total_ofertas': self._cached_metrics.total_ofertas,
            'lojas_ativas': self._cached_metrics.lojas_ativas,
            'preco_medio': self._cached_metrics.preco_medio,
            'ultima_atualizacao': self.status.last_run
        }

    def set_system_enabled(self, enabled: bool) -> None:
        """
        Define se o sistema de coleta está habilitado.
        
        Args:
            enabled: True para habilitar, False para desabilitar
        """
        self._system_enabled = enabled
        self.logger.info(f"🔧 Sistema de coleta {'habilitado' if enabled else 'desabilitado'}")
        
        # Se desabilitado e rodando, parar
        if not enabled and self.status.running:
            self.logger.info("🛑 Parando coleta devido ao sistema desabilitado")
            asyncio.create_task(self.stop_scraping())
    
    def is_system_enabled(self) -> bool:
        """Verifica se o sistema de coleta está habilitado."""
        return self._system_enabled


# ===== SISTEMA DE CONTROLE GLOBAL =====

_RUNNING = False
_MASTER_ENABLED = True
_INTERVAL_SEC = 10
_TASK: Optional[asyncio.Task] = None
_STORAGE: Optional[Any] = None

def init_runner(storage) -> None:
    """Inicializa o runner com storage."""
    global _STORAGE, _MASTER_ENABLED
    _STORAGE = storage
    _MASTER_ENABLED = storage.get_runner_enabled()
    
    # Carregar overrides de fontes
    from . import scraper_registry as reg
    reg.init_overrides_from_storage(storage)
    
    print(f"✅ Runner inicializado: master_enabled={_MASTER_ENABLED}")

def get_master_enabled() -> bool:
    """Obtém se o runner mestre está habilitado."""
    return _MASTER_ENABLED

def set_master_enabled(val: bool) -> None:
    """Define se o runner mestre está habilitado."""
    global _MASTER_ENABLED, _STORAGE
    _MASTER_ENABLED = bool(val)
    if _STORAGE:
        _STORAGE.set_runner_enabled(_MASTER_ENABLED)
    if not _MASTER_ENABLED:
        stop_scraping()
    print(f"🔧 Runner mestre {'habilitado' if _MASTER_ENABLED else 'desabilitado'}")

def is_running() -> bool:
    """Verifica se o runner está rodando."""
    return _RUNNING

def status() -> str:
    """Retorna status do runner."""
    return "running" if _RUNNING else "stopped"

async def _loop():
    """Loop principal do runner."""
    global _RUNNING
    try:
        while _RUNNING:
            # Respeita toggle mestre
            if not _MASTER_ENABLED:
                await asyncio.sleep(_INTERVAL_SEC)
                continue

            # Pega fontes habilitadas EFETIVAMENTE a cada ciclo
            from . import scraper_registry as reg
            sources = reg.get_sources_for_run()

            if sources:
                print(f"🔄 Executando ciclo com {len(sources)} fontes habilitadas")
                # Aqui você pode implementar a lógica de coleta real
                # Por enquanto, apenas simular
                await asyncio.sleep(2)  # Simular trabalho
            else:
                print("⚠️ Nenhuma fonte habilitada para execução")

            await asyncio.sleep(_INTERVAL_SEC)
    finally:
        _RUNNING = False

def start_scraping(loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
    """Inicia o runner."""
    global _RUNNING, _TASK
    if _RUNNING:
        return
    _RUNNING = True
    ev = loop or asyncio.get_event_loop()
    _TASK = ev.create_task(_loop())
    print("🟢 Runner iniciado")

def stop_scraping() -> None:
    """Para o runner."""
    global _RUNNING, _TASK
    _RUNNING = False
    if _TASK and not _TASK.done():
        _TASK.cancel()
    _TASK = None
    print("🔴 Runner parado")
