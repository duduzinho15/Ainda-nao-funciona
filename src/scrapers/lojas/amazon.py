"""
Scraper da Amazon com pipeline ASIN-first.

Implementa estratégia de extração de ASIN em ordem de prioridade:
1. URL direta (sem baixar página)
2. HTML leve (regex simples)
3. Playwright como fallback (quando necessário)

Extrai informações de produtos da Amazon, incluindo ASIN,
e converte URLs para formato canônico de afiliado.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from src.affiliate.amazon import extract_asin_from_url
from src.core.models import Offer
from src.core.performance_logger import (
    log_amazon_asin_extraction,
    log_amazon_asin_missing,
)
from src.utils.asin_cache import cache_asin, get_cached_asin
from src.utils.url_utils import is_amazon_url

logger = logging.getLogger(__name__)


class AmazonScraper:
    """Scraper para produtos da Amazon com normalização ASIN."""

    def __init__(self):
        self.name = "Amazon"
        self.base_url = "https://www.amazon.com.br"

    async def scrape_product(
        self, url: str, html_content: str = None
    ) -> Optional[Offer]:
        """
        Extrai informações do produto da Amazon usando pipeline ASIN-first.

        Estratégia de extração:
        1. URL direta (sem baixar página)
        2. HTML leve (regex simples)
        3. Playwright como fallback (quando necessário)

        Args:
            url: URL do produto da Amazon
            html_content: Conteúdo HTML da página (opcional)

        Returns:
            Objeto Offer com informações do produto ou None se falhar
        """
        try:
            # Validar se é URL da Amazon
            if not is_amazon_url(url):
                logger.warning(f"URL não é da Amazon: {url}")
                return None

            # Verificar cache primeiro
            cached_result = get_cached_asin(url)
            asin: Optional[str] = None
            strategy_used: str = "unknown"

            if cached_result:
                logger.info(f"ASIN encontrado em cache: {cached_result['asin']}")
                asin = cached_result["asin"]
                strategy_used = cached_result["strategy_used"]
            else:
                # Estratégia 1: Tentar extrair ASIN direto da URL
                asin = extract_asin_from_url(url)
                strategy_used = "url"

            # Estratégia 2: Se não encontrou na URL, tentar do HTML
            if not asin and html_content:
                asin = self._extract_asin_from_html(html_content)
                strategy_used = "html"

            # Estratégia 3: Se ainda não encontrou, usar Playwright como fallback
            if not asin:
                asin = await self._extract_asin_with_playwright(url)
                strategy_used = "playwright"

            if not asin:
                logger.warning(f"ASIN não encontrado para URL: {url}")
                # Log do evento para métricas
                strategies_tried = ["url", "html"]
                if not cached_result:
                    strategies_tried.append("playwright")
                log_amazon_asin_missing(url, strategies_tried)
                # Marcar como incompleta para não publicar
                return self._create_incomplete_offer(url, "ASIN não encontrado")

            # Log da estratégia utilizada para métricas
            if not cached_result:
                log_amazon_asin_extraction(strategy_used, asin, url)
                cache_asin(
                    url,
                    asin,
                    strategy_used,
                    metadata={"url": url, "scraper": "amazon", "success": True},
                )
                logger.debug(
                    f"ASIN {asin} armazenado em cache (estratégia: {strategy_used})"
                )

            # Canonizar URL com ASIN encontrado
            canonical_url = self._build_canonical_url(asin, url)

            # Extrair informações básicas do produto
            product_info = (
                self._extract_product_info(html_content) if html_content else {}
            )

            # Criar oferta com ASIN
            offer = Offer(
                title=product_info.get("title", "Produto Amazon"),
                price=product_info.get(
                    "price", Decimal("1.00")
                ),  # Preço mínimo para validação
                original_price=product_info.get("original_price"),
                url=canonical_url,  # URL canonizada com tag de afiliado
                store="Amazon",
                asin=asin,  # Campo ASIN preenchido
                affiliate_url=canonical_url,
                source="amazon_scraper",
            )

            logger.info(
                f"Produto Amazon extraído via {strategy_used}: ASIN={asin}, URL={canonical_url}"
            )
            return offer

        except Exception as e:
            logger.error(f"Erro ao fazer scraping do produto Amazon {url}: {e}")
            return None

    def _create_incomplete_offer(self, url: str, reason: str) -> Offer:
        """
        Cria uma oferta incompleta para produtos sem ASIN.

        Args:
            url: URL original do produto
            reason: Motivo da incompletude

        Returns:
            Objeto Offer marcado como incompleto
        """
        logger.warning(f"Oferta Amazon incompleta: {reason} - {url}")

        return Offer(
            title="Produto Amazon (ASIN não encontrado)",
            price=Decimal("1.00"),  # Preço mínimo para validação
            original_price=None,
            url=url,
            store="Amazon",
            asin=None,  # ASIN não encontrado
            affiliate_url=None,  # Sem URL de afiliado
            source="amazon_scraper",
            # Marcar como incompleta para não publicar
            is_complete=False,
            incomplete_reason=reason,
        )

    def _extract_product_info(self, html_content: str) -> Dict[str, Any]:
        """
        Extrai informações básicas do produto do HTML.

        Args:
            html_content: Conteúdo HTML da página

        Returns:
            Dicionário com informações do produto
        """
        info = {}

        try:
            # Extrair título do produto
            title_match = self._extract_title(html_content)
            if title_match:
                info["title"] = title_match

            # Extrair preço atual
            price_match = self._extract_price(html_content)
            if price_match:
                info["price"] = price_match

            # Extrair preço original (se disponível)
            original_price_match = self._extract_original_price(html_content)
            if original_price_match:
                info["original_price"] = original_price_match

        except Exception as e:
            logger.warning(f"Erro ao extrair informações do HTML: {e}")

        return info

    def _extract_asin_from_html(self, html_content: str) -> Optional[str]:
        """
        Extrai ASIN do HTML usando regex simples (estratégia leve).

        Args:
            html_content: Conteúdo HTML da página

        Returns:
            ASIN extraído ou None
        """
        try:
            # Buscar em múltiplos locais do HTML
            patterns = [
                r'<input[^>]*id="ASIN"[^>]*value="([A-Z0-9]{10})"',
                r'<input[^>]*name="ASIN"[^>]*value="([A-Z0-9]{10})"',
                r'data-asin="([A-Z0-9]{10})"',
                r'meta[^>]*property="product:retailer_item_id"[^>]*content="([A-Z0-9]{10})"',
                r'<meta[^>]*name="ASIN"[^>]*content="([A-Z0-9]{10})"',
                r'<meta[^>]*property="og:url"[^>]*content="[^"]*dp/([A-Z0-9]{10})"',
                r'"asin":"([A-Z0-9]{10})"',
                r'"product_id":"([A-Z0-9]{10})"',
            ]

            for pattern in patterns:
                import re

                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    asin = match.group(1).upper()
                    logger.debug(f"ASIN extraído do HTML via padrão: {pattern[:30]}...")
                    return asin

            return None

        except Exception as e:
            logger.error(f"Erro ao extrair ASIN do HTML: {e}")
            return None

    async def _extract_asin_with_playwright(self, url: str) -> Optional[str]:
        """
        Extrai ASIN usando Playwright como fallback com retry e jitter.

        Args:
            url: URL do produto

        Returns:
            ASIN extraído ou None
        """
        import random

        max_retries = 3
        base_delay = 1.0  # 1 segundo base

        for attempt in range(max_retries):
            try:
                # Importar Playwright apenas quando necessário
                try:
                    from playwright.async_api import async_playwright
                except ImportError:
                    logger.warning("Playwright não instalado, pulando fallback")
                    return None

                logger.info(
                    f"Tentativa {attempt + 1}/{max_retries} com Playwright para: {url}"
                )

                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()

                    # Configurar timeout e user agent robustos
                    page.set_default_timeout(
                        8000
                    )  # 8 segundos (reduzido para evitar bloqueios)
                    await page.set_extra_http_headers(
                        {
                            "User-Agent": (
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                            ),
                            "Accept": (
                                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                                "image/webp,*/*;q=0.8"
                            ),
                            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                            "Accept-Encoding": "gzip, deflate, br",
                            "DNT": "1",
                            "Connection": "keep-alive",
                            "Upgrade-Insecure-Requests": "1",
                            "Sec-Fetch-Dest": "document",
                            "Sec-Fetch-Mode": "navigate",
                            "Sec-Fetch-Site": "none",
                            "Cache-Control": "max-age=0",
                        }
                    )

                    # Navegar para a página
                    await page.goto(url, wait_until="domcontentloaded")

                    # Tentar extrair ASIN do DOM renderizado
                    asin = await page.evaluate(
                        """
                        () => {
                            // Buscar em múltiplos locais
                            const asinInput = document.querySelector('input[id="ASIN"], input[name="ASIN"]');
                            if (asinInput && asinInput.value) {
                                return asinInput.value;
                            }

                            const dataAsin = document.querySelector('[data-asin]');
                            if (dataAsin && dataAsin.dataset.asin) {
                                return dataAsin.dataset.asin;
                            }

                            const metaAsin = document.querySelector('meta[name="ASIN"], meta[property="product:retailer_item_id"]');
                            if (metaAsin && metaAsin.content) {
                                return metaAsin.content;
                            }

                            // Buscar em JSON-LD
                            const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                            for (const script of scripts) {
                                try {
                                    const data = JSON.parse(script.textContent);
                                    if (data.asin || data.product_id) {
                                        return data.asin || data.product_id;
                                    }
                                } catch (e) {
                                    // Ignorar erros de JSON
                                }
                            }

                            return null;
                        }
                    """
                    )

                    await browser.close()

                    if asin:
                        logger.info(
                            f"ASIN extraído via Playwright (tentativa {attempt + 1}): {asin}"
                        )
                        return asin.upper()

                    # Se chegou aqui, não encontrou ASIN nesta tentativa
                    if attempt < max_retries - 1:
                        # Calcular delay com jitter
                        jitter = random.uniform(0.5, 1.5)
                        delay = base_delay * (2**attempt) * jitter
                        logger.info(
                            f"ASIN não encontrado, aguardando {delay:.2f}s antes da próxima tentativa..."
                        )
                        await asyncio.sleep(delay)

                    return None

            except Exception as e:
                logger.error(f"Erro na tentativa {attempt + 1} com Playwright: {e}")
                if attempt < max_retries - 1:
                    # Calcular delay com jitter para retry
                    jitter = random.uniform(0.5, 1.5)
                    delay = base_delay * (2**attempt) * jitter
                    logger.info(
                        f"Aguardando {delay:.2f}s antes da próxima tentativa..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Todas as {max_retries} tentativas falharam")
                    return None

        return None

    def _build_canonical_url(self, asin: str, original_url: str) -> str:
        """
        Constrói URL canônica da Amazon com tag de afiliado.

        Args:
            asin: ASIN do produto
            original_url: URL original para extrair domínio

        Returns:
            URL canônica com tag de afiliado
        """
        try:
            from src.affiliate.amazon import to_affiliate_url
            from src.utils.url_utils import get_amazon_domain_from_url

            # Extrair domínio da URL original
            domain = get_amazon_domain_from_url(original_url)

            # Construir URL canônica
            return to_affiliate_url(asin, domain)

        except Exception as e:
            logger.error(f"Erro ao construir URL canônica: {e}")
            # Fallback para URL padrão
            return f"https://www.amazon.com.br/dp/{asin}?tag=garimpeirogee-20&language=pt_BR"

    def _extract_title(self, html_content: str) -> Optional[str]:
        """Extrai o título do produto do HTML."""
        import re

        # Padrões comuns para título de produto na Amazon
        patterns = [
            r"<title[^>]*>([^<]+)</title>",
            r'<h1[^>]*id="title"[^>]*>([^<]+)</h1>',
            r'<span[^>]*id="productTitle"[^>]*>([^<]+)</span>',
            r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip()
                # Limpar caracteres especiais e normalizar
                title = re.sub(r"\s+", " ", title)
                return title[:200]  # Limitar tamanho

        return None

    def _extract_price(self, html_content: str) -> Optional[Decimal]:
        """Extrai o preço atual do produto do HTML."""
        import re

        # Padrões para preço na Amazon
        patterns = [
            r'<span[^>]*class="[^"]*price[^"]*"[^>]*>R\$\s*([\d,]+(?:\.\d{2})?)</span>',
            r'<meta[^>]*property="product:price:amount"[^>]*content="([\d.]+)"',
        ]

        # Tentar padrões simples primeiro
        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                try:
                    price_str = match.group(1).replace(",", ".")
                    return Decimal(price_str)
                except (ValueError, TypeError):
                    continue

        # Tentar combinar parte inteira e fracionária
        whole_match = re.search(
            r'<span[^>]*class="[^"]*a-price-whole[^"]*"[^>]*>([\d,]+)</span>',
            html_content,
            re.IGNORECASE,
        )
        fraction_match = re.search(
            r'<span[^>]*class="[^"]*a-price-fraction[^"]*"[^>]*>(\d{2})</span>',
            html_content,
            re.IGNORECASE,
        )

        if whole_match and fraction_match:
            try:
                whole = whole_match.group(1).replace(",", "")
                fraction = fraction_match.group(1)
                price_str = f"{whole}.{fraction}"
                return Decimal(price_str)
            except (ValueError, TypeError):
                pass
        elif whole_match:
            try:
                whole = whole_match.group(1).replace(",", "")
                return Decimal(whole)
            except (ValueError, TypeError):
                pass

        return None

    def _extract_original_price(self, html_content: str) -> Optional[Decimal]:
        """Extrai o preço original do produto do HTML (se disponível)."""
        import re

        # Padrões para preço original/riscado na Amazon
        patterns = [
            r'<span[^>]*class="[^"]*a-text-strike[^"]*"[^>]*>R\$\s*([\d,]+(?:\.\d{2})?)</span>',
            r'<span[^>]*class="[^"]*a-price-delete[^"]*"[^>]*>R\$\s*([\d,]+(?:\.\d{2})?)</span>',
            r'<span[^>]*class="[^"]*a-text-strike[^"]*"[^>]*>([\d,]+(?:\.\d{2})?)</span>',
            r'<span[^>]*class="[^"]*a-price-delete[^"]*"[^>]*>([\d,]+(?:\.\d{2})?)</span>',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                try:
                    price_str = match.group(1).replace(",", ".")
                    return Decimal(price_str)
                except (ValueError, TypeError):
                    continue

        return None

    def can_handle_url(self, url: str) -> bool:
        """
        Verifica se o scraper pode processar a URL.

        Args:
            url: URL para verificar

        Returns:
            True se puder processar, False caso contrário
        """
        from src.affiliate.amazon import is_valid_amazon_url

        return is_valid_amazon_url(url)

    def get_asin_from_url(self, url: str) -> Optional[str]:
        """
        Extrai o ASIN de uma URL da Amazon.

        Args:
            url: URL da Amazon

        Returns:
            ASIN extraído ou None se não encontrado
        """
        return extract_asin_from_url(url)


# Instância global do scraper
amazon_scraper = AmazonScraper()


def scrape_amazon_product(url: str, html_content: str = None) -> Optional[Offer]:
    """
    Função de conveniência para fazer scraping de produto Amazon.

    Args:
        url: URL do produto da Amazon
        html_content: Conteúdo HTML da página (opcional)

    Returns:
        Objeto Offer com informações do produto ou None se falhar
    """
    return amazon_scraper.scrape_product(url, html_content)
