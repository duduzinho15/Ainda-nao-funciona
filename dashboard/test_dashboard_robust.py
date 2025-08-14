#!/usr/bin/env python3
"""
Script de teste robusto para o Dashboard
Testa todos os métodos de execução disponíveis
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path

# Adiciona o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_flask_direct():
    """Testa Flask diretamente"""
    print("🔍 Testando Flask diretamente...")
    
    try:
        from app import app
        
        # Inicia servidor em thread separada
        import threading
        
        def run_server():
            app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Aguarda servidor inicializar
        time.sleep(3)
        
        # Testa conexão
        response = requests.get('http://127.0.0.1:5001/health', timeout=5)
        if response.status_code == 200:
            print("✅ Flask funcionando na porta 5001")
            return True
        else:
            print(f"❌ Flask retornou status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro com Flask: {e}")
        return False

def test_waitress():
    """Testa Waitress"""
    print("🔍 Testando Waitress...")
    
    try:
        import waitress
        from app import app
        
        # Inicia servidor em thread separada
        import threading
        
        def run_waitress():
            waitress.serve(app, host='127.0.0.1', port=5002, threads=2)
        
        server_thread = threading.Thread(target=run_waitress, daemon=True)
        server_thread.start()
        
        # Aguarda servidor inicializar
        time.sleep(3)
        
        # Testa conexão
        response = requests.get('http://127.0.0.1:5002/health', timeout=5)
        if response.status_code == 200:
            print("✅ Waitress funcionando na porta 5002")
            return True
        else:
            print(f"❌ Waitress retornou status {response.status_code}")
            return False
            
    except ImportError:
        print("⚠️ Waitress não instalado")
        return False
    except Exception as e:
        print(f"❌ Erro com Waitress: {e}")
        return False

def test_gunicorn():
    """Testa Gunicorn"""
    print("🔍 Testando Gunicorn...")
    
    try:
        # Inicia servidor em processo separado
        cmd = [
            "gunicorn",
            "--bind", "127.0.0.1:5003",
            "--workers", "1",
            "--timeout", "30",
            "--preload",
            "app:app"
        ]
        
        process = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(__file__),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Aguarda servidor inicializar
        time.sleep(5)
        
        # Testa conexão
        try:
            response = requests.get('http://127.0.0.1:5003/health', timeout=5)
            if response.status_code == 200:
                print("✅ Gunicorn funcionando na porta 5003")
                process.terminate()
                return True
            else:
                print(f"❌ Gunicorn retornou status {response.status_code}")
                process.terminate()
                return False
        except:
            process.terminate()
            print("❌ Gunicorn não respondeu")
            return False
            
    except FileNotFoundError:
        print("⚠️ Gunicorn não instalado")
        return False
    except Exception as e:
        print(f"❌ Erro com Gunicorn: {e}")
        return False

def test_all_routes():
    """Testa todas as rotas do dashboard"""
    print("🔍 Testando todas as rotas...")
    
    base_url = "http://127.0.0.1:5000"
    routes = [
        "/",
        "/health",
        "/lojas",
        "/ofertas-hoje",
        "/estatisticas"
    ]
    
    success_count = 0
    total_routes = len(routes)
    
    for route in routes:
        try:
            response = requests.get(f"{base_url}{route}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {route} - OK")
                success_count += 1
            else:
                print(f"❌ {route} - Status {response.status_code}")
        except Exception as e:
            print(f"❌ {route} - Erro: {e}")
    
    print(f"\n📊 Resultado: {success_count}/{total_routes} rotas funcionando")
    return success_count == total_routes

def test_static_files():
    """Testa arquivos estáticos"""
    print("🔍 Testando arquivos estáticos...")
    
    base_url = "http://127.0.0.1:5000"
    static_files = [
        "/static/style.css",
        "/static/script.js"
    ]
    
    success_count = 0
    total_files = len(static_files)
    
    for file_path in static_files:
        try:
            response = requests.get(f"{base_url}{file_path}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {file_path} - OK ({len(response.content)} bytes)")
                success_count += 1
            else:
                print(f"❌ {file_path} - Status {response.status_code}")
        except Exception as e:
            print(f"❌ {file_path} - Erro: {e}")
    
    print(f"\n📊 Resultado: {success_count}/{total_files} arquivos estáticos funcionando")
    return success_count == total_files

def main():
    """Função principal de teste"""
    print("=" * 60)
    print("🧪 TESTE ROBUSTO DO DASHBOARD GARIMPEIRO GEEK")
    print("=" * 60)
    print()
    
    # Verifica se o dashboard está rodando
    print("🔍 Verificando se o dashboard está rodando...")
    try:
        response = requests.get('http://127.0.0.1:5000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Dashboard está rodando na porta 5000")
            dashboard_running = True
        else:
            print(f"⚠️ Dashboard retornou status {response.status_code}")
            dashboard_running = False
    except:
        print("❌ Dashboard não está rodando na porta 5000")
        dashboard_running = False
    
    if not dashboard_running:
        print("\n🚀 Iniciando testes de servidores individuais...")
        
        # Testa cada servidor individualmente
        results = {
            "Flask": test_flask_direct(),
            "Waitress": test_waitress(),
            "Gunicorn": test_gunicorn()
        }
        
        print("\n📊 Resultados dos testes individuais:")
        for server, result in results.items():
            status = "✅ OK" if result else "❌ FALHOU"
            print(f"   {server}: {status}")
        
        working_servers = [server for server, result in results.items() if result]
        if working_servers:
            print(f"\n🎯 Servidores funcionando: {', '.join(working_servers)}")
            print("💡 Use um destes para executar o dashboard")
        else:
            print("\n❌ Nenhum servidor funcionou")
            print("💡 Verifique as dependências e configurações")
    else:
        print("\n🧪 Testando funcionalidades do dashboard...")
        
        # Testa rotas
        routes_ok = test_all_routes()
        
        # Testa arquivos estáticos
        static_ok = test_static_files()
        
        print("\n📊 Resumo dos testes:")
        print(f"   Rotas: {'✅ OK' if routes_ok else '❌ FALHOU'}")
        print(f"   Arquivos estáticos: {'✅ OK' if static_ok else '❌ FALHOU'}")
        
        if routes_ok and static_ok:
            print("\n🎉 Dashboard funcionando perfeitamente!")
        else:
            print("\n⚠️ Dashboard tem alguns problemas")
    
    print("\n" + "=" * 60)
    print("🏁 Teste concluído")
    print("=" * 60)

if __name__ == "__main__":
    main()
