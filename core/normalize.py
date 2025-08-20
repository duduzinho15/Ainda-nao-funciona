"""
Funções de normalização e deduplicação de ofertas.
Remove duplicatas baseadas em URL canônica e título normalizado.
"""

import re
import unicodedata
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs, urlunparse


def normalize_title(s: str) -> str:
    """
    Normaliza o título de uma oferta para comparação.
    
    Args:
        s: Título original
        
    Returns:
        Título normalizado (minúsculo, sem acentos, espaços normalizados)
    """
    if not s:
        return ""
    
    # Converter para minúsculo
    s = s.lower()
    
    # Remover acentos
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    
    # Normalizar espaços (múltiplos espaços -> um espaço)
    s = re.sub(r'\s+', ' ', s)
    
    # Remover espaços no início e fim
    s = s.strip()
    
    # Remover caracteres especiais comuns
    s = re.sub(r'[^\w\s\-]', '', s)
    
    return s


def canonical_url(url: str) -> str:
    """
    Converte URL para forma canônica para comparação.
    
    Args:
        url: URL original
        
    Returns:
        URL canônica
    """
    if not url:
        return ""
    
    try:
        parsed = urlparse(url)
        
        # Para Amazon: reduzir ao ASIN e manter tag de afiliado
        if 'amazon' in parsed.netloc.lower():
            return _canonicalize_amazon_url(parsed)
        
        # Para outras lojas: remover parâmetros de tracking
        return _canonicalize_generic_url(parsed)
        
    except Exception:
        # Se falhar o parsing, retornar URL original limpa
        return url.strip()


def _canonicalize_amazon_url(parsed) -> str:
    """Canonicaliza URL da Amazon."""
    # Extrair ASIN do caminho
    asin_match = re.search(r'/([A-Z0-9]{10})', parsed.path)
    if asin_match:
        asin = asin_match.group(1)
        
        # Manter tag de afiliado se existir
        affiliate_tag = None
        if parsed.query:
            query_params = parse_qs(parsed.query)
            # Procurar por parâmetros de afiliado comuns
            for key in ['tag', 'linkCode', 'ref']:
                if key in query_params:
                    affiliate_tag = query_params[key][0]
                    break
        
        # Construir URL canônica
        canonical_path = f"/dp/{asin}"
        canonical_query = f"tag={affiliate_tag}" if affiliate_tag else ""
        
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            canonical_path,
            parsed.params,
            canonical_query,
            parsed.fragment
        ))
    
    # Se não encontrar ASIN, retornar caminho principal
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        "",  # Sem query
        ""   # Sem fragment
    ))


def _canonicalize_generic_url(parsed) -> str:
    """Canonicaliza URL genérica removendo parâmetros de tracking."""
    # Parâmetros de tracking comuns para remover
    tracking_params = [
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'gclid', 'fbclid', 'msclkid', 'ref', 'source', 'campaign',
        'affiliate', 'partner', 'tracking', 'click'
    ]
    
    # Filtrar query parameters
    if parsed.query:
        query_params = parse_qs(parsed.query)
        
        # Remover parâmetros de tracking
        filtered_params = {
            k: v for k, v in query_params.items()
            if not any(tracking in k.lower() for tracking in tracking_params)
        }
        
        # Reconstruir query string
        if filtered_params:
            new_query = "&".join(f"{k}={v[0]}" for k, v in filtered_params.items())
        else:
            new_query = ""
    else:
        new_query = ""
    
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))


def deduplicate_ofertas(ofertas: List[Any]) -> List[Any]:
    """
    Remove ofertas duplicadas baseadas em URL canônica e título normalizado.
    
    Args:
        ofertas: Lista de ofertas
        
    Returns:
        Lista de ofertas sem duplicatas
    """
    if not ofertas:
        return []
    
    # Dicionário para rastrear ofertas únicas
    unique_ofertas = {}
    
    for oferta in ofertas:
        # Extrair informações para comparação
        titulo = getattr(oferta, 'titulo', '') or getattr(oferta, 'title', '')
        url = getattr(oferta, 'url', '') or getattr(oferta, 'preco', '')
        
        # Normalizar para comparação
        titulo_normalizado = normalize_title(titulo)
        url_canonica = canonical_url(url)
        
        # Criar chave única
        if url_canonica:
            key = url_canonica
        else:
            key = titulo_normalizado
        
        # Se já existe uma oferta com essa chave, decidir qual manter
        if key in unique_ofertas:
            existing = unique_ofertas[key]
            
            # Preferir a oferta com melhor preço ou mais completa
            if _should_replace_existing(existing, oferta):
                unique_ofertas[key] = oferta
        else:
            unique_ofertas[key] = oferta
    
    return list(unique_ofertas.values())


