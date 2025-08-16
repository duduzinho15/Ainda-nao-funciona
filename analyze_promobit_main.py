#!/usr/bin/env python3
"""
Script para analisar a página principal do Promobit
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def analyze_promobit_main():
    """Analisa a página principal do Promobit"""
    url = "https://www.promobit.com.br"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print(f"🔍 Analisando: {url}")
            async with session.get(url, headers=headers, timeout=15) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Salva HTML para análise
                    with open('promobit_main.html', 'w', encoding='utf-8') as f:
                        f.write(html)
                    print("✅ HTML salvo em promobit_main.html")
                    
                    # Procura por elementos de oferta
                    print("\n🔍 Procurando por elementos de oferta...")
                    
                    # Procura por cards de produto
                    cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(word in x.lower() for word in ['card', 'produto', 'oferta', 'deal']))
                    print(f"Cards encontrados: {len(cards)}")
                    
                    # Procura por links de oferta
                    links = soup.find_all('a', href=True)
                    oferta_links = [link for link in links if any(word in link['href'].lower() for word in ['oferta', 'produto', 'deal'])]
                    print(f"Links de oferta: {len(oferta_links)}")
                    
                    # Procura por preços
                    precos = soup.find_all(text=lambda text: text and 'R$' in text)
                    print(f"Preços encontrados: {len(precos)}")
                    
                    # Procura por títulos de produtos
                    titulos = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    print(f"Títulos encontrados: {len(titulos)}")
                    
                    # Mostra alguns exemplos
                    if cards:
                        print(f"\n📋 Exemplo de card:")
                        print(f"   Classes: {cards[0].get('class', [])}")
                        print(f"   Conteúdo: {cards[0].get_text()[:200]}...")
                    
                    if oferta_links:
                        print(f"\n🔗 Exemplo de link de oferta:")
                        print(f"   URL: {oferta_links[0]['href']}")
                        print(f"   Texto: {oferta_links[0].get_text()[:100]}...")
                    
                    if precos:
                        print(f"\n💰 Exemplo de preço:")
                        print(f"   Texto: {precos[0][:50]}...")
                    
                else:
                    print(f"❌ Erro: Status {response.status}")
                    
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_promobit_main())
