#!/usr/bin/env python3
"""
Script para testar a extração de ofertas do Promobit
"""
import requests
from bs4 import BeautifulSoup
import brotli
import re

def test_promobit_extraction():
    """Testa a extração de ofertas do Promobit"""
    url = 'https://www.promobit.com.br/promocoes/informatica/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"🔍 Acessando: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        print(f"✅ Página carregada com sucesso")
        
        # Procura por ofertas usando seletores baseados na estrutura HTML analisada
        print("\n🔍 Procurando por ofertas...")
        
        # Seletor principal: divs que contêm links de oferta
        ofertas = soup.find_all('a', href=re.compile(r'/oferta/'))
        print(f"📊 Encontradas {len(ofertas)} ofertas com links /oferta/")
        
        if ofertas:
            print(f"\n📋 Primeiras 3 ofertas encontradas:")
            print("-" * 60)
            
            for i, oferta in enumerate(ofertas[:3], 1):
                print(f"\n{i}. OFERTA:")
                
                # Extrai o link
                link = oferta.get('href', '')
                if link.startswith('/'):
                    link = f"https://www.promobit.com.br{link}"
                print(f"   🔗 Link: {link}")
                
                # Extrai o título
                titulo_elem = oferta.find('span', class_=re.compile(r'line-clamp-2'))
                if titulo_elem:
                    titulo = titulo_elem.get_text(strip=True)
                    print(f"   📝 Título: {titulo}")
                
                # Extrai o preço atual
                preco_elem = oferta.find('span', class_=re.compile(r'text-primary-400'))
                if preco_elem:
                    preco = preco_elem.get_text(strip=True)
                    print(f"   💰 Preço: {preco}")
                
                # Extrai o preço original (riscado)
                preco_original_elem = oferta.find('span', class_=re.compile(r'line-through'))
                if preco_original_elem:
                    preco_original = preco_original_elem.get_text(strip=True)
                    print(f"   💸 Preço Original: {preco_original}")
                
                # Extrai a loja
                loja_elem = oferta.find('span', class_=re.compile(r'font-bold.*text-sm'))
                if loja_elem:
                    loja = loja_elem.get_text(strip=True)
                    print(f"   🏪 Loja: {loja}")
                
                # Extrai a imagem
                img_elem = oferta.find('img')
                if img_elem:
                    img_src = img_elem.get('src', '')
                    print(f"   🖼️ Imagem: {img_src}")
                
                # Extrai tags/badges
                badges = oferta.find_all('div', class_=re.compile(r'bg-neutral-high-300'))
                if badges:
                    print(f"   🏷️ Tags: {[badge.get_text(strip=True) for badge in badges]}")
                
                print("-" * 40)
        
        # Testa extração usando o scraper existente
        print(f"\n🧪 Testando scraper existente...")
        try:
            from promobit_scraper import buscar_ofertas_promobit
            ofertas_scraper = buscar_ofertas_promobit(max_pages=1)
            print(f"✅ Scraper retornou {len(ofertas_scraper)} ofertas")
            
            if ofertas_scraper:
                print(f"\n📋 Primeira oferta do scraper:")
                oferta = ofertas_scraper[0]
                for key, value in oferta.items():
                    print(f"   {key}: {value}")
                    
        except Exception as e:
            print(f"❌ Erro no scraper: {e}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_promobit_extraction()
