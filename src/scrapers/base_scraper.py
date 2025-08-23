"""
Classe base para todos os scrapers do sistema
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List


class BaseScraper(ABC):
    """Classe base abstrata para todos os scrapers"""

    def __init__(self, name: str, base_url: str, enabled: bool = True):
        self.name = name
        self.base_url = base_url
        self.enabled = enabled
        self.last_run = None
        self.success_count = 0
        self.error_count = 0
        self.logger = logging.getLogger(f"scraper.{name}")

    @abstractmethod
    async def scrape(
        self, query: str = "", max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Método abstrato para implementar a lógica de scraping

        Args:
            query: Termo de busca (opcional)
            max_results: Número máximo de resultados

        Returns:
            Lista de ofertas encontradas
        """
        pass

    @abstractmethod
    def parse_offer(self, raw_data: Any) -> Dict[str, Any]:
        """
        Método abstrato para parsear dados brutos em oferta estruturada

        Args:
            raw_data: Dados brutos da fonte

        Returns:
            Dicionário com dados da oferta
        """
        pass

    async def run(self, query: str = "", max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Executa o scraper com tratamento de erros

        Args:
            query: Termo de busca
            max_results: Número máximo de resultados

        Returns:
            Lista de ofertas ou lista vazia em caso de erro
        """
        if not self.enabled:
            self.logger.info(f"Scraper {self.name} está desabilitado")
            return []

        try:
            self.logger.info(f"Iniciando scraping em {self.name}")
            start_time = datetime.now()

            offers = await self.scrape(query, max_results)

            self.success_count += 1
            self.last_run = datetime.now()
            duration = (self.last_run - start_time).total_seconds()

            self.logger.info(
                f"Scraping concluído em {self.name}: {len(offers)} ofertas em {duration:.2f}s"
            )
            return offers

        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Erro no scraper {self.name}: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do scraper"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_count / (self.success_count + self.error_count)
            if (self.success_count + self.error_count) > 0
            else 0,
        }

    def enable(self):
        """Habilita o scraper"""
        self.enabled = True
        self.logger.info(f"Scraper {self.name} habilitado")

    def disable(self):
        """Desabilita o scraper"""
        self.enabled = False
        self.logger.info(f"Scraper {self.name} desabilitado")

    def reset_stats(self):
        """Reseta as estatísticas do scraper"""
        self.success_count = 0
        self.error_count = 0
        self.last_run = None
        self.logger.info(f"Estatísticas do scraper {self.name} resetadas")

    def validate_offer(self, offer: Dict[str, Any]) -> bool:
        """
        Valida se uma oferta tem todos os campos obrigatórios

        Args:
            offer: Dicionário com dados da oferta

        Returns:
            True se a oferta é válida, False caso contrário
        """
        required_fields = ["title", "price", "url", "store"]

        for field in required_fields:
            if field not in offer or not offer[field]:
                self.logger.warning(f"Campo obrigatório '{field}' ausente na oferta")
                return False

        # Validar preço
        try:
            price = float(offer["price"])
            if price <= 0:
                self.logger.warning(f"Preço inválido: {offer['price']}")
                return False
        except (ValueError, TypeError):
            self.logger.warning(f"Preço não é um número válido: {offer['price']}")
            return False

        # Validar URL
        if not offer["url"].startswith(("http://", "https://")):
            self.logger.warning(f"URL inválida: {offer['url']}")
            return False

        return True
