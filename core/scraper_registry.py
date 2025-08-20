"""
Registry de scrapers e APIs para descoberta automática.
Carrega dinamicamente todos os scrapers e APIs disponíveis.
"""

import os
import importlib
import inspect
import asyncio
import random
import time
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import logging
from dataclasses import dataclass
import aiohttp
from urllib.parse import urlparse


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
    rate_limit: Optional[float] = None  # requests per second
    retry_count: int = 3
    retry_delay: float = 0.5

    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = []


class RateLimiter:
    """Rate limiter por domínio."""
    
    def __init__(self):
        self._semaphores: Dict[str, asyncio.Semaphore] = {}
        self._last_request: Dict[str, float] = {}
        self._min_interval: Dict[str, float] = {}
    
    def get_semaphore(self, domain: str, max_concurrent: int = 3) -> asyncio.Semaphore:
        """Retorna semáforo para um domínio específico."""
        if domain not in self._semaphores:
            self._semaphores[domain] = asyncio.Semaphore(max_concurrent)
        return self._semaphores[domain]
    
    def set_rate_limit(self, domain: str, requests_per_second: float):
        """Define rate limit para um domínio."""
        if requests_per_second > 0:
            self._min_interval[domain] = 1.0 / requests_per_second
    
    async def wait_if_needed(self, domain: str):
        """Aguarda se necessário para respeitar rate limit."""
        if domain in self._min_interval:
            last = self._last_request.get(domain, 0)
            now = time.time()
            elapsed = now - last
            min_interval = self._min_interval[domain]
            
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                await asyncio.sleep(wait_time)
            
            self._last_request[domain] = time.time()


class RetryHandler:
    """Handler para retries com backoff exponencial."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 0.5):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs):
        """Executa função com retry e backoff exponencial."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    raise last_exception
                
                # Backoff exponencial com jitter
                delay = self.base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                await asyncio.sleep(delay)
        
        raise last_exception


class ProxyManager:
    """Gerenciador de proxy opcional."""
    
    def __init__(self):
        self.proxy_url = os.getenv("PROXY_URL")
        self.proxy_user = os.getenv("PROXY_USER")
        self.proxy_pass = os.getenv("PROXY_PASS")
    
    def get_proxy_config(self) -> Optional[Dict[str, str]]:
        """Retorna configuração de proxy se disponível."""
        if not self.proxy_url:
            return None
        
        config = {"http": self.proxy_url, "https": self.proxy_url}
        
        if self.proxy_user and self.proxy_pass:
            # Adicionar autenticação ao proxy
            auth_url = self.proxy_url.replace("://", f"://{self.proxy_user}:{self.proxy_pass}@")
            config = {"http": auth_url, "https": auth_url}
        
        return config
    
    def get_session_kwargs(self) -> Dict[str, Any]:
        """Retorna kwargs para aiohttp.ClientSession."""
        kwargs = {}
        
        if self.proxy_url:
            kwargs["proxy"] = self.proxy_url
            if self.proxy_user and self.proxy_pass:
                kwargs["proxy_auth"] = aiohttp.BasicAuth(self.proxy_user, self.proxy_pass)
        
        return kwargs


class UserAgentRotator:
    """Rotador de User-Agent para evitar bloqueios."""
    
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
        ]
        self._current_index = 0
    
    def get_next(self) -> str:
        """Retorna próximo User-Agent da lista."""
        ua = self.user_agents[self._current_index]
        self._current_index = (self._current_index + 1) % len(self.user_agents)
        return ua
    
    def get_random(self) -> str:
        """Retorna User-Agent aleatório."""
        return random.choice(self.user_agents)


