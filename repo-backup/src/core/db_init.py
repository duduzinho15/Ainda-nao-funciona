"""
Inicialização dos bancos de dados SQLite
Cria/valida schemas para aff_cache.sqlite e analytics.sqlite
"""

import logging
from pathlib import Path
from typing import Dict, List

from src.utils.sqlite_helpers import execute, table_exists

logger = logging.getLogger(__name__)

# Configuração dos bancos
DB_CONFIG = {
    "aff_cache": "src/db/aff_cache.sqlite",
    "analytics": "src/db/analytics.sqlite",
}

# Schema para aff_cache.sqlite
AFF_CACHE_SCHEMA = """
-- Cache de shortlinks e deeplinks
CREATE TABLE IF NOT EXISTS shortlinks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    platform      TEXT NOT NULL,      -- shopee | mercadolivre | aliexpress | awin | amazon | magalu
    merchant      TEXT,
    original_url  TEXT NOT NULL,
    affiliate_url TEXT NOT NULL,
    subid         TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at    DATETIME,
    meta_json     TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_shortlinks_platform_original
ON shortlinks(platform, original_url);

CREATE INDEX IF NOT EXISTS ix_shortlinks_platform ON shortlinks(platform);
CREATE INDEX IF NOT EXISTS ix_shortlinks_created ON shortlinks(created_at);
"""

