#!/usr/bin/env python3
"""
Script robusto para executar o Dashboard do Garimpeiro Geek
Resolve problemas de execução em background no Windows
"""

import os
import sys
import signal
import time
import threading
from pathlib import Path

# Adiciona o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    try:
        import flask
        import sqlite3
        print("✅ Todas as dependências estão disponíveis")
        return True
    except ImportError as e:
        print(f"❌ Dependência não encontrada: {e}")
        print("Execute: pip install -r requirements.txt")
        return False

def check_database():
    """Verifica se o banco de dados está acessível"""
    try:
        db_path = project_root / "ofertas.db"
        if not db_path.exists():
            print("❌ Banco de dados não encontrado")
            return False
        
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ofertas")
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"✅ Banco de dados acessível: {count} ofertas encontradas")
        return True
    except Exception as e:
        print(f"❌ Erro ao acessar banco de dados: {e}")
        return False

def start_flask_server():
    """Inicia o servidor Flask com configurações otimizadas"""
    try:
        from app import app
        
        print("🚀 Iniciando Dashboard do Garimpeiro Geek...")
        print(f"📊 Banco de dados disponível: {check_database()}")
        
        # Configurações otimizadas para produção
        app.config['ENV'] = 'production'
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        
        # Inicia o servidor
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            use_reloader=False,  # Desabilita reloader automático
            threaded=True        # Habilita threading para melhor performance
        )
        
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor Flask: {e}")
        return False

def start_with_waitress():
    """Tenta iniciar com Waitress (servidor WSGI mais robusto)"""
    try:
        import waitress
        from app import app
        
        print("🚀 Iniciando com Waitress (servidor WSGI robusto)...")
        print("🌐 Acesse: http://127.0.0.1:5000")
        
        waitress.serve(
            app,
            host='127.0.0.1',
            port=5000,
            threads=4,
            connection_limit=1000
        )
        return True
        
    except ImportError:
        print("⚠️ Waitress não instalado. Instalando...")
        os.system("pip install waitress")
        return start_with_waitress()
    except Exception as e:
        print(f"❌ Erro com Waitress: {e}")
        return False

def start_with_gunicorn():
    """Tenta iniciar com Gunicorn (alternativa ao Waitress)"""
    try:
        import subprocess
        from app import app
        
        print("🚀 Iniciando com Gunicorn...")
        print("🌐 Acesse: http://127.0.0.1:5000")
        
        # Comando Gunicorn
        cmd = [
            "gunicorn",
            "--bind", "127.0.0.1:5000",
            "--workers", "2",
            "--timeout", "120",
            "--keep-alive", "5",
            "app:app"
        ]
        
        subprocess.run(cmd, cwd=os.path.dirname(__file__))
        return True
        
    except ImportError:
        print("⚠️ Gunicorn não instalado. Instalando...")
        os.system("pip install gunicorn")
        return start_with_gunicorn()
    except Exception as e:
        print(f"❌ Erro com Gunicorn: {e}")
        return False

def signal_handler(signum, frame):
    """Manipulador de sinais para shutdown graceful"""
    print("\n🛑 Recebido sinal de parada. Encerrando servidor...")
    sys.exit(0)

def main():
    """Função principal"""
    print("=" * 60)
    print("🚀 INICIADOR DO DASHBOARD GARIMPEIRO GEEK")
    print("=" * 60)
    
    # Configura manipuladores de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Verifica dependências
    if not check_dependencies():
        print("❌ Dependências não satisfeitas. Abortando...")
        sys.exit(1)
    
    # Verifica banco de dados
    if not check_database():
        print("⚠️ Problemas com banco de dados, mas continuando...")
    
    print("\n🔧 Escolha o método de execução:")
    print("1. Flask padrão (desenvolvimento)")
    print("2. Waitress (recomendado para Windows)")
    print("3. Gunicorn (alternativa)")
    print("4. Auto-detect (recomendado)")
    
    try:
        choice = input("\nEscolha (1-4) ou Enter para auto-detect: ").strip()
    except KeyboardInterrupt:
        print("\n🛑 Operação cancelada pelo usuário")
        sys.exit(0)
    
    if not choice:
        choice = "4"
    
    print(f"\n🎯 Método selecionado: {choice}")
    
    success = False
    
    if choice == "1":
        success = start_flask_server()
    elif choice == "2":
        success = start_with_waitress()
    elif choice == "3":
        success = start_with_gunicorn()
    elif choice == "4":
        # Auto-detect: tenta Waitress primeiro, depois Flask
        print("🔍 Auto-detectando melhor método...")
        if not start_with_waitress():
            print("⚠️ Waitress falhou, tentando Flask...")
            success = start_flask_server()
        else:
            success = True
    else:
        print("❌ Opção inválida")
        sys.exit(1)
    
    if not success:
        print("❌ Todos os métodos falharam")
        print("💡 Dicas de solução:")
        print("   - Verifique se a porta 5000 está livre")
        print("   - Execute como administrador se necessário")
        print("   - Verifique o firewall do Windows")
        sys.exit(1)

if __name__ == "__main__":
    main()
