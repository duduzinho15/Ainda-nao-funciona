"""
Sistema de Alertas para Falhas Críticas
Gerencia notificações por email, SMS e Slack para problemas do sistema
"""
import os
import json
import logging
import smtplib
import requests
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import queue

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertLevel:
    """Níveis de alerta disponíveis"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

class AlertChannel:
    """Canais de alerta disponíveis"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"

class AlertSystem:
    """Sistema de alertas para falhas críticas"""
    
    def __init__(self, config_path: str = "config_producao.env"):
        self.config = self._load_config(config_path)
        self.alert_queue = queue.Queue()
        self.alert_history = []
        self.max_history = 1000
        
        # Configurações de canais
        self.email_config = self._get_email_config()
        self.sms_config = self._get_sms_config()
        self.slack_config = self._get_slack_config()
        self.telegram_config = self._get_telegram_config()
        
        # Configurações de rate limiting
        self.rate_limit = {
            'max_alerts_per_hour': int(self.config.get('MAX_ALERTS_PER_HOUR', 100)),
            'max_alerts_per_day': int(self.config.get('MAX_ALERTS_PER_DAY', 1000)),
            'alert_cooldown_minutes': int(self.config.get('ALERT_COOLDOWN_MINUTES', 15))
        }
        
        # Contadores de rate limiting
        self.alert_counters = {
            'hourly': {'count': 0, 'reset_time': datetime.now() + timedelta(hours=1)},
            'daily': {'count': 0, 'reset_time': datetime.now() + timedelta(days=1)}
        }
        
        # Inicia worker thread para processar alertas
        self.worker_thread = None
        self.running = False
        self.start_worker()
    
    def _load_config(self, config_path: str) -> Dict[str, str]:
        """Carrega configurações do arquivo"""
        config = {}
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
            except Exception as e:
                logger.error(f"Erro ao carregar configuração: {e}")
        
        return config
    
    def _get_email_config(self) -> Dict[str, str]:
        """Obtém configuração de email"""
        return {
            'enabled': bool(self.config.get('ALERT_EMAIL')),
            'smtp_server': self.config.get('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(self.config.get('SMTP_PORT', 587)),
            'username': self.config.get('ALERT_EMAIL_FROM', ''),
            'password': self.config.get('ALERT_EMAIL_PASSWORD', ''),
            'use_tls': self.config.get('SMTP_USE_TLS', 'true').lower() == 'true',
            'recipients': self.config.get('ALERT_EMAIL', '').split(',') if self.config.get('ALERT_EMAIL') else []
        }
    
    def _get_sms_config(self) -> Dict[str, str]:
        """Obtém configuração de SMS"""
        return {
            'enabled': bool(self.config.get('ALERT_SMS_NUMBER')),
            'provider': self.config.get('SMS_PROVIDER', 'twilio'),
            'account_sid': self.config.get('TWILIO_ACCOUNT_SID', ''),
            'auth_token': self.config.get('TWILIO_AUTH_TOKEN', ''),
            'from_number': self.config.get('TWILIO_FROM_NUMBER', ''),
            'recipients': self.config.get('ALERT_SMS_NUMBER', '').split(',') if self.config.get('ALERT_SMS_NUMBER') else []
        }
    
    def _get_slack_config(self) -> Dict[str, str]:
        """Obtém configuração do Slack"""
        return {
            'enabled': bool(self.config.get('SLACK_WEBHOOK_URL')),
            'webhook_url': self.config.get('SLACK_WEBHOOK_URL', ''),
            'channel': self.config.get('SLACK_CHANNEL', '#alerts'),
            'username': self.config.get('SLACK_USERNAME', 'Sistema de Alertas')
        }
    
    def _get_telegram_config(self) -> Dict[str, str]:
        """Obtém configuração do Telegram"""
        return {
            'enabled': bool(self.config.get('TELEGRAM_BOT_TOKEN') and self.config.get('TELEGRAM_ADMIN_ID')),
            'bot_token': self.config.get('TELEGRAM_BOT_TOKEN', ''),
            'chat_id': self.config.get('TELEGRAM_ADMIN_ID', ''),
            'parse_mode': 'HTML'
        }
    
    def send_alert(self, 
                   level: str, 
                   title: str, 
                   message: str, 
                   details: Optional[Dict[str, Any]] = None,
                   channels: Optional[List[str]] = None) -> bool:
        """
        Envia alerta através dos canais configurados
        
        Args:
            level: Nível do alerta (INFO, WARNING, ERROR, CRITICAL, EMERGENCY)
            title: Título do alerta
            message: Mensagem principal
            details: Detalhes adicionais (opcional)
            channels: Canais específicos para enviar (opcional)
            
        Returns:
            bool: True se o alerta foi enviado com sucesso
        """
        try:
            # Verifica rate limiting
            if not self._check_rate_limit():
                logger.warning("Rate limit excedido - alerta não enviado")
                return False
            
            # Cria objeto de alerta
            alert = {
                'id': self._generate_alert_id(),
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'title': title,
                'message': message,
                'details': details or {},
                'channels': channels or self._get_default_channels(level)
            }
            
            # Adiciona à fila de processamento
            self.alert_queue.put(alert)
            
            # Adiciona ao histórico
            self._add_to_history(alert)
            
            logger.info(f"🚨 Alerta {level} adicionado à fila: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar alerta: {e}")
            return False
    
    def _generate_alert_id(self) -> str:
        """Gera ID único para o alerta"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        return f"alert_{timestamp}"
    
    def _get_default_channels(self, level: str) -> List[str]:
        """Determina canais padrão baseado no nível do alerta"""
        if level in [AlertLevel.EMERGENCY, AlertLevel.CRITICAL]:
            # Para emergências e críticos, usa todos os canais
            channels = []
            if self.email_config['enabled']:
                channels.append(AlertChannel.EMAIL)
            if self.sms_config['enabled']:
                channels.append(AlertChannel.SMS)
            if self.slack_config['enabled']:
                channels.append(AlertChannel.SLACK)
            if self.telegram_config['enabled']:
                channels.append(AlertChannel.TELEGRAM)
            return channels
        elif level == AlertLevel.ERROR:
            # Para erros, usa email e Slack
            channels = []
            if self.email_config['enabled']:
                channels.append(AlertChannel.EMAIL)
            if self.slack_config['enabled']:
                channels.append(AlertChannel.SLACK)
            return channels
        else:
            # Para warnings e info, usa apenas Slack
            if self.slack_config['enabled']:
                return [AlertChannel.SLACK]
            return []
    
    def _check_rate_limit(self) -> bool:
        """Verifica se o rate limit permite enviar mais alertas"""
        now = datetime.now()
        
        # Reseta contadores se necessário
        if now >= self.alert_counters['hourly']['reset_time']:
            self.alert_counters['hourly'] = {'count': 0, 'reset_time': now + timedelta(hours=1)}
        
        if now >= self.alert_counters['daily']['reset_time']:
            self.alert_counters['daily'] = {'count': 0, 'reset_time': now + timedelta(days=1)}
        
        # Verifica limites
        if (self.alert_counters['hourly']['count'] >= self.rate_limit['max_alerts_per_hour'] or
            self.alert_counters['daily']['count'] >= self.rate_limit['max_alerts_per_day']):
            return False
        
        # Incrementa contadores
        self.alert_counters['hourly']['count'] += 1
        self.alert_counters['daily']['count'] += 1
        
        return True
    
    def _add_to_history(self, alert: Dict[str, Any]):
        """Adiciona alerta ao histórico"""
        self.alert_history.append(alert)
        
        # Mantém apenas os últimos N alertas
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
    
    def start_worker(self):
        """Inicia thread worker para processar alertas"""
        if self.worker_thread and self.worker_thread.is_alive():
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_alerts, daemon=True)
        self.worker_thread.start()
        logger.info("🚀 Worker de alertas iniciado")
    
    def stop_worker(self):
        """Para thread worker"""
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        logger.info("🛑 Worker de alertas parado")
    
    def _process_alerts(self):
        """Processa alertas da fila"""
        while self.running:
            try:
                # Pega próximo alerta da fila (timeout para permitir parada)
                try:
                    alert = self.alert_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Processa alerta
                self._send_alert_to_channels(alert)
                
                # Marca como processado
                self.alert_queue.task_done()
                
            except Exception as e:
                logger.error(f"Erro no processamento de alertas: {e}")
                time.sleep(1)
    
    def _send_alert_to_channels(self, alert: Dict[str, Any]):
        """Envia alerta para todos os canais configurados"""
        channels = alert.get('channels', [])
        
        for channel in channels:
            try:
                if channel == AlertChannel.EMAIL:
                    self._send_email_alert(alert)
                elif channel == AlertChannel.SMS:
                    self._send_sms_alert(alert)
                elif channel == AlertChannel.SLACK:
                    self._send_slack_alert(alert)
                elif channel == AlertChannel.TELEGRAM:
                    self._send_telegram_alert(alert)
                elif channel == AlertChannel.WEBHOOK:
                    self._send_webhook_alert(alert)
                    
            except Exception as e:
                logger.error(f"Erro ao enviar alerta via {channel}: {e}")
    
    def _send_email_alert(self, alert: Dict[str, Any]):
        """Envia alerta por email"""
        if not self.email_config['enabled']:
            return
        
        try:
            # Cria mensagem
            msg = MIMEMultipart()
            msg['From'] = self.email_config['username']
            msg['To'] = ', '.join(self.email_config['recipients'])
            msg['Subject'] = f"[{alert['level']}] {alert['title']}"
            
            # Corpo da mensagem
            body = self._format_email_body(alert)
            msg.attach(MIMEText(body, 'html'))
            
            # Envia email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            
            if self.email_config['use_tls']:
                server.starttls()
            
            server.login(self.email_config['username'], self.email_config['password'])
            text = msg.as_string()
            server.sendmail(self.email_config['username'], self.email_config['recipients'], text)
            server.quit()
            
            logger.info(f"📧 Alerta enviado por email para {len(self.email_config['recipients'])} destinatários")
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
    
    def _format_email_body(self, alert: Dict[str, Any]) -> str:
        """Formata corpo do email"""
        level_colors = {
            AlertLevel.INFO: '#17a2b8',
            AlertLevel.WARNING: '#ffc107',
            AlertLevel.ERROR: '#dc3545',
            AlertLevel.CRITICAL: '#fd7e14',
            AlertLevel.EMERGENCY: '#6f42c1'
        }
        
        color = level_colors.get(alert['level'], '#6c757d')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ margin: 20px 0; }}
                .details {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .footer {{ color: #6c757d; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 {alert['title']}</h2>
                <p><strong>Nível:</strong> {alert['level']}</p>
                <p><strong>Data/Hora:</strong> {alert['timestamp']}</p>
            </div>
            
            <div class="content">
                <p>{alert['message']}</p>
            </div>
        """
        
        if alert['details']:
            html += f"""
            <div class="details">
                <h3>📋 Detalhes Adicionais:</h3>
                <pre>{json.dumps(alert['details'], indent=2, ensure_ascii=False)}</pre>
            </div>
            """
        
        html += f"""
            <div class="footer">
                <p>---</p>
                <p>Sistema de Alertas - Sistema de Recomendações</p>
                <p>Este é um alerta automático, não responda a este email.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _send_sms_alert(self, alert: Dict[str, Any]):
        """Envia alerta por SMS"""
        if not self.sms_config['enabled']:
            return
        
        try:
            # Formata mensagem SMS
            message = f"[{alert['level']}] {alert['title']}\n{alert['message']}"
            
            if self.sms_config['provider'] == 'twilio':
                self._send_twilio_sms(message)
            else:
                logger.warning(f"Provedor SMS não suportado: {self.sms_config['provider']}")
                
        except Exception as e:
            logger.error(f"Erro ao enviar SMS: {e}")
    
    def _send_twilio_sms(self, message: str):
        """Envia SMS via Twilio"""
        try:
            from twilio.rest import Client
            
            client = Client(self.sms_config['account_sid'], self.sms_config['auth_token'])
            
            for recipient in self.sms_config['recipients']:
                message_obj = client.messages.create(
                    body=message,
                    from_=self.sms_config['from_number'],
                    to=recipient.strip()
                )
                
                logger.info(f"📱 SMS enviado via Twilio para {recipient}: {message_obj.sid}")
                
        except ImportError:
            logger.error("Biblioteca Twilio não instalada")
        except Exception as e:
            logger.error(f"Erro ao enviar SMS Twilio: {e}")
    
    def _send_slack_alert(self, alert: Dict[str, Any]):
        """Envia alerta para Slack"""
        if not self.slack_config['enabled']:
            return
        
        try:
            # Formata mensagem Slack
            payload = self._format_slack_message(alert)
            
            response = requests.post(
                self.slack_config['webhook_url'],
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info("📱 Alerta enviado para Slack")
            
        except Exception as e:
            logger.error(f"Erro ao enviar alerta Slack: {e}")
    
    def _format_slack_message(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Formata mensagem para Slack"""
        level_emojis = {
            AlertLevel.INFO: ':information_source:',
            AlertLevel.WARNING: ':warning:',
            AlertLevel.ERROR: ':x:',
            AlertLevel.CRITICAL: ':rotating_light:',
            AlertLevel.EMERGENCY: ':ambulance:'
        }
        
        emoji = level_emojis.get(alert['level'], ':bell:')
        
        # Cor baseada no nível
        level_colors = {
            AlertLevel.INFO: '#17a2b8',
            AlertLevel.WARNING: '#ffc107',
            AlertLevel.ERROR: '#dc3545',
            AlertLevel.CRITICAL: '#fd7e14',
            AlertLevel.EMERGENCY: '#6f42c1'
        }
        
        color = level_colors.get(alert['level'], '#6c757d')
        
        # Cria attachment
        attachment = {
            "color": color,
            "title": f"{emoji} {alert['title']}",
            "text": alert['message'],
            "fields": [
                {
                    "title": "Nível",
                    "value": alert['level'],
                    "short": True
                },
                {
                    "title": "Data/Hora",
                    "value": alert['timestamp'],
                    "short": True
                }
            ],
            "footer": "Sistema de Alertas",
            "ts": int(datetime.now().timestamp())
        }
        
        # Adiciona detalhes se disponíveis
        if alert['details']:
            details_text = json.dumps(alert['details'], indent=2, ensure_ascii=False)
            if len(details_text) > 1000:
                details_text = details_text[:1000] + "..."
            
            attachment["fields"].append({
                "title": "Detalhes",
                "value": f"```{details_text}```",
                "short": False
            })
        
        return {
            "username": self.slack_config['username'],
            "channel": self.slack_config['channel'],
            "attachments": [attachment]
        }
    
    def _send_telegram_alert(self, alert: Dict[str, Any]):
        """Envia alerta para Telegram"""
        if not self.telegram_config['enabled']:
            return
        
        try:
            # Formata mensagem Telegram
            message = self._format_telegram_message(alert)
            
            # Envia via API do Telegram
            url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
            
            payload = {
                "chat_id": self.telegram_config['chat_id'],
                "text": message,
                "parse_mode": self.telegram_config['parse_mode']
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("📱 Alerta enviado para Telegram")
            
        except Exception as e:
            logger.error(f"Erro ao enviar alerta Telegram: {e}")
    
    def _format_telegram_message(self, alert: Dict[str, Any]) -> str:
        """Formata mensagem para Telegram"""
        level_emojis = {
            AlertLevel.INFO: 'ℹ️',
            AlertLevel.WARNING: '⚠️',
            AlertLevel.ERROR: '❌',
            AlertLevel.CRITICAL: '🚨',
            AlertLevel.EMERGENCY: '🚑'
        }
        
        emoji = level_emojis.get(alert['level'], '🔔')
        
        message = f"{emoji} <b>{alert['level']}</b>\n"
        message += f"<b>{alert['title']}</b>\n\n"
        message += f"{alert['message']}\n\n"
        message += f"📅 {alert['timestamp']}"
        
        if alert['details']:
            message += f"\n\n📋 <b>Detalhes:</b>\n"
            details_text = json.dumps(alert['details'], indent=2, ensure_ascii=False)
            if len(details_text) > 1000:
                details_text = details_text[:1000] + "..."
            message += f"<code>{details_text}</code>"
        
        return message
    
    def _send_webhook_alert(self, alert: Dict[str, Any]):
        """Envia alerta para webhook personalizado"""
        webhook_url = self.config.get('WEBHOOK_URL')
        if not webhook_url:
            return
        
        try:
            payload = {
                "alert": alert,
                "timestamp": datetime.now().isoformat(),
                "source": "Sistema de Alertas"
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("🌐 Alerta enviado para webhook")
            
        except Exception as e:
            logger.error(f"Erro ao enviar webhook: {e}")
    
    def get_alert_status(self) -> Dict[str, Any]:
        """Retorna status atual do sistema de alertas"""
        return {
            'status': 'operational' if self.running else 'stopped',
            'worker_running': self.running,
            'queue_size': self.alert_queue.qsize(),
            'total_alerts_sent': len(self.alert_history),
            'rate_limit': {
                'hourly': self.alert_counters['hourly'],
                'daily': self.alert_counters['daily'],
                'limits': self.rate_limit
            },
            'channels': {
                'email': self.email_config['enabled'],
                'sms': self.sms_config['enabled'],
                'slack': self.slack_config['enabled'],
                'telegram': self.telegram_config['enabled']
            },
            'recent_alerts': self.alert_history[-10:] if self.alert_history else []
        }
    
    def test_channels(self) -> Dict[str, Dict[str, Any]]:
        """Testa todos os canais de alerta configurados"""
        results = {}
        
        # Testa email
        if self.email_config['enabled']:
            try:
                self._send_email_alert({
                    'level': AlertLevel.INFO,
                    'title': 'Teste de Canal',
                    'message': 'Este é um teste do sistema de alertas',
                    'timestamp': datetime.now().isoformat()
                })
                results['email'] = {'status': 'success', 'message': 'Email enviado com sucesso'}
            except Exception as e:
                results['email'] = {'status': 'error', 'message': str(e)}
        
        # Testa Slack
        if self.slack_config['enabled']:
            try:
                self._send_slack_alert({
                    'level': AlertLevel.INFO,
                    'title': 'Teste de Canal',
                    'message': 'Este é um teste do sistema de alertas',
                    'timestamp': datetime.now().isoformat()
                })
                results['slack'] = {'status': 'success', 'message': 'Mensagem enviada para Slack'}
            except Exception as e:
                results['slack'] = {'status': 'error', 'message': str(e)}
        
        # Testa Telegram
        if self.telegram_config['enabled']:
            try:
                self._send_telegram_alert({
                    'level': AlertLevel.INFO,
                    'title': 'Teste de Canal',
                    'message': 'Este é um teste do sistema de alertas',
                    'timestamp': datetime.now().isoformat()
                })
                results['telegram'] = {'status': 'success', 'message': 'Mensagem enviada para Telegram'}
            except Exception as e:
                results['telegram'] = {'status': 'error', 'message': str(e)}
        
        return results


def main():
    """Função principal para teste do sistema de alertas"""
    print("🚨 Sistema de Alertas para Falhas Críticas")
    print("=" * 50)
    
    alert_system = AlertSystem()
    
    # Exibe status
    print("\n📊 Status do Sistema:")
    status = alert_system.get_alert_status()
    
    print(f"   Status: {status['status']}")
    print(f"   Worker: {'✅ Rodando' if status['worker_running'] else '❌ Parado'}")
    print(f"   Fila: {status['queue_size']} alertas")
    print(f"   Total enviados: {status['total_alerts_sent']}")
    
    print(f"\n📡 Canais Configurados:")
    for channel, enabled in status['channels'].items():
        print(f"   {channel}: {'✅' if enabled else '❌'}")
    
    # Menu de teste
    while True:
        print(f"\n📋 Menu de Teste:")
        print(f"   1. 📧 Testar Email")
        print(f"   2. 📱 Testar Slack")
        print(f"   3. 🤖 Testar Telegram")
        print(f"   4. 🚨 Enviar Alerta de Teste")
        print(f"   5. 📊 Status Detalhado")
        print(f"   6. ❌ Sair")
        
        choice = input(f"\n❓ Escolha uma opção (1-6): ")
        
        if choice == '1':
            print("\n📧 Testando canal de email...")
            results = alert_system.test_channels()
            if 'email' in results:
                result = results['email']
                print(f"   Status: {result['status']}")
                print(f"   Mensagem: {result['message']}")
        
        elif choice == '2':
            print("\n📱 Testando canal do Slack...")
            results = alert_system.test_channels()
            if 'slack' in results:
                result = results['slack']
                print(f"   Status: {result['status']}")
                print(f"   Mensagem: {result['message']}")
        
        elif choice == '3':
            print("\n🤖 Testando canal do Telegram...")
            results = alert_system.test_channels()
            if 'telegram' in results:
                result = results['telegram']
                print(f"   Status: {result['status']}")
                print(f"   Mensagem: {result['message']}")
        
        elif choice == '4':
            print("\n🚨 Enviando alerta de teste...")
            success = alert_system.send_alert(
                level=AlertLevel.INFO,
                title="Teste do Sistema",
                message="Este é um alerta de teste para verificar o funcionamento do sistema.",
                details={"test": True, "timestamp": datetime.now().isoformat()}
            )
            
            if success:
                print("   ✅ Alerta enviado com sucesso!")
            else:
                print("   ❌ Falha ao enviar alerta")
        
        elif choice == '5':
            print("\n📊 Status Detalhado:")
            status = alert_system.get_alert_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
        
        elif choice == '6':
            print("\n👋 Saindo...")
            alert_system.stop_worker()
            break
        
        else:
            print("❌ Opção inválida")


if __name__ == "__main__":
    main()
