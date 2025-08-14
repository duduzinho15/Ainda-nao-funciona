#!/usr/bin/env python3
"""
Teste Rápido de Integração
Verifica apenas as importações essenciais dos módulos
"""

import sys

def test_imports():
    """Testa importações básicas"""
    print("🧪 Testando Importações...")
    
    modules = [
        'cache_system',
        'rate_limiter', 
        'health_monitor',
        'performance_metrics',
        'user_categories',
        'price_history',
        'price_comparator',
        'product_reviews',
        'notification_system'
    ]
    
    results = {}
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
            results[module] = True
        except Exception as e:
            print(f"❌ {module}: {e}")
            results[module] = False
    
    # Testa main.py
    try:
        import main
        print("✅ main.py")
        results['main'] = True
    except Exception as e:
        print(f"❌ main.py: {e}")
        results['main'] = False
    
    return results

def main():
    """Função principal"""
    print("🚀 Teste Rápido de Integração")
    print("=" * 40)
    
    results = test_imports()
    
    print("\n📊 RESULTADO:")
    total = len(results)
    success = sum(results.values())
    failed = total - success
    
    print(f"Total: {total}")
    print(f"✅ Sucessos: {success}")
    print(f"❌ Falhas: {failed}")
    print(f"Taxa de sucesso: {(success/total)*100:.1f}%")
    
    if success == total:
        print("\n🎉 TODOS OS MÓDULOS IMPORTADOS COM SUCESSO!")
    else:
        print(f"\n⚠️  {failed} módulo(s) com problema(s)")

if __name__ == "__main__":
    main()
