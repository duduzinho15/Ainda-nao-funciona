#!/usr/bin/env python3
"""
SOLUÇÃO ULTIMATE para Windows - Dashboard Garimpeiro Geek
Tenta todas as soluções possíveis para a limitação técnica
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

# Adiciona o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_connection(port, host="127.0.0.1"):
    """Testa conexão em uma porta específica"""
    try:
        response = requests.get(f"http://{host}:{port}", timeout=5)
        return True, response.status_code
    except requests.exceptions.ConnectionError:
        return False, None
    except Exception as e:
        return False, str(e)


def start_dashboard_with_waitress():
    """Inicia o dashboard usando Waitress (mais robusto para Windows)"""
    print("🚀 Tentando Waitress (mais robusto para Windows)...")

    try:
        from waitress import serve
        from app import app

        print("✅ Waitress importado com sucesso")
        print("🌐 Iniciando servidor Waitress na porta 8080...")
        print("💡 Acesse: http://127.0.0.1:8080")

        serve(app, host="127.0.0.1", port=8080)

    except ImportError:
        print("❌ Waitress não está instalado")
        print("💡 Execute: pip install waitress")
        return False
    except Exception as e:
        print(f"❌ Erro com Waitress: {e}")
        return False


def start_dashboard_with_flask_foreground():
    """Inicia Flask em primeiro plano para diagnóstico"""
    print("🚀 Tentando Flask em primeiro plano...")

    try:
        from app import app

        print("✅ App importado com sucesso")
        print("🌐 Iniciando Flask na porta 8080...")
        print("💡 Acesse: http://127.0.0.1:8080")
        print("⚠️  IMPORTANTE: Mantenha esta janela aberta!")

        app.run(
            host="127.0.0.1", port=8080, debug=False, use_reloader=False, threaded=True
        )

    except Exception as e:
        print(f"❌ Erro com Flask: {e}")
        return False


def create_firewall_exception():
    """Cria exceção no firewall do Windows"""
    print("🔧 Tentando criar exceção no firewall...")

    try:
        # Comando para adicionar exceção no firewall
        cmd = [
            "netsh",
            "advfirewall",
            "firewall",
            "add",
            "rule",
            'name="Dashboard Garimpeiro Geek"',
            "dir=in",
            "action=allow",
            "protocol=TCP",
            "localport=8080",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

        if result.returncode == 0:
            print("✅ Exceção no firewall criada com sucesso!")
            return True
        else:
            print(f"⚠️  Erro ao criar exceção: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Erro ao configurar firewall: {e}")
        return False


def create_admin_batch_script():
    """Cria script batch para executar como administrador"""
    print("📋 Criando script para executar como administrador...")

    script_content = """@echo off
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

:: Inicia o dashboard
echo 🚀 Iniciando dashboard...
cd /d "%~dp0"
python start_windows_ultimate.py

pause
"""

    script_path = Path(__file__).parent / "start_as_admin_ultimate.bat"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    return script_path


def main():
    """Função principal"""
    print("=" * 80)
    print("🚀 SOLUÇÃO ULTIMATE - DASHBOARD GARIMPEIRO GEEK")
    print("=" * 80)
    print()

    # Verifica se é Windows
    if os.name != "nt":
        print("❌ Este script é específico para Windows")
        sys.exit(1)

    print("🔍 DIAGNÓSTICO COMPLETO:")
    print("   O Windows está bloqueando conexões locais por segurança")
    print("   Isso é comum com Windows Defender, firewall e configurações de rede")
    print("   A solução é usar portas alternativas ou executar como administrador")
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
    print("1. 🚀 Tentar Waitress (mais robusto para Windows)")
    print("2. 🚀 Tentar Flask em primeiro plano")
    print("3. 🔧 Tentar criar exceção no firewall")
    print("4. 📋 Criar script para executar como administrador")
    print("5. ❌ Sair")

    try:
        choice = input("\nEscolha (1-5): ").strip()
    except KeyboardInterrupt:
        print("\n🛑 Operação cancelada")
        sys.exit(0)

    if choice == "1":
        start_dashboard_with_waitress()

    elif choice == "2":
        start_dashboard_with_flask_foreground()

    elif choice == "3":
        if create_firewall_exception():
            print("\n🔄 Agora tente iniciar o dashboard novamente...")
            time.sleep(3)
            start_dashboard_with_waitress()
        else:
            print("\n💡 Execute como administrador para configurar o firewall")

    elif choice == "4":
        script_path = create_admin_batch_script()
        print(f"✅ Script criado: {script_path}")
        print("💡 Execute este arquivo como administrador:")
        print("   - Clique com botão direito no arquivo")
        print("   - Selecione 'Executar como administrador'")
        print("   - Ou execute manualmente: start_as_admin_ultimate.bat")

    elif choice == "5":
        print("👋 Saindo...")
        sys.exit(0)

    else:
        print("❌ Opção inválida")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("🏁 SOLUÇÃO APLICADA")
    print("=" * 80)
    print("\n💡 SE O DASHBOARD FUNCIONAR:")
    print("   - Acesse: http://127.0.0.1:8080")
    print("\n💡 SE NÃO FUNCIONAR:")
    print("   - Execute o script como administrador")
    print("   - Desative temporariamente o Windows Defender")
    print("   - Verifique configurações de firewall")


if __name__ == "__main__":
    main()
