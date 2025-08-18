#!/usr/bin/env python3
"""
Módulo para busca de ofertas no site Pelando - VERSÃO SIMPLES

Este módulo implementa um scraper para buscar ofertas de produtos de tecnologia
no site Pelando, usando aiohttp e BeautifulSoup.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
import aiohttp
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Headers para simular um navegador
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}


def extrair_preco(texto: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extrai preço atual e original de um texto de preço do Pelando.

    Args:
        texto: Texto contendo os preços (ex: "R$ 1.199,99 R$ 999,99")

    Returns:
        tuple: (preco_atual, preco_original) ou (preco_atual, None) se não houver desconto
    """
    # Encontra todos os valores numéricos no formato R$ X.XXX,XX
    precos = re.findall(r"R\$\s*([\d\.]+,\d{2})", texto)

    if not precos:
        return None, None

    # Remove o símbolo R$ e espaços para padronização
    precos = [p.strip() for p in precos]

    # Se tiver apenas um preço, retorna ele como preço atual
    if len(precos) == 1:
        return precos[0], None

    # Se tiver mais de um, assume que o primeiro é o preço original e o segundo o com desconto
    return precos[1], precos[0]


async def buscar_ofertas_pelando_simple(
    max_paginas: int = 2, min_desconto: int = 10
) -> List[Dict[str, Any]]:
    """
    Busca ofertas no Pelando usando aiohttp.

    Args:
        max_paginas: Número máximo de páginas para buscar
        min_desconto: Percentual mínimo de desconto para considerar a oferta

    Returns:
        Lista de dicionários contendo as ofertas encontradas
    """
    ofertas = []

    try:
        # URLs das páginas principais do Pelando
        urls = ["https://www.pelando.com.br/", "https://www.pelando.com.br/hot"]

        async with aiohttp.ClientSession(headers=HEADERS) as session:
            for url in urls[:max_paginas]:
                try:
                    logger.info(f"🔍 Buscando ofertas em: {url}")

                    async with session.get(url, timeout=30) as response:
                        if response.status != 200:
                            logger.warning(
                                f"⚠️ Erro ao acessar {url}: {response.status}"
                            )
                            continue

                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")

                        # Salva HTML para debug se necessário
                        if len(ofertas) == 0:
                            with open(
                                "pelando_debug_simple.html", "w", encoding="utf-8"
                            ) as f:
                                f.write(html)
                            logger.info(
                                "✅ HTML salvo em pelando_debug_simple.html para debug"
                            )

                        # Busca por produtos usando seletores mais genéricos
                        produtos = []

                        # Seletores específicos do Pelando baseados no HTML analisado
                        seletores = [
                            '[class*="default-deal-card"]',
                            '[class*="comment-deal-card"]',
                            '[class*="deal-card"]',
                            '[class*="card"]',
                        ]

                        for seletor in seletores:
                            produtos = soup.select(seletor)
                            if produtos and len(produtos) > 5:  # Pelo menos 5 produtos
                                logger.info(
                                    f"✅ Encontrados {len(produtos)} produtos com seletor: {seletor}"
                                )
                                break

                        if not produtos:
                            logger.warning(f"Nenhum produto encontrado em {url}")
                            continue

                        logger.info(
                            f"🔍 Encontrados {len(produtos)} produtos para análise em {url}"
                        )

                        for produto in produtos[:20]:  # Limita a 20 produtos por página
                            try:
                                oferta = extrair_oferta_produto(produto)
                                if oferta:
                                    # Verifica se a oferta já foi adicionada
                                    if not any(
                                        o["url_produto"] == oferta["url_produto"]
                                        for o in ofertas
                                    ):
                                        ofertas.append(oferta)
                                        logger.debug(
                                            f"Oferta adicionada: {oferta['titulo']} - {oferta['preco']}"
                                        )

                            except Exception as e:
                                logger.warning(f"⚠️ Erro ao extrair produto: {e}")
                                continue

                            # Delay entre produtos
                            await asyncio.sleep(0.1)

                        # Delay entre páginas
                        await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"❌ Erro ao processar {url}: {e}")
                    continue

        logger.info(f"✅ {len(ofertas)} ofertas extraídas com sucesso")
        return ofertas

    except Exception as e:
        logger.error(f"❌ Erro inesperado ao buscar ofertas: {e}", exc_info=True)
        return []


