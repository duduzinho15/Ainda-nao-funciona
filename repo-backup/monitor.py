#!/usr/bin/env python3
"""
Script de Monitoramento do Garimpeiro Geek
Monitora performance, recursos e saúde do sistema
"""

import psutil
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import sqlite3
import asyncio
import aiohttp
from dataclasses import dataclass, asdict

@dataclass
class SystemMetrics:
    """Métricas do sistema"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    python_processes: int

@dataclass
class ApplicationMetrics:
    """Métricas da aplicação"""
    timestamp: datetime
    database_size: int
    log_file_count: int
    total_log_size: int
    backup_count: int
    backup_size_mb: float
    active_scrapers: int
    telegram_bot_status: str

class SystemMonitor:
    def __init__(self, config_file: str = "config.py"):
        self.config_file = Path(config_file)
        self.metrics_dir = Path(".data/metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("system_monitor")
        
        # Configurações de monitoramento
        self.monitoring_config = {
            "monitoring_interval": 60,  # segundos
            "metrics_retention_days": 30,
            "alert_thresholds": {
                "cpu_percent": 80.0,
                "memory_percent": 85.0,
                "disk_percent": 90.0,
                "database_size_mb": 1000,
                "log_size_mb": 500
            },
            "notifications": {
                "enabled": True,
                "telegram_chat_id": None,
                "email_enabled": False
            }
        }
        
        self.load_config()
        self.start_time = datetime.now()
        self.metrics_history: List[SystemMetrics] = []
        self.application_metrics_history: List[ApplicationMetrics] = []
    
    def load_config(self):
        """Carrega configurações do arquivo de configuração"""
        if self.config_file.exists():
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("config", self.config_file)
                config_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config_module)
                
                if hasattr(config_module, 'MONITORING_CONFIG'):
                    self.monitoring_config.update(config_module.MONITORING_CONFIG)
                    self.logger.info("Configurações de monitoramento carregadas")
            except Exception as e:
                self.logger.warning(f"Erro ao carregar configurações: {e}")
    
    def get_system_metrics(self) -> SystemMetrics:
        """Coleta métricas do sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memória
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Rede
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            # Processos
            process_count = len(psutil.pids())
            python_processes = len([p for p in psutil.process_iter(['name']) 
                                  if 'python' in p.info['name'].lower()])
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io=network_io,
                process_count=process_count,
                python_processes=python_processes
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar métricas do sistema: {e}")
            return None
    
    def get_application_metrics(self) -> ApplicationMetrics:
        """Coleta métricas da aplicação"""
        try:
            # Banco de dados
            db_size = 0
            db_path = Path(".data/garimpeiro_geek.db")
            if db_path.exists():
                db_size = db_path.stat().st_size
            
            # Logs
            log_dirs = ["logs", ".data/logs"]
            log_file_count = 0
            total_log_size = 0
            
            for log_dir in log_dirs:
                log_path = Path(log_dir)
                if log_path.exists():
                    for log_file in log_path.rglob("*.log"):
                        log_file_count += 1
                        total_log_size += log_file.stat().st_size
            
            # Backups
            backup_dir = Path("backups")
            backup_count = 0
            backup_size = 0
            
            if backup_dir.exists():
                for backup_file in backup_dir.glob("*.zip"):
                    backup_count += 1
                    backup_size += backup_file.stat().st_size
            
            # Status dos scrapers (simulado)
            active_scrapers = 0
            try:
                # Verificar se há processos de scraping ativos
                for proc in psutil.process_iter(['name', 'cmdline']):
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        if proc.info['cmdline'] and any('scraper' in cmd.lower() for cmd in proc.info['cmdline']):
                            active_scrapers += 1
            except:
                pass
            
            # Status do bot Telegram (simulado)
            telegram_bot_status = "unknown"
            try:
                for proc in psutil.process_iter(['name', 'cmdline']):
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        if proc.info['cmdline'] and any('telegram' in cmd.lower() for cmd in proc.info['cmdline']):
                            telegram_bot_status = "running"
                            break
                else:
                    telegram_bot_status = "stopped"
            except:
                pass
            
            return ApplicationMetrics(
                timestamp=datetime.now(),
                database_size=db_size,
                log_file_count=log_file_count,
                total_log_size=total_log_size,
                backup_count=backup_count,
                backup_size_mb=round(backup_size / (1024 * 1024), 2),
                active_scrapers=active_scrapers,
                telegram_bot_status=telegram_bot_status
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar métricas da aplicação: {e}")
            return None
    
    def check_alerts(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics) -> List[str]:
        """Verifica se há alertas baseado nos thresholds"""
        alerts = []
        
        # Verificar CPU
        if system_metrics.cpu_percent > self.monitoring_config["alert_thresholds"]["cpu_percent"]:
            alerts.append(f"⚠️ CPU alto: {system_metrics.cpu_percent:.1f}%")
        
        # Verificar memória
        if system_metrics.memory_percent > self.monitoring_config["alert_thresholds"]["memory_percent"]:
            alerts.append(f"⚠️ Memória alta: {system_metrics.memory_percent:.1f}%")
        
        # Verificar disco
        if system_metrics.disk_percent > self.monitoring_config["alert_thresholds"]["disk_percent"]:
            alerts.append(f"⚠️ Disco quase cheio: {system_metrics.disk_percent:.1f}%")
        
        # Verificar tamanho do banco
        db_size_mb = app_metrics.database_size / (1024 * 1024)
        if db_size_mb > self.monitoring_config["alert_thresholds"]["database_size_mb"]:
            alerts.append(f"⚠️ Banco de dados grande: {db_size_mb:.1f} MB")
        
        # Verificar tamanho dos logs
        log_size_mb = app_metrics.total_log_size / (1024 * 1024)
        if log_size_mb > self.monitoring_config["alert_thresholds"]["log_size_mb"]:
            alerts.append(f"⚠️ Logs grandes: {log_size_mb:.1f} MB")
        
        return alerts
    
    def save_metrics(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """Salva métricas em arquivo JSON"""
        try:
            # Adicionar às listas de histórico
            self.metrics_history.append(system_metrics)
            self.application_metrics_history.append(app_metrics)
            
            # Manter apenas histórico recente
            cutoff_date = datetime.now() - timedelta(days=self.monitoring_config["metrics_retention_days"])
            self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_date]
            self.application_metrics_history = [m for m in self.application_metrics_history if m.timestamp > cutoff_date]
            
            # Salvar em arquivo
            metrics_data = {
                "system_metrics": [asdict(m) for m in self.metrics_history],
                "application_metrics": [asdict(m) for m in self.application_metrics_history],
                "last_updated": datetime.now().isoformat()
            }
            
            metrics_file = self.metrics_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
            with open(metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)
            
            # Limpar arquivos antigos
            self.cleanup_old_metrics()
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar métricas: {e}")
    
    def cleanup_old_metrics(self):
        """Remove arquivos de métricas antigos"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.monitoring_config["metrics_retention_days"])
            
            for metrics_file in self.metrics_dir.glob("metrics_*.json"):
                try:
                    file_time = datetime.fromtimestamp(metrics_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        metrics_file.unlink()
                        self.logger.info(f"Arquivo de métricas antigo removido: {metrics_file.name}")
                except Exception as e:
                    self.logger.warning(f"Erro ao verificar arquivo {metrics_file}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Erro na limpeza de métricas: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Gera relatório de métricas"""
        if not self.metrics_history or not self.application_metrics_history:
            return {"error": "Nenhuma métrica disponível"}
        
        # Métricas mais recentes
        latest_system = self.metrics_history[-1]
        latest_app = self.application_metrics_history[-1]
        
        # Calcular médias
        cpu_avg = sum(m.cpu_percent for m in self.metrics_history) / len(self.metrics_history)
        memory_avg = sum(m.memory_percent for m in self.metrics_history) / len(self.metrics_history)
        
        # Calcular tendências
        cpu_trend = "↗️" if latest_system.cpu_percent > cpu_avg else "↘️"
        memory_trend = "↗️" if latest_system.memory_percent > memory_avg else "↘️"
        
        # Tempo de execução
        uptime = datetime.now() - self.start_time
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime": str(uptime).split('.')[0],  # Remover microssegundos
            "system": {
                "current": {
                    "cpu_percent": latest_system.cpu_percent,
                    "memory_percent": latest_system.memory_percent,
                    "disk_percent": latest_system.disk_percent,
                    "process_count": latest_system.process_count,
                    "python_processes": latest_system.python_processes
                },
                "averages": {
                    "cpu_percent": round(cpu_avg, 1),
                    "memory_percent": round(memory_avg, 1)
                },
                "trends": {
                    "cpu": cpu_trend,
                    "memory": memory_trend
                }
            },
            "application": {
                "database_size_mb": round(latest_app.database_size / (1024 * 1024), 2),
                "log_file_count": latest_app.log_file_count,
                "log_size_mb": round(latest_app.total_log_size / (1024 * 1024), 2),
                "backup_count": latest_app.backup_count,
                "backup_size_mb": latest_app.backup_size_mb,
                "active_scrapers": latest_app.active_scrapers,
                "telegram_bot_status": latest_app.telegram_bot_status
            },
            "network": {
                "bytes_sent_mb": round(latest_system.network_io["bytes_sent"] / (1024 * 1024), 2),
                "bytes_recv_mb": round(latest_system.network_io["bytes_recv"] / (1024 * 1024), 2)
            },
            "alerts": self.check_alerts(latest_system, latest_app)
        }
    
    def print_report(self, report: Dict[str, Any]):
        """Imprime relatório formatado"""
        print("\n" + "="*60)
        print("📊 RELATÓRIO DE MONITORAMENTO - GARIMPEIRO GEEK")
        print("="*60)
        
        if "error" in report:
            print(f"❌ {report['error']}")
            return
        
        # Informações gerais
        print(f"🕐 Última atualização: {report['timestamp']}")
        print(f"⏱️  Tempo de execução: {report['uptime']}")
        
        # Sistema
        print(f"\n💻 SISTEMA:")
        print(f"  CPU: {report['system']['current']['cpu_percent']:.1f}% {report['system']['trends']['cpu']} (média: {report['system']['averages']['cpu_percent']:.1f}%)")
        print(f"  Memória: {report['system']['current']['memory_percent']:.1f}% {report['system']['trends']['memory']} (média: {report['system']['averages']['memory_percent']:.1f}%)")
        print(f"  Disco: {report['system']['current']['disk_percent']:.1f}%")
        print(f"  Processos: {report['system']['current']['process_count']} (Python: {report['system']['current']['python_processes']})")
        
        # Aplicação
        print(f"\n🚀 APLICAÇÃO:")
        print(f"  Banco de dados: {report['application']['database_size_mb']:.2f} MB")
        print(f"  Logs: {report['application']['log_file_count']} arquivos ({report['application']['log_size_mb']:.2f} MB)")
        print(f"  Backups: {report['application']['backup_count']} ({report['application']['backup_size_mb']:.2f} MB)")
        print(f"  Scrapers ativos: {report['application']['active_scrapers']}")
        print(f"  Bot Telegram: {report['application']['telegram_bot_status']}")
        
        # Rede
        print(f"\n🌐 REDE:")
        print(f"  Enviado: {report['network']['bytes_sent_mb']:.2f} MB")
        print(f"  Recebido: {report['network']['bytes_recv_mb']:.2f} MB")
        
        # Alertas
        if report['alerts']:
            print(f"\n🚨 ALERTAS:")
            for alert in report['alerts']:
                print(f"  {alert}")
        else:
            print(f"\n✅ Nenhum alerta - Sistema saudável!")
        
        print("="*60)
    
    async def monitor_continuously(self):
        """Monitora o sistema continuamente"""
        self.logger.info("Iniciando monitoramento contínuo...")
        
        while True:
            try:
                # Coletar métricas
                system_metrics = self.get_system_metrics()
                app_metrics = self.get_application_metrics()
                
                if system_metrics and app_metrics:
                    # Salvar métricas
                    self.save_metrics(system_metrics, app_metrics)
                    
                    # Verificar alertas
                    alerts = self.check_alerts(system_metrics, app_metrics)
                    if alerts:
                        self.logger.warning(f"Alertas detectados: {alerts}")
                    
                    # Gerar e imprimir relatório
                    report = self.generate_report()
                    self.print_report(report)
                
                # Aguardar próximo ciclo
                await asyncio.sleep(self.monitoring_config["monitoring_interval"])
                
            except KeyboardInterrupt:
                self.logger.info("Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                self.logger.error(f"Erro no monitoramento: {e}")
                await asyncio.sleep(10)  # Aguardar antes de tentar novamente

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor do Sistema Garimpeiro Geek")
    parser.add_argument("--once", action="store_true", help="Executar apenas uma vez")
    parser.add_argument("--continuous", action="store_true", help="Executar continuamente")
    parser.add_argument("--report", action="store_true", help="Gerar relatório das métricas salvas")
    parser.add_argument("--config", type=str, default="config.py", help="Arquivo de configuração")
    
    args = parser.parse_args()
    
    monitor = SystemMonitor(args.config)
    
    try:
        if args.once:
            # Executar uma vez
            system_metrics = monitor.get_system_metrics()
            app_metrics = monitor.get_application_metrics()
            
            if system_metrics and app_metrics:
                monitor.save_metrics(system_metrics, app_metrics)
                report = monitor.generate_report()
                monitor.print_report(report)
            else:
                print("❌ Erro ao coletar métricas")
        
        elif args.report:
            # Gerar relatório das métricas salvas
            report = monitor.generate_report()
            monitor.print_report(report)
        
        elif args.continuous:
            # Executar continuamente
            asyncio.run(monitor.monitor_continuously())
        
        else:
            # Modo interativo
            print("🔄 Monitor do Sistema Garimpeiro Geek")
            print("=" * 50)
            
            while True:
                print("\nEscolha uma opção:")
                print("1. Verificar sistema (uma vez)")
                print("2. Monitoramento contínuo")
                print("3. Gerar relatório")
                print("4. Ver configurações")
                print("0. Sair")
                
                choice = input("\nOpção: ").strip()
                
                if choice == "1":
                    system_metrics = monitor.get_system_metrics()
                    app_metrics = monitor.get_application_metrics()
                    
                    if system_metrics and app_metrics:
                        monitor.save_metrics(system_metrics, app_metrics)
                        report = monitor.generate_report()
                        monitor.print_report(report)
                    else:
                        print("❌ Erro ao coletar métricas")
                
                elif choice == "2":
                    print("🔄 Iniciando monitoramento contínuo... (Ctrl+C para parar)")
                    try:
                        asyncio.run(monitor.monitor_continuously())
                    except KeyboardInterrupt:
                        print("\n⏹️ Monitoramento parado")
                
                elif choice == "3":
                    report = monitor.generate_report()
                    monitor.print_report(report)
                
                elif choice == "4":
                    print("\n⚙️ Configurações de Monitoramento:")
                    for key, value in monitor.monitoring_config.items():
                        print(f"  {key}: {value}")
                
                elif choice == "0":
                    print("👋 Até logo!")
                    break
                
                else:
                    print("❌ Opção inválida")
    
    except KeyboardInterrupt:
        print("\n\n👋 Operação cancelada pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()

