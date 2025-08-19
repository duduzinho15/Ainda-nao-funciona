"""
Storage system for user preferences and settings
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class UserPreferences:
    """Preferências do usuário"""
    theme: str = "system"  # "light", "dark", "system"
    ui_density: str = "comfortable"  # "comfortable", "compact"
    default_period: str = "7d"  # "24h", "7d", "30d", "all"
    last_selected_period: str = "7d"
    auto_refresh_interval: int = 300  # segundos
    max_log_lines: int = 500
    export_path: str = "./exports"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPreferences":
        """Cria instância a partir de dicionário"""
        return cls(**data)

class ConfigStorage:
    """Sistema de storage para configurações"""
    
    def __init__(self, config_dir: str = ".data"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self.preferences = UserPreferences()
        self._ensure_config_dir()
        self.load_preferences()
    
    def _ensure_config_dir(self):
        """Garante que o diretório de configuração existe"""
        self.config_dir.mkdir(exist_ok=True)
    
    def load_preferences(self) -> UserPreferences:
        """Carrega preferências do arquivo"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.preferences = UserPreferences.from_dict(data)
            else:
                self.save_preferences()  # Criar arquivo padrão
        except Exception as e:
            print(f"Erro ao carregar preferências: {e}")
            # Usar padrões em caso de erro
        
        return self.preferences
    
    def save_preferences(self) -> bool:
        """Salva preferências no arquivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar preferências: {e}")
            return False
    
    def update_preference(self, key: str, value: Any) -> bool:
        """Atualiza uma preferência específica"""
        if hasattr(self.preferences, key):
            setattr(self.preferences, key, value)
            return self.save_preferences()
        return False
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Obtém uma preferência específica"""
        return getattr(self.preferences, key, default)
    
    def reset_to_defaults(self) -> bool:
        """Reseta para configurações padrão"""
        self.preferences = UserPreferences()
        return self.save_preferences()

# Instância global
config_storage = ConfigStorage()
