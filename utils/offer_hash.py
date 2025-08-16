# -*- coding: utf-8 -*-
"""
Sistema de Hash para Deduplicação de Ofertas - Garimpeiro Geek

Este módulo implementa funções para gerar hashes únicos de ofertas,
permitindo detecção confiável de duplicatas baseada em:
- URL do produto (normalizada)
- Título (normalizado)
- Preço (normalizado)
- Loja (normalizada)
"""

import hashlib
import re
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs, urlunparse

logger = logging.getLogger(__name__)

def normalize_url(url: str) -> str:
    """
    Normaliza URL removendo parâmetros desnecessários e padronizando formato
    
    Args:
        url: URL original
        
    Returns:
        URL normalizada
    """
    if not url or not isinstance(url, str):
        return ""
    
    try:
        # Parse da URL
        parsed = urlparse(url.strip())
        
        # Normaliza domínio (remove www, converte para minúsculas)
        netloc = parsed.netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        
        # Normaliza path (remove trailing slash, converte para minúsculas)
        path = parsed.path.lower().rstrip('/')
        
        # Remove fragmentos
        fragment = ""
        
        # Filtra parâmetros de query relevantes
        query_params = parse_qs(parsed.query)
        
        # Parâmetros que devem ser mantidos (identificam o produto)
        relevant_params = {}
        
        # Amazon: mantém apenas ASIN (mais importante para deduplicação)
        if 'amazon' in netloc:
            if 'dp' in path:
                # Extrai ASIN do path
                asin_match = re.search(r'/dp/([A-Z0-9]{10})', path)
                if asin_match:
                    relevant_params['asin'] = [asin_match.group(1)]
                    # Para Amazon, ASIN é suficiente - não precisa de tag
        
        # Shopee: mantém product_id
        elif 'shopee' in netloc:
            if 'product' in path:
                product_match = re.search(r'/product/([^/?]+)', path)
                if product_match:
                    relevant_params['product_id'] = [product_match.group(1)]
        
        # AliExpress: mantém product_id
        elif 'aliexpress' in netloc:
            if 'item' in path:
                item_match = re.search(r'/item/([^/?]+)', path)
                if item_match:
                    relevant_params['product_id'] = [item_match.group(1)]
        
        # Mercado Livre: mantém item_id
        elif 'mercadolivre' in netloc:
            if 'MLB' in path:
                item_match = re.search(r'MLB[0-9]+', path)
                if item_match:
                    relevant_params['item_id'] = [item_match.group(0)]
        
        # KaBuM: mantém produto_id
        elif 'kabum' in netloc:
            if 'produto' in path:
                produto_match = re.search(r'/produto/([^/?]+)', path)
                if produto_match:
                    relevant_params['produto_id'] = [produto_match.group(1)]
        
        # Samsung: mantém product_id
        elif 'samsung' in netloc:
            if 'produto' in path:
                produto_match = re.search(r'/produto/([^/?]+)', path)
                if produto_match:
                    relevant_params['produto_id'] = [produto_match.group(1)]
        
        # LG: mantém product_id
        elif 'lg' in netloc:
            if 'produto' in path:
                produto_match = re.search(r'/produto/([^/?]+)', path)
                if produto_match:
                    relevant_params['produto_id'] = [produto_match.group(1)]
        
        # Comfy: mantém product_id
        elif 'comfy' in netloc:
            if 'produto' in path:
                produto_match = re.search(r'/produto/([^/?]+)', path)
                if produto_match:
                    relevant_params['produto_id'] = [produto_match.group(1)]
        
        # Trocafy: mantém product_id
        elif 'trocafy' in netloc:
            if 'produto' in path:
                produto_match = re.search(r'/produto/([^/?]+)', path)
                if produto_match:
                    relevant_params['produto_id'] = [produto_match.group(1)]
        
        # Reconstrói query string apenas com parâmetros relevantes
        if relevant_params:
            from urllib.parse import urlencode
            query = urlencode(relevant_params, doseq=True)
        else:
            query = ""
        
        # Reconstrói URL normalizada
        normalized_url = urlunparse((
            parsed.scheme,
            netloc,
            path,
            parsed.params,
            query,
            fragment
        ))
        
        logger.debug(f"🔗 URL normalizada: {url} -> {normalized_url}")
        return normalized_url
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao normalizar URL {url}: {e}")
        return url.strip()

