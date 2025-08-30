"""
Sistema de Monitoramento para o Garimpeiro Geek.
Monitora saúde do sistema e gera alertas automáticos.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from src.core.cache.redis_manager import redis_manager


class AlertLevel(Enum):
    """Níveis de alerta."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Status de um alerta."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class SystemAlert:
    """Alerta do sistema."""
    id: str
    level: AlertLevel
    title: str
    message: str
    component: str
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthMetric:
    """Métrica de saúde do sistema."""
    name: str
    value: float
    unit: str
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime


class SystemMonitor:
    """Monitor do sistema."""
    
    def __init__(self):
        """Inicializa o monitor."""
        self.logger = logging.getLogger(__name__)
        
        # Alertas ativos
        self.active_alerts: Dict[str, SystemAlert] = {}
        
        # Métricas de saúde
        self.health_metrics: Dict[str, HealthMetric] = {}
        
        # Callbacks de alerta
        self.alert_callbacks: List[Callable[[SystemAlert], None]] = []
        
        # Configurações
        self.monitoring_interval = 30  # segundos
        self.alert_cooldown = 300  # 5 minutos
        
        # Estatísticas
        self.stats = {
            "total_alerts": 0,
            "active_alerts": 0,
            "resolved_alerts": 0,
            "last_check": None
        }
        
        # Inicializar métricas padrão
        self._initialize_default_metrics()
    
    def _initialize_default_metrics(self):
        """Inicializa métricas padrão do sistema."""
        default_metrics = {
            "cpu_usage": HealthMetric(
                name="CPU Usage",
                value=0.0,
                unit="%",
                threshold_warning=70.0,
                threshold_critical=90.0,
                timestamp=datetime.now()
            ),
            "memory_usage": HealthMetric(
                name="Memory Usage",
                value=0.0,
                unit="%",
                threshold_warning=80.0,
                threshold_critical=95.0,
                timestamp=datetime.now()
            ),
            "disk_usage": HealthMetric(
                name="Disk Usage",
                value=0.0,
                unit="%",
                threshold_warning=85.0,
                threshold_critical=95.0,
                timestamp=datetime.now()
            ),
            "response_time": HealthMetric(
                name="Response Time",
                value=0.0,
                unit="ms",
                threshold_warning=1000.0,
                threshold_critical=5000.0,
                timestamp=datetime.now()
            )
        }
        
        self.health_metrics.update(default_metrics)
    
    async def start_monitoring(self):
        """Inicia o monitoramento do sistema."""
        self.logger.info("🔍 Iniciando monitoramento do sistema")
        
        # Iniciar loop de monitoramento
        asyncio.create_task(self._monitoring_loop())
    
    async def _monitoring_loop(self):
        """Loop principal de monitoramento."""
        while True:
            try:
                await self._check_system_health()
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Erro no loop de monitoramento: {e}")
                await asyncio.sleep(10)
    
    async def _check_system_health(self):
        """Verifica saúde do sistema."""
        try:
            self.logger.debug("🔍 Verificando saúde do sistema...")
            
            # Verificar Redis
            await self._check_redis_health()
            
            # Verificar métricas do sistema
            await self._check_system_metrics()
            
            # Verificar alertas antigos
            await self._check_old_alerts()
            
            # Atualizar estatísticas
            self.stats["last_check"] = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Erro na verificação de saúde: {e}")
    
    async def _check_redis_health(self):
        """Verifica saúde do Redis."""
        try:
            redis_healthy = await redis_manager.health_check()
            
            if not redis_healthy:
                await self._create_alert(
                    level=AlertLevel.ERROR,
                    title="Redis Unhealthy",
                    message="Redis não está respondendo corretamente",
                    component="redis"
                )
            else:
                # Resolver alertas de Redis se existirem
                await self._resolve_component_alerts("redis")
                
        except Exception as e:
            self.logger.error(f"Erro ao verificar Redis: {e}")
    
    async def _check_system_metrics(self):
        """Verifica métricas do sistema."""
        try:
            # Simular coleta de métricas
            # Em produção, isso viria de um sistema de monitoramento real
            
            # CPU Usage (simulado)
            cpu_usage = 45.0  # Simular 45% de uso
            self._update_metric("cpu_usage", cpu_usage)
            
            # Memory Usage (simulado)
            memory_usage = 65.0  # Simular 65% de uso
            self._update_metric("memory_usage", memory_usage)
            
            # Disk Usage (simulado)
            disk_usage = 75.0  # Simular 75% de uso
            self._update_metric("disk_usage", disk_usage)
            
            # Response Time (simulado)
            response_time = 250.0  # Simular 250ms
            self._update_metric("response_time", response_time)
            
            # Verificar thresholds
            await self._check_metric_thresholds()
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar métricas: {e}")
    
    def _update_metric(self, metric_name: str, value: float):
        """Atualiza uma métrica."""
        if metric_name in self.health_metrics:
            self.health_metrics[metric_name].value = value
            self.health_metrics[metric_name].timestamp = datetime.now()
    
    async def _check_metric_thresholds(self):
        """Verifica thresholds das métricas."""
        for metric_name, metric in self.health_metrics.items():
            try:
                if metric.value >= metric.threshold_critical:
                    await self._create_alert(
                        level=AlertLevel.CRITICAL,
                        title=f"{metric.name} Critical",
                        message=f"{metric.name}: {metric.value}{metric.unit} (threshold: {metric.threshold_critical}{metric.unit})",
                        component=metric_name
                    )
                elif metric.value >= metric.threshold_warning:
                    await self._create_alert(
                        level=AlertLevel.WARNING,
                        title=f"{metric.name} Warning",
                        message=f"{metric.name}: {metric.value}{metric.unit} (threshold: {metric.threshold_warning}{metric.unit})",
                        component=metric_name
                    )
                else:
                    # Resolver alertas se métrica voltou ao normal
                    await self._resolve_component_alerts(metric_name)
                    
            except Exception as e:
                self.logger.error(f"Erro ao verificar threshold de {metric_name}: {e}")
    
    async def _create_alert(self, level: AlertLevel, title: str, 
                           message: str, component: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Cria um novo alerta.
        
        Args:
            level: Nível do alerta
            title: Título do alerta
            message: Mensagem do alerta
            component: Componente afetado
            metadata: Metadados adicionais
        """
        try:
            # Verificar se já existe alerta similar
            alert_key = f"{component}:{title}"
            
            if alert_key in self.active_alerts:
                # Atualizar alerta existente
                existing_alert = self.active_alerts[alert_key]
                existing_alert.timestamp = datetime.now()
                existing_alert.message = message
                if metadata:
                    existing_alert.metadata.update(metadata)
                return
            
            # Criar novo alerta
            alert = SystemAlert(
                id=alert_key,
                level=level,
                title=title,
                message=message,
                component=component,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            # Adicionar aos alertas ativos
            self.active_alerts[alert_key] = alert
            
            # Atualizar estatísticas
            self.stats["total_alerts"] += 1
            self.stats["active_alerts"] = len(self.active_alerts)
            
            # Log do alerta
            self.logger.warning(f"🚨 ALERTA {level.value.upper()}: {title} - {message}")
            
            # Executar callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"Erro no callback de alerta: {e}")
            
        except Exception as e:
            self.logger.error(f"Erro ao criar alerta: {e}")
    
    async def _resolve_component_alerts(self, component: str):
        """Resolve alertas de um componente específico."""
        alerts_to_resolve = []
        
        for alert_id, alert in self.active_alerts.items():
            if alert.component == component:
                alerts_to_resolve.append(alert_id)
        
        for alert_id in alerts_to_resolve:
            await self._resolve_alert(alert_id, "Componente voltou ao normal")
    
    async def _resolve_alert(self, alert_id: str, resolution_message: str):
        """
        Resolve um alerta específico.
        
        Args:
            alert_id: ID do alerta
            resolution_message: Mensagem de resolução
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts.pop(alert_id)
            alert.status = AlertStatus.RESOLVED
            
            # Atualizar estatísticas
            self.stats["active_alerts"] = len(self.active_alerts)
            self.stats["resolved_alerts"] += 1
            
            self.logger.info(f"✅ Alerta resolvido: {alert.title} - {resolution_message}")
    
    async def _check_old_alerts(self):
        """Verifica alertas antigos para limpeza."""
        now = datetime.now()
        alerts_to_clean = []
        
        for alert_id, alert in self.active_alerts.items():
            # Limpar alertas com mais de 24 horas
            if (now - alert.timestamp).total_seconds() > 86400:  # 24 horas
                alerts_to_clean.append(alert_id)
        
        for alert_id in alerts_to_clean:
            await self._resolve_alert(alert_id, "Alerta expirado")
    
    def add_alert_callback(self, callback: Callable[[SystemAlert], None]):
        """Adiciona callback para alertas."""
        self.alert_callbacks.append(callback)
        self.logger.info(f"Callback de alerta adicionado: {callback.__name__}")
    
    def get_active_alerts(self) -> List[SystemAlert]:
        """Retorna alertas ativos."""
        return list(self.active_alerts.values())
    
    def get_alerts_by_level(self, level: AlertLevel) -> List[SystemAlert]:
        """Retorna alertas por nível."""
        return [alert for alert in self.active_alerts.values() if alert.level == level]
    
    def get_alerts_by_component(self, component: str) -> List[SystemAlert]:
        """Retorna alertas por componente."""
        return [alert for alert in self.active_alerts.values() if alert.component == component]
    
    def get_health_metrics(self) -> Dict[str, HealthMetric]:
        """Retorna métricas de saúde."""
        return self.health_metrics.copy()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema."""
        stats = self.stats.copy()
        
        # Adicionar métricas atuais
        stats["current_metrics"] = {
            name: {
                "value": metric.value,
                "unit": metric.unit,
                "status": self._get_metric_status(metric)
            }
            for name, metric in self.health_metrics.items()
        }
        
        return stats
    
    def _get_metric_status(self, metric: HealthMetric) -> str:
        """Retorna status de uma métrica."""
        if metric.value >= metric.threshold_critical:
            return "critical"
        elif metric.value >= metric.threshold_warning:
            return "warning"
        else:
            return "healthy"
    
    async def health_check(self) -> bool:
        """Verifica saúde geral do sistema."""
        try:
            # Verificar Redis
            redis_healthy = await redis_manager.health_check()
            
            # Verificar métricas críticas
            critical_metrics = [
                metric for metric in self.health_metrics.values()
                if metric.value >= metric.threshold_critical
            ]
            
            # Sistema saudável se Redis OK e sem métricas críticas
            return redis_healthy and len(critical_metrics) == 0
            
        except Exception as e:
            self.logger.error(f"Health check falhou: {e}")
            return False


# Instância global do monitor
system_monitor = SystemMonitor()

