"""
Migration script to add the 'asin' column to the 'ofertas' table.
This script is idempotent and can be safely run multiple times.
"""
import sqlite3
import config

def run_migration():
    """
    Executa a migração para adicionar a coluna 'asin' à tabela 'ofertas'.
    
    Returns:
        bool: True se a migração foi bem-sucedida, False caso contrário
    """
    print("\n🔧 Iniciando migração: Adicionando coluna 'asin' à tabela 'ofertas'...")
    
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()
        
        # Verifica se a coluna já existe
        cursor.execute("PRAGMA table_info(ofertas)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'asin' in columns:
            print("✅ A coluna 'asin' já existe na tabela 'ofertas'.")
            return True
            
        # Adiciona a coluna 'asin' à tabela 'ofertas'
        cursor.execute('''
        ALTER TABLE ofertas
        ADD COLUMN asin TEXT;
        ''')
        
        # Cria o índice na coluna 'asin' se não existir
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_asin ON ofertas(asin);
        ''')
        
        conn.commit()
        print("✅ Migração concluída com sucesso!")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro durante a migração: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_migration()
