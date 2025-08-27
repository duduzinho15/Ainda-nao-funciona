"""
Conversor de afiliados Mercado Livre para Garimpeiro Geek.

Implementa validação e geração de links de afiliado baseados nos exemplos
dos arquivos de referência.

REQUISITOS:
- Aceitar variações: produto.mercadolivre.com.br/MLB-..., www.mercadolivre.com.br/.../p/MLB...
- Shortlink: mercadolivre.com/sec/{token}
- Perfil social: www.mercadolivre.com.br/social/garimpeirogeek?... (como fallback válido)
- Remover UTMs irrelevantes e forçar uso de shortlink /sec/ quando disponível
"""

import logging
import re
import sqlite3
from typing import Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse

logger = logging.getLogger(__name__)

# Padrões de validação baseados nos exemplos
ML_SHORTLINK_PATTERN = re.compile(
    r"^https?://(?:www\.)?mercadolivre\.com(?:\.br)?/sec/[A-Za-z0-9]+$"
)
ML_SOCIAL_PATTERN = re.compile(
    r"^https?://(?:www\.)?mercadolivre\.com\.br/social/garimpeirogeek\?.*matt_word=garimpeirogeek"
)

# Padrões para URLs de produto (BLOQUEAR - precisam conversão)
ML_PRODUCT_PATTERNS = [
    r"^https?://(?:www\.)?mercadolivre\.com\.br/.*?/p/MLB\d+",
    r"^https?://(?:www\.)?mercadolivre\.com\.br/.*?/up/MLB\d+",
    r"^https?://produto\.mercadolivre\.com\.br/MLB-\d+",
    r"^https?://(?:www\.)?mercadolivre\.com\.br/.*?MLB\d+",
]

# Domínios válidos do Mercado Livre
VALID_ML_DOMAINS = [
    "mercadolivre.com.br",
    "www.mercadolivre.com.br",
    "mercadolivre.com",
    "www.mercadolivre.com",
    "produto.mercadolivre.com.br",
]

# Cache local para URLs de afiliado
CACHE_DB_PATH = "aff_cache.sqlite"

# Métricas para registro
METRICS = {
    "short_success": 0,
    "short_fail": 0,
    "social_accepted": 0,
    "product_blocked": 0,
}


def _ensure_cache_db():
    """Garante que o banco de cache existe"""
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ml_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT UNIQUE NOT NULL,
                affiliate_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao criar banco de cache: {e}")


def _normalize_ml_url(url: str) -> str:
    """
    Normaliza URL do Mercado Livre removendo parâmetros desnecessários
    e limpando a estrutura.
    """
    try:
        parsed = urlparse(url)

        # Remover parâmetros de query desnecessários
        query_params = parse_qs(parsed.query)

        # Manter apenas parâmetros essenciais
        essential_params = {}
        for key, value in query_params.items():
            if key.lower() not in [
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "utm_term",
                "utm_content",
                "src",
                "tracking",
                "pdp_filters",
                "deal_print_id",
                "position",
                "wid",
                "sid",
            ]:
                essential_params[key] = value[0] if value else ""

        # Reconstruir URL limpa
        clean_query = urlencode(essential_params) if essential_params else ""
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        if clean_query:
            clean_url += f"?{clean_query}"

        if parsed.fragment:
            clean_url += f"#{parsed.fragment}"

        return clean_url

    except Exception as e:
        logger.warning(f"Erro ao normalizar URL ML: {e}")
        return url


def _is_ml_product_url(url: str) -> bool:
    """
    Verifica se a URL é um produto do Mercado Livre (BLOQUEAR).
    """
    try:
        for pattern in ML_PRODUCT_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                METRICS["product_blocked"] += 1
                logger.warning(
                    f"URL de produto ML bloqueada (precisa conversão): {url}"
                )
                return True
        return False
    except Exception:
        return False


