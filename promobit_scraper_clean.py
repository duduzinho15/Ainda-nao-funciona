"""
Módulo para busca de ofertas no site Promobit.

Este módulo implementa um scraper para buscar ofertas de produtos de informática
no site Promobit, com tratamento de erros e anti-bloqueio.
"""
import asyncio
import logging
import random
import re
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

import aiohttp
import aiohttp.client_exceptions
import brotli
from bs4 import BeautifulSoup

# Configuração de logging
logger = logging.getLogger('promobit_scraper')
logger.setLevel(logging.DEBUG)  # Set to DEBUG level

# Remove all handlers if any
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Create console handler with a higher log level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Show all levels in console

# Create file handler which logs even debug messages
file_handler = logging.FileHandler('promobit_scraper.log', mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)  # Log all levels to file

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Disable debug logging for external libraries
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# User Agents para rotação
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'
]

# Headers base para as requisições
BASE_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}

# URLs base para busca de ofertas
BASE_URL = "https://www.promobit.com.br/"
CATEGORIAS = {
    'informatica': '',
    'eletronicos': '',
    'games': '',
    'celulares': ''
}

# Adicionando logging para debug
logger.debug(f"URLs base configuradas: {CATEGORIAS}")

# Lista de palavras-chave para filtrar ofertas relevantes
PALAVRAS_CHAVE = [
    'notebook', 'laptop', 'ultrabook', 'macbook', 'chromebook',
    'ssd', 'hd', 'disco rígido', 'nvme', 'm.2',
    'memória ram', 'memoria ram', 'ddr4', 'ddr5',
    'placa de vídeo', 'placa de video', 'rtx', 'gtx', 'radeon', 'nvidia', 'amd',
    'processador', 'ryzen', 'core i5', 'core i7', 'core i9', 'xeon', 'threadripper',
    'monitor', 'gaming', '144hz', '240hz', '4k', 'ultrawide', 'curvo',
    'mouse', 'mecânico', 'gamer', 'sem fio', 'bluetooth',
    'teclado', 'mecânico', 'mecanico', 'gamer', 'rgb', 'sem fio',
    'headset', 'fone de ouvido', 'headphone', 'headset gamer', 'sem fio', 'bluetooth'
]

