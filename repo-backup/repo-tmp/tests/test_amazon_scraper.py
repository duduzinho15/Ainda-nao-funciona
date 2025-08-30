"""
Testes para o scraper da Amazon com normalização ASIN.

Verifica extração de informações de produtos, normalização de URLs
e criação de ofertas com validação de ASIN.
"""

from decimal import Decimal
from unittest.mock import patch

import pytest

from src.scrapers.lojas.amazon import AmazonScraper


class TestAmazonScraper:
    def setup_method(self):
        self.scraper = AmazonScraper()

    def test_scraper_initialization(self):
        assert self.scraper.name == "Amazon"
        assert self.scraper.base_url == "https://www.amazon.com.br"

    def test_can_handle_url_valid(self):
        url = "https://www.amazon.com.br/dp/B08N5WRWNW"
        assert self.scraper.can_handle_url(url) is True

    def test_can_handle_url_invalid(self):
        url = "https://www.google.com"
        assert self.scraper.can_handle_url(url) is False

    def test_get_asin_from_url(self):
        url = "https://www.amazon.com.br/dp/B08N5WRWNW"
        asin = self.scraper.get_asin_from_url(url)
        assert asin == "B08N5WRWNW"

    def test_get_asin_from_url_invalid(self):
        url = "https://www.amazon.com.br/product/invalid"
        asin = self.scraper.get_asin_from_url(url)
        assert asin is None


class TestAmazonScraperProductExtraction:
    def setup_method(self):
        self.scraper = AmazonScraper()

    @pytest.mark.asyncio
    async def test_scrape_product_success(self):
        """Testa extração bem-sucedida com ASIN da URL"""
        url = "https://www.amazon.com.br/dp/B08N5WRWNW"

        with patch.object(self.scraper, "_extract_asin_from_html", return_value=None):
            offer = await self.scraper.scrape_product(url)

        assert offer is not None
        assert offer.title == "Produto Amazon"  # Título padrão quando não há HTML
        assert offer.asin == "B08N5WRWNW"
        assert offer.price == Decimal("1.00")  # Preço padrão quando não há HTML
        assert offer.store == "Amazon"
        assert offer.is_complete is True

    @pytest.mark.asyncio
    async def test_scrape_product_no_asin(self):
        """Testa caso onde não é possível extrair ASIN"""
        url = "https://www.amazon.com.br/product/invalid"

        with patch.object(self.scraper, "_extract_asin_from_html", return_value=None):
            with patch.object(
                self.scraper, "_extract_asin_with_playwright", return_value=None
            ):
                offer = await self.scraper.scrape_product(url)

        assert offer is not None
        assert offer.title == "Produto Amazon (ASIN não encontrado)"
        assert offer.asin is None
        assert offer.is_complete is False
        assert offer.incomplete_reason is not None
        assert "ASIN não encontrado" in offer.incomplete_reason

    @pytest.mark.asyncio
    async def test_scrape_product_with_html_extraction(self):
        """Testa extração de ASIN via HTML quando URL falha"""
        url = "https://www.amazon.com.br/product/invalid"
        html_content = "<title>Produto Teste Amazon</title>"

        with patch.object(
            self.scraper, "_extract_asin_from_html", return_value="B08N5WRWNW"
        ):
            offer = await self.scraper.scrape_product(url, html_content)

        assert offer is not None
        assert offer.title == "Produto Teste Amazon"  # Título extraído do HTML
        assert offer.asin == "B08N5WRWNW"
        assert offer.is_complete is True

    @pytest.mark.asyncio
    async def test_scrape_product_exception_handling(self):
        """Testa tratamento de exceções durante scraping"""
        url = "https://www.amazon.com.br/dp/B08N5WRWNW"

        with patch.object(
            self.scraper, "_extract_asin_from_html", side_effect=Exception("Erro HTML")
        ):
            with patch.object(
                self.scraper,
                "_extract_asin_with_playwright",
                side_effect=Exception("Erro Playwright"),
            ):
                offer = await self.scraper.scrape_product(url)

        assert offer is not None
        assert offer.is_complete is True  # ASIN foi encontrado na URL
        assert offer.asin == "B08N5WRWNW"


class TestAmazonScraperHtmlExtraction:
    def setup_method(self):
        self.scraper = AmazonScraper()

    def test_extract_title_from_html(self):
        html = "<title>Produto Teste Amazon</title>"
        title = self.scraper._extract_title(html)
        assert title == "Produto Teste Amazon"

    def test_extract_title_from_product_title(self):
        html = '<span id="productTitle">Produto Teste Amazon</span>'
        title = self.scraper._extract_title(html)
        assert title == "Produto Teste Amazon"

    def test_extract_title_from_og_title(self):
        html = '<meta property="og:title" content="Produto Teste Amazon">'
        title = self.scraper._extract_title(html)
        assert title == "Produto Teste Amazon"

    def test_extract_title_not_found(self):
        html = "<div>Sem título</div>"
        title = self.scraper._extract_title(html)
        assert title is None

    def test_extract_price_from_html(self):
        html = '<span class="a-price-whole">199</span><span class="a-price-fraction">99</span>'
        price = self.scraper._extract_price(html)
        assert price == Decimal("199.99")

    def test_extract_price_with_currency(self):
        html = '<span class="a-price-whole">199</span><span class="a-price-fraction">99</span><span class="a-price-symbol">R$</span>'
        price = self.scraper._extract_price(html)
        assert price == Decimal("199.99")

    def test_extract_price_not_found(self):
        html = "<div>Sem preço</div>"
        price = self.scraper._extract_price(html)
        assert price is None

    def test_extract_original_price_from_html(self):
        html = '<span class="a-text-strike">299,99</span>'
        price = self.scraper._extract_original_price(html)
        assert price == Decimal("299.99")

    def test_extract_original_price_not_found(self):
        html = "<div>Sem preço original</div>"
        price = self.scraper._extract_original_price(html)
        assert price is None


class TestAmazonScraperIntegration:
    def setup_method(self):
        self.scraper = AmazonScraper()

    @pytest.mark.asyncio
    async def test_scrape_amazon_product_function(self):
        """Testa função de scraping completa"""
        url = "https://www.amazon.com.br/dp/B08N5WRWNW"

        with patch.object(self.scraper, "_extract_asin_from_html", return_value=None):
            offer = await self.scraper.scrape_product(url)

        assert offer is not None
        assert offer.asin == "B08N5WRWNW"
        assert offer.store == "Amazon"
        assert offer.is_complete is True

    @pytest.mark.asyncio
    async def test_offer_validation(self):
        """Testa validação do objeto Offer retornado"""
        url = "https://www.amazon.com.br/dp/B08N5WRWNW"

        with patch.object(self.scraper, "_extract_asin_from_html", return_value=None):
            offer = await self.scraper.scrape_product(url)

        assert offer is not None
        assert offer.title is not None
        assert offer.price > 0
        assert offer.store == "Amazon"
        assert offer.url.startswith("https://www.amazon.com.br/dp/")
        assert "tag=garimpeirogee-20" in offer.url

    @pytest.mark.asyncio
    async def test_asin_field_population(self):
        """Testa preenchimento correto do campo ASIN"""
        url = "https://www.amazon.com.br/dp/B08N5WRWNW"

        with patch.object(self.scraper, "_extract_asin_from_html", return_value=None):
            offer = await self.scraper.scrape_product(url)

        assert offer is not None
        assert offer.asin == "B08N5WRWNW"
        assert offer.is_complete is True
        assert offer.incomplete_reason is None  # Campo é None quando completo