# Schema para analytics.sqlite
ANALYTICS_SCHEMA = """
-- Produtos normalizados (chave: platform + canonical_url)
CREATE TABLE IF NOT EXISTS products (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    platform      TEXT NOT NULL,
    store         TEXT,
    canonical_url TEXT NOT NULL,
    sku           TEXT,
    asin          TEXT,                    -- Amazon Standard Identification Number
    title         TEXT,
    first_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen_at  DATETIME
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_products_platform_url
ON products(platform, canonical_url);

CREATE INDEX IF NOT EXISTS ix_products_platform ON products(platform);
CREATE INDEX IF NOT EXISTS ix_products_store ON products(store);
CREATE INDEX IF NOT EXISTS ix_products_last_seen ON products(last_seen_at);

-- Índices para ASIN (Amazon)
CREATE UNIQUE INDEX IF NOT EXISTS ux_products_asin ON products(asin) WHERE asin IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_products_asin ON products(asin);

-- Histórico nativo (coletado pelos scrapers das lojas)
CREATE TABLE IF NOT EXISTS price_history (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id          INTEGER NOT NULL,
    collected_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    price_cents         INTEGER NOT NULL,
    price_before_cents  INTEGER,
    in_stock            INTEGER DEFAULT 1,
    source              TEXT,        -- scraper_loja | comunidade
    extra_json          TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_price_history_product_time
ON price_history(product_id, collected_at);

CREATE INDEX IF NOT EXISTS ix_price_history_collected ON price_history(collected_at);
CREATE INDEX IF NOT EXISTS ix_price_history_source ON price_history(source);

-- Agregado diário nativo
CREATE TABLE IF NOT EXISTS price_daily (
    product_id   INTEGER NOT NULL,
    day          DATE NOT NULL,
    min_cents    INTEGER NOT NULL,
    max_cents    INTEGER NOT NULL,
    avg_cents    INTEGER NOT NULL,
    count_points INTEGER DEFAULT 0,
    PRIMARY KEY(product_id, day),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_price_daily_product ON price_daily(product_id);
CREATE INDEX IF NOT EXISTS ix_price_daily_day ON price_daily(day);

-- Mapeamento para fontes externas (Zoom/Buscapé)
CREATE TABLE IF NOT EXISTS external_product_map (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id   INTEGER NOT NULL,
    source       TEXT NOT NULL,        -- zoom | buscape
    external_url TEXT NOT NULL,
    confidence   REAL NOT NULL,        -- 0..1
    last_ok_at   DATETIME,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ext_map_source_url
ON external_product_map(source, external_url);

CREATE INDEX IF NOT EXISTS ix_ext_map_product ON external_product_map(product_id);
CREATE INDEX IF NOT EXISTS ix_ext_map_source ON external_product_map(source);
CREATE INDEX IF NOT EXISTS ix_ext_map_confidence ON external_product_map(confidence);

-- Pontos de preço externos (bruto)
CREATE TABLE IF NOT EXISTS external_price_points (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id   INTEGER NOT NULL,
    source       TEXT NOT NULL,        -- zoom | buscape
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    price_cents  INTEGER NOT NULL,
    seller       TEXT,
    meta_json    TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_ext_points_prod_time
ON external_price_points(product_id, collected_at);

CREATE INDEX IF NOT EXISTS ix_ext_points_source ON external_price_points(source);
CREATE INDEX IF NOT EXISTS ix_ext_points_collected ON external_price_points(collected_at);

-- Agregado diário externo
CREATE TABLE IF NOT EXISTS external_price_daily (
    product_id   INTEGER NOT NULL,
    source       TEXT NOT NULL,
    day          DATE NOT NULL,
    min_cents    INTEGER NOT NULL,
    max_cents    INTEGER NOT NULL,
    avg_cents    INTEGER NOT NULL,
    count_points INTEGER DEFAULT 0,
    PRIMARY KEY(product_id, source, day),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_ext_daily_product ON external_price_daily(product_id);
CREATE INDEX IF NOT EXISTS ix_ext_daily_source ON external_price_daily(source);
CREATE INDEX IF NOT EXISTS ix_ext_daily_day ON external_price_daily(day);

-- Observabilidade e resultados
CREATE TABLE IF NOT EXISTS perf (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    component   TEXT NOT NULL,
    metric      TEXT NOT NULL,         -- latency_ms | success | error | items_found etc.
    value       REAL NOT NULL,
    occurred_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_perf_component ON perf(component);
CREATE INDEX IF NOT EXISTS ix_perf_time ON perf(occurred_at);
CREATE INDEX IF NOT EXISTS ix_perf_metric ON perf(metric);

-- Ofertas postadas
CREATE TABLE IF NOT EXISTS offers_posted (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    platform       TEXT NOT NULL,
    store          TEXT,
    title          TEXT NOT NULL,
    canonical_url  TEXT NOT NULL,
    affiliate_url  TEXT NOT NULL,
    price_cents    INTEGER,
    posted_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    message_id     TEXT,
    extra_json     TEXT
);

CREATE INDEX IF NOT EXISTS ix_offers_posted_time ON offers_posted(posted_at);
CREATE INDEX IF NOT EXISTS ix_offers_posted_platform ON offers_posted(platform);
CREATE INDEX IF NOT EXISTS ix_offers_posted_store ON offers_posted(store);

-- Receita
CREATE TABLE IF NOT EXISTS revenue (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    platform      TEXT NOT NULL,     -- awin | mercadolivre | magalu | amazon | shopee | aliexpress | rakuten
    merchant      TEXT,
    amount_cents  INTEGER NOT NULL,
    status        TEXT DEFAULT 'estimated',
    occurred_on   DATE NOT NULL,
    reference_id  TEXT,
    subid         TEXT
);

CREATE INDEX IF NOT EXISTS ix_revenue_date ON revenue(occurred_on);
CREATE INDEX IF NOT EXISTS ix_revenue_platform ON revenue(platform);
CREATE INDEX IF NOT EXISTS ix_revenue_merchant ON revenue(merchant);
CREATE INDEX IF NOT EXISTS ix_revenue_status ON revenue(status);

-- ============================================================================
-- VIEWS PARA MÉTRICAS DO DASHBOARD
-- ============================================================================

-- 1) Ofertas Amazon com/sem ASIN (últimos 7 dias)
CREATE VIEW IF NOT EXISTS vw_amz_asin_quality_7d AS
SELECT
  SUM(CASE WHEN COALESCE(json_extract(extra_json,'$.asin'), '') <> '' THEN 1 ELSE 0 END) AS with_asin,
  SUM(CASE WHEN COALESCE(json_extract(extra_json,'$.asin'), '') = '' THEN 1 ELSE 0 END) AS without_asin,
  COUNT(*) AS total
FROM offers_posted
WHERE platform='amazon'
  AND posted_at >= DATE('now','-7 day');

-- 2) Estratégia ASIN (a partir da perf) últimos 7 dias
CREATE VIEW IF NOT EXISTS vw_amz_asin_strategy_7d AS
SELECT
  CASE
    WHEN metric='amazon_asin.method' AND value=0 THEN 'url'
    WHEN metric='amazon_asin.method' AND value=1 THEN 'html'
    WHEN metric='amazon_asin.method' AND value=2 THEN 'playwright'
    ELSE 'unknown'
  END AS method,
  COUNT(*) AS cnt
FROM perf
WHERE component='amazon'
  AND metric='amazon_asin.method'
  AND occurred_at >= DATE('now','-7 day')
GROUP BY method;

-- 3) Posts bloqueados por motivo/plataforma (7d)
CREATE VIEW IF NOT EXISTS vw_posts_blocked_7d AS
SELECT component AS platform,
       metric    AS reason,
       COUNT(*)  AS blocked
FROM perf
WHERE metric IN ('affiliate_format_invalid','amazon_asin_missing')
  AND occurred_at >= DATE('now','-7 day')
GROUP BY platform, reason;

-- 4) Latência média por plataforma para deeplink (7d)
CREATE VIEW IF NOT EXISTS vw_deeplink_latency_7d AS
SELECT component AS platform,
       ROUND(AVG(value),0) AS avg_ms,
       COUNT(*) AS samples
FROM perf
WHERE metric='deeplink_latency_ms'
  AND occurred_at >= DATE('now','-7 day')
GROUP BY platform;

-- 5) Receita por plataforma e R$/post (7d)
CREATE VIEW IF NOT EXISTS vw_revenue_per_platform_7d AS
WITH r AS (
  SELECT platform, SUM(amount_cents)/100.0 AS revenue
  FROM revenue
  WHERE occurred_on >= DATE('now','-7 day')
  GROUP BY platform
),
p AS (
  SELECT platform, COUNT(*) AS posts
  FROM offers_posted
  WHERE posted_at >= DATE('now','-7 day')
  GROUP BY platform
)
SELECT p.platform,
       COALESCE(r.revenue,0) AS revenue,
       p.posts,
       CASE WHEN p.posts>0 THEN COALESCE(r.revenue,0)/p.posts ELSE 0 END AS revenue_per_post
FROM p
LEFT JOIN r ON r.platform=p.platform;

-- 6) Uso de badges (7d)
CREATE VIEW IF NOT EXISTS vw_badges_7d AS
SELECT metric AS badge, COUNT(*) AS used
FROM perf
WHERE metric IN ('badge_90d_internal','badge_90d_both','badge_30d_avg')
  AND occurred_at >= DATE('now','-7 day')
GROUP BY metric;

-- 7) Freshness de coleta interna/externa (por plataforma)
CREATE VIEW IF NOT EXISTS vw_price_freshness_7d AS
WITH last_internal AS (
  SELECT pr.platform,
         AVG(julianday('now') - julianday(pd.date)) AS avg_age_days
  FROM products pr
  JOIN price_daily pd ON pd.product_id = pr.id
  WHERE pd.date >= DATE('now','-7 day')
  GROUP BY pr.platform
),
last_external AS (
  SELECT pr.platform,
         AVG(julianday('now') - julianday(epd.date)) AS avg_age_days
  FROM products pr
  JOIN external_price_daily epd ON epd.internal_product_id = pr.id
  WHERE epd.date >= DATE('now','-7 day')
  GROUP BY pr.platform
)
SELECT li.platform,
       ROUND(li.avg_age_days,2) AS avg_age_internal_days,
       ROUND(COALESCE(le.avg_age_days,0),2) AS avg_age_external_days
FROM last_internal li
LEFT JOIN last_external le ON le.platform = li.platform;

-- 8) Fallback por fonte (se você grava 'source_type' na perf) (7d)
CREATE VIEW IF NOT EXISTS vw_source_fallback_7d AS
SELECT component AS platform,
       CASE value
         WHEN 0 THEN 'FEED'
         WHEN 1 THEN 'API_LIKE'
         WHEN 2 THEN 'SCRAPER'
         ELSE 'UNKNOWN'
       END AS source_type,
       COUNT(*) AS cnt
FROM perf
WHERE metric='source_type'
  AND occurred_at >= DATE('now','-7 day')
GROUP BY platform, source_type;

-- Views para 30 dias (versões estendidas)
CREATE VIEW IF NOT EXISTS vw_amz_asin_quality_30d AS
SELECT
  SUM(CASE WHEN COALESCE(json_extract(extra_json,'$.asin'), '') <> '' THEN 1 ELSE 0 END) AS with_asin,
  SUM(CASE WHEN COALESCE(json_extract(extra_json,'$.asin'), '') = '' THEN 1 ELSE 0 END) AS without_asin,
  COUNT(*) AS total
FROM offers_posted
WHERE platform='amazon'
  AND posted_at >= DATE('now','-30 day');

CREATE VIEW IF NOT EXISTS vw_posts_blocked_30d AS
SELECT component AS platform,
       metric    AS reason,
       COUNT(*)  AS blocked
FROM perf
WHERE metric IN ('affiliate_format_invalid','amazon_asin_missing')
  AND occurred_at >= DATE('now','-30 day')
GROUP BY platform, reason;

CREATE VIEW IF NOT EXISTS vw_revenue_per_platform_30d AS
WITH r AS (
  SELECT platform, SUM(amount_cents)/100.0 AS revenue
  FROM revenue
  WHERE occurred_on >= DATE('now','-30 day')
  GROUP BY platform
),
p AS (
  SELECT platform, COUNT(*) AS posts
  FROM offers_posted
  WHERE posted_at >= DATE('now','-30 day')
  GROUP BY platform
)
SELECT p.platform,
       COALESCE(r.revenue,0) AS revenue,
       p.posts,
       CASE WHEN p.posts>0 THEN COALESCE(r.revenue,0)/p.posts ELSE 0 END AS revenue_per_post
FROM p
LEFT JOIN r ON r.platform=p.platform;
"""