def extrair_preco(texto: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """
    Extrai preço atual, original e desconto de um texto de preço.
    
    Args:
        texto: Texto contendo os preços (ex: "R$ 1.199,99 R$ 999,99 20% OFF")
        
    Returns:
        tuple: (preco_atual, preco_original, desconto) ou (preco_atual, None, None) se não houver desconto
    """
    if not texto:
        return None, None, None
        
    # Padroniza o formato do texto
    texto = texto.lower().replace('r$', '').strip()
    
    # Encontra todos os valores numéricos no formato X.XXX,XX
    precos = re.findall(r'[\d\.]+,\d{2}', texto)
    
    # Encontra o valor de desconto (ex: "30% OFF")
    desconto_match = re.search(r'(\d+)%', texto)
    desconto = int(desconto_match.group(1)) if desconto_match else 0
    
    if not precos:
        return None, None, None
    
    # Remove pontos de milhar e substitui vírgula por ponto
    precos_limpos = []
    for p in precos:
        try:
            valor = float(p.replace('.', '').replace(',', '.'))
            precos_limpos.append((p, valor))
        except (ValueError, AttributeError):
            continue
    
    # Se não tem preços válidos, retorna None
    if not precos_limpos:
        return None, None, None
    
    # Ordena os preços (menor para maior)
    precos_limpos.sort(key=lambda x: x[1])
    
    # Se tiver apenas um preço, retorna ele como preço atual
    if len(precos_limpos) == 1:
        return precos_limpos[0][0], None, None
    
    # Se tiver desconto, assume que o menor preço é o com desconto
    if desconto > 0:
        return precos_limpos[0][0], precos_limpos[-1][0], desconto
    
    # Se não tem desconto explícito, tenta inferir pelo formato
    menor_preco = precos_limpos[0][1]
    maior_preco = precos_limpos[-1][1]
    
    if maior_preco > menor_preco * 1.1:  # Pelo menos 10% de diferença
        desconto_calculado = int(((maior_preco - menor_preco) / maior_preco) * 100)
        return precos_limpos[0][0], precos_limpos[-1][0], desconto_calculado
    
    # Se não, retorna apenas o menor preço
    return precos_limpos[0][0], None, None

def get_random_headers() -> Dict[str, str]:
    """Retorna headers aleatórios para evitar bloqueio."""
    headers = BASE_HEADERS.copy()
    headers['User-Agent'] = random.choice(USER_AGENTS)
    return headers

def normalizar_loja(nome_loja: str) -> str:
    """Normaliza o nome da loja para um padrão consistente."""
    if not nome_loja:
        return 'Desconhecida'
        
    # Dicionário de mapeamento de nomes de lojas
    mapeamento = {
        'amazon': 'Amazon',
        'magazine luiza': 'Magazine Luiza',
        'magalu': 'Magazine Luiza',
        'americanas': 'Americanas',
        'submarino': 'Submarino',
        'shoptime': 'Shoptime',
        'ponto': 'Ponto Frio',
        'pontofrio': 'Ponto Frio',
        'casas bahia': 'Casas Bahia',
        'kabum': 'Kabum',
        'pichau': 'Pichau',
        'terabyteshop': 'Terabyte',
        'terabyte': 'Terabyte',
        'fast shop': 'Fast Shop',
        'fastshop': 'Fast Shop',
        'carrefour': 'Carrefour',
        'extra': 'Extra',
        'walmart': 'Walmart',
        'mercado livre': 'Mercado Livre',
        'mercadolivre': 'Mercado Livre'
    }
    
    nome_loja = nome_loja.lower().strip()
    
    # Verifica se o nome da loja está no mapeamento
    for key, value in mapeamento.items():
        if key in nome_loja:
            return value
    
    # Se não encontrar no mapeamento, retorna o nome original com a primeira letra maiúscula
    return nome_loja.capitalize()

def extrair_dominio(url: str) -> str:
    """Extrai o domínio principal de uma URL."""
    if not url or not isinstance(url, str):
        return 'desconhecido'
    
    # Remove protocolo e www
    dominio = url.replace('https://', '').replace('http://', '').replace('www.', '')
    
    # Pega a primeira parte do domínio
    dominio = dominio.split('/')[0]
    
    # Remove subdomínios (ex: loja.mercadolivre.com.br -> mercadolivre.com.br)
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
                        logger.info(f"Fazendo requisição para: {url}")
                        logger.debug(f"Headers da requisição: {headers}")
                        
                        async with session.get(url, headers=headers, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=30)) as response:
                            logger.info(f"Status da resposta: {response.status}")
                            logger.debug(f"Headers da resposta: {dict(response.headers)}")
                            
                            # Verifica o status da resposta
                            if response.status != 200:
                                logger.error(f"Erro na requisição: Status {response.status} para URL: {url}")
                                logger.error(f"URL de redirecionamento: {response.url}")
                                # Tenta ler o corpo da resposta para mais detalhes
                                try:
                                    error_content = await response.text()
                                    logger.error(f"Conteúdo do erro: {error_content[:500]}...")
                                except Exception as e:
                                    logger.error(f"Não foi possível ler o corpo da resposta de erro: {e}")
                                return []
                            
                            # Lê o conteúdo da resposta
                            content = await response.read()
                            logger.info(f"Tamanho do conteúdo bruto: {len(content)} bytes")
                            
                            # Se o conteúdo for muito pequeno, pode ser um erro
                            if len(content) < 1000:
                                logger.warning(f"Conteúdo da resposta muito pequeno (apenas {len(content)} bytes). Pode indicar um erro ou redirecionamento.")
                                try:
                                    content_text = content.decode('utf-8', errors='ignore')
                                    logger.warning(f"Conteúdo da resposta: {content_text[:1000]}...")
                                except Exception as e:
                                    logger.error(f"Erro ao decodificar o conteúdo da resposta: {e}")
                                return []
                            
                            # Verifica se o conteúdo está compactado com Brotli
                            content_encoding = response.headers.get('Content-Encoding', '').lower()
                            logger.debug(f"Content-Encoding: {content_encoding}")
                            
                            if 'br' in content_encoding:
                                try:
                                    logger.debug("Descomprimindo conteúdo com Brotli...")
                                    content = brotli.decompress(content)
                                    logger.debug(f"Tamanho após descompressão: {len(content)} bytes")
                                except Exception as e:
                                    logger.warning(f"Falha ao descompactar conteúdo com Brotli: {e}")
                            
                            # Decodifica o conteúdo para texto
                            try:
                                html = content.decode('utf-8', errors='replace')
                                logger.info(f"Tamanho do HTML decodificado: {len(html)} caracteres")
                                
                                # Salva o HTML para análise, se necessário
                                with open(f'promobit_page_{page_num}.html', 'w', encoding='utf-8') as f:
                                    f.write(html)
                                logger.info(f"HTML salvo em 'promobit_page_{page_num}.html' para análise")
                                
                                # Verifica se o HTML contém elementos esperados
                                if 'ofertas' not in html.lower() and 'offers' not in html.lower():
                                    logger.warning("O HTML não contém termos esperados como 'ofertas' ou 'offers'")
                                
                            except Exception as e:
                                logger.error(f"Erro ao decodificar o conteúdo: {e}")
                                # Tenta salvar o conteúdo bruto para análise
                                with open(f'promobit_page_{page_num}_raw.bin', 'wb') as f:
                                    f.write(content)
                                logger.info(f"Conteúdo bruto salvo em 'promobit_page_{page_num}_raw.bin' para análise")
                                return []
                            
                            # Decodifica o conteúdo para string
                            html = content.decode('utf-8', errors='replace')
                            
                            # Salva o HTML para análise
                            with open(f'promobit_page_{page_num}.html', 'w', encoding='utf-8') as f:
                                f.write(html)
                            logger.debug(f"HTML salvo em promobit_page_{page_num}.html")
                            
                            # Log das primeiras 500 caracteres do HTML para debug
                            logger.debug(f"Primeiros 500 caracteres do HTML: {html[:500]}")
                            
                    except Exception as e:
                        logger.error(f"Erro ao buscar a página {url}: {e}", exc_info=True)
                        return []
                    
                    if not html:
                        logger.error("Nenhum conteúdo HTML retornado")
                        return []
                    
                    try:
                        soup = BeautifulSoup(html, 'html.parser')
                        logger.debug("HTML parseado com sucesso")
                    except Exception as e:
                        logger.error(f"Erro ao fazer parse do HTML: {e}")
                        return []
                    
                    # Procura por cards de ofertas
                    cards_oferta = soup.find_all('section')
                    
                    if not cards_oferta:
                        logger.warning(f"Nenhum card de oferta encontrado na página {page_num}")
                        return []
                    
                    logger.info(f"Encontrados {len(cards_oferta)} cards de oferta na página {page_num}")
                    
                    for card in cards_oferta:
                        try:
                            # Inicializa o dicionário da oferta
                            oferta = {}
                            
                            # URL do produto
                            url_produto = ""
                            link_elem = card.find('a', href=True)
                            if link_elem:
                                url_produto = link_elem['href']
                                if not url_produto.startswith('http'):
                                    url_produto = f"https://www.promobit.com.br{url_produto}"
                            
                            # Título da oferta
                            titulo_elem = card.find('span', class_=lambda x: x and 'line-clamp-2' in x)
                            titulo = titulo_elem.get_text(strip=True) if titulo_elem else "Título não encontrado"
                            
                            # Extrai preço com validação rigorosa
                            price_text = card.get_text(" ", strip=True) or ""
                            m = re.search(r"(R\$\s?\d{1,3}(?:\.\d{3})*,\d{2})", price_text)
                            if not m:
                                continue  # Pula ofertas sem preço válido
                            
                            preco_atual = m.group(1)
                            
                            # Valida se o preço é realmente válido
                            if not re.match(r"^R\$\s?\d{1,3}(?:\.\d{3})*,\d{2}$", preco_atual):
                                continue  # Pula se o preço não estiver no formato correto
                            
                            # Preço atual - corrigindo para pegar o valor correto
                            preco_container = card.find('div', class_=lambda x: x and 'lg:order-0' in x and 'items-center' in x)
                            if preco_container:
                                # Pega o símbolo R$ e o valor separadamente
                                simbolo_elem = preco_container.find('span', class_=lambda x: x and 'pr-1' in x)
                                valor_elem = preco_container.find('span', class_=lambda x: x and 'whitespace-nowrap' in x)
                                
                                if simbolo_elem and valor_elem:
                                    preco_atual = f"{simbolo_elem.get_text(strip=True)}{valor_elem.get_text(strip=True)}"
                                elif valor_elem:
                                    preco_atual = f"R$ {valor_elem.get_text(strip=True)}"
                                else:
                                    preco_atual = "Preço não encontrado"
                            else:
                                preco_atual = "Preço não encontrado"
                            
                            # Preço original (riscado) - corrigindo o seletor
                            preco_original_elem = card.find('span', class_=lambda x: x and 'line-through' in x and 'text-sm' in x)
                            preco_original = preco_original_elem.get_text(strip=True) if preco_original_elem else ""
                            
                            # Calcula desconto usando a função extrair_preco
                            if preco_atual and preco_original and preco_atual != "Preço não encontrado":
                                # Extrai apenas os valores numéricos dos preços
                                preco_atual_limpo = preco_atual.replace('R$', '').strip()
                                preco_original_limpo = preco_original.replace('R$', '').strip()
                                
                                try:
                                    # Converte para float para calcular desconto
                                    preco_atual_valor = float(preco_atual_limpo.replace('.', '').replace(',', '.'))
                                    preco_original_valor = float(preco_original_limpo.replace('.', '').replace(',', '.'))
                                    
                                    # Calcula desconto
                                    if preco_original_valor > preco_atual_valor:
                                        desconto = int(((preco_original_valor - preco_atual_valor) / preco_original_valor) * 100)
                                    else:
                                        desconto = 0
                                except:
                                    desconto = 0
                            else:
                                desconto = 0
                            
                            # Imagem do produto
                            img_elem = card.find('img')
                            imagem_url = img_elem.get('src') if img_elem else ""
                            
                            # Loja
                            loja_elem = card.find('span', class_=lambda x: x and 'text-sm' in x and 'mr-1' in x)
                            loja = loja_elem.get_text(strip=True) if loja_elem else "Loja não identificada"
                            
                            # Cria objeto da oferta
                            oferta = {
                                'titulo': titulo,
                                'preco': preco_atual,  # Campo principal para compatibilidade
                                'preco_atual': preco_atual,
                                'preco_original': preco_original,
                                'desconto': desconto,
                                'imagem_url': imagem_url,
                                'url_produto': url_produto,
                                'loja': loja,
                                'url_afiliado': url_produto,  # Por enquanto, usa a mesma URL
                                'fonte': 'promobit'
                            }
                            
                            ofertas.append(oferta)
                            logger.debug(f"Oferta extraída: {titulo[:50]}... - {preco_atual}")
                            
                        except Exception as e:
                            logger.error(f"Erro ao extrair oferta do card: {e}")
                            continue
                            
                    logger.info(f"Página {page_num}: {len(ofertas)} ofertas passaram nos filtros")
                    return ofertas
                    
                except Exception as e:
                    logger.error(f"Erro ao processar a página {page_num}: {e}", exc_info=True)
                    return []
        
        # Cria tarefas para buscar as páginas
        for page_num in range(1, max_paginas + 1):
            tasks.append(asyncio.ensure_future(fetch_page(page_num)))
            
        # Executa as tarefas em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa os resultados
        for result in results:
            if isinstance(result, list):
                ofertas.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Erro em uma das tarefas: {result}")
        
        logger.info(f"Busca concluída. Total de ofertas encontradas: {len(ofertas)}")
        
    except Exception as e:
        logger.error(f"Erro inesperado ao buscar ofertas: {e}", exc_info=True)
    
    return ofertas

