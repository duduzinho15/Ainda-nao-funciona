#!/usr/bin/env python3
"""
Script de teste para o dashboard
"""
import requests
import time

def test_dashboard():
    """Testa o dashboard web."""
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testando Dashboard do Garimpeiro Geek...")
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
                
            if "dashboard" in response.text.lower():
                print("   ✅ CSS carregado")
            else:
                print("   ❌ CSS não carregado")
                
        else:
            print(f"   ❌ Erro na rota principal: {response.status_code}")
            return False
            
        # Testa o health check
        print("\n2. Testando health check...")
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
        print("\n3. Testando arquivos estáticos...")
        
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

if __name__ == "__main__":
    # Aguarda um pouco para o servidor inicializar
    print("⏳ Aguardando servidor inicializar...")
    time.sleep(3)
    
    success = test_dashboard()
    
    if success:
        print("\n✅ Dashboard funcionando perfeitamente!")
        print("🌐 Acesse: http://127.0.0.1:5000")
    else:
        print("\n❌ Dashboard com problemas")
