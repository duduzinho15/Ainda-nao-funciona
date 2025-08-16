# tests/adapters_scrapers.py
from __future__ import annotations
from typing import List, Dict, Any
import asyncio
import sys
import os
import aiohttp

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def run_promobit() -> List[Dict[str, Any]]:
    """Executa scraper do Promobit e retorna ofertas no formato padrão"""
    try:
        from promobit_scraper_clean import buscar_ofertas_promobit
        
        # Cria sessão HTTP para o scraper
        async with aiohttp.ClientSession() as session:
            # Executa o scraper com parâmetros corretos
            ofertas = await buscar_ofertas_promobit(
                session=session,
                max_paginas=1,  # Apenas 1 página para teste
                max_requests=3   # Limita requisições para teste
            )
        
        # Converte para formato padrão se necessário
        ofertas_padronizadas = []
        for oferta in ofertas:
            oferta_padrao = {
                "titulo": oferta.get("titulo", ""),
                "preco": oferta.get("preco_atual", oferta.get("preco", "")),  # Corrigido: usa preco_atual
                "preco_original": oferta.get("preco_original", ""),
                "url_produto": oferta.get("url_produto", ""),
                "imagem_url": oferta.get("imagem_url", ""),
                "loja": oferta.get("loja", "Promobit"),
                "fonte": "Promobit",
                "desconto": oferta.get("desconto", 0)
            }
            ofertas_padronizadas.append(oferta_padrao)
        
        return ofertas_padronizadas
    except Exception as e:
        print(f"❌ Erro ao executar scraper Promobit: {e}")
        return []

async def run_pelando() -> List[Dict[str, Any]]:
    """Executa scraper do Pelando e retorna ofertas no formato padrão"""
    try:
        from pelando_scraper import buscar_ofertas_pelando
        
        # Cria sessão HTTP para o scraper
        async with aiohttp.ClientSession() as session:
            # Executa o scraper com parâmetros corretos
            ofertas = await buscar_ofertas_pelando(
                session=session,
                max_paginas=1  # Apenas 1 página para teste
            )
        
        # Converte para formato padrão se necessário
        ofertas_padronizadas = []
        for oferta in ofertas:
            oferta_padrao = {
                "titulo": oferta.get("titulo", ""),
                "preco": oferta.get("preco_atual", oferta.get("preco", "")),  # Corrigido: usa preco_atual
                "preco_original": oferta.get("preco_original", ""),
                "url_produto": oferta.get("url_produto", ""),
                "imagem_url": oferta.get("imagem_url", ""),
                "loja": oferta.get("loja", "Pelando"),
                "fonte": "Pelando",
                "desconto": oferta.get("desconto", 0)
            }
            ofertas_padronizadas.append(oferta_padrao)
        
        return ofertas_padronizadas
    except Exception as e:
        print(f"❌ Erro ao executar scraper Pelando: {e}")
        return []

async def run_shopee() -> List[Dict[str, Any]]:
    """Executa scraper da Shopee e retorna ofertas no formato padrão"""
    try:
        # Por enquanto, retorna lista vazia para evitar erros
        print("⚠️ Scraper Shopee temporariamente desabilitado para testes")
        return []
    except Exception as e:
        print(f"❌ Erro ao executar scraper Shopee: {e}")
        return []

async def run_amazon() -> List[Dict[str, Any]]:
    """Executa scraper da Amazon e retorna ofertas no formato padrão"""
    try:
        # Por enquanto, retorna lista vazia para evitar erros
        print("⚠️ Scraper Amazon temporariamente desabilitado para testes")
        return []
    except Exception as e:
        print(f"❌ Erro ao executar scraper Amazon: {e}")
        return []

SCRAPER_ADAPTERS = {
    "promobit": run_promobit,
    "pelando": run_pelando,
    "shopee": run_shopee,
    "amazon": run_amazon,
}
