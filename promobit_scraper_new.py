"""
Módulo para busca de ofertas no site Promobit.

Este módulo implementa um scraper para buscar ofertas de produtos de informática
no site Promobit, com tratamento de erros e anti-bloqueio.
"""
import asyncio
import logging
import random
import re
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

import aiohttp
import aiohttp.client_exceptions
from bs4 import BeautifulSoup

# Configuração de logging
logger = logging.getLogger('promobit_scraper')
logger.setLevel(logging.INFO)

# Cria handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('promobit_scraper.log', encoding='utf-8')

# Define formato
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Adiciona handlers ao logger
if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# User Agents para rotação
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
]

# Headers base para as requisições
BASE_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

# URLs base para busca de ofertas
BASE_URL = "https://www.promobit.com.br/"
CATEGORIAS = {
    'informatica': 'ofertas/informatica/',
    'eletronicos': 'ofertas/eletronicos/',
    'games': 'ofertas/games/',
    'celulares': 'ofertas/celulares/'
}

# Lista de palavras-chave para filtrar ofertas relevantes
PALAVRAS_CHAVE = [
    'notebook', 'laptop', 'ultrabook', 'macbook', 'chromebook',
    'ssd', 'hd', 'disco rígido', 'nvme', 'm.2',
    'memória ram', 'memoria ram', 'ddr4', 'ddr5',
    'placa de vídeo', 'placa de video', 'rtx', 'gtx', 'radeon',
    'processador', 'ryzen', 'core i5', 'core i7', 'core i9',
    'monitor', '144hz', '240hz', '4k', 'ultrawide',
    'teclado mecânico', 'teclado mecanico',
    'mouse gamer', 'mouse sem fio',
    'headset', 'fone de ouvido', 'headphone',
    'webcam', 'câmera web', 'camera web',
    'impressora', 'scanner', 'roteador', 'switch', 'hub',
    'nobreak', 'estabilizador', 'fonte', 'gabinete',
    'water cooler', 'cooler', 'ventoinha', 'fan',
    'cadeira gamer', 'cadeira ergonômica', 'cadeira ergonomica',
    'mesa digitalizadora', 'tablet', 'ipad', 'galaxy tab',
    'carregador', 'bateria', 'power bank', 'cabo', 'adaptador',
    'dock station', 'hub usb', 'ssd externo', 'hd externo',
    'pen drive', 'cartão de memória', 'cartao de memoria',
    'leitor de cartão', 'leitor de cartao', 'hub usb c',
    'carregador notebook', 'carregador usb c', 'cabo hdmi', 'cabo displayport'
]

def extrair_preco(texto: str) -> tuple:
    """
    Extrai preço atual, original e desconto de um texto de preço.
    
    Args:
        texto: Texto contendo os preços (ex: "R$ 1.199,99 R$ 999,99 20% OFF")
        
    Returns:
        tuple: (preco_atual, preco_original, desconto) ou (preco_atual, None, None) se não houver desconto
    """
    try:
        # Remove espaços extras e quebras de linha
        texto = ' '.join(texto.split())
        
        # Padrão para preço atual e original (ex: R$ 1.199,99 R$ 999,99 20% OFF)
        padrao_com_desconto = r'R\$\s*([\d.,]+).*?R\$\s*([\d.,]+).*?(\d+)%'
        # Padrão para apenas preço atual (sem desconto)
        padrao_sem_desconto = r'R\$\s*([\d.,]+)'
        
        match = re.search(padrao_com_desconto, texto, re.IGNORECASE)
        
        if match:
            # Extrai preço atual, original e desconto
            preco_atual = match.group(1).replace('.', '').replace(',', '.')
            preco_original = match.group(2).replace('.', '').replace(',', '.')
            desconto = int(match.group(3))
            return (preco_atual, preco_original, desconto)
        else:
            # Tenta extrair apenas o preço atual
            match = re.search(padrao_sem_desconto, texto, re.IGNORECASE)
            if match:
                preco_atual = match.group(1).replace('.', '').replace(',', '.')
                return (preco_atual, None, None)
        
        return (None, None, None)
    except Exception as e:
        logger.error(f"Erro ao extrair preço de '{texto}': {e}")
        return (None, None, None)

def get_random_headers() -> dict:
    """Retorna headers aleatórios para evitar bloqueio."""
    headers = BASE_HEADERS.copy()
    headers['User-Agent'] = random.choice(USER_AGENTS)
    return headers

