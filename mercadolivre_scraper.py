"""
Scraper avançado para o Mercado Livre - Busca ofertas em múltiplas categorias
"""
import asyncio
import logging
import random
import re
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import aiohttp
from bs4 import BeautifulSoup

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mercadolivre_scraper.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger('mercadolivre_scraper')

# User Agents para rotação
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
]

# URLs base para busca de ofertas
BASE_URL = "https://www.mercadolivre.com.br"
CATEGORIAS = {
    'informatica': '/c/informatica',
    'componentes-pc': '/c/informatica/componentes-para-pc',
    'notebooks': '/c/informatica/notebooks-e-acessorios/notebooks',
    'monitores': '/c/informatica/monitores-e-acessorios/monitores',
    'perifericos': '/c/informatica/perifericos',
    'games': '/c/games',
    'eletronicos': '/c/eletronicos-audio-e-video',
    'celulares': '/c/celulares-e-telefones',
    'casa': '/c/casa-moveis-e-decoracao',
    'esporte': '/c/esportes',
    'livros': '/c/livros-revistas-e-comics',
    'moda': '/c/roupas-e-acessorios',
    'automotivo': '/c/automotivo',
    'brinquedos': '/c/brinquedos-e-hobbies'
}

# Palavras-chave para busca específica
PALAVRAS_CHAVE = [
    'notebook gamer', 'placa de video', 'processador', 'memoria ram',
    'ssd', 'monitor gamer', 'teclado mecanico', 'mouse gamer',
    'cadeira gamer', 'mesa gamer', 'smartphone', 'smartwatch',
    'fone bluetooth', 'caixa de som bluetooth', 'drone', 'action figure',
    'manga', 'hq', 'quadrinho', 'cosplay', 'decoração geek'
]

def get_random_headers() -> dict:
    """Retorna headers aleatórios para evitar bloqueio."""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.mercadolivre.com.br/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

def normalizar_loja(nome_loja: str) -> str:
    """Normaliza o nome da loja para consistência."""
    if not nome_loja:
        return "Mercado Livre"
    
    nome_loja = nome_loja.strip().lower()
    
    # Mapeamento de variações de nomes de lojas
    lojas = {
        'mercadolivre': 'Mercado Livre',
        'ml': 'Mercado Livre',
        'mercadolibre': 'Mercado Livre',
        'mercadolivre.com.br': 'Mercado Livre'
    }
    
    for padrao, nome_normalizado in lojas.items():
        if padrao in nome_loja:
            return nome_normalizado
    
    return "Mercado Livre"

