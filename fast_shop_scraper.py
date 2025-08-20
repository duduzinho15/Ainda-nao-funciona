#!/usr/bin/env python3
"""
Scraper para Fast Shop - Coleta ofertas e promoções
"""

import time
import logging
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FastShopScraper:
    """Scraper para Fast Shop usando aiohttp"""

    def __init__(self):
        self.base_url = "https://www.fastshop.com.br"
        self.ofertas_url = "https://www.fastshop.com.br/ofertas"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def buscar_ofertas(self, max_paginas: int = 2) -> List[Dict[str, Any]]:
        """
        Busca ofertas na Fast Shop
        
        Args:
            max_paginas: Número máximo de páginas para buscar
            
        Returns:
            Lista de ofertas encontradas
        """
        ofertas = []
        
        try:
            logger.info("🔍 Iniciando busca de ofertas na Fast Shop")
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                for pagina in range(1, max_paginas + 1):
                    try:
                        # URL da página de ofertas
                        if pagina == 1:
                            url = self.ofertas_url
                        else:
                            url = f"{self.ofertas_url}?page={pagina}"
                        
                        logger.info(f"📄 Acessando página {pagina}: {url}")
                        
                        async with session.get(url, timeout=30) as response:
                            if response.status == 200:
                                html = await response.text()
                                page_ofertas = self._extrair_ofertas_da_pagina(html)
                                ofertas.extend(page_ofertas)
                                
                                logger.info(f"✅ Página {pagina}: {len(page_ofertas)} ofertas encontradas")
                                
                                # Delay entre requisições
                                await asyncio.sleep(1)
                            else:
                                logger.warning(f"⚠️ Página {pagina}: Status {response.status}")
                                
                    except Exception as e:
                        logger.error(f"❌ Erro na página {pagina}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Erro geral na busca: {e}")
            
        logger.info(f"🎯 Total de ofertas encontradas: {len(ofertas)}")
        return ofertas

    def _extrair_ofertas_da_pagina(self, html: str) -> List[Dict[str, Any]]:
        """Extrai ofertas do HTML da página"""
        ofertas = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Procura por produtos em oferta
            produtos = soup.find_all('div', class_=re.compile(r'product|item|card|product-item'))
            
            for produto in produtos[:20]:  # Limita a 20 produtos por página
                try:
                    oferta = self._extrair_dados_produto(produto)
                    if oferta:
                        ofertas.append(oferta)
                except Exception as e:
                    logger.debug(f"Erro ao extrair produto: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Erro ao extrair ofertas da página: {e}")
            
        return ofertas

    def _extrair_dados_produto(self, produto) -> Optional[Dict[str, Any]]:
        """Extrai dados de um produto individual"""
        try:
            # Título do produto
            titulo_elem = produto.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|product'))
            titulo = titulo_elem.get_text(strip=True) if titulo_elem else "Produto Fast Shop"
            
            # Preço
            preco_elem = produto.find(['span', 'div'], class_=re.compile(r'price|value|cost'))
            preco = preco_elem.get_text(strip=True) if preco_elem else "Preço sob consulta"
            
            # Preço original (se houver desconto)
            preco_original_elem = produto.find(['span', 'div'], class_=re.compile(r'original|old|before'))
            preco_original = preco_original_elem.get_text(strip=True) if preco_original_elem else None
            
            # URL do produto
            url_elem = produto.find('a', href=True)
            url = urljoin(self.base_url, url_elem['href']) if url_elem else None
            
            # Imagem
            img_elem = produto.find('img')
            imagem_url = urljoin(self.base_url, img_elem['src']) if img_elem and img_elem.get('src') else None
            
            # Verifica se tem dados mínimos
            if not titulo or titulo == "Produto Fast Shop":
                return None
                
            return {
                'titulo': titulo,
                'loja': 'Fast Shop',
                'preco': preco,
                'preco_original': preco_original,
                'url': url,
                'imagem_url': imagem_url,
                'fonte': 'fast_shop_scraper'
            }
            
        except Exception as e:
            logger.debug(f"Erro ao extrair dados do produto: {e}")
            return None


async def buscar_ofertas_fast_shop(max_paginas: int = 2) -> List[Dict[str, Any]]:
    """
    Função principal para buscar ofertas na Fast Shop
    
    Args:
        max_paginas: Número máximo de páginas para buscar
        
    Returns:
        Lista de ofertas encontradas
    """
    scraper = FastShopScraper()
    return await scraper.buscar_ofertas(max_paginas)


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
        # Buscar ofertas da Fast Shop
        ofertas = await buscar_ofertas_fast_shop(max_paginas=2)
        
        # Adicionar metadados
        for oferta in ofertas:
            oferta['fonte'] = 'fast_shop_scraper'
            oferta['periodo'] = periodo
            oferta['timestamp'] = time.time()
        
        return ofertas
        
    except Exception as e:
        logger.error(f"❌ Erro na função get_ofertas: {e}")
        return []

# Configurações para o scraper registry
priority = 80  # Prioridade alta
rate_limit = 0.5  # 0.5 requisições por segundo
description = "Scraper para Fast Shop - Ofertas e promoções"


# Teste direto
if __name__ == "__main__":
    async def main():
        print("🔍 Testando scraper da Fast Shop...")
        print("=" * 60)
        
        try:
            ofertas = await buscar_ofertas_fast_shop(max_paginas=1)
            
            print(f"\n✅ {len(ofertas)} ofertas encontradas!")
            
            for i, oferta in enumerate(ofertas[:5], 1):
                print(f"\n{i}. {oferta['titulo'][:60]}...")
                print(f"   Preço: {oferta['preco']}")
                if oferta.get('preco_original'):
                    print(f"   De: {oferta['preco_original']}")
                print(f"   Loja: {oferta['loja']}")
                
        except Exception as e:
            print(f"❌ Erro durante o teste: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(main())
