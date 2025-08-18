#!/usr/bin/env python3
"""
Script simples para iniciar o Dashboard
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    print("🚀 Iniciando Dashboard Garimpeiro Geek...")
    print("=" * 50)

    try:
        # Tenta importar o app
        from app import app

        print("✅ App importado com sucesso")

        # Verifica se o banco está acessível
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

        print("\n🔧 Escolha o método:")
        print("1. Flask (desenvolvimento)")
        print("2. Waitress (recomendado para Windows)")
        print("3. Gunicorn")

        choice = input("\nEscolha (1-3): ").strip()

        if choice == "1":
            print("🚀 Iniciando Flask...")
            app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
        elif choice == "2":
            print("🚀 Iniciando Waitress...")
            import waitress

            waitress.serve(app, host="127.0.0.1", port=5000, threads=2)
        elif choice == "3":
            print("🚀 Iniciando Gunicorn...")
            import subprocess

            subprocess.run(
                ["gunicorn", "--bind", "127.0.0.1:5000", "app:app"],
                cwd=os.path.dirname(__file__),
            )
        else:
            print("❌ Opção inválida")

    except ImportError as e:
        print(f"❌ Erro ao importar: {e}")
        print("💡 Execute: pip install flask waitress gunicorn")
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    main()
