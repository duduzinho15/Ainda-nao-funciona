"""
Motor de coleta assíncrono para o dashboard.
Roda em segundo plano, atualiza métricas e escreve logs.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from .data_service import DataService
from .metrics import MetricsCollector


@dataclass
class ScrapingStatus:
    """Status atual do motor de coleta."""
    running: bool = False
    last_run: Optional[str] = None
    total_ofertas: int = 0
    total_postadas: int = 0
    ultimas_ofertas: List[Dict] = None
    inicio_execucao: Optional[datetime] = None
    periodo_atual: str = "24h"
    erro_ultimo: Optional[str] = None
    cache_timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.ultimas_ofertas is None:
            self.ultimas_ofertas = []


class ScrapeRunner:
    """Motor de coleta que roda em segundo plano."""
    
    def __init__(self, data_service: DataService, metrics: MetricsCollector):
        self.data_service = data_service
        self.metrics = metrics
        self.status = ScrapingStatus()
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._interval = 10.0  # segundos entre execuções
        
        # Cache global de ofertas e métricas
        self._ofertas_cache: List[Any] = []
        self._metrics_cache: Dict[str, Any] = {}
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura logging para o motor de coleta."""
        log_file = Path("./.data/logs/app.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    async def start_scraping(self, periodo: str, interval_s: float = 10.0) -> None:
        """
        Inicia o motor de coleta.
        
        Args:
            periodo: Período para coleta (24h, 7d, 30d, all)
            interval_s: Intervalo entre execuções em segundos
        """
        if self.status.running:
            self.logger.warning("Motor já está rodando")
            return
        
        self.logger.info(f"Iniciando motor de coleta para período: {periodo} (intervalo: {interval_s}s)")
        self.status.running = True
        self.status.periodo_atual = periodo
        self.status.inicio_execucao = datetime.now()
        self.status.erro_ultimo = None
        self._interval = interval_s
        
        # Criar task assíncrona
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_scraping_loop())
        
        # Log inicial
        self.logger.info(f"✅ Motor de coleta iniciado - Período: {periodo}, Intervalo: {interval_s}s")
    
    async def stop_scraping(self) -> None:
        """Para o motor de coleta."""
        if not self.status.running:
            self.logger.warning("Motor não está rodando")
            return
        
        self.logger.info("Parando motor de coleta")
        self.status.running = False
        self._stop_event.set()
        
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self.logger.warning("Timeout ao parar motor, cancelando task")
                self._task.cancel()
        
        self._task = None
        self.logger.info("🔴 Motor de coleta parado")
    
    def is_running(self) -> bool:
        """Verifica se o motor está rodando."""
        return self.status.running
    
    def status(self) -> Dict[str, Any]:
        """
        Retorna o status atual do motor.
        
        Returns:
            Dicionário com status: {running: bool, last_run: str|None, 
                                   total_ofertas: int, total_postadas: int}
        """
        return {
            'running': self.status.running,
            'last_run': self.status.last_run,
            'total_ofertas': self.status.total_ofertas,
            'total_postadas': self.status.total_postadas,
            'periodo_atual': self.status.periodo_atual,
            'erro_ultimo': self.status.erro_ultimo,
            'cache_timestamp': self.status.cache_timestamp.isoformat() if self.status.cache_timestamp else None
        }
    
    def get_cached_ofertas(self) -> List[Any]:
        """Retorna as ofertas em cache."""
        return self._ofertas_cache.copy()
    
    def get_cached_metrics(self) -> Dict[str, Any]:
        """Retorna as métricas em cache."""
        return self._metrics_cache.copy()
    
    async def _run_scraping_loop(self):
        """Loop principal do motor de coleta."""
        try:
            self.logger.info(f"🔄 Loop de coleta iniciado - Intervalo: {self._interval}s")
            
            while not self._stop_event.is_set():
                await self._execute_scraping_cycle()
                await asyncio.sleep(self._interval)
                
        except asyncio.CancelledError:
            self.logger.info("Motor de coleta cancelado")
        except Exception as e:
            self.logger.error(f"Erro no motor de coleta: {e}")
            self.status.erro_ultimo = str(e)
        finally:
            self.status.running = False
            self.logger.info("Motor de coleta parado")
    
    async def _execute_scraping_cycle(self):
        """Executa um ciclo de coleta."""
        try:
            self.logger.info(f"Executando ciclo de coleta para período: {self.status.periodo_atual}")
            
            # Carregar ofertas do período
            ofertas = await self.data_service.load_ofertas(self.status.periodo_atual)
            
            if ofertas:
                # Atualizar cache global
                self._ofertas_cache = ofertas
                self.status.total_ofertas = len(ofertas)
                self.status.total_postadas = len(ofertas)  # Para simplificar, consideramos todas como postadas
                self.status.ultimas_ofertas = ofertas[-5:]  # Últimas 5 ofertas
                self.status.last_run = datetime.now().isoformat()
                self.status.cache_timestamp = datetime.now()
                
                # Atualizar métricas do dashboard
                await self._update_dashboard_metrics(ofertas)
                
                self.logger.info(f"✅ Ciclo concluído: {len(ofertas)} ofertas carregadas e cache atualizado")
            else:
                self.logger.warning("⚠️ Nenhuma oferta carregada neste ciclo")
                
        except Exception as e:
            self.logger.error(f"❌ Erro no ciclo de coleta: {e}")
            self.status.erro_ultimo = str(e)
    
    async def _update_dashboard_metrics(self, ofertas: List[Any]):
        """Atualiza as métricas do dashboard."""
        try:
            # Calcular métricas básicas
            total_ofertas = len(ofertas)
            total_lojas = len(set(o.get('loja', '') for o in ofertas))
            
            # Calcular preço médio
            precos = []
            for oferta in ofertas:
                preco_str = oferta.get('preco', '0')
                try:
                    # Remover "R$ " e converter para float
                    preco_limpo = preco_str.replace('R$ ', '').replace(',', '.')
                    preco_float = float(preco_limpo)
                    precos.append(preco_float)
                except (ValueError, AttributeError):
                    continue
            
            preco_medio = sum(precos) / len(precos) if precos else 0
            
            # Atualizar métricas
            self.metrics.update_metrics({
                'total_ofertas': total_ofertas,
                'total_lojas': total_lojas,
                'preco_medio': preco_medio,
                'periodo': self.status.periodo_atual
            })
            
            # Atualizar cache de métricas
            self._metrics_cache = {
                'total_ofertas': total_ofertas,
                'total_lojas': total_lojas,
                'preco_medio': preco_medio,
                'periodo': self.status.periodo_atual,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar métricas: {e}")
    
    def set_interval(self, seconds: float):
        """Define o intervalo entre execuções (em segundos)."""
        if seconds < 1.0:
            raise ValueError("Intervalo deve ser >= 1.0 segundo")
        self._interval = seconds
        self.logger.info(f"Intervalo de coleta alterado para {seconds} segundos")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna resumo das métricas para o dashboard."""
        return {
            'is_running': self.status.running,
            'total_postadas': self.status.total_postadas,
            'ultima_execucao': self.status.last_run,
            'periodo_atual': self.status.periodo_atual,
            'erro_ultimo': self.status.erro_ultimo,
            'cache_timestamp': self.status.cache_timestamp.isoformat() if self.status.cache_timestamp else None,
            'intervalo_atual': self._interval
        }
    
    def force_refresh(self):
        """Força uma atualização imediata do cache."""
        if self.status.running:
            self.logger.info("Forçando atualização imediata do cache")
            # Criar task para atualização imediata
            asyncio.create_task(self._execute_scraping_cycle())
        else:
            self.logger.warning("Motor não está rodando, não é possível forçar atualização")
