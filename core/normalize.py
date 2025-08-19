"""
Sistema de normalização para deduplicar ofertas.
Normaliza títulos e URLs para evitar duplicatas por pequenas diferenças.
"""

import re
from typing import Optional
from urllib.parse import urlparse, parse_qs


def normalize_title(title: str) -> str:
    """
    Normaliza o título de uma oferta para deduplicação.
    Remove elementos irrelevantes mas preserva palavras que identificam o produto.
    
    Args:
        title: Título original da oferta
        
    Returns:
        Título normalizado para comparação
    """
    if not title:
        return ""
    
    # Converter para minúsculas
    normalized = title.lower().strip()
    
    # Remover caracteres especiais e múltiplos espaços
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remover palavras comuns que não identificam o produto
    stop_words = {
        'com', 'de', 'da', 'do', 'das', 'dos', 'em', 'na', 'no', 'nas', 'nos',
        'para', 'por', 'com', 'sem', 'sob', 'sobre', 'entre', 'atrás', 'antes',
        'depois', 'durante', 'até', 'desde', 'a', 'o', 'e', 'ou', 'mas', 'se',
        'que', 'qual', 'quem', 'onde', 'quando', 'como', 'porque', 'então',
        'novo', 'nova', 'usado', 'usada', 'original', 'genuino', 'genuina',
        'promocao', 'promoção', 'oferta', 'desconto', 'liquidação', 'liquidaçao',
        'frete', 'gratis', 'grátis', 'envio', 'entrega', 'garantia', 'warranty',
        'loja', 'marca', 'modelo', 'cor', 'tamanho', 'quantidade', 'unidade',
        'kit', 'pack', 'conjunto', 'set', 'coleção', 'coleçao', 'edição', 'ediçao'
    }
    
    # Filtrar palavras que não são stop words
    words = normalized.split()
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    return ' '.join(filtered_words)


def canonical_url(url: str) -> str:
    """
    Normaliza URL para deduplicação.
    Para Amazon: preserva apenas ASIN e tag de afiliado.
    Para outras lojas: remove parâmetros irrelevantes.
    
    Args:
        url: URL original da oferta
        
    Returns:
        URL canônica para comparação
    """
    if not url:
        return ""
    
    try:
        parsed = urlparse(url)
        
        # Caso especial: Amazon
        if 'amazon' in parsed.netloc.lower():
            return _canonicalize_amazon_url(parsed)
        
        # Outras lojas: remover parâmetros irrelevantes
        return _canonicalize_generic_url(parsed)
        
    except Exception:
        # Se falhar o parsing, retorna a URL original
        return url


def _canonicalize_amazon_url(parsed_url) -> str:
    """
    Canonicaliza URL da Amazon preservando apenas ASIN e tag de afiliado.
    """
    path = parsed_url.path
    
    # Extrair ASIN (padrão: /dp/XXXXXXXXXX ou /gp/product/XXXXXXXXXX)
    asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', path)
    if not asin_match:
        return parsed_url.geturl()
    
    asin = asin_match.group(1)
    
    # Extrair tag de afiliado dos parâmetros
    query_params = parse_qs(parsed_url.query)
    tag = query_params.get('tag', [''])[0]
    
    # Construir URL canônica
    canonical = f"https://{parsed_url.netloc}/dp/{asin}"
    if tag:
        canonical += f"?tag={tag}"
    
    return canonical


def _canonicalize_generic_url(parsed_url) -> str:
    """
    Canonicaliza URL genérica removendo parâmetros irrelevantes.
    """
    # Parâmetros que devem ser preservados (identificam o produto)
    relevant_params = {
        'id', 'product_id', 'produto', 'codigo', 'cod', 'ref', 'reference',
        'sku', 'ean', 'gtin', 'mpn', 'model', 'variant', 'cor', 'tamanho'
    }
    
    # Filtrar parâmetros relevantes
    query_params = parse_qs(parsed_url.query)
    filtered_params = {}
    
    for key, values in query_params.items():
        if key.lower() in relevant_params:
            filtered_params[key] = values
    
    # Reconstruir query string
    if filtered_params:
        query_string = '&'.join([
            f"{key}={value[0]}" for key, value in filtered_params.items()
        ])
        canonical = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{query_string}"
    else:
        canonical = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    
    return canonical


def deduplicate_ofertas(ofertas: list, key_func: Optional[callable] = None) -> list:
    """
    Remove ofertas duplicadas baseado em uma chave de normalização.
    
    Args:
        ofertas: Lista de ofertas
        key_func: Função para gerar chave de normalização (padrão: combina título e URL)
        
    Returns:
        Lista de ofertas sem duplicatas
    """
    if not key_func:
        def key_func(oferta):
            title = normalize_title(oferta.get('titulo', ''))
            url = canonical_url(oferta.get('url', ''))
            return f"{title}|{url}"
    
    seen = set()
    deduplicated = []
    
    for oferta in ofertas:
        key = key_func(oferta)
        if key not in seen:
            seen.add(key)
            deduplicated.append(oferta)
    
    return deduplicated


def get_deduplication_stats(ofertas: list) -> dict:
    """
    Retorna estatísticas de deduplicação.
    
    Args:
        ofertas: Lista de ofertas
        
    Returns:
        Dicionário com estatísticas
    """
    if not ofertas:
        return {'total': 0, 'duplicatas': 0, 'unicas': 0, 'reducao_percentual': 0}
    
    total_original = len(ofertas)
    ofertas_unicas = deduplicate_ofertas(ofertas)
    total_unicas = len(ofertas_unicas)
    duplicatas = total_original - total_unicas
    
    reducao_percentual = (duplicatas / total_original * 100) if total_original > 0 else 0
    
    return {
        'total': total_original,
        'duplicatas': duplicatas,
        'unicas': total_unicas,
        'reducao_percentual': round(reducao_percentual, 2)
    }