class DatabaseInitializer:
    """Inicializador dos bancos de dados"""

    def __init__(self):
        self.db_paths = {}
        self.schemas = {"aff_cache": AFF_CACHE_SCHEMA, "analytics": ANALYTICS_SCHEMA}

        # Configurar caminhos dos bancos
        for name, path in DB_CONFIG.items():
            self.db_paths[name] = Path(path)

    def ensure_db_directory(self, db_path: Path) -> None:
        """Garante que o diretório do banco existe"""
        db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Diretório do banco verificado: {db_path.parent}")

    def init_database(self, db_name: str) -> bool:
        """
        Inicializa um banco específico

        Args:
            db_name: Nome do banco (aff_cache ou analytics)

        Returns:
            True se inicializado com sucesso, False caso contrário
        """
        if db_name not in self.db_paths:
            logger.error(f"Banco desconhecido: {db_name}")
            return False

        db_path = self.db_paths[db_name]
        schema = self.schemas[db_name]

        try:
            # Garantir que o diretório existe
            self.ensure_db_directory(db_path)

            # Aplicar schema
            logger.info(f"Inicializando banco {db_name}: {db_path}")

            # Dividir schema em comandos individuais
            commands = [cmd.strip() for cmd in schema.split(";") if cmd.strip()]

            for command in commands:
                if command:
                    execute(db_path, command)
                    logger.debug(f"Comando executado: {command[:50]}...")

            logger.info(f"✅ Banco {db_name} inicializado com sucesso")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao inicializar banco {db_name}: {e}")
            return False

    def init_all_databases(self) -> Dict[str, bool]:
        """
        Inicializa todos os bancos

        Returns:
            Dicionário com status de cada banco
        """
        results = {}

        logger.info("🚀 Iniciando inicialização de todos os bancos...")

        for db_name in self.db_paths.keys():
            results[db_name] = self.init_database(db_name)

        return results

    def validate_schemas(self) -> Dict[str, Dict]:
        """
        Valida se todos os schemas estão corretos

        Returns:
            Dicionário com informações de validação
        """
        validation_results = {}

        for db_name, db_path in self.db_paths.items():
            logger.info(f"🔍 Validando schema do banco {db_name}...")

            validation = {"exists": db_path.exists(), "tables": {}, "errors": []}

            if validation["exists"]:
                try:
                    # Verificar tabelas principais
                    expected_tables = self._get_expected_tables(db_name)

                    for table in expected_tables:
                        exists = table_exists(db_path, table)
                        validation["tables"][table] = exists

                        if not exists:
                            validation["errors"].append(
                                f"Tabela {table} não encontrada"
                            )

                except Exception as e:
                    validation["errors"].append(f"Erro na validação: {e}")
            else:
                validation["errors"].append("Banco não existe")

            validation_results[db_name] = validation

            if validation["errors"]:
                logger.warning(f"⚠️ Validação do banco {db_name} encontrou problemas")
            else:
                logger.info(f"✅ Validação do banco {db_name} OK")

        return validation_results

    def _get_expected_tables(self, db_name: str) -> List[str]:
        """Retorna lista de tabelas esperadas para cada banco"""
        if db_name == "aff_cache":
            return ["shortlinks"]
        elif db_name == "analytics":
            return [
                "products",
                "price_history",
                "price_daily",
                "external_product_map",
                "external_price_points",
                "external_price_daily",
                "perf",
                "offers_posted",
                "revenue",
            ]
        else:
            return []

    def get_schema_version(self) -> str:
        """Retorna versão atual do schema"""
        return "1.0.0"

    def print_status(self) -> None:
        """Imprime status dos bancos"""
        print("\n" + "=" * 60)
        print("📊 STATUS DOS BANCOS DE DADOS")
        print("=" * 60)

        for db_name, db_path in self.db_paths.items():
            exists = db_path.exists()
            size = db_path.stat().st_size if exists else 0

            print(f"\n🏦 {db_name.upper()}:")
            print(f"   📁 Caminho: {db_path}")
            print(f"   📊 Status: {'✅ Existe' if exists else '❌ Não existe'}")
            print(f"   📏 Tamanho: {size:,} bytes" if exists else "   📏 Tamanho: N/A")

        print(f"\n🔧 Versão do Schema: {self.get_schema_version()}")
        print("=" * 60)


