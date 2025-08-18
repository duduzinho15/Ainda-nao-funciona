#!/usr/bin/env python3
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
from typing import Any, Dict, List, Optional, TypedDict, Union, cast

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientResponse
from bs4 import BeautifulSoup, Tag
from bs4.element import ResultSet

import config

logger = logging.getLogger("amazon_scraper")

# Tipos tipados para ofertas
class OfertaDict(TypedDict):
    titulo: str
    preco: str
    preco_original: str
    desconto: int
    url_produto: str
    imagem_url: str
    loja: str
    fonte: str
    categoria: str
    timestamp: str

class AmazonScraper:
    """Scraper para Amazon usando Promobit como fonte"""
    
    def __init__(self) -> None:
        self.base_url: str = "https://www.promobit.com.br"
        self.session: Optional[ClientSession] = None
        self.timeout: ClientTimeout = ClientTimeout(total=30)
        self.user_agents: List[str] = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        
        # URLs do Promobit que filtram produtos da Amazon
        self.amazon_urls: List[str] = [
            "/ofertas",
            "/ofertas/",
            "/"
        ]
    
    def _ensure_session(self) -> ClientSession:
        """Garante que a sessão está disponível"""
        if self.session is None:
            raise RuntimeError("ClientSession ainda não inicializada. Use o contexto ou chame start().")
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
                "Upgrade-Insecure-Requests": "1"
            }
        )
        return self
    
    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Any) -> None:
        """Context manager exit"""
        if self.session is not None:
            await self.session.close()
            self.session = None
    
    async def buscar_ofertas(self, max_paginas: int = 2, max_requests: int = 4) -> List[OfertaDict]:
        """Busca ofertas da Amazon via Promobit"""
        logger.info(f"🚀 Iniciando busca de ofertas da Amazon via Promobit (max_paginas={max_paginas})")
        
        all_ofertas: List[OfertaDict] = []
        request_count = 0
        
        try:
            # Busca em URLs específicas da Amazon no Promobit
            for url_suffix in self.amazon_urls[:max_paginas]:
                if request_count >= max_requests:
                    break
                
                try:
                    url = f"{self.base_url}{url_suffix}"
                    logger.info(f"📄 Buscando em: {url}")
                    
                    ofertas = await self._scrape_pagina(url)
                    # Filtra apenas ofertas válidas e da Amazon
                    amazon_ofertas: List[OfertaDict] = [
                        o for o in ofertas 
                        if o and isinstance(o, dict) and o.get("loja") and "amazon" in (o.get("loja") or "").lower()
                    ]
                    all_ofertas.extend(amazon_ofertas)
                    request_count += 1
                    
                    # Delay entre requests
                    await asyncio.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao buscar em {url_suffix}: {e}")
                    continue
            
            # Se não encontrou ofertas específicas da Amazon, busca em categorias gerais
            if not all_ofertas:
                logger.info("🔍 Buscando ofertas da Amazon em categorias gerais...")
                general_urls: List[str] = [
                    "/ofertas",
                    "/"
                ]
                
                for url_suffix in general_urls:
                    if request_count >= max_requests:
                        break
                    
                    try:
                        url = f"{self.base_url}{url_suffix}"
                        logger.info(f"📄 Buscando em: {url}")
                        
                        ofertas = await self._scrape_pagina(url)
                        # Filtra apenas ofertas válidas e da Amazon
                        amazon_ofertas = [
                            o for o in ofertas 
                            if o and isinstance(o, dict) and o.get("loja") and "amazon" in (o.get("loja") or "").lower()
                        ]
                        all_ofertas.extend(amazon_ofertas)
                        request_count += 1
                        
                        await asyncio.sleep(random.uniform(2, 4))
                        
                    except Exception as e:
                        logger.error(f"❌ Erro ao buscar em {url_suffix}: {e}")
                        continue
            
            logger.info(f"✅ Busca concluída. Total de ofertas da Amazon encontradas: {len(all_ofertas)}")
            return all_ofertas
            
        except Exception as e:
            logger.error(f"❌ Erro geral na busca: {e}")
            return []
    
    async def _scrape_pagina(self, url: str) -> List[OfertaDict]:
        """Scrapa uma página específica do Promobit"""
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
                
                return self._parse_ofertas(html_text, url)
                
        except Exception as e:
            logger.error(f"❌ Erro ao fazer request para {url}: {e}")
            return []
    
    def _parse_ofertas(self, html: str, source_url: str) -> List[OfertaDict]:
        """Parseia o HTML para extrair ofertas do Promobit"""
        try:
            soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
            ofertas: List[OfertaDict] = []
            
            # Busca por cards de ofertas (mesmo padrão do Promobit)
            # Usa cast para resolver o problema de tipagem do método select
            offer_cards: ResultSet[Tag] = cast(ResultSet[Tag], soup.select('div[data-component-type="s-search-result"], .s-result-item, .sg-col-inner'))
            
            if not offer_cards:
                # Fallback para outros seletores
                offer_cards = cast(ResultSet[Tag], soup.select('.card, .offer, .product, article'))
            
            # Se ainda não encontrou, tenta seletores mais genéricos
            if not offer_cards:
                offer_cards = cast(ResultSet[Tag], soup.select('div[class*="card"], div[class*="offer"], div[class*="product"], div[class*="item"]'))
            
            # Último fallback: busca por elementos que contenham preços
            if not offer_cards:
                price_elements: List[Any] = soup.find_all(text=re.compile(r"R\$\s*\d"))
                if price_elements:
                    for price_elem in price_elements:
                        parent = price_elem.parent
                        if parent and parent.name:
                            offer_cards.append(parent)
            
            logger.info(f"🔍 Encontrados {len(offer_cards)} cards de oferta em {source_url}")
            
            for card in offer_cards:
                try:
                    oferta = self._extrair_oferta(card, source_url)
                    if oferta and isinstance(oferta, dict):
                        ofertas.append(oferta)
                        logger.debug(f"Oferta extraída: {oferta['titulo'][:50]}... - {oferta['preco']}")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao extrair oferta: {e}")
                    continue
            
            logger.info(f"📊 Página {source_url}: {len(ofertas)} ofertas extraídas")
            return ofertas
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer parse do HTML: {e}")
            return []
    
    def _extrair_oferta(self, card: Tag, source_url: str) -> Optional[OfertaDict]:
        """Extrai dados de uma oferta individual"""
        try:
            # Título da oferta - busca em múltiplos elementos
            titulo: str = ""
            titulo_selectors: List[str] = [
                'h2 a span', '.a-text-normal', '.a-size-base-plus', '.titulo', '.title',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'a[title]', 'a[alt]', 'div[title]', 'span[title]',
                'div.titulo', 'div.title', 'span.titulo', 'span.title'
            ]
            
            for selector in titulo_selectors:
                elem: Optional[Tag] = card.select_one(selector)
                if elem:
                    titulo_raw = elem.get_text(strip=True)
                    titulo = titulo_raw if isinstance(titulo_raw, str) else ""
                    if titulo and len(titulo) > 10:
                        break
            
            # Se não encontrou título, tenta extrair do texto do card
            if not titulo:
                text_elements: List[Any] = card.find_all(string=True)
                for text in text_elements:
                    text_str: str = text.strip() if isinstance(text, str) else ""
                    if (len(text_str) > 15 and 
                        not re.search(r"R\$\s*\d", text_str) and
                        not re.search(r"\d{1,3}(?:\.\d{3})*,\d{2}", text_str)):
                        titulo = text_str
                        break
            
            if not titulo or len(titulo) < 10:
                return None
            
            # Preço atual - busca em múltiplos elementos
            preco: str = ""
            preco_selectors: List[str] = [
                '.a-price-whole', '.a-price .a-offscreen', '.preco', '.price',
                'span[class*="price"]', 'span[class*="preco"]', 'span[class*="valor"]',
                'div[class*="price"]', 'div[class*="preco"]', 'div[class*="valor"]',
                'strong', 'b', 'span.preco', 'div.preco'
            ]
            
            for selector in preco_selectors:
                elem = card.select_one(selector)
                if elem:
                    text_raw = elem.get_text(strip=True)
                    text: str = text_raw if isinstance(text_raw, str) else ""
                    if self._is_valid_price(text):
                        preco = text
                        break
            
            # Se não encontrou preço, busca no texto do card
            if not preco:
                card_text: str = card.get_text() or ""
                price_match = re.search(r"R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}", card_text)
                if price_match:
                    preco = price_match.group(0)
            
            if not self._is_valid_price(preco):
                return None
            
            # Preço original (se houver desconto)
            preco_original: str = ""
            original_selectors: List[str] = [
                '.a-text-strike', '.a-price.a-text-price .a-offscreen', '.preco-original',
                'span[class*="original"]', 'span[class*="old"]', 'span[class*="antigo"]',
                'del', 's', 'strike'
            ]
            
            for selector in original_selectors:
                elem = card.select_one(selector)
                if elem:
                    text_raw = elem.get_text(strip=True)
                    text = text_raw if isinstance(text_raw, str) else ""
                    if self._is_valid_price(text):
                        preco_original = text
                        break
            
            # Calcula desconto
            desconto: int = 0
            if preco_original and self._is_valid_price(preco_original):
                try:
                    preco_atual = float(re.sub(r"[^\d,]", "", preco).replace(",", "."))
                    preco_orig = float(re.sub(r"[^\d,]", "", preco_original).replace(",", "."))
                    if preco_orig > preco_atual:
                        desconto = int(((preco_orig - preco_atual) / preco_orig) * 100)
                except:
                    pass
            
            # URL do produto
            url_produto: str = ""
            link_elem: Optional[Tag] = card.select_one('a[href*="/dp/"], a[href*="amazon"], a[href]')
            if link_elem and link_elem.get('href'):
                href_raw = link_elem['href']
                # Garante que href seja uma string
                if isinstance(href_raw, list):
                    href: str = href_raw[0] if href_raw else ""
                else:
                    href: str = str(href_raw)
                
                if href and href.startswith('/'):
                    url_produto = f"{self.base_url}{href}"
                elif href and href.startswith('http'):
                    url_produto = href
                elif href:
                    url_produto = f"{self.base_url}/{href}"
            
            if not url_produto:
                url_produto = source_url
            
            # Imagem do produto
            imagem_url: str = ""
            img_elem: Optional[Tag] = card.select_one('img[src*="images"], .s-image, img')
            if img_elem and img_elem.get('src'):
                src_raw = img_elem['src']
                # Garante que src seja uma string
                if isinstance(src_raw, list):
                    imagem_url = src_raw[0] if src_raw else ""
                else:
                    imagem_url = str(src_raw)
            
            # Loja (deve ser Amazon)
            loja: str = "Amazon"
            
            return {
                "titulo": titulo,
                "preco": preco,
                "preco_original": preco_original,
                "desconto": desconto,
                "url_produto": url_produto,
                "imagem_url": imagem_url,
                "loja": loja,
                "fonte": "amazon_scraper",
                "categoria": "hardware",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao extrair oferta: {e}")
            return None
    
    def _is_valid_price(self, price_str: str) -> bool:
        """Valida se o preço é válido"""
        if not price_str:
            return False
        
        # Remove espaços e normaliza
        price_str = price_str.strip()
        
        # Padrões de preço brasileiro
        patterns: List[str] = [
            r"R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}",  # R$ 1.234,56
            r"R\$\s*\d+,\d{2}",                   # R$ 123,45
            r"R\$\s*\d+",                         # R$ 123
            r"\d{1,3}(?:\.\d{3})*,\d{2}",        # 1.234,56
            r"\d+,\d{2}"                          # 123,45
        ]
        
        for pattern in patterns:
            if re.match(pattern, price_str):
                return True
        
        return False

async def buscar_ofertas_amazon(session: Optional[ClientSession] = None, max_paginas: int = 2, max_requests: int = 4) -> List[OfertaDict]:
    """Função principal para buscar ofertas da Amazon via Promobit"""
    async with AmazonScraper() as scraper:
        return await scraper.buscar_ofertas(max_paginas=max_paginas, max_requests=max_requests)

# Teste direto
if __name__ == "__main__":
    async def main() -> None:
        logging.basicConfig(level=logging.INFO)
        ofertas = await buscar_ofertas_amazon(max_paginas=1, max_requests=2)
        
        print(f"\n📊 RESULTADO: {len(ofertas)} ofertas da Amazon encontradas")
        for i, oferta in enumerate(ofertas[:5], 1):
            print(f"{i}. {oferta['titulo'][:60]}... - {oferta['preco']}")
    
    asyncio.run(main())
