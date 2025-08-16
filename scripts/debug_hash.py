#!/usr/bin/env python3
"""
Script de debug para entender por que a deduplicação está falhando
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.offer_hash import offer_hash, offer_hash_components

def debug_offer_hash():
    """Debug da geração de hash de ofertas"""
    
    # Oferta 1
    offer1 = {
        'url_produto': 'https://www.amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogee-20',
        'titulo': 'Smartphone Samsung Galaxy S21 128GB - NOVO LANÇAMENTO!',
        'preco_atual': 'R$ 2.999,00',
        'loja': 'Amazon'
    }
    
    # Oferta 2 (similar, mas com diferenças menores)
    offer2 = {
        'url_produto': 'https://www.amazon.com.br/dp/B08N5WRWNW?tag=garimpeirogee-20&ref=test',
        'titulo': 'Smartphone Samsung Galaxy S21 128GB - PROMOÇÃO ESPECIAL!',
        'preco_atual': 'R$ 2.999,00',
        'loja': 'Amazon.com.br'
    }
    
    print("🔍 DEBUG: Geração de Hash de Ofertas")
    print("=" * 50)
    
    # Gera hashes
    hash1 = offer_hash(offer1)
    hash2 = offer_hash(offer2)
    
    print(f"🔐 Hash 1: {hash1}")
    print(f"🔐 Hash 2: {hash2}")
    print()
    
    # Verifica componentes
    components1 = offer_hash_components(offer1)
    components2 = offer_hash_components(offer2)
    
    print("📋 Componentes da Oferta 1:")
    for key, value in components1.items():
        if key != 'offer_hash':
            print(f"   {key}: {value}")
    
    print()
    print("📋 Componentes da Oferta 2:")
    for key, value in components2.items():
        if key != 'offer_hash':
            print(f"   {key}: {value}")
    
    print()
    
    # Verifica se são iguais
    if hash1 == hash2:
        print("✅ Deduplicação funcionando: hashes iguais")
    else:
        print("❌ Deduplicação falhou: hashes diferentes")
        
        # Identifica diferenças
        print("\n🔍 Análise das diferenças:")
        for key in ['normalized_url', 'normalized_title', 'normalized_price', 'normalized_store']:
            if components1[key] != components2[key]:
                print(f"   {key}:")
                print(f"      Oferta 1: {components1[key]}")
                print(f"      Oferta 2: {components2[key]}")
    
    print()
    
    # Testa com dados mais similares
    print("🧪 Teste com dados mais similares:")
    
    offer3 = {
        'url_produto': 'https://www.amazon.com.br/dp/B08N5WRWNW',
        'titulo': 'Smartphone Samsung Galaxy S21 128GB',
        'preco_atual': 'R$ 2.999,00',
        'loja': 'Amazon'
    }
    
    offer4 = {
        'url_produto': 'https://www.amazon.com.br/dp/B08N5WRWNW',
        'titulo': 'Smartphone Samsung Galaxy S21 128GB',
        'preco_atual': 'R$ 2.999,00',
        'loja': 'Amazon'
    }
    
    hash3 = offer_hash(offer3)
    hash4 = offer_hash(offer4)
    
    print(f"🔐 Hash 3: {hash3}")
    print(f"🔐 Hash 4: {hash4}")
    
    if hash3 == hash4:
        print("✅ Ofertas idênticas geraram hashes iguais")
    else:
        print("❌ Ofertas idênticas geraram hashes diferentes")

if __name__ == "__main__":
    debug_offer_hash()
