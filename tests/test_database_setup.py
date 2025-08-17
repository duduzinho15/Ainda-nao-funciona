import sqlite3
import os
import config
import database

def test_setup_database_creates_expected_columns(tmp_path):
    db_file = tmp_path / "test.db"
    # Usa banco temporário
    config.DB_NAME = str(db_file)
    assert database.setup_database() is True

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(ofertas)")
    columns = {row[1] for row in cur.fetchall()}
    # Verifica colunas essenciais do novo esquema
    for expected in {"asin", "url_fonte", "imagem_url"}:
        assert expected in columns
    conn.close()