def extrair_oferta_produto(produto_element) -> Optional[Dict[str, Any]]:
    """Extrai informações de uma oferta de produto do Pelando."""
    try:
        # Título do produto - usa seletores específicos do Pelando
        titulo_elem = (
            produto_element.select_one('[class*="title"]')
            or produto_element.find(["h1", "h2", "h3", "h4", "h5", "h6"])
            or produto_element.find("a", title=True)
            or produto_element.find("a", href=True)
        )

        if not titulo_elem:
            return None

        titulo = titulo_elem.get_text(strip=True)
        if not titulo or len(titulo) < 10:
            return None

        # URL do produto
        url_produto = ""
        if titulo_elem.name == "a":
            url_produto = titulo_elem.get("href", "")
        else:
            link_elem = produto_element.find("a", href=True)
            if link_elem:
                url_produto = link_elem.get("href", "")

        # Garante que a URL completa está sendo usada
        if url_produto and not url_produto.startswith("http"):
            url_produto = f"https://www.pelando.com.br{url_produto}"

        # Preço - usa seletores específicos do Pelando
        preco_elem = (
            produto_element.select_one('[class*="price"]')
            or produto_element.find(
                ["span", "div"], class_=re.compile(r"price|preco|valor")
            )
            or produto_element.find(string=re.compile(r"R\$\s*\d+"))
        )

        preco_atual, preco_original = None, None
        if preco_elem:
            if hasattr(preco_elem, "get_text"):
                preco_texto = preco_elem.get_text(strip=True)
            else:
                preco_texto = str(preco_elem)
            preco_atual, preco_original = extrair_preco(preco_texto)

        # Se não conseguiu extrair preço, tenta do texto geral
        if not preco_atual:
            texto_geral = produto_element.get_text()
            preco_atual, preco_original = extrair_preco(texto_geral)

        # Se não conseguiu extrair preço, pula para a próxima oferta
        if not preco_atual:
            return None

        # Extrai URL da imagem
        img_elem = produto_element.find("img")
        imagem_url = ""
        if img_elem:
            imagem_url = img_elem.get("src", "")
            if imagem_url.startswith("//"):
                imagem_url = f"https:{imagem_url}"

        # Extrai porcentagem de desconto
        card_text = produto_element.get_text()
        desconto = 0
        desconto_match = re.search(
            r"(\d+)%?\s*off|(\d+)%?\s*desconto|(\d+)%?\s*menos",
            card_text,
            re.IGNORECASE,
        )
        if desconto_match:
            for group in desconto_match.groups():
                if group:
                    desconto = int(group)
                    break

        # Extrai nome da loja
        loja_elem = produto_element.find(
            ["span", "div"], class_=re.compile(r"store|loja|vendor")
        ) or produto_element.find("img", alt=re.compile(r"logo|store"))

        loja = "Pelando"
        if loja_elem:
            if hasattr(loja_elem, "get_text"):
                loja_texto = loja_elem.get_text(strip=True)
            else:
                loja_texto = loja_elem.get("alt", "")

            if loja_texto and len(loja_texto) > 1:
                loja = loja_texto

        # Cria a oferta
        oferta = {
            "titulo": titulo,
            "url_produto": url_produto or "https://www.pelando.com.br",
            "url_fonte": "https://www.pelando.com.br",
            "preco": preco_atual,
            "preco_original": preco_original,
            "loja": loja,
            "fonte": "Pelando",
            "imagem_url": imagem_url,
            "desconto": desconto,
            "data_coleta": datetime.now().isoformat(),
        }

        return oferta

    except Exception as e:
        logger.error(f"Erro ao extrair oferta: {e}")
        return None


async def main():
    """Função de teste para o módulo."""
    ofertas = await buscar_ofertas_pelando_simple(max_paginas=2)

    print(f"\n=== OFERTAS ENCONTRADAS ({len(ofertas)}) ===\n")

    for i, oferta in enumerate(
        ofertas[:5], 1
    ):  # Mostra apenas as 5 primeiras para teste
        print(f"\n--- Oferta {i} ---")
        print(f"Título: {oferta['titulo']}")
        print(f"Loja: {oferta['loja']}")
        print(f"Preço: R$ {oferta['preco']}")
        if oferta["preco_original"]:
            print(f"Preço original: R$ {oferta['preco_original']}")
        print(f"Desconto: {oferta['desconto']}%")
        print(f"URL: {oferta['url_produto']}")
        print(f"Fonte: {oferta['fonte']}")
        if oferta["imagem_url"]:
            print(f"Imagem: {oferta['imagem_url']}")
        print("-" * 50)


if __name__ == "__main__":
    # Configura logging para debug
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

    # Executa o teste
    asyncio.run(main())
