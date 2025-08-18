"""
Sistema de persistência de configurações do sistema Garimpeiro Geek.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from .settings import SystemConfig

logger = logging.getLogger(__name__)


class ConfigStorage:
    """Gerencia o carregamento e salvamento de configurações."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Inicializa o storage de configurações.

        Args:
            config_path: Caminho para o arquivo de configuração.
                         Padrão: ./.data/config.json
        """
        if config_path is None:
            self.config_path = Path(".data/config.json")
        else:
            self.config_path = Path(config_path)

        # Garantir que o diretório existe
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self._config: Optional[SystemConfig] = None

    def load(self) -> SystemConfig:
        """
        Carrega a configuração do arquivo.

        Returns:
            Configuração carregada ou padrão se arquivo não existir.
        """
        try:
            if not self.config_path.exists():
                logger.info("Arquivo de configuração não encontrado, usando padrões")
                return SystemConfig.get_defaults()

            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            config = SystemConfig.from_dict(data)
            logger.info(f"Configuração carregada de {self.config_path}")
            return config

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            logger.info("Usando configuração padrão")
            return SystemConfig.get_defaults()

        except Exception as e:
            logger.error(f"Erro inesperado ao carregar configuração: {e}")
            return SystemConfig.get_defaults()

    def save(self, config: SystemConfig) -> bool:
        """
        Salva a configuração no arquivo.

        Args:
            config: Configuração a ser salva.

        Returns:
            True se salvou com sucesso, False caso contrário.
        """
        try:
            # Criar backup se arquivo existir
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix(".json.backup")
                self.config_path.rename(backup_path)
                logger.info(f"Backup criado: {backup_path}")

            # Salvar nova configuração
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)

            self._config = config
            logger.info(f"Configuração salva em {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")

            # Tentar restaurar backup se existir
            backup_path = self.config_path.with_suffix(".json.backup")
            if backup_path.exists():
                try:
                    backup_path.rename(self.config_path)
                    logger.info("Backup restaurado após erro de salvamento")
                except Exception as restore_error:
                    logger.error(f"Erro ao restaurar backup: {restore_error}")

            return False

    def get_config(self) -> SystemConfig:
        """
        Retorna a configuração atual (carrega se necessário).

        Returns:
            Configuração atual do sistema.
        """
        if self._config is None:
            self._config = self.load()
        return self._config

    def update_config(self, **updates: Dict[str, Any]) -> bool:
        """
        Atualiza configurações específicas.

        Args:
            **updates: Dicionário com atualizações a aplicar.

        Returns:
            True se atualizou com sucesso, False caso contrário.
        """
        try:
            config = self.get_config()

            # Aplicar atualizações
            for section, values in updates.items():
                if hasattr(config, section):
                    section_obj = getattr(config, section)
                    for key, value in values.items():
                        if hasattr(section_obj, key):
                            setattr(section_obj, key, value)
                        else:
                            logger.warning(f"Chave desconhecida: {section}.{key}")
                else:
                    logger.warning(f"Seção desconhecida: {section}")

            # Salvar configuração atualizada
            return self.save(config)

        except Exception as e:
            logger.error(f"Erro ao atualizar configuração: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """
        Reseta a configuração para os valores padrão.

        Returns:
            True se resetou com sucesso, False caso contrário.
        """
        try:
            default_config = SystemConfig.get_defaults()
            return self.save(default_config)
        except Exception as e:
            logger.error(f"Erro ao resetar configuração: {e}")
            return False

    def get_config_path(self) -> Path:
        """Retorna o caminho do arquivo de configuração."""
        return self.config_path

    def backup_exists(self) -> bool:
        """Verifica se existe um backup da configuração."""
        backup_path = self.config_path.with_suffix(".json.backup")
        return backup_path.exists()

    def restore_backup(self) -> bool:
        """
        Restaura a configuração do backup.

        Returns:
            True se restaurou com sucesso, False caso contrário.
        """
        try:
            backup_path = self.config_path.with_suffix(".json.backup")
            if not backup_path.exists():
                logger.warning("Backup não encontrado para restauração")
                return False

            # Restaurar backup
            backup_path.rename(self.config_path)
            self._config = None  # Forçar recarregamento

            logger.info("Configuração restaurada do backup")
            return True

        except Exception as e:
            logger.error(f"Erro ao restaurar backup: {e}")
            return False
