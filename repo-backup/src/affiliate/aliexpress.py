"""
Conversor de afiliados AliExpress para Garimpeiro Geek.

Implementa geração de shortlinks e validações baseadas nos exemplos
dos arquivos de referência.
"""

import logging
import os
import re
import sqlite3
from typing import Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Padrão de validação baseado nos exemplos
ALIEXPRESS_SHORTLINK_PATTERN = r"^https?://s\.click\.aliexpress\.com/e/[A-Za-z0-9_-]+$"
ALIEXPRESS_PRODUCT_PATTERN = r"^https?://(?:pt\.)?aliexpress\.com/item/\d+\.html"

# Cache local para shortlinks
CACHE_DB_PATH = "aff_cache.sqlite"


def _ensure_cache_db():
    """Garante que o banco de cache existe"""
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS aliexpress_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT UNIQUE NOT NULL,
                shortlink TEXT NOT NULL,
                tracking_id TEXT DEFAULT 'telegram',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao criar banco de cache: {e}")


def validate_aliexpress_url(url: str) -> Tuple[bool, str]:
    """
    Valida se uma URL do AliExpress é válida para afiliação.

    Args:
        url: URL para validar

    Returns:
        Tuple (is_valid, error_message)
    """
    if not url:
        return False, "URL vazia"

    # Verificar se é shortlink válido
    if re.match(ALIEXPRESS_SHORTLINK_PATTERN, url):
        return True, ""

    # Verificar se é URL de produto válida
    if re.match(ALIEXPRESS_PRODUCT_PATTERN, url):
        return True, ""

    return False, "URL não segue padrão de afiliado AliExpress"


def _is_valid_aliexpress_product_url(url: str) -> bool:
    """Verifica se é uma URL de produto válida do AliExpress"""
    try:
        parsed = urlparse(url)

        # Domínios válidos
        valid_domains = ["aliexpress.com", "pt.aliexpress.com"]
        if parsed.netloc.lower() not in valid_domains:
            return False

        # Verificar se tem estrutura de produto (/item/{id}.html)
        if re.search(r"/item/\d+\.html", parsed.path):
            return True

        return False

    except Exception:
        return False


def get_cached_shortlink(original_url: str) -> Optional[str]:
    """Busca shortlink em cache"""
    try:
        _ensure_cache_db()
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT shortlink FROM aliexpress_cache
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
            UPDATE aliexpress_cache
            SET last_used = CURRENT_TIMESTAMP
            WHERE original_url = ?
        """,
            [original_url],
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao atualizar cache: {e}")


def cache_shortlink(original_url: str, shortlink: str, tracking_id: str = "telegram"):
    """Armazena shortlink em cache"""
    try:
        _ensure_cache_db()
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO aliexpress_cache
            (original_url, shortlink, tracking_id)
            VALUES (?, ?, ?)
        """,
            [original_url, shortlink, tracking_id],
        )

        conn.commit()
        conn.close()
        logger.info(f"Shortlink AliExpress armazenado em cache: {shortlink[:30]}...")

    except Exception as e:
        logger.error(f"Erro ao armazenar cache: {e}")


def generate_aliexpress_shortlink(
    product_url: str, tracking: str = "telegram"
) -> Tuple[bool, str, str]:
    """
    Gera shortlink para produto do AliExpress.

    Args:
        product_url: URL do produto
        tracking: ID de tracking (padrão: telegram)

    Returns:
        Tuple (success, shortlink, error_message)
    """
    try:
        # Validar URL de produto
        if not _is_valid_aliexpress_product_url(product_url):
            return False, "", "URL de produto inválida"

        # Validar tracking ID
        valid_tracking_ids = ["telegram", "web", "mobile", "app"]
        if tracking not in valid_tracking_ids:
            return (
                False,
                "",
                f"Tracking ID inválido: {tracking}. Válidos: {', '.join(valid_tracking_ids)}",
            )

        # Verificar cache primeiro
        cached = get_cached_shortlink(product_url)
        if cached:
            logger.info(f"Shortlink AliExpress encontrado em cache: {cached}")
            return True, cached, ""

        # Simular geração via painel/portal (conforme especificação)
        # Em produção, isso seria uma chamada para a API do AliExpress
        import hashlib
        import time

        # Gerar ID único baseado na URL e timestamp
        url_hash = hashlib.md5(product_url.encode()).hexdigest()[:8]
        timestamp = str(int(time.time()))[-4:]
        shortlink_id = f"{url_hash}{timestamp}"

        # Formato baseado nos exemplos: s.click.aliexpress.com/e/{id}
        shortlink = f"https://s.click.aliexpress.com/e/{shortlink_id}"

        # Armazenar em cache
        cache_shortlink(product_url, shortlink, tracking)

        logger.info(f"Shortlink AliExpress gerado: {shortlink} (tracking: {tracking})")
        return True, shortlink, ""

    except Exception as e:
        error_msg = f"Erro ao gerar shortlink AliExpress: {e}"
        logger.error(error_msg)
        return False, "", error_msg


