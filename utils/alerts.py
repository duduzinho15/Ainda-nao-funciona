# utils/alerts.py
"""
Sistema de Alertas para Garimpeiro Geek
Monitora falhas e envia notificações
"""
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import config

logger = logging.getLogger("alerts")

class AlertManager:
    """Gerencia alertas e notificações do sistema"""
    
    def __init__(self):
        self.alert_history: List[Dict] = []
        self.max_history = 100
        self.alert_thresholds = {
            "scraper_failures": 3,  # Máximo de falhas consecutivas
            "post_failures": 5,     # Máximo de falhas de postagem
            "db_errors": 2,         # Máximo de erros de banco
            "memory_usage": 80,     # Percentual máximo de uso de memória
        }
    
    def add_alert(self, alert_type: str, message: str, severity: str = "WARNING", data: Optional[Dict] = None):
        """Adiciona um novo alerta"""
        alert = {
            "timestamp": datetime.now(),
            "type": alert_type,
            "message": message,
            "severity": severity,
            "data": data or {}
        }
        
        self.alert_history.append(alert)
        
        # Mantém apenas os últimos alertas
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
        
        # Log do alerta
        log_level = logging.WARNING if severity == "WARNING" else logging.ERROR
        logger.log(log_level, f"ALERTA [{severity}]: {alert_type} - {message}")
        
        # Verifica se deve enviar notificação
        if severity in ["ERROR", "CRITICAL"]:
            self._send_notification(alert)
    
    def check_scraper_health(self, scraper_name: str, success_count: int, error_count: int):
        """Verifica saúde de um scraper específico"""
        if error_count > 0 and success_count == 0:
            self.add_alert(
                "scraper_failure",
                f"Scraper {scraper_name} falhou completamente",
                "ERROR",
                {"scraper": scraper_name, "errors": error_count, "success": success_count}
            )
        elif error_count >= self.alert_thresholds["scraper_failures"]:
            self.add_alert(
                "scraper_degraded",
                f"Scraper {scraper_name} com muitas falhas",
                "WARNING",
                {"scraper": scraper_name, "errors": error_count, "success": success_count}
            )
    
    def check_post_health(self, success_count: int, error_count: int):
        """Verifica saúde do sistema de postagem"""
        if error_count >= self.alert_thresholds["post_failures"]:
            self.add_alert(
                "post_failures",
                f"Muitas falhas de postagem: {error_count} erros",
                "ERROR",
                {"success": success_count, "errors": error_count}
            )
    
    def check_database_health(self, error_message: str):
        """Verifica saúde do banco de dados"""
        self.add_alert(
            "database_error",
            f"Erro no banco de dados: {error_message}",
            "ERROR",
            {"error": error_message}
        )
    
    def check_memory_usage(self):
        """Verifica uso de memória"""
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent
            
            if memory_percent > self.alert_thresholds["memory_usage"]:
                self.add_alert(
                    "high_memory",
                    f"Uso de memória alto: {memory_percent}%",
                    "WARNING",
                    {"memory_percent": memory_percent}
                )
        except ImportError:
            pass  # psutil não disponível
    
    def get_alert_summary(self, hours: int = 24) -> Dict:
        """Retorna resumo dos alertas das últimas horas"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_alerts = [a for a in self.alert_history if a["timestamp"] > cutoff]
        
        summary = {
            "total_alerts": len(recent_alerts),
            "by_severity": {},
            "by_type": {},
            "recent_alerts": recent_alerts[-10:]  # Últimos 10 alertas
        }
        
        for alert in recent_alerts:
            # Conta por severidade
            severity = alert["severity"]
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            
            # Conta por tipo
            alert_type = alert["type"]
            summary["by_type"][alert_type] = summary["by_type"].get(alert_type, 0) + 1
        
        return summary
    
    def _send_notification(self, alert: Dict):
        """Envia notificação por email (se configurado)"""
        try:
            # Verifica se email está configurado
            smtp_server = os.getenv("SMTP_SERVER")
            smtp_port = os.getenv("SMTP_PORT")
            smtp_user = os.getenv("SMTP_USER")
            smtp_password = os.getenv("SMTP_PASSWORD")
            alert_email = os.getenv("ALERT_EMAIL")
            
            if not all([smtp_server, smtp_user, smtp_password, alert_email]):
                logger.debug("Configuração de email não encontrada, pulando notificação")
                return
            
            # Cria mensagem
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = alert_email
            msg["Subject"] = f"🚨 ALERTA Garimpeiro Geek: {alert['type']}"
            
            body = f"""
🚨 ALERTA DO SISTEMA GARIMPEIRO GEEK

Tipo: {alert['type']}
Severidade: {alert['severity']}
Mensagem: {alert['message']}
Timestamp: {alert['timestamp']}

Dados adicionais: {alert.get('data', {})}

---
Sistema de Alertas Automático
            """
            
            msg.attach(MIMEText(body, "plain"))
            
            # Envia email
            with smtplib.SMTP(smtp_server, int(smtp_port or 587)) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Notificação enviada para {alert_email}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar notificação: {e}")
    
    def clear_old_alerts(self, days: int = 7):
        """Remove alertas antigos"""
        cutoff = datetime.now() - timedelta(days=days)
        self.alert_history = [a for a in self.alert_history if a["timestamp"] > cutoff]
        logger.info(f"🧹 Alertas antigos removidos (mais de {days} dias)")

# Instância global do gerenciador de alertas
alert_manager = AlertManager()

# Funções de conveniência
def alert_scraper_failure(scraper_name: str, error: str):
    """Alerta de falha de scraper"""
    alert_manager.add_alert("scraper_failure", f"Scraper {scraper_name}: {error}", "ERROR")

def alert_post_failure(message: str, data: Optional[Dict] = None):
    """Alerta de falha de postagem"""
    alert_manager.add_alert("post_failure", message, "ERROR", data)

def alert_database_error(error: str):
    """Alerta de erro de banco"""
    alert_manager.add_alert("database_error", error, "ERROR")

def alert_high_memory(percent: float):
    """Alerta de uso alto de memória"""
    alert_manager.add_alert("high_memory", f"Memória: {percent}%", "WARNING")

def get_alerts_summary(hours: int = 24) -> Dict:
    """Retorna resumo dos alertas"""
    return alert_manager.get_alert_summary(hours)

def clear_old_alerts(days: int = 7):
    """Remove alertas antigos"""
    alert_manager.clear_old_alerts(days)
