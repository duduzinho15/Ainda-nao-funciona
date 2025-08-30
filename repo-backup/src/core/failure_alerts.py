"""
Sistema de Alertas de Falha
Implementa alertas automáticos para problemas do sistema em produção
"""

import json
import logging
import smtplib
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Níveis de severidade dos alertas"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Status dos alertas"""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class AlertRule:
    """Regra de alerta configurável"""

    name: str
    description: str
    severity: AlertSeverity
    condition: str  # Expressão de condição
    threshold: float
    time_window: int  # Segundos
    cooldown: int  # Segundos entre alertas
    enabled: bool = True
    notification_channels: List[str] = field(default_factory=lambda: ["log", "email"])
    auto_resolve: bool = True
    auto_resolve_threshold: float = 0.0


@dataclass
class Alert:
    """Alerta individual"""

    id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    occurrences: int = 1


class NotificationChannel:
    """Canal de notificação base"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)

    async def send_notification(self, alert: Alert) -> bool:
        """Envia notificação (implementar nas subclasses)"""
        raise NotImplementedError

    def is_enabled(self) -> bool:
        """Verifica se o canal está habilitado"""
        return self.enabled


class LogNotificationChannel(NotificationChannel):
    """Canal de notificação via logs"""

    async def send_notification(self, alert: Alert) -> bool:
        """Envia notificação via logs"""
        try:
            log_level = {
                AlertSeverity.LOW: logging.INFO,
                AlertSeverity.MEDIUM: logging.WARNING,
                AlertSeverity.HIGH: logging.ERROR,
                AlertSeverity.CRITICAL: logging.CRITICAL,
            }.get(alert.severity, logging.WARNING)

            logger.log(
                log_level,
                f"ALERTA [{alert.severity.value.upper()}] {alert.rule_name}: {alert.message}",
            )
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar notificação via log: {e}")
            return False


class EmailNotificationChannel(NotificationChannel):
    """Canal de notificação via email"""

    async def send_notification(self, alert: Alert) -> bool:
        """Envia notificação via email"""
        try:
            if not self.config.get("smtp_server"):
                logger.warning(
                    "Servidor SMTP não configurado para notificações por email"
                )
                return False

            # Configurar mensagem
            msg = MIMEMultipart()
            msg["From"] = self.config.get("from_email", "alerts@garimpeirogeek.com")
            msg["To"] = self.config.get("to_email", "admin@garimpeirogeek.com")
            msg["Subject"] = (
                f"[{alert.severity.value.upper()}] Alerta: {alert.rule_name}"
            )

            # Corpo da mensagem
            body = f"""
            ALERTA DETECTADO

            Regra: {alert.rule_name}
            Severidade: {alert.severity.value.upper()}
            Mensagem: {alert.message}
            Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            ID: {alert.id}

            Detalhes:
            - Status: {alert.status.value}
            - Ocorrências: {alert.occurrences}
            - Metadados: {json.dumps(alert.metadata, indent=2)}

            Acesse o dashboard para mais informações.
            """

            msg.attach(MIMEText(body, "plain"))

            # Enviar email
            with smtplib.SMTP(
                self.config["smtp_server"], self.config.get("smtp_port", 587)
            ) as server:
                if self.config.get("use_tls", True):
                    server.starttls()

                if self.config.get("username") and self.config.get("password"):
                    server.login(self.config["username"], self.config["password"])

                server.send_message(msg)

            logger.info(f"Notificação por email enviada para {msg['To']}")
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar notificação por email: {e}")
            return False


class TelegramNotificationChannel(NotificationChannel):
    """Canal de notificação via Telegram"""

    async def send_notification(self, alert: Alert) -> bool:
        """Envia notificação via Telegram"""
        try:
            # Implementar integração com Telegram Bot API
            # Por enquanto, apenas log
            logger.info(f"Notificação Telegram (simulada): {alert.message}")
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar notificação via Telegram: {e}")
            return False


class FailureAlertSystem:
    """Sistema de alertas de falha"""

    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.last_alert_times: Dict[str, datetime] = {}

        # Configurar regras padrão
        self._setup_default_rules()

        # Configurar canais de notificação padrão
        self._setup_default_channels()

    def _setup_default_rules(self):
        """Configura regras de alerta padrão"""
        default_rules = [
            AlertRule(
                name="high_error_rate",
                description="Taxa de erro alta",
                severity=AlertSeverity.HIGH,
                condition="error_rate > threshold",
                threshold=0.1,  # 10%
                time_window=300,  # 5 minutos
                cooldown=600,  # 10 minutos
                notification_channels=["log", "email"],
            ),
            AlertRule(
                name="low_success_rate",
                description="Taxa de sucesso baixa",
                severity=AlertSeverity.MEDIUM,
                condition="success_rate < threshold",
                threshold=0.8,  # 80%
                time_window=300,  # 5 minutos
                cooldown=600,  # 10 minutos
                notification_channels=["log", "email"],
            ),
            AlertRule(
                name="high_response_time",
                description="Tempo de resposta alto",
                severity=AlertSeverity.MEDIUM,
                condition="response_time > threshold",
                threshold=1000,  # 1 segundo
                time_window=300,  # 5 minutos
                cooldown=600,  # 10 minutos
                notification_channels=["log", "email"],
            ),
            AlertRule(
                name="cache_failure",
                description="Falha no cache",
                severity=AlertSeverity.HIGH,
                condition="cache_errors > threshold",
                threshold=5,  # 5 erros
                time_window=60,  # 1 minuto
                cooldown=300,  # 5 minutos
                notification_channels=["log", "email", "telegram"],
            ),
            AlertRule(
                name="platform_unavailable",
                description="Plataforma indisponível",
                severity=AlertSeverity.CRITICAL,
                condition="unavailable_time > threshold",
                threshold=300,  # 5 minutos
                time_window=60,  # 1 minuto
                cooldown=1800,  # 30 minutos
                notification_channels=["log", "email", "telegram"],
            ),
        ]

        for rule in default_rules:
            self.add_alert_rule(rule)

    def _setup_default_channels(self):
        """Configura canais de notificação padrão"""
        # Canal de log (sempre habilitado)
        self.add_notification_channel(
            "log", LogNotificationChannel("log", {"enabled": True})
        )

        # Canal de email (configurável)
        email_config = {
            "enabled": False,  # Habilitar via configuração
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": True,
            "username": None,
            "password": None,
            "from_email": "alerts@garimpeirogeek.com",
            "to_email": "admin@garimpeirogeek.com",
        }
        self.add_notification_channel(
            "email", EmailNotificationChannel("email", email_config)
        )

        # Canal de Telegram (configurável)
        telegram_config = {
            "enabled": False,  # Habilitar via configuração
            "bot_token": None,
            "chat_id": None,
        }
        self.add_notification_channel(
            "telegram", TelegramNotificationChannel("telegram", telegram_config)
        )

    def add_alert_rule(self, rule: AlertRule) -> None:
        """Adiciona uma regra de alerta"""
        self.alert_rules[rule.name] = rule
        logger.info(f"Regra de alerta adicionada: {rule.name}")

    def remove_alert_rule(self, rule_name: str) -> None:
        """Remove uma regra de alerta"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"Regra de alerta removida: {rule_name}")

    def add_notification_channel(self, name: str, channel: NotificationChannel) -> None:
        """Adiciona um canal de notificação"""
        self.notification_channels[name] = channel
        logger.info(f"Canal de notificação adicionado: {name}")

    def remove_notification_channel(self, name: str) -> None:
        """Remove um canal de notificação"""
        if name in self.notification_channels:
            del self.notification_channels[name]
            logger.info(f"Canal de notificação removido: {name}")

    async def check_alerts(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Verifica se há alertas para disparar baseado nas métricas"""
        new_alerts = []

        try:
            for rule_name, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue

                # Verificar cooldown
                if rule_name in self.last_alert_times:
                    time_since_last = datetime.now() - self.last_alert_times[rule_name]
                    if time_since_last.total_seconds() < rule.cooldown:
                        continue

                # Verificar condição
                if self._evaluate_condition(rule, metrics):
                    # Criar alerta
                    alert = Alert(
                        id=f"{rule_name}_{int(datetime.now().timestamp())}",
                        rule_name=rule_name,
                        severity=rule.severity,
                        message=f"Condição '{rule.condition}' foi atendida",
                        timestamp=datetime.now(),
                        metadata={
                            "threshold": rule.threshold,
                            "current_value": metrics.get(rule_name, "N/A"),
                        },
                    )

                    # Verificar se já existe alerta ativo
                    if rule_name in self.active_alerts:
                        # Incrementar ocorrências
                        existing_alert = self.active_alerts[rule_name]
                        existing_alert.occurrences += 1
                        existing_alert.timestamp = datetime.now()
                        existing_alert.metadata.update(alert.metadata)
                    else:
                        # Novo alerta
                        self.active_alerts[rule_name] = alert
                        new_alerts.append(alert)

                    # Atualizar timestamp do último alerta
                    self.last_alert_times[rule_name] = datetime.now()

                    # Enviar notificações
                    await self._send_notifications(alert, rule)

            return new_alerts

        except Exception as e:
            logger.error(f"Erro ao verificar alertas: {e}")
            return []

    def _evaluate_condition(self, rule: AlertRule, metrics: Dict[str, Any]) -> bool:
        """Avalia se uma condição de alerta foi atendida"""
        try:
            # Implementar parser de condições mais sofisticado
            # Por enquanto, implementação simples
            if rule.condition == "error_rate > threshold":
                error_rate = metrics.get("error_rate", 0.0)
                return error_rate > rule.threshold

            elif rule.condition == "success_rate < threshold":
                success_rate = metrics.get("success_rate", 1.0)
                return success_rate < rule.threshold

            elif rule.condition == "response_time > threshold":
                response_time = metrics.get("response_time", 0.0)
                return response_time > rule.threshold

            elif rule.condition == "cache_errors > threshold":
                cache_errors = metrics.get("cache_errors", 0)
                return cache_errors > rule.threshold

            elif rule.condition == "unavailable_time > threshold":
                unavailable_time = metrics.get("unavailable_time", 0)
                return unavailable_time > rule.threshold

            return False

        except Exception as e:
            logger.error(f"Erro ao avaliar condição '{rule.condition}': {e}")
            return False

    async def _send_notifications(self, alert: Alert, rule: AlertRule) -> None:
        """Envia notificações para um alerta"""
        try:
            for channel_name in rule.notification_channels:
                if channel_name in self.notification_channels:
                    channel = self.notification_channels[channel_name]
                    if channel.is_enabled():
                        success = await channel.send_notification(alert)
                        if success:
                            logger.debug(f"Notificação enviada via {channel_name}")
                        else:
                            logger.warning(
                                f"Falha ao enviar notificação via {channel_name}"
                            )
                    else:
                        logger.debug(f"Canal {channel_name} desabilitado")
                else:
                    logger.warning(
                        f"Canal de notificação não encontrado: {channel_name}"
                    )

        except Exception as e:
            logger.error(f"Erro ao enviar notificações: {e}")

    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Reconhece um alerta"""
        try:
            for alert in self.active_alerts.values():
                if alert.id == alert_id:
                    alert.status = AlertStatus.ACKNOWLEDGED
                    alert.acknowledged_by = user
                    alert.acknowledged_at = datetime.now()
                    logger.info(f"Alerta {alert_id} reconhecido por {user}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Erro ao reconhecer alerta: {e}")
            return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve um alerta"""
        try:
            for rule_name, alert in self.active_alerts.items():
                if alert.id == alert_id:
                    alert.status = AlertStatus.RESOLVED
                    alert.resolved_at = datetime.now()

                    # Mover para histórico
                    self.alert_history.append(alert)
                    del self.active_alerts[rule_name]

                    logger.info(f"Alerta {alert_id} resolvido")
                    return True

            return False

        except Exception as e:
            logger.error(f"Erro ao resolver alerta: {e}")
            return False

    def get_active_alerts(self) -> List[Alert]:
        """Retorna alertas ativos"""
        return list(self.active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Retorna histórico de alertas"""
        return self.alert_history[-limit:] if self.alert_history else []

    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Retorna alertas por severidade"""
        return [
            alert for alert in self.active_alerts.values() if alert.severity == severity
        ]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos alertas"""
        active_count = len(self.active_alerts)
        history_count = len(self.alert_history)

        severity_counts = {}
        for alert in self.active_alerts.values():
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "active_alerts": active_count,
            "total_history": history_count,
            "severity_distribution": severity_counts,
            "last_check": datetime.now().isoformat(),
        }

    def cleanup_old_alerts(self, max_history: int = 1000) -> None:
        """Remove alertas antigos do histórico"""
        if len(self.alert_history) > max_history:
            self.alert_history = self.alert_history[-max_history:]
            logger.debug(f"Histórico de alertas limpo: {max_history} mantidos")

    def export_alerts(self, format: str = "json") -> str:
        """Exporta alertas em diferentes formatos"""
        try:
            data = {
                "active_alerts": [
                    {
                        "id": alert.id,
                        "rule_name": alert.rule_name,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "status": alert.status.value,
                        "occurrences": alert.occurrences,
                        "metadata": alert.metadata,
                    }
                    for alert in self.active_alerts.values()
                ],
                "alert_history": [
                    {
                        "id": alert.id,
                        "rule_name": alert.rule_name,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "status": alert.status.value,
                        "resolved_at": (
                            alert.resolved_at.isoformat() if alert.resolved_at else None
                        ),
                    }
                    for alert in self.alert_history[-100:]  # Últimos 100
                ],
                "export_timestamp": datetime.now().isoformat(),
            }

            if format.lower() == "json":
                return json.dumps(data, indent=2, default=str)
            else:
                raise ValueError(f"Formato não suportado: {format}")

        except Exception as e:
            logger.error(f"Erro ao exportar alertas: {e}")
            return "{}"


# Instância global do sistema de alertas
failure_alert_system = FailureAlertSystem()