def normalizar_loja(nome_loja: str) -> str:
    """Normaliza o nome da loja para um padrão consistente."""
    if not nome_loja:
        return 'Desconhecida'
    
    # Converte para minúsculas e remove espaços extras
    nome = nome_loja.lower().strip()
    
    # Mapeamento de variações para nomes padronizados
    mapeamento = {
        'amazon': 'Amazon',
        'amazon.com.br': 'Amazon',
        'amazon br': 'Amazon',
        'magazine luiza': 'Magazine Luiza',
        'magalu': 'Magazine Luiza',
        'americanas': 'Americanas',
        'submarino': 'Submarino',
        'shoptime': 'Shoptime',
        'pontofrio': 'Ponto Frio',
        'ponto frio': 'Ponto Frio',
        'casas bahia': 'Casas Bahia',
        'casasbahia': 'Casas Bahia',
        'kabum': 'Kabum',
        'pichau': 'Pichau',
        'terabyte': 'Terabyte',
        'mercadolivre': 'Mercado Livre',
        'mercado livre': 'Mercado Livre',
        'aliexpress': 'AliExpress',
        'alibaba': 'Alibaba',
    }
    
    # Verifica se o nome da loja está no mapeamento
    for padrao, padronizado in mapeamento.items():
        if padrao in nome:
            return padronizado
    
    # Se não encontrou no mapeamento, retorna o nome original capitalizado
    return nome_loja.strip().title()

def extrair_dominio(url: str) -> str:
    """Extrai o domínio principal de uma URL."""
    if not url:
        return ''
    
    # Remove protocolo e www
    dominio = url.replace('https://', '').replace('http://', '').replace('www.', '')
    
    # Pega a primeira parte do domínio
    dominio = dominio.split('/')[0]
    
    # Remove subdomínios (pega apenas os últimos dois níveis)
    partes = dominio.split('.')
    if len(partes) > 2:
        dominio = '.'.join(partes[-2:])
    
    return dominio

