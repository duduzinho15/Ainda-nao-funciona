"""
Motor de coleta assíncrono para o dashboard.
Roda em segundo plano, atualiza métricas e escreve logs.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

from .data_service import DataService
from .metrics import MetricsCollector


@dataclass
class ScrapingStatus:
    """Status atual do motor de coleta."""
    is_running: bool = False
    total_postadas: int = 0
    ultimas_ofertas: List[Dict] = None
    ultima_execucao: Optional[datetime] = None
    inicio_execucao: Optional[datetime] = None
    periodo_atual: str = "24h"
    erro_ultimo: Optional[str] = None

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
        self._interval = 10  # segundos entre execuções
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura logging para o motor de coleta."""
        log_file = "./.data/logs/app.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
    
    async def start_scraping(self, periodo: str = "24h") -> bool:
        """Inicia o motor de coleta."""
        if self.status.is_running:
            self.logger.warning("Motor já está rodando")
            return False
        
        self.logger.info(f"Iniciando motor de coleta para período: {periodo}")
        self.status.is_running = True
        self.status.periodo_atual = periodo
        self.status.inicio_execucao = datetime.now()
        self.status.erro_ultimo = None
        
        # Criar task assíncrona
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_scraping_loop())
        
        return True
    
    async def stop_scraping(self) -> bool:
        """Para o motor de coleta."""
        if not self.status.is_running:
            self.logger.warning("Motor não está rodando")
            return False
        
        self.logger.info("Parando motor de coleta")
        self.status.is_running = False
        self._stop_event.set()
        
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self.logger.warning("Timeout ao parar motor, cancelando task")
                self._task.cancel()
        
        self._task = None
        return True
    
    def is_running(self) -> bool:
        """Verifica se o motor está rodando."""
        return self.status.is_running
    
    def get_status(self) -> ScrapingStatus:
        """Retorna o status atual do motor."""
        return self.status
    
    async def _run_scraping_loop(self):
        """Loop principal do motor de coleta."""
        try:
            while not self._stop_event.is_set():
                await self._execute_scraping_cycle()
                await asyncio.sleep(self._interval)
        except asyncio.CancelledError:
            self.logger.info("Motor de coleta cancelado")
        except Exception as e:
            self.logger.error(f"Erro no motor de coleta: {e}")
            self.status.erro_ultimo = str(e)
        finally:
            self.status.is_running = False
            self.logger.info("Motor de coleta parado")
    
    async def _execute_scraping_cycle(self):
        """Executa um ciclo de coleta."""
        try:
            self.logger.info(f"Executando ciclo de coleta para período: {self.status.periodo_atual}")
            
            # Carregar ofertas do período
            ofertas = await self.data_service.load_ofertas(self.status.periodo_atual)
            
            if ofertas:
                # Atualizar métricas
                self.status.total_postadas = len(ofertas)
                self.status.ultimas_ofertas = ofertas[-5:]  # Últimas 5 ofertas
                self.status.ultima_execucao = datetime.now()
                
                # Atualizar métricas do dashboard
                await self._update_dashboard_metrics(ofertas)
                
                self.logger.info(f"Ciclo concluído: {len(ofertas)} ofertas carregadas")
            else:
                self.logger.warning("Nenhuma oferta carregada neste ciclo")
                
        except Exception as e:
            self.logger.error(f"Erro no ciclo de coleta: {e}")
            self.status.erro_ultimo = str(e)
    
    async def _update_dashboard_metrics(self, ofertas: List[Dict]):
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
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar métricas: {e}")
    
    def set_interval(self, seconds: int):
        """Define o intervalo entre execuções (em segundos)."""
        if seconds < 1:
            raise ValueError("Intervalo deve ser >= 1 segundo")
        self._interval = seconds
        self.logger.info(f"Intervalo de coleta alterado para {seconds} segundos")
    
    def get_metrics_summary(self) -> Dict:
        """Retorna resumo das métricas para o dashboard."""
        return {
            'is_running': self.status.is_running,
            'total_postadas': self.status.total_postadas,
            'ultima_execucao': self.status.ultima_execucao.isoformat() if self.status.ultima_execucao else None,
            'periodo_atual': self.status.periodo_atual,
            'erro_ultimo': self.status.erro_ultimo,
            'tempo_execucao': None  # TODO: implementar
        }
