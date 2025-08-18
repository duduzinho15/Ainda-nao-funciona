#!/usr/bin/env python3
"""
Script de migração para adicionar coluna offer_hash ao banco de dados existente

Este script:
1. Verifica se a coluna offer_hash já existe
2. Adiciona a coluna se não existir
3. Gera hashes para ofertas existentes
4. Cria o índice único
"""

import sqlite3
import os
import sys
import logging

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_NAME
from utils.offer_hash import offer_hash

# Configuração de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    """
    Verifica se uma coluna existe em uma tabela

    Args:
        cursor: Cursor do banco de dados
        table: Nome da tabela
        column: Nome da coluna

    Returns:
        True se a coluna existe, False caso contrário
    """
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()

        for col in columns:
            if col[1] == column:
                return True

        return False

    except Exception as e:
        logger.error(f"Erro ao verificar coluna {column} na tabela {table}: {e}")
        return False


def add_offer_hash_column(cursor: sqlite3.Cursor):
    """
    Adiciona a coluna offer_hash à tabela ofertas

    Args:
        cursor: Cursor do banco de dados
    """
    try:
        # Adiciona a coluna offer_hash
        cursor.execute("""
            ALTER TABLE ofertas 
            ADD COLUMN offer_hash TEXT
        """)

        logger.info("✅ Coluna offer_hash adicionada com sucesso")

    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            logger.info("ℹ️ Coluna offer_hash já existe")
        else:
            raise e
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar coluna offer_hash: {e}")
        raise e


def create_offer_hash_index(cursor: sqlite3.Cursor):
    """
    Cria o índice único para offer_hash

    Args:
        cursor: Cursor do banco de dados
    """
    try:
        # Cria o índice único
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_ofertas_offer_hash 
            ON ofertas(offer_hash)
        """)

        logger.info("✅ Índice único idx_ofertas_offer_hash criado com sucesso")

    except Exception as e:
        logger.error(f"❌ Erro ao criar índice: {e}")
        raise e


def generate_hashes_for_existing_offers(cursor: sqlite3.Cursor):
    """
    Gera hashes para ofertas existentes que não possuem offer_hash

    Args:
        cursor: Cursor do banco de dados
    """
    try:
        # Busca ofertas sem offer_hash
        cursor.execute("""
            SELECT id, asin, loja, titulo, preco, preco_original, 
                   url_produto, imagem_url, fonte
            FROM ofertas 
            WHERE offer_hash IS NULL OR offer_hash = ''
        """)

        offers_without_hash = cursor.fetchall()

        if not offers_without_hash:
            logger.info("ℹ️ Todas as ofertas já possuem offer_hash")
            return 0

        logger.info(
            f"🔄 Gerando hashes para {len(offers_without_hash)} ofertas existentes..."
        )

        updated_count = 0

        for offer in offers_without_hash:
            try:
                # Constrói dicionário da oferta
                offer_dict = {
                    "id_produto": offer[1] or str(offer[0]),  # ASIN ou ID como fallback
                    "loja": offer[2],
                    "titulo": offer[3],
                    "preco": offer[4],
                    "preco_original": offer[5],
                    "url_produto": offer[6],
                    "url_imagem": offer[7],
                    "fonte": offer[8],
                }

                # Gera hash
                hash_value = offer_hash(offer_dict)

                if hash_value:
                    # Atualiza a oferta com o hash
                    cursor.execute(
                        """
                        UPDATE ofertas 
                        SET offer_hash = ? 
                        WHERE id = ?
                    """,
                        (hash_value, offer[0]),
                    )

                    updated_count += 1

                    if updated_count % 100 == 0:
                        logger.info(f"🔄 {updated_count} ofertas processadas...")

                else:
                    logger.warning(
                        f"⚠️ Não foi possível gerar hash para oferta: {offer[2]}"
                    )

            except Exception as e:
                logger.error(f"❌ Erro ao processar oferta {offer[2]}: {e}")
                continue

        logger.info(f"✅ {updated_count} ofertas atualizadas com offer_hash")
        return updated_count

    except Exception as e:
        logger.error(f"❌ Erro ao gerar hashes para ofertas existentes: {e}")
        raise e