async def buscar_ofertas_promobit(
    session: aiohttp.ClientSession,
    max_paginas: int = 3,
    min_desconto: int = 10,
    categoria: str = 'informatica',
    min_preco: Optional[float] = None,
    max_preco: Optional[float] = None,
    min_avaliacao: float = 4.0,
    min_votos: int = 10,
    apenas_frete_gratis: bool = True,
    apenas_lojas_oficiais: bool = True,
    max_requests: int = 10
) -> List[Dict[str, Any]]:
    """
    Busca ofertas no Promobit com base nos critérios fornecidos.
    
    Args:
        session: Sessão aiohttp para fazer as requisições
        max_paginas: Número máximo de páginas para buscar (padrão: 3)
        min_desconto: Percentual mínimo de desconto para considerar (padrão: 10%)
        categoria: Categoria de produtos para buscar (padrão: 'informatica')
        min_preco: Preço mínimo para filtrar ofertas (opcional)
        max_preco: Preço máximo para filtrar ofertas (opcional)
        min_avaliacao: Avaliação mínima do produto (0-5, padrão: 4.0)
        min_votos: Número mínimo de votos para considerar avaliação (padrão: 10)
        apenas_frete_gratis: Se True, retorna apenas ofertas com frete grátis (padrão: True)
        apenas_lojas_oficiais: Se True, retorna apenas ofertas de lojas oficiais (padrão: True)
        max_requests: Número máximo de requisições simultâneas (padrão: 10)
        
    Returns:
        Lista de dicionários contendo as ofertas encontradas
    """
    ofertas = []
    
    # Valida a categoria
    if categoria not in CATEGORIAS:
        logger.warning(f"Categoria '{categoria}' inválida. Usando 'informatica' como padrão.")
        categoria = 'informatica'
    
    base_url = f"{BASE_URL}{CATEGORIAS[categoria]}"
    
    try:
        # Lista para armazenar as tarefas de busca
        tasks = []
        
        # Cria uma sessão de semáforo para limitar requisições concorrentes
        sem = asyncio.Semaphore(max_requests)
        
        async def fetch_page(page_num: int) -> List[Dict[str, Any]]:
            """Busca ofertas em uma única página."""
            url = f"{base_url}?page={page_num}" if page_num > 1 else base_url
            page_ofertas = []
            
            async with sem:  # Limita o número de requisições concorrentes
                try:
                    # Gera headers aleatórios para cada requisição
                    headers = get_random_headers()
                    
                    # Adiciona um atraso aleatório entre requisições
                    await asyncio.sleep(random.uniform(1.0, 3.0))
                    
                    logger.info(f"Buscando ofertas na página {page_num} - {url}")
                    
                    # Faz a requisição HTTP
                    try:
                        async with session.get(url, headers=headers) as response:
                            response.raise_for_status()
                            html = await response.text()
                    except Exception as e:
                        logger.error(f"Erro ao buscar a página {url}: {e}")
                        return []
                    
                    if not html:
                        return []
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Encontra todos os cards de oferta
                    # Tenta diferentes seletores CSS para maior robustez
                    selectors = [
                        'article[data-testid="offer-card"]',  # Seletor principal
                        'div.thread--deal',  # Alternativa comum
                        'div.thread',  # Alternativa mais genérica
                        'div.deal',    # Outra alternativa
                    ]
                    
                    cards = []
                    for selector in selectors:
                        cards = soup.select(selector)
                        if cards:
                            logger.debug(f"Encontrados {len(cards)} cards com o seletor: {selector}")
                            break
                    
                    if not cards:
                        logger.warning(f"Nenhum card de oferta encontrado na página {page_num}")
                        return []
                    
                    logger.info(f"Encontrados {len(cards)} ofertas na página {page_num}")
                    
                    for card in cards:
                        try:
                            # Extrai título e URL do produto
                            titulo_elem = card.select_one('h3 a, h2 a, a.thread-title, a.thread-link, a.title')
                            if not titulo_elem:
                                logger.debug("Nenhum título encontrado no card")
                                continue
                                
                            titulo = titulo_elem.get_text(strip=True)
                            url_oferta = titulo_elem.get('href', '')
                            
                            # Garante que a URL seja absoluta
                            if url_oferta and not url_oferta.startswith(('http://', 'https://')):
                                if url_oferta.startswith('/'):
                                    url_oferta = f"https://www.promobit.com.br{url_oferta}"
                                else:
                                    url_oferta = f"https://www.promobit.com.br/{url_oferta}"
                            
                            # Extrai preços e desconto
                            preco_elems = card.select('div.thread-price, div.price, span.price, div[data-testid="offer-price"]')
                            if not preco_elems:
                                logger.debug("Nenhum preço encontrado no card")
                                continue
                                
                            # Pega o texto de todos os elementos de preço
                            preco_texto = ' '.join([elem.get_text(strip=True, separator=' ') for elem in preco_elems])
                            preco_atual, preco_original, desconto = extrair_preco(preco_texto)
                            
                            # Se não conseguiu extrair preço, pula para a próxima oferta
                            if not preco_atual or (desconto is not None and desconto < min_desconto):
                                continue
                            
                            # Converte preços para float para comparação
                            try:
                                preco_atual_float = float(preco_atual)
                                
                                # Filtra por faixa de preço
                                if min_preco is not None and preco_atual_float < min_preco:
                                    continue
                                    
                                if max_preco is not None and preco_atual_float > max_preco:
                                    continue
                                    
                            except (ValueError, AttributeError):
                                continue
                            
                            # Extrai URL da imagem
                            img_elems = card.select('img.thread-image, img[src*="product"], img[src*="produto"], img')
                            imagem_url = ''
                            
                            if img_elems:
                                for img in img_elems:
                                    src = img.get('src', '') or img.get('data-src', '')
                                    if src and not any(x in src.lower() for x in ['logo', 'icon', 'avatar']):
                                        imagem_url = src
                                        break
                            
                            # Se a URL da imagem for relativa, converte para absoluta
                            if imagem_url and not imagem_url.startswith(('http://', 'https://')):
                                if imagem_url.startswith('/'):
                                    imagem_url = f"https://www.promobit.com.br{imagem_url}"
                                else:
                                    imagem_url = f"https://www.promobit.com.br/{imagem_url}"
                            
                            # Extrai nome da loja
                            loja_elems = card.select('a.thread-store, a.store, span.store, a[data-testid="offer-store"]')
                            loja = 'Desconhecida'
                            
                            if loja_elems:
                                loja = loja_elems[0].get_text(strip=True)
                            else:
                                # Tenta extrair o nome da loja da URL da imagem
                                img_elems = card.select('img.store-logo, img[src*="logo"], img[alt*="logo"]')
                                if img_elems:
                                    alt_text = img_elems[0].get('alt', '').lower()
                                    if alt_text:
                                        loja = alt_text.replace('logo', '').replace('da loja', '').strip()
                                        if not loja:
                                            loja = 'Desconhecida'
                            
                            # Normaliza o nome da loja
                            loja_normalizada = normalizar_loja(loja)
                            
                            # Filtra por lojas oficiais, se necessário
                            if apenas_lojas_oficiais and loja_normalizada == 'Desconhecida':
                                continue
                            
                            # Extrai URL do produto na loja
                            url_produto = ''
                            
                            # Tenta diferentes seletores para o link do produto
                            link_selectors = [
                                'a[data-testid="offer-link"]',
                                'a.thread-link[href*="go."]',
                                'a.external-link',
                                'a[href*="redirect/"]',
                                'a[href*="go.promobit"]'
                            ]
                            
                            for selector in link_selectors:
                                link_elem = card.select_one(selector)
                                if link_elem and link_elem.get('href'):
                                    url_produto = link_elem.get('href')
                                    break
                            
                            # Se não encontrou um link específico, usa o link do título
                            if not url_produto and titulo_elem and titulo_elem.get('href'):
                                url_produto = titulo_elem.get('href')
                            
                            # Se ainda não tem URL, usa a URL da oferta
                            if not url_produto:
                                url_produto = f"https://www.promobit.com.br{url_oferta}"
                            
                            # Remove parâmetros de rastreamento comuns
                            for param in ['utm_', 'ref=', 'source=', 'origem=']:
                                if param in url_produto:
                                    url_produto = url_produto.split(param)[0].rstrip('?&')
                                    break
                            
                            # Extrai avaliação do produto
                            avaliacao = 0.0
                            votos = 0
                            
                            # Tenta diferentes seletores para avaliação
                            rating_selectors = [
                                'span[data-testid="offer-rating"]',
                                'div.rating',
                                'span.rating',
                                'div[class*="rating"]',
                                'span[class*="rating"]',
                                'div[title*="estrela"]',
                                'span[title*="estrela"]'
                            ]
                            
                            for selector in rating_selectors:
                                try:
                                    avaliacao_elems = card.select(selector)
                                    if avaliacao_elems:
                                        for elem in avaliacao_elems:
                                            avaliacao_texto = elem.get_text(strip=True)
                                            if avaliacao_texto:
                                                # Tenta extrair avaliação no formato "4.5 (123)" ou similar
                                                match = re.search(r'(\d+[\.,]?\d*).*?[\s(]*(\d+)*', avaliacao_texto)
                                                if match:
                                                    avaliacao = float(match.group(1).replace(',', '.'))
                                                    if match.group(2):
                                                        votos = int(match.group(2))
                                                    break
                                        if avaliacao > 0:
                                            break
                                except (ValueError, AttributeError) as e:
                                    logger.debug(f"Erro ao extrair avaliação: {e}")
                            
                            # Filtra por avaliação mínima
                            if avaliacao < min_avaliacao or votos < min_votos:
                                continue
                            
                            # Verifica se tem frete grátis
                            frete_gratis = 'frete grátis' in card.get_text().lower()
                            if apenas_frete_gratis and not frete_gratis:
                                continue
                            
                            # Extrai domínio da URL do produto
                            dominio = extrair_dominio(url_produto)
                            
                            # Adiciona a oferta à lista
                            oferta = {
                                'titulo': titulo,
                                'preco': f"R$ {float(preco_atual):.2f}".replace('.', ','),
                                'preco_original': f"R$ {float(preco_original):.2f}".replace('.', ',') if preco_original else None,
                                'desconto': desconto or 0,
                                'loja': loja_normalizada,
                                'url_produto': url_produto,
                                'url_fonte': f"https://www.promobit.com.br{url_oferta}",
                                'imagem_url': imagem_url,
                                'avaliacao': avaliacao,
                                'votos': votos,
                                'frete_gratis': frete_gratis,
                                'data_coleta': datetime.now().isoformat(),
                                'categoria': categoria
                            }
                            
                            page_ofertas.append(oferta)
                            logger.debug(f"Oferta adicionada: {titulo} - R$ {preco_atual}")
                            
                        except Exception as e:
                            logger.error(f"Erro ao processar card: {e}", exc_info=True)
                            continue
                    
                    return page_ofertas
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout ao acessar a página {page_num}")
                    return []
                except Exception as e:
                    logger.error(f"Erro ao processar a página {page_num}: {e}", exc_info=True)
                    return []
        
        # Cria tarefas para buscar várias páginas em paralelo
        for page_num in range(1, max_paginas + 1):
            tasks.append(fetch_page(page_num))
            
        # Executa as tarefas em paralelo e aguarda a conclusão
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa os resultados
        for result in results:
            if isinstance(result, list):
                ofertas.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Erro em uma das tarefas: {result}", exc_info=True)
        
        # Remove ofertas duplicadas baseado na URL do produto
        ofertas_unicas = {}
        for oferta in ofertas:
            url = oferta.get('url_produto')
            if url and url not in ofertas_unicas:
                ofertas_unicas[url] = oferta
        
        ofertas = list(ofertas_unicas.values())
        
        # Ordena as ofertas por desconto (maior primeiro) e depois por preço (menor primeiro)
        ofertas.sort(key=lambda x: (-x.get('desconto', 0), float(x.get('preco', '0').replace('R$', '').replace('.', '').replace(',', '.'))))
        
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
