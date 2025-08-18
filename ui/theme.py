# ui/theme.py
import json
import os
from pathlib import Path
from typing import Literal, Optional
from dataclasses import dataclass, asdict

ThemeMode = Literal["light", "dark"]

@dataclass
class DashboardPreferences:
    theme: ThemeMode = "light"
    last_tab: int = 0
    period_filter: str = "24h"
    auto_refresh: bool = True
    refresh_interval: int = 30

class ThemeManager:
    def __init__(self, config_dir: Path = Path("config")):
        self.config_dir = config_dir
        self.config_dir.mkdir(exist_ok=True)
        self.prefs_file = config_dir / "dashboard_prefs.json"
        
    def load_prefs(self) -> DashboardPreferences:
        """Carrega preferências do usuário ou cria padrões"""
        try:
            if self.prefs_file.exists():
                with open(self.prefs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return DashboardPreferences(**data)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Erro ao carregar preferências: {e}")
        
        # Retorna padrões se arquivo não existir ou for inválido
        return DashboardPreferences()
    
    def save_prefs(self, prefs: DashboardPreferences) -> bool:
        """Salva preferências do usuário"""
        try:
            with open(self.prefs_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(prefs), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar preferências: {e}")
            return False
    
    def update_theme(self, prefs: DashboardPreferences, new_theme: ThemeMode) -> bool:
        """Atualiza tema e salva preferências"""
        prefs.theme = new_theme
        return self.save_prefs(prefs)
    
    def update_last_tab(self, prefs: DashboardPreferences, tab_index: int) -> bool:
        """Atualiza última aba aberta e salva preferências"""
        prefs.last_tab = tab_index
        return self.save_prefs(prefs)

# Instância global
theme_manager = ThemeManager()

