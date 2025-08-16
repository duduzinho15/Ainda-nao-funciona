#!/usr/bin/env python3
"""
Script para debugar a lógica de filtragem de produtos
"""
import asyncio
import logging
from auto_poster_integrated import AutoPosterIntegrated

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def debug_filtering():
    """Debuga a lógica de filtragem de produtos"""
    
    print("🔍 DEBUGANDO LÓGICA DE FILTRAGEM")
    print("=" * 60)
    
    try:
        # Cria instância do auto poster
        auto_poster = AutoPosterIntegrated()
        
        print("📦 Coletando produtos...")
        
        # Coleta produtos
        products = await auto_poster.collect_products_from_orchestrator()
        
        print(f"📊 Total de produtos coletados: {len(products)}")
        
        # Analisa produtos por fonte
        products_by_source = {}
        for product in products:
            source = product.get('fonte', 'N/A')
            if source not in products_by_source:
                products_by_source[source] = []
            products_by_source[source].append(product)
        
        print("\n📋 Produtos por fonte:")
        for source, source_products in products_by_source.items():
            print(f"   {source}: {len(source_products)} produtos")
        
        # Analisa produtos do Promobit especificamente
        if 'Promobit' in products_by_source:
            print(f"\n🔍 ANALISANDO PRODUTOS DO PROMOBIT ({len(products_by_source['Promobit'])} produtos)")
            
            promobit_products = products_by_source['Promobit']
            
            for i, product in enumerate(promobit_products[:10], 1):  # Primeiros 10
                print(f"\n   Produto {i}: {product.get('titulo', 'Sem título')[:60]}...")
                print(f"      Loja: {product.get('loja', 'N/A')}")
                print(f"      Preço: {product.get('preco', 'N/A')}")
                print(f"      URL: {product.get('url_produto', 'N/A')[:50]}...")
                
                # Verifica cada critério de filtro
                product_id = auto_poster.generate_product_id(product)
                already_posted = product_id in auto_poster.posted_products
                print(f"      Já postado: {'✅' if already_posted else '❌'}")
                
                is_valid = auto_poster.is_valid_product(product)
                print(f"      Produto válido: {'✅' if is_valid else '❌'}")
                
                is_geek = auto_poster.is_geek_product(product)
                print(f"      Produto geek: {'✅' if is_geek else '❌'}")
                
                # Verifica filtro de lojas afiliadas
                is_affiliated = auto_poster.is_affiliated_store(product)
                print(f"      Loja afiliada: {'✅' if is_affiliated else '❌'}")
                
                # Mostra campos obrigatórios
                required_fields = ['titulo', 'preco', 'url_produto']
                for field in required_fields:
                    value = product.get(field)
                    print(f"      {field}: {'✅' if value else '❌'} ({value[:30] if value else 'N/A'}...)")
                
                # Verifica se seria filtrado
                if not already_posted and is_valid and is_geek and is_affiliated:
                    print(f"      🎯 SERIA POSTADO: ✅")
                else:
                    print(f"      🎯 SERIA POSTADO: ❌")
                    if already_posted:
                        print(f"         Motivo: Já postado")
                    if not is_valid:
                        print(f"         Motivo: Produto inválido")
                    if not is_geek:
                        print(f"         Motivo: Não é produto geek")
                    if not is_affiliated:
                        print(f"         Motivo: Loja sem afiliação")
        
        # Analisa produtos do Buscapé (que estão sendo filtrados incorretamente)
        if 'Buscapé' in products_by_source:
            print(f"\n🔍 ANALISANDO PRODUTOS DO BUSCAPÉ ({len(products_by_source['Buscapé'])} produtos)")
            
            buscape_products = products_by_source['Buscapé']
            
            for i, product in enumerate(buscape_products[:5], 1):  # Primeiros 5
                print(f"\n   Produto {i}: {product.get('titulo', 'Sem título')[:60]}...")
                print(f"      Loja: {product.get('loja', 'N/A')}")
                print(f"      Preço: {product.get('preco', 'N/A')}")
                
                # Verifica cada critério de filtro
                product_id = auto_poster.generate_product_id(product)
                already_posted = product_id in auto_poster.posted_products
                print(f"      Já postado: {'✅' if already_posted else '❌'}")
                
                is_valid = auto_poster.is_valid_product(product)
                print(f"      Produto válido: {'✅' if is_valid else '❌'}")
                
                is_geek = auto_poster.is_geek_product(product)
                print(f"      Produto geek: {'✅' if is_geek else '❌'}")
                
                # Verifica filtro de lojas afiliadas
                is_affiliated = auto_poster.is_affiliated_store(product)
                print(f"      Loja afiliada: {'✅' if is_affiliated else '❌'}")
                
                # Verifica se seria filtrado
                if not already_posted and is_valid and is_geek and is_affiliated:
                    print(f"      🎯 SERIA POSTADO: ✅")
                else:
                    print(f"      🎯 SERIA POSTADO: ❌")
                    if already_posted:
                        print(f"         Motivo: Já postado")
                    if not is_valid:
                        print(f"         Motivo: Produto inválido")
                    if not is_geek:
                        print(f"         Motivo: Não é produto geek")
                    if not is_affiliated:
                        print(f"         Motivo: Loja sem afiliação")
        
        print("\n" + "=" * 60)
        print("🏁 DEBUG CONCLUÍDO")
        
    except Exception as e:
        print(f"❌ Erro durante o debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_filtering())
