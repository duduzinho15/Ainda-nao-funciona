"""
Dashboard Web para Produção - Sistema de Recomendações
Interface web para monitoramento de métricas, status e configurações em tempo real
"""
import os
import json
import logging
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Flask e dependências web
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import plotly.graph_objs as go
import plotly.utils
import pandas as pd

# Sistema de monitoramento
from deployment.alert_system import AlertSystem, AlertLevel
from deployment.backup_system import DatabaseBackupSystem
from deployment.production_setup import ProductionConfig

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionDashboard:
    """Dashboard web para monitoramento de produção"""
    
    def __init__(self, config_path: str = "config_producao.env"):
        self.config = ProductionConfig(config_path)
        self.alert_system = AlertSystem(config_path)
        self.backup_system = DatabaseBackupSystem(config_path)
        
        # Configurações do dashboard
        self.dashboard_config = {
            'title': 'Sistema de Recomendações - Dashboard de Produção',
            'refresh_interval': 30,  # segundos
            'max_data_points': 1000,
            'timezone': 'America/Sao_Paulo'
        }
        
        # Dados em tempo real
        self.real_time_data = {
            'system_metrics': {},
            'performance_metrics': {},
            'error_logs': [],
            'alert_history': [],
            'backup_status': {},
            'last_update': datetime.now().isoformat()
        }
        
        # Inicializa Flask
        self.app = Flask(__name__)
        self.app.secret_key = self.config.load_config().get('SECRET_KEY', 'dev-secret-key')
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Configura rotas
        self._setup_routes()
        
        # Inicia thread de atualização de dados
        self.data_update_thread = None
        self.running = False
        self.start_data_updater()
    
    def _setup_routes(self):
        """Configura rotas do dashboard"""
        
        @self.app.route('/')
        def index():
            """Página principal do dashboard"""
            return render_template('dashboard.html', 
                                title=self.dashboard_config['title'],
                                config=self.dashboard_config)
        
        @self.app.route('/api/status')
        def api_status():
            """API para status geral do sistema"""
            try:
                status = self._get_system_status()
                return jsonify(status)
            except Exception as e:
                logger.error(f"Erro ao obter status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """API para métricas do sistema"""
            try:
                metrics = self._get_system_metrics()
                return jsonify(metrics)
            except Exception as e:
                logger.error(f"Erro ao obter métricas: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/alerts')
        def api_alerts():
            """API para histórico de alertas"""
            try:
                alerts = self._get_alert_history()
                return jsonify(alerts)
            except Exception as e:
                logger.error(f"Erro ao obter alertas: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/backups')
        def api_backups():
            """API para status de backups"""
            try:
                backups = self._get_backup_status()
                return jsonify(backups)
            except Exception as e:
                logger.error(f"Erro ao obter status de backup: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/charts/<chart_type>')
        def api_charts(chart_type):
            """API para gráficos"""
            try:
                chart_data = self._generate_chart_data(chart_type)
                return jsonify(chart_data)
            except Exception as e:
                logger.error(f"Erro ao gerar gráfico {chart_type}: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/config')
        def config_page():
            """Página de configuração"""
            config_data = self.config.load_config()
            return render_template('config.html', 
                                title="Configuração de Produção",
                                config=config_data)
        
        @self.app.route('/config/update', methods=['POST'])
        def update_config():
            """Atualiza configurações"""
            try:
                # Processa dados do formulário
                form_data = request.form.to_dict()
                
                # Valida e salva configuração
                validation = self.config.validate_config(form_data)
                if validation['is_valid']:
                    self.config.save_config(validation['config'])
                    flash('Configuração atualizada com sucesso!', 'success')
                else:
                    for error in validation['errors']:
                        flash(f'Erro: {error}', 'error')
                
                return redirect(url_for('config_page'))
                
            except Exception as e:
                flash(f'Erro ao atualizar configuração: {e}', 'error')
                return redirect(url_for('config_page'))
        
        @self.app.route('/alerts')
        def alerts_page():
            """Página de alertas"""
            alert_status = self.alert_system.get_alert_status()
            return render_template('alerts.html',
                                title="Sistema de Alertas",
                                alerts=alert_status)
        
        @self.app.route('/backups')
        def backups_page():
            """Página de backups"""
            backup_status = self.backup_system.get_backup_status()
            return render_template('backups.html',
                                title="Sistema de Backups",
                                backups=backup_status)
        
        @self.app.route('/logs')
        def logs_page():
            """Página de logs"""
            log_data = self._get_recent_logs()
            return render_template('logs.html',
                                title="Logs do Sistema",
                                logs=log_data)
        
        # WebSocket para atualizações em tempo real
        @self.socketio.on('connect')
        def handle_connect():
            """Cliente conectado"""
            logger.info("Cliente conectado ao dashboard")
            emit('status', self._get_system_status())
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Cliente desconectado"""
            logger.info("Cliente desconectado do dashboard")
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Obtém status geral do sistema"""
        try:
            # Status dos sistemas
            alert_status = self.alert_system.get_alert_status()
            backup_status = self.backup_system.get_backup_status()
            
            # Métricas do sistema
            system_metrics = self._get_system_metrics()
            
            # Status geral
            overall_status = 'operational'
            if (alert_status.get('status') == 'error' or 
                backup_status.get('status') == 'error'):
                overall_status = 'error'
            elif (alert_status.get('status') == 'warning' or 
                  backup_status.get('status') == 'warning'):
                overall_status = 'warning'
            
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': overall_status,
                'systems': {
                    'alerts': alert_status,
                    'backups': backup_status
                },
                'metrics': system_metrics,
                'uptime': self._calculate_uptime(),
                'version': '1.0.0'
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter status do sistema: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do sistema"""
        try:
            # Métricas básicas do sistema
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Métricas de rede
            network = psutil.net_io_counters()
            
            # Métricas de processos
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count(),
                    'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {}
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'process': {
                    'memory_rss': process_memory.rss,
                    'memory_vms': process_memory.vms,
                    'cpu_percent': process.cpu_percent(),
                    'num_threads': process.num_threads()
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter métricas do sistema: {e}")
            return {'error': str(e)}
    
    def _get_alert_history(self) -> Dict[str, Any]:
        """Obtém histórico de alertas"""
        try:
            alert_status = self.alert_system.get_alert_status()
            
            # Filtra alertas recentes
            recent_alerts = alert_status.get('recent_alerts', [])
            
            # Agrupa por nível
            alert_counts = {}
            for alert in recent_alerts:
                level = alert.get('level', 'unknown')
                alert_counts[level] = alert_counts.get(level, 0) + 1
            
            return {
                'total_alerts': len(recent_alerts),
                'alert_counts': alert_counts,
                'recent_alerts': recent_alerts[-20:],  # Últimos 20 alertas
                'system_status': alert_status
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico de alertas: {e}")
            return {'error': str(e)}
    
    def _get_backup_status(self) -> Dict[str, Any]:
        """Obtém status dos backups"""
        try:
            backup_status = self.backup_system.get_backup_status()
            
            # Adiciona informações adicionais
            if backup_status.get('status') == 'operational':
                backup_status['health'] = 'good'
                if backup_status.get('backup_success_rate', 0) < 90:
                    backup_status['health'] = 'warning'
                if backup_status.get('backup_success_rate', 0) < 70:
                    backup_status['health'] = 'critical'
            else:
                backup_status['health'] = 'critical'
            
            return backup_status
            
        except Exception as e:
            logger.error(f"Erro ao obter status de backup: {e}")
            return {'error': str(e)}
    
    def _generate_chart_data(self, chart_type: str) -> Dict[str, Any]:
        """Gera dados para gráficos"""
        try:
            if chart_type == 'cpu_usage':
                return self._generate_cpu_chart()
            elif chart_type == 'memory_usage':
                return self._generate_memory_chart()
            elif chart_type == 'alert_trends':
                return self._generate_alert_trends_chart()
            elif chart_type == 'backup_history':
                return self._generate_backup_history_chart()
            else:
                return {'error': f'Tipo de gráfico não suportado: {chart_type}'}
                
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico {chart_type}: {e}")
            return {'error': str(e)}
    
    def _generate_cpu_chart(self) -> Dict[str, Any]:
        """Gera gráfico de uso de CPU"""
        try:
            # Simula dados históricos (em produção, viria do banco)
            timestamps = pd.date_range(start=datetime.now() - timedelta(hours=24), 
                                     end=datetime.now(), 
                                     freq='5T')
            
            # Dados simulados
            cpu_data = [30 + i * 0.5 + np.random.normal(0, 5) for i in range(len(timestamps))]
            cpu_data = [max(0, min(100, x)) for x in cpu_data]  # Limita entre 0-100
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=cpu_data,
                mode='lines',
                name='CPU %',
                line=dict(color='#1f77b4', width=2)
            ))
            
            fig.update_layout(
                title='Uso de CPU (Últimas 24h)',
                xaxis_title='Tempo',
                yaxis_title='CPU (%)',
                yaxis=dict(range=[0, 100]),
                height=400
            )
            
            return {
                'chart_data': json.loads(fig.to_json()),
                'summary': {
                    'current': cpu_data[-1],
                    'average': sum(cpu_data) / len(cpu_data),
                    'max': max(cpu_data),
                    'min': min(cpu_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico de CPU: {e}")
            return {'error': str(e)}
    
    def _generate_memory_chart(self) -> Dict[str, Any]:
        """Gera gráfico de uso de memória"""
        try:
            import psutil
            
            # Simula dados históricos
            timestamps = pd.date_range(start=datetime.now() - timedelta(hours=24), 
                                     end=datetime.now(), 
                                     freq='5T')
            
            memory = psutil.virtual_memory()
            current_percent = memory.percent
            
            # Dados simulados baseados no valor atual
            memory_data = [current_percent + np.random.normal(0, 3) for _ in range(len(timestamps))]
            memory_data = [max(0, min(100, x)) for x in memory_data]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=memory_data,
                mode='lines',
                name='Memória %',
                line=dict(color='#ff7f0e', width=2)
            ))
            
            fig.update_layout(
                title='Uso de Memória (Últimas 24h)',
                xaxis_title='Tempo',
                yaxis_title='Memória (%)',
                yaxis=dict(range=[0, 100]),
                height=400
            )
            
            return {
                'chart_data': json.loads(fig.to_json()),
                'summary': {
                    'current': memory_data[-1],
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico de memória: {e}")
            return {'error': str(e)}
    
    def _generate_alert_trends_chart(self) -> Dict[str, Any]:
        """Gera gráfico de tendências de alertas"""
        try:
            # Simula dados de alertas por hora
            timestamps = pd.date_range(start=datetime.now() - timedelta(hours=24), 
                                     end=datetime.now(), 
                                     freq='1H')
            
            # Dados simulados
            critical_alerts = [np.random.poisson(0.5) for _ in range(len(timestamps))]
            error_alerts = [np.random.poisson(1.0) for _ in range(len(timestamps))]
            warning_alerts = [np.random.poisson(2.0) for _ in range(len(timestamps))]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=critical_alerts,
                mode='lines+markers',
                name='Críticos',
                line=dict(color='#d62728', width=3)
            ))
            
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=error_alerts,
                mode='lines+markers',
                name='Erros',
                line=dict(color='#ff7f0e', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=warning_alerts,
                mode='lines+markers',
                name='Avisos',
                line=dict(color='#2ca02c', width=2)
            ))
            
            fig.update_layout(
                title='Tendências de Alertas (Últimas 24h)',
                xaxis_title='Tempo',
                yaxis_title='Quantidade de Alertas',
                height=400
            )
            
            return {
                'chart_data': json.loads(fig.to_json()),
                'summary': {
                    'total_critical': sum(critical_alerts),
                    'total_errors': sum(error_alerts),
                    'total_warnings': sum(warning_alerts)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico de tendências: {e}")
            return {'error': str(e)}
    
    def _generate_backup_history_chart(self) -> Dict[str, Any]:
        """Gera gráfico de histórico de backups"""
        try:
            backup_status = self.backup_system.get_backup_status()
            recent_backups = backup_status.get('recent_backups', [])
            
            if not recent_backups:
                return {'error': 'Nenhum backup encontrado'}
            
            # Prepara dados para o gráfico
            dates = [datetime.fromisoformat(backup['date']) for backup in recent_backups]
            sizes = [backup['size'] for backup in recent_backups]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=dates,
                y=sizes,
                name='Tamanho do Backup',
                marker_color='#1f77b4'
            ))
            
            fig.update_layout(
                title='Histórico de Backups',
                xaxis_title='Data',
                yaxis_title='Tamanho (bytes)',
                height=400
            )
            
            return {
                'chart_data': json.loads(fig.to_json()),
                'summary': {
                    'total_backups': len(recent_backups),
                    'total_size': sum(sizes),
                    'average_size': sum(sizes) / len(sizes) if sizes else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar gráfico de backups: {e}")
            return {'error': str(e)}
    
    def _calculate_uptime(self) -> str:
        """Calcula tempo de atividade do sistema"""
        try:
            import psutil
            
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
                
        except Exception as e:
            logger.error(f"Erro ao calcular uptime: {e}")
            return "Desconhecido"
    
    def _get_recent_logs(self) -> Dict[str, Any]:
        """Obtém logs recentes do sistema"""
        try:
            log_file = self.config.load_config().get('LOG_FILE', './logs/production.log')
            
            if not os.path.exists(log_file):
                return {'logs': [], 'total_lines': 0}
            
            # Lê últimas 100 linhas do log
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            recent_lines = lines[-100:] if len(lines) > 100 else lines
            
            # Processa linhas de log
            processed_logs = []
            for line in recent_lines:
                try:
                    # Tenta extrair informações do log
                    if ' - ' in line:
                        parts = line.split(' - ', 2)
                        if len(parts) >= 3:
                            timestamp, level, message = parts
                            processed_logs.append({
                                'timestamp': timestamp.strip(),
                                'level': level.strip(),
                                'message': message.strip()
                            })
                except:
                    continue
            
            return {
                'logs': processed_logs[-50:],  # Últimos 50 logs processados
                'total_lines': len(lines),
                'log_file': log_file
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter logs: {e}")
            return {'error': str(e)}
    
    def start_data_updater(self):
        """Inicia thread para atualizar dados em tempo real"""
        if self.data_update_thread and self.data_update_thread.is_alive():
            return
        
        self.running = True
        self.data_update_thread = threading.Thread(target=self._update_data_loop, daemon=True)
        self.data_update_thread.start()
        logger.info("🚀 Thread de atualização de dados iniciada")
    
    def stop_data_updater(self):
        """Para thread de atualização de dados"""
        self.running = False
        if self.data_update_thread and self.data_update_thread.is_alive():
            self.data_update_thread.join(timeout=5)
        logger.info("🛑 Thread de atualização de dados parada")
    
    def _update_data_loop(self):
        """Loop principal de atualização de dados"""
        while self.running:
            try:
                # Atualiza dados
                self.real_time_data['system_metrics'] = self._get_system_metrics()
                self.real_time_data['last_update'] = datetime.now().isoformat()
                
                # Envia atualizações via WebSocket
                self.socketio.emit('data_update', self.real_time_data)
                
                # Aguarda próximo ciclo
                time.sleep(self.dashboard_config['refresh_interval'])
                
            except Exception as e:
                logger.error(f"Erro na atualização de dados: {e}")
                time.sleep(10)  # Espera mais tempo em caso de erro
    
    def run(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """Executa o dashboard"""
        try:
            logger.info(f"🚀 Iniciando dashboard em http://{host}:{port}")
            
            if debug:
                self.app.run(host=host, port=port, debug=debug)
            else:
                self.socketio.run(self.app, host=host, port=port, debug=debug)
                
        except Exception as e:
            logger.error(f"Erro ao executar dashboard: {e}")
        finally:
            self.stop_data_updater()


def main():
    """Função principal"""
    print("🚀 Dashboard de Produção - Sistema de Recomendações")
    print("=" * 60)
    
    # Cria dashboard
    dashboard = ProductionDashboard()
    
    # Configurações de execução
    host = os.getenv('DASHBOARD_HOST', '0.0.0.0')
    port = int(os.getenv('DASHBOARD_PORT', 8080))
    debug = os.getenv('DASHBOARD_DEBUG', 'false').lower() == 'true'
    
    print(f"\n📊 Configurações:")
    print(f"   Host: {host}")
    print(f"   Porta: {port}")
    print(f"   Debug: {'Sim' if debug else 'Não'}")
    print(f"   URL: http://{host}:{port}")
    
    print(f"\n📋 Funcionalidades:")
    print(f"   ✅ Monitoramento em tempo real")
    print(f"   ✅ Gráficos e métricas")
    print(f"   ✅ Sistema de alertas")
    print(f"   ✅ Status de backups")
    print(f"   ✅ Configurações")
    print(f"   ✅ Logs do sistema")
    
    try:
        # Executa dashboard
        dashboard.run(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao executar dashboard: {e}")
    finally:
        dashboard.stop_data_updater()
        print("✅ Dashboard finalizado")


if __name__ == "__main__":
    main()
