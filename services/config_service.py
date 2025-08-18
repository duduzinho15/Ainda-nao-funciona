# services/config_service.py
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class SystemConfig:
    # Configurações de scraping
    search_interval: int = 15  # minutos
    discount_threshold: float = 20.0  # %
    commission_threshold: float = 5.0  # %
    max_products: int = 100

    # Configurações do Telegram
    telegram_chat_id: str = ""
    telegram_bot_token: str = ""

    # Configurações de alertas
    alert_cooldown: int = 2  # horas
    auto_posting: bool = True
    dry_run: bool = True

    # Configurações de notificação
    email_notifications: bool = False
    email_smtp: str = ""
    email_user: str = ""
    email_password: str = ""

    # Campos opcionais que podem existir no JSON
    lowest_price_ever: Optional[bool] = None
    lowest_price_recent: Optional[bool] = None
    recent_days: Optional[int] = None
    priority_categories: Optional[List[str]] = None
    log_level: Optional[str] = None
    auto_clean_logs: Optional[bool] = None
    max_log_size_mb: Optional[int] = None


class ConfigService:
    def __init__(self, config_file: str = "geek_alert_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()

    def _load_config_safe(self, data: Dict[str, Any]) -> SystemConfig:
        """Carrega configurações de forma segura, ignorando chaves desconhecidas"""
        try:
            # Filtra apenas as chaves que existem no dataclass
            valid_fields = {
                field.name for field in SystemConfig.__dataclass_fields__.values()
            }
            filtered_data = {k: v for k, v in data.items() if k in valid_fields}

            # Converte tipos se necessário
            if "search_interval" in filtered_data and isinstance(
                filtered_data["search_interval"], str
            ):
                filtered_data["search_interval"] = int(filtered_data["search_interval"])
            if "discount_threshold" in filtered_data and isinstance(
                filtered_data["discount_threshold"], str
            ):
                filtered_data["discount_threshold"] = float(
                    filtered_data["discount_threshold"]
                )
            if "commission_threshold" in filtered_data and isinstance(
                filtered_data["commission_threshold"], str
            ):
                filtered_data["commission_threshold"] = float(
                    filtered_data["commission_threshold"]
                )
            if "max_products" in filtered_data and isinstance(
                filtered_data["max_products"], str
            ):
                filtered_data["max_products"] = int(filtered_data["max_products"])
            if "alert_cooldown" in filtered_data and isinstance(
                filtered_data["alert_cooldown"], str
            ):
                filtered_data["alert_cooldown"] = int(filtered_data["alert_cooldown"])
            if "recent_days" in filtered_data and isinstance(
                filtered_data["recent_days"], str
            ):
                filtered_data["recent_days"] = int(filtered_data["recent_days"])
            if "max_log_size_mb" in filtered_data and isinstance(
                filtered_data["max_log_size_mb"], str
            ):
                filtered_data["max_log_size_mb"] = int(filtered_data["max_log_size_mb"])

            return SystemConfig(**filtered_data)
        except Exception as e:
            logger.error(f"Erro ao processar configurações: {e}")
            return SystemConfig()

    def _load_config(self) -> SystemConfig:
        """Carrega configurações do arquivo ou cria padrões"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return self._load_config_safe(data)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Erro ao carregar configurações: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao carregar configurações: {e}")

        # Retorna configurações padrão se arquivo não existir ou for inválido
        return SystemConfig()

    def save_config(self, config: SystemConfig) -> bool:
        """Salva configurações no arquivo"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(asdict(config), f, indent=2, ensure_ascii=False)
            logger.info("Configurações salvas com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            return False

    def update_config(self, **kwargs) -> bool:
        """Atualiza configurações específicas"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logger.warning(f"Configuração '{key}' não existe")

        return self.save_config(self.config)

    def get_config(self) -> SystemConfig:
        """Retorna configuração atual"""
        return self.config

    def reset_to_defaults(self) -> SystemConfig:
        """Reseta para configurações padrão"""
        self.config = SystemConfig()
        return self.config

    def validate_config(self, config: SystemConfig) -> tuple[bool, str]:
        """Valida configurações"""
        errors = []

        if config.search_interval < 1:
            errors.append("Intervalo de busca deve ser maior que 0")

        if config.discount_threshold < 0 or config.discount_threshold > 100:
            errors.append("Desconto deve estar entre 0% e 100%")

        if config.commission_threshold < 0 or config.commission_threshold > 100:
            errors.append("Comissão deve estar entre 0% e 100%")

        if config.max_products < 1:
            errors.append("Máximo de produtos deve ser maior que 0")

        if config.alert_cooldown < 0:
            errors.append("Cooldown de alertas deve ser maior ou igual a 0")

        if errors:
            return False, "; ".join(errors)

        return True, "Configurações válidas"


# Instância global
config_service = ConfigService()
