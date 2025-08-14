#!/usr/bin/env python3
"""
SOLUÇÃO DEFINITIVA para Windows - Dashboard Garimpeiro Geek
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Adiciona o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_windows_batch():
    """Cria um arquivo batch para executar como administrador"""
    batch_content = '''@echo off
chcp 65001 >nul
title Dashboard Garimpeiro Geek - Administrador

echo.
echo ============================================================
echo 🚀 INICIADOR DO DASHBOARD GARIMPEIRO GEEK
echo ============================================================
echo.

:: Verifica se é administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Executando como administrador
) else (
    echo ⚠️ Não é administrador
    echo 🔧 Tentando elevar privilégios...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" && \"%~f0\"' -Verb RunAs"
    exit /b
)

:: Ativa ambiente virtual
if not defined VIRTUAL_ENV (
    echo 🔧 Ativando ambiente virtual...
    call "..\\venv\\Scripts\\activate.bat"
)

:: Instala dependências se necessário
echo 🔍 Verificando dependências...
python -c "import waitress" 2>nul || (
    echo ⚠️ Waitress não instalado, instalando...
    pip install waitress
)

:: Inicia o dashboard
echo 🚀 Iniciando dashboard...
python -c "from app import app; import waitress; print('✅ Dashboard iniciado!'); print('🌐 Acesse: http://127.0.0.1:5000'); waitress.serve(app, host='127.0.0.1', port=5000)"

pause
'''
    
    batch_path = Path(__file__).parent / "start_admin.bat"
    with open(batch_path, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    return batch_path

def start_with_port_alternative():
    """Tenta iniciar em uma porta alternativa"""
    print("🔄 Tentando porta alternativa (8080)...")
    
    try:
        from app import app
        
        # Configurações para porta alternativa
        app.config['ENV'] = 'production'
        app.config['DEBUG'] = False
        
        print("🚀 Iniciando na porta 8080...")
        print("🌐 Acesse: http://127.0.0.1:8080")
        
        app.run(
            host='127.0.0.1',
            port=8080,
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Falhou na porta 8080: {e}")
        return False

def start_with_localhost_only():
    """Tenta iniciar apenas com localhost"""
    print("🔄 Tentando apenas localhost...")
    
    try:
        from app import app
        
        print("🚀 Iniciando apenas localhost...")
        print("🌐 Acesse: http://localhost:5000")
        
        app.run(
            host='localhost',
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Falhou com localhost: {e}")
        return False

def main():
    """Função principal"""
    print("=" * 70)
    print("🚀 SOLUÇÃO DEFINITIVA - DASHBOARD GARIMPEIRO GEEK")
    print("=" * 70)
    print()
    
    # Verifica se é Windows
    if os.name != 'nt':
        print("❌ Este script é específico para Windows")
        sys.exit(1)
    
    print("🔍 DIAGNÓSTICO DO PROBLEMA:")
    print("   O Windows está bloqueando conexões locais por segurança")
    print("   Isso é comum com Windows Defender e configurações de rede")
    print()
    
    # Verifica dependências
    try:
        import flask
        import sqlite3
        print("✅ Dependências básicas: OK")
    except ImportError as e:
        print(f"❌ Dependência não encontrada: {e}")
        print("💡 Execute: pip install flask sqlite3")
        sys.exit(1)
    
    # Verifica banco de dados
    try:
        db_path = project_root / "ofertas.db"
        if db_path.exists():
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ofertas")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"✅ Banco de dados: {count} ofertas")
        else:
            print("⚠️ Banco de dados não encontrado")
    except Exception as e:
        print(f"⚠️ Erro no banco: {e}")
    
    print("\n🔧 SOLUÇÕES DISPONÍVEIS:")
    print("1. 🚀 Executar como administrador (RECOMENDADO)")
    print("2. 🔄 Tentar porta alternativa (8080)")
    print("3. 🌐 Tentar apenas localhost")
    print("4. 📋 Criar script batch para administrador")
    print("5. ❌ Sair")
    
    try:
        choice = input("\nEscolha (1-5): ").strip()
    except KeyboardInterrupt:
        print("\n🛑 Operação cancelada")
        sys.exit(0)
    
    if choice == "1":
        print("\n🚀 Executando como administrador...")
        print("💡 Se não funcionar, execute manualmente como administrador")
        
        try:
            from app import app
            import waitress
            
            print("✅ Iniciando com Waitress...")
            print("🌐 Acesse: http://127.0.0.1:5000")
            
            waitress.serve(
                app,
                host='127.0.0.1',
                port=5000,
                threads=2,
                connection_limit=100
            )
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            print("💡 Execute manualmente como administrador")
    
    elif choice == "2":
        start_with_port_alternative()
    
    elif choice == "3":
        start_with_localhost_only()
    
    elif choice == "4":
        print("\n📋 Criando script batch para administrador...")
        batch_path = create_windows_batch()
        print(f"✅ Script criado: {batch_path}")
        print("💡 Execute este arquivo como administrador")
        print("💡 Clique com botão direito → Executar como administrador")
    
    elif choice == "5":
        print("👋 Saindo...")
        sys.exit(0)
    
    else:
        print("❌ Opção inválida")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("🏁 SOLUÇÃO APLICADA")
    print("=" * 70)

if __name__ == "__main__":
    main()
