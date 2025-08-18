#!/usr/bin/env python3
"""
Script para recriar o banco de dados com o esquema correto.
"""

import sqlite3
import os
import config


def recreate_database():
    """Recria o banco de dados com o esquema correto."""
    try:
        # Remove o arquivo do banco de dados existente, se houver
        if os.path.exists(config.DB_NAME):
            try:
                os.rename(config.DB_NAME, f"{config.DB_NAME}.bak")
                print(f"ℹ️ Backup do banco de dados criado em: {config.DB_NAME}.bak")
            except Exception as e:
                print(f"⚠️ Não foi possível fazer backup do banco de dados: {e}")
                print("ℹ️ Tentando remover o arquivo existente...")
                try:
                    os.remove(config.DB_NAME)
                except Exception as e:
                    print(f"❌ Falha ao remover o arquivo existente: {e}")
                    return False

        print("\n🔄 Criando novo banco de dados...")

        # Conecta ao banco de dados (cria um novo arquivo)
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()

        # Cria a tabela de ofertas com o esquema correto
        print("📋 Criando tabela 'ofertas'...")
        cursor.execute("""
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
        """)

        # Cria índices
        print("🔍 Criando índices...")
        cursor.execute("CREATE INDEX idx_url_produto ON ofertas(url_produto)")
        cursor.execute("CREATE INDEX idx_asin ON ofertas(asin)")
        cursor.execute("CREATE INDEX idx_loja ON ofertas(loja)")
        cursor.execute("CREATE INDEX idx_fonte ON ofertas(fonte)")

        # Cria a tabela de configurações
        print("⚙️ Criando tabela 'configuracoes'...")
        cursor.execute("""
        CREATE TABLE configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT,
            descricao TEXT,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Insere configurações padrão
        print("📝 Inserindo configurações iniciais...")
        cursor.execute(
            """
        INSERT INTO configuracoes (chave, valor, descricao)
        VALUES (?, ?, ?)
        """,
            (
                "ultima_atualizacao",
                "2000-01-01 00:00:00",
                "Data da última atualização de ofertas",
            ),
        )

        conn.commit()
        print("\n✅ Banco de dados criado com sucesso!")

        # Verifica as tabelas criadas
        print("\n📊 Verificando o esquema criado...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("\nTabelas no banco de dados:")
        for table in tables:
            print(f"- {table[0]}")

            # Mostra as colunas de cada tabela
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            print(f"  Colunas: {', '.join([col[1] for col in columns])}")

        return True

    except Exception as e:
        print(f"\n❌ Erro ao criar o banco de dados: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    print("=== RECRIAÇÃO DO BANCO DE DADOS ===")
    print("Este script irá recriar o banco de dados com o esquema correto.\n")

    if os.path.exists(config.DB_NAME):
        print(f"⚠️  ATENÇÃO: O arquivo {config.DB_NAME} já existe.")
        resposta = input("Deseja continuar? Um backup será criado. (s/n): ")
        if resposta.lower() != "s":
            print("Operação cancelada pelo usuário.")
            exit(0)

    if recreate_database():
        print("\n✅ Banco de dados recriado com sucesso!")
        print(f"Local: {os.path.abspath(config.DB_NAME)}")
    else:
        print("\n❌ Falha ao recriar o banco de dados.")