def extrair_preco(texto: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extrai preço atual e original de um texto de preço do Mercado Livre.
    
    Args:
        texto: Texto contendo os preços
        
    Returns:
        tuple: (preco_atual, preco_original) ou (preco_atual, None) se não houver desconto
    """
    try:
        # Remove espaços extras e normaliza
        texto = re.sub(r'\s+', ' ', texto.strip())
        
        # Encontra todos os valores numéricos no formato R$ X.XXX,XX
        precos = re.findall(r'R\$\s*[\d\.]+,\d{2}', texto)
        
        if not precos:
            return None, None
        
        # Remove o símbolo R$ e espaços para padronização
        precos = [p.replace('R$', '').strip() for p in precos]
        
        # Se tiver apenas um preço, retorna ele como preço atual
        if len(precos) == 1:
            return precos[0], None
        
        # Se tiver mais de um, assume que o primeiro é o preço original e o segundo o com desconto
        return precos[1], precos[0]
        
    except Exception as e:
        logger.warning(f"Erro ao extrair preços de '{texto}': {e}")
        return None, None

def extrair_desconto(texto: str) -> int:
    """
    Extrai o percentual de desconto de um texto.
    
    Args:
        texto: Texto contendo informação de desconto
        
    Returns:
        int: Percentual de desconto ou 0 se não encontrado
    """
    try:
        # Procura por padrões como "20% OFF", "20% de desconto", etc.
        padroes = [
            r'(\d+)%\s*OFF',
            r'(\d+)%\s*de\s*desconto',
            r'(\d+)%\s*menos',
            r'(\d+)%\s*redução'
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 0
        
    except Exception as e:
        logger.warning(f"Erro ao extrair desconto de '{texto}': {e}")
        return 0

def limpar_texto(texto: str) -> str:
    """Remove caracteres especiais e normaliza o texto."""
    if not texto:
        return ""
    
    # Remove caracteres especiais e normaliza espaços
    texto = re.sub(r'[^\w\s\-\.]', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    
    return texto.strip()

async def buscar_ofertas_categoria(
    session: aiohttp.ClientSession,
    categoria: str,
    max_paginas: int = 3,
    min_desconto: int = 15
) -> List[Dict[str, Any]]:
    """
    Busca ofertas em uma categoria específica do Mercado Livre.
    
    Args:
        session: Sessão aiohttp
        categoria: Nome da categoria
        max_paginas: Número máximo de páginas para buscar
        min_desconto: Percentual mínimo de desconto
        
    Returns:
        Lista de ofertas encontradas
    """
    ofertas = []
    
    try:
        if categoria not in CATEGORIAS:
            logger.warning(f"Categoria '{categoria}' não encontrada")
            return []
        
        url_categoria = BASE_URL + CATEGORIAS[categoria]
        logger.info(f"🔍 Buscando ofertas na categoria: {categoria}")
        
        for pagina in range(1, max_paginas + 1):
            try:
                # Constrói URL da página
                if pagina == 1:
                    url = url_categoria
                else:
                    url = f"{url_categoria}?page={pagina}"
                
                # Faz a requisição
                async with session.get(url, headers=get_random_headers(), timeout=15) as response:
                    if response.status != 200:
                        logger.warning(f"Erro ao acessar página {pagina} da categoria {categoria}: HTTP {response.status}")
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extrai produtos da página
                    produtos = soup.find_all('div', class_='ui-search-result__wrapper')
                    
                    if not produtos:
                        logger.info(f"Nenhum produto encontrado na página {pagina} da categoria {categoria}")
                        break
                    
                    logger.info(f"📦 Encontrados {len(produtos)} produtos na página {pagina}")
                    
                    # Processa cada produto
                    for produto in produtos:
                        try:
                            oferta = extrair_oferta_produto(produto, categoria)
                            if oferta and oferta.get('desconto', 0) >= min_desconto:
                                ofertas.append(oferta)
                        except Exception as e:
                            logger.warning(f"Erro ao extrair produto: {e}")
                            continue
                    
                    # Aguarda um pouco entre as páginas
                    await asyncio.sleep(random.uniform(1, 3))
                    
            except Exception as e:
                logger.error(f"Erro ao processar página {pagina} da categoria {categoria}: {e}")
                continue
        
        logger.info(f"✅ Categoria {categoria}: {len(ofertas)} ofertas encontradas")
        return ofertas
        
    except Exception as e:
        logger.error(f"Erro ao buscar ofertas na categoria {categoria}: {e}")
        return []

async def buscar_ofertas_palavra_chave(
    session: aiohttp.ClientSession,
    palavra_chave: str,
    max_paginas: int = 2,
    min_desconto: int = 15
) -> List[Dict[str, Any]]:
    """
    Busca ofertas por palavra-chave no Mercado Livre.
    
    Args:
        session: Sessão aiohttp
        palavra_chave: Palavra-chave para busca
        max_paginas: Número máximo de páginas
        min_desconto: Percentual mínimo de desconto
        
    Returns:
        Lista de ofertas encontradas
    """
    ofertas = []
    
    try:
        # Constrói URL de busca
        palavra_encoded = palavra_chave.replace(' ', '-')
        url_busca = f"{BASE_URL}/search?q={palavra_encoded}"
        
        logger.info(f"🔍 Buscando ofertas para: {palavra_chave}")
        
        for pagina in range(1, max_paginas + 1):
            try:
                # Constrói URL da página
                if pagina == 1:
                    url = url_busca
                else:
                    url = f"{url_busca}&page={pagina}"
                
                # Faz a requisição
                async with session.get(url, headers=get_random_headers(), timeout=15) as response:
                    if response.status != 200:
                        logger.warning(f"Erro ao acessar página {pagina} da busca '{palavra_chave}': HTTP {response.status}")
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extrai produtos da página
                    produtos = soup.find_all('div', class_='ui-search-result__wrapper')
                    
                    if not produtos:
                        logger.info(f"Nenhum produto encontrado na página {pagina} da busca '{palavra_chave}'")
                        break
                    
                    logger.info(f"📦 Encontrados {len(produtos)} produtos na página {pagina}")
                    
                    # Processa cada produto
                    for produto in produtos:
                        try:
                            oferta = extrair_oferta_produto(produto, palavra_chave)
                            if oferta and oferta.get('desconto', 0) >= min_desconto:
                                ofertas.append(oferta)
                        except Exception as e:
                            logger.warning(f"Erro ao extrair produto: {e}")
                            continue
                    
                    # Aguarda um pouco entre as páginas
                    await asyncio.sleep(random.uniform(1, 3))
                    
            except Exception as e:
                logger.error(f"Erro ao processar página {pagina} da busca '{palavra_chave}': {e}")
                continue
        
        logger.info(f"✅ Busca '{palavra_chave}': {len(ofertas)} ofertas encontradas")
        return ofertas
        
    except Exception as e:
        logger.error(f"Erro ao buscar ofertas para '{palavra_chave}': {e}")
        return []

def extrair_oferta_produto(produto_html, categoria: str) -> Optional[Dict[str, Any]]:
    """
    Extrai informações de uma oferta de produto.
    
    Args:
        produto_html: HTML do produto
        categoria: Categoria ou palavra-chave da busca
        
    Returns:
        Dicionário com informações da oferta ou None se inválida
    """
    try:
        # Extrai título
        titulo_elem = produto_html.find('h2', class_='ui-search-item__title')
        if not titulo_elem:
            return None
        
        titulo = limpar_texto(titulo_elem.get_text())
        if not titulo:
            return None
        
        # Extrai URL do produto
        link_elem = produto_html.find('a', class_='ui-search-item__group__element')
        if not link_elem:
            return None
        
        url_produto = link_elem.get('href')
        if not url_produto:
            return None
        
        # Extrai preços
        preco_elem = produto_html.find('span', class_='andes-money-amount__fraction')
        if not preco_elem:
            return None
        
        preco_texto = preco_elem.get_text()
        preco_atual, preco_original = extrair_preco(preco_texto)
        
        if not preco_atual:
            return None
        
        # Extrai desconto
        desconto_elem = produto_html.find('span', class_='ui-search-price-discount')
        desconto = 0
        if desconto_elem:
            desconto = extrair_desconto(desconto_elem.get_text())
        
        # Extrai imagem
        img_elem = produto_html.find('img')
        url_imagem = ""
        if img_elem:
            url_imagem = img_elem.get('src') or img_elem.get('data-src', '')
        
        # Extrai avaliação
        avaliacao_elem = produto_html.find('span', class_='ui-search-reviews__rating-number')
        avaliacao = "N/A"
        if avaliacao_elem:
            avaliacao = avaliacao_elem.get_text().strip()
        
        # Extrai número de vendas
        vendas_elem = produto_html.find('span', class_='ui-search-item__group__element--sold')
        vendas = 0
        if vendas_elem:
            vendas_texto = vendas_elem.get_text()
            vendas_match = re.search(r'(\d+)', vendas_texto)
            if vendas_match:
                vendas = int(vendas_match.group(1))
        
        # Gera ID único
        id_produto = f"ml_{hash(url_produto) % 1000000}"
        
        # Constrói a oferta
        oferta = {
            'id_produto': id_produto,
            'loja': 'Mercado Livre',
            'titulo': titulo,
            'preco': f"R$ {preco_atual}",
            'preco_original': f"R$ {preco_original}" if preco_original else None,
            'url_produto': url_produto,
            'url_afiliado': url_produto,  # Será convertido pelo affiliate.py
            'url_imagem': url_imagem,
            'fonte': 'Mercado Livre Scraper',
            'desconto': desconto,
            'categoria': categoria,
            'avaliacao': avaliacao,
            'vendas': vendas,
            'data_coleta': datetime.now().isoformat()
        }
        
        return oferta
        
    except Exception as e:
        logger.warning(f"Erro ao extrair oferta: {e}")
        return None

async def buscar_ofertas_mercadolivre(
    max_ofertas: int = 50,
    min_desconto: int = 15,
    categorias: Optional[List[str]] = None,
    palavras_chave: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Função principal para buscar ofertas no Mercado Livre.
    
    Args:
        max_ofertas: Número máximo de ofertas para retornar
        min_desconto: Percentual mínimo de desconto
        categorias: Lista de categorias para buscar (se None, usa todas)
        palavras_chave: Lista de palavras-chave para busca específica
        
    Returns:
        Lista de ofertas encontradas
    """
    todas_ofertas = []
    
    try:
        # Configura timeout e limites de conexão
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        
        async with aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=get_random_headers()
        ) as session:
            
            # Busca por categorias
            if categorias:
                cats_para_buscar = [c for c in categorias if c in CATEGORIAS]
            else:
                cats_para_buscar = list(CATEGORIAS.keys())[:5]  # Limita a 5 categorias
            
            logger.info(f"🏪 Buscando ofertas em {len(cats_para_buscar)} categorias...")
            
            for categoria in cats_para_buscar:
                try:
                    ofertas_cat = await buscar_ofertas_categoria(
                        session, categoria, max_paginas=2, min_desconto=min_desconto
                    )
                    todas_ofertas.extend(ofertas_cat)
                    
                    # Aguarda entre categorias
                    await asyncio.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.error(f"Erro ao buscar categoria {categoria}: {e}")
                    continue
            
            # Busca por palavras-chave
            if palavras_chave:
                logger.info(f"🔍 Buscando ofertas por {len(palavras_chave)} palavras-chave...")
                
                for palavra in palavras_chave[:10]:  # Limita a 10 palavras-chave
                    try:
                        ofertas_palavra = await buscar_ofertas_palavra_chave(
                            session, palavra, max_paginas=2, min_desconto=min_desconto
                        )
                        todas_ofertas.extend(ofertas_palavra)
                        
                        # Aguarda entre buscas
                        await asyncio.sleep(random.uniform(1, 3))
                        
                    except Exception as e:
                        logger.error(f"Erro ao buscar palavra-chave '{palavra}': {e}")
                        continue
            
            # Remove duplicatas e ordena por desconto
            ofertas_unicas = {}
            for oferta in todas_ofertas:
                chave = (oferta['id_produto'], oferta['loja'])
                if chave not in ofertas_unicas or oferta['desconto'] > ofertas_unicas[chave]['desconto']:
                    ofertas_unicas[chave] = oferta
            
            ofertas_finais = list(ofertas_unicas.values())
            ofertas_finais.sort(key=lambda x: x['desconto'], reverse=True)
            
            logger.info(f"✅ Busca concluída: {len(ofertas_finais)} ofertas únicas encontradas")
            return ofertas_finais[:max_ofertas]
            
    except Exception as e:
        logger.error(f"❌ Erro na busca principal: {e}")
        return []

