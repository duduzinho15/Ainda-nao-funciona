"""
Sistema de armazenamento de preferências do usuário
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

class PreferencesStorage:
    """Gerencia as preferências do usuário"""
    
    def __init__(self, config_dir: str = ".data/config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.preferences_file = self.config_dir / "user_preferences.json"
        self._preferences = {}
        self._load_preferences()
    
    def _load_default_preferences(self) -> Dict[str, Any]:
        """Carrega preferências padrão"""
        return {
            "theme": "dark",
            "language": "pt_BR",
            "last_period": "7d",
            "auto_refresh": True,
            "refresh_interval": 30,
            "max_log_lines": 1000,
            "notifications_enabled": True,
            "csv_export_format": "csv"
        }
    
    def _load_saved_preferences(self) -> Dict[str, Any]:
        """Carrega preferências salvas do arquivo"""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Erro ao carregar preferências: {e}")
        return {}
    
    def _load_preferences(self):
        """Carrega todas as preferências"""
        default_prefs = self._load_default_preferences()
        saved_prefs = self._load_saved_preferences()
        
        # Mesclar preferências salvas com padrões
        self._preferences = {**default_prefs, **saved_prefs}
        
        if not saved_prefs:
            print("📝 Arquivo de preferências não encontrado, usando padrões")
        else:
            print(f"✅ Preferências carregadas de: {self.preferences_file}")
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Obtém uma preferência específica"""
        return self._preferences.get(key, default)
    
    def set_preference(self, key: str, value: Any, auto_save: bool = True):
        """Define uma preferência"""
        self._preferences[key] = value
        print(f"⚙️ Preferência atualizada: {key} = {value}")
        
        if auto_save:
            self.save_preferences()
    
    def save_preferences(self):
        """Salva todas as preferências no arquivo"""
        try:
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self._preferences, f, indent=2, ensure_ascii=False)
            print(f"💾 Preferências salvas em: {self.preferences_file}")
        except Exception as e:
            print(f"❌ Erro ao salvar preferências: {e}")
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """Retorna todas as preferências"""
        return self._preferences.copy()
    
    def reset_preferences(self):
        """Reseta para preferências padrão"""
        self._preferences = self._load_default_preferences()
        self.save_preferences()
        print("🔄 Preferências resetadas para padrão")
    
    def has_preference(self, key: str) -> bool:
        """Verifica se uma preferência existe"""
        return key in self._preferences