class ScraperRegistry:
    """Registry para gerenciar scrapers e APIs."""
    
    def __init__(self):
        self.scrapers: Dict[str, ScraperInfo] = {}
        self.rate_limiter = RateLimiter()
        self.retry_handler = RetryHandler()
        self.proxy_manager = ProxyManager()
        self.ua_rotator = UserAgentRotator()
        self.logger = logging.getLogger(__name__)
        
        # Verificar se estamos em modo CI
        self.ci_mode = bool(os.getenv("GG_SEED") and os.getenv("GG_FREEZE_TIME"))
        self.allow_scraping = os.getenv("GG_ALLOW_SCRAPING") == "1"
        
        if self.ci_mode:
            self.logger.info("🔒 Modo CI detectado - sem chamadas de rede")
        elif not self.allow_scraping:
            self.logger.info("⚠️ Scraping desabilitado - use GG_ALLOW_SCRAPING=1 para habilitar")
        
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
            
            # Configurações de rate limiting e retry
            rate_limit = getattr(module, 'rate_limit', None)
            retry_count = getattr(module, 'retry_count', 3)
            retry_delay = getattr(module, 'retry_delay', 0.5)
            
            # Criar info do scraper
            scraper_info = ScraperInfo(
                name=module_name,
                module_name=module_name,
                enabled=enabled,
                priority=priority,
                get_ofertas_func=get_ofertas_func,
                description=description,
                env_vars=env_vars,
                rate_limit=rate_limit,
                retry_count=retry_count,
                retry_delay=retry_delay
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
            
            # Configurar rate limiter se especificado
            if rate_limit:
                domain = self._get_domain_from_module(module)
                if domain:
                    self.rate_limiter.set_rate_limit(domain, rate_limit)
            
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
    
    def _get_domain_from_module(self, module) -> Optional[str]:
        """Extrai domínio base de um módulo para rate limiting."""
        # Tentar extrair de constantes ou configurações
        for attr_name in ['BASE_URL', 'DOMAIN', 'HOST']:
            if hasattr(module, attr_name):
                url = getattr(module, attr_name)
                if url:
                    parsed = urlparse(url)
                    return parsed.netloc
        
        return None
    
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
                    # Verificar se estamos em modo CI ou se scraping não é permitido
                    if self.ci_mode:
                        self.logger.info(f"🔒 Modo CI - pulando {scraper.name}")
                        continue
                    
                    if not self.allow_scraping:
                        self.logger.info(f"⚠️ Scraping desabilitado - pulando {scraper.name}")
                        continue
                    
                    # Aplicar rate limiting se necessário
                    domain = self._get_domain_from_module(importlib.import_module(scraper.module_name))
                    if domain:
                        await self.rate_limiter.wait_if_needed(domain)
                    
                    # Executar com retry
                    ofertas = await self.retry_handler.execute_with_retry(
                        scraper.get_ofertas_func, periodo
                    )
                    
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
            'ci_mode': self.ci_mode,
            'allow_scraping': self.allow_scraping,
            'scrapers_list': [
                {
                    'name': s.name,
                    'enabled': s.enabled,
                    'priority': s.priority,
                    'description': s.description,
                    'error': s.error_message,
                    'rate_limit': s.rate_limit
                }
                for s in self.scrapers.values()
            ]
        }


# Instância global
scraper_registry = ScraperRegistry()

# ===== SISTEMA DE CONTROLE DE ESTADO EFETIVO =====

_ENABLED_OVERRIDE: Dict[str, bool] = {}   # sobrescritas persistidas

def _is_ci_mode() -> bool:
    """Verifica se estamos em modo CI."""
    return bool(os.getenv("GG_SEED")) and bool(os.getenv("GG_FREEZE_TIME"))

def scraping_allowed() -> bool:
    """Verifica se scraping é permitido (não CI + GG_ALLOW_SCRAPING=1)."""
    return (os.getenv("GG_ALLOW_SCRAPING", "0") == "1") and not _is_ci_mode()

def _env_enabled_set() -> set[str] | None:
    """Obtém conjunto de fontes habilitadas via variável de ambiente."""
    raw = os.getenv("GG_SCRAPERS_ENABLED")
    if not raw:
        return None
    return {s.strip() for s in raw.split(",") if s.strip()}

def init_overrides_from_storage(storage) -> None:
    """Inicializa overrides a partir do storage."""
    global _ENABLED_OVERRIDE
    try:
        _ENABLED_OVERRIDE = storage.get_enabled_sources()
    except Exception:
        _ENABLED_OVERRIDE = {}

def set_enabled(name: str, enabled: bool, storage=None) -> None:
    """Define se uma fonte está habilitada."""
    global _ENABLED_OVERRIDE
    _ENABLED_OVERRIDE[name] = bool(enabled)
    if storage:
        storage.set_source_enabled(name, bool(enabled))

def set_all_enabled(names: list[str], enabled: bool, storage=None) -> None:
    """Define múltiplas fontes de uma vez."""
    global _ENABLED_OVERRIDE
    for n in names:
        _ENABLED_OVERRIDE[n] = bool(enabled)
    if storage:
        storage.set_sources_bulk(names, bool(enabled))

def _effective_enabled(name: str, default_enabled: bool) -> bool:
    """Calcula se uma fonte está efetivamente habilitada."""
    # 1) default do próprio scraper
    enabled = bool(default_enabled)

    # 2) filtro por ambiente GG_SCRAPERS_ENABLED (se definido)
    envset = _env_enabled_set()
    if envset is not None:
        enabled = enabled and (name in envset)

    # 3) override persistido
    if name in _ENABLED_OVERRIDE:
        enabled = bool(_ENABLED_OVERRIDE[name])

    # 4) compliance/CI gating final
    if not scraping_allowed():
        return False
    return enabled

def list_sources() -> List[Dict[str, Any]]:
    """Retorna metadados para UI."""
    items: List[Dict[str, Any]] = []
    
    # Obter scrapers do registry
    scrapers = scraper_registry.scrapers.values()
    
    for src in sorted(scrapers, key=lambda s: (s.priority, s.name)):
        default = bool(src.enabled)  # default do scraper
        items.append({
            "name": src.name,
            "priority": src.priority,
            "enabled_default": default,
            "enabled_effective": _effective_enabled(src.name, default),
            "description": src.description,
            "rate_limit": src.rate_limit,
        })
    return items

def get_sources_for_run():
    """Retorna fontes efetivamente habilitadas para execução."""
    allowed = []
    scrapers = scraper_registry.scrapers.values()
    
    for src in sorted(scrapers, key=lambda s: (s.priority, s.name)):
        if _effective_enabled(src.name, src.enabled):
            allowed.append(src)
    return allowed

