#!/usr/bin/env python3
"""
Módulo para busca de ofertas no site Pelando usando Selenium - VERSÃO CORRIGIDA

Este módulo implementa um scraper para buscar ofertas de produtos de tecnologia
no site Pelando, lidando com conteúdo carregado dinamicamente via JavaScript.
"""
import asyncio
import logging
import re
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# URLs para buscar ofertas
URLS = [
    "https://www.pelando.com.br/",
    "https://www.pelando.com.br/ofertas"
]

def setup_chrome_driver():
    """Configura o driver do Chrome com opções otimizadas"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Executa em background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        logger.error(f"❌ Erro ao configurar driver do Chrome: {e}")
        return None

async def buscar_ofertas_pelando_selenium() -> List[Dict[str, Any]]:
    """
    Busca ofertas no site Pelando usando Selenium para lidar com conteúdo dinâmico.
    
    Returns:
        Lista de ofertas encontradas
    """
    ofertas = []
    
    try:
        logger.info("🚀 Iniciando scraper do Pelando com Selenium")
        
        # Configura driver
        driver = setup_chrome_driver()
        if not driver:
            logger.error("❌ Não foi possível configurar o driver do Chrome")
            return []
        
        try:
            for url in URLS:
                try:
                    logger.info(f"🔍 Acessando: {url}")
                    driver.get(url)
                    
                    # Aguarda carregamento da página
                    time.sleep(5)
                    
                    # Aguarda elementos de oferta aparecerem
                    try:
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="default-deal-card"]'))
                        )
                        logger.info("✅ Elementos de oferta carregados")
                    except TimeoutException:
                        logger.warning("⚠️ Timeout aguardando elementos de oferta")
                    
                    # Aguarda um pouco mais para garantir carregamento completo
                    time.sleep(3)
                    
                    # Obtém HTML da página
                    html = driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Salva HTML para debug se necessário
                    if len(ofertas) == 0:
                        with open('pelando_selenium_debug.html', 'w', encoding='utf-8') as f:
                            f.write(html)
                        logger.info("✅ HTML salvo em pelando_selenium_debug.html para debug")
                    
                    # Busca por produtos usando seletores específicos do Pelando
                    produtos = []
                    
                    # Seletores específicos do Pelando baseados no HTML analisado
                    seletores = [
                        '[class*="default-deal-card"]',
                        '[class*="comment-deal-card"]',
                        '[class*="deal-card"]'
                    ]
                    
                    for seletor in seletores:
                        produtos = soup.select(seletor)
                        if produtos and len(produtos) > 5:  # Pelo menos 5 produtos
                            logger.info(f"✅ Encontrados {len(produtos)} produtos com seletor: {seletor}")
                            break
                    
                    if not produtos:
                        logger.warning(f"Nenhum produto encontrado em {url}")
                        continue
                    
                    logger.info(f"🔍 Encontrados {len(produtos)} produtos para análise em {url}")
                    
                    for produto in produtos[:20]:  # Limita a 20 produtos por página
                        try:
                            oferta = extrair_oferta_produto(produto)
                            if oferta:
                                # Verifica se a oferta já foi adicionada
                                if not any(o['url_produto'] == oferta['url_produto'] for o in ofertas):
                                    ofertas.append(oferta)
                                    logger.debug(f"Oferta adicionada: {oferta['titulo']} - {oferta['preco']}")
                            
                        except Exception as e:
                            logger.warning(f"⚠️ Erro ao extrair produto: {e}")
                            continue
                        
                        # Delay entre produtos
                        await asyncio.sleep(0.1)
                    
                    # Delay entre páginas
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao processar {url}: {e}")
                    continue
        
        finally:
            # Fecha o driver
            driver.quit()
            logger.info("✅ Driver do Chrome fechado")
        
        logger.info(f"✅ {len(ofertas)} ofertas extraídas com sucesso")
        return ofertas
        
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao buscar ofertas: {e}", exc_info=True)
        return []

def extrair_oferta_produto(produto_element) -> Optional[Dict[str, Any]]:
    """Extrai informações de uma oferta de produto do Pelando."""
    try:
        # Título do produto - usa seletores específicos do Pelando
        titulo_elem = produto_element.select_one('[class*="title"]') or \
                     produto_element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or \
                     produto_element.find('a', title=True) or \
                     produto_element.find('a', href=True)
        
        if not titulo_elem:
            return None
        
        titulo = titulo_elem.get_text(strip=True)
        if not titulo or len(titulo) < 10:
            return None
        
        # URL do produto
        url_produto = ""
        if titulo_elem.name == 'a':
            url_produto = titulo_elem.get('href', '')
        else:
            link_elem = produto_element.find('a', href=True)
            if link_elem:
                url_produto = link_elem.get('href', '')
        
        # Garante que a URL completa está sendo usada
        if url_produto and not url_produto.startswith('http'):
            url_produto = f"https://www.pelando.com.br{url_produto}"
        
        # Preço - usa seletores específicos do Pelando
        preco_elem = produto_element.select_one('[class*="price"]') or \
                    produto_element.find(['span', 'div'], class_=re.compile(r'price|preco|valor')) or \
                    produto_element.find(string=re.compile(r'R\$\s*\d+'))
        
        preco_atual, preco_original = None, None
        if preco_elem:
            if hasattr(preco_elem, 'get_text'):
                preco_texto = preco_elem.get_text(strip=True)
            else:
                preco_texto = str(preco_elem)
            
            # Extrai preços usando regex
            precos = re.findall(r'R\$\s*([\d\.]+,\d{2})', preco_texto)
            if len(precos) >= 2:
                preco_atual = precos[1]  # Preço com desconto
                preco_original = precos[0]  # Preço original
            elif len(precos) == 1:
                preco_atual = precos[0]
        
        # Se não conseguiu extrair preço, tenta do texto geral
        if not preco_atual:
            texto_geral = produto_element.get_text()
            precos = re.findall(r'R\$\s*([\d\.]+,\d{2})', texto_geral)
            if len(precos) >= 2:
                preco_atual = precos[1]
                preco_original = precos[0]
            elif len(precos) == 1:
                preco_atual = precos[0]
        
        # Loja
        loja_elem = produto_element.select_one('[class*="store"]') or \
                   produto_element.find('a', class_=re.compile(r'store|loja'))
        
        loja = "Pelando"
        if loja_elem:
            loja_texto = loja_elem.get_text(strip=True)
            if loja_texto and len(loja_texto) > 1:
                loja = loja_texto
        
        # Imagem
        img_elem = produto_element.select_one('img')
        imagem_url = ""
        if img_elem:
            src = img_elem.get('src', '')
            if src.startswith('//'):
                imagem_url = f"https:{src}"
            elif src.startswith('/'):
                imagem_url = f"https://www.pelando.com.br{src}"
            else:
                imagem_url = src
        
        # Cria a oferta
        oferta = {
            'titulo': titulo,
            'url_produto': url_produto or "https://www.pelando.com.br",
            'url_fonte': "https://www.pelando.com.br",
            'preco': preco_atual or 'Preço não informado',
            'preco_original': preco_original,
            'loja': loja,
            'fonte': 'Pelando',
            'imagem_url': imagem_url,
            'data_coleta': datetime.now().isoformat()
        }
        
        return oferta
        
    except Exception as e:
        logger.error(f"Erro ao extrair oferta: {e}")
        return None

async def main():
    """Função de teste para o módulo."""
    ofertas = await buscar_ofertas_pelando_selenium()
    
    print(f"\n=== OFERTAS ENCONTRADAS ({len(ofertas)}) ===\n")
    
    for i, oferta in enumerate(ofertas[:5], 1):  # Mostra apenas as 5 primeiras para teste
        print(f"\n--- Oferta {i} ---")
        print(f"Título: {oferta['titulo']}")
        print(f"Loja: {oferta['loja']}")
        print(f"Preço: {oferta['preco']}")
        if oferta['preco_original']:
            print(f"Preço original: {oferta['preco_original']}")
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
