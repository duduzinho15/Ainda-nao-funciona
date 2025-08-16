# tests/run_scraper_checks.py
from __future__ import annotations
import asyncio
import sys
import os
from typing import List, Dict, Any, Set

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper_contract import (
    Offer, validate_offer_structure, ensure_offer_hash, write_report
)
from adapters_scrapers import SCRAPER_ADAPTERS

def _guess_store_kind(loja: str) -> str:
    """Identifica o tipo de loja para validação de afiliados"""
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
    # Só gera se não existir
    if not o.url_afiliado and o.url_produto:
        try:
            from affiliate import gerar_link_afiliado
            o.url_afiliado = gerar_link_afiliado(o.url_produto, o.loja)
        except Exception as e:
            print(f"⚠️ Erro ao gerar link de afiliado para {o.loja}: {e}")
            o.url_afiliado = o.url_produto  # Fallback para URL original
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
            continue
    
    print(f"✅ [{adapter_name}] {len(offers)} ofertas válidas processadas")
    return offers

async def main():
    """Função principal que executa todos os scrapers e gera relatório"""
    print("🚀 EXECUÇÃO COMPLETA DOS SCRAPERS - GARIMPEIRO GEEK")
    print("=" * 70)
    print("🎯 Objetivo: Validar estrutura, deduplicar e gerar relatórios")
    print("📝 Nenhuma oferta será postada no Telegram (modo teste)")
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
            
            # Estatísticas por scraper
            print(f"📊 {name}: {len(res)} ofertas válidas")
            
        except Exception as e:
            print(f"❌ Erro fatal no scraper {name}: {e}")
            continue
    
    # Resumo final
    print(f"\n{'='*70}")
    print("📊 RESUMO FINAL")
    print(f"{'='*70}")
    print(f"🔍 Scrapers executados: {len(SCRAPER_ADAPTERS)}")
    print(f"✅ Ofertas válidas: {total_valid}")
    print(f"🔄 Total de ofertas processadas: {len(all_offers)}")
    
    # Estatísticas por loja
    lojas = {}
    for o in all_offers:
        loja = o.loja
        lojas[loja] = lojas.get(loja, 0) + 1
    
    print(f"\n🏪 OFERTAS POR LOJA:")
    for loja, count in sorted(lojas.items(), key=lambda x: x[1], reverse=True):
        print(f"  {loja}: {count} ofertas")
    
    # Estatísticas de imagens e afiliados (com proteção contra divisão por zero)
    if all_offers:
        com_imagem = sum(1 for o in all_offers if o.imagem_url)
        com_afiliado = sum(1 for o in all_offers if o.url_afiliado)
        
        print(f"\n📸 ESTATÍSTICAS:")
        print(f"  Com imagem: {com_imagem}/{len(all_offers)} ({com_imagem/len(all_offers)*100:.1f}%)")
        print(f"  Com afiliado: {com_afiliado}/{len(all_offers)} ({com_afiliado/len(all_offers)*100:.1f}%)")
        
        # Gera relatório
        report_path = write_report(all_offers, total_valid, 0)
        print(f"\n📄 Relatório gerado: {report_path}")
        
        # Mostra algumas ofertas de exemplo
        print(f"\n🎯 EXEMPLOS DE OFERTAS VALIDADAS:")
        for i, o in enumerate(all_offers[:3]):
            print(f"  {i+1}. {o.titulo[:60]}...")
            print(f"     💰 {o.preco} | 🏪 {o.loja} | 📸 {'Sim' if o.imagem_url else 'Não'}")
    else:
        print(f"\n⚠️ Nenhuma oferta válida foi coletada. Verifique os logs acima.")
    
    print(f"\n🎯 Execução concluída! Nenhuma oferta foi postada no Telegram.")

if __name__ == "__main__":
    asyncio.run(main())
