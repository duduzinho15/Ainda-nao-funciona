#!/usr/bin/env python3
"""
Script para analisar a estrutura do HTML do Pelando
"""
from bs4 import BeautifulSoup
import re

def analyze_pelando_structure():
    """Analisa a estrutura do HTML do Pelando"""
    
    # Lê o HTML salvo
    with open('pelando_debug_simple.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    print("🔍 ANALISANDO ESTRUTURA DO PELANDO")
    print("=" * 50)
    
    # Busca por cards de oferta
    seletores = [
        '[class*="default-deal-card"]',
        '[class*="comment-deal-card"]',
        '[class*="deal-card"]',
        '[class*="card"]'
    ]
    
    for seletor in seletores:
        elementos = soup.select(seletor)
        if elementos:
            print(f"\n✅ Seletor '{seletor}': {len(elementos)} elementos encontrados")
            
            # Analisa o primeiro elemento
            if elementos:
                primeiro = elementos[0]
                print(f"\n📋 Primeiro elemento:")
                print(f"   Tag: {primeiro.name}")
                print(f"   Classes: {primeiro.get('class', [])}")
                print(f"   ID: {primeiro.get('id', 'N/A')}")
                
                # Busca por título
                titulo_elem = primeiro.select_one('[class*="title"]')
                if titulo_elem:
                    print(f"   ✅ Título encontrado: {titulo_elem.get_text(strip=True)[:100]}...")
                else:
                    print(f"   ❌ Título não encontrado")
                
                # Busca por preço
                preco_elem = primeiro.select_one('[class*="price"]')
                if preco_elem:
                    print(f"   ✅ Preço encontrado: {preco_elem.get_text(strip=True)}")
                else:
                    print(f"   ❌ Preço não encontrado")
                
                # Busca por link
                link_elem = primeiro.find('a', href=True)
                if link_elem:
                    print(f"   ✅ Link encontrado: {link_elem.get('href')}")
                else:
                    print(f"   ❌ Link não encontrado")
                
                # Busca por loja
                loja_elem = primeiro.select_one('[class*="store"]')
                if loja_elem:
                    print(f"   ✅ Loja encontrada: {loja_elem.get_text(strip=True)}")
                else:
                    print(f"   ❌ Loja não encontrada")
                
                # Mostra HTML do primeiro elemento (limitado)
                html_elemento = str(primeiro)[:500]
                print(f"\n📄 HTML (primeiros 500 chars):")
                print(f"   {html_elemento}...")
                
                break
        else:
            print(f"❌ Seletor '{seletor}': Nenhum elemento encontrado")
    
    # Busca por outros elementos que podem conter ofertas
    print(f"\n🔍 BUSCA ALTERNATIVA:")
    
    # Busca por elementos com links de oferta
    links_oferta = soup.find_all('a', href=re.compile(r'/deal/|/oferta/|/produto/'))
    print(f"   Links de oferta: {len(links_oferta)} encontrados")
    
    # Busca por elementos com texto de preço
    precos = soup.find_all(string=re.compile(r'R\$\s*\d+'))
    print(f"   Textos com preço: {len(precos)} encontrados")
    
    # Busca por elementos com texto de título
    titulos = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    print(f"   Títulos: {len(titulos)} encontrados")
    
    # Busca por elementos com classe que contenha "deal"
    deals = soup.find_all(class_=re.compile(r'deal'))
    print(f"   Elementos com 'deal': {len(deals)} encontrados")

if __name__ == "__main__":
    analyze_pelando_structure()
