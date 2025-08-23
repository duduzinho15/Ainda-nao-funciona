"""
Utilitários anti-bot para scrapers
"""

import asyncio
import logging
import random
import time
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

import aiohttp


class AntiBotUtils:
    """Utilitários para evitar detecção de bot"""
    
    # User-Agents rotativos
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edge/120.0.0.0"
    ]
    
    # Headers padrão para parecer mais humano
    DEFAULT_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def get_session(self) -> aiohttp.ClientSession:
        """Obtém ou cria uma sessão HTTP com configurações anti-bot"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=self.get_random_headers()
            )
            
        return self.session
    
    def get_random_headers(self) -> Dict[str, str]:
        """Retorna headers aleatórios para evitar detecção"""
        headers = self.DEFAULT_HEADERS.copy()
        headers["User-Agent"] = random.choice(self.USER_AGENTS)
        
        # Adicionar variações aleatórias
        if random.random() > 0.5:
            headers["Accept-Language"] = "en-US,en;q=0.9,pt;q=0.8"
        
        return headers
    
    async def make_request(
        self, 
        url: str, 
        method: str = "GET", 
        max_retries: int = 3,
        base_delay: float = 1.0,
        **kwargs
    ) -> Optional[aiohttp.ClientResponse]:
        """
        Faz uma requisição HTTP com retry e backoff exponencial
        
        Args:
            url: URL da requisição
            method: Método HTTP (GET, POST, etc.)
            max_retries: Número máximo de tentativas
            base_delay: Delay base entre tentativas (segundos)
            **kwargs: Argumentos adicionais para aiohttp
            
        Returns:
            Response da requisição ou None se falhar
        """
        session = await self.get_session()
        
        for attempt in range(max_retries):
            try:
                # Delay aleatório antes da requisição
                await self.random_delay(0.5, 2.0)
                
                # Headers aleatórios para cada tentativa
                headers = self.get_random_headers()
                if "headers" in kwargs:
                    headers.update(kwargs["headers"])
                kwargs["headers"] = headers
                
                self.logger.info(f"Tentativa {attempt + 1}/{max_retries} para {url}")
                
                async with session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        self.logger.info(f"Requisição bem-sucedida para {url}")
                        return response
                    elif response.status in [429, 503]:  # Rate limit ou serviço indisponível
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        self.logger.warning(f"Rate limit para {url}, aguardando {delay:.2f}s")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        self.logger.warning(f"Status {response.status} para {url}")
                        if attempt == max_retries - 1:
                            return response
                        
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout na tentativa {attempt + 1} para {url}")
                if attempt == max_retries - 1:
                    return None
                    
            except Exception as e:
                self.logger.error(f"Erro na tentativa {attempt + 1} para {url}: {e}")
                if attempt == max_retries - 1:
                    return None
            
            # Backoff exponencial
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                self.logger.info(f"Aguardando {delay:.2f}s antes da próxima tentativa")
                await asyncio.sleep(delay)
        
        self.logger.error(f"Falha em todas as {max_retries} tentativas para {url}")
        return None
    
    async def random_delay(self, min_delay: float = 0.5, max_delay: float = 2.0):
        """Delay aleatório para parecer mais humano"""
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    def get_domain_from_url(self, url: str) -> str:
        """Extrai o domínio de uma URL"""
        try:
            return urlparse(url).netloc
        except Exception:
            return ""
    
    def is_rate_limited(self, response: aiohttp.ClientResponse) -> bool:
        """Verifica se a resposta indica rate limiting"""
        return response.status in [429, 503, 502]
    
    def get_retry_after(self, response: aiohttp.ClientResponse) -> Optional[int]:
        """Extrai o header Retry-After da resposta"""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                pass
        return None
    
    async def close(self):
        """Fecha a sessão HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()


# Instância global para uso em outros módulos
anti_bot_utils = AntiBotUtils()
