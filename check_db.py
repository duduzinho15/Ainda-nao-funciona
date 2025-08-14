#!/usr/bin/env python3
"""
Script para verificar o conteúdo do banco de dados
"""
import sqlite3
import os

def verificar_banco():
    """Verifica o conteúdo do banco de dados."""
    db_name = 'ofertas.db'
    
    if not os.path.exists(db_name):
        print(f"❌ Banco de dados {db_name} não encontrado")
        return
    
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Lista todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tabelas encontradas: {tabelas}")
        
        # Verifica se a tabela ofertas existe
        if 'ofertas' in tabelas:
            # Mostra a estrutura da tabela
            cursor.execute("PRAGMA table_info(ofertas)")
            colunas = cursor.fetchall()
            print(f"\n🏗️ Estrutura da tabela 'ofertas':")
            for col in colunas:
                print(f"   - {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")
            
            # Conta total de ofertas
            cursor.execute('SELECT COUNT(*) FROM ofertas')
            total_ofertas = cursor.fetchone()[0]
            print(f"\n📊 Total de ofertas: {total_ofertas}")
            
            if total_ofertas > 0:
                # Mostra algumas ofertas de exemplo
                cursor.execute('SELECT * FROM ofertas LIMIT 3')
                colunas_nomes = [desc[0] for desc in cursor.description]
                print(f"\n🔍 Colunas disponíveis: {colunas_nomes}")
                
                print("\n📋 Primeiras 3 ofertas (dados brutos):")
                for i, row in enumerate(cursor.fetchall(), 1):
                    print(f"   {i}. {dict(zip(colunas_nomes, row))}")
            else:
                print("📭 Nenhuma oferta encontrada na tabela")
        else:
            print("❌ Tabela 'ofertas' não encontrada")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")

if __name__ == "__main__":
    verificar_banco()
