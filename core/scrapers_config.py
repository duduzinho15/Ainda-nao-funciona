"""
Sistema de configuração de scrapers com persistência em JSON.
Gerencia toggles globais e individuais por fonte.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class ScrapersConfig:
    """Gerencia configuração de scrapers com persistência."""
    
    def __init__(self, config_dir: str = "./.data/config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "scrapers.json"
        self._config = self._load_default_config()
        self._load_saved_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Carrega configuração padrão."""
        return {
            "global_enabled": True,
            "sources": {
                "amazon_scraper": True,
                "magalu_scraper": True,
                "shopee_scraper": True,
                "aliexpress_scraper": True,
                "promobit_scraper": True,
                "pelando_scraper": True,
                "meupc_scraper": True,
                "buscape_scraper": True,
                "casas_bahia_scraper": True,
                "fast_shop_scraper": True,
                "ricardo_eletro_scraper": True,
                "ponto_frio_scraper": True,
                "scrapers.submarino_scraper": True,
                "scrapers.americanas_scraper": True,
                "scrapers.kabum_scraper": True,
                "scrapers.magalu_scraper": True,
                "scrapers.aliexpress_scraper": True,
                "scrapers.mercadolivre_scraper": True,
                "providers.mercadolivre_api": True,
            },
            "updated_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
    
    def _load_saved_config(self):
        """Carrega configuração salva do arquivo."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    
                    # Mesclar com padrões (preservar novas opções)
                    for key, value in saved_config.items():
                        if key in self._config:
                            if key == "sources":
                                # Mesclar fontes
                                for src_name, src_enabled in value.items():
                                    if src_name in self._config["sources"]:
                                        self._config["sources"][src_name] = src_enabled
                            else:
                                self._config[key] = value
                    
                    # Atualizar timestamp
                    self._config['updated_at'] = datetime.now().isoformat()
                    
                    print(f"✅ Configuração de scrapers carregada de: {self.config_file}")
            else:
                print("📝 Arquivo de configuração de scrapers não encontrado, usando padrões")
                
        except Exception as e:
            print(f"⚠️ Erro ao carregar configuração de scrapers: {e}, usando padrões")
    
    def save_config(self) -> bool:
        """
        Salva configuração atual no arquivo.
        
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            # Atualizar timestamp
            self._config['updated_at'] = datetime.now().isoformat()
            
            # Salvar no arquivo
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Configuração de scrapers salva em: {self.config_file}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar configuração de scrapers: {e}")
            return False
    
    def get_global_enabled(self) -> bool:
        """Obtém se o sistema global está habilitado."""
        # Verificar variáveis de ambiente para CI
        if self._is_ci_mode():
            return False
        return self._config.get("global_enabled", True)
    
    def set_global_enabled(self, enabled: bool) -> None:
        """Define se o sistema global está habilitado."""
        self._config["global_enabled"] = enabled
        self.save_config()
    
    def get_source_enabled(self, name: str) -> bool:
        """Obtém se uma fonte específica está habilitada."""
        # Verificar variáveis de ambiente para CI
        if self._is_ci_mode():
            return False
        
        # Verificar GG_SCRAPERS_ENABLED
        env_enabled = self._get_env_enabled_sources()
        if env_enabled is not None:
            return name in env_enabled
        
        return self._config.get("sources", {}).get(name, True)
    
    def set_source_enabled(self, name: str, enabled: bool) -> None:
        """Define se uma fonte específica está habilitada."""
        if "sources" not in self._config:
            self._config["sources"] = {}
        self._config["sources"][name] = enabled
        self.save_config()
    
    def get_enabled_sources(self) -> Dict[str, bool]:
        """Obtém mapa de todas as fontes e seus estados."""
        if self._is_ci_mode():
            return {}
        
        # Verificar GG_SCRAPERS_ENABLED
        env_enabled = self._get_env_enabled_sources()
        if env_enabled is not None:
            return {name: name in env_enabled for name in self._config.get("sources", {})}
        
        return self._config.get("sources", {})
    
    def get_all_sources(self) -> list:
        """Obtém lista de todas as fontes disponíveis."""
        return list(self._config.get("sources", {}).keys())
    
    def _is_ci_mode(self) -> bool:
        """Verifica se está em modo CI determinístico."""
        return bool(os.getenv("GG_SEED")) and bool(os.getenv("GG_FREEZE_TIME"))
    
    def _get_env_enabled_sources(self) -> Optional[list]:
        """Obtém lista de fontes habilitadas via variável de ambiente."""
        env_sources = os.getenv("GG_SCRAPERS_ENABLED")
        if env_sources:
            return [s.strip() for s in env_sources.split(",") if s.strip()]
        return None
    
    def is_scraping_allowed(self) -> bool:
        """Verifica se o scraping é permitido pelo ambiente."""
        return os.getenv("GG_ALLOW_SCRAPING") == "1"


# Instância global
scrapers_config = ScrapersConfig()


# Funções de conveniência
def load_config() -> Dict[str, Any]:
    """Carrega configuração completa."""
    return scrapers_config._config

def save_config(cfg: Dict[str, Any]) -> None:
    """Salva configuração completa."""
    scrapers_config._config = cfg
    scrapers_config.save_config()

def get_global_enabled() -> bool:
    """Obtém se o sistema global está habilitado."""
    return scrapers_config.get_global_enabled()

def set_global_enabled(enabled: bool) -> None:
    """Define se o sistema global está habilitado."""
    scrapers_config.set_global_enabled(enabled)

def get_source_enabled(name: str) -> bool:
    """Obtém se uma fonte específica está habilitada."""
    return scrapers_config.get_source_enabled(name)

def set_source_enabled(name: str, enabled: bool) -> None:
    """Define se uma fonte específica está habilitada."""
    scrapers_config.set_source_enabled(name, enabled)

def get_enabled_map() -> Dict[str, bool]:
    """Obtém mapa de todas as fontes e seus estados."""
    return scrapers_config.get_enabled_sources()

def get_all_sources() -> list:
    """Obtém lista de todas as fontes disponíveis."""
    return scrapers_config.get_all_sources()

def is_scraping_allowed() -> bool:
    """Verifica se o scraping é permitido pelo ambiente."""
    return scrapers_config.is_scraping_allowed()
