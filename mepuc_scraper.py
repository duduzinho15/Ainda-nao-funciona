#!/usr/bin/env python3
"""
Scraper para MeuPC.net - Garimpeiro Geek
Extrai ofertas de hardware e tecnologia
"""
import asyncio
import aiohttp
import logging
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime
import random

logger = logging.getLogger("mepuc_scraper")

class MeuPCScraper:
    """Scraper para MeuPC.net"""
    
    def __init__(self):
        self.base_url = "https://www.meupc.net"
        self.session = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
    
    async def __aenter__(self):
        """Context manager entry"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
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
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.close()
    
    async def buscar_ofertas(self, max_paginas: int = 3, max_requests: int = 10) -> List[Dict[str, Any]]:
        """Busca ofertas do MeuPC.net"""
        logger.info(f"🚀 Iniciando busca de ofertas no MeuPC.net (max_paginas={max_paginas})")
        
        all_ofertas = []
        request_count = 0
        
        try:
            # Busca na página principal de ofertas
            urls = [
                f"{self.base_url}/ofertas",
                f"{self.base_url}/ofertas/",
                f"{self.base_url}/"
            ]
            
            for url in urls[:max_paginas]:
                if request_count >= max_requests:
                    break
                
                try:
                    logger.info(f"📄 Buscando em: {url}")
                    ofertas = await self._scrape_pagina(url)
                    all_ofertas.extend(ofertas)
                    request_count += 1
                    
                    # Delay entre requests
                    await asyncio.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao buscar em {url}: {e}")
                    continue
            
            logger.info(f"✅ Busca concluída. Total de ofertas encontradas: {len(all_ofertas)}")
            return all_ofertas
            
        except Exception as e:
            logger.error(f"❌ Erro geral na busca: {e}")
            return []
    
    async def _scrape_pagina(self, url: str) -> List[Dict[str, Any]]:
        """Scrapa uma página específica"""
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                
                # Salva HTML para debug
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"mepuc_page_{timestamp}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(html)
                logger.debug(f"HTML salvo em {filename}")
                
                return self._parse_ofertas(html, url)
                
        except Exception as e:
            logger.error(f"❌ Erro ao fazer request para {url}: {e}")
            return []
    
    def _parse_ofertas(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """Parseia o HTML para extrair ofertas"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            ofertas = []
            
            # Busca por cards de ofertas - ajustando seletores baseado na estrutura real
            offer_cards = []
            
            # Tenta diferentes seletores baseados na estrutura do site
            selectors = [
                "div.offer", "div.product", "div.item", "div.card", "div.box",
                "article", "div.oferta", "div.produto", "div.produto-item",
                "div[class*='offer']", "div[class*='product']", "div[class*='item']",
                "div[class*='card']", "div[class*='box']"
            ]
            
            for selector in selectors:
                offer_cards = soup.select(selector)
                if offer_cards:
                    logger.info(f"✅ Seletores encontrados com: {selector}")
                    break
            
            # Se ainda não encontrou, tenta buscar por estrutura genérica
            if not offer_cards:
                # Busca por elementos que contenham preços
                price_elements = soup.find_all(text=re.compile(r"R\$\s*\d"))
                if price_elements:
                    # Cria cards baseados nos elementos de preço
                    for price_elem in price_elements:
                        parent = price_elem.parent
                        if parent and parent.name:
                            offer_cards.append(parent)
            
            logger.info(f"🔍 Encontrados {len(offer_cards)} cards de oferta em {source_url}")
            
            for card in offer_cards:
                try:
                    oferta = self._extrair_oferta(card, source_url)
                    if oferta:
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
    
    def _extrair_oferta(self, card, source_url: str) -> Dict[str, Any] | None:
        """Extrai dados de uma oferta individual"""
        try:
            # Título - busca em múltiplos elementos
            titulo = ""
            titulo_selectors = [
                "h1", "h2", "h3", "h4", "h5", "h6",
                "a[title]", "a[alt]", "div[title]", "span[title]",
                "div.titulo", "div.title", "span.titulo", "span.title"
            ]
            
            for selector in titulo_selectors:
                elem = card.select_one(selector)
                if elem:
                    titulo = elem.get_text(strip=True)
                    if titulo and len(titulo) > 10:
                        break
            
            # Se não encontrou título, tenta extrair do texto do card
            if not titulo:
                # Busca por texto que pareça título (mais longo, sem números de preço)
                text_elements = card.find_all(text=True)
                for text in text_elements:
                    text = text.strip()
                    if (len(text) > 15 and 
                        not re.search(r"R\$\s*\d", text) and
                        not re.search(r"\d{1,3}(?:\.\d{3})*,\d{2}", text)):
                        titulo = text
                        break
            
            if not titulo or len(titulo) < 10:
                return None
            
            # Preço - busca em múltiplos elementos
            preco = ""
            preco_selectors = [
                "span[class*='price']", "span[class*='preco']", "span[class*='valor']",
                "div[class*='price']", "div[class*='preco']", "div[class*='valor']",
                "strong", "b", "span.preco", "div.preco"
            ]
            
            for selector in preco_selectors:
                elem = card.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if self._is_valid_price(text):
                        preco = text
                        break
            
            # Se não encontrou preço, busca no texto do card
            if not preco:
                price_match = re.search(r"R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}", card.get_text())
                if price_match:
                    preco = price_match.group(0)
            
            if not self._is_valid_price(preco):
                return None
            
            # URL do produto
            url_produto = ""
            url_elem = card.find("a", href=True)
            if url_elem and url_elem["href"]:
                href = url_elem["href"]
                if href.startswith("/"):
                    url_produto = f"{self.base_url}{href}"
                elif href.startswith("http"):
                    url_produto = href
                else:
                    url_produto = f"{self.base_url}/{href}"
            
            if not url_produto:
                # Se não tem URL específica, usa a URL da página
                url_produto = source_url
            
            # Imagem
            imagem_url = ""
            img_elem = card.find("img")
            if img_elem and img_elem.get("src"):
                src = img_elem["src"]
                if src.startswith("/"):
                    imagem_url = f"{self.base_url}{src}"
                elif src.startswith("http"):
                    imagem_url = src
                else:
                    imagem_url = f"{self.base_url}/{src}"
            
            # Preço original (se houver desconto)
            preco_original = ""
            # Busca por preços riscados ou originais
            original_selectors = [
                "span[class*='original']", "span[class*='old']", "span[class*='antigo']",
                "del", "s", "strike"
            ]
            
            for selector in original_selectors:
                elem = card.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if self._is_valid_price(text):
                        preco_original = text
                        break
            
            # Calcula desconto
            desconto = 0
            if preco_original and self._is_valid_price(preco_original):
                try:
                    preco_atual = float(re.sub(r"[^\d,]", "", preco).replace(",", "."))
                    preco_orig = float(re.sub(r"[^\d,]", "", preco_original).replace(",", "."))
                    if preco_orig > preco_atual:
                        desconto = int(((preco_orig - preco_atual) / preco_orig) * 100)
                except:
                    pass
            
            return {
                "titulo": titulo,
                "preco": preco,
                "preco_original": preco_original,
                "desconto": desconto,
                "url_produto": url_produto,
                "imagem_url": imagem_url,
                "loja": "MeuPC.net",
                "fonte": "mepuc_scraper",
                "categoria": self._detectar_categoria(titulo),
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
        patterns = [
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
    
    def _detectar_categoria(self, titulo: str) -> str:
        """Detecta categoria baseada no título"""
        titulo_lower = titulo.lower()
        
        categorias = {
            "processador": ["cpu", "processador", "intel", "amd", "ryzen", "core"],
            "placa_video": ["gpu", "placa", "rtx", "gtx", "radeon", "nvidia"],
            "memoria": ["ram", "memória", "ddr4", "ddr5"],
            "armazenamento": ["ssd", "hd", "disco", "nvme"],
            "placa_mae": ["motherboard", "placa-mãe", "b550", "z690"],
            "fonte": ["fonte", "power supply", "psu"],
            "gabinete": ["gabinete", "case"],
            "monitor": ["monitor", "tela", "display"],
            "perifericos": ["mouse", "teclado", "headset", "webcam"]
        }
        
        for categoria, keywords in categorias.items():
            if any(keyword in titulo_lower for keyword in keywords):
                return categoria
        
        return "hardware"

async def buscar_ofertas_mepuc(session: aiohttp.ClientSession | None = None, max_paginas: int = 3, max_requests: int = 10) -> List[Dict[str, Any]]:
    """Função principal para buscar ofertas do MeuPC.net"""
    async with MeuPCScraper() as scraper:
        return await scraper.buscar_ofertas(max_paginas=max_paginas, max_requests=max_requests)

# Teste direto
if __name__ == "__main__":
    async def main():
        logging.basicConfig(level=logging.INFO)
        ofertas = await buscar_ofertas_mepuc(max_paginas=2, max_requests=5)
        
        print(f"\n📊 RESULTADO: {len(ofertas)} ofertas encontradas")
        for i, oferta in enumerate(ofertas[:5], 1):
            print(f"{i}. {oferta['titulo'][:60]}... - {oferta['preco']}")
    
    asyncio.run(main())