def is_aliexpress_affiliate_url(url: str) -> bool:
    """Verifica se uma URL é um link de afiliado válido do AliExpress"""
    is_valid, _ = validate_aliexpress_url(url)
    return is_valid


def get_cache_stats() -> dict:
    """Retorna estatísticas do cache AliExpress"""
    try:
        _ensure_cache_db()
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()

        # Total de entradas
        cursor.execute("SELECT COUNT(*) FROM aliexpress_cache")
        total = cursor.fetchone()[0]

        # Entradas recentes (últimos 7 dias)
        cursor.execute(
            """
            SELECT COUNT(*) FROM aliexpress_cache
            WHERE (julianday('now') - julianday(created_at)) < 7
        """
        )
        recent = cursor.fetchone()[0]

        # Entradas antigas (mais de 30 dias)
        cursor.execute(
            """
            SELECT COUNT(*) FROM aliexpress_cache
            WHERE (julianday('now') - julianday(last_used)) > 30
        """
        )
        old = cursor.fetchone()[0]

        # Tracking IDs utilizados
        cursor.execute(
            """
            SELECT tracking_id, COUNT(*) as count
            FROM aliexpress_cache
            GROUP BY tracking_id
        """
        )
        tracking_stats = dict(cursor.fetchall())

        conn.close()

        return {
            "total_entries": total,
            "recent_entries": recent,
            "old_entries": old,
            "tracking_stats": tracking_stats,
            "cache_db_path": CACHE_DB_PATH,
        }

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do cache: {e}")
        return {"error": str(e)}


def get_tracking_id() -> str:
    """Retorna o tracking ID configurado (padrão: telegram)"""
    return os.getenv("ALIEXPRESS_TRACKING_ID", "telegram")


# Teste dos exemplos do arquivo de referência
if __name__ == "__main__":
    print("🧪 TESTANDO CONVERSOR ALIEXPRESS COM EXEMPLOS DO ARQUIVO")
    print("=" * 70)

    # Exemplos do arquivo "Informações base de geração de link.txt"
    test_cases = [
        "https://s.click.aliexpress.com/e/_opftn1L",
        "https://s.click.aliexpress.com/e/_okCiVDF",
        "https://s.click.aliexpress.com/e/_oo01Cb7",
        "https://s.click.aliexpress.com/e/_oBT0z5b",
        "https://s.click.aliexpress.com/e/_oEodyO1",
        "https://pt.aliexpress.com/item/1005006756452012.html?scm=null&pvid=null&gatewayAdapt=glo2bra",
        "https://pt.aliexpress.com/item/1005007488115262.html?scm=null&pvid=null&gatewayAdapt=glo2bra",
        "https://exemplo-invalido.com/produto",
    ]

    for url in test_cases:
        print(f"\n🔍 Testando: {url}")

        is_valid, error = validate_aliexpress_url(url)

        if is_valid:
            print("   ✅ VÁLIDO")
        else:
            print(f"   ❌ INVÁLIDO: {error}")

    # Teste de geração de shortlink
    print("\n🔧 TESTANDO GERAÇÃO DE SHORTLINK:")
    test_product_url = "https://pt.aliexpress.com/item/1005006756452012.html?scm=null&pvid=null&gatewayAdapt=glo2bra"
    tracking_id = get_tracking_id()

    success, shortlink, error = generate_aliexpress_shortlink(
        test_product_url, tracking_id
    )

    if success:
        print(f"   ✅ SUCESSO: {shortlink}")
        print(f"   📍 Tracking ID: {tracking_id}")
    else:
        print(f"   ❌ FALHA: {error}")

    # Estatísticas do cache
    print("\n📊 ESTATÍSTICAS DO CACHE:")
    stats = get_cache_stats()
    for key, value in stats.items():
        if key == "tracking_stats":
            print(f"   {key}:")
            for tid, count in value.items():
                print(f"     {tid}: {count}")
        else:
            print(f"   {key}: {value}")
