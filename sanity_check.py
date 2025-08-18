#!/usr/bin/env python3
"""
🧪 SANITY CHECK - GARIMPEIRO GEEK
Script para validar sistema antes da produção
"""

import os
import sqlite3
import subprocess
import sys


def main():
    print("🧪 SANITY CHECK - GARIMPEIRO GEEK")
    print("=" * 50)

    # Configura DRY_RUN
    os.environ["DRY_RUN"] = "1"
    print("✅ DRY_RUN ativado (não vai postar)")

    # Executa testes de scrapers
    print("\n🔄 Executando testes de scrapers...")
    try:
        result = subprocess.run(
            [sys.executable, "orchestrator.py", "--dry-run", "--limit", "5"],
            capture_output=True,
            text=True,
            check=True,
        )
        print("✅ Testes de scrapers executados com sucesso")
        print(f"📊 Saída: {result.stdout[-200:]}...")  # Últimas 200 chars
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro nos testes: {e}")
        print(f"📄 Stderr: {e.stderr}")

    # Verifica duplicatas no DB
    print("\n🔍 Verificando duplicatas no banco...")
    try:
        conn = sqlite3.connect("ofertas.db")
        cursor = conn.cursor()

        # Verifica se a coluna offer_hash existe
        cursor.execute("PRAGMA table_info(ofertas)")
        columns = [col[1] for col in cursor.fetchall()]

        if "offer_hash" not in columns:
            print("❌ Coluna offer_hash não existe - execute migrate_database.py")
        else:
            # Verifica duplicatas
            cursor.execute("""
                SELECT offer_hash, COUNT(*) c 
                FROM ofertas 
                WHERE offer_hash IS NOT NULL
                GROUP BY offer_hash 
                HAVING c > 1
            """)
            dups = cursor.fetchall()

            if dups:
                print(f"❌ {len(dups)} hashes duplicados encontrados!")
                for h, c in dups:
                    print(f"  Hash: {h[:16]}... - {c} ocorrências")
            else:
                print("✅ Nenhuma duplicata encontrada")

            # Estatísticas
            cursor.execute("SELECT COUNT(*) FROM ofertas")
            total = cursor.fetchone()[0]
            print(f"📊 Total de ofertas no banco: {total}")

        conn.close()

    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")

    print("\n🧪 Sanity check concluído!")


if __name__ == "__main__":
    main()