def normalize_title(title: str) -> str:
    """
    Normaliza título removendo elementos desnecessários
    
    Args:
        title: Título original
        
    Returns:
        Título normalizado
    """
    if not title or not isinstance(title, str):
        return ""
    
    try:
        # Converte para minúsculas
        normalized = title.lower().strip()
        
        # Remove caracteres especiais e números de versão
        normalized = re.sub(r'[^\w\s\-]', ' ', normalized)
        
        # Remove apenas palavras muito comuns que não identificam o produto
        stop_words = {
            'frete', 'gratis', 'grátis', 'envio', 'entrega'
        }
        
        words = normalized.split()
        filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
        
        # Reconstrói título normalizado
        normalized_title = ' '.join(filtered_words)
        
        logger.debug(f"📝 Título normalizado: {title} -> {normalized_title}")
        return normalized_title
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao normalizar título {title}: {e}")
        return title.strip()

def normalize_price(price: Any) -> str:
    """
    Normaliza preço removendo formatação e convertendo para formato padrão
    
    Args:
        price: Preço em qualquer formato
        
    Returns:
        Preço normalizado como string
    """
    if price is None:
        return ""
    
    try:
        price_str = str(price).strip()
        
        # Remove símbolos de moeda e espaços
        price_str = re.sub(r'[R$\s]', '', price_str)
        
        # Substitui vírgula por ponto para decimal
        price_str = price_str.replace(',', '.')
        
        # Extrai apenas números e ponto decimal
        price_match = re.search(r'(\d+\.?\d*)', price_str)
        if price_match:
            normalized_price = price_match.group(1)
            
            # Converte para float e volta para string para padronizar
            try:
                price_float = float(normalized_price)
                normalized_price = f"{price_float:.2f}"
            except ValueError:
                pass
            
            logger.debug(f"💰 Preço normalizado: {price} -> {normalized_price}")
            return normalized_price
        
        return price_str
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao normalizar preço {price}: {e}")
        return str(price).strip()

def normalize_store(store: str) -> str:
    """
    Normaliza nome da loja para consistência
    
    Args:
        store: Nome da loja
        
    Returns:
        Nome da loja normalizado
    """
    if not store or not isinstance(store, str):
        return ""
    
    try:
        # Converte para minúsculas e remove espaços extras
        normalized = store.lower().strip()
        
        # Mapeamento de aliases para nomes padrão
        store_aliases = {
            'mercado livre': 'mercadolivre',
            'magazine luiza': 'magalu',
            'ml': 'mercadolivre',
            'kabum!': 'kabum',
            'samsung br': 'samsung',
            'lg br': 'lg',
            'comfy br': 'comfy',
            'trocafy br': 'trocafy',
            'amazon.com.br': 'amazon',
            'shopee.com.br': 'shopee',
            'aliexpress.com': 'aliexpress',
            'pt.aliexpress.com': 'aliexpress'
        }
        
        # Aplica aliases
        for alias, standard in store_aliases.items():
            if alias in normalized:
                normalized = standard
                break
        
        # Remove caracteres especiais
        normalized = re.sub(r'[^\w]', '', normalized)
        
        logger.debug(f"🏪 Loja normalizada: {store} -> {normalized}")
        return normalized
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao normalizar loja {store}: {e}")
        return store.strip()

def offer_hash(offer: Dict[str, Any]) -> str:
    """
    Gera hash único para uma oferta baseado em dados normalizados
    
    Args:
        offer: Dicionário com dados da oferta
        
    Returns:
        Hash SHA-256 único da oferta
    """
    try:
        # Extrai campos relevantes
        url = offer.get('url_produto') or offer.get('affiliate_url') or offer.get('url', '')
        title = offer.get('titulo') or offer.get('title', '')
        price = offer.get('preco_atual') or offer.get('price') or offer.get('preco', '')
        store = offer.get('loja') or offer.get('store', '')
        
        # Normaliza campos
        normalized_url = normalize_url(url)
        normalized_title = normalize_title(title)
        normalized_price = normalize_price(price)
        normalized_store = normalize_store(store)
        
        # Cria string de dados normalizados
        data_string = f"{normalized_url}|{normalized_title}|{normalized_price}|{normalized_store}"
        
        # Gera hash SHA-256
        hash_object = hashlib.sha256(data_string.encode('utf-8'))
        offer_hash = hash_object.hexdigest()
        
        logger.debug(f"🔐 Hash gerado para oferta: {offer_hash[:16]}...")
        logger.debug(f"   URL: {normalized_url}")
        logger.debug(f"   Título: {normalized_title}")
        logger.debug(f"   Preço: {normalized_price}")
        logger.debug(f"   Loja: {normalized_store}")
        
        return offer_hash
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar hash da oferta: {e}")
        # Fallback: hash da URL se disponível
        if url:
            fallback_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
            logger.warning(f"⚠️ Usando hash fallback: {fallback_hash[:16]}...")
            return fallback_hash
        return ""

