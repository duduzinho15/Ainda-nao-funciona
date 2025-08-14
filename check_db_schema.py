#!/usr/bin/env python3
"""
Script para verificar o esquema do banco de dados.
"""
import sqlite3
import config

def check_database_schema():
    """Verifica o esquema do banco de dados e exibe informações detalhadas."""
    try:
        print("=== VERIFICAÇÃO DO ESQUEMA DO BANCO DE DADOS ===\n")
        
        # Conecta ao banco de dados
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        # Verifica se a tabela 'ofertas' existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ofertas'")
        if not cursor.fetchone():
            print("❌ A tabela 'ofertas' não existe no banco de dados.")
            return False
        
        # Obtém informações sobre as colunas da tabela 'ofertas'
        cursor.execute("PRAGMA table_info(ofertas)")
        columns = cursor.fetchall()
        
        print("📋 Colunas na tabela 'ofertas':")
        required_columns = [
            'id', 'asin', 'url_produto', 'titulo', 'preco', 
            'preco_original', 'loja', 'fonte', 'url_fonte', 
            'imagem_url', 'data_postagem', 'data_atualizacao'
        ]
        
        missing_columns = []
        existing_columns = []
        
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            col_notnull = "NOT NULL" if col[3] else "NULL"
            col_pk = "PRIMARY KEY" if col[5] else ""
            existing_columns.append(col_name)
            print(f"- {col_name}: {col_type} {col_notnull} {col_pk}")
        
        # Verifica colunas ausentes
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            print("\n❌ Colunas ausentes na tabela 'ofertas':")
            for col in missing_columns:
                print(f"- {col}")
        else:
            print("\n✅ Todas as colunas necessárias estão presentes na tabela 'ofertas'.")
        
        # Verifica índices
        print("\n🔍 Índices na tabela 'ofertas':")
        cursor.execute("PRAGMA index_list('ofertas')")
        indexes = cursor.fetchall()
        
        if not indexes:
            print("- Nenhum índice encontrado.")
        else:
            for idx in indexes:
                idx_name = idx[1]
                idx_unique = "UNIQUE" if idx[2] else ""
                print(f"- {idx_name} {idx_unique}")
                
                # Obtém as colunas do índice
                cursor.execute(f"PRAGMA index_info('{idx_name}')")
                idx_columns = cursor.fetchall()
                for col in idx_columns:
                    print(f"  → {col[2]}")
        
        # Verifica se a tabela 'configuracoes' existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='configuracoes'")
        if not cursor.fetchone():
            print("\n❌ A tabela 'configuracoes' não existe no banco de dados.")
        else:
            print("\n✅ Tabela 'configuracoes' encontrada.")
        
        return len(missing_columns) == 0
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao verificar o esquema do banco de dados: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def recreate_database():
    """Recria o banco de dados com o esquema correto."""
    import os
    try:
        # Faz backup do banco de dados existente, se houver
        if os.path.exists(config.DB_NAME):
            backup_name = f"{config.DB_NAME}.bak"
            os.rename(config.DB_NAME, backup_name)
            print(f"ℹ️ Backup do banco de dados criado em: {backup_name}")
        
        # Reconecta para criar um novo banco de dados
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        # Cria a tabela de ofertas com o esquema correto
        cursor.execute('''
        CREATE TABLE ofertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asin TEXT,
            url_produto TEXT NOT NULL,
            titulo TEXT NOT NULL,
            preco TEXT NOT NULL,
            preco_original TEXT,
            loja TEXT NOT NULL,
            fonte TEXT NOT NULL,
            url_fonte TEXT,
            imagem_url TEXT,
            data_postagem TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(url_produto) ON CONFLICT IGNORE,
            UNIQUE(asin) ON CONFLICT IGNORE
        )
        ''')
        
        # Cria índices
        cursor.execute('CREATE INDEX idx_url_produto ON ofertas(url_produto)')
        cursor.execute('CREATE INDEX idx_asin ON ofertas(asin)')
        cursor.execute('CREATE INDEX idx_loja ON ofertas(loja)')
        cursor.execute('CREATE INDEX idx_fonte ON ofertas(fonte)')
        
        # Cria a tabela de configurações
        cursor.execute('''
        CREATE TABLE configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT,
            descricao TEXT,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Insere configurações padrão
        cursor.execute('''
        INSERT INTO configuracoes (chave, valor, descricao)
        VALUES (?, ?, ?)
        ''', ('ultima_atualizacao', '2000-01-01 00:00:00', 'Data da última atualização de ofertas'))
        
        conn.commit()
        print("\n✅ Banco de dados recriado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao recriar o banco de dados: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Verificando o esquema do banco de dados...\n")
    
    # Verifica o esquema atual
    schema_ok = check_database_schema()
    
    if not schema_ok:
        print("\n❌ O esquema do banco de dados não está correto.")
        resposta = input("\nDeseja recriar o banco de dados? (s/n): ")
        if resposta.lower() == 's':
            if recreate_database():
                print("\n✅ Banco de dados recriado com sucesso!")
                print("\nVerificando o novo esquema...\n")
                check_database_schema()
            else:
                print("\n❌ Falha ao recriar o banco de dados.")
        else:
            print("\nOperação cancelada pelo usuário.")
    else:
        print("\n✅ O esquema do banco de dados está correto!")