def validate_migration(cursor: sqlite3.Cursor):
    """
    Valida a migração verificando se tudo está funcionando

    Args:
        cursor: Cursor do banco de dados
    """
    try:
        # Verifica se a coluna existe
        if not check_column_exists(cursor, "ofertas", "offer_hash"):
            logger.error("❌ Validação falhou: coluna offer_hash não existe")
            return False

        # Verifica se o índice existe
        cursor.execute("PRAGMA index_list(ofertas)")
        indexes = cursor.fetchall()

        index_names = [index[1] for index in indexes]
        if "idx_ofertas_offer_hash" not in index_names:
            logger.error(
                "❌ Validação falhou: índice idx_ofertas_offer_hash não existe"
            )
            return False

        # Verifica se todas as ofertas têm hash
        cursor.execute("""
            SELECT COUNT(*) FROM ofertas WHERE offer_hash IS NULL OR offer_hash = ''
        """)

        offers_without_hash = cursor.fetchone()[0]

        if offers_without_hash > 0:
            logger.warning(
                f"⚠️ {offers_without_hash} ofertas ainda não possuem offer_hash"
            )
        else:
            logger.info("✅ Todas as ofertas possuem offer_hash")

        # Verifica se há hashes duplicados
        cursor.execute("""
            SELECT offer_hash, COUNT(*) as count
            FROM ofertas 
            WHERE offer_hash IS NOT NULL AND offer_hash != ''
            GROUP BY offer_hash 
            HAVING COUNT(*) > 1
        """)

        duplicate_hashes = cursor.fetchall()

        if duplicate_hashes:
            logger.warning(f"⚠️ {len(duplicate_hashes)} hashes duplicados encontrados")
            for hash_val, count in duplicate_hashes[:5]:  # Mostra apenas os primeiros 5
                logger.warning(f"   Hash {hash_val[:16]}... aparece {count} vezes")
        else:
            logger.info("✅ Nenhum hash duplicado encontrado")

        return True

    except Exception as e:
        logger.error(f"❌ Erro durante validação: {e}")
        return False


def main():
    """
    Função principal de migração
    """
    logger.info("🚀 INICIANDO MIGRAÇÃO DO BANCO DE DADOS")
    logger.info("=" * 50)

    # Verifica se o banco existe
    if not os.path.exists(DB_NAME):
        logger.error(f"❌ Banco de dados {DB_NAME} não encontrado")
        return False

    try:
        # Conecta ao banco
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        logger.info(f"✅ Conectado ao banco {DB_NAME}")

        # 1. Verifica se a coluna já existe
        if check_column_exists(cursor, "ofertas", "offer_hash"):
            logger.info("ℹ️ Coluna offer_hash já existe")
        else:
            logger.info("🔄 Adicionando coluna offer_hash...")
            add_offer_hash_column(cursor)

        # 2. Cria o índice único
        logger.info("🔄 Criando índice único...")
        create_offer_hash_index(cursor)

        # 3. Gera hashes para ofertas existentes
        logger.info("🔄 Processando ofertas existentes...")
        updated_count = generate_hashes_for_existing_offers(cursor)

        # 4. Valida a migração
        logger.info("🔄 Validando migração...")
        if validate_migration(cursor):
            logger.info("✅ Migração validada com sucesso!")
        else:
            logger.error("❌ Falha na validação da migração")
            return False

        # 5. Commit das alterações
        conn.commit()
        logger.info("✅ Alterações commitadas com sucesso")

        # 6. Estatísticas finais
        cursor.execute("SELECT COUNT(*) FROM ofertas")
        total_offers = cursor.fetchone()[0]

        cursor.execute(
            'SELECT COUNT(*) FROM ofertas WHERE offer_hash IS NOT NULL AND offer_hash != ""'
        )
        offers_with_hash = cursor.fetchone()[0]

        logger.info("📊 ESTATÍSTICAS FINAIS:")
        logger.info(f"   Total de ofertas: {total_offers}")
        logger.info(f"   Ofertas com hash: {offers_with_hash}")
        logger.info(f"   Ofertas sem hash: {total_offers - offers_with_hash}")

        if updated_count > 0:
            logger.info(f"   Ofertas atualizadas nesta migração: {updated_count}")

        logger.info("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        return True

    except Exception as e:
        logger.error(f"❌ ERRO DURANTE A MIGRAÇÃO: {e}")
        logger.exception("Erro detalhado:")
        return False

    finally:
        if "conn" in locals():
            conn.close()
            logger.info("🔌 Conexão com banco fechada")


if __name__ == "__main__":
    # Executa a migração
    success = main()

    if success:
        print("\n✅ Migração concluída com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Migração falhou. Verifique os logs acima.")
        sys.exit(1)