def main():
    """Função principal para inicialização via linha de comando"""
    import sys

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    initializer = DatabaseInitializer()

    if len(sys.argv) > 1 and sys.argv[1] == "--validate":
        # Modo validação
        print("🔍 Validando schemas existentes...")
        validation = initializer.validate_schemas()

        for db_name, result in validation.items():
            print(f"\n📋 {db_name}:")
            if result["errors"]:
                for error in result["errors"]:
                    print(f"   ❌ {error}")
            else:
                print("   ✅ Schema válido")

    else:
        # Modo inicialização
        print("🚀 Inicializando bancos de dados...")
        results = initializer.init_all_databases()

        # Mostrar resultados
        print("\n📊 Resultados da inicialização:")
        for db_name, success in results.items():
            status = "✅ OK" if success else "❌ FALHOU"
            print(f"   {db_name}: {status}")

        # Validar schemas
        print("\n🔍 Validando schemas...")
        validation = initializer.validate_schemas()

        # Mostrar status final
        initializer.print_status()

        # Verificar se tudo está OK
        all_ok = all(results.values())
        if all_ok:
            print("\n🎉 Todos os bancos foram inicializados com sucesso!")
            return 0
        else:
            print("\n⚠️ Alguns bancos falharam na inicialização")
            return 1


if __name__ == "__main__":
    exit(main())
