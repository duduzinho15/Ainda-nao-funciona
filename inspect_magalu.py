#!/usr/bin/env python3
"""
Script temporário para inspecionar a estrutura HTML do Magazine Luiza
"""
import requests
from bs4 import BeautifulSoup
import brotli

def inspect_magalu():
    """Inspeciona a estrutura HTML do Magazine Luiza"""
    url = 'https://www.magazineluiza.com.br/selecao/ofertasdodia/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"🔍 Acessando: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"✅ Status: {response.status_code}")
        print(f"📄 Content-Type: {response.headers.get('content-type')}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        print(f"📝 Título da página: {soup.title.string if soup.title else 'N/A'}")
        
        # Tenta diferentes seletores
        print("\n🔍 Testando seletores...")
        
        # Seletor 1: data-testid
        produtos1 = soup.find_all('li', {'data-testid': 'product-card-container'})
        print(f"1. data-testid='product-card-container': {len(produtos1)} produtos")
        
        # Seletor 2: classes com 'product'
        produtos2 = soup.find_all('li', class_=lambda c: c and 'product' in c.lower())
        print(f"2. Classe contendo 'product': {len(produtos2)} produtos")
        
        # Seletor 3: qualquer li com link de produto
        produtos3 = soup.find_all('li')
        produtos_com_link = [p for p in produtos3 if p.find('a', href=lambda h: h and '/p/' in h)]
        print(f"3. Li com link de produto (/p/): {len(produtos_com_link)} produtos")
        
        # Seletor 4: divs com 'product'
        produtos4 = soup.find_all('div', class_=lambda c: c and 'product' in c.lower())
        print(f"4. Div com classe contendo 'product': {len(produtos4)} produtos")
        
        # Seletor 5: qualquer elemento com link de produto
        links_produto = soup.find_all('a', href=lambda h: h and '/p/' in h)
        print(f"5. Links de produto (/p/): {len(links_produto)} produtos")
        
        # Mostra detalhes do primeiro produto encontrado
        if produtos_com_link:
            print(f"\n📋 Primeiro produto encontrado:")
            primeiro = produtos_com_link[0]
            print(f"   HTML: {primeiro}")
            
            # Procura por título
            titulo = primeiro.find('h2') or primeiro.find('h3') or primeiro.find('h4')
            if titulo:
                print(f"   Título: {titulo.get_text(strip=True)}")
            
            # Procura por preço
            preco = primeiro.find('span', class_=lambda c: c and 'price' in c.lower())
            if preco:
                print(f"   Preço: {preco.get_text(strip=True)}")
            
            # Procura por link
            link = primeiro.find('a', href=True)
            if link:
                print(f"   Link: {link['href']}")
        
        # Salva o HTML para análise manual
        with open('magalu_inspect.html', 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"\n💾 HTML salvo em: magalu_inspect.html")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_magalu()
