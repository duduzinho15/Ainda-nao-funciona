"""
Sistema de Métricas de Performance em Tempo Real para o Bot Garimpeiro Geek

Este módulo implementa um sistema de métricas avançado com:
- Coleta de métricas em tempo real
- Histórico de performance
- Alertas de performance
- Dashboard de métricas
- Integração com sistemas de monitoramento
- Análise de tendências
"""

import time
import asyncio
import threading
import json
import sqlite3
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import statistics
from collections import defaultdict, deque
import psutil

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Tipos de métricas suportadas."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class MetricUnit(Enum):
    """Unidades de medida para métricas."""
    COUNT = "count"
    PERCENT = "percent"
    MILLISECONDS = "ms"
    SECONDS = "s"
    BYTES = "bytes"
    REQUESTS_PER_SECOND = "req/s"
    SUCCESS_RATE = "success_rate"

@dataclass
class MetricPoint:
    """Ponto individual de uma métrica."""
    name: str
    value: Union[int, float]
    timestamp: datetime
    tags: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class MetricSummary:
    """Resumo estatístico de uma métrica."""
    name: str
    metric_type: MetricType
    unit: MetricUnit
    count: int
    min_value: float
    max_value: float
    mean_value: float
    median_value: float
    p95_value: float
    p99_value: float
    last_value: float
    last_update: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização."""
        data = asdict(self)
        data['last_update'] = self.last_update.isoformat()
        data['metric_type'] = self.metric_type.value
        data['unit'] = self.unit.value
        return data

class MetricCollector:
    """Coletor de métricas individual."""
    
    def __init__(self, name: str, metric_type: MetricType, unit: MetricUnit,
                 retention_hours: int = 24, max_points: int = 1000):
        self.name = name
        self.metric_type = metric_type
        self.unit = unit
        self.retention_hours = retention_hours
        self.max_points = max_points
        
        # Armazena pontos de métrica
        self.points: deque = deque(maxlen=max_points)
        self.lock = threading.RLock()
        
        # Estatísticas em tempo real
        self._stats_cache = None
        self._last_stats_update = None
        self._stats_cache_ttl = 60  # Cache por 1 minuto
    
    def record(self, value: Union[int, float], tags: Optional[Dict[str, str]] = None,
               metadata: Optional[Dict[str, Any]] = None):
        """Registra um novo ponto de métrica."""
        with self.lock:
            # Remove pontos antigos
            self._cleanup_old_points()
            
            # Adiciona novo ponto
            point = MetricPoint(
                name=self.name,
                value=value,
                timestamp=datetime.now(),
                tags=tags,
                metadata=metadata
            )
            
            self.points.append(point)
            
            # Invalida cache de estatísticas
            self._stats_cache = None
    
    def _cleanup_old_points(self):
        """Remove pontos antigos baseado na retenção."""
        if not self.points:
            return
        
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        # Remove pontos antigos
        while self.points and self.points[0].timestamp < cutoff_time:
            self.points.popleft()
    
    def get_summary(self) -> MetricSummary:
        """Obtém resumo estatístico da métrica."""
        with self.lock:
            # Verifica cache
            if (self._stats_cache and self._last_stats_update and 
                (datetime.now() - self._last_stats_update).total_seconds() < self._stats_cache_ttl):
                return self._stats_cache
            
            if not self.points:
                # Retorna métrica vazia
                empty_summary = MetricSummary(
                    name=self.name,
                    metric_type=self.metric_type,
                    unit=self.unit,
                    count=0,
                    min_value=0.0,
                    max_value=0.0,
                    mean_value=0.0,
                    median_value=0.0,
                    p95_value=0.0,
                    p99_value=0.0,
                    last_value=0.0,
                    last_update=datetime.now()
                )
                return empty_summary
            
            # Calcula estatísticas
            values = [point.value for point in self.points]
            values.sort()
            
            count = len(values)
            min_value = float(values[0])
            max_value = float(values[-1])
            mean_value = statistics.mean(values)
            median_value = statistics.median(values)
            
            # Calcula percentis
            p95_index = int(count * 0.95)
            p99_index = int(count * 0.99)
            p95_value = float(values[p95_index]) if p95_index < count else max_value
            p99_value = float(values[p99_index]) if p99_index < count else max_value
            
            last_value = float(self.points[-1].value)
            last_update = self.points[-1].timestamp
            
            summary = MetricSummary(
                name=self.name,
                metric_type=self.metric_type,
                unit=self.unit,
                count=count,
                min_value=min_value,
                max_value=max_value,
                mean_value=mean_value,
                median_value=median_value,
                p95_value=p95_value,
                p99_value=p99_value,
                last_value=last_value,
                last_update=last_update
            )
            
            # Atualiza cache
            self._stats_cache = summary
            self._last_stats_update = datetime.now()
            
            return summary
    
    def get_recent_points(self, hours: int = 1) -> List[MetricPoint]:
        """Obtém pontos recentes da métrica."""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_points = [
                point for point in self.points
                if point.timestamp >= cutoff_time
            ]
            return recent_points
    
    def get_value_at(self, timestamp: datetime) -> Optional[float]:
        """Obtém valor da métrica em um timestamp específico."""
        with self.lock:
            # Encontra o ponto mais próximo do timestamp
            if not self.points:
                return None
            
            closest_point = min(self.points, key=lambda p: abs((p.timestamp - timestamp).total_seconds()))
            
            # Verifica se está dentro de uma janela de tolerância (5 minutos)
            if abs((closest_point.timestamp - timestamp).total_seconds()) <= 300:
                return closest_point.value
            
            return None

class PerformanceMetrics:
    """
    Sistema principal de métricas de performance.
    """
    
    def __init__(self, db_path: str = "performance_metrics.db"):
        self.db_path = db_path
        self.collectors: Dict[str, MetricCollector] = {}
        self.running = False
        self.metrics_thread = None
        
        # Callbacks para alertas
        self.threshold_callbacks: List[Callable] = []
        self.anomaly_callbacks: List[Callable] = []
        
        # Configurações
        self.collection_interval = 10  # Coleta métricas a cada 10 segundos
        self.anomaly_detection_enabled = True
        self.anomaly_threshold = 2.0  # Desvio padrão para detecção de anomalias
        
        # Inicializa banco de dados
        self._init_database()
        
        # Adiciona métricas padrão do sistema
        self._add_system_metrics()
    
    def _init_database(self):
        """Inicializa banco de dados para métricas."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS metric_points (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_type TEXT NOT NULL,
                        unit TEXT NOT NULL,
                        value REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        tags TEXT,
                        metadata TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS metric_summaries (
                        metric_name TEXT PRIMARY KEY,
                        metric_type TEXT NOT NULL,
                        unit TEXT NOT NULL,
                        count INTEGER DEFAULT 0,
                        min_value REAL DEFAULT 0,
                        max_value REAL DEFAULT 0,
                        mean_value REAL DEFAULT 0,
                        median_value REAL DEFAULT 0,
                        p95_value REAL DEFAULT 0,
                        p99_value REAL DEFAULT 0,
                        last_value REAL DEFAULT 0,
                        last_update TEXT
                    )
                """)
                
                # Índices para performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_metric_timestamp ON metric_points(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_metric_name ON metric_points(metric_name)")
                
                conn.commit()
                logger.info("Banco de dados de métricas inicializado")
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
    
    def _add_system_metrics(self):
        """Adiciona métricas padrão do sistema."""
        # Métricas de sistema
        self.add_metric("system.cpu_usage", MetricType.GAUGE, MetricUnit.PERCENT)
        self.add_metric("system.memory_usage", MetricType.GAUGE, MetricUnit.PERCENT)
        self.add_metric("system.disk_usage", MetricType.GAUGE, MetricUnit.PERCENT)
        self.add_metric("system.network_io", MetricType.GAUGE, MetricUnit.BYTES)
        
        # Métricas de aplicação
        self.add_metric("app.requests_total", MetricType.COUNTER, MetricUnit.COUNT)
        self.add_metric("app.requests_success", MetricType.COUNTER, MetricUnit.COUNT)
        self.add_metric("app.requests_failed", MetricType.COUNTER, MetricUnit.COUNT)
        self.add_metric("app.response_time", MetricType.HISTOGRAM, MetricUnit.MILLISECONDS)
        self.add_metric("app.success_rate", MetricType.GAUGE, MetricUnit.SUCCESS_RATE)
    
    def add_metric(self, name: str, metric_type: MetricType, unit: MetricUnit,
                   retention_hours: int = 24, max_points: int = 1000) -> MetricCollector:
        """Adiciona uma nova métrica."""
        collector = MetricCollector(name, metric_type, unit, retention_hours, max_points)
        self.collectors[name] = collector
        logger.info(f"Métrica adicionada: {name} ({metric_type.value}, {unit.value})")
        return collector
    
    def record_metric(self, name: str, value: Union[int, float], 
                     tags: Optional[Dict[str, str]] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """Registra valor para uma métrica."""
        if name not in self.collectors:
            logger.warning(f"Métrica não encontrada: {name}")
            return
        
        self.collectors[name].record(value, tags, metadata)
    
    def get_metric_summary(self, name: str) -> Optional[MetricSummary]:
        """Obtém resumo de uma métrica específica."""
        if name in self.collectors:
            return self.collectors[name].get_summary()
        return None
    
    def get_all_metrics_summary(self) -> List[MetricSummary]:
        """Obtém resumo de todas as métricas."""
        summaries = []
        for collector in self.collectors.values():
            summaries.append(collector.get_summary())
        return summaries
    
    def start_metrics_collection(self):
        """Inicia coleta automática de métricas."""
        if self.running:
            logger.warning("Coleta de métricas já está rodando")
            return
        
        self.running = True
        self.metrics_thread = threading.Thread(target=self._metrics_worker, daemon=True)
        self.metrics_thread.start()
        logger.info("Coleta de métricas iniciada")
    
    def stop_metrics_collection(self):
        """Para a coleta de métricas."""
        self.running = False
        if self.metrics_thread:
            self.metrics_thread.join(timeout=5)
        logger.info("Coleta de métricas parada")
    
    def _metrics_worker(self):
        """Worker thread para coleta de métricas."""
        while self.running:
            try:
                # Coleta métricas do sistema
                self._collect_system_metrics()
                
                # Coleta métricas de aplicação
                self._collect_app_metrics()
                
                # Verifica anomalias
                if self.anomaly_detection_enabled:
                    self._detect_anomalies()
                
                # Persiste métricas no banco
                self._persist_metrics()
                
                # Aguarda próximo ciclo
                time.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Erro na coleta de métricas: {e}")
                time.sleep(5)
    
    def _collect_system_metrics(self):
        """Coleta métricas do sistema."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric("system.cpu_usage", cpu_percent)
            
            # Memória
            memory = psutil.virtual_memory()
            self.record_metric("system.memory_usage", memory.percent)
            
            # Disco
            disk = psutil.disk_usage('/')
            self.record_metric("system.disk_usage", disk.percent)
            
            # Rede
            net_io = psutil.net_io_counters()
            total_io = net_io.bytes_sent + net_io.bytes_recv
            self.record_metric("system.network_io", total_io)
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas do sistema: {e}")
    
    def _collect_app_metrics(self):
        """Coleta métricas da aplicação."""
        try:
            # Métricas de cache
            if 'cache_system' in globals():
                cache_stats = cache.get_stats()
                self.record_metric("app.cache_hit_rate", cache_stats.get('hit_rate', 0))
                self.record_metric("app.cache_usage", cache_stats.get('usage_percentage', 0))
            
            # Métricas de rate limiting
            if 'rate_limiter' in globals():
                rate_limiter_stats = rate_limiter.get_stats()
                self.record_metric("app.rate_limit_block_rate", rate_limiter_stats.get('block_rate_percent', 0))
                self.record_metric("app.rate_limit_success_rate", rate_limiter_stats.get('success_rate_percent', 0))
            
            # Métricas de saúde
            if 'health_monitor' in globals():
                health_summary = health_monitor.get_health_summary()
                healthy_services = health_summary.get('healthy_services', 0)
                total_services = health_summary.get('services_count', 0)
                if total_services > 0:
                    health_percentage = (healthy_services / total_services) * 100
                    self.record_metric("app.system_health", health_percentage)
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas da aplicação: {e}")
    
    def _detect_anomalies(self):
        """Detecta anomalias nas métricas."""
        try:
            for name, collector in self.collectors.items():
                summary = collector.get_summary()
                
                if summary.count < 10:  # Precisa de pelo menos 10 pontos
                    continue
                
                # Calcula desvio padrão dos valores recentes
                recent_points = collector.get_recent_points(hours=1)
                if len(recent_points) < 5:
                    continue
                
                values = [point.value for point in recent_points]
                mean = statistics.mean(values)
                std_dev = statistics.stdev(values) if len(values) > 1 else 0
                
                if std_dev == 0:
                    continue
                
                # Verifica se o último valor é uma anomalia
                last_value = values[-1]
                z_score = abs((last_value - mean) / std_dev)
                
                if z_score > self.anomaly_threshold:
                    logger.warning(f"Anomalia detectada na métrica {name}: z-score={z_score:.2f}")
                    
                    # Executa callbacks de anomalia
                    for callback in self.anomaly_callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                asyncio.create_task(callback(name, last_value, mean, std_dev, z_score))
                            else:
                                callback(name, last_value, mean, std_dev, z_score)
                        except Exception as e:
                            logger.error(f"Erro no callback de anomalia: {e}")
        
        except Exception as e:
            logger.error(f"Erro na detecção de anomalias: {e}")
    
    def _persist_metrics(self):
        """Persiste métricas no banco de dados."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for name, collector in self.collectors.items():
                    summary = collector.get_summary()
                    
                    # Insere ou atualiza resumo
                    conn.execute("""
                        INSERT OR REPLACE INTO metric_summaries 
                        (metric_name, metric_type, unit, count, min_value, max_value, 
                         mean_value, median_value, p95_value, p99_value, last_value, last_update)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        summary.name,
                        summary.metric_type.value,
                        summary.unit.value,
                        summary.count,
                        summary.min_value,
                        summary.max_value,
                        summary.mean_value,
                        summary.median_value,
                        summary.p95_value,
                        summary.p99_value,
                        summary.last_value,
                        summary.last_update.isoformat()
                    ))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao persistir métricas: {e}")
    
    def add_threshold_callback(self, callback: Callable):
        """Adiciona callback para alertas de threshold."""
        self.threshold_callbacks.append(callback)
    
    def add_anomaly_callback(self, callback: Callable):
        """Adiciona callback para detecção de anomalias."""
        self.anomaly_callbacks.append(callback)
    
    def get_metrics_dashboard(self) -> Dict[str, Any]:
        """Obtém dados para dashboard de métricas."""
        try:
            # Resumo geral
            all_summaries = self.get_all_metrics_summary()
            
            # Agrupa por categoria
            system_metrics = [s for s in all_summaries if s.name.startswith('system.')]
            app_metrics = [s for s in all_summaries if s.name.startswith('app.')]
            scraper_metrics = [s for s in all_summaries if s.name.startswith('scraper.')]
            
            # Calcula estatísticas gerais
            total_metrics = len(all_summaries)
            active_metrics = sum(1 for s in all_summaries if s.count > 0)
            
            # Métricas críticas
            critical_metrics = []
            for summary in all_summaries:
                if summary.name in ['system.cpu_usage', 'system.memory_usage', 'system.disk_usage']:
                    if summary.last_value > 80:  # Acima de 80%
                        critical_metrics.append({
                            'name': summary.name,
                            'value': summary.last_value,
                            'unit': summary.unit.value,
                            'threshold': 80
                        })
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_metrics': total_metrics,
                'active_metrics': active_metrics,
                'system_metrics': [s.to_dict() for s in system_metrics],
                'app_metrics': [s.to_dict() for s in app_metrics],
                'scraper_metrics': [s.to_dict() for s in scraper_metrics],
                'critical_metrics': critical_metrics,
                'overall_status': 'warning' if critical_metrics else 'healthy'
            }
        except Exception as e:
            logger.error(f"Erro ao gerar dashboard: {e}")
            return {'error': str(e)}
    
    def get_metric_history(self, name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Obtém histórico de uma métrica específica."""
        if name not in self.collectors:
            return []
        
        try:
            points = self.collectors[name].get_recent_points(hours)
            return [point.to_dict() for point in points]
        except Exception as e:
            logger.error(f"Erro ao obter histórico da métrica {name}: {e}")
            return []

# Instância global do sistema de métricas
performance_metrics = PerformanceMetrics()

# Funções de conveniência
def start_metrics_collection():
    """Inicia coleta de métricas."""
    performance_metrics.start_metrics_collection()

def stop_metrics_collection():
    """Para coleta de métricas."""
    performance_metrics.stop_metrics_collection()

def add_metric(name: str, metric_type: MetricType, unit: MetricUnit) -> MetricCollector:
    """Adiciona uma nova métrica."""
    return performance_metrics.add_metric(name, metric_type, unit)

def record_metric(name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None):
    """Registra valor para uma métrica."""
    performance_metrics.record_metric(name, value, tags)

def get_metrics_dashboard() -> Dict[str, Any]:
    """Obtém dashboard de métricas."""
    return performance_metrics.get_metrics_dashboard()

def get_metric_summary(name: str) -> Optional[MetricSummary]:
    """Obtém resumo de uma métrica."""
    return performance_metrics.get_metric_summary(name)

# Decorator para métricas automáticas
def track_performance(metric_name: str, metric_type: MetricType = MetricType.TIMER):
    """
    Decorator para rastrear performance de funções automaticamente.
    
    Args:
        metric_name: Nome da métrica
        metric_type: Tipo da métrica (padrão: timer)
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                # Registra sucesso
                duration = (time.time() - start_time) * 1000
                record_metric(f"{metric_name}.duration", duration)
                record_metric(f"{metric_name}.success", 1)
                return result
            except Exception as e:
                # Registra falha
                duration = (time.time() - start_time) * 1000
                record_metric(f"{metric_name}.duration", duration)
                record_metric(f"{metric_name}.failed", 1)
                raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                # Registra sucesso
                duration = (time.time() - start_time) * 1000
                record_metric(f"{metric_name}.duration", duration)
                record_metric(f"{metric_name}.success", 1)
                return result
            except Exception as e:
                # Registra falha
                duration = (time.time() - start_time) * 1000
                record_metric(f"{metric_name}.duration", duration)
                record_metric(f"{metric_name}.failed", 1)
                raise
        
        # Retorna wrapper apropriado
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

if __name__ == "__main__":
    # Teste do sistema de métricas
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testando Sistema de Métricas de Performance...")
    
    # Adiciona métricas de exemplo
    add_metric("test.counter", MetricType.COUNTER, MetricUnit.COUNT)
    add_metric("test.gauge", MetricType.GAUGE, MetricUnit.PERCENT)
    add_metric("test.timer", MetricType.TIMER, MetricUnit.MILLISECONDS)
    
    # Registra algumas métricas
    record_metric("test.counter", 1)
    record_metric("test.gauge", 75.5)
    record_metric("test.timer", 150.0)
    
    # Testa decorator
    @track_performance("test_function")
    def test_function():
        time.sleep(0.1)
        return "success"
    
    test_function()
    
    # Inicia coleta
    start_metrics_collection()
    
    # Aguarda algumas coletas
    time.sleep(30)
    
    # Mostra dashboard
    dashboard = get_metrics_dashboard()
    print(f"Dashboard: {json.dumps(dashboard, indent=2)}")
    
    # Para coleta
    stop_metrics_collection()
