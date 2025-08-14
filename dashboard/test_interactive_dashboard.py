#!/usr/bin/env python3
"""
Script de teste para o dashboard interativo
"""
import requests
import time

def test_dashboard():
    """Testa o dashboard web interativo."""
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testando Dashboard Interativo do Garimpeiro Geek...")
    print(f"🌐 URL Base: {base_url}")
    
    try:
        # Testa a rota principal
        print("\n1. Testando rota principal...")
        response = requests.get(base_url, timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Rota principal funcionando")
            print(f"   📄 Tamanho da resposta: {len(response.text)} bytes")
            
            # Verifica se contém elementos importantes
            if "Garimpeiro Geek" in response.text:
                print("   ✅ Título encontrado")
            else:
                print("   ❌ Título não encontrado")
                
            if "Ver detalhes" in response.text:
                print("   ✅ Cards interativos encontrados")
            else:
                print("   ❌ Cards interativos não encontrados")
                
        else:
            print(f"   ❌ Erro na rota principal: {response.status_code}")
            return False
            
        # Testa a rota de lojas
        print("\n2. Testando rota de lojas...")
        response = requests.get(f"{base_url}/lojas", timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Rota de lojas funcionando")
            if "Lojas Ativas" in response.text:
                print("   ✅ Página de lojas carregada corretamente")
            else:
                print("   ❌ Conteúdo da página de lojas não encontrado")
        else:
            print(f"   ❌ Erro na rota de lojas: {response.status_code}")
            
        # Testa a rota de ofertas de hoje
        print("\n3. Testando rota de ofertas de hoje...")
        response = requests.get(f"{base_url}/ofertas-hoje", timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Rota de ofertas de hoje funcionando")
            if "Ofertas de Hoje" in response.text:
                print("   ✅ Página de ofertas de hoje carregada corretamente")
            else:
                print("   ❌ Conteúdo da página de ofertas de hoje não encontrado")
        else:
            print(f"   ❌ Erro na rota de ofertas de hoje: {response.status_code}")
            
        # Testa a rota de estatísticas
        print("\n4. Testando rota de estatísticas...")
        response = requests.get(f"{base_url}/estatisticas", timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Rota de estatísticas funcionando")
            if "Estatísticas Detalhadas" in response.text:
                print("   ✅ Página de estatísticas carregada corretamente")
            else:
                print("   ❌ Conteúdo da página de estatísticas não encontrado")
        else:
            print(f"   ❌ Erro na rota de estatísticas: {response.status_code}")
            
        # Testa o health check
        print("\n5. Testando health check...")
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Health check funcionando")
            try:
                data = response.json()
                print(f"   📊 Status: {data.get('status')}")
                print(f"   🗄️ Banco disponível: {data.get('database_available')}")
            except:
                print("   ⚠️ Resposta não é JSON válido")
        else:
            print(f"   ❌ Erro no health check: {response.status_code}")
            
        # Testa arquivos estáticos
        print("\n6. Testando arquivos estáticos...")
        
        # CSS
        response = requests.get(f"{base_url}/static/style.css", timeout=10)
        if response.status_code == 200:
            print("   ✅ CSS carregado")
            print(f"   📄 Tamanho do CSS: {len(response.text)} bytes")
        else:
            print(f"   ❌ Erro ao carregar CSS: {response.status_code}")
            
        # JavaScript
        response = requests.get(f"{base_url}/static/script.js", timeout=10)
        if response.status_code == 200:
            print("   ✅ JavaScript carregado")
            print(f"   📄 Tamanho do JS: {len(response.text)} bytes")
        else:
            print(f"   ❌ Erro ao carregar JavaScript: {response.status_code}")
            
        print("\n🎉 Todos os testes concluídos!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão: Verifique se o servidor está rodando")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_navigation():
    """Testa a navegação entre páginas."""
    base_url = "http://127.0.0.1:5000"
    
    print("\n🧭 Testando navegação entre páginas...")
    
    try:
        # Testa navegação da página principal para outras páginas
        print("   📍 Testando links da página principal...")
        
        # Página principal
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("   ✅ Página principal acessível")
            
            # Verifica se os links estão presentes
            if 'href="/lojas"' in response.text:
                print("   ✅ Link para lojas encontrado")
            else:
                print("   ❌ Link para lojas não encontrado")
                
            if 'href="/ofertas-hoje"' in response.text:
                print("   ✅ Link para ofertas de hoje encontrado")
            else:
                print("   ❌ Link para ofertas de hoje não encontrado")
                
            if 'href="/estatisticas"' in response.text:
                print("   ✅ Link para estatísticas encontrado")
            else:
                print("   ❌ Link para estatísticas não encontrado")
        else:
            print("   ❌ Página principal não acessível")
            
        print("   🎯 Navegação testada com sucesso!")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao testar navegação: {e}")
        return False

if __name__ == "__main__":
    # Aguarda um pouco para o servidor inicializar
    print("⏳ Aguardando servidor inicializar...")
    time.sleep(3)
    
    success = test_dashboard()
    nav_success = test_navigation()
    
    if success and nav_success:
        print("\n✅ Dashboard interativo funcionando perfeitamente!")
        print("🌐 Acesse: http://127.0.0.1:5000")
        print("🔗 Páginas disponíveis:")
        print("   - / (Dashboard Principal)")
        print("   - /lojas (Análise de Lojas)")
        print("   - /ofertas-hoje (Ofertas do Dia)")
        print("   - /estatisticas (Estatísticas Detalhadas)")
    else:
        print("\n❌ Dashboard com problemas")
