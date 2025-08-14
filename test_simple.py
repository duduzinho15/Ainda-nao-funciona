#!/usr/bin/env python3
"""
Script de teste simplificado para verificar a funcionalidade básica.
"""
import logging
import sys

# Configura o logging básico
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Testa a conexão com o banco de dados."""
    try:
        logger.info("Testando conexão com o banco de dados...")
        import sqlite3
        conn = sqlite3.connect('ofertas.db')
        cursor = conn.cursor()
        
        # Verifica se a tabela de ofertas existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ofertas'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            logger.info("✅ Tabela 'ofertas' encontrada no banco de dados.")
            
            # Conta o número de ofertas no banco
            cursor.execute("SELECT COUNT(*) FROM ofertas")
            count = cursor.fetchone()[0]
            logger.info(f"Total de ofertas no banco: {count}")
            
        else:
            logger.error("❌ Tabela 'ofertas' não encontrada no banco de dados.")
            
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar o banco de dados: {e}", exc_info=True)
        return False

def test_telegram_config():
    """Verifica as configurações do Telegram."""
    try:
        logger.info("Verificando configurações do Telegram...")
        import config
        
        config_valid = True
        
        if not hasattr(config, 'TELEGRAM_BOT_TOKEN') or not config.TELEGRAM_BOT_TOKEN:
            logger.error("❌ TELEGRAM_BOT_TOKEN não configurado.")
            config_valid = False
        else:
            logger.info("✅ TELEGRAM_BOT_TOKEN configurado.")
            
        if not hasattr(config, 'TELEGRAM_CHAT_ID') or not config.TELEGRAM_CHAT_ID:
            logger.error("❌ TELEGRAM_CHAT_ID não configurado.")
            config_valid = False
        else:
            logger.info(f"✅ TELEGRAM_CHAT_ID configurado: {config.TELEGRAM_CHAT_ID}")
            
        if not hasattr(config, 'ADMIN_USER_ID') or not config.ADMIN_USER_ID:
            logger.error("❌ ADMIN_USER_ID não configurado.")
            config_valid = False
        else:
            logger.info(f"✅ ADMIN_USER_ID configurado: {config.ADMIN_USER_ID}")
            
        return config_valid
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar configurações: {e}", exc_info=True)
        return False

def main():
    """Função principal do script de teste."""
    logger.info("=== INÍCIO DOS TESTES SIMPLIFICADOS ===")
    
    # Testa a conexão com o banco de dados
    logger.info("\n=== TESTE 1: Conexão com o banco de dados ===")
    db_ok = test_database_connection()
    
    # Testa as configurações do Telegram
    logger.info("\n=== TESTE 2: Configurações do Telegram ===")
    telegram_ok = test_telegram_config()
    
    # Exibe o resumo dos testes
    logger.info("\n=== RESUMO DOS TESTES ===")
    logger.info(f"Banco de dados: {'✅' if db_ok else '❌'}")
    logger.info(f"Configurações do Telegram: {'✅' if telegram_ok else '❌'}")
    
    if db_ok and telegram_ok:
        logger.info("\n✅ TESTES BEM-SUCEDIDOS!")
        return True
    else:
        logger.error("\n❌ ALGUNS TESTES FALHARAM. Verifique as mensagens acima.")
        return False

if __name__ == "__main__":
    main()