# Função para teste direto
async def testar_scraper():
    """Função para testar o scraper diretamente."""
    print("🧪 Testando Scraper do Mercado Livre...")
    
    try:
        # Testa busca por categorias
        print("\n🏪 Testando busca por categorias...")
        ofertas_cat = await buscar_ofertas_mercadolivre(
            max_ofertas=10,
            min_desconto=10,
            categorias=['informatica', 'games']
        )
        
        print(f"✅ {len(ofertas_cat)} ofertas encontradas por categoria")
        
        # Testa busca por palavras-chave
        print("\n🔍 Testando busca por palavras-chave...")
        ofertas_palavra = await buscar_ofertas_mercadolivre(
            max_ofertas=5,
            min_desconto=10,
            palavras_chave=['notebook gamer', 'placa de video']
        )
        
        print(f"✅ {len(ofertas_palavra)} ofertas encontradas por palavra-chave")
        
        # Mostra algumas ofertas
        todas_ofertas = ofertas_cat + ofertas_palavra
        if todas_ofertas:
            print(f"\n📦 Exemplos de ofertas encontradas:")
            for i, oferta in enumerate(todas_ofertas[:3], 1):
                print(f"\n   {i}. {oferta['titulo'][:60]}...")
                print(f"      Preço: {oferta['preco']}")
                print(f"      Desconto: {oferta['desconto']}%")
                print(f"      Categoria: {oferta['categoria']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Executa teste se chamado diretamente
    asyncio.run(testar_scraper())
