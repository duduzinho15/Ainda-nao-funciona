"""
Classe base para todas as APIs do sistema
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp


class BaseAPI(ABC):
    """Classe base abstrata para todas as APIs"""

    def __init__(self, name: str, base_url: str, api_key: Optional[str] = None):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = None
        self.last_request = None
        self.request_count = 0
        self.error_count = 0
        self.logger = logging.getLogger(f"api.{name}")

        # Headers padrão
        self.headers = {
            "User-Agent": "GarimpeiroGeek/2.0.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    async def __aenter__(self):
        """Context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.disconnect()

    async def connect(self):
        """Estabelece conexão com a API"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout, headers=self.headers)
            self.logger.info(f"Conexão estabelecida com {self.name}")

    async def disconnect(self):
        """Fecha conexão com a API"""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info(f"Conexão fechada com {self.name}")

    @abstractmethod
    async def search_products(
        self, query: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Método abstrato para busca de produtos

        Args:
            query: Termo de busca
            limit: Número máximo de resultados

        Returns:
            Lista de produtos encontrados
        """
        pass

    @abstractmethod
    async def get_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Método abstrato para obter detalhes de um produto

        Args:
            product_id: ID do produto

        Returns:
            Detalhes do produto ou None se não encontrado
        """
        pass

    async def make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Faz uma requisição HTTP para a API

        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint da API
            **kwargs: Argumentos adicionais para a requisição

        Returns:
            Resposta da API ou None em caso de erro
        """
        if not self.session:
            await self.connect()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            self.logger.debug(f"Fazendo requisição {method} para {url}")

            async with self.session.request(method, url, **kwargs) as response:
                self.request_count += 1
                self.last_request = datetime.now()

                if response.status == 200:
                    data = await response.json()
                    self.logger.debug(
                        f"Resposta recebida de {self.name}: {len(str(data))} bytes"
                    )
                    return data
                elif response.status == 429:  # Rate limit
                    self.logger.warning(f"Rate limit atingido em {self.name}")
                    await self.handle_rate_limit(response)
                    return None
                else:
                    self.error_count += 1
                    self.logger.error(
                        f"Erro {response.status} da API {self.name}: {response.reason}"
                    )
                    return None

        except asyncio.TimeoutError:
            self.error_count += 1
            self.logger.error(f"Timeout na requisição para {self.name}")
            return None
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Erro na requisição para {self.name}: {e}")
            return None

    async def handle_rate_limit(self, response):
        """Trata rate limiting da API"""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                wait_time = int(retry_after)
                self.logger.info(f"Aguardando {wait_time}s devido ao rate limit")
                await asyncio.sleep(wait_time)
            except ValueError:
                self.logger.warning("Valor inválido para Retry-After")
        else:
            # Fallback: aguardar 1 minuto
            self.logger.info("Aguardando 60s devido ao rate limit")
            await asyncio.sleep(60)

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da API"""
        return {
            "name": self.name,
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key),
            "request_count": self.request_count,
            "error_count": self.error_count,
            "success_rate": (self.request_count - self.error_count) / self.request_count
            if self.request_count > 0
            else 0,
            "last_request": self.last_request.isoformat()
            if self.last_request
            else None,
            "is_connected": bool(self.session),
        }

    def reset_stats(self):
        """Reseta as estatísticas da API"""
        self.request_count = 0
        self.error_count = 0
        self.last_request = None
        self.logger.info(f"Estatísticas da API {self.name} resetadas")

    def update_headers(self, new_headers: Dict[str, str]):
        """Atualiza os headers da API"""
        self.headers.update(new_headers)
        if self.session:
            self.session._default_headers.update(new_headers)
        self.logger.info(f"Headers atualizados para {self.name}")

    def set_api_key(self, api_key: str):
        """Define uma nova chave de API"""
        self.api_key = api_key
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        else:
            self.headers.pop("Authorization", None)
        self.logger.info(f"Chave de API atualizada para {self.name}")