def _should_replace_existing(existing: Any, new: Any) -> bool:
    """
    Decide se uma nova oferta deve substituir uma existente.
    
    Args:
        existing: Oferta existente
        new: Nova oferta
        
    Returns:
        True se deve substituir
    """
    # Extrair preços
    existing_preco = getattr(existing, 'preco', 0) or 0
    new_preco = getattr(new, 'preco', 0) or 0
    
    # Extrair timestamps
    existing_time = getattr(existing, 'created_at', None)
    new_time = getattr(new, 'created_at', None)
    
    # Preferir preço menor (melhor oferta)
    if new_preco > 0 and existing_preco > 0:
        if new_preco < existing_preco:
            return True
    
    # Preferir oferta mais recente
    if new_time and existing_time:
        if new_time > existing_time:
            return True
    
    # Preferir oferta com mais informações
    existing_info = _count_oferta_info(existing)
    new_info = _count_oferta_info(new)
    
    if new_info > existing_info:
        return True
    
    return False


def _count_oferta_info(oferta: Any) -> int:
    """Conta quantas informações úteis uma oferta tem."""
    info_count = 0
    
    # Campos básicos
    if getattr(oferta, 'titulo', None) or getattr(oferta, 'title', None):
        info_count += 1
    if getattr(oferta, 'preco', None):
        info_count += 1
    if getattr(oferta, 'url', None):
        info_count += 1
    if getattr(oferta, 'imagem_url', None) or getattr(oferta, 'image_url', None):
        info_count += 1
    if getattr(oferta, 'loja', None) or getattr(oferta, 'store', None):
        info_count += 1
    if getattr(oferta, 'created_at', None):
        info_count += 1
    
    return info_count


def get_deduplication_stats(ofertas: List[Any]) -> Dict[str, Any]:
    """
    Retorna estatísticas sobre a deduplicação.
    
    Args:
        ofertas: Lista de ofertas
        
    Returns:
        Dicionário com estatísticas
    """
    total = len(ofertas)
    unicas = len(deduplicate_ofertas(ofertas))
    duplicatas = total - unicas
    
    reducao_percentual = 0
    if total > 0:
        reducao_percentual = round((duplicatas / total) * 100, 1)
    
    return {
        'total': total,
        'unicas': unicas,
        'duplicatas': duplicatas,
        'reducao_percentual': reducao_percentual
    }


def find_similar_ofertas(ofertas: List[Any], threshold: float = 0.8) -> List[List[Any]]:
    """
    Encontra grupos de ofertas similares baseadas no título.
    
    Args:
        ofertas: Lista de ofertas
        threshold: Limiar de similaridade (0.0 a 1.0)
        
    Returns:
        Lista de grupos de ofertas similares
    """
    if not ofertas:
        return []
    
    # Normalizar todos os títulos
    normalized_titles = []
    for oferta in ofertas:
        titulo = getattr(oferta, 'titulo', '') or getattr(oferta, 'title', '')
        normalized_titles.append((oferta, normalize_title(titulo)))
    
    # Agrupar por similaridade
    groups = []
    used = set()
    
    for i, (oferta1, titulo1) in enumerate(normalized_titles):
        if i in used:
            continue
        
        group = [oferta1]
        used.add(i)
        
        for j, (oferta2, titulo2) in enumerate(normalized_titles[i+1:], i+1):
            if j in used:
                continue
            
            # Calcular similaridade
            similarity = _calculate_similarity(titulo1, titulo2)
            if similarity >= threshold:
                group.append(oferta2)
                used.add(j)
        
        if len(group) > 1:  # Só incluir grupos com mais de uma oferta
            groups.append(group)
    
    return groups


def _calculate_similarity(titulo1: str, titulo2: str) -> float:
    """
    Calcula similaridade entre dois títulos normalizados.
    
    Args:
        titulo1: Primeiro título
        titulo2: Segundo título
        
    Returns:
        Similaridade (0.0 a 1.0)
    """
    if not titulo1 or not titulo2:
        return 0.0
    
    # Dividir em palavras
    words1 = set(titulo1.split())
    words2 = set(titulo2.split())
    
    if not words1 or not words2:
        return 0.0
    
    # Calcular Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    
    return intersection / union
