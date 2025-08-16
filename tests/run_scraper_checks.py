# tests/run_scraper_checks.py
from __future__ import annotations
import asyncio
import sys
import os
from typing import List, Dict, Any, Set

# Adiciona o diretório raiz ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports relativos para funcionar quando executado diretamente
from scraper_contract import (
    Offer, validate_offer_structure, ensure_offer_hash, write_report
)
from adapters_scrapers import SCRAPER_ADAPTERS
from affiliate import AffiliateLinkConverter

def _guess_store_kind(loja: str) -> str:
    """Identifica o tipo de loja para geração de links de afiliado"""
    l = (loja or "").lower()
    if any(x in l for x in ["comfy", "trocafy", "lg", "kabum", "samsung"]):
        return "awin"
    if "amazon" in l:
        return "amazon"
    if "shopee" in l:
        return "shopee"
    if "aliexpress" in l or "ali express" in l:
        return "aliexpress"
    if "magalu" in l or "magazine" in l:
        return "magalu"
    if "mercado livre" in l or "mercadolivre" in l:
        return "mercadolivre"
    return "desconhecido"

async def _generate_affiliate(o: Offer) -> Offer:
    """Gera link de afiliado se não existir"""
    if not o.url_afiliado and o.url_produto:
        try:
            converter = AffiliateLinkConverter()
            o.url_afiliado = converter.gerar_link_afiliado(o.url_produto, o.loja)
            print(f"🔗 Link de afiliado gerado para {o.loja}: {o.url_afiliado[:50]}...")
        except Exception as e:
            print(f"⚠️ Erro ao gerar link de afiliado para {o.loja}: {e}")
    return o

async def _run_one(adapter_name: str) -> List[Offer]:
    """Executa um scraper específico e retorna ofertas validadas"""
    print(f"🔄 Executando scraper: {adapter_name}")
    
    fn = SCRAPER_ADAPTERS[adapter_name]
    raw_list: List[Dict[str, Any]] = await fn()
    
    print(f"📊 {adapter_name}: {len(raw_list)} ofertas brutas coletadas")
    
    offers: List[Offer] = []
    seen_hashes: Set[str] = set()

    for i, d in enumerate(raw_list):
        try:
            o = Offer.from_dict(d)
            ok, msg = validate_offer_structure(o)
            if not ok:
                print(f"❌ [{adapter_name}] Oferta {i+1} reprovada (estrutura): {msg}")
                continue

            o = ensure_offer_hash(o)
            if o.offer_hash in seen_hashes:
                print(f"🔄 [{adapter_name}] DEDUPE: oferta {i+1} ignorada (hash repetido) -> {o.titulo[:50]}...")
                continue
            seen_hashes.add(o.offer_hash)

            # Gera link de afiliado se faltando
            o = await _generate_affiliate(o)

            offers.append(o)
            print(f"✅ [{adapter_name}] Oferta {i+1} validada: {o.titulo[:50]}...")

        except Exception as e:
            print(f"❌ [{adapter_name}] Erro ao processar oferta {i+1}: {e}")
    
    print(f"✅ [{adapter_name}] {len(offers)} ofertas válidas após validação")
    return offers

async def main():
    """Função principal que executa todos os scrapers e gera relatório"""
    print("🚀 EXECUTOR DE TESTES DE SCRAPERS - GARIMPEIRO GEEK")
    print("=" * 70)
    print("🎯 Objetivo: Validar scrapers, estrutura de dados e geração de afiliados")
    print("📊 Saída: Relatórios CSV/JSON na pasta reports/")
    print("=" * 70)
    
    all_offers: List[Offer] = []
    total_raw = 0
    total_valid = 0
    
    # Executa cada scraper
    for name in SCRAPER_ADAPTERS.keys():
        print(f"\n{'='*20} SCRAPER: {name.upper()} {'='*20}")
        
        try:
            res = await _run_one(name)
            all_offers.extend(res)
            total_valid += len(res)
            
        except Exception as e:
            print(f"❌ Erro crítico no scraper {name}: {e}")
            continue
    
    # Resumo final
    print(f"\n{'='*70}")
    print("📊 RESUMO FINAL")
    print("=" * 70)
    print(f"🎯 Total de ofertas válidas: {total_valid}")
    print(f"🏪 Scrapers executados: {len(SCRAPER_ADAPTERS)}")
    
    # Gera relatório
    if all_offers:
        report_path = write_report(all_offers, total_valid, 0)
        print(f"📄 Relatório gerado: {report_path}")
        
        # Mostra algumas estatísticas
        lojas = set(o.loja for o in all_offers)
        fontes = set(o.fonte for o in all_offers)
        com_imagem = sum(1 for o in all_offers if o.imagem_url)
        com_afiliado = sum(1 for o in all_offers if o.url_afiliado)
        
        print(f"\n📈 ESTATÍSTICAS:")
        print(f"  🏪 Lojas encontradas: {', '.join(lojas)}")
        print(f"  📊 Fontes de dados: {', '.join(fontes)}")
        print(f"  🖼️ Ofertas com imagem: {com_imagem}/{total_valid} ({com_imagem/total_valid*100:.1f}%)")
        print(f"  🔗 Ofertas com afiliado: {com_afiliado}/{total_valid} ({com_afiliado/total_valid*100:.1f}%)")
        
    else:
        print("❌ Nenhuma oferta válida foi coletada!")
    
    print(f"\n🎯 Execução concluída! Verifique os relatórios na pasta reports/")

if __name__ == "__main__":
    asyncio.run(main())
