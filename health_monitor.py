"""
Sistema de Monitoramento de Saúde dos Scrapers para o Bot Garimpeiro Geek

Este módulo implementa um sistema de monitoramento avançado com:
- Verificação de saúde em tempo real dos scrapers
- Métricas de performance e disponibilidade
- Detecção automática de problemas
- Sistema de alertas e notificações
- Dashboard de status em tempo real
- Histórico de métricas
"""

import time
import asyncio
import threading
import json
import sqlite3
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import psutil
import requests

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Status de saúde dos serviços."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class ServiceType(Enum):
    """Tipos de serviços monitorados."""
    SCRAPER = "scraper"
    API = "api"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"

@dataclass
class HealthCheck:
    """Resultado de uma verificação de saúde."""
    service_name: str
    service_type: ServiceType
    status: HealthStatus
    timestamp: datetime
    response_time_ms: float
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['service_type'] = self.service_type.value
        data['status'] = self.status.value
        return data

@dataclass
class ServiceMetrics:
    """Métricas agregadas de um serviço."""
    service_name: str
    service_type: ServiceType
    total_checks: int
    successful_checks: int
    failed_checks: int
    average_response_time_ms: float
    uptime_percentage: float
    last_check: datetime
    last_status: HealthStatus
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização."""
        data = asdict(self)
        data['last_check'] = self.last_check.isoformat()
        data['service_type'] = self.service_type.value
        data['status'] = self.last_status.value
        return data

class HealthChecker:
    """Verificador de saúde individual para um serviço."""
    
    def __init__(self, name: str, service_type: ServiceType, 
                 check_function: Callable, interval: int = 60,
                 timeout: int = 30, retries: int = 3):
        self.name = name
        self.service_type = service_type
        self.check_function = check_function
        self.interval = interval
        self.timeout = timeout
        self.retries = retries
        self.last_check = None
        self.last_status = HealthStatus.UNKNOWN
        self.consecutive_failures = 0
        
    async def check_health(self) -> HealthCheck:
        """Executa verificação de saúde do serviço."""
        start_time = time.time()
        error_message = None
        metadata = {}
        
        try:
            # Executa verificação com timeout
            if asyncio.iscoroutinefunction(self.check_function):
                result = await asyncio.wait_for(
                    self.check_function(), 
                    timeout=self.timeout
                )
            else:
                # Para funções síncronas, executa em thread
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, self.check_function
                )
            
            # Processa resultado
            if isinstance(result, dict):
                metadata = result
                success = result.get('success', True)
                error_message = result.get('error')
            else:
                success = bool(result)
            
            # Determina status
            if success:
                status = HealthStatus.HEALTHY
                self.consecutive_failures = 0
            else:
                if self.consecutive_failures >= 2:
                    status = HealthStatus.CRITICAL
                else:
                    status = HealthStatus.WARNING
                self.consecutive_failures += 1
                
        except asyncio.TimeoutError:
            status = HealthStatus.CRITICAL
            error_message = f"Timeout após {self.timeout}s"
            self.consecutive_failures += 1
        except Exception as e:
            status = HealthStatus.CRITICAL
            error_message = str(e)
            self.consecutive_failures += 1
        
        # Calcula tempo de resposta
        response_time_ms = (time.time() - start_time) * 1000
        
        # Atualiza estado interno
        self.last_check = datetime.now()
        self.last_status = status
        
        # Cria resultado
        health_check = HealthCheck(
            service_name=self.name,
            service_type=self.service_type,
            status=status,
            timestamp=self.last_check,
            response_time_ms=response_time_ms,
            error_message=error_message,
            metadata=metadata
        )
        
        return health_check

class HealthMonitor:
    """
    Sistema principal de monitoramento de saúde.
    """
    
    def __init__(self, db_path: str = "health_monitor.db"):
        self.db_path = db_path
        self.checkers: Dict[str, HealthChecker] = {}
        self.running = False
        self.monitor_thread = None
        
        # Callbacks para notificações
        self.status_change_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []
        
        # Configurações
        self.check_interval = 60  # Verificação principal a cada minuto
        self.alert_threshold = 3  # Alertas após 3 falhas consecutivas
        
        # Inicializa banco de dados
        self._init_database()
        
        # Adiciona verificadores padrão
        self._add_default_checkers()
    
    def _init_database(self):
        """Inicializa banco de dados para métricas."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS health_checks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_name TEXT NOT NULL,
                        service_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        response_time_ms REAL NOT NULL,
                        error_message TEXT,
                        metadata TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS service_metrics (
                        service_name TEXT PRIMARY KEY,
                        service_type TEXT NOT NULL,
                        total_checks INTEGER DEFAULT 0,
                        successful_checks INTEGER DEFAULT 0,
                        failed_checks INTEGER DEFAULT 0,
                        average_response_time_ms REAL DEFAULT 0,
                        uptime_percentage REAL DEFAULT 100,
                        last_check TEXT,
                        last_status TEXT
                    )
                """)
                
                conn.commit()
                logger.info("Banco de dados de monitoramento inicializado")
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
    
    def _add_default_checkers(self):
        """Adiciona verificadores padrão do sistema."""
        # Verificador de sistema
        self.add_checker(
            "system_resources",
            ServiceType.SYSTEM,
            self._check_system_resources,
            interval=30
        )
        
        # Verificador de conectividade de internet
        self.add_checker(
            "internet_connectivity",
            ServiceType.EXTERNAL_SERVICE,
            self._check_internet_connectivity,
            interval=60
        )
        
        # Verificador de banco de dados
        self.add_checker(
            "database_connection",
            ServiceType.DATABASE,
            self._check_database_connection,
            interval=120
        )
    
    def add_checker(self, name: str, service_type: ServiceType, 
                   check_function: Callable, interval: int = 60,
                   timeout: int = 30, retries: int = 3):
        """Adiciona um novo verificador de saúde."""
        checker = HealthChecker(name, service_type, check_function, interval, timeout, retries)
        self.checkers[name] = checker
        logger.info(f"Verificador de saúde adicionado: {name}")
    
    def add_scraper_checker(self, name: str, check_function: Callable, 
                           interval: int = 300):  # 5 minutos para scrapers
        """Adiciona verificador específico para scrapers."""
        self.add_checker(name, ServiceType.SCRAPER, check_function, interval)
    
    def add_api_checker(self, name: str, check_function: Callable, 
                       interval: int = 120):  # 2 minutos para APIs
        """Adiciona verificador específico para APIs."""
        self.add_checker(name, ServiceType.API, check_function, interval)
    
    def start_monitoring(self):
        """Inicia o monitoramento de saúde."""
        if self.running:
            logger.warning("Monitoramento já está rodando")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self.monitor_thread.start()
        logger.info("Monitoramento de saúde iniciado")
    
    def stop_monitoring(self):
        """Para o monitoramento de saúde."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Monitoramento de saúde parado")
    
    def _monitor_worker(self):
        """Worker thread para monitoramento contínuo."""
        while self.running:
            try:
                # Executa verificações
                asyncio.run(self._run_all_checks())
                
                # Aguarda próximo ciclo
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Erro no worker de monitoramento: {e}")
                time.sleep(10)  # Aguarda um pouco antes de tentar novamente
    
    async def _run_all_checks(self):
        """Executa todas as verificações de saúde."""
        tasks = []
        
        for checker in self.checkers.values():
            # Verifica se é hora de executar este checker
            if (checker.last_check is None or 
                (datetime.now() - checker.last_check).total_seconds() >= checker.interval):
                tasks.append(self._run_checker(checker))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Processa resultados
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Erro na verificação de saúde: {result}")
                elif result:
                    await self._process_health_check(result)
    
    async def _run_checker(self, checker: HealthChecker) -> Optional[HealthCheck]:
        """Executa um verificador específico."""
        try:
            return await checker.check_health()
        except Exception as e:
            logger.error(f"Erro ao executar checker {checker.name}: {e}")
            return None
    
    async def _process_health_check(self, health_check: HealthCheck):
        """Processa resultado de verificação de saúde."""
        try:
            # Salva no banco de dados
            self._save_health_check(health_check)
            
            # Atualiza métricas
            self._update_service_metrics(health_check)
            
            # Verifica mudanças de status
            await self._check_status_changes(health_check)
            
            # Verifica necessidade de alertas
            await self._check_alerts(health_check)
            
        except Exception as e:
            logger.error(f"Erro ao processar verificação de saúde: {e}")
    
    def _save_health_check(self, health_check: HealthCheck):
        """Salva verificação de saúde no banco de dados."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO health_checks 
                    (service_name, service_type, status, timestamp, response_time_ms, error_message, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    health_check.service_name,
                    health_check.service_type.value,
                    health_check.status.value,
                    health_check.timestamp.isoformat(),
                    health_check.response_time_ms,
                    health_check.error_message,
                    json.dumps(health_check.metadata) if health_check.metadata else None
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao salvar verificação de saúde: {e}")
    
    def _update_service_metrics(self, health_check: HealthCheck):
        """Atualiza métricas agregadas do serviço."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Obtém métricas atuais
                cursor = conn.execute("""
                    SELECT total_checks, successful_checks, failed_checks, average_response_time_ms
                    FROM service_metrics WHERE service_name = ?
                """, (health_check.service_name,))
                
                row = cursor.fetchone()
                if row:
                    total_checks, successful_checks, failed_checks, avg_response_time = row
                else:
                    total_checks = successful_checks = failed_checks = 0
                    avg_response_time = 0
                
                # Atualiza métricas
                total_checks += 1
                if health_check.status == HealthStatus.HEALTHY:
                    successful_checks += 1
                else:
                    failed_checks += 1
                
                # Calcula nova média de tempo de resposta
                if total_checks > 0:
                    new_avg = ((avg_response_time * (total_checks - 1)) + health_check.response_time_ms) / total_checks
                else:
                    new_avg = health_check.response_time_ms
                
                # Calcula uptime
                uptime_percentage = (successful_checks / total_checks * 100) if total_checks > 0 else 100
                
                # Insere ou atualiza métricas
                conn.execute("""
                    INSERT OR REPLACE INTO service_metrics 
                    (service_name, service_type, total_checks, successful_checks, failed_checks, 
                     average_response_time_ms, uptime_percentage, last_check, last_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    health_check.service_name,
                    health_check.service_type.value,
                    total_checks,
                    successful_checks,
                    failed_checks,
                    new_avg,
                    uptime_percentage,
                    health_check.timestamp.isoformat(),
                    health_check.status.value
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao atualizar métricas: {e}")
    
    async def _check_status_changes(self, health_check: HealthCheck):
        """Verifica mudanças de status e executa callbacks."""
        # Obtém status anterior
        previous_status = None
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT last_status FROM service_metrics WHERE service_name = ?
                """, (health_check.service_name,))
                row = cursor.fetchone()
                if row:
                    previous_status = HealthStatus(row[0])
        except Exception as e:
            logger.error(f"Erro ao obter status anterior: {e}")
        
        # Verifica se houve mudança
        if previous_status and previous_status != health_check.status:
            logger.info(f"Status do serviço {health_check.service_name} mudou de {previous_status.value} para {health_check.status.value}")
            
            # Executa callbacks de mudança de status
            for callback in self.status_change_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(health_check.service_name, previous_status, health_check.status)
                    else:
                        callback(health_check.service_name, previous_status, health_check.status)
                except Exception as e:
                    logger.error(f"Erro no callback de mudança de status: {e}")
    
    async def _check_alerts(self, health_check: HealthCheck):
        """Verifica necessidade de alertas."""
        if health_check.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
            # Executa callbacks de alerta
            for callback in self.alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(health_check)
                    else:
                        callback(health_check)
                except Exception as e:
                    logger.error(f"Erro no callback de alerta: {e}")
    
    def add_status_change_callback(self, callback: Callable):
        """Adiciona callback para mudanças de status."""
        self.status_change_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable):
        """Adiciona callback para alertas."""
        self.alert_callbacks.append(callback)
    
    def get_service_health(self, service_name: str) -> Optional[HealthCheck]:
        """Obtém status de saúde atual de um serviço."""
        if service_name in self.checkers:
            checker = self.checkers[service_name]
            if checker.last_check:
                return HealthCheck(
                    service_name=checker.name,
                    service_type=checker.service_type,
                    status=checker.last_status,
                    timestamp=checker.last_check,
                    response_time_ms=0,
                    metadata={'consecutive_failures': checker.consecutive_failures}
                )
        return None
    
    def get_all_services_health(self) -> List[HealthCheck]:
        """Obtém status de saúde de todos os serviços."""
        health_status = []
        for checker in self.checkers.values():
            if checker.last_check:
                health_status.append(HealthCheck(
                    service_name=checker.name,
                    service_type=checker.service_type,
                    status=checker.last_status,
                    timestamp=checker.last_check,
                    response_time_ms=0,
                    metadata={'consecutive_failures': checker.consecutive_failures}
                ))
        return health_status
    
    def get_service_metrics(self, service_name: str) -> Optional[ServiceMetrics]:
        """Obtém métricas agregadas de um serviço."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM service_metrics WHERE service_name = ?
                """, (service_name,))
                row = cursor.fetchone()
                
                if row:
                    return ServiceMetrics(
                        service_name=row[0],
                        service_type=ServiceType(row[1]),
                        total_checks=row[2],
                        successful_checks=row[3],
                        failed_checks=row[4],
                        average_response_time_ms=row[5],
                        uptime_percentage=row[6],
                        last_check=datetime.fromisoformat(row[7]),
                        last_status=HealthStatus(row[8])
                    )
        except Exception as e:
            logger.error(f"Erro ao obter métricas do serviço: {e}")
        
        return None
    
    def get_all_services_metrics(self) -> List[ServiceMetrics]:
        """Obtém métricas de todos os serviços."""
        metrics = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM service_metrics")
                for row in cursor.fetchall():
                    metrics.append(ServiceMetrics(
                        service_name=row[0],
                        service_type=ServiceType(row[1]),
                        total_checks=row[2],
                        successful_checks=row[3],
                        failed_checks=row[4],
                        average_response_time_ms=row[5],
                        uptime_percentage=row[6],
                        last_check=datetime.fromisoformat(row[7]),
                        last_status=HealthStatus(row[8])
                    ))
        except Exception as e:
            logger.error(f"Erro ao obter métricas: {e}")
        
        return metrics
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Obtém resumo geral da saúde do sistema."""
        all_metrics = self.get_all_services_metrics()
        
        if not all_metrics:
            return {'status': 'unknown', 'services_count': 0}
        
        # Calcula estatísticas gerais
        total_services = len(all_metrics)
        healthy_services = sum(1 for m in all_metrics if m.last_status == HealthStatus.HEALTHY)
        warning_services = sum(1 for m in all_metrics if m.last_status == HealthStatus.WARNING)
        critical_services = sum(1 for m in all_metrics if m.last_status == HealthStatus.CRITICAL)
        
        # Determina status geral
        if critical_services > 0:
            overall_status = 'critical'
        elif warning_services > 0:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        # Calcula uptime médio
        avg_uptime = sum(m.uptime_percentage for m in all_metrics) / total_services
        
        return {
            'status': overall_status,
            'services_count': total_services,
            'healthy_services': healthy_services,
            'warning_services': warning_services,
            'critical_services': critical_services,
            'average_uptime_percentage': round(avg_uptime, 2),
            'last_updated': datetime.now().isoformat()
        }
    
    # Verificadores padrão
    def _check_system_resources(self) -> Dict[str, Any]:
        """Verifica recursos do sistema."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Define limites
            cpu_ok = cpu_percent < 80
            memory_ok = memory.percent < 85
            disk_ok = disk.percent < 90
            
            success = cpu_ok and memory_ok and disk_ok
            
            return {
                'success': success,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'cpu_ok': cpu_ok,
                'memory_ok': memory_ok,
                'disk_ok': disk_ok
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _check_internet_connectivity(self) -> Dict[str, Any]:
        """Verifica conectividade com a internet."""
        try:
            # Testa múltiplos serviços
            test_urls = [
                'https://www.google.com',
                'https://www.cloudflare.com',
                'https://www.github.com'
            ]
            
            successful_tests = 0
            response_times = []
            
            for url in test_urls:
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=10)
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status_code == 200:
                        successful_tests += 1
                        response_times.append(response_time)
                except:
                    pass
            
            success = successful_tests >= 2  # Pelo menos 2 de 3 devem funcionar
            
            return {
                'success': success,
                'successful_tests': successful_tests,
                'total_tests': len(test_urls),
                'average_response_time_ms': sum(response_times) / len(response_times) if response_times else 0
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _check_database_connection(self) -> Dict[str, Any]:
        """Verifica conexão com o banco de dados."""
        try:
            import database
            # Tenta executar uma query simples
            conn = sqlite3.connect('ofertas.db')
            cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            
            success = result is not None and result[0] == 1
            
            return {
                'success': success,
                'database_name': 'ofertas.db'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Instância global do monitor de saúde
health_monitor = HealthMonitor()

# Funções de conveniência
def start_health_monitoring():
    """Inicia o monitoramento de saúde."""
    health_monitor.start_monitoring()

def stop_health_monitoring():
    """Para o monitoramento de saúde."""
    health_monitor.stop_monitoring()

def add_scraper_health_check(name: str, check_function: Callable, interval: int = 300):
    """Adiciona verificação de saúde para um scraper."""
    health_monitor.add_scraper_checker(name, check_function, interval)

def add_api_health_check(name: str, check_function: Callable, interval: int = 120):
    """Adiciona verificação de saúde para uma API."""
    health_monitor.add_api_checker(name, check_function, interval)

def get_system_health_summary() -> Dict[str, Any]:
    """Obtém resumo da saúde do sistema."""
    return health_monitor.get_health_summary()

def get_service_health(service_name: str) -> Optional[HealthCheck]:
    """Obtém saúde de um serviço específico."""
    return health_monitor.get_service_health(service_name)

def get_all_services_health() -> List[HealthCheck]:
    """Obtém saúde de todos os serviços."""
    return health_monitor.get_all_services_health()

if __name__ == "__main__":
    # Teste do sistema de monitoramento
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testando Sistema de Monitoramento de Saúde...")
    
    # Adiciona verificadores de exemplo
    def test_scraper_check():
        """Verificação de exemplo para scraper."""
        import random
        return random.choice([True, False])
    
    health_monitor.add_scraper_checker("test_scraper", test_scraper_check, 10)
    
    # Inicia monitoramento
    health_monitor.start_monitoring()
    
    # Aguarda algumas verificações
    time.sleep(30)
    
    # Mostra resumo
    summary = health_monitor.get_health_summary()
    print(f"Resumo de saúde: {summary}")
    
    # Para monitoramento
    health_monitor.stop_monitoring()
