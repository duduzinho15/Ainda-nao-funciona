"""
Conversor de afiliados Magazine Luiza para Garimpeiro Geek.

Implementa validação e geração de links de afiliado baseados nos exemplos
dos arquivos de referência.

REQUISITOS:
- Aceitar APENAS URLs de vitrine: magazinevoce.com.br/magazinegarimpeirogeek/{slug}/p/{sku}/...
- Bloquear magazineluiza.com.br (sem vitrine) como não afiliado
- Normalizar slug/params e remover UTMs
"""

import logging
import re
import sqlite3
from typing import Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse

logger = logging.getLogger(__name__)

# Padrões de validação baseados nos exemplos
MAGAZINE_VITRINE_PATTERN = (
    r"^https?://(?:www\.)?magazinevoce\.com\.br/magazinegarimpeirogeek/.*?/p/\d+"
)

# Domínios válidos (apenas magazinevoce.com.br com vitrine)
VALID_MAGAZINE_DOMAINS = ["magazinevoce.com.br", "www.magazinevoce.com.br"]

# Domínios bloqueados (magazineluiza.com.br sem vitrine)
BLOCKED_MAGAZINE_DOMAINS = ["magazineluiza.com.br", "www.magazineluiza.com.br"]

# Cache local para URLs de afiliado
CACHE_DB_PATH = "aff_cache.sqlite"

# Métricas para registro
METRICS = {"vitrine_accepted": 0, "domain_blocked": 0}


def _ensure_cache_db():
    """Garante que o banco de cache existe"""
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS magazine_cache (
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


def _normalize_magazine_url(url: str) -> str:
    """
    Normaliza URL do Magazine Luiza removendo parâmetros desnecessários
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
                "ref",
                "tracking",
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
        logger.warning(f"Erro ao normalizar URL Magazine Luiza: {e}")
        return url


def _is_valid_magazine_vitrine_url(url: str) -> bool:
    """
    Verifica se é uma URL de vitrine válida do Magazine Luiza.
    Aceita APENAS URLs com magazinegarimpeirogeek.
    """
    try:
        parsed = urlparse(url)

        # Verificar domínio válido (apenas magazinevoce.com.br)
        if parsed.netloc.lower() not in VALID_MAGAZINE_DOMAINS:
            return False

        # Verificar se tem estrutura de vitrine válida
        if re.match(MAGAZINE_VITRINE_PATTERN, url, re.IGNORECASE):
            return True

        return False

    except Exception:
        return False


def _is_blocked_magazine_domain(url: str) -> bool:
    """
    Verifica se é um domínio bloqueado do Magazine Luiza.
    Bloqueia magazineluiza.com.br (sem vitrine).
    """
    try:
        parsed = urlparse(url)
        if parsed.netloc.lower() in BLOCKED_MAGAZINE_DOMAINS:
            METRICS["domain_blocked"] += 1
            logger.warning(f"Domínio Magazine Luiza bloqueado: {url}")
            return True
        return False
    except Exception:
        return False


def _get_magazine_validation_error(url: str) -> str:
    """
    Retorna mensagem de erro específica para Magazine Luiza baseada no tipo de URL
    """
    try:
        parsed = urlparse(url)

        # Verificar se é domínio bloqueado
        if _is_blocked_magazine_domain(url):
            return "Domínio magazineluiza.com.br não é válido para afiliação (use vitrine magazinevoce.com.br)"

        # Verificar se é domínio inválido
        if parsed.netloc.lower() not in VALID_MAGAZINE_DOMAINS:
            return "Domínio não é válido para Magazine Luiza (use magazinevoce.com.br)"

        # Verificar se não tem estrutura de vitrine
        if not re.match(MAGAZINE_VITRINE_PATTERN, url, re.IGNORECASE):
            return "URL deve seguir padrão de vitrine: magazinevoce.com.br/magazinegarimpeirogeek/..."

        return "URL não segue padrão de afiliado Magazine Luiza (vitrine)"

    except Exception:
        return "URL não segue padrão de afiliado Magazine Luiza (vitrine)"


def validate_magazine_url(url: str) -> Tuple[bool, str]:
    """
    Valida se uma URL do Magazine Luiza é válida para afiliação.

    Regras:
    - Vitrine magazinevoce.com.br/magazinegarimpeirogeek/... → ACEITO
    - Domínio magazineluiza.com.br → BLOQUEADO
    - Outros domínios → BLOQUEADO

    Args:
        url: URL para validar

    Returns:
        Tuple (is_valid, error_message)
    """
    if not url:
        return False, "URL vazia"

    # Verificar se é domínio bloqueado (BLOQUEADO)
    if _is_blocked_magazine_domain(url):
        return (
            False,
            "Domínio magazineluiza.com.br não é válido para afiliação (use vitrine magazinevoce.com.br)",
        )

    # Verificar se é vitrine válida (ACEITO)
    if _is_valid_magazine_vitrine_url(url):
        METRICS["vitrine_accepted"] += 1
        return True, ""

    # Retornar erro específico
    return False, _get_magazine_validation_error(url)


def get_cached_affiliate_url(original_url: str) -> Optional[str]:
    """Busca URL de afiliado em cache"""
    try:
        _ensure_cache_db()
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT affiliate_url FROM magazine_cache
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
            UPDATE magazine_cache
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
            INSERT OR REPLACE INTO magazine_cache (original_url, affiliate_url)
            VALUES (?, ?)
        """,
            [original_url, affiliate_url],
        )

        conn.commit()
        conn.close()
        logger.info(
            f"URL de afiliado Magazine Luiza armazenada em cache: {affiliate_url[:30]}..."
        )

    except Exception as e:
        logger.error(f"Erro ao armazenar cache: {e}")


