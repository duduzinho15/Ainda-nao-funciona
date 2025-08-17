# orchestrator.py
from __future__ import annotations
import asyncio, logging, random, re, os, shutil
from datetime import datetime
from typing import Dict, Any, List, Tuple, Set, Callable, Awaitable
from utils.offer_hash import offer_hash
from affiliate import AffiliateLinkConverter
from database import adicionar_oferta, oferta_ja_existe_por_hash
from telegram_poster import publicar_oferta_automatica
from metrics import (
    POSTS_OK, POSTS_FAIL, OFFERS_COLLECTED, OFFERS_APPROVED, 
    OFFERS_DUPLICATED, SCRAPER_ERRORS, SCRAPER_SUCCESS, maybe_start_server
)
import config

logger = logging.getLogger("orchestrator")

# ===== Config rápida por env (opcional) =====
POST_RATE_DELAY_MS = int(os.getenv("POST_RATE_DELAY_MS", "250"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

# ===== Adapters mínimos (chamam seus scrapers reais) =====
async def scrape_promobit(limit: int = 20) -> List[Dict[str, Any]]:
    """Executa scraper do Promobit"""
    if not config.ENABLE_PROMOBIT:
        logger.info("Promobit desabilitado por configuração")
        return []
    
    try:
        from promobit_scraper import buscar_ofertas_promobit
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            ofertas = await buscar_ofertas_promobit(
                session=session,
                max_paginas=1,
                max_requests=3
            )
        SCRAPER_SUCCESS.labels(scraper_name="promobit").inc()
        return ofertas[:limit]
    except Exception as e:
        logger.error(f"Erro no scraper Promobit: {e}")
        SCRAPER_ERRORS.labels(scraper_name="promobit").inc()
        return []

async def scrape_pelando(limit: int = 20) -> List[Dict[str, Any]]:
    """Executa scraper do Pelando"""
    if not config.ENABLE_PELANDO:
        logger.info("Pelando desabilitado por configuração")
        return []
    
    try:
        from pelando_scraper import buscar_ofertas_pelando
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            ofertas = await buscar_ofertas_pelando(
                session=session,
                max_paginas=1
            )
        SCRAPER_SUCCESS.labels(scraper_name="pelando").inc()
        return ofertas[:limit]
    except Exception as e:
        logger.error(f"Erro no scraper Pelando: {e}")
        SCRAPER_ERRORS.labels(scraper_name="pelando").inc()
        return []

async def scrape_shopee(limit: int = 10) -> List[Dict[str, Any]]:
    """Executa scraper da Shopee"""
    if not config.ENABLE_SHOPEE:
        logger.info("Shopee desabilitado por configuração")
        return []
    
    try:
        from product_scraper_ultimate import UltimateProductScraper
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            scraper = UltimateProductScraper()
            # Simula busca por produtos populares
            ofertas = [{
                "titulo": "📱 Smartphone Teste Shopee",
                "preco": "R$ 599,99",
                "url_produto": "https://shopee.com.br/teste",
                "loja": "Shopee",
                "fonte": "product_scraper_ultimate",
                "imagem_url": "https://picsum.photos/400/300?random=shopee"
            }]
        SCRAPER_SUCCESS.labels(scraper_name="shopee").inc()
        return ofertas[:limit]
    except Exception as e:
        logger.error(f"Erro no scraper Shopee: {e}")
        SCRAPER_ERRORS.labels(scraper_name="shopee").inc()
        return []

async def scrape_amazon(limit: int = 10) -> List[Dict[str, Any]]:
    """Executa scraper da Amazon usando método de scraping"""
    if not config.ENABLE_AMAZON:
        logger.info("Amazon desabilitado por configuração")
        return []
    
    try:
        from amazon_scraper import buscar_ofertas_amazon
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            ofertas = await buscar_ofertas_amazon(
                session=session,
                max_paginas=1,
                max_requests=2
            )
        SCRAPER_SUCCESS.labels(scraper_name="amazon").inc()
        return ofertas[:limit]
    except Exception as e:
        logger.error(f"Erro no scraper Amazon: {e}")
        SCRAPER_ERRORS.labels(scraper_name="amazon").inc()
        return []
    


async def scrape_mepuc(limit: int = 15) -> List[Dict[str, Any]]:
    """Executa scraper do MeuPC.net"""
    if not config.ENABLE_MEPUC:
        logger.info("MeuPC.net desabilitado por configuração")
        return []
    
    try:
        from mepuc_scraper import buscar_ofertas_mepuc
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            ofertas = await buscar_ofertas_mepuc(
                session=session,
                max_paginas=2,
                max_requests=5
            )
        SCRAPER_SUCCESS.labels(scraper_name="mepuc").inc()
        return ofertas[:limit]
    except Exception as e:
        logger.error(f"Erro no scraper MeuPC.net: {e}")
        SCRAPER_ERRORS.labels(scraper_name="mepuc").inc()
        return []

# Lista dinâmica de scrapers baseada na configuração
def get_active_scrapers():
    """Retorna lista de scrapers ativos baseada na configuração"""
    scrapers = []
    
    if config.ENABLE_PROMOBIT:
        scrapers.append(("promobit", scrape_promobit))
    if config.ENABLE_PELANDO:
        scrapers.append(("pelando", scrape_pelando))
    if config.ENABLE_SHOPEE:
        scrapers.append(("shopee", scrape_shopee))
    if config.ENABLE_AMAZON:
        scrapers.append(("amazon", scrape_amazon))
    if config.ENABLE_MEPUC:
        scrapers.append(("mepuc", scrape_mepuc))
    
    return scrapers

# ===== Sistema de Backup Automático =====
def create_backup():
    """Cria backup automático do banco de dados"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = "backups"
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        backup_file = f"{backup_dir}/ofertas_backup_{timestamp}.db"
        shutil.copy2(config.DB_NAME, backup_file)
        
        # Remove backups antigos (mantém apenas os últimos 5)
        backup_files = sorted([f for f in os.listdir(backup_dir) if f.endswith('.db')])
        if len(backup_files) > 5:
            for old_file in backup_files[:-5]:
                os.remove(os.path.join(backup_dir, old_file))
        
        logger.info(f"✅ Backup criado: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"❌ Erro ao criar backup: {e}")
        return None

# ===== Helpers de validação compatíveis com seus testes =====
_PRIC_RE = re.compile(r"^(R\$)?\s?\d{1,3}(?:\.\d{3})*,\d{2}$")

def _normalize_offer(d: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza campos da oferta para formato padrão"""
    o = dict(d)
    
    # padroniza campos esperados pelo sistema
    if "preco" not in o and "preco_atual" in o:
        o["preco"] = o.pop("preco_atual")
    
    o["fonte"] = o.get("fonte") or "Desconhecida"
    
    # loja canônica (domínio/nome → Amazon, KaBuM, Samsung, etc.)
    if "loja" not in o or not o["loja"]:
        o["loja"] = "Desconhecida"
    
    return o

def _is_valid(o: Dict[str, Any]) -> Tuple[bool, str]:
    """Valida se a oferta tem todos os campos obrigatórios"""
    for k in ("titulo", "preco", "url_produto", "loja", "fonte"):
        if not o.get(k):
            return False, f"falta campo obrigatório: {k}"
    
    if not _PRIC_RE.match(o["preco"].strip()):
        return False, f"preço inválido: {o['preco']!r}"
    
    if not str(o["url_produto"]).startswith(("http://", "https://")):
        return False, f"url_produto inválida: {o['url_produto']!r}"
    
    img = o.get("imagem_url")
    if img and not str(img).startswith(("http://", "https://")):
        return False, f"imagem_url inválida: {img!r}"
    
    return True, "OK"

async def _gen_affiliate(o: Dict[str, Any]) -> Dict[str, Any]:
    """Gera link de afiliado para a oferta"""
    try:
        converter = AffiliateLinkConverter()
        
        # Para Amazon, usa sistema de ASIN
        if o.get("loja", "").lower() in ["amazon", "amazon.com.br"]:
            try:
                from utils.amazon_link import canonicalize_amazon
                amazon_tag = os.getenv("AMAZON_ASSOCIATE_TAG", "garimpeirogee-20")
                o["url_afiliado"] = await canonicalize_amazon(o.get("url_produto"), amazon_tag)
                
                if not o["url_afiliado"]:
                    # Fallback para método antigo
                    o["url_afiliado"] = converter._gerar_link_amazon_antigo(o.get("url_produto"))
                    
            except ImportError:
                logger.warning("Módulo amazon_link não encontrado, usando método antigo")
                o["url_afiliado"] = converter._gerar_link_amazon_antigo(o.get("url_produto"))
        else:
            # Para outras lojas, usa método síncrono
            o["url_afiliado"] = converter._gerar_link_afiliado_sync(o.get("url_produto"), o.get("loja"))
        
        logger.debug(f"Link de afiliado gerado para {o.get('loja')}: {o['url_afiliado'][:50]}...")
        
    except Exception as e:
        logger.warning(f"Erro ao gerar link de afiliado para {o.get('loja')}: {e}")
        o["url_afiliado"] = o.get("url_produto")  # Fallback para URL original
    
    return o

async def _post_one(o: Dict[str, Any], dry_run: bool) -> bool:
    """Publica uma oferta (ou simula se dry_run=True)"""
    if dry_run:
        logger.info(f"[DRY_RUN] {o['titulo']} | {o.get('loja')} | {o.get('preco')} -> NÃO será postado.")
        return True
    
    # respeita rate limit suave
    await asyncio.sleep(POST_RATE_DELAY_MS / 1000 + random.uniform(0, 0.5))
    
    try:
        # Simula contexto para publicação
        class ContextoSimulado:
            def __init__(self):
                from telegram import Bot
                token = os.getenv("TELEGRAM_BOT_TOKEN")
                self.bot = Bot(token=token) if token else None
                self.job = None
        
        context = ContextoSimulado()
        return await publicar_oferta_automatica(o, context)
    except Exception as e:
        logger.error(f"Erro ao publicar oferta: {e}")
        return False

async def coletar_e_publicar(dry_run: bool | None = None, limit_por_scraper: int = 20) -> Dict[str, Any]:
    """Função principal: coleta, normaliza, valida, deduplica e publica"""
    maybe_start_server()  # Inicia servidor de métricas se METRICS=1
    
    if dry_run is None:
        dry_run = DRY_RUN
    
    logger.info(f"🚀 Iniciando coleta e publicação (DRY_RUN={dry_run})")
    
    # Cria backup antes de começar
    backup_file = create_backup()
    if backup_file:
        logger.info(f"💾 Backup criado: {backup_file}")
    
    all_raw: List[Dict[str, Any]] = []
    
    # Obtém lista de scrapers ativos
    active_scrapers = get_active_scrapers()
    logger.info(f"📊 Scrapers ativos: {[name for name, _ in active_scrapers]}")

    # 1) Coleta concorrente
    async def run_one(name: str, fn):
        try:
            res = await fn(limit=limit_por_scraper)
            logger.info(f"✅ {name}: {len(res)} ofertas brutas coletadas")
            all_raw.extend((dict(r) | {"fonte": name}) for r in res)
        except Exception as e:
            logger.exception(f"❌ Erro no scraper {name}: {e}")

    # Executa todos os scrapers em paralelo
    if active_scrapers:
        await asyncio.gather(*(run_one(n, f) for n, f in active_scrapers))
    else:
        logger.warning("⚠️ Nenhum scraper ativo configurado!")

    logger.info(f"📊 Total de ofertas brutas coletadas: {len(all_raw)}")
    
    # Atualiza métricas
    OFFERS_COLLECTED.set(len(all_raw))

    # 2) Normaliza, valida, afilia, dedup (memória + DB)
    vistos: Set[str] = set()
    aprovadas: List[Dict[str, Any]] = []
    
    for i, d in enumerate(all_raw):
        try:
            o = _normalize_offer(d)
            ok, msg = _is_valid(o)
            
            if not ok:
                logger.debug(f"❌ Oferta {i+1} reprovada (estrutura): {msg}")
                continue
            
            # Gera hash para deduplicação
            h = offer_hash(o)
            o["offer_hash"] = h

            # dedupe memória
            if h in vistos:
                logger.debug(f"🔄 Dedupe (memória): {o.get('titulo')[:50]}...")
                OFFERS_DUPLICATED.inc()
                continue
            vistos.add(h)

            # dedupe DB
            try:
                if oferta_ja_existe_por_hash(h):
                    logger.info(f"🔄 Dedupe (DB): {o.get('titulo')[:50]}...")
                    OFFERS_DUPLICATED.inc()
                    continue
            except Exception as e:
                logger.warning(f"Erro ao verificar duplicata no DB: {e}")

            # Gera link de afiliado
            o = await _gen_affiliate(o)
            aprovadas.append(o)
            
            logger.debug(f"✅ Oferta {i+1} aprovada: {o.get('titulo')[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar oferta {i+1}: {e}")

    logger.info(f"📋 Ofertas aprovadas após validação: {len(aprovadas)}")
    
    # Atualiza métricas
    OFFERS_APPROVED.set(len(aprovadas))

    # 3) Persistência + Postagem
    publicados = 0
    for i, o in enumerate(aprovadas):
        try:
            # salvar antes de postar (evita race em múltiplas instâncias)
            if not oferta_ja_existe_por_hash(o["offer_hash"]):
                adicionar_oferta(o)
                logger.debug(f"💾 Oferta {i+1} salva no banco")
            
            # Publica (ou simula se dry_run)
            ok = await _post_one(o, dry_run=dry_run)
            publicados += int(bool(ok))
            
            # Atualiza métricas
            if ok:
                POSTS_OK.inc()
                logger.info(f"📤 Oferta {i+1} publicada com sucesso: {o.get('titulo')[:50]}...")
            else:
                POSTS_FAIL.inc()
                logger.warning(f"⚠️ Falha ao publicar oferta {i+1}: {o.get('titulo')[:50]}...")
                
        except Exception as e:
            logger.exception(f"❌ Falha publicando oferta {i+1}: {e}")

    resultado = {
        "coletadas": len(all_raw),
        "aprovadas": len(aprovadas),
        "publicadas": publicados,
        "dry_run": dry_run,
        "scrapers_executados": len(active_scrapers),
        "backup_file": backup_file
    }
    
    logger.info(f"🎯 Execução concluída: {resultado}")
    return resultado

# Função para execução manual
async def main():
    """Execução manual do orquestrador para testes"""
    import sys
    
    dry_run = "--dry-run" in sys.argv
    limit = 20
    
    if "--limit" in sys.argv:
        try:
            idx = sys.argv.index("--limit")
            limit = int(sys.argv[idx + 1])
        except (ValueError, IndexError):
            pass
    
    logger.info(f"Executando orquestrador manualmente (DRY_RUN={dry_run}, LIMIT={limit})")
    
    resultado = await coletar_e_publicar(dry_run=dry_run, limit_por_scraper=limit)
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"  📥 Ofertas coletadas: {resultado['coletadas']}")
    print(f"  ✅ Ofertas aprovadas: {resultado['aprovadas']}")
    print(f"  📤 Ofertas publicadas: {resultado['publicadas']}")
    print(f"  🔄 DRY_RUN: {resultado['dry_run']}")
    print(f"  🏪 Scrapers executados: {resultado['scrapers_executados']}")
    if resultado.get('backup_file'):
        print(f"  💾 Backup criado: {resultado['backup_file']}")

if __name__ == "__main__":
    # Configuração básica de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
