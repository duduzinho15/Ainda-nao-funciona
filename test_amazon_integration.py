#!/usr/bin/env python3
"""
Teste da Integração do Amazon Scraper com o Sistema Principal
Verifica se o scraper está funcionando e se as mensagens estão sendo formatadas corretamente
"""
import sys
import os
import asyncio
from datetime import datetime

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_amazon_scraper():
    """Testa o Amazon Scraper isoladamente"""
    print("🔍 TESTE 1: AMAZON SCRAPER ISOLADO")
    print("=" * 60)
    
    try:
        from amazon_api_scraper import AmazonAPIScraper
        
        scraper = AmazonAPIScraper()
        
        # Testa conexão
        if not scraper.test_connection():
            print("❌ Falha na conexão com a Amazon")
            return False
        
        # Busca ofertas (limita para teste)
        print("🔍 Buscando ofertas...")
        ofertas = scraper.buscar_ofertas_gerais()
        
        if not ofertas:
            print("❌ Nenhuma oferta encontrada")
            return False
        
        print(f"✅ {len(ofertas)} ofertas encontradas")
        
        # Mostra algumas ofertas
        for i, oferta in enumerate(ofertas[:3], 1):
            print(f"\n{i}. {oferta['titulo'][:50]}...")
            print(f"   💰 Preço: {oferta['preco']}")
            print(f"   🏪 Loja: {oferta['loja']}")
            print(f"   📂 Categoria: {oferta['categoria']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do scraper: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_message_formatting():
    """Testa a formatação de mensagens"""
    print("\n🔍 TESTE 2: FORMATAÇÃO DE MENSAGENS")
    print("=" * 60)
    
    try:
        # Simula uma oferta do Amazon Scraper
        oferta_teste = {
            'titulo': 'Apple iPhone 16 Pro (128 GB) – Titânio preto',
            'preco': '7.799,',
            'link': 'https://www.amazon.com.br/Apple-iPhone-16-Pro-128/dp/B0DGMH7J54',
            'loja': 'Amazon Brasil',
            'categoria': 'smartphones',
            'desconto': 15
        }
        
        # Importa a função de formatação
        from main import formatar_mensagem_oferta
        
        # Formata a mensagem
        mensagem = formatar_mensagem_oferta(oferta_teste)
        
        print("✅ Mensagem formatada com sucesso:")
        print("-" * 40)
        print(mensagem)
        print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na formatação: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Testa a integração completa"""
    print("\n🔍 TESTE 3: INTEGRAÇÃO COMPLETA")
    print("=" * 60)
    
    try:
        # Simula o processo de busca e formatação
        from amazon_api_scraper import AmazonAPIScraper
        from main import formatar_mensagem_oferta
        
        print("🔍 Buscando ofertas na Amazon...")
        scraper = AmazonAPIScraper()
        ofertas = scraper.buscar_ofertas_gerais()
        
        if not ofertas:
            print("❌ Nenhuma oferta para testar")
            return False
        
        print(f"✅ {len(ofertas)} ofertas encontradas")
        
        # Filtra e formata algumas ofertas
        ofertas_filtradas = []
        for oferta in ofertas:
            try:
                # Prioriza ofertas com desconto
                if oferta.get('desconto') and oferta['desconto'] >= 10:
                    ofertas_filtradas.append(oferta)
                # Ou produtos com preços competitivos
                elif float(oferta['preco']) < 1000:
                    ofertas_filtradas.append(oferta)
                
                if len(ofertas_filtradas) >= 3:
                    break
            except (ValueError, TypeError) as e:
                print(f"⚠️ Erro ao processar preço da oferta: {oferta.get('titulo', 'Sem título')} - {e}")
                continue
        
        print(f"✅ {len(ofertas_filtradas)} ofertas filtradas")
        
        # Formata as mensagens
        for i, oferta in enumerate(ofertas_filtradas, 1):
            print(f"\n📝 OFERTA {i}:")
            mensagem = formatar_mensagem_oferta(oferta)
            print(mensagem)
            print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal de teste"""
    print("🚀 TESTE COMPLETO DA INTEGRAÇÃO AMAZON")
    print("=" * 60)
    print(f"⏰ Início: {datetime.now().strftime('%H:%M:%S')}")
    
    resultados = []
    
    # Teste 1: Amazon Scraper
    resultado1 = test_amazon_scraper()
    resultados.append(("Amazon Scraper", resultado1))
    
    # Teste 2: Formatação de Mensagens
    resultado2 = test_message_formatting()
    resultados.append(("Formatação de Mensagens", resultado2))
    
    # Teste 3: Integração Completa
    resultado3 = test_integration()
    resultados.append(("Integração Completa", resultado3))
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print("=" * 60)
    
    for nome_teste, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{nome_teste}: {status}")
    
    total_passou = sum(1 for _, resultado in resultados if resultado)
    total_testes = len(resultados)
    
    print(f"\n🎯 RESULTADO: {total_passou}/{total_testes} testes passaram")
    
    if total_passou == total_testes:
        print("🎉 TODOS OS TESTES PASSARAM! Integração funcionando perfeitamente!")
    else:
        print("⚠️ Alguns testes falharam. Verifique os erros acima.")
    
    print(f"\n⏰ Fim: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