def generate_magazine_affiliate_url(product_url: str) -> Tuple[bool, str, str]:
    """
    Gera URL de afiliado para produto do Magazine Luiza.

    Args:
        product_url: URL do produto

    Returns:
        Tuple (success, affiliate_url, error_message)
    """
    try:
        # Normalizar URL primeiro
        normalized_url = _normalize_magazine_url(product_url)

        # Verificar se já é uma URL de afiliado válida
        if validate_magazine_url(normalized_url)[0]:
            logger.info("URL já é uma URL de afiliado válida")
            cache_affiliate_url(normalized_url, normalized_url)
            return True, normalized_url, ""

        # Verificar se é vitrine válida para conversão
        if not _is_valid_magazine_vitrine_url(normalized_url):
            return False, "", "URL não é uma vitrine válida do Magazine Luiza"

        # Verificar cache primeiro
        cached = get_cached_affiliate_url(normalized_url)
        if cached:
            logger.info(f"URL de afiliado Magazine Luiza encontrada em cache: {cached}")
            return True, cached, ""

        # Simular geração via painel/portal (conforme especificação)
        # Em produção, isso seria uma chamada para a API do Magazine Luiza
        import hashlib
        import time

        # Gerar ID único baseado na URL normalizada e timestamp
        url_hash = hashlib.md5(normalized_url.encode()).hexdigest()[:8]
        timestamp = str(int(time.time()))[-4:]
        affiliate_id = f"{url_hash}{timestamp}"

        # Construir URL de afiliado (manter estrutura de vitrine)
        parsed = urlparse(normalized_url)
        affiliate_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?affiliate_id={affiliate_id}"

        # Armazenar em cache
        cache_affiliate_url(normalized_url, affiliate_url)

        logger.info(f"URL de afiliado Magazine Luiza gerada: {affiliate_url}")
        return True, affiliate_url, ""

    except Exception as e:
        error_msg = f"Erro ao gerar URL de afiliado Magazine Luiza: {e}"
        logger.error(error_msg)
        return False, "", error_msg


def is_magazine_affiliate_url(url: str) -> bool:
    """Verifica se uma URL é um link de afiliado válido do Magazine Luiza"""
    is_valid, _ = validate_magazine_url(url)
    return is_valid


def get_cache_stats() -> dict:
    """Retorna estatísticas do cache Magazine Luiza"""
    try:
        _ensure_cache_db()
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()

        # Total de entradas
        cursor.execute("SELECT COUNT(*) FROM magazine_cache")
        total = cursor.fetchone()[0]

        # Entradas recentes (últimos 7 dias)
        cursor.execute(
            """
            SELECT COUNT(*) FROM magazine_cache
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
    """Retorna métricas de validação Magazine Luiza"""
    return METRICS.copy()


def reset_metrics():
    """Reseta métricas para testes"""
    global METRICS
    METRICS = {"vitrine_accepted": 0, "domain_blocked": 0}
