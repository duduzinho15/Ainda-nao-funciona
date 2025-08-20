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
from typing import List, Dict, Optional, Any, Tuple, Callable, TypeVar, Type, Union
from functools import wraps

import aiohttp
import aiohttp.client_exceptions
from bs4 import BeautifulSoup

# Type variable for generic function return type
T = TypeVar("T")


def async_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
) -> Callable:
    """
    A decorator for retrying async functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor by which the delay should increase on each retry
        exceptions: Exception(s) to catch and retry on
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        raise

                    # Calculate next delay with exponential backoff and jitter
                    sleep_time = min(delay * (backoff_factor**attempt), max_delay)
                    jitter = random.uniform(0.5, 1.5)  # Add some randomness
                    actual_delay = sleep_time * jitter

                    logger.warning(
                        f"Attempt {attempt + 1} failed with error: {str(e)}. "
                        f"Retrying in {actual_delay:.2f} seconds..."
                    )

                    await asyncio.sleep(actual_delay)

            # This should never be reached due to the raise in the except block
            raise last_exception  # type: ignore

        return wrapper

    return decorator


# Configuração de logging
logger = logging.getLogger("promobit_scraper")
logger.setLevel(logging.INFO)

# Cria handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("promobit_scraper.log", encoding="utf-8")

# Define formato
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Adiciona handlers ao logger
if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# Configuração de logging para aiohttp
aiohttp_logger = logging.getLogger("aiohttp")
aiohttp_logger.setLevel(logging.WARNING)  # Reduz o log do aiohttp para WARNING

# Tenta importar o módulo Brotli para suporte a compactação
try:
    import brotli

    BROTLI_AVAILABLE = True
except ImportError:
    logger.warning(
        "Módulo 'brotli' não encontrado. O suporte a respostas Brotli estará desabilitado."
    )
    BROTLI_AVAILABLE = False

# Configurações do scraper
BASE_URL = "https://www.promobit.com.br"
CATEGORIAS = {
    "informatica": "/promocoes/informatica/",
    "smartphones": "/promocoes/smartphones-tablets-e-telefones/",
    "eletronicos": "/promocoes/eletronicos-audio-e-video/",
    "games": "/promocoes/games/",
    "livros": "/promocoes/livros-ebooks-e-ereaders/",
    "moda": "/promocoes/moda-e-calcados-femininos/",
    "casa": "/promocoes/moveis-e-decoracao/",
    "esporte": "/promocoes/esporte-e-lazer/",
    "outros": "/promocoes/outros/",
}

# Headers para simular um navegador real
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br" if BROTLI_AVAILABLE else "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

# Configurações de delay para evitar bloqueio
MIN_DELAY = 1.0
MAX_DELAY = 3.0


async def create_session() -> aiohttp.ClientSession:
    """
    Cria uma sessão aiohttp configurada para o scraper.

    Returns:
        aiohttp.ClientSession: Sessão configurada
    """
    # Configurações da sessão
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    connector = aiohttp.TCPConnector(
        limit=10, limit_per_host=5, ttl_dns_cache=300, use_dns_cache=True
    )

    # Cria a sessão
    session = aiohttp.ClientSession(
        headers=DEFAULT_HEADERS, timeout=timeout, connector=connector
    )

    return session


@async_retry(max_retries=3, initial_delay=1.0, max_delay=10.0)
async def fetch_page(
    session: aiohttp.ClientSession, url: str, timeout: int = 30
) -> Optional[str]:
    """
    Faz o download de uma página do Promobit.

    Args:
        session: Sessão aiohttp
        url: URL da página a ser baixada
        timeout: Timeout em segundos

    Returns:
        str: Conteúdo HTML da página ou None se falhar
    """
    try:
        logger.debug(f"Fazendo requisição para: {url}")

        async with session.get(url, timeout=timeout) as response:
            response.raise_for_status()

            # Verifica o tipo de conteúdo
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                logger.warning(f"Tipo de conteúdo inesperado: {content_type}")
                return None

            # Lê o conteúdo
            content = await response.text()

            # Aguarda um pouco para não sobrecarregar o servidor
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            await asyncio.sleep(delay)

            logger.debug(f"Página baixada com sucesso: {len(content)} caracteres")
            return content

    except aiohttp.ClientResponseError as e:
        logger.error(f"Erro HTTP {e.status} ao acessar {url}: {e}")
        return None
    except aiohttp.ClientError as e:
        logger.error(f"Erro de cliente ao acessar {url}: {e}")
        return None
    except asyncio.TimeoutError:
        logger.error(f"Timeout ao acessar {url}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado ao acessar {url}: {e}")
        return None


def extract_ofertas_from_html(html_content: str) -> List[Dict[str, Any]]:
    """
    Extrai ofertas do HTML de uma página do Promobit.

    Args:
        html_content: Conteúdo HTML da página

    Returns:
        List[Dict[str, Any]]: Lista de ofertas extraídas
    """
    ofertas = []

    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # Procura por links de oferta
        links_oferta = soup.find_all("a", href=re.compile(r"/oferta/"))

        logger.info(f"Encontrados {len(links_oferta)} links de oferta na página")

        for link in links_oferta:
            try:
                oferta = extract_single_oferta(link)
                if oferta:
                    ofertas.append(oferta)
            except Exception as e:
                logger.error(f"Erro ao extrair oferta: {e}")
                continue

        logger.info(f"Extraídas {len(ofertas)} ofertas válidas")

    except Exception as e:
        logger.error(f"Erro ao processar HTML: {e}")

    return ofertas


def extract_single_oferta(link_element) -> Optional[Dict[str, Any]]:
    """
    Extrai informações de uma oferta individual.

    Args:
        link_element: Elemento HTML do link da oferta

    Returns:
        Dict[str, Any]: Dicionário com as informações da oferta ou None se falhar
    """
    try:
        # Extrai o link da oferta
        href = link_element.get("href", "")
        if not href:
            return None

        # Constrói a URL completa
        if href.startswith("/"):
            url_oferta = f"{BASE_URL}{href}"
        else:
            url_oferta = href

        # Extrai o ID da oferta da URL
        id_match = re.search(r"/oferta/([^/]+)/?$", href)
        if id_match:
            id_oferta = id_match.group(1)
        else:
            id_oferta = str(hash(href))[-8:]

        # Extrai o título
        titulo = ""
        titulo_elem = link_element.find("span", class_=re.compile(r"line-clamp-2"))
        if titulo_elem:
            titulo = titulo_elem.get_text(strip=True)

        if not titulo:
            return None

        # Extrai o preço atual
        preco = ""
        preco_elem = link_element.find("span", class_=re.compile(r"text-primary-400"))
        if preco_elem:
            preco = preco_elem.get_text(strip=True)

        # Extrai o preço original (riscado)
        preco_original = ""
        preco_original_elem = link_element.find(
            "span", class_=re.compile(r"line-through")
        )
        if preco_original_elem:
            preco_original = preco_original_elem.get_text(strip=True)

        # Extrai a loja
        loja = ""
        loja_elem = link_element.find("span", class_=re.compile(r"font-bold.*text-sm"))
        if loja_elem:
            loja = loja_elem.get_text(strip=True)

        # Extrai a imagem
        url_imagem = ""
        img_elem = link_element.find("img")
        if img_elem:
            img_src = img_elem.get("src", "")
            if img_src:
                if img_src.startswith("//"):
                    url_imagem = f"https:{img_src}"
                elif img_src.startswith("/"):
                    url_imagem = f"{BASE_URL}{img_src}"
                else:
                    url_imagem = img_src

        # Extrai tags/badges
        tags = []
        badges = link_element.find_all("div", class_=re.compile(r"bg-neutral-high-300"))
        if badges:
            tags = [badge.get_text(strip=True) for badge in badges]

        # Calcula o desconto se houver preço original
        desconto = 0
        if preco_original and preco:
            try:
                # Remove caracteres não numéricos e converte para float
                preco_orig = float(
                    re.sub(r"[^\d.,]", "", preco_original).replace(",", ".")
                )
                preco_atual = float(re.sub(r"[^\d.,]", "", preco).replace(",", "."))

                if preco_orig > 0:
                    desconto = ((preco_orig - preco_atual) / preco_orig) * 100
            except (ValueError, ZeroDivisionError):
                pass

        # Cria o dicionário da oferta
        oferta = {
            "id_produto": id_oferta,
            "loja": loja,
            "titulo": titulo,
            "preco": preco,
            "url_produto": url_oferta,
            "url_imagem": url_imagem,
            "preco_original": preco_original,
            "desconto": round(desconto, 2),
            "tags": tags,
            "data_extração": datetime.now().isoformat(),
        }

        return oferta

    except Exception as e:
        logger.error(f"Erro ao extrair oferta individual: {e}")
        return None


async def processar_pagina(
    session: aiohttp.ClientSession,
    url: str,
    min_desconto: int = 10,
    min_preco: Optional[float] = None,
    max_preco: Optional[float] = None,
    min_avaliacao: float = 4.0,
    min_votos: int = 10,
    apenas_frete_gratis: bool = True,
    apenas_lojas_oficiais: bool = True,
) -> List[Dict[str, Any]]:
    """
    Processa uma página do Promobit e extrai as ofertas.

    Args:
        session: Sessão aiohttp
        url: URL da página a ser processada
        min_desconto: Percentual mínimo de desconto
        min_preco: Preço mínimo
        max_preco: Preço máximo
        min_avaliacao: Avaliação mínima
        min_votos: Número mínimo de votos
        apenas_frete_gratis: Se True, retorna apenas ofertas com frete grátis
        apenas_lojas_oficiais: Se True, retorna apenas ofertas de lojas oficiais

    Returns:
        List[Dict[str, Any]]: Lista de ofertas encontradas na página
    """
    try:
        logger.info(f"Processando página: {url}")

        # Faz o download da página
        html_content = await fetch_page(session, url)
        if not html_content:
            logger.warning(f"Falha ao baixar página: {url}")
            return []

        # Extrai as ofertas do HTML
        ofertas = extract_ofertas_from_html(html_content)

        # Filtra as ofertas baseado nos critérios
        ofertas_filtradas = filter_ofertas(
            ofertas,
            min_desconto=min_desconto,
            min_preco=min_preco,
            max_preco=max_preco,
            apenas_frete_gratis=apenas_frete_gratis,
            apenas_lojas_oficiais=apenas_lojas_oficiais,
        )

        logger.info(
            f"Página processada: {len(ofertas)} ofertas encontradas, {len(ofertas_filtradas)} após filtros"
        )

        return ofertas_filtradas

    except Exception as e:
        logger.error(f"Erro ao processar página {url}: {e}")
        return []


def filter_ofertas(
    ofertas: List[Dict[str, Any]],
    min_desconto: int = 10,
    min_preco: Optional[float] = None,
    max_preco: Optional[float] = None,
    apenas_frete_gratis: bool = True,
    apenas_lojas_oficiais: bool = True,
) -> List[Dict[str, Any]]:
    """
    Filtra as ofertas baseado nos critérios especificados.

    Args:
        ofertas: Lista de ofertas a serem filtradas
        min_desconto: Percentual mínimo de desconto
        min_preco: Preço mínimo
        max_preco: Preço máximo
        apenas_frete_gratis: Se True, retorna apenas ofertas com frete grátis
        apenas_lojas_oficiais: Se True, retorna apenas ofertas de lojas oficiais

    Returns:
        List[Dict[str, Any]]: Lista de ofertas filtradas
    """
    ofertas_filtradas = []

    for oferta in ofertas:
        try:
            # Filtra por desconto mínimo
            if oferta.get("desconto", 0) < min_desconto:
                continue

            # Filtra por preço mínimo
            if min_preco is not None:
                preco_atual = extract_price_value(oferta.get("preco", ""))
                if preco_atual is None or preco_atual < min_preco:
                    continue

            # Filtra por preço máximo
            if max_preco is not None:
                preco_atual = extract_price_value(oferta.get("preco", ""))
                if preco_atual is None or preco_atual > max_preco:
                    continue

            # Filtra por frete grátis
            if apenas_frete_gratis:
                tags = oferta.get("tags", [])
                if not any(
                    "frete" in tag.lower() and "grátis" in tag.lower() for tag in tags
                ):
                    continue

            # Filtra por lojas oficiais
            if apenas_lojas_oficiais:
                loja = oferta.get("loja", "").lower()
                lojas_oficiais = [
                    "amazon",
                    "magazine luiza",
                    "kabum",
                    "americanas",
                    "casas bahia",
                ]
                if not any(loja_oficial in loja for loja_oficial in lojas_oficiais):
                    continue

            ofertas_filtradas.append(oferta)

        except Exception as e:
            logger.error(f"Erro ao filtrar oferta: {e}")
            continue

    return ofertas_filtradas


def extract_price_value(price_str: str) -> Optional[float]:
    """
    Extrai o valor numérico de uma string de preço.

    Args:
        price_str: String contendo o preço

    Returns:
        float: Valor numérico do preço ou None se falhar
    """
    try:
        if not price_str:
            return None

        # Remove caracteres não numéricos e converte para float
        clean_price = re.sub(r"[^\d.,]", "", price_str)
        clean_price = clean_price.replace(",", ".")

        if clean_price:
            return float(clean_price)

        return None

    except (ValueError, TypeError):
        return None


async def buscar_ofertas_promobit(
    session: Optional[aiohttp.ClientSession] = None,
    max_paginas: int = 3,
    min_desconto: int = 10,
    categoria: str = "informatica",
    min_preco: Optional[float] = None,
    max_preco: Optional[float] = None,
    min_avaliacao: float = 4.0,
    min_votos: int = 10,
    apenas_frete_gratis: bool = True,
    apenas_lojas_oficiais: bool = True,
    max_requests: int = 10,
    request_timeout: int = 30,
) -> List[Dict[str, Any]]:
    """
    Busca ofertas no Promobit com base nos critérios fornecidos.

    Args:
        session: Sessão aiohttp (opcional). Se não for fornecida, uma nova será criada.
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
        request_timeout: Timeout em segundos para cada requisição (padrão: 30)

    Returns:
        Lista de dicionários contendo as ofertas encontradas
    """
    # Cria uma nova sessão se não for fornecida
    close_session = False
    if session is None:
        session = await create_session()
        close_session = True

    try:
        # Obtém a URL base para a categoria
        categoria_url = CATEGORIAS.get(categoria.lower(), CATEGORIAS["informatica"])
        base_url = f"{BASE_URL}{categoria_url}"

        logger.info(
            f"Iniciando busca por ofertas na categoria: {categoria} (URL: {base_url})"
        )

        # Lista para armazenar todas as ofertas encontradas
        todas_as_ofertas = []

        # Lista de tarefas para buscar páginas em paralelo
        tasks = []

        # Cria tarefas para buscar cada página
        for page_num in range(1, max_paginas + 1):
            # Constrói a URL da página
            if page_num == 1:
                url = base_url
            else:
                url = f"{base_url}?page={page_num}"

            # Adiciona a tarefa à lista
            tasks.append(
                processar_pagina(
                    session=session,
                    url=url,
                    min_desconto=min_desconto,
                    min_preco=min_preco,
                    max_preco=max_preco,
                    min_avaliacao=min_avaliacao,
                    min_votos=min_votos,
                    apenas_frete_gratis=apenas_frete_gratis,
                    apenas_lojas_oficiais=apenas_lojas_oficiais,
                )
            )

        # Executa as tarefas em paralelo, limitando o número de requisições simultâneas
        sem = asyncio.Semaphore(max_requests)

        async def bounded_gather(tasks):
            async def sem_task(task):
                async with sem:
                    return await task

            return await asyncio.gather(*(sem_task(task) for task in tasks))

        # Aguarda a conclusão de todas as tarefas
        resultados = await bounded_gather(tasks)

        # Processa os resultados
        for resultado in resultados:
            if isinstance(resultado, list):
                todas_as_ofertas.extend(resultado)
            elif isinstance(resultado, Exception):
                logger.error(f"Erro ao processar página: {resultado}", exc_info=True)

        # Remove ofertas duplicadas (mesma URL)
        ofertas_unicas = {}
        for oferta in todas_as_ofertas:
            url = oferta.get("url_produto", "")
            if url and url not in ofertas_unicas:
                ofertas_unicas[url] = oferta

        ofertas_finais = list(ofertas_unicas.values())

        # Ordena por desconto (maior primeiro)
        ofertas_finais.sort(key=lambda x: x.get("desconto", 0), reverse=True)

        logger.info(
            f"Busca concluída: {len(ofertas_finais)} ofertas únicas encontradas"
        )

        return ofertas_finais

    except Exception as e:
        logger.error(f"Erro durante a busca de ofertas: {e}", exc_info=True)
        return []

    finally:
        # Fecha a sessão se foi criada por esta função
        if close_session and session:
            await session.close()


# Função síncrona para compatibilidade
def buscar_ofertas_promobit_sync(
    max_paginas: int = 3,
    min_desconto: int = 0,  # Reduzido de 10 para 0
    categoria: str = "informatica",
    min_preco: Optional[float] = None,
    max_preco: Optional[float] = None,
    apenas_frete_gratis: bool = False,  # Mudado de True para False
    apenas_lojas_oficiais: bool = False,  # Mudado de True para False
) -> List[Dict[str, Any]]:
    """
    Versão síncrona da função de busca de ofertas.

    Args:
        max_paginas: Número máximo de páginas para buscar
        min_desconto: Percentual mínimo de desconto
        categoria: Categoria de produtos
        min_preco: Preço mínimo
        max_preco: Preço máximo
        apenas_frete_gratis: Se True, retorna apenas ofertas com frete grátis
        apenas_lojas_oficiais: Se True, retorna apenas ofertas de lojas oficiais

    Returns:
        Lista de dicionários contendo as ofertas encontradas
    """
    try:
        # Executa a função assíncrona em um novo loop de eventos
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            return loop.run_until_complete(
                buscar_ofertas_promobit(
                    max_paginas=max_paginas,
                    min_desconto=min_desconto,
                    categoria=categoria,
                    min_preco=min_preco,
                    max_preco=max_preco,
                    apenas_frete_gratis=apenas_frete_gratis,
                    apenas_lojas_oficiais=apenas_lojas_oficiais,
                )
            )
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Erro na versão síncrona: {e}")
        return []


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
        # Buscar ofertas de informática (categoria principal)
        ofertas = await buscar_ofertas_promobit(
            max_paginas=2,
            min_desconto=0,
            categoria="informatica"
        )
        
        # Adicionar metadados de compatibilidade
        for oferta in ofertas:
            oferta['fonte'] = 'promobit_scraper'
            oferta['periodo'] = periodo
            oferta['timestamp'] = time.time()
        
        return ofertas
        
    except Exception as e:
        logger.error(f"❌ Erro na função get_ofertas: {e}")
        return []

# Configurações para o scraper registry
priority = 80  # Prioridade alta (site especializado)
rate_limit = 1.0  # 1 requisição por segundo
description = "Scraper para o Promobit - Site especializado em ofertas de informática"

if __name__ == "__main__":
    print("🔍 Testando scraper do Promobit...")
    print("=" * 50)

    try:
        ofertas = buscar_ofertas_promobit_sync(max_paginas=1, min_desconto=0)

        if ofertas:
            print(f"✅ Encontradas {len(ofertas)} ofertas!")
            print("\n📋 Primeiras 3 ofertas encontradas:")
            print("-" * 50)

            for i, oferta in enumerate(ofertas[:3], 1):
                print(f"\n{i}. {oferta['titulo'][:60]}...")
                print(f"   💰 Preço: {oferta['preco']}")
                if oferta["preco_original"]:
                    print(f"   💸 Preço Original: {oferta['preco_original']}")
                print(f"   🏪 Loja: {oferta['loja']}")
                print(f"   🔗 URL: {oferta['url_produto'][:80]}...")
                print(f"   🆔 ID: {oferta['id_produto']}")
                if oferta["desconto"] > 0:
                    print(f"   📉 Desconto: {oferta['desconto']:.1f}%")
        else:
            print("❌ Nenhuma oferta encontrada")

    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback

        traceback.print_exc()
