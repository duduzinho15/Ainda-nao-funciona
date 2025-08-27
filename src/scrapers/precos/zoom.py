"""
Scraper para coleta de preços no Zoom
Coleta preços de produtos para enriquecimento de histórico
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote_plus, urljoin

from src.utils.anti_bot import anti_bot_utils

logger = logging.getLogger(__name__)


@dataclass
class PricePoint:
    """Ponto de preço coletado"""

    source: str
    external_url: str
    price_cents: int
    seller: Optional[str]
    meta: Optional[Dict] = None


class ZoomScraper:
    """Scraper para o Zoom"""

    def __init__(self):
        self.base_url = "https://www.zoom.com.br"
        self.search_url = "https://www.zoom.com.br/search"
        self.session = None
        self.logger = logging.getLogger(f"{__name__}.ZoomScraper")

        # Configurações
        self.max_retries = 3
        self.timeout = 30
        self.delay_between_requests = 1.0

        self.logger.info("ZoomScraper inicializado")

    async def __aenter__(self):
        """Context manager entry"""
        self.session = await anti_bot_utils.get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await anti_bot_utils.close()

    async def search_product(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Busca produtos no Zoom

        Args:
            query: Termo de busca
            max_results: Máximo de resultados

        Returns:
            Lista de produtos encontrados
        """
        try:
            # Construir URL de busca
            search_url = f"{self.search_url}?q={quote_plus(query)}"

            self.logger.info(f"Buscando: {query}")

            # Fazer requisição
            response = await anti_bot_utils.make_request(
                search_url,
                max_retries=self.max_retries,
                base_delay=self.delay_between_requests,
            )

            if not response:
                self.logger.warning("Falha na busca - sem resposta")
                return []

            if response.status != 200:
                self.logger.warning(f"Falha na busca - status {response.status}")
                return []

            # Extrair produtos da resposta
            products = await self._extract_products_from_search(response, max_results)

            self.logger.info(f"Encontrados {len(products)} produtos para '{query}'")
            return products

        except Exception as e:
            self.logger.error(f"Erro na busca: {e}")
            return []

    async def get_product_price(self, product_url: str) -> Optional[PricePoint]:
        """
        Obtém preço de um produto específico

        Args:
            product_url: URL do produto

        Returns:
            Ponto de preço ou None
        """
        try:
            self.logger.info(f"Coletando preço: {product_url}")

            # Fazer requisição para a página do produto
            response = await anti_bot_utils.make_request(
                product_url,
                max_retries=self.max_retries,
                base_delay=self.delay_between_requests,
            )

            if not response or response.status != 200:
                self.logger.warning(
                    f"Falha ao acessar produto: {response.status if response else 'sem resposta'}"
                )
                return None

            # Extrair informações do produto
            price_info = await self._extract_price_from_product(response, product_url)

            if price_info:
                self.logger.info(
                    f"Preço coletado: R$ {price_info.price_cents / 100:.2f}"
                )
                return price_info
            else:
                self.logger.warning("Preço não encontrado")
                return None

        except Exception as e:
            self.logger.error(f"Erro ao coletar preço: {e}")
            return None

    async def _extract_products_from_search(
        self, response, max_results: int
    ) -> List[Dict]:
        """
        Extrai produtos da página de busca

        Args:
            response: Resposta HTTP
            max_results: Máximo de resultados

        Returns:
            Lista de produtos
        """
        try:
            html_content = await response.text()

            # Padrões para extrair produtos
            products = []

            # Tentar extrair dados JSON (mais confiável)
            json_data = self._extract_json_data(html_content)
            if json_data:
                products = self._parse_json_products(json_data, max_results)

            # Se não conseguiu JSON, tentar HTML
            if not products:
                products = self._parse_html_products(html_content, max_results)

            return products[:max_results]

        except Exception as e:
            self.logger.error(f"Erro ao extrair produtos da busca: {e}")
            return []

    async def _extract_price_from_product(
        self, response, product_url: str
    ) -> Optional[PricePoint]:
        """
        Extrai preço da página do produto

        Args:
            response: Resposta HTTP
            product_url: URL do produto

        Returns:
            Ponto de preço ou None
        """
        try:
            html_content = await response.text()

            # Tentar extrair dados JSON primeiro
            json_data = self._extract_json_data(html_content)
            if json_data:
                price_info = self._parse_json_price(json_data, product_url)
                if price_info:
                    return price_info

            # Fallback para parsing HTML
            price_info = self._parse_html_price(html_content, product_url)
            return price_info

        except Exception as e:
            self.logger.error(f"Erro ao extrair preço do produto: {e}")
            return None

    def _extract_json_data(self, html_content: str) -> Optional[Dict]:
        """Extrai dados JSON do HTML"""
        try:
            # Procurar por scripts com dados JSON
            json_patterns = [
                r"window\.__INITIAL_STATE__\s*=\s*({.*?});",
                r"window\.__PRELOADED_STATE__\s*=\s*({.*?});",
                r"<script[^>]*>.*?({.*?})</script>",
                r'data-json="([^"]*)"',
            ]

            for pattern in json_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        # Limpar o JSON
                        json_str = match.strip()
                        if json_str.startswith('"') and json_str.endswith('"'):
                            json_str = json_str[1:-1]

                        # Decodificar HTML entities
                        json_str = json_str.replace("&quot;", '"').replace("&amp;", "&")

                        data = json.loads(json_str)
                        if data:
                            return data
                    except (json.JSONDecodeError, ValueError):
                        continue

            return None

        except Exception as e:
            self.logger.debug(f"Erro ao extrair JSON: {e}")
            return None

    def _parse_json_products(self, json_data: Dict, max_results: int) -> List[Dict]:
        """Parse produtos de dados JSON"""
        products = []

        try:
            # Navegar pela estrutura JSON para encontrar produtos
            # Estrutura pode variar, tentar caminhos comuns
            product_paths = [
                ["products"],
                ["search", "products"],
                ["results", "products"],
                ["data", "products"],
                ["items"],
                ["results"],
            ]

            for path in product_paths:
                current = json_data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        current = None
                        break

                if current and isinstance(current, list):
                    for product in current[:max_results]:
                        if isinstance(product, dict):
                            parsed = self._parse_json_product(product)
                            if parsed:
                                products.append(parsed)
                    break

            return products

        except Exception as e:
            self.logger.debug(f"Erro ao parse JSON produtos: {e}")
            return []

    def _parse_json_product(self, product_data: Dict) -> Optional[Dict]:
        """Parse um produto individual de JSON"""
        try:
            # Extrair campos comuns
            title = (
                product_data.get("title")
                or product_data.get("name")
                or product_data.get("productName")
            )
            url = (
                product_data.get("url")
                or product_data.get("link")
                or product_data.get("productUrl")
            )
            price = (
                product_data.get("price")
                or product_data.get("currentPrice")
                or product_data.get("value")
            )
            sku = (
                product_data.get("sku")
                or product_data.get("id")
                or product_data.get("productId")
            )

            if not title or not url:
                return None

            # Construir URL completa se necessário
            if not url.startswith("http"):
                url = urljoin(self.base_url, url)

            return {
                "title": title,
                "url": url,
                "price": price,
                "sku": sku,
                "source": "zoom",
            }

        except Exception as e:
            self.logger.debug(f"Erro ao parse produto JSON: {e}")
            return None

    def _parse_json_price(
        self, json_data: Dict, product_url: str
    ) -> Optional[PricePoint]:
        """Parse preço de dados JSON"""
        try:
            # Procurar por informações de preço
            price_paths = [
                ["price"],
                ["currentPrice"],
                ["value"],
                ["pricing", "currentPrice"],
                ["product", "price"],
            ]

            price = None
            seller = None

            for path in price_paths:
                current = json_data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        current = None
                        break

                if current and isinstance(current, (int, float)):
                    price = int(current * 100)  # Converter para centavos
                    break

            # Procurar por vendedor
            seller_paths = [
                ["seller"],
                ["store"],
                ["merchant"],
                ["vendor"],
            ]

            for path in seller_paths:
                current = json_data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        current = None
                        break

                if current and isinstance(current, str):
                    seller = current
                    break

            if price:
                return PricePoint(
                    source="zoom",
                    external_url=product_url,
                    price_cents=price,
                    seller=seller,
                    meta={
                        "extraction_method": "json",
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            return None

        except Exception as e:
            self.logger.debug(f"Erro ao parse JSON preço: {e}")
            return None

    def _parse_html_products(self, html_content: str, max_results: int) -> List[Dict]:
        """Parse produtos de HTML (fallback)"""
        products = []

        try:
            # Padrões para extrair produtos do HTML
            # Este é um fallback quando JSON não está disponível

            # Procurar por links de produtos
            product_links = re.findall(
                r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*product[^"]*"[^>]*>',
                html_content,
                re.IGNORECASE,
            )

            # Procurar por títulos de produtos
            product_titles = re.findall(
                r'<h[1-6][^>]*class="[^"]*product[^"]*"[^>]*>([^<]+)</h[1-6]>',
                html_content,
                re.IGNORECASE,
            )

            # Combinar links e títulos
            for i, (link, title) in enumerate(zip(product_links, product_titles)):
                if i >= max_results:
                    break

                # Limpar dados
                title = re.sub(r"<[^>]+>", "", title).strip()
                if not title or len(title) < 10:
                    continue

                # Construir URL completa
                if not link.startswith("http"):
                    link = urljoin(self.base_url, link)

                products.append(
                    {
                        "title": title,
                        "url": link,
                        "price": None,
                        "sku": None,
                        "source": "zoom",
                    }
                )

            return products

        except Exception as e:
            self.logger.debug(f"Erro ao parse HTML produtos: {e}")
            return []

    def _parse_html_price(
        self, html_content: str, product_url: str
    ) -> Optional[PricePoint]:
        """Parse preço de HTML (fallback)"""
        try:
            # Padrões para extrair preço do HTML
            price_patterns = [
                r"R\$\s*([\d.,]+)",
                r"R\$\s*(\d+(?:,\d{2})?)",
                r"preço[^>]*>R\$\s*([\d.,]+)",
                r"price[^>]*>R\$\s*([\d.,]+)",
            ]

            price = None
            for pattern in price_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    try:
                        # Converter para centavos
                        price_str = matches[0].replace(",", ".")
                        price_float = float(price_str)
                        price = int(price_float * 100)
                        break
                    except (ValueError, TypeError):
                        continue

            if price:
                return PricePoint(
                    source="zoom",
                    external_url=product_url,
                    price_cents=price,
                    seller=None,
                    meta={
                        "extraction_method": "html",
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            return None

        except Exception as e:
            self.logger.debug(f"Erro ao parse HTML preço: {e}")
            return None

    async def collect_prices_for_products(
        self, products: List[Dict]
    ) -> List[PricePoint]:
        """
        Coleta preços para uma lista de produtos

        Args:
            products: Lista de produtos com URLs

        Returns:
            Lista de pontos de preço
        """
        price_points = []

        self.logger.info(f"Iniciando coleta de preços para {len(products)} produtos")

        for i, product in enumerate(products):
            try:
                # Delay entre requisições para evitar rate limiting
                if i > 0:
                    await anti_bot_utils.random_delay(0.5, 1.5)

                url = product.get("url")
                if not url:
                    continue

                price_point = await self.get_product_price(url)
                if price_point:
                    price_points.append(price_point)

                # Log de progresso
                if (i + 1) % 10 == 0:
                    self.logger.info(
                        f"Progresso: {i + 1}/{len(products)} produtos processados"
                    )

            except Exception as e:
                self.logger.error(f"Erro ao coletar preço para produto {i}: {e}")
                continue

        self.logger.info(f"Coleta concluída: {len(price_points)} preços coletados")
        return price_points


# Função de conveniência para uso direto
async def search_zoom_products(query: str, max_results: int = 10) -> List[Dict]:
    """Busca produtos no Zoom"""
    async with ZoomScraper() as scraper:
        return await scraper.search_product(query, max_results)


async def get_zoom_price(product_url: str) -> Optional[PricePoint]:
    """Obtém preço de um produto no Zoom"""
    async with ZoomScraper() as scraper:
        return await scraper.get_product_price(product_url)


async def collect_zoom_prices(products: List[Dict]) -> List[PricePoint]:
    """Coleta preços de produtos no Zoom"""
    async with ZoomScraper() as scraper:
        return await scraper.collect_prices_for_products(products)
