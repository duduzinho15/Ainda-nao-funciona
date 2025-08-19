"""
Registry de scrapers e APIs para descoberta automática.
Carrega dinamicamente todos os scrapers e APIs disponíveis.
"""

import os
import importlib
import inspect
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import logging
from dataclasses import dataclass


@dataclass
class ScraperInfo:
    """Informações sobre um scraper ou API."""
    name: str
    module_name: str
    enabled: bool
    priority: int
    get_ofertas_func: Optional[Callable] = None
    description: str = ""
    env_vars: List[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = []


class ScraperRegistry:
    """Registry para gerenciar scrapers e APIs."""
    
    def __init__(self):
        self.scrapers: Dict[str, ScraperInfo] = {}
        self.logger = logging.getLogger(__name__)
        self._load_all_scrapers()
    
    def _load_all_scrapers(self):
        """Carrega todos os scrapers e APIs disponíveis."""
        try:
            # Carregar scrapers do diretório scrapers/
            scrapers_dir = Path("scrapers")
            if scrapers_dir.exists():
                self._load_from_directory(scrapers_dir, "_scraper.py", "scraper")
            
            # Carregar APIs do diretório providers/
            providers_dir = Path("providers")
            if providers_dir.exists():
                self._load_from_directory(providers_dir, "_api.py", "api")
            
            # Carregar scrapers da raiz do projeto
            self._load_root_scrapers()
            
            self.logger.info(f"✅ Registry carregado: {len(self.scrapers)} fontes encontradas")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar registry: {e}")
    
    def _load_from_directory(self, directory: Path, suffix: str, source_type: str):
        """Carrega scrapers/APIs de um diretório específico."""
        for file_path in directory.glob(f"*{suffix}"):
            try:
                module_name = f"{directory.name}.{file_path.stem}"
                self._load_module(module_name, source_type)
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao carregar {file_path}: {e}")
    
    def _load_root_scrapers(self):
        """Carrega scrapers da raiz do projeto."""
        root_files = [
            "amazon_scraper.py",
            "magalu_scraper.py", 
            "shopee_scraper.py",
            "aliexpress_scraper.py",
            "promobit_scraper.py",
            "pelando_scraper.py",
            "meupc_scraper.py",
            "buscape_scraper.py"
        ]
        
        for file_name in root_files:
            if Path(file_name).exists():
                try:
                    module_name = file_name.replace(".py", "")
                    self._load_module(module_name, "scraper")
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro ao carregar {file_name}: {e}")
    
    def _load_module(self, module_name: str, source_type: str):
        """Carrega um módulo específico."""
        try:
            # Tentar importar o módulo
            module = importlib.import_module(module_name)
            
            # Verificar se tem a função get_ofertas
            get_ofertas_func = getattr(module, 'get_ofertas', None)
            
            # Verificar se está habilitado
            enabled = self._check_if_enabled(module_name)
            
            # Determinar prioridade
            priority = getattr(module, 'priority', 100)
            
            # Obter descrição
            description = getattr(module, '__doc__', f"{source_type.title()} {module_name}")
            
            # Verificar variáveis de ambiente necessárias
            env_vars = self._get_required_env_vars(module)
            
            # Criar info do scraper
            scraper_info = ScraperInfo(
                name=module_name,
                module_name=module_name,
                enabled=enabled,
                priority=priority,
                get_ofertas_func=get_ofertas_func,
                description=description,
                env_vars=env_vars
            )
            
            # Verificar se há erros de configuração
            if enabled and not get_ofertas_func:
                scraper_info.error_message = "Função get_ofertas não encontrada"
                scraper_info.enabled = False
            
            if enabled and env_vars:
                missing_vars = [var for var in env_vars if not os.getenv(var)]
                if missing_vars:
                    scraper_info.error_message = f"Variáveis de ambiente faltando: {', '.join(missing_vars)}"
                    scraper_info.enabled = False
            
            self.scrapers[module_name] = scraper_info
            
            if enabled:
                self.logger.info(f"✅ {source_type.title()} carregado: {module_name}")
            else:
                self.logger.info(f"⚠️ {source_type.title()} desabilitado: {module_name} - {scraper_info.error_message}")
                
        except ImportError as e:
            # Criar stub para módulo não encontrado
            self.scrapers[module_name] = ScraperInfo(
                name=module_name,
                module_name=module_name,
                enabled=False,
                priority=100,
                description=f"Stub para {source_type} {module_name}",
                error_message=f"Módulo não encontrado: {e}"
            )
            self.logger.info(f"📝 Stub criado para {module_name}")
    
    def _check_if_enabled(self, module_name: str) -> bool:
        """Verifica se um scraper está habilitado."""
        # Verificar variável de ambiente global
        enabled_list = os.getenv("GG_SCRAPERS_ENABLED", "")
        if enabled_list:
            enabled_modules = [m.strip() for m in enabled_list.split(",")]
            return module_name in enabled_modules
        
        # Por padrão, habilitar se não houver restrições
        return True
    
    def _get_required_env_vars(self, module) -> List[str]:
        """Extrai variáveis de ambiente necessárias do módulo."""
        env_vars = []
        
        # Verificar docstring
        if hasattr(module, '__doc__') and module.__doc__:
            doc = module.__doc__
            if 'env:' in doc.lower() or 'environment' in doc.lower():
                # Extrair variáveis mencionadas na docstring
                lines = doc.split('\n')
                for line in lines:
                    if 'env:' in line.lower() or 'environment' in line.lower():
                        # Procurar por padrões como VAR_NAME, $VAR_NAME, etc.
                        import re
                        vars_found = re.findall(r'[A-Z_][A-Z0-9_]*', line)
                        env_vars.extend(vars_found)
        
        # Verificar atributos do módulo
        if hasattr(module, 'REQUIRED_ENV_VARS'):
            env_vars.extend(module.REQUIRED_ENV_VARS)
        
        return list(set(env_vars))  # Remover duplicatas
    
    def get_enabled_scrapers(self) -> List[ScraperInfo]:
        """Retorna lista de scrapers habilitados ordenados por prioridade."""
        enabled = [s for s in self.scrapers.values() if s.enabled]
        return sorted(enabled, key=lambda x: (x.priority, x.name))
    
    def get_scraper(self, name: str) -> Optional[ScraperInfo]:
        """Retorna informações de um scraper específico."""
        return self.scrapers.get(name)
    
    def enable_scraper(self, name: str) -> bool:
        """Habilita um scraper específico."""
        if name in self.scrapers:
            scraper = self.scrapers[name]
            if scraper.get_ofertas_func and not scraper.error_message:
                scraper.enabled = True
                self.logger.info(f"✅ Scraper habilitado: {name}")
                return True
            else:
                self.logger.warning(f"⚠️ Não é possível habilitar {name}: {scraper.error_message}")
        return False
    
    def disable_scraper(self, name: str) -> bool:
        """Desabilita um scraper específico."""
        if name in self.scrapers:
            self.scrapers[name].enabled = False
            self.logger.info(f"🔴 Scraper desabilitado: {name}")
            return True
        return False
    
    async def collect_from_all(self, periodo: str) -> List[Dict[str, Any]]:
        """
        Coleta ofertas de todos os scrapers habilitados.
        
        Args:
            periodo: Período para coleta
            
        Returns:
            Lista de ofertas coletadas
        """
        all_ofertas = []
        enabled_scrapers = self.get_enabled_scrapers()
        
        if not enabled_scrapers:
            self.logger.warning("⚠️ Nenhum scraper habilitado")
            return []
        
        self.logger.info(f"🔄 Iniciando coleta de {len(enabled_scrapers)} fontes para período: {periodo}")
        
        for scraper in enabled_scrapers:
            try:
                self.logger.info(f"📡 Coletando de: {scraper.name}")
                
                if scraper.get_ofertas_func:
                    # Verificar se é função assíncrona
                    if inspect.iscoroutinefunction(scraper.get_ofertas_func):
                        ofertas = await scraper.get_ofertas_func(periodo)
                    else:
                        ofertas = scraper.get_ofertas_func(periodo)
                    
                    if ofertas:
                        # Adicionar fonte às ofertas
                        for oferta in ofertas:
                            if isinstance(oferta, dict):
                                oferta['fonte'] = scraper.name
                            else:
                                # Se for objeto, tentar adicionar atributo
                                try:
                                    setattr(oferta, 'fonte', scraper.name)
                                except:
                                    pass
                        
                        all_ofertas.extend(ofertas)
                        self.logger.info(f"✅ {scraper.name}: {len(ofertas)} ofertas coletadas")
                    else:
                        self.logger.info(f"ℹ️ {scraper.name}: nenhuma oferta encontrada")
                        
                else:
                    self.logger.warning(f"⚠️ {scraper.name}: função get_ofertas não disponível")
                    
            except Exception as e:
                self.logger.error(f"❌ Erro ao coletar de {scraper.name}: {e}")
                # Continuar com próximo scraper (tolerância a falhas)
                continue
        
        self.logger.info(f"🎯 Coleta concluída: {len(all_ofertas)} ofertas de {len(enabled_scrapers)} fontes")
        return all_ofertas
    
    def get_registry_summary(self) -> Dict[str, Any]:
        """Retorna resumo do registry para o dashboard."""
        total = len(self.scrapers)
        enabled = len(self.get_enabled_scrapers())
        disabled = total - enabled
        
        return {
            'total_scrapers': total,
            'enabled_scrapers': enabled,
            'disabled_scrapers': disabled,
            'scrapers_list': [
                {
                    'name': s.name,
                    'enabled': s.enabled,
                    'priority': s.priority,
                    'description': s.description,
                    'error': s.error_message
                }
                for s in self.scrapers.values()
            ]
        }


# Instância global
scraper_registry = ScraperRegistry()