def offer_hash_components(offer: Dict[str, Any]) -> Dict[str, str]:
    """
    Retorna componentes normalizados usados para gerar o hash
    
    Args:
        offer: Dicionário com dados da oferta
        
    Returns:
        Dicionário com componentes normalizados
    """
    try:
        url = offer.get('url_produto') or offer.get('affiliate_url') or offer.get('url', '')
        title = offer.get('titulo') or offer.get('title', '')
        price = offer.get('preco_atual') or offer.get('price') or offer.get('preco', '')
        store = offer.get('loja') or offer.get('store', '')
        
        return {
            'normalized_url': normalize_url(url),
            'normalized_title': normalize_title(title),
            'normalized_price': normalize_price(price),
            'normalized_store': normalize_store(store),
            'offer_hash': offer_hash(offer)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao extrair componentes da oferta: {e}")
        return {}

def is_similar_offer(offer1: Dict[str, Any], offer2: Dict[str, Any], similarity_threshold: float = 0.8) -> bool:
    """
    Verifica se duas ofertas são similares baseado em similaridade de texto
    
    Args:
        offer1: Primeira oferta
        offer2: Segunda oferta
        similarity_threshold: Limite de similaridade (0.0 a 1.0)
        
    Returns:
        True se as ofertas são similares
    """
    try:
        from difflib import SequenceMatcher
        
        # Extrai títulos
        title1 = offer1.get('titulo') or offer1.get('title', '')
        title2 = offer2.get('titulo') or offer2.get('title', '')
        
        if not title1 or not title2:
            return False
        
        # Calcula similaridade entre títulos
        similarity = SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
        
        logger.debug(f"🔍 Similaridade entre ofertas: {similarity:.2f}")
        logger.debug(f"   Título 1: {title1}")
        logger.debug(f"   Título 2: {title2}")
        
        return similarity >= similarity_threshold
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar similaridade: {e}")
        return False

def validate_offer_data(offer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida e normaliza dados da oferta
    
    Args:
        offer: Dicionário com dados da oferta
        
    Returns:
        Dicionário com dados validados e normalizados
    """
    try:
        validated_offer = offer.copy()
        
        # Valida campos obrigatórios
        required_fields = ['titulo', 'preco_atual', 'loja']
        missing_fields = [field for field in required_fields if not offer.get(field)]
        
        if missing_fields:
            logger.warning(f"⚠️ Campos obrigatórios ausentes: {missing_fields}")
        
        # Normaliza campos
        if 'url_produto' in offer:
            validated_offer['url_produto'] = normalize_url(offer['url_produto'])
        
        if 'titulo' in offer:
            validated_offer['titulo'] = offer['titulo'].strip()
        
        if 'preco_atual' in offer:
            validated_offer['preco_atual'] = normalize_price(offer['preco_atual'])
        
        if 'loja' in offer:
            validated_offer['loja'] = normalize_store(offer['loja'])
        
        # Gera hash da oferta
        validated_offer['offer_hash'] = offer_hash(validated_offer)
        
        logger.info(f"✅ Oferta validada: {validated_offer['offer_hash'][:16]}...")
        return validated_offer
        
    except Exception as e:
        logger.error(f"❌ Erro ao validar oferta: {e}")
        return offer

if __name__ == "__main__":
    # Teste das funções
    test_offer = {
        'url_produto': 'https://www.amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogee-20&ref=test',
        'titulo': 'Smartphone Samsung Galaxy S21 128GB - NOVO LANÇAMENTO!',
        'preco_atual': 'R$ 2.999,00',
        'loja': 'Amazon.com.br'
    }
    
    print("🧪 Teste do sistema de hash de ofertas")
    print("=" * 50)
    
    # Testa normalização
    print(f"URL original: {test_offer['url_produto']}")
    print(f"URL normalizada: {normalize_url(test_offer['url_produto'])}")
    print()
    
    print(f"Título original: {test_offer['titulo']}")
    print(f"Título normalizado: {normalize_title(test_offer['titulo'])}")
    print()
    
    print(f"Preço original: {test_offer['preco_atual']}")
    print(f"Preço normalizado: {normalize_price(test_offer['preco_atual'])}")
    print()
    
    print(f"Loja original: {test_offer['loja']}")
    print(f"Loja normalizada: {normalize_store(test_offer['loja'])}")
    print()
    
    # Testa hash
    hash_result = offer_hash(test_offer)
    print(f"Hash da oferta: {hash_result}")
    print()
    
    # Testa componentes
    components = offer_hash_components(test_offer)
    print("Componentes normalizados:")
    for key, value in components.items():
        if key != 'offer_hash':
            print(f"  {key}: {value}")
    print(f"  offer_hash: {components['offer_hash'][:16]}...")
    print()
    
    # Testa validação
    validated = validate_offer_data(test_offer)
    print("Oferta validada:")
    for key, value in validated.items():
        if key == 'offer_hash':
            print(f"  {key}: {value[:16]}...")
        else:
            print(f"  {key}: {value}")
