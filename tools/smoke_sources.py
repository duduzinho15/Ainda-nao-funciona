#!/usr/bin/env python3
"""
CLI de smoke test para fontes de dados.
Testa cada scraper/API individualmente sem salvar dados.

Uso:
    python tools/smoke_sources.py --periodo 7d --max 50
    python tools/smoke_sources.py --periodo 24h --max 20 --verbose
    python tools/smoke_sources.py --list-sources
"""

import os
import sys
import asyncio
import argparse
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Adicionar o diretório raiz ao path para importar módulos core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scraper_registry import scraper_registry


def setup_logging(verbose: bool = False) -> None:
    """Configura logging para o smoke test."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def check_ci_mode() -> bool:
    """Verifica se estamos em modo CI."""
    return bool(os.getenv("GG_SEED") and os.getenv("GG_FREEZE_TIME"))


async def test_single_source(source_name: str, periodo: str, max_items: int) -> Dict[str, Any]:
    """
    Testa uma fonte individual.
    
    Args:
        source_name: Nome da fonte
        periodo: Período para teste
        max_items: Máximo de itens para mostrar
        
    Returns:
        Dicionário com resultados do teste
    """
    logger = logging.getLogger(f"smoke.{source_name}")
    
    try:
        # Obter informações da fonte
        source_info = scraper_registry.get_scraper(source_name)
        
        if not source_info:
            return {
                "name": source_name,
                "status": "error",
                "error": "Fonte não encontrada no registry",
                "ofertas": [],
                "count": 0
            }
        
        if not source_info.enabled:
            return {
                "name": source_name,
                "status": "disabled",
                "error": source_info.error_message or "Fonte desabilitada",
                "ofertas": [],
                "count": 0
            }
        
        logger.info(f"🧪 Testando fonte: {source_name}")
        logger.info(f"  - Descrição: {source_info.description}")
        logger.info(f"  - Prioridade: {source_info.priority}")
        logger.info(f"  - Rate Limit: {source_info.rate_limit}")
        
        # Testar coleta
        start_time = asyncio.get_event_loop().time()
        ofertas = await source_info.get_ofertas_func(periodo)
        end_time = asyncio.get_event_loop().time()
        
        duration = end_time - start_time
        
        # Limitar número de ofertas para exibição
        display_ofertas = ofertas[:max_items] if ofertas else []
        
        # Preparar amostras para exibição
        samples = []
        for i, oferta in enumerate(display_ofertas):
            sample = {
                "indice": i + 1,
                "titulo": oferta.get("titulo", "")[:60] + "..." if len(oferta.get("titulo", "")) > 60 else oferta.get("titulo", ""),
                "preco": f"R$ {oferta.get('preco', 0):.2f}",
                "loja": oferta.get("loja", ""),
                "fonte": oferta.get("fonte", "")
            }
            samples.append(sample)
        
        return {
            "name": source_name,
            "status": "success",
            "duration": duration,
            "ofertas": samples,
            "count": len(ofertas),
            "total_count": len(ofertas)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar {source_name}: {e}")
        return {
            "name": source_name,
            "status": "error",
            "error": str(e),
            "ofertas": [],
            "count": 0
        }


async def run_smoke_test(periodo: str, max_items: int, sources: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Executa o smoke test completo.
    
    Args:
        periodo: Período para teste
        max_items: Máximo de itens para mostrar por fonte
        sources: Lista específica de fontes para testar (None = todas)
        
    Returns:
        Lista com resultados de todos os testes
    """
    logger = logging.getLogger("smoke_test")
    
    # Verificar modo CI
    if check_ci_mode():
        logger.error("🔒 Modo CI detectado - abortando smoke test")
        logger.error("   Use GG_SEED e GG_FREEZE_TIME apenas para testes determinísticos")
        return []
    
    # Obter fontes para testar
    if sources:
        sources_to_test = sources
    else:
        enabled_sources = scraper_registry.get_enabled_scrapers()
        sources_to_test = [s.name for s in enabled_sources]
    
    if not sources_to_test:
        logger.warning("⚠️ Nenhuma fonte habilitada para teste")
        return []
    
    logger.info(f"🚀 Iniciando smoke test para {len(sources_to_test)} fontes")
    logger.info(f"  - Período: {periodo}")
    logger.info(f"  - Máximo de itens por fonte: {max_items}")
    logger.info(f"  - Fontes: {', '.join(sources_to_test)}")
    
    # Executar testes em paralelo
    tasks = [
        test_single_source(source_name, periodo, max_items)
        for source_name in sources_to_test
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Processar resultados
    processed_results = []
    for result in results:
        if isinstance(result, Exception):
            processed_results.append({
                "name": "unknown",
                "status": "error",
                "error": str(result),
                "ofertas": [],
                "count": 0
            })
        else:
            processed_results.append(result)
    
    return processed_results


def print_results(results: List[Dict[str, Any]], verbose: bool = False) -> None:
    """
    Exibe os resultados do smoke test.
    
    Args:
        results: Lista de resultados
        verbose: Se deve mostrar detalhes completos
    """
    print("\n" + "="*80)
    print("📊 RESULTADOS DO SMOKE TEST")
    print("="*80)
    
    # Estatísticas gerais
    total_sources = len(results)
    successful_sources = len([r for r in results if r["status"] == "success"])
    disabled_sources = len([r for r in results if r["status"] == "disabled"])
    error_sources = len([r for r in results if r["status"] == "error"])
    total_ofertas = sum(r.get("count", 0) for r in results)
    
    print(f"\n📈 ESTATÍSTICAS:")
    print(f"  - Total de fontes: {total_sources}")
    print(f"  - Fontes com sucesso: {successful_sources}")
    print(f"  - Fontes desabilitadas: {disabled_sources}")
    print(f"  - Fontes com erro: {error_sources}")
    print(f"  - Total de ofertas coletadas: {total_ofertas}")
    
    # Resultados por fonte
    print(f"\n🔍 RESULTADOS POR FONTE:")
    print("-" * 80)
    
    for result in results:
        name = result["name"]
        status = result["status"]
        count = result.get("count", 0)
        duration = result.get("duration", 0)
        
        # Status com emoji
        status_emoji = {
            "success": "✅",
            "disabled": "⚠️",
            "error": "❌"
        }.get(status, "❓")
        
        print(f"\n{status_emoji} {name}")
        print(f"  Status: {status}")
        print(f"  Ofertas: {count}")
        
        if duration > 0:
            print(f"  Duração: {duration:.2f}s")
        
        if status == "error":
            print(f"  Erro: {result.get('error', 'Erro desconhecido')}")
        elif status == "success" and count > 0:
            print(f"  Amostras:")
            for oferta in result.get("ofertas", [])[:3]:  # Mostrar apenas 3 amostras
                print(f"    {oferta['indice']}. {oferta['titulo']}")
                print(f"       Preço: {oferta['preco']} | Loja: {oferta['loja']}")
        
        if verbose and status == "success" and count > 0:
            print(f"  Todas as ofertas ({count}):")
            for oferta in result.get("ofertas", []):
                print(f"    {oferta['indice']}. {oferta['titulo']}")
                print(f"       Preço: {oferta['preco']} | Loja: {oferta['loja']} | Fonte: {oferta['fonte']}")


def list_sources() -> None:
    """Lista todas as fontes disponíveis no registry."""
    print("\n📋 FONTES DISPONÍVEIS NO REGISTRY")
    print("="*80)
    
    all_sources = scraper_registry.scrapers.values()
    enabled_sources = scraper_registry.get_enabled_scrapers()
    
    print(f"\n🔧 Total de fontes: {len(all_sources)}")
    print(f"✅ Fontes habilitadas: {len(enabled_sources)}")
    print(f"⚠️ Fontes desabilitadas: {len(all_sources) - len(enabled_sources)}")
    
    print(f"\n📝 DETALHES DAS FONTES:")
    print("-" * 80)
    
    for source in sorted(all_sources, key=lambda x: (x.priority, x.name)):
        status_emoji = "✅" if source.enabled else "⚠️"
        print(f"\n{status_emoji} {source.name}")
        print(f"  Prioridade: {source.priority}")
        print(f"  Status: {'Habilitada' if source.enabled else 'Desabilitada'}")
        print(f"  Descrição: {source.description}")
        
        if source.rate_limit:
            print(f"  Rate Limit: {source.rate_limit} req/seg")
        
        if source.env_vars:
            print(f"  Variáveis de ambiente: {', '.join(source.env_vars)}")
        
        if source.error_message:
            print(f"  Erro: {source.error_message}")
        
        if source.enabled and source.get_ofertas_func:
            print(f"  Função: get_ofertas() disponível")
        else:
            print(f"  Função: get_ofertas() não disponível")


def main():
    """Função principal do CLI."""
    parser = argparse.ArgumentParser(
        description="CLI de smoke test para fontes de dados",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python tools/smoke_sources.py --periodo 7d --max 50
  python tools/smoke_sources.py --periodo 24h --max 20 --verbose
  python tools/smoke_sources.py --list-sources
  python tools/smoke_sources.py --sources mercadolivre_api,kabum_scraper
        """
    )
    
    parser.add_argument(
        "--periodo",
        choices=["24h", "7d", "30d", "all"],
        default="7d",
        help="Período para teste (padrão: 7d)"
    )
    
    parser.add_argument(
        "--max",
        type=int,
        default=10,
        help="Máximo de itens para mostrar por fonte (padrão: 10)"
    )
    
    parser.add_argument(
        "--sources",
        help="Lista de fontes específicas para testar (separadas por vírgula)"
    )
    
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="Listar todas as fontes disponíveis no registry"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostrar detalhes completos"
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(args.verbose)
    
    # Verificar se deve apenas listar fontes
    if args.list_sources:
        list_sources()
        return
    
    # Verificar modo CI
    if check_ci_mode():
        print("🔒 Modo CI detectado - use --list-sources para ver fontes disponíveis")
        return
    
    # Preparar lista de fontes
    sources = None
    if args.sources:
        sources = [s.strip() for s in args.sources.split(",")]
    
    # Executar smoke test
    try:
        results = asyncio.run(run_smoke_test(args.periodo, args.max, sources))
        print_results(results, args.verbose)
        
        # Código de saída baseado nos resultados
        if any(r["status"] == "error" for r in results):
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Smoke test interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erro fatal no smoke test: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
