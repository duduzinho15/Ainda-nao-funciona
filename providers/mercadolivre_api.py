"""
Provider da API do Mercado Livre.
Usa endpoint público de busca para coletar ofertas.
"""

import os
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from urllib.parse import urlencode
import json


# Configurações
name = "mercadolivre_api"
priority = 20
rate_limit = 2.0  # 2 requests por segundo
retry_count = 3
retry_delay = 1.0

# URLs base
BASE_URL = "https://api.mercadolibre.com"
SEARCH_URL = f"{BASE_URL}/sites/MLB/search"
DOMAIN = "api.mercadolibre.com"

# Headers padrão
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# Categorias populares para busca
POPULAR_CATEGORIES = [
    "MLB1000",  # Eletrônicos, Áudio e Vídeo
    "MLB1144",  # Games
    "MLB1039",  # Casa, Móveis e Decoração
    "MLB1051",  # Esportes e Fitness
    "MLB1196",  # Moda
    "MLB1182",  # Livros, Revistas e Comics
    "MLB1168",  # Bebês
    "MLB1132",  # Ferramentas e Construção
    "MLB1105",  # Jardim
    "MLB1071"   # Automóveis
]


def enabled() -> bool:
    """Verifica se o provider está habilitado."""
    # Sempre habilitado - API pública
    return True


async def get_ofertas(periodo: str) -> List[Dict[str, Any]]:
    """
    Coleta ofertas do Mercado Livre via API pública.
    
    Args:
        periodo: Período para coleta (24h, 7d, 30d, all)
        
    Returns:
        Lista de ofertas encontradas
    """
    logger = logging.getLogger(f"scraper.{name}")
    logger.info(f"🔄 Iniciando coleta de ofertas para período: {periodo}")
    
    try:
        # Configurar período de busca
        search_params = _get_search_params(periodo)
        
        # Coletar ofertas de categorias populares
        all_ofertas = []
        
        for category_id in POPULAR_CATEGORIES[:5]:  # Limitar a 5 categorias para evitar rate limit
            try:
                logger.info(f"📡 Buscando na categoria {category_id}")
                
                # Buscar ofertas na categoria
                category_ofertas = await _search_category(category_id, search_params)
                
                if category_ofertas:
                    all_ofertas.extend(category_ofertas)
                    logger.info(f"✅ Categoria {category_id}: {len(category_ofertas)} ofertas")
                
                # Rate limiting entre categorias
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"⚠️ Erro na categoria {category_id}: {e}")
                continue
        
        # Remover duplicatas por ID
        unique_ofertas = _remove_duplicates(all_ofertas)
        
        logger.info(f"🎯 Coleta concluída: {len(unique_ofertas)} ofertas únicas")
        return unique_ofertas
        
    except Exception as e:
        logger.error(f"❌ Erro geral na coleta: {e}")
        return []


def _get_search_params(periodo: str) -> Dict[str, Any]:
    """Gera parâmetros de busca baseados no período."""
    params = {
        "limit": 50,  # Máximo por categoria
        "sort": "price_asc",  # Ordenar por preço crescente
        "condition": "new",  # Produtos novos
        "shipping_mode": "fulfillment",  # Fulfillment (entrega rápida)
    }
    
    # Adicionar filtros de período se aplicável
    if periodo == "24h":
        # Para 24h, buscar produtos com promoções recentes
        params["has_pictures"] = "yes"
        params["shipping_mode"] = "fulfillment"
    elif periodo == "7d":
        # Para 7 dias, buscar produtos em destaque
        params["has_pictures"] = "yes"
    elif periodo == "30d":
        # Para 30 dias, buscar produtos populares
        params["has_pictures"] = "yes"
    
    return params


async def _search_category(category_id: str, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Busca ofertas em uma categoria específica."""
    logger = logging.getLogger(f"scraper.{name}")
    
    # Adicionar categoria aos parâmetros
    params = search_params.copy()
    params["category"] = category_id
    
    try:
        # Fazer requisição para a API
        async with aiohttp.ClientSession() as session:
            url = f"{SEARCH_URL}?{urlencode(params)}"
            
            async with session.get(url, headers=DEFAULT_HEADERS) as response:
                if response.status == 200:
                    data = await response.json()
                    return _parse_search_results(data, category_id)
                else:
                    logger.warning(f"⚠️ Status {response.status} para categoria {category_id}")
                    return []
                    
    except Exception as e:
        logger.error(f"❌ Erro ao buscar categoria {category_id}: {e}")
        return []


def _parse_search_results(data: Dict[str, Any], category_id: str) -> List[Dict[str, Any]]:
    """Parse dos resultados da busca."""
    ofertas = []
    
    try:
        results = data.get("results", [])
        
        for item in results:
            try:
                # Extrair informações básicas
                title = item.get("title", "")
                price = item.get("price", 0)
                permalink = item.get("permalink", "")
                thumbnail = item.get("thumbnail", "")
                seller_id = item.get("seller", {}).get("id", "")
                seller_name = item.get("seller", {}).get("eshop", {}).get("nickname", "Mercado Livre")
                
                # Verificar se é uma oferta válida
                if not title or not price or not permalink:
                    continue
                
                # Criar objeto de oferta
                oferta = {
                    "titulo": title,
                    "preco": float(price),
                    "loja": seller_name or "Mercado Livre",
                    "url": permalink,
                    "imagem_url": thumbnail,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "categoria_id": category_id,
                    "vendedor_id": seller_id,
                    "fonte": name
                }
                
                ofertas.append(oferta)
                
            except Exception as e:
                # Continuar com próximo item se houver erro
                continue
        
    except Exception as e:
        logging.getLogger(f"scraper.{name}").error(f"❌ Erro ao fazer parse dos resultados: {e}")
    
    return ofertas


def _remove_duplicates(ofertas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove ofertas duplicadas baseado na URL."""
    seen_urls = set()
    unique_ofertas = []
    
    for oferta in ofertas:
        url = oferta.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_ofertas.append(oferta)
    
    return unique_ofertas


# Variáveis de ambiente necessárias (nenhuma para API pública)
REQUIRED_ENV_VARS = []


# Teste local (se executado diretamente)
if __name__ == "__main__":
    async def test():
        print("🧪 Testando provider do Mercado Livre...")
        ofertas = await get_ofertas("7d")
        print(f"✅ Encontradas {len(ofertas)} ofertas")
        
        if ofertas:
            print("\n📋 Amostras:")
            for i, oferta in enumerate(ofertas[:3]):
                print(f"  {i+1}. {oferta['titulo'][:50]}... - R$ {oferta['preco']:.2f}")
    
    asyncio.run(test())
