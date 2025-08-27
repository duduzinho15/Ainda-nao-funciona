"""
Scraper para KaBuM! - Loja de eletrônicos
Integração com Awin para geração de deeplinks
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote_plus, urljoin

from src.core.models import Offer
from src.utils.anti_bot import anti_bot_utils

logger = logging.getLogger(__name__)


@dataclass
class KabumProduct:
    """Produto do KaBuM!"""

    title: str
    price: float
    original_price: Optional[float]
    url: str
    image_url: Optional[str]
    available: bool
    sku: Optional[str]


class KabumScraper:
    """Scraper para o KaBuM!"""

    def __init__(self):
        self.base_url = "https://www.kabum.com.br"
        self.search_url = "https://www.kabum.com.br/busca"
        self.session = None
        self.logger = logging.getLogger(f"{__name__}.KabumScraper")

        # Configurações Awin
        self.awin_mid = "17729"  # KaBuM! MID
        self.awin_affid = "2370719"  # Seu AFFID

        # Configurações
        self.max_retries = 3
        self.timeout = 30
        self.delay_between_requests = 1.0

        self.logger.info("KabumScraper inicializado")

    async def __aenter__(self):
        """Context manager entry"""
        self.session = await anti_bot_utils.get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await anti_bot_utils.close()

    async def scrape(self, query: str = "", max_results: int = 10) -> List[Offer]:
        """
        Scrapes produtos do KaBuM!

        Args:
            query: Termo de busca (opcional)
            max_results: Máximo de resultados

        Returns:
            Lista de ofertas
        """
        try:
            if query:
                self.logger.info(f"Buscando produtos: {query}")
                products = await self._search_products(query, max_results)
            else:
                self.logger.info("Buscando produtos em destaque")
                products = await self._get_featured_products(max_results)

            # Converter para Offers
            offers = []
            for product in products:
                from decimal import Decimal

                offer = Offer(
                    title=product.title,
                    price=Decimal(str(product.price)),
                    original_price=(
                        Decimal(str(product.original_price))
                        if product.original_price
                        else None
                    ),
                    url=product.url,
                    store="KaBuM!",
                    image_url=product.image_url,
                    source="kabum_scraper",
                    store_data={
                        "sku": product.sku,
                        "platform": "kabum",
                        "available": product.available,
                    },
                )
                offers.append(offer)

            self.logger.info(f"Encontradas {len(offers)} ofertas")
            return offers

        except Exception as e:
            self.logger.error(f"Erro no scraping: {e}")
            return []

    async def _search_products(
        self, query: str, max_results: int
    ) -> List[KabumProduct]:
        """Busca produtos por termo"""
        try:
            # Construir URL de busca
            search_url = f"{self.search_url}?query={quote_plus(query)}"

            # Fazer requisição
            response = await anti_bot_utils.make_request(
                search_url,
                max_retries=self.max_retries,
                base_delay=self.delay_between_requests,
            )

            if not response or response.status != 200:
                self.logger.warning(
                    f"Falha na busca - status {response.status if response else 'sem resposta'}"
                )
                return []

            # Extrair produtos da resposta
            products = await self._extract_products_from_search(response, max_results)
            return products

        except Exception as e:
            self.logger.error(f"Erro na busca: {e}")
            return []

    async def _get_featured_products(self, max_results: int) -> List[KabumProduct]:
        """Obtém produtos em destaque"""
        try:
            # URL da página inicial
            home_url = self.base_url

            # Fazer requisição
            response = await anti_bot_utils.make_request(
                home_url,
                max_retries=self.max_retries,
                base_delay=self.delay_between_requests,
            )

            if not response or response.status != 200:
                self.logger.warning(
                    f"Falha ao acessar página inicial - status {response.status if response else 'sem resposta'}"
                )
                return []

            # Extrair produtos em destaque
            products = await self._extract_featured_products(response, max_results)
            return products

        except Exception as e:
            self.logger.error(f"Erro ao obter produtos em destaque: {e}")
            return []

    async def _extract_products_from_search(
        self, response, max_results: int
    ) -> List[KabumProduct]:
        """Extrai produtos da página de busca"""
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

    async def _extract_featured_products(
        self, response, max_results: int
    ) -> List[KabumProduct]:
        """Extrai produtos em destaque da página inicial"""
        try:
            html_content = await response.text()

            # Padrões para produtos em destaque
            products = []

            # Tentar extrair dados JSON
            json_data = self._extract_json_data(html_content)
            if json_data:
                products = self._parse_json_featured(json_data, max_results)

            # Fallback para HTML
            if not products:
                products = self._parse_html_featured(html_content, max_results)

            return products[:max_results]

        except Exception as e:
            self.logger.error(f"Erro ao extrair produtos em destaque: {e}")
            return []

    def _extract_json_data(self, html_content: str) -> Optional[dict]:
        """Extrai dados JSON do HTML"""
        try:
            # Padrões comuns para dados JSON
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

                        import json

                        data = json.loads(json_str)
                        if data:
                            return data
                    except (json.JSONDecodeError, ValueError):
                        continue

            return None

        except Exception as e:
            self.logger.debug(f"Erro ao extrair JSON: {e}")
            return None

    def _parse_json_products(
        self, json_data: dict, max_results: int
    ) -> List[KabumProduct]:
        """Parse produtos de dados JSON"""
        products = []

        try:
            # Navegar pela estrutura JSON para encontrar produtos
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

    def _parse_json_featured(
        self, json_data: dict, max_results: int
    ) -> List[KabumProduct]:
        """Parse produtos em destaque de JSON"""
        products = []

        try:
            # Caminhos para produtos em destaque
            featured_paths = [
                ["featured"],
                ["highlights"],
                ["banners"],
                ["main", "products"],
            ]

            for path in featured_paths:
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
            self.logger.debug(f"Erro ao parse JSON produtos em destaque: {e}")
            return []

    def _parse_json_product(self, product_data: dict) -> Optional[KabumProduct]:
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
            original_price = (
                product_data.get("originalPrice")
                or product_data.get("oldPrice")
                or product_data.get("listPrice")
            )
            image_url = (
                product_data.get("image")
                or product_data.get("imageUrl")
                or product_data.get("photo")
            )
            sku = (
                product_data.get("sku")
                or product_data.get("id")
                or product_data.get("productId")
            )
            available = product_data.get("available", True) or product_data.get(
                "inStock", True
            )

            if not title or not url:
                return None

            # Construir URL completa se necessário
            if not url.startswith("http"):
                url = urljoin(self.base_url, url)

            # Construir URL da imagem se necessário
            if image_url and not image_url.startswith("http"):
                image_url = urljoin(self.base_url, image_url)

            # Converter preços para float
            try:
                price_float = float(price) if price else 0.0
                original_price_float = float(original_price) if original_price else None
            except (ValueError, TypeError):
                price_float = 0.0
                original_price_float = None

            return KabumProduct(
                title=title,
                price=price_float,
                original_price=original_price_float,
                url=url,
                image_url=image_url,
                available=bool(available),
                sku=str(sku) if sku else None,
            )

        except Exception as e:
            self.logger.debug(f"Erro ao parse produto JSON: {e}")
            return None

    def _parse_html_products(
        self, html_content: str, max_results: int
    ) -> List[KabumProduct]:
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
                    KabumProduct(
                        title=title,
                        price=0.0,  # Preço não disponível no HTML
                        original_price=None,
                        url=link,
                        image_url=None,
                        available=True,
                        sku=None,
                    )
                )

            return products

        except Exception as e:
            self.logger.debug(f"Erro ao parse HTML produtos: {e}")
            return []

    def _parse_html_featured(
        self, html_content: str, max_results: int
    ) -> List[KabumProduct]:
        """Parse produtos em destaque de HTML"""
        # Similar ao _parse_html_products mas focado em seções de destaque
        return self._parse_html_products(html_content, max_results)

    def get_affiliate_url(self, product_url: str, subid: Optional[str] = None) -> str:
        """
        Gera URL de afiliado Awin para KaBuM!

        Args:
            product_url: URL do produto
            subid: Sub-ID opcional para tracking

        Returns:
            URL de afiliado Awin
        """
        try:
            # Codificar URL do produto
            encoded_url = quote_plus(product_url)

            # Construir deeplink Awin
            deeplink = (
                f"https://www.awin1.com/cread.php?awinmid={self.awin_mid}"
                f"&awinaffid={self.awin_affid}&ued={encoded_url}"
            )

            # Adicionar subid se fornecido
            if subid:
                deeplink += f"&u1={subid}"

            self.logger.info(f"URL de afiliado gerada: {deeplink}")
            return deeplink

        except Exception as e:
            self.logger.error(f"Erro ao gerar URL de afiliado: {e}")
            return product_url  # Fallback para URL original


# Instância global para uso em outros módulos
kabum_scraper = KabumScraper()

__all__ = ["KabumScraper", "kabum_scraper"]
