"""
Sistema de persistência de preferências do dashboard.
Salva e carrega configurações do usuário em JSON.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union


class PreferencesStorage:
    """Sistema de armazenamento de preferências do usuário."""
    
    def __init__(self, config_dir: str = "./.data/config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.preferences_file = self.config_dir / "user_preferences.json"
        self._preferences = self._load_default_preferences()
        self._load_saved_preferences()
    
    def _load_default_preferences(self) -> Dict[str, Any]:
        """Carrega preferências padrão."""
        return {
            'theme': 'system',  # system, light, dark
            'density': 'comfortable',  # compact, comfortable, spacious
            'last_period': '7d',  # 24h, 7d, 30d, all
            'auto_refresh': True,
            'refresh_interval': 30,  # segundos
            'chart_height': 300,
            'logs_max_lines': 1000,
            'export_format': 'csv',
            'notifications_enabled': True,
            'last_export_path': None,
            'ui_scale': 1.0,
            'language': 'pt_BR',
            'system_enabled': True,  # NOVO: Toggle geral do sistema
            'scrapers_overrides': {},  # NOVO: Overrides individuais por fonte
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    
    def _load_saved_preferences(self):
        """Carrega preferências salvas do arquivo."""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    saved_prefs = json.load(f)
                    
                    # Mesclar com padrões (preservar novas opções)
                    for key, value in saved_prefs.items():
                        if key in self._preferences:
                            self._preferences[key] = value
                    
                    # Atualizar timestamp
                    self._preferences['updated_at'] = datetime.now().isoformat()
                    
                    print(f"✅ Preferências carregadas de: {self.preferences_file}")
            else:
                print("📝 Arquivo de preferências não encontrado, usando padrões")
                
        except Exception as e:
            print(f"⚠️ Erro ao carregar preferências: {e}, usando padrões")
    
    def save_preferences(self) -> bool:
        """
        Salva preferências atuais no arquivo.
        
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            # Atualizar timestamp
            self._preferences['updated_at'] = datetime.now().isoformat()
            
            # Salvar no arquivo
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self._preferences, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Preferências salvas em: {self.preferences_file}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar preferências: {e}")
            return False
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Obtém uma preferência específica.
        
        Args:
            key: Chave da preferência
            default: Valor padrão se não encontrado
            
        Returns:
            Valor da preferência ou default
        """
        return self._preferences.get(key, default)
    
    def set_preference(self, key: str, value: Any, auto_save: bool = True) -> bool:
        """
        Define uma preferência específica.
        
        Args:
            key: Chave da preferência
            value: Valor a ser definido
            auto_save: Se deve salvar automaticamente
            
        Returns:
            True se definiu com sucesso, False caso contrário
        """
        try:
            if key in self._preferences:
                self._preferences[key] = value
                print(f"⚙️ Preferência atualizada: {key} = {value}")
                
                if auto_save:
                    return self.save_preferences()
                return True
            else:
                print(f"⚠️ Chave de preferência desconhecida: {key}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao definir preferência {key}: {e}")
            return False
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """
        Retorna todas as preferências atuais.
        
        Returns:
            Dicionário com todas as preferências
        """
        return self._preferences.copy()
    
    def reset_preferences(self, auto_save: bool = True) -> bool:
        """
        Reseta todas as preferências para os valores padrão.
        
        Args:
            auto_save: Se deve salvar automaticamente
            
        Returns:
            True se resetou com sucesso, False caso contrário
        """
        try:
            self._preferences = self._load_default_preferences()
            print("🔄 Preferências resetadas para valores padrão")
            
            if auto_save:
                return self.save_preferences()
            return True
            
        except Exception as e:
            print(f"❌ Erro ao resetar preferências: {e}")
            return False
    
    def export_preferences(self, filepath: Optional[Union[str, Path]] = None) -> str:
        """
        Exporta preferências para arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo (opcional)
            
        Returns:
            Caminho do arquivo exportado
        """
        try:
            if not filepath:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = self.config_dir / f"preferences_backup_{timestamp}.json"
            
            export_path = Path(filepath)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self._preferences, f, indent=2, ensure_ascii=False)
            
            print(f"📤 Preferências exportadas para: {export_path}")
            return str(export_path)
            
        except Exception as e:
            print(f"❌ Erro ao exportar preferências: {e}")
            return ""
    
    def import_preferences(self, filepath: str, merge: bool = True) -> bool:
        """
        Importa preferências de arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo para importar
            merge: Se deve mesclar com preferências existentes
            
        Returns:
            True se importou com sucesso, False caso contrário
        """
        try:
            import_path = Path(filepath)
            
            if not import_path.exists():
                print(f"❌ Arquivo não encontrado: {filepath}")
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_prefs = json.load(f)
            
            if merge:
                # Mesclar com preferências existentes
                for key, value in imported_prefs.items():
                    if key in self._preferences:
                        self._preferences[key] = value
                print(f"🔄 Preferências mescladas de: {filepath}")
            else:
                # Substituir completamente
                self._preferences = imported_prefs.copy()
                print(f"📥 Preferências importadas de: {filepath}")
            
            # Atualizar timestamp
            self._preferences['updated_at'] = datetime.now().isoformat()
            
            # Salvar automaticamente
            return self.save_preferences()
            
        except Exception as e:
            print(f"❌ Erro ao importar preferências: {e}")
            return False
    
    def get_preferences_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo das preferências para o dashboard.
        
        Returns:
            Dicionário com resumo das preferências
        """
        return {
            'theme': self.get_preference('theme'),
            'density': self.get_preference('density'),
            'last_period': self.get_preference('last_period'),
            'auto_refresh': self.get_preference('auto_refresh'),
            'refresh_interval': self.get_preference('refresh_interval'),
            'chart_height': self.get_preference('chart_height'),
            'notifications_enabled': self.get_preference('notifications_enabled'),
            'ui_scale': self.get_preference('ui_scale'),
            'language': self.get_preference('language'),
            'config_file': str(self.preferences_file),
            'last_updated': self.get_preference('updated_at')
        }


# Instância global para uso no dashboard
preferences_storage = PreferencesStorage()
