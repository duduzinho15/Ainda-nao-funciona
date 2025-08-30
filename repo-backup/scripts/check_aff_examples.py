#!/usr/bin/env python3
"""
Script para validar todos os exemplos de afiliados em lote.

Lê os padrões dos arquivos de referência e valida cada exemplo
contra o sistema de validação implementado.
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.affiliate_validator import validate_affiliate_link, get_validation_summary
from src.affiliate.awin import build_awin_deeplink, validate_awin_deeplink
from src.affiliate.mercadolivre import validate_mercadolivre_url, generate_ml_affiliate_url
from src.affiliate.shopee import validate_shopee_url, generate_shopee_shortlink
from src.affiliate.aliexpress import validate_aliexpress_url, generate_aliexpress_shortlink
from src.affiliate.magazineluiza import validate_magazineluiza_url, generate_magazine_affiliate_url

def test_awin_examples():
    """Testa exemplos Awin"""
    print("🔗 TESTANDO EXEMPLOS AWIN")
    print("=" * 50)
    
    # Exemplos do arquivo de referência
    test_cases = [
        ("https://www.comfy.com.br/", "Comfy"),
        ("https://www.trocafy.com.br/", "Trocafy"),
        ("https://www.lg.com/br/", "LG"),
        ("https://www.kabum.com.br/", "KaBuM"),
        ("https://www.comfy.com.br/cadeira-de-escritorio-comfy-ergopro-cinza-tela-mesh-cinza-braco-ajustavel-e-relax-avancado.html", "Comfy"),
        ("https://www.trocafy.com.br/smartphone-samsung-galaxy-s22-256gb-verde-5g-8gb-ram-tela-6-1-camera-tripla-de-50mp-10mp-12mp-frontal-10mp-sou-como-novo-4607/p", "Trocafy")
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for url, expected_store in test_cases:
        print(f"\n🔍 Testando: {expected_store}")
        print(f"   URL: {url}")
        
        # Gerar deeplink
        success, deeplink, error = build_awin_deeplink(url)
        
        if success:
            print(f"   ✅ SUCESSO: {deeplink[:80]}...")
            
            # Validar o deeplink gerado
            is_valid, validation_error = validate_awin_deeplink(deeplink)
            if is_valid:
                print(f"   ✅ VALIDAÇÃO: Deeplink válido")
                success_count += 1
            else:
                print(f"   ❌ VALIDAÇÃO: {validation_error}")
        else:
            print(f"   ❌ FALHA: {error}")
    
    print(f"\n📊 RESULTADO AWIN: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    return success_count, total_count

def test_mercadolivre_examples():
    """Testa exemplos Mercado Livre"""
    print("\n🛒 TESTANDO EXEMPLOS MERCADO LIVRE")
    print("=" * 50)
    
    test_cases = [
        "https://mercadolivre.com/sec/1vt6gtj",
        "https://mercadolivre.com/sec/2AsYJk3",
        "https://mercadolivre.com/sec/27Hhvsc",
        "https://www.mercadolivre.com.br/produto/MLB-123456789",
        "https://www.mercadolivre.com.br/social/garimpeirogeek?matt_word=garimpeirogeek&matt_tool=82173227&forceInApp=true&ref=test"
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for url in test_cases:
        print(f"\n🔍 Testando: {url}")
        
        is_valid, error = validate_mercadolivre_url(url)
        
        if is_valid:
            print(f"   ✅ VÁLIDO")
            success_count += 1
        else:
            print(f"   ❌ INVÁLIDO: {error}")
    
    print(f"\n📊 RESULTADO MERCADO LIVRE: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    return success_count, total_count

def test_shopee_examples():
    """Testa exemplos Shopee"""
    print("\n🛍️ TESTANDO EXEMPLOS SHOPEE")
    print("=" * 50)
    
    test_cases = [
        "https://s.shopee.com.br/3LGfnEjEXu",
        "https://s.shopee.com.br/3Va5zXibCx",
        "https://s.shopee.com.br/4L9Cz4fQW8",
        "https://shopee.com.br/iPhone-16-Pro-Max-256GB-5G-eSIM-XDR-OLED-6-9-Polegadas-C%C3%A2mera-48MP-HDR-Inteligente-5-Tit%C3%A2nio-i.337570318.22498324413"
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for url in test_cases:
        print(f"\n🔍 Testando: {url}")
        
        is_valid, error = validate_shopee_url(url)
        
        if is_valid:
            print(f"   ✅ VÁLIDO")
            success_count += 1
        else:
            print(f"   ❌ INVÁLIDO: {error}")
    
    # Teste de geração de shortlink
    print(f"\n🔧 TESTANDO GERAÇÃO DE SHORTLINK:")
    test_product_url = "https://shopee.com.br/iPhone-16-Pro-Max-256GB-5G-eSIM-XDR-OLED-6-9-Polegadas-C%C3%A2mera-48MP-HDR-Inteligente-5-Tit%C3%A2nio-i.337570318.22498324413"
    
    success, shortlink, error = generate_shopee_shortlink(test_product_url)
    
    if success:
        print(f"   ✅ SUCESSO: {shortlink}")
        success_count += 1
    else:
        print(f"   ❌ FALHA: {error}")
    
    total_count += 1
    
    print(f"\n📊 RESULTADO SHOPEE: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    return success_count, total_count

def test_aliexpress_examples():
    """Testa exemplos AliExpress"""
    print("\n🌐 TESTANDO EXEMPLOS ALIEXPRESS")
    print("=" * 50)
    
    test_cases = [
        "https://s.click.aliexpress.com/e/_opftn1L",
        "https://s.click.aliexpress.com/e/_okCiVDF",
        "https://s.click.aliexpress.com/e/_oo01Cb7",
        "https://pt.aliexpress.com/item/1005006756452012.html?scm=null&pvid=null&gatewayAdapt=glo2bra"
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for url in test_cases:
        print(f"\n🔍 Testando: {url}")
        
        is_valid, error = validate_aliexpress_url(url)
        
        if is_valid:
            print(f"   ✅ VÁLIDO")
            success_count += 1
        else:
            print(f"   ❌ INVÁLIDO: {error}")
    
    # Teste de geração de shortlink
    print(f"\n🔧 TESTANDO GERAÇÃO DE SHORTLINK:")
    test_product_url = "https://pt.aliexpress.com/item/1005006756452012.html?scm=null&pvid=null&gatewayAdapt=glo2bra"
    
    success, shortlink, error = generate_aliexpress_shortlink(test_product_url)
    
    if success:
        print(f"   ✅ SUCESSO: {shortlink}")
        success_count += 1
    else:
        print(f"   ❌ FALHA: {error}")
    
    total_count += 1
    
    print(f"\n📊 RESULTADO ALIEXPRESS: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    return success_count, total_count

def test_magazineluiza_examples():
    """Testa exemplos Magazine Luiza"""
    print("\n🏪 TESTANDO EXEMPLOS MAGAZINE LUIZA")
    print("=" * 50)
    
    test_cases = [
        "https://www.magazinevoce.com.br/magazinegarimpeirogeek/apple-iphone-14-128gb-estelar-61-12mp-ios-5g/p/237184100/te/ip14/",
        "https://www.magazinevoce.com.br/magazinegarimpeirogeek/apple-iphone-14-128gb-meia-noite-61-12mp-ios-5g/p/237184000/te/ip14/",
        "https://www.magazineluiza.com.br/apple-iphone-14-128gb-estelar-61-12mp-ios-5g/p/237184100/te/ip14/"
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for url in test_cases:
        print(f"\n🔍 Testando: {url}")
        
        is_valid, error = validate_magazineluiza_url(url)
        
        if is_valid:
            print(f"   ✅ VÁLIDO")
            success_count += 1
        else:
            print(f"   ❌ INVÁLIDO: {error}")
    
    # Teste de geração de URL de afiliado
    print(f"\n🔧 TESTANDO GERAÇÃO DE URL DE AFILIADO:")
    test_product_url = "https://www.magazineluiza.com.br/apple-iphone-14-128gb-estelar-61-12mp-ios-5g/p/237184100/te/ip14/"
    
    success, affiliate_url, error = generate_magazine_affiliate_url(test_product_url)
    
    if success:
        print(f"   ✅ SUCESSO: {affiliate_url}")
        success_count += 1
    else:
        print(f"   ❌ FALHA: {error}")
    
    total_count += 1
    
    print(f"\n📊 RESULTADO MAGAZINE LUIZA: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    return success_count, total_count

def test_amazon_examples():
    """Testa exemplos Amazon"""
    print("\n📦 TESTANDO EXEMPLOS AMAZON")
    print("=" * 50)
    
    test_cases = [
        "https://www.amazon.com.br/Apple-iPhone-13-256-GB-das-estrelas/dp/B09T4WC9GN?tag=garimpeirogee-20&language=pt_BR",
        "https://www.amazon.com.br/Notebook-ASUS-Gaming-KeepOS-RTX3050/dp/B0D63QVQ9K?tag=garimpeirogee-20&language=pt_BR"
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for url in test_cases:
        print(f"\n🔍 Testando: {url}")
        
        is_valid, platform, error = validate_affiliate_link(url)
        
        if is_valid:
            print(f"   ✅ VÁLIDO - {platform.upper()}")
            success_count += 1
        else:
            print(f"   ❌ INVÁLIDO - {platform.upper()}: {error}")
    
    print(f"\n📊 RESULTADO AMAZON: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    return success_count, total_count

def main():
    """Função principal"""
    print("🧪 VALIDAÇÃO EM LOTE DOS EXEMPLOS DE AFILIADOS")
    print("=" * 70)
    print("Este script valida todos os exemplos dos arquivos de referência")
    print("contra o sistema de validação implementado.")
    print()
    
    # Executar todos os testes
    results = []
    
    results.append(test_awin_examples())
    results.append(test_mercadolivre_examples())
    results.append(test_shopee_examples())
    results.append(test_aliexpress_examples())
    results.append(test_magazineluiza_examples())
    results.append(test_amazon_examples())
    
    # Resumo final
    print("\n" + "=" * 70)
    print("📊 RESUMO FINAL DOS TESTES")
    print("=" * 70)
    
    total_success = sum(success for success, _ in results)
    total_tests = sum(total for _, total in results)
    
    print(f"Total de testes: {total_tests}")
    print(f"Total de sucessos: {total_success}")
    print(f"Taxa de sucesso: {total_success/total_tests*100:.1f}%")
    
    if total_success == total_tests:
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema de validação funcionando perfeitamente.")
    else:
        print(f"\n⚠️  {total_tests - total_success} testes falharam. Verifique as implementações.")
    
    # Mostrar resumo das validações
    print("\n📋 RESUMO DAS VALIDAÇÕES DISPONÍVEIS:")
    summary = get_validation_summary()
    for platform, description in summary['descriptions'].items():
        print(f"   {platform.upper()}: {description}")

if __name__ == "__main__":
    main()
