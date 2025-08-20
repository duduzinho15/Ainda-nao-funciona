#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper para Amazon - Garimpeiro Geek
Extrai ofertas da Amazon via Promobit (evita bloqueios diretos)
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
import random
from pathlib import Path
from typing import Any, List, Optional, cast

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup, Tag
from bs4.element import ResultSet, NavigableString

# from core.models import Oferta, ScraperSettings  # Comentado temporariamente

logger = logging.getLogger("amazon_scraper")


class AmazonScraper:
    """Scraper para Amazon usando Promobit como fonte"""

    def __init__(self) -> None:
        self.base_url: str = "https://www.promobit.com.br"
        self.session: Optional[ClientSession] = None
        self.timeout: ClientTimeout = ClientTimeout(total=30)
        self.user_agents: List[str] = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]

        # URLs do Promobit que filtram produtos da Amazon
        self.amazon_urls: List[str] = ["/ofertas", "/ofertas/", "/"]

    def _ensure_session(self) -> ClientSession:
        """Garante que a sessao esta disponivel"""
        if self.session is None:
            raise RuntimeError(
                "ClientSession ainda nao inicializada. Use o contexto ou chame start()."
            )
        return self.session

    async def __aenter__(self) -> AmazonScraper:
        """Context manager entry"""
        self.session = ClientSession(
            timeout=self.timeout,
            headers={
                "User-Agent": random.choice(self.user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
        )
        return self

    async def __aexit__(
        self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Any
    ) -> None:
        """Context manager exit"""
        if self.session is not None:
            await self.session.close()
            self.session = None

    def _safe_select(self, soup: BeautifulSoup, selector: str) -> List[Tag]:
        """Funcao helper tipada para o metodo select do BeautifulSoup"""
        try:
            result: ResultSet[Tag] = soup.select(selector)
            # Garante que o resultado seja uma lista de Tags
            return list(result)
        except Exception as e:
            logger.warning(f"Erro ao usar selector '{selector}': {e}")
            return []

    async def buscar_ofertas(
        self, max_paginas: int = 2, max_requests: int = 4
    ) -> List[Oferta]:
        """Busca ofertas da Amazon via Promobit"""
        logger.info(
            f"Iniciando busca de ofertas da Amazon via Promobit (max_paginas={max_paginas})"
        )

        all_ofertas: List[Oferta] = []
        request_count = 0

        try:
            # Busca em URLs especificas da Amazon no Promobit
            for url_suffix in self.amazon_urls[:max_paginas]:
                if request_count >= max_requests:
                    break

                try:
                    url = f"{self.base_url}{url_suffix}"
                    logger.info(f"Buscando em: {url}")

                    ofertas = await self._scrape_pagina(url)
                    # Filtra apenas ofertas validas e da Amazon
                    amazon_ofertas: List[Oferta] = [
                        o
                        for o in ofertas
                        if o
                        and isinstance(o, Oferta)
                        and o.loja
                        and "amazon" in o.loja.lower()
                    ]
                    all_ofertas.extend(amazon_ofertas)
                    request_count += 1

                    # Delay entre requests
                    await asyncio.sleep(random.uniform(2, 4))

                except Exception as e:
                    logger.error(f"Erro ao buscar em {url_suffix}: {e}")
                    continue

            # Se nao encontrou ofertas especificas da Amazon, busca em categorias gerais
            if not all_ofertas:
                logger.info("Buscando ofertas da Amazon em categorias gerais...")
                general_urls: List[str] = ["/ofertas", "/"]

                for url_suffix in general_urls:
                    if request_count >= max_requests:
                        break

                    try:
                        url = f"{self.base_url}{url_suffix}"
                        logger.info(f"Buscando em: {url}")

                        ofertas = await self._scrape_pagina(url)
                        # Filtra apenas ofertas validas e da Amazon
                        amazon_ofertas = [
                            o
                            for o in ofertas
                            if o
                            and isinstance(o, Oferta)
                            and o.loja
                            and "amazon" in o.loja.lower()
                        ]
                        all_ofertas.extend(amazon_ofertas)
                        request_count += 1

                        await asyncio.sleep(random.uniform(2, 4))

                    except Exception as e:
                        logger.error(f"Erro ao buscar em {url_suffix}: {e}")
                        continue

            logger.info(
                f"Busca concluida. Total de ofertas da Amazon encontradas: {len(all_ofertas)}"
            )
            return all_ofertas

        except Exception as e:
            logger.error(f"Erro geral na busca: {e}")
            return []

    async def fetch_html(
        self, session: aiohttp.ClientSession, url: str, timeout: aiohttp.ClientTimeout
    ) -> str:
        """
        Busca HTML de uma URL com timeout configurável.

        Args:
            session: Sessão HTTP ativa.
            url: URL para buscar.
            timeout: Timeout configurável.

        Returns:
            Conteúdo HTML da página.

        Raises:
            aiohttp.ClientError: Em caso de erro HTTP.
            asyncio.TimeoutError: Em caso de timeout.
        """
        try:
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                return await response.text()
        except aiohttp.ClientError as e:
            logger.error(f"Erro HTTP ao buscar {url}: {e}")
            raise
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout ao buscar {url}: {e}")
            raise

    def parse_ofertas(self, html: str, source_url: str) -> List[Oferta]:
        """
        Parse HTML e extrai lista de ofertas.

        Args:
            html: Conteúdo HTML da página.
            source_url: URL de origem para rastreamento.

        Returns:
            Lista de ofertas extraídas.
        """
        try:
            # Implementar parsing específico do Promobit
            # Por enquanto, retorna lista vazia
            logger.info(f"Parsing HTML de {source_url} - {len(html)} caracteres")

            return []

        except Exception as e:
            logger.error(f"Erro ao fazer parsing de {source_url}: {e}")
            return []

    async def get_ofertas(
        self, urls: List[str], settings: ScraperSettings
    ) -> List[Oferta]:
        """
        Busca ofertas de múltiplas URLs com configurações.

        Args:
            urls: Lista de URLs para buscar.
            settings: Configurações do scraper.

        Returns:
            Lista de ofertas encontradas.
        """
        try:
            all_ofertas = []

            for url in urls:
                try:
                    # Aplicar intervalo entre requisições
                    if all_ofertas:  # Não esperar na primeira requisição
                        await asyncio.sleep(settings.intervalo_requisicoes / 1000)

                    # Buscar HTML
                    html = await self.fetch_html(
                        self._ensure_session(),
                        url,
                        aiohttp.ClientTimeout(total=settings.timeout),
                    )

                    # Salvar HTML se debug estiver ativado
                    if settings.salvar_html_debug:
                        await self._save_debug_html(html, url)

                    # Parse das ofertas
                    ofertas = self.parse_ofertas(html, url)
                    all_ofertas.extend(ofertas)

                    logger.info(f"URL {url}: {len(ofertas)} ofertas encontradas")

                except Exception as e:
                    logger.error(f"Erro ao processar {url}: {e}")
                    continue

            logger.info(f"Total de ofertas encontradas: {len(all_ofertas)}")
            return all_ofertas

        except Exception as e:
            logger.error(f"Erro geral ao buscar ofertas: {e}")
            return []

    async def _save_debug_html(self, html: str, url: str) -> None:
        """
        Salva HTML para debug se configurado.

        Args:
            html: Conteúdo HTML.
            url: URL de origem.
        """
        try:
            debug_dir = Path("./debug_html")
            debug_dir.mkdir(exist_ok=True)

            # Nome do arquivo baseado na URL
            filename = re.sub(r"[^\w\-_.]", "_", url) + ".html"
            filepath = debug_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)

            logger.debug(f"HTML salvo para debug: {filepath}")

        except Exception as e:
            logger.error(f"Erro ao salvar HTML de debug: {e}")

        except Exception as e:
            logger.error(f"Erro geral na busca: {e}")
            return []

    async def _scrape_pagina(self, url: str) -> List[Oferta]:
        """Scrapa uma pagina especifica do Promobit"""
        try:
            session = self._ensure_session()
            async with session.get(url) as response:
                response.raise_for_status()
                html_text: str = await response.text()

                # Salva HTML para debug
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"amazon_via_promobit_{timestamp}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(html_text)
                logger.debug(f"HTML salvo em {filename}")

                return self.parse_ofertas(html_text, url)

        except Exception as e:
            logger.error(f"Erro ao fazer request para {url}: {e}")
            return []

    def _parse_ofertas(self, html: str, source_url: str) -> List[Oferta]:
        """Parseia o HTML para extrair ofertas do Promobit"""
        try:
            soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
            ofertas: List[Oferta] = []

            # Busca por cards de ofertas usando a funcao helper tipada
            offer_cards: List[Tag] = self._safe_select(
                soup,
                'div[data-component-type="s-search-result"], .s-result-item, .sg-col-inner',
            )

            if not offer_cards:
                # Fallback para outros seletores
                offer_cards = self._safe_select(
                    soup, ".card, .offer, .product, article"
                )

            # Se ainda nao encontrou, tenta seletores mais genericos
            if not offer_cards:
                offer_cards = self._safe_select(
                    soup,
                    'div[class*="card"], div[class*="offer"], div[class*="product"], div[class*="item"]',
                )

            # Ultimo fallback: busca por elementos que contenham precos
            if not offer_cards:
                price_elements: List[NavigableString] = soup.find_all(
                    text=re.compile(r"R\$\s*\d")
                )
                if price_elements:
                    for price_elem in price_elements:
                        parent = price_elem.parent
                        if parent and hasattr(parent, "name") and parent.name:
                            offer_cards.append(cast(Tag, parent))

            logger.info(
                f"Encontrados {len(offer_cards)} cards de oferta em {source_url}"
            )

            for card in offer_cards:
                try:
                    oferta = self._extrair_oferta(card, source_url)
                    if oferta and isinstance(oferta, Oferta):
                        ofertas.append(oferta)
                        logger.debug(
                            f"Oferta extraida: {oferta.titulo[:50]}... - {oferta.preco}"
                        )
                except Exception as e:
                    logger.warning(f"Erro ao extrair oferta: {e}")
                    continue

            logger.info(f"Pagina {source_url}: {len(ofertas)} ofertas extraidas")
            return ofertas

        except Exception as e:
            logger.error(f"Erro ao fazer parse do HTML: {e}")
            return []

    def _extrair_oferta(self, card: Tag, source_url: str) -> Optional[Oferta]:
        """Extrai dados de uma oferta individual"""
        try:
            # Titulo da oferta - busca em multiplos elementos
            titulo: str = ""
            titulo_selectors: List[str] = [
                "h2 a span",
                ".a-text-normal",
                ".a-size-base-plus",
                ".titulo",
                ".title",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "a[title]",
                "a[alt]",
                "div[title]",
                "span[title]",
                "div.titulo",
                "div.title",
                "span.titulo",
                "span.title",
            ]

            for selector in titulo_selectors:
                elem: Optional[Tag] = card.select_one(selector)
                if elem:
                    titulo_raw = elem.get_text(strip=True)
                    titulo = titulo_raw if isinstance(titulo_raw, str) else ""
                    if titulo and len(titulo) > 10:
                        break

            # Se nao encontrou titulo, tenta extrair do texto do card
            if not titulo:
                text_elements: List[NavigableString] = card.find_all(string=True)
                for text in text_elements:
                    text_str: str = text.strip() if isinstance(text, str) else ""
                    if (
                        len(text_str) > 15
                        and not re.search(r"R\$\s*\d", text_str)
                        and not re.search(r"\d{1,3}(?:\.\d{3})*,\d{2}", text_str)
                    ):
                        titulo = text_str
                        break

            if not titulo or len(titulo) < 10:
                return None

            # Preco atual - busca em multiplos elementos
            preco: str = ""
            preco_selectors: List[str] = [
                ".a-price-whole",
                ".a-price .a-offscreen",
                ".preco",
                ".price",
                'span[class*="price"]',
                'span[class*="preco"]',
                'span[class*="valor"]',
                'div[class*="price"]',
                'div[class*="preco"]',
                'div[class*="valor"]',
                "strong",
                "b",
                "span.preco",
                "div.preco",
            ]

            for selector in preco_selectors:
                elem = card.select_one(selector)
                if elem:
                    text_raw = elem.get_text(strip=True)
                    text: str = text_raw if isinstance(text_raw, str) else ""
                    if self._is_valid_price(text):
                        preco = text
                        break

            # Se nao encontrou preco, busca no texto do card
            if not preco:
                card_text: str = card.get_text() or ""
                price_match = re.search(r"R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}", card_text)
                if price_match:
                    preco = price_match.group(0)

            if not self._is_valid_price(preco):
                return None

            # Preco original (se houver desconto)
            preco_original: str = ""
            original_selectors: List[str] = [
                ".a-text-strike",
                ".a-price.a-text-price .a-offscreen",
                ".preco-original",
                'span[class*="original"]',
                'span[class*="old"]',
                'span[class*="antigo"]',
                "del",
                "s",
                "strike",
            ]

            for selector in original_selectors:
                elem = card.select_one(selector)
                if elem:
                    text_raw = elem.get_text(strip=True)
                    text = text_raw if isinstance(text_raw, str) else ""
                    if self._is_valid_price(text):
                        preco_original = text
                        break

            # Calcula desconto (não utilizado atualmente)
            if preco_original and self._is_valid_price(preco_original):
                try:
                    preco_atual = float(re.sub(r"[^\d,]", "", preco).replace(",", "."))
                    preco_orig = float(
                        re.sub(r"[^\d,]", "", preco_original).replace(",", ".")
                    )
                    if preco_orig > preco_atual:
                        _ = int(((preco_orig - preco_atual) / preco_orig) * 100)
                except Exception:
                    pass

            # URL do produto
            url_produto: str = ""
            link_elem: Optional[Tag] = card.select_one(
                'a[href*="/dp/"], a[href*="amazon"], a[href]'
            )
            if link_elem and link_elem.get("href"):
                href_raw = link_elem["href"]
                # Garante que href seja uma string
                if isinstance(href_raw, list):
                    href_value: str = href_raw[0] if href_raw else ""
                else:
                    href_value: str = str(href_raw)

                if href_value and href_value.startswith("/"):
                    url_produto = f"{self.base_url}{href_value}"
                elif href_value and href_value.startswith("http"):
                    url_produto = href_value
                elif href_value:
                    url_produto = f"{self.base_url}/{href_value}"

            if not url_produto:
                url_produto = source_url

            # Imagem do produto
            imagem_url: str = ""
            img_elem: Optional[Tag] = card.select_one(
                'img[src*="images"], .s-image, img'
            )
            if img_elem and img_elem.get("src"):
                src_raw = img_elem["src"]
                # Garante que src seja uma string
                if isinstance(src_raw, list):
                    imagem_url = src_raw[0] if src_raw else ""
                else:
                    imagem_url = str(src_raw)

            # Loja (deve ser Amazon)
            loja: str = "Amazon"

            return Oferta(
                titulo=titulo,
                loja=loja,
                preco=float(re.sub(r"[^\d,]", "", preco).replace(",", "."))
                if preco
                else None,
                preco_original=float(
                    re.sub(r"[^\d,]", "", preco_original).replace(",", ".")
                )
                if preco_original
                else None,
                url=url_produto,
                imagem_url=imagem_url if imagem_url else None,
                created_at=datetime.now(),
                fonte="amazon_scraper",
            )

        except Exception as e:
            logger.warning(f"Erro ao extrair oferta: {e}")
            return None

    def _is_valid_price(self, price_str: str) -> bool:
        """Valida se o preco e valido"""
        if not price_str:
            return False

        # Remove espacos e normaliza
        price_str = price_str.strip()

        # Padroes de preco brasileiro
        patterns: List[str] = [
            r"R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}",  # R$ 1.234,56
            r"R\$\s*\d+,\d{2}",  # R$ 123,45
            r"R\$\s*\d+",  # R$ 123
            r"\d{1,3}(?:\.\d{3})*,\d{2}",  # 1.234,56
            r"\d+,\d{2}",  # 123,45
        ]

        for pattern in patterns:
            if re.match(pattern, price_str):
                return True

        return False


async def buscar_ofertas_amazon(
    session: Optional[ClientSession] = None, max_paginas: int = 2, max_requests: int = 4
) -> List[Oferta]:
    """Funcao principal para buscar ofertas da Amazon via Promobit"""
    async with AmazonScraper() as scraper:
        return await scraper.buscar_ofertas(
            max_paginas=max_paginas, max_requests=max_requests
        )


# ===== FUNÇÃO COMPATIBILIDADE COM SCRAPER REGISTRY =====

async def get_ofertas(periodo: str = "24h") -> List[Dict[str, Any]]:
    """
    Função de compatibilidade com o scraper registry.
    
    Args:
        periodo: Período para coleta (24h, 7d, 30d, all)
        
    Returns:
        Lista de ofertas encontradas
    """
    try:
        # Buscar ofertas da Amazon
        ofertas = await buscar_ofertas_amazon(max_paginas=2, max_requests=4)
        
        # Converter para formato de dicionário
        ofertas_dict = []
        for oferta in ofertas:
            oferta_dict = {
                'titulo': oferta.titulo,
                'loja': oferta.loja,
                'preco': oferta.preco,
                'preco_original': oferta.preco_original,
                'url': oferta.url,
                'imagem_url': oferta.imagem_url,
                'fonte': 'amazon_scraper',
                'periodo': periodo,
                'timestamp': time.time()
            }
            ofertas_dict.append(oferta_dict)
        
        return ofertas_dict
        
    except Exception as e:
        logger.error(f"❌ Erro na função get_ofertas: {e}")
        return []

# Configurações para o scraper registry
priority = 95  # Prioridade muito alta (Amazon)
rate_limit = 0.2  # 0.2 requisições por segundo (site muito sensível)
description = "Scraper para Amazon via Promobit - Evita bloqueios diretos"

# Teste direto
if __name__ == "__main__":

    async def main() -> None:
        logging.basicConfig(level=logging.INFO)
        ofertas = await buscar_ofertas_amazon(max_paginas=1, max_requests=2)

        print(f"\nRESULTADO: {len(ofertas)} ofertas da Amazon encontradas")
        for i, oferta in enumerate(ofertas[:5], 1):
            print(f"{i}. {oferta.titulo[:60]}... - {oferta.preco}")

    asyncio.run(main())
