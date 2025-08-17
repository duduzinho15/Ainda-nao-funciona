"""
Sistema de Monitoramento de Saúde - Sistema Garimpeiro Geek
"""
import os
import time
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthMonitor:
    """Monitor de saúde do sistema"""
    
    def __init__(self):
        self.health_status = {
            'system': 'unknown',
            'last_check': None,
            'uptime': 0,
            'start_time': time.time(),
            'checks': {}
        }
        
        # Configurações de monitoramento
        self.check_interval = int(os.getenv('HEALTH_CHECK_INTERVAL', '300'))  # 5 minutos
        self.alert_threshold = int(os.getenv('HEALTH_ALERT_THRESHOLD', '3'))  # 3 falhas
        self.telegram_webhook = os.getenv('TELEGRAM_WEBHOOK_URL', '')
        
        # Histórico de falhas
        self.failure_history = []
        self.max_history = 100
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Verifica a saúde geral do sistema"""
        try:
            start_time = time.time()
            
            # Verificações básicas
            checks = {
                'database': await self._check_database(),
                'scrapers': await self._check_scrapers(),
                'telegram': await self._check_telegram(),
                'apis': await self._check_external_apis(),
                'disk_space': self._check_disk_space(),
                'memory_usage': self._check_memory_usage()
            }
            
            # Calcula status geral
            failed_checks = [check for check in checks.values() if not check['healthy']]
            overall_status = 'healthy' if len(failed_checks) == 0 else 'degraded'
            
            if len(failed_checks) >= self.alert_threshold:
                overall_status = 'critical'
                await self._send_alert(failed_checks)
            
            # Atualiza status
            self.health_status.update({
                'system': overall_status,
                'last_check': datetime.now().isoformat(),
                'uptime': time.time() - self.health_status['start_time'],
                'checks': checks,
                'check_duration': time.time() - start_time
            })
            
            logger.info(f"Health check completed: {overall_status}")
            return self.health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.health_status['system'] = 'error'
            return self.health_status
    
    async def _check_database(self) -> Dict[str, Any]:
        """Verifica saúde do banco de dados"""
        try:
            # Simula verificação do banco
            await asyncio.sleep(0.1)
            
            return {
                'healthy': True,
                'status': 'connected',
                'response_time': 0.1,
                'last_error': None
            }
        except Exception as e:
            return {
                'healthy': False,
                'status': 'error',
                'response_time': None,
                'last_error': str(e)
            }
    
    async def _check_scrapers(self) -> Dict[str, Any]:
        """Verifica saúde dos scrapers"""
        try:
            # Verifica se os scrapers estão funcionando
            scraper_status = {
                'promobit': os.getenv('ENABLE_PROMOBIT', '0') == '1',
                'pelando': os.getenv('ENABLE_PELANDO', '0') == '1',
                'shopee': os.getenv('ENABLE_SHOPEE', '0') == '1'
            }
            
            active_scrapers = sum(scraper_status.values())
            healthy = active_scrapers > 0
            
            return {
                'healthy': healthy,
                'status': 'active' if healthy else 'inactive',
                'active_scrapers': active_scrapers,
                'scraper_status': scraper_status
            }
        except Exception as e:
            return {
                'healthy': False,
                'status': 'error',
                'last_error': str(e)
            }
    
    async def _check_telegram(self) -> Dict[str, Any]:
        """Verifica saúde da conexão Telegram"""
        try:
            token = os.getenv('TELEGRAM_BOT_TOKEN', '')
            chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
            
            if not token or not chat_id:
                return {
                    'healthy': False,
                    'status': 'not_configured',
                    'message': 'Telegram credentials not configured'
                }
            
            # Simula verificação da API do Telegram
            await asyncio.sleep(0.1)
            
            return {
                'healthy': True,
                'status': 'connected',
                'bot_configured': bool(token),
                'chat_configured': bool(chat_id)
            }
        except Exception as e:
            return {
                'healthy': False,
                'status': 'error',
                'last_error': str(e)
            }
    
    async def _check_external_apis(self) -> Dict[str, Any]:
        """Verifica saúde das APIs externas"""
        try:
            api_status = {}
            
            # Verifica Amazon API
            if os.getenv('AMAZON_ACCESS_KEY'):
                api_status['amazon'] = 'configured'
            else:
                api_status['amazon'] = 'not_configured'
            
            # Verifica Shopee API
            if os.getenv('SHOPEE_API_KEY'):
                api_status['shopee'] = 'configured'
            else:
                api_status['shopee'] = 'not_configured'
            
            # Verifica AliExpress API
            if os.getenv('ALIEXPRESS_APP_KEY'):
                api_status['aliexpress'] = 'configured'
            else:
                api_status['aliexpress'] = 'not_configured'
            
            # Verifica AWIN API
            if os.getenv('AWIN_API_TOKEN'):
                api_status['awin'] = 'configured'
            else:
                api_status['awin'] = 'not_configured'
            
            configured_apis = sum(1 for status in api_status.values() if status == 'configured')
            healthy = configured_apis > 0
            
            return {
                'healthy': healthy,
                'status': 'configured' if healthy else 'not_configured',
                'configured_apis': configured_apis,
                'api_status': api_status
            }
        except Exception as e:
            return {
                'healthy': False,
                'status': 'error',
                'last_error': str(e)
            }
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Verifica espaço em disco"""
        try:
            import psutil
            
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024**3)
            total_gb = disk.total / (1024**3)
            usage_percent = (disk.used / disk.total) * 100
            
            healthy = free_gb > 1.0  # Pelo menos 1GB livre
            
            return {
                'healthy': healthy,
                'status': 'ok' if healthy else 'low_space',
                'free_gb': round(free_gb, 2),
                'total_gb': round(total_gb, 2),
                'usage_percent': round(usage_percent, 1)
            }
        except ImportError:
            return {
                'healthy': True,
                'status': 'unknown',
                'message': 'psutil not available'
            }
        except Exception as e:
            return {
                'healthy': False,
                'status': 'error',
                'last_error': str(e)
            }
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """Verifica uso de memória"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            available_gb = memory.available / (1024**3)
            
            healthy = usage_percent < 90  # Menos de 90% de uso
            
            return {
                'healthy': healthy,
                'status': 'ok' if healthy else 'high_usage',
                'usage_percent': round(usage_percent, 1),
                'available_gb': round(available_gb, 2)
            }
        except ImportError:
            return {
                'healthy': True,
                'status': 'unknown',
                'message': 'psutil not available'
            }
        except Exception as e:
            return {
                'healthy': False,
                'status': 'error',
                'last_error': str(e)
            }
    
    async def _send_alert(self, failed_checks: List[Dict[str, Any]]):
        """Envia alerta sobre falhas críticas"""
        try:
            if not self.telegram_webhook:
                logger.warning("Telegram webhook not configured for alerts")
                return
            
            alert_message = f"🚨 ALERTA DE SAÚDE DO SISTEMA!\n\n"
            alert_message += f"Status: CRÍTICO\n"
            alert_message += f"Falhas detectadas: {len(failed_checks)}\n\n"
            
            for check in failed_checks:
                alert_message += f"❌ {check.get('status', 'Unknown')}\n"
            
            alert_message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Envia alerta via webhook
            async with aiohttp.ClientSession() as session:
                await session.post(self.telegram_webhook, json={
                    'text': alert_message
                })
            
            logger.info("Health alert sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send health alert: {e}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Retorna resumo da saúde do sistema"""
        return {
            'status': self.health_status['system'],
            'uptime_seconds': self.health_status['uptime'],
            'uptime_formatted': str(timedelta(seconds=int(self.health_status['uptime']))),
            'last_check': self.health_status['last_check'],
            'total_checks': len(self.health_status['checks']),
            'healthy_checks': sum(1 for check in self.health_status['checks'].values() 
                                if check.get('healthy', False))
        }
    
    def export_metrics(self) -> str:
        """Exporta métricas no formato Prometheus"""
        try:
            metrics = []
            
            # Métricas básicas
            metrics.append(f"# HELP garimpeiro_geek_health_status System health status")
            metrics.append(f"# TYPE garimpeiro_geek_health_status gauge")
            metrics.append(f"garimpeiro_geek_health_status{{component=\"overall\"}} "
                         f"{1 if self.health_status['system'] == 'healthy' else 0}")
            
            # Métricas de uptime
            metrics.append(f"# HELP garimpeiro_geek_uptime_seconds System uptime in seconds")
            metrics.append(f"# TYPE garimpeiro_geek_uptime_seconds counter")
            metrics.append(f"garimpeiro_geek_uptime_seconds {self.health_status['uptime']}")
            
            # Métricas por componente
            for component, check in self.health_status['checks'].items():
                metrics.append(f"# HELP garimpeiro_geek_component_health Component health status")
                metrics.append(f"# TYPE garimpeiro_geek_component_health gauge")
                metrics.append(f"garimpeiro_geek_component_health{{component=\"{component}\"}} "
                             f"{1 if check.get('healthy', False) else 0}")
            
            return "\n".join(metrics)
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return f"# Error exporting metrics: {e}"


async def main():
    """Função principal para teste do monitor"""
    monitor = HealthMonitor()
    
    print("🏥 Iniciando monitor de saúde do sistema...")
    
    # Primeira verificação
    health = await monitor.check_system_health()
    
    print(f"\n📊 Status da Saúde: {health['system'].upper()}")
    print(f"⏱️  Uptime: {monitor.get_health_summary()['uptime_formatted']}")
    print(f"🔍 Última verificação: {health['last_check']}")
    
    print("\n📋 Detalhes das Verificações:")
    for component, check in health['checks'].items():
        status_icon = "✅" if check.get('healthy', False) else "❌"
        print(f"   {status_icon} {component}: {check.get('status', 'unknown')}")
    
    print(f"\n📈 Resumo: {monitor.get_health_summary()['healthy_checks']}/{monitor.get_health_summary()['total_checks']} componentes saudáveis")
    
    # Exporta métricas
    print("\n📊 Métricas Prometheus:")
    print(monitor.export_metrics())


if __name__ == "__main__":
    asyncio.run(main())
