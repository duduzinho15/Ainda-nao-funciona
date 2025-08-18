"""
Dashboard Web - Sistema Garimpeiro Geek
"""
import os
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_socketio import SocketIO, emit
import psutil

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebDashboard:
    """Dashboard web para visualização de métricas"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'garimpeiro_geek_dashboard_2024'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Configurações
        self.dashboard_config = self._load_dashboard_config()
        self.refresh_interval = self.dashboard_config.get('refresh_interval', 5)
        
        # Dados em tempo real
        self.realtime_data = {
            'system': {},
            'scrapers': {},
            'telegram': {},
            'database': {},
            'alerts': []
        }
        
        # Histórico de métricas
        self.metrics_history = []
        self.max_history = 1000
        
        # Thread de atualização
        self._stop_updating = False
        self._update_thread = threading.Thread(target=self._update_metrics_loop, daemon=True)
        self._update_thread.start()
        
        # Configura rotas
        self._setup_routes()
        self._setup_socketio()
    
    def _load_dashboard_config(self) -> Dict[str, Any]:
        """Carrega configuração do dashboard"""
        config_path = Path('dashboard/dashboard_config.json')
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Falha ao carregar configuração do dashboard: {e}")
        
        # Configuração padrão
        return {
            'title': 'Sistema Garimpeiro Geek - Dashboard',
            'theme': 'dark',
            'refresh_interval': 5,
            'port': 8080,
            'host': '0.0.0.0',
            'debug': False,
            'features': {
                'real_time_updates': True,
                'charts': True,
                'alerts': True,
                'system_monitoring': True,
                'scraper_monitoring': True
            }
        }
    
    def _setup_routes(self):
        """Configura rotas do Flask"""
        
        @self.app.route('/')
        def index():
            """Página principal do dashboard"""
            return render_template('index.html', config=self.dashboard_config)
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """API para obter métricas atuais"""
            try:
                return jsonify({
                    'success': True,
                    'data': self.realtime_data,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/metrics/history')
        def get_metrics_history():
            """API para obter histórico de métricas"""
            try:
                hours = request.args.get('hours', 24, type=int)
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                filtered_history = [
                    metric for metric in self.metrics_history
                    if datetime.fromisoformat(metric['timestamp']) > cutoff_time
                ]
                
                return jsonify({
                    'success': True,
                    'data': filtered_history,
                    'count': len(filtered_history)
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/system/status')
        def get_system_status():
            """API para obter status do sistema"""
            try:
                status = self._get_system_status()
                return jsonify({
                    'success': True,
                    'data': status
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/scrapers/status')
        def get_scrapers_status():
            """API para obter status dos scrapers"""
            try:
                status = self._get_scrapers_status()
                return jsonify({
                    'success': True,
                    'data': status
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/alerts')
        def get_alerts():
            """API para obter alertas"""
            try:
                return jsonify({
                    'success': True,
                    'data': self.realtime_data['alerts']
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/config')
        def get_config():
            """API para obter configuração"""
            try:
                return jsonify({
                    'success': True,
                    'data': self.dashboard_config
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/health')
        def health_check():
            """Health check do dashboard"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'uptime': time.time(),
                'version': '1.0.0'
            })
    
    def _setup_socketio(self):
        """Configura eventos do Socket.IO"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Cliente conectado"""
            logger.info(f"Cliente conectado: {request.sid}")
            emit('connected', {'message': 'Conectado ao dashboard'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Cliente desconectado"""
            logger.info(f"Cliente desconectado: {request.sid}")
        
        @self.socketio.on('request_metrics')
        def handle_metrics_request():
            """Cliente solicitou métricas"""
            emit('metrics_update', self.realtime_data)
        
        @self.socketio.on('request_system_status')
        def handle_system_request():
            """Cliente solicitou status do sistema"""
            status = self._get_system_status()
            emit('system_status_update', status)
    
    def _update_metrics_loop(self):
        """Loop de atualização de métricas"""
        while not self._stop_updating:
            try:
                # Atualiza métricas do sistema
                self._update_system_metrics()
                
                # Atualiza métricas dos scrapers
                self._update_scrapers_metrics()
                
                # Atualiza métricas do Telegram
                self._update_telegram_metrics()
                
                # Atualiza métricas do banco
                self._update_database_metrics()
                
                # Salva no histórico
                self._save_to_history()
                
                # Emite atualização via WebSocket
                self.socketio.emit('metrics_update', self.realtime_data)
                
                # Aguarda próximo ciclo
                time.sleep(self.refresh_interval)
                
            except Exception as e:
                logger.error(f"Erro na atualização de métricas: {e}")
                time.sleep(5)
    
    def _update_system_metrics(self):
        """Atualiza métricas do sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memória
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / (1024**3)
            
            # Rede
            network = psutil.net_io_counters()
            
            # Processos
            processes = len(psutil.pids())
            
            self.realtime_data['system'] = {
                'cpu_percent': round(cpu_percent, 1),
                'memory_percent': round(memory_percent, 1),
                'memory_available_gb': round(memory_available_gb, 2),
                'disk_percent': round(disk_percent, 1),
                'disk_free_gb': round(disk_free_gb, 2),
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'processes_count': processes,
                'uptime_seconds': time.time(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Falha ao atualizar métricas do sistema: {e}")
    
    def _update_scrapers_metrics(self):
        """Atualiza métricas dos scrapers"""
        try:
            # Simula dados dos scrapers (em produção, viria do sistema real)
            scrapers = ['promobit', 'pelando', 'shopee', 'amazon', 'aliexpress']
            
            for scraper in scrapers:
                if scraper not in self.realtime_data['scrapers']:
                    self.realtime_data['scrapers'][scraper] = {
                        'status': 'idle',
                        'last_run': None,
                        'success_count': 0,
                        'error_count': 0,
                        'avg_response_time': 0.0,
                        'last_error': None
                    }
                
                # Simula atividade
                if self.realtime_data['scrapers'][scraper]['status'] == 'running':
                    # Simula conclusão
                    if random.random() < 0.3:  # 30% chance de concluir
                        self.realtime_data['scrapers'][scraper]['status'] = 'idle'
                        self.realtime_data['scrapers'][scraper]['last_run'] = datetime.now().isoformat()
                        self.realtime_data['scrapers'][scraper]['success_count'] += 1
                else:
                    # Simula início
                    if random.random() < 0.1:  # 10% chance de iniciar
                        self.realtime_data['scrapers'][scraper]['status'] = 'running'
            
        except Exception as e:
            logger.error(f"Falha ao atualizar métricas dos scrapers: {e}")
    
    def _update_telegram_metrics(self):
        """Atualiza métricas do Telegram"""
        try:
            # Simula dados do Telegram
            if 'telegram' not in self.realtime_data:
                self.realtime_data['telegram'] = {
                    'messages_sent': 0,
                    'messages_failed': 0,
                    'last_message': None,
                    'bot_status': 'online',
                    'chat_members': 0
                }
            
            # Simula envio de mensagens
            if random.random() < 0.2:  # 20% chance de enviar mensagem
                if random.random() < 0.95:  # 95% de sucesso
                    self.realtime_data['telegram']['messages_sent'] += 1
                    self.realtime_data['telegram']['last_message'] = datetime.now().isoformat()
                else:
                    self.realtime_data['telegram']['messages_failed'] += 1
            
        except Exception as e:
            logger.error(f"Falha ao atualizar métricas do Telegram: {e}")
    
    def _update_database_metrics(self):
        """Atualiza métricas do banco de dados"""
        try:
            # Simula dados do banco
            if 'database' not in self.realtime_data:
                self.realtime_data['database'] = {
                    'queries_count': 0,
                    'slow_queries': 0,
                    'errors_count': 0,
                    'connections': 1,
                    'size_mb': 0.0
                }
            
            # Simula queries
            if random.random() < 0.3:  # 30% chance de nova query
                self.realtime_data['database']['queries_count'] += 1
                
                if random.random() < 0.05:  # 5% chance de query lenta
                    self.realtime_data['database']['slow_queries'] += 1
                
                if random.random() < 0.02:  # 2% chance de erro
                    self.realtime_data['database']['errors_count'] += 1
            
        except Exception as e:
            logger.error(f"Falha ao atualizar métricas do banco: {e}")
    
    def _save_to_history(self):
        """Salva métricas no histórico"""
        try:
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'system': self.realtime_data['system'].copy(),
                'scrapers': self.realtime_data['scrapers'].copy(),
                'telegram': self.realtime_data['telegram'].copy(),
                'database': self.realtime_data['database'].copy()
            }
            
            self.metrics_history.append(history_entry)
            
            # Limita tamanho do histórico
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
                
        except Exception as e:
            logger.error(f"Falha ao salvar no histórico: {e}")
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Obtém status do sistema"""
        try:
            # Status geral
            overall_status = 'healthy'
            issues = []
            
            # Verifica CPU
            if self.realtime_data['system'].get('cpu_percent', 0) > 90:
                overall_status = 'warning'
                issues.append('CPU usage high')
            
            # Verifica memória
            if self.realtime_data['system'].get('memory_percent', 0) > 85:
                overall_status = 'warning'
                issues.append('Memory usage high')
            
            # Verifica disco
            if self.realtime_data['system'].get('disk_percent', 0) > 90:
                overall_status = 'critical'
                issues.append('Disk space low')
            
            # Verifica scrapers
            active_scrapers = sum(1 for s in self.realtime_data['scrapers'].values() 
                                if s.get('status') == 'running')
            if active_scrapers == 0:
                overall_status = 'warning'
                issues.append('No active scrapers')
            
            return {
                'overall_status': overall_status,
                'issues': issues,
                'active_scrapers': active_scrapers,
                'system_metrics': self.realtime_data['system'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Falha ao obter status do sistema: {e}")
            return {
                'overall_status': 'error',
                'issues': [str(e)],
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_scrapers_status(self) -> Dict[str, Any]:
        """Obtém status dos scrapers"""
        try:
            status_summary = {
                'total': len(self.realtime_data['scrapers']),
                'running': 0,
                'idle': 0,
                'error': 0,
                'scrapers': {}
            }
            
            for name, data in self.realtime_data['scrapers'].items():
                status = data.get('status', 'unknown')
                status_summary['scrapers'][name] = {
                    'status': status,
                    'last_run': data.get('last_run'),
                    'success_count': data.get('success_count', 0),
                    'error_count': data.get('error_count', 0),
                    'avg_response_time': data.get('avg_response_time', 0.0)
                }
                
                if status == 'running':
                    status_summary['running'] += 1
                elif status == 'idle':
                    status_summary['idle'] += 1
                elif status == 'error':
                    status_summary['error'] += 1
            
            return status_summary
            
        except Exception as e:
            logger.error(f"Falha ao obter status dos scrapers: {e}")
            return {'error': str(e)}
    
    def add_alert(self, level: str, title: str, message: str, 
                  details: Optional[Dict[str, Any]] = None):
        """Adiciona alerta ao dashboard"""
        try:
            alert = {
                'id': f"alert_{int(time.time())}",
                'level': level,
                'title': title,
                'message': message,
                'details': details or {},
                'timestamp': datetime.now().isoformat(),
                'acknowledged': False
            }
            
            self.realtime_data['alerts'].append(alert)
            
            # Limita número de alertas
            if len(self.realtime_data['alerts']) > 100:
                self.realtime_data['alerts'].pop(0)
            
            # Emite alerta via WebSocket
            self.socketio.emit('new_alert', alert)
            
            logger.info(f"Alerta adicionado: {title}")
            
        except Exception as e:
            logger.error(f"Falha ao adicionar alerta: {e}")
    
    def run(self, host: str = None, port: int = None, debug: bool = None):
        """Executa o dashboard"""
        try:
            # Usa configurações padrão se não fornecidas
            host = host or self.dashboard_config.get('host', '0.0.0.0')
            port = port or self.dashboard_config.get('port', 8080)
            debug = debug if debug is not None else self.dashboard_config.get('debug', False)
            
            logger.info(f"🚀 Iniciando dashboard em {host}:{port}")
            logger.info(f"📊 Acesse: http://{host}:{port}")
            
            # Executa o dashboard
            self.socketio.run(
                self.app,
                host=host,
                port=port,
                debug=debug,
                use_reloader=False
            )
            
        except Exception as e:
            logger.error(f"Falha ao executar dashboard: {e}")
    
    def stop(self):
        """Para o dashboard"""
        try:
            self._stop_updating = True
            if self._update_thread.is_alive():
                self._update_thread.join(timeout=5)
            
            logger.info("✅ Dashboard finalizado")
            
        except Exception as e:
            logger.error(f"Erro ao finalizar dashboard: {e}")


def create_dashboard_templates():
    """Cria templates HTML para o dashboard"""
    templates_dir = Path('dashboard/templates')
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Template principal
    index_html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ config.title }}</title>
    
    <!-- CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/chart.js@3.7.0/dist/chart.min.css" rel="stylesheet">
    
    <style>
        :root {
            --primary-color: #007bff;
            --success-color: #28a745;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
            --info-color: #17a2b8;
            --dark-color: #343a40;
            --light-color: #f8f9fa;
        }
        
        body {
            background-color: var(--light-color);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .navbar-brand {
            font-weight: bold;
            font-size: 1.5rem;
        }
        
        .card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        
        .card-header {
            background: linear-gradient(135deg, var(--primary-color), var(--info-color));
            color: white;
            border-radius: 15px 15px 0 0 !important;
            font-weight: bold;
        }
        
        .metric-card {
            text-align: center;
            padding: 20px;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.9rem;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        
        .status-healthy { background-color: var(--success-color); }
        .status-warning { background-color: var(--warning-color); }
        .status-critical { background-color: var(--danger-color); }
        .status-error { background-color: var(--danger-color); }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin: 20px 0;
        }
        
        .alert-item {
            border-left: 4px solid var(--danger-color);
            padding: 15px;
            margin: 10px 0;
            background-color: white;
            border-radius: 5px;
        }
        
        .alert-warning { border-left-color: var(--warning-color); }
        .alert-info { border-left-color: var(--info-color); }
        
        .refresh-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
        }
        
        .loading {
            display: none;
        }
        
        .loading.show {
            display: block;
        }
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class="fas fa-chart-line me-2"></i>
                {{ config.title }}
            </a>
            
            <div class="navbar-nav ms-auto">
                <span class="navbar-text">
                    <i class="fas fa-clock me-1"></i>
                    <span id="current-time"></span>
                </span>
            </div>
        </div>
    </nav>
    
    <!-- Refresh Indicator -->
    <div class="refresh-indicator">
        <div class="loading alert alert-info" id="refresh-indicator">
            <i class="fas fa-sync-alt fa-spin me-2"></i>
            Atualizando...
        </div>
    </div>
    
    <div class="container-fluid mt-4">
        <!-- Status Geral -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-heartbeat me-2"></i>
                        Status Geral do Sistema
                    </div>
                    <div class="card-body">
                        <div class="row" id="system-status">
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <i class="fas fa-server fa-2x text-primary"></i>
                                    <div class="metric-value" id="overall-status">-</div>
                                    <div class="metric-label">Status Geral</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <i class="fas fa-microchip fa-2x text-info"></i>
                                    <div class="metric-value" id="cpu-usage">-</div>
                                    <div class="metric-label">CPU</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <i class="fas fa-memory fa-2x text-warning"></i>
                                    <div class="metric-value" id="memory-usage">-</div>
                                    <div class="metric-label">Memória</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <i class="fas fa-hdd fa-2x text-success"></i>
                                    <div class="metric-value" id="disk-usage">-</div>
                                    <div class="metric-label">Disco</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Métricas dos Scrapers -->
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-spider me-2"></i>
                        Status dos Scrapers
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Scraper</th>
                                        <th>Status</th>
                                        <th>Última Execução</th>
                                        <th>Sucessos</th>
                                        <th>Erros</th>
                                        <th>Tempo Médio</th>
                                    </tr>
                                </thead>
                                <tbody id="scrapers-table">
                                    <!-- Preenchido via JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-chart-pie me-2"></i>
                        Resumo dos Scrapers
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="scrapers-chart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Gráficos de Performance -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-chart-line me-2"></i>
                        CPU e Memória (Últimas 24h)
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="performance-chart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-chart-bar me-2"></i>
                        Atividade dos Scrapers
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="activity-chart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Alertas -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Alertas do Sistema
                    </div>
                    <div class="card-body">
                        <div id="alerts-container">
                            <!-- Preenchido via JavaScript -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.0/dist/chart.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.4.1/socket.io.js"></script>
    
    <script>
        // Configuração do Socket.IO
        const socket = io();
        
        // Variáveis globais
        let currentMetrics = {};
        let charts = {};
        
        // Inicialização
        document.addEventListener('DOMContentLoaded', function() {
            initializeDashboard();
            setupSocketIO();
            startAutoRefresh();
        });
        
        function initializeDashboard() {
            // Atualiza tempo atual
            updateCurrentTime();
            setInterval(updateCurrentTime, 1000);
            
            // Carrega métricas iniciais
            loadMetrics();
            
            // Inicializa gráficos
            initializeCharts();
        }
        
        function updateCurrentTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = 
                now.toLocaleTimeString('pt-BR');
        }
        
        function setupSocketIO() {
            socket.on('connect', function() {
                console.log('Conectado ao dashboard');
                showRefreshIndicator(false);
            });
            
            socket.on('disconnect', function() {
                console.log('Desconectado do dashboard');
                showRefreshIndicator(true);
            });
            
            socket.on('metrics_update', function(data) {
                updateDashboard(data);
            });
            
            socket.on('new_alert', function(alert) {
                addAlert(alert);
            });
        }
        
        function loadMetrics() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateDashboard(data.data);
                    }
                })
                .catch(error => {
                    console.error('Erro ao carregar métricas:', error);
                });
        }
        
        function updateDashboard(data) {
            currentMetrics = data;
            
            // Atualiza status geral
            updateSystemStatus(data.system);
            
            // Atualiza tabela de scrapers
            updateScrapersTable(data.scrapers);
            
            // Atualiza gráficos
            updateCharts(data);
            
            // Atualiza alertas
            updateAlerts(data.alerts);
        }
        
        function updateSystemStatus(systemData) {
            if (systemData.cpu_percent !== undefined) {
                document.getElementById('cpu-usage').textContent = 
                    systemData.cpu_percent + '%';
            }
            
            if (systemData.memory_percent !== undefined) {
                document.getElementById('memory-usage').textContent = 
                    systemData.memory_percent + '%';
            }
            
            if (systemData.disk_percent !== undefined) {
                document.getElementById('disk-usage').textContent = 
                    systemData.disk_percent + '%';
            }
        }
        
        function updateScrapersTable(scrapersData) {
            const tbody = document.getElementById('scrapers-table');
            tbody.innerHTML = '';
            
            for (const [name, data] of Object.entries(scrapersData)) {
                const row = document.createElement('tr');
                
                const statusClass = getStatusClass(data.status);
                const statusText = getStatusText(data.status);
                
                row.innerHTML = `
                    <td><strong>${name}</strong></td>
                    <td>
                        <span class="status-indicator ${statusClass}"></span>
                        ${statusText}
                    </td>
                    <td>${data.last_run ? formatDateTime(data.last_run) : 'Nunca'}</td>
                    <td><span class="badge bg-success">${data.success_count}</span></td>
                    <td><span class="badge bg-danger">${data.error_count}</span></td>
                    <td>${data.avg_response_time.toFixed(2)}ms</td>
                `;
                
                tbody.appendChild(row);
            }
        }
        
        function getStatusClass(status) {
            switch (status) {
                case 'running': return 'status-warning';
                case 'idle': return 'status-healthy';
                case 'error': return 'status-critical';
                default: return 'status-error';
            }
        }
        
        function getStatusText(status) {
            switch (status) {
                case 'running': return 'Executando';
                case 'idle': return 'Ocioso';
                case 'error': return 'Erro';
                default: return 'Desconhecido';
            }
        }
        
        function formatDateTime(isoString) {
            const date = new Date(isoString);
            return date.toLocaleString('pt-BR');
        }
        
        function initializeCharts() {
            // Gráfico de pizza dos scrapers
            const scrapersCtx = document.getElementById('scrapers-chart').getContext('2d');
            charts.scrapers = new Chart(scrapersCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Executando', 'Ocioso', 'Erro'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: ['#ffc107', '#28a745', '#dc3545']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            
            // Gráfico de performance
            const performanceCtx = document.getElementById('performance-chart').getContext('2d');
            charts.performance = new Chart(performanceCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU %',
                        data: [],
                        borderColor: '#007bff',
                        tension: 0.4
                    }, {
                        label: 'Memória %',
                        data: [],
                        borderColor: '#28a745',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
            
            // Gráfico de atividade
            const activityCtx = document.getElementById('activity-chart').getContext('2d');
            charts.activity = new Chart(activityCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Mensagens Enviadas',
                        data: [],
                        backgroundColor: '#007bff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
        
        function updateCharts(data) {
            // Atualiza gráfico dos scrapers
            if (data.scrapers) {
                const running = Object.values(data.scrapers).filter(s => s.status === 'running').length;
                const idle = Object.values(data.scrapers).filter(s => s.status === 'idle').length;
                const error = Object.values(data.scrapers).filter(s => s.status === 'error').length;
                
                charts.scrapers.data.datasets[0].data = [running, idle, error];
                charts.scrapers.update();
            }
            
            // Atualiza gráfico de performance
            if (data.system) {
                const now = new Date().toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'});
                
                charts.performance.data.labels.push(now);
                charts.performance.data.datasets[0].data.push(data.system.cpu_percent || 0);
                charts.performance.data.datasets[1].data.push(data.system.memory_percent || 0);
                
                // Mantém apenas últimos 20 pontos
                if (charts.performance.data.labels.length > 20) {
                    charts.performance.data.labels.shift();
                    charts.performance.data.datasets[0].data.shift();
                    charts.performance.data.datasets[1].data.shift();
                }
                
                charts.performance.update();
            }
        }
        
        function updateAlerts(alerts) {
            const container = document.getElementById('alerts-container');
            
            if (!alerts || alerts.length === 0) {
                container.innerHTML = '<p class="text-muted">Nenhum alerta ativo</p>';
                return;
            }
            
            container.innerHTML = '';
            
            alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = `alert-item alert-${alert.level}`;
                
                alertDiv.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">${alert.title}</h6>
                            <p class="mb-1">${alert.message}</p>
                            <small class="text-muted">${formatDateTime(alert.timestamp)}</small>
                        </div>
                        <span class="badge bg-${getAlertBadgeClass(alert.level)}">${alert.level.toUpperCase()}</span>
                    </div>
                `;
                
                container.appendChild(alertDiv);
            });
        }
        
        function getAlertBadgeClass(level) {
            switch (level) {
                case 'critical': return 'danger';
                case 'warning': return 'warning';
                case 'info': return 'info';
                default: return 'secondary';
            }
        }
        
        function addAlert(alert) {
            // Adiciona alerta no topo da lista
            const container = document.getElementById('alerts-container');
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert-item alert-${alert.level}`;
            
            alertDiv.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">${alert.title}</h6>
                        <p class="mb-1">${alert.message}</p>
                        <small class="text-muted">${formatDateTime(alert.timestamp)}</small>
                    </div>
                    <span class="badge bg-${getAlertBadgeClass(alert.level)}">${alert.level.toUpperCase()}</span>
                </div>
            `;
            
            container.insertBefore(alertDiv, container.firstChild);
            
            // Remove alertas antigos se houver muitos
            const alerts = container.querySelectorAll('.alert-item');
            if (alerts.length > 10) {
                alerts[alerts.length - 1].remove();
            }
        }
        
        function showRefreshIndicator(show) {
            const indicator = document.getElementById('refresh-indicator');
            if (show) {
                indicator.classList.add('show');
            } else {
                indicator.classList.remove('show');
            }
        }
        
        function startAutoRefresh() {
            // Atualiza métricas a cada 30 segundos
            setInterval(() => {
                if (socket.connected) {
                    socket.emit('request_metrics');
                } else {
                    loadMetrics();
                }
            }, 30000);
        }
    </script>
</body>
</html>"""
    
    # Salva template
    with open(templates_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    logger.info("✅ Templates do dashboard criados")


def main():
    """Função principal"""
    print("🚀 Dashboard Web - Sistema Garimpeiro Geek")
    print("=" * 50)
    
    # Cria templates se não existirem
    create_dashboard_templates()
    
    # Cria e executa dashboard
    dashboard = WebDashboard()
    
    try:
        dashboard.run()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrompido pelo usuário")
    finally:
        dashboard.stop()


if __name__ == "__main__":
    import random  # Para simulação
    main()