async def main():
    """Função de teste para o módulo."""
    try:
        # Configura logging para debug
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('promobit_scraper_debug.log', mode='w', encoding='utf-8')
            ]
        )
        
        logger.info("=== INÍCIO DO TESTE DO SCRAPER PROMOBIT ===")
        logger.info("Configurações iniciais:")
        logger.info(f"- Categorias disponíveis: {list(CATEGORIAS.keys())}")
        logger.info(f"- URL base: {BASE_URL}")
        
        # Cria uma sessão aiohttp com timeout maior
        timeout = aiohttp.ClientTimeout(total=60)  # Aumentando timeout para 60 segundos
        connector = aiohttp.TCPConnector(
            force_close=True, 
            enable_cleanup_closed=True,
            limit=5  # Limita o número de conexões simultâneas
        )
        
        # Configuração de headers personalizados
        headers = get_random_headers()
        logger.info("Headers da requisição:")
        for key, value in headers.items():
            logger.info(f"  {key}: {value}")
        
        async with aiohttp.ClientSession(
            timeout=timeout, 
            connector=connector,
            headers=headers
        ) as session:
            logger.info("Sessão aiohttp criada com sucesso")
            
            # Testa a conexão com a página inicial primeiro
            logger.info("\n=== TESTE DE CONEXÃO COM A PÁGINA INICIAL ===")
            try:
                test_url = BASE_URL
                logger.info(f"Testando conexão com: {test_url}")
                
                async with session.get(test_url, allow_redirects=True) as response:
                    logger.info(f"Status da resposta: {response.status}")
                    logger.info(f"URL final após redirecionamentos: {response.url}")
                    logger.info(f"Tipo de conteúdo: {response.headers.get('Content-Type')}")
                    
                    # Lê o conteúdo da resposta
                    content = await response.read()
                    logger.info(f"Tamanho do conteúdo: {len(content)} bytes")
                    
                    # Salva o HTML para análise
                    with open('promobit_homepage.html', 'wb') as f:
                        f.write(content)
                    logger.info("Página inicial salva em 'promobit_homepage.html'")
                    
                    # Verifica se o conteúdo parece válido
                    try:
                        html = content.decode('utf-8', errors='replace')
                        if len(html) < 1000:
                            logger.warning("O conteúdo da página inicial é muito pequeno. Pode indicar um erro.")
                        
                        # Verifica se há elementos esperados na página
                        if 'ofertas' not in html.lower() and 'promoções' not in html.lower():
                            logger.warning("Não foram encontradas as palavras-chave 'ofertas' ou 'promoções' no conteúdo da página.")
                        else:
                            logger.info("Palavras-chave 'ofertas' ou 'promoções' encontradas na página inicial.")
                            
                    except Exception as e:
                        logger.error(f"Erro ao processar o conteúdo da página inicial: {e}")
            
            except Exception as e:
                logger.error(f"Falha no teste de conexão: {e}", exc_info=True)
                return
            
            # Busca ofertas
            logger.info("\n=== INICIANDO BUSCA POR OFERTAS ===")
            try:
                ofertas = await buscar_ofertas_promobit(
                    session=session,
                    max_paginas=1,  # Apenas 1 página para teste inicial
                    min_desconto=5,  # Reduzindo o desconto mínimo para incluir mais ofertas
                    min_preco=50.0,  # Reduzindo o preço mínimo
                    max_preco=10000.0,  # Aumentando o preço máximo
                    min_avaliacao=3.0,  # Reduzindo a avaliação mínima
                    min_votos=1,  # Reduzindo o número mínimo de votos
                    apenas_frete_gratis=False,  # Relaxando filtro para teste
                    apenas_lojas_oficiais=False,  # Relaxando filtro para teste
                    max_requests=3  # Reduzindo requisições simultâneas
                )
                
                logger.info(f"Busca concluída. Total de ofertas encontradas: {len(ofertas)}")
                
                # Exibe os resultados
                print(f"\nEncontradas {len(ofertas)} ofertas:")
                for i, oferta in enumerate(ofertas[:10], 1):  # Mostra até 10 ofertas
                    print(f"\n{i}. {oferta.get('titulo', 'Sem título')}")
                    print(f"   Loja: {oferta.get('loja', 'N/A')}")
                    print(f"   Preço: R$ {oferta.get('preco_atual', 'N/A')}")
                    if oferta.get('preco_original'):
                        print(f"   Preço original: R$ {oferta['preco_original']} ({oferta.get('desconto', 0)}% de desconto)")
                    print(f"   Avaliação: {oferta.get('avaliacao', 'N/A')} ({oferta.get('votos', 0)} votos)")
                    print(f"   Frete grátis: {'Sim' if oferta.get('frete_gratis') else 'Não'}")
                    print(f"   URL: {oferta.get('url_produto', 'N/A')}")
                
                if len(ofertas) > 10:
                    print(f"\n... e mais {len(ofertas) - 10} ofertas")
                
                # Salva as ofertas em um arquivo JSON para análise
                import json
                with open('ofertas_promobit.json', 'w', encoding='utf-8') as f:
                    json.dump(ofertas, f, ensure_ascii=False, indent=2)
                logger.info(f"Ofertas salvas em 'ofertas_promobit.json'")
                
            except Exception as e:
                logger.error(f"Erro durante a busca por ofertas: {e}", exc_info=True)
                return []
                
    except Exception as e:
        logger.critical(f"Erro crítico no módulo principal: {e}", exc_info=True)
        return []
    
    return ofertas if 'ofertas' in locals() else []

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Execução interrompida pelo usuário")
    except Exception as e:
        logger.critical(f"Erro não tratado: {e}", exc_info=True)
