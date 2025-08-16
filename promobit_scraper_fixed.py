#!/usr/bin/env python3
"""
Módulo para busca de ofertas no site Promobit - VERSÃO CORRIGIDA

Este módulo implementa um scraper para buscar ofertas de produtos de tecnologia
no site Promobit, usando a API correta.
"""
import asyncio
import logging
import re
import json
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
import aiohttp
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Headers para simular um navegador
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Referer': 'https://www.promobit.com.br/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin'
}

# URLs da API do Promobit
API_BASE_URL = "https://api.promobit.com.br"
SEARCH_URL = f"{API_BASE_URL}/search"
CATEGORIES_URL = f"{API_BASE_URL}/categories"

# Categorias de interesse para produtos geek/tech
CATEGORIES = [
    'informatica',
    'eletronicos-audio-e-video',
    'games',
    'smartphones-tablets-e-telefones',
    'cameras-filmadoras-e-drones'
]

def extrair_preco(texto: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """
    Extrai preço atual, original e desconto de um texto de preço.
    
    Args:
        texto: Texto contendo os preços
        
    Returns:
        tuple: (preco_atual, preco_original, desconto)
    """
    # Encontra todos os valores numéricos no formato R$ X.XXX,XX
    precos = re.findall(r'R\$\s*([\d\.]+,\d{2})', texto)
    
    if not precos:
        return None, None, 0
    
    # Remove o símbolo R$ e espaços para padronização
    precos = [p.strip() for p in precos]
    
    # Se tiver apenas um preço, retorna ele como preço atual
    if len(precos) == 1:
        return precos[0], None, 0
    
    # Se tiver mais de um, assume que o primeiro é o preço original e o segundo o com desconto
    preco_original = precos[0]
    preco_atual = precos[1]
    
    # Calcula desconto
    try:
        original = float(preco_original.replace('.', '').replace(',', '.'))
        atual = float(preco_atual.replace('.', '').replace(',', '.'))
        if original > 0:
            desconto = int(((original - atual) / original) * 100)
        else:
            desconto = 0
    except:
        desconto = 0
    
    return preco_atual, preco_original, desconto

async def buscar_ofertas_promobit(
    session: aiohttp.ClientSession,
    max_paginas: int = 3,
    min_desconto: int = 10
) -> List[Dict[str, Any]]:
    """
    Busca ofertas no Promobit usando a API correta.
    
    Args:
        session: Sessão aiohttp para fazer as requisições
        max_paginas: Número máximo de páginas para buscar
        min_desconto: Percentual mínimo de desconto para considerar a oferta
        
    Returns:
        Lista de dicionários contendo as ofertas encontradas
    """
    ofertas = []
    
    try:
        # Primeiro, vamos tentar buscar ofertas da página principal
        logger.info("🔍 Buscando ofertas da página principal do Promobit")
        
        # Tenta acessar a página principal para obter cookies
        async with session.get("https://www.promobit.com.br/", headers=HEADERS, timeout=15) as response:
            if response.status != 200:
                logger.warning(f"Erro ao acessar página principal: HTTP {response.status}")
                return []
            
            # Agora tenta buscar ofertas usando a API
            for categoria in CATEGORIES[:max_paginas]:
                try:
                    logger.info(f"🔍 Buscando ofertas na categoria: {categoria}")
                    
                    # Parâmetros da busca
                    params = {
                        'category': categoria,
                        'page': 1,
                        'limit': 20,
                        'sort': 'relevance'
                    }
                    
                    # Faz requisição para a API
                    async with session.get(SEARCH_URL, params=params, headers=HEADERS, timeout=15) as api_response:
                        if api_response.status == 200:
                            try:
                                data = await api_response.json()
                                logger.info(f"✅ Dados recebidos da API para {categoria}")
                                
                                # Processa os dados da API
                                if 'offers' in data and isinstance(data['offers'], list):
                                    for offer in data['offers']:
                                        try:
                                            # Extrai informações da oferta
                                            titulo = offer.get('title', '')
                                            if not titulo or len(titulo) < 10:
                                                continue
                                            
                                            # Extrai preços
                                            preco_atual = offer.get('current_price', '')
                                            preco_original = offer.get('original_price', '')
                                            desconto = offer.get('discount_percentage', 0)
                                            
                                            # Se não tem desconto específico, calcula
                                            if not desconto and preco_original and preco_atual:
                                                try:
                                                    original = float(preco_original.replace('.', '').replace(',', '.'))
                                                    atual = float(preco_atual.replace('.', '').replace(',', '.'))
                                                    if original > 0:
                                                        desconto = int(((original - atual) / original) * 100)
                                                except:
                                                    desconto = 0
                                            
                                            # Filtra por desconto mínimo
                                            if desconto < min_desconto:
                                                continue
                                            
                                            # Extrai outras informações
                                            url_produto = offer.get('product_url', '')
                                            url_fonte = offer.get('offer_url', '')
                                            loja = offer.get('store_name', 'Desconhecida')
                                            imagem_url = offer.get('image_url', '')
                                            
                                            # Adiciona a oferta
                                            oferta = {
                                                'titulo': titulo,
                                                'url_produto': url_produto,
                                                'url_fonte': url_fonte,
                                                'preco': preco_atual,
                                                'preco_original': preco_original,
                                                'loja': loja,
                                                'fonte': 'Promobit',
                                                'imagem_url': imagem_url,
                                                'desconto': desconto,
                                                'data_coleta': datetime.now().isoformat()
                                            }
                                            
                                            # Verifica se a oferta já foi adicionada
                                            if not any(o['url_produto'] == oferta['url_produto'] for o in ofertas):
                                                ofertas.append(oferta)
                                                logger.debug(f"Oferta adicionada: {titulo} - {preco_atual}")
                                            
                                        except Exception as e:
                                            logger.error(f"Erro ao processar oferta: {e}")
                                            continue
                                            
                                else:
                                    logger.warning(f"Formato de dados inesperado para {categoria}")
                                    
                            except json.JSONDecodeError:
                                logger.warning(f"Resposta não é JSON válido para {categoria}")
                                continue
                                
                        else:
                            logger.warning(f"Erro na API para {categoria}: HTTP {api_response.status}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Erro ao processar categoria {categoria}: {e}")
                    continue
        
        # Se não conseguiu nada da API, tenta buscar da página principal
        if not ofertas:
            logger.info("🔄 Tentando buscar ofertas da página principal...")
            
            async with session.get("https://www.promobit.com.br/", headers=HEADERS, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Procura por ofertas na página principal
                    oferta_links = soup.find_all('a', href=re.compile(r'/oferta/'))
                    
                    for link in oferta_links[:20]:  # Limita a 20 ofertas
                        try:
                            href = link.get('href', '')
                            if not href:
                                continue
                                
                            # Constrói URL completa
                            if href.startswith('/'):
                                url_oferta = f"https://www.promobit.com.br{href}"
                            else:
                                url_oferta = href
                            
                            # Extrai título
                            titulo_elem = link.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div'])
                            if titulo_elem:
                                titulo = titulo_elem.get_text(strip=True)
                            else:
                                titulo = link.get_text(strip=True)
                            
                            if not titulo or len(titulo) < 10:
                                continue
                            
                            # Extrai preços do texto
                            link_text = link.get_text()
                            preco_atual, preco_original, desconto = extrair_preco(link_text)
                            
                            # Se não tem desconto específico, aceita a oferta mesmo assim
                            if desconto < min_desconto:
                                desconto = 0
                            
                            # Extrai imagem
                            img_elem = link.find('img')
                            imagem_url = img_elem.get('src', '') if img_elem else ''
                            
                            # Extrai a loja real do título ou URL
                            loja_real = 'Desconhecida'
                            
                            # Tenta extrair a loja do título (geralmente está no início)
                            if 'aliexpress.com' in titulo.lower():
                                loja_real = 'AliExpress'
                            elif 'amazon.com.br' in titulo.lower() or 'amazon.com' in titulo.lower():
                                loja_real = 'Amazon'
                            elif 'shopee.com.br' in titulo.lower() or 'shopee.com' in titulo.lower():
                                loja_real = 'Shopee'
                            elif 'magazineluiza.com.br' in titulo.lower() or 'magalu.com.br' in titulo.lower():
                                loja_real = 'Magazine Luiza'
                            elif 'mercadolivre.com.br' in titulo.lower():
                                loja_real = 'Mercado Livre'
                            elif 'kabum.com.br' in titulo.lower():
                                loja_real = 'Kabum'
                            elif 'dell.com.br' in titulo.lower():
                                loja_real = 'Dell'
                            elif 'lenovo.com.br' in titulo.lower():
                                loja_real = 'Lenovo'
                            elif 'acer.com.br' in titulo.lower():
                                loja_real = 'Acer'
                            elif 'asus.com.br' in titulo.lower():
                                loja_real = 'ASUS'
                            elif 'samsung.com.br' in titulo.lower():
                                loja_real = 'Samsung'
                            elif 'fastshop.com.br' in titulo.lower():
                                loja_real = 'Fast Shop'
                            elif 'webcontinental.com.br' in titulo.lower():
                                loja_real = 'Web Continental'
                            elif 'nike.com.br' in titulo.lower():
                                loja_real = 'Nike'
                            elif 'petz.com.br' in titulo.lower():
                                loja_real = 'Petz'
                            else:
                                # Se não conseguiu identificar, tenta extrair do domínio da URL
                                try:
                                    from urllib.parse import urlparse
                                    parsed_url = urlparse(url_oferta)
                                    domain = parsed_url.netloc.lower()
                                    if 'aliexpress' in domain:
                                        loja_real = 'AliExpress'
                                    elif 'amazon' in domain:
                                        loja_real = 'Amazon'
                                    elif 'shopee' in domain:
                                        loja_real = 'Shopee'
                                    elif 'magalu' in domain or 'magazineluiza' in domain:
                                        loja_real = 'Magazine Luiza'
                                    elif 'mercadolivre' in domain:
                                        loja_real = 'Mercado Livre'
                                    elif 'kabum' in domain:
                                        loja_real = 'Kabum'
                                    elif 'dell' in domain:
                                        loja_real = 'Dell'
                                    elif 'lenovo' in domain:
                                        loja_real = 'Lenovo'
                                    elif 'acer' in domain:
                                        loja_real = 'Acer'
                                    elif 'asus' in domain:
                                        loja_real = 'ASUS'
                                    elif 'samsung' in domain:
                                        loja_real = 'Samsung'
                                    elif 'fastshop' in domain:
                                        loja_real = 'Fast Shop'
                                    elif 'webcontinental' in domain:
                                        loja_real = 'Web Continental'
                                    elif 'nike' in domain:
                                        loja_real = 'Nike'
                                    elif 'petz' in domain:
                                        loja_real = 'Petz'
                                    else:
                                        loja_real = domain.replace('www.', '').replace('.com.br', '').replace('.com', '').title()
                                except:
                                    loja_real = 'Desconhecida'
                            
                            # Adiciona a oferta
                            oferta = {
                                'titulo': titulo,
                                'url_produto': url_oferta,
                                'url_fonte': url_oferta,
                                'preco': preco_atual or 'Preço não informado',
                                'preco_original': preco_original,
                                'loja': loja_real,
                                'fonte': 'Promobit',
                                'imagem_url': imagem_url,
                                'desconto': desconto,
                                'data_coleta': datetime.now().isoformat()
                            }
                            
                            # Verifica se a oferta já foi adicionada
                            if not any(o['url_produto'] == oferta['url_produto'] for o in ofertas):
                                ofertas.append(oferta)
                                logger.debug(f"Oferta da página principal adicionada: {titulo}")
                            
                        except Exception as e:
                            logger.error(f"Erro ao processar link da página principal: {e}")
                            continue
        
        logger.info(f"Busca concluída. Total de ofertas encontradas: {len(ofertas)}")
        return ofertas
        
    except Exception as e:
        logger.error(f"Erro inesperado ao buscar ofertas: {e}", exc_info=True)
        return []

async def main():
    """Função de teste para o módulo."""
    async with aiohttp.ClientSession() as session:
        ofertas = await buscar_ofertas_promobit(session, max_paginas=2)
        
        print(f"\n=== OFERTAS ENCONTRADAS ({len(ofertas)}) ===\n")
        
        for i, oferta in enumerate(ofertas[:5], 1):  # Mostra apenas as 5 primeiras para teste
            print(f"\n--- Oferta {i} ---")
            print(f"Título: {oferta['titulo']}")
            print(f"Loja: {oferta['loja']}")
            print(f"Preço: {oferta['preco']}")
            if oferta['preco_original']:
                print(f"Preço original: {oferta['preco_original']}")
            print(f"Desconto: {oferta['desconto']}%")
            print(f"URL: {oferta['url_produto']}")
            print(f"Fonte: {oferta['fonte']}")
            if oferta['imagem_url']:
                print(f"Imagem: {oferta['imagem_url']}")
            print("-" * 50)

if __name__ == "__main__":
    # Configura logging para debug
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    
    # Executa o teste
    asyncio.run(main())