def _is_valid_ml_product_url(url: str) -> bool:
    """
    Verifica se a URL é um produto válido do Mercado Livre.
    Aceita URLs de produto, shortlinks e perfis sociais.
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        parsed.path.lower()

        # Verificar domínio
        if not any(
            domain.endswith(d) for d in ["mercadolivre.com.br", "mercadolivre.com"]
        ):
            return False

        # Verificar se é shortlink válido
        if ML_SHORTLINK_PATTERN.match(url):
            return True

        # Verificar se é perfil social válido
        if ML_SOCIAL_PATTERN.match(url):
            return True

        # Verificar se é produto (BLOQUEAR)
        if _is_ml_product_url(url):
            return False

        return False

    except Exception:
        return False


def _get_ml_validation_error(url: str) -> str:
    """
    Retorna mensagem de erro específica para ML baseada no tipo de URL
    """
    try:
        # Verificar se é produto (precisa conversão)
        if _is_ml_product_url(url):
            return (
                "URL de produto precisa ser convertida para shortlink /sec/ ou social"
            )

        # Verificar se é domínio inválido
        parsed = urlparse(url)
        if parsed.netloc.lower() not in VALID_ML_DOMAINS:
            return "Domínio não é válido para Mercado Livre"

        return "URL não segue padrão de afiliado ML (shortlink /sec/ ou social)"

    except Exception:
        return "URL não segue padrão de afiliado ML (shortlink /sec/ ou social)"


def validate_ml_url(url: str) -> Tuple[bool, str]:
    """
    Valida se uma URL do Mercado Livre é válida para afiliação.

    Regras:
    - Shortlink /sec/ → ACEITO
    - Página social garimpeirogeek → ACEITO
    - URL de produto → BLOQUEADO (precisa conversão)

    Args:
        url: URL para validar

    Returns:
        Tuple (is_valid, error_message)
    """
    if not url:
        return False, "URL vazia"

    # Verificar se é shortlink válido (ACEITO)
    if ML_SHORTLINK_PATTERN.match(url):
        METRICS["short_success"] += 1
        return True, ""

    # Verificar se é perfil social válido (ACEITO)
    if ML_SOCIAL_PATTERN.match(url):
        METRICS["social_accepted"] += 1
        return True, ""

    # Verificar se é URL de produto (BLOQUEADO)
    if _is_ml_product_url(url):
        return (
            False,
            "URL de produto precisa ser convertida para shortlink /sec/ ou social",
        )

    # Retornar erro específico
    return False, _get_ml_validation_error(url)


def get_cached_affiliate_url(original_url: str) -> Optional[str]:
    """Busca URL de afiliado em cache"""
    try:
        _ensure_cache_db()
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT affiliate_url FROM ml_cache
            WHERE original_url = ? AND
                  (julianday('now') - julianday(last_used)) < 30
        """,
            [original_url],
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            # Atualizar último uso
            _update_cache_usage(original_url)
            return result[0]

        return None

    except Exception as e:
        logger.error(f"Erro ao buscar cache: {e}")
        return None


def _update_cache_usage(original_url: str):
    """Atualiza timestamp de último uso"""
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE ml_cache
            SET last_used = CURRENT_TIMESTAMP
            WHERE original_url = ?
        """,
            [original_url],
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao atualizar cache: {e}")


def cache_affiliate_url(original_url: str, affiliate_url: str):
    """Armazena URL de afiliado em cache"""
    try:
        _ensure_cache_db()
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO ml_cache (original_url, affiliate_url)
            VALUES (?, ?)
        """,
            [original_url, affiliate_url],
        )

        conn.commit()
        conn.close()
        logger.info(f"URL de afiliado ML armazenada em cache: {affiliate_url[:30]}...")

    except Exception as e:
        logger.error(f"Erro ao armazenar cache: {e}")


def generate_ml_shortlink(product_url: str) -> Tuple[bool, str, str]:
    """
    Gera shortlink para produto do Mercado Livre.

    Args:
        product_url: URL do produto

    Returns:
        Tuple (success, shortlink, error_message)
    """
    try:
        # Normalizar URL primeiro
        normalized_url = _normalize_ml_url(product_url)

        # Verificar se é produto válido
        if not _is_ml_product_url(normalized_url):
            return False, "", "URL não é um produto válido do ML"

        # Verificar cache primeiro
        cached = get_cached_affiliate_url(normalized_url)
        if cached:
            logger.info(f"Shortlink ML encontrado em cache: {cached}")
            return True, cached, ""

        # Simular geração via painel/portal (conforme especificação)
        # Em produção, isso seria uma chamada para a API do ML
        import hashlib
        import time

        # Gerar ID único baseado na URL normalizada e timestamp
        url_hash = hashlib.md5(normalized_url.encode()).hexdigest()[:8]
        timestamp = str(int(time.time()))[-4:]
        shortlink_id = f"{url_hash}{timestamp}"

        shortlink = f"https://mercadolivre.com/sec/{shortlink_id}"

        # Armazenar em cache
        cache_affiliate_url(normalized_url, shortlink)

        logger.info(f"Shortlink ML gerado: {shortlink}")
        METRICS["short_success"] += 1
        return True, shortlink, ""

    except Exception as e:
        error_msg = f"Erro ao gerar shortlink ML: {e}"
        logger.error(error_msg)
        METRICS["short_fail"] += 1
        return False, "", error_msg


def is_ml_affiliate_url(url: str) -> bool:
    """Verifica se uma URL é um link de afiliado válido do ML"""
    is_valid, _ = validate_ml_url(url)
    return is_valid


def get_cache_stats() -> dict:
    """Retorna estatísticas do cache ML"""
    try:
        _ensure_cache_db()
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()

        # Total de entradas
        cursor.execute("SELECT COUNT(*) FROM ml_cache")
        total = cursor.fetchone()[0]

        # Entradas recentes (últimos 7 dias)
        cursor.execute(
            """
            SELECT COUNT(*) FROM ml_cache
            WHERE (julianday('now') - julianday(created_at)) < 7
        """
        )
        recent = cursor.fetchone()[0]

        conn.close()

        return {
            "total_entries": total,
            "recent_entries": recent,
            "metrics": METRICS.copy(),
        }

    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return {"error": str(e)}


def get_metrics() -> dict:
    """Retorna métricas de validação ML"""
    return METRICS.copy()


def reset_metrics():
    """Reseta métricas para testes"""
    global METRICS
    METRICS = {
        "short_success": 0,
        "short_fail": 0,
        "social_accepted": 0,
        "product_blocked": 0,
    }
