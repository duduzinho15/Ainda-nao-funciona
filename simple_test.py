"""
Script de teste simples para validar as funcionalidades básicas do Garimpeiro Geek.
"""
import logging
import sqlite3
import requests
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('simple_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Testa a conexão com o banco de dados."""
    logger.info("🔍 Testando conexão com o banco de dados...")
    try:
        conn = sqlite3.connect('ofertas.db')
        cursor = conn.cursor()
        
        # Verifica se a tabela de ofertas existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ofertas';")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            logger.info("✅ Tabela 'ofertas' encontrada no banco de dados")
        else:
            logger.warning("⚠️ Tabela 'ofertas' não encontrada no banco de dados")
        
        # Conta o número de ofertas no banco de dados
        cursor.execute("SELECT COUNT(*) FROM ofertas;")
        count = cursor.fetchone()[0]
        logger.info(f"📊 Total de ofertas no banco de dados: {count}")
        
        # Mostra as ofertas mais recentes
        if count > 0:
            cursor.execute("SELECT titulo, preco, loja, data_postagem FROM ofertas ORDER BY data_postagem DESC LIMIT 3;")
            logger.info("\n📋 Últimas ofertas no banco de dados:")
            for titulo, preco, loja, data in cursor.fetchall():
                logger.info(f"   • {titulo} - {preco} ({loja}) - {data}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao acessar o banco de dados: {e}")
        return False

def test_magalu_scraper():
    """Testa o scraper do Magazine Luiza."""
    logger.info("\n🔍 Testando o scraper do Magazine Luiza...")
    
    try:
        # Importa o módulo dinamicamente
        from magalu_scraper import buscar_ofertas_magalu
        
        # Busca ofertas na primeira página
        ofertas = buscar_ofertas_magalu(paginas=1)
        
        if not ofertas:
            logger.warning("⚠️ Nenhuma oferta encontrada no Magazine Luiza")
            return False
        
        logger.info(f"✅ Encontradas {len(ofertas)} ofertas no Magazine Luiza")
        
        # Mostra detalhes das ofertas encontradas
        for i, oferta in enumerate(ofertas[:3], 1):  # Mostra apenas as 3 primeiras
            logger.info(f"\n📦 Oferta {i}:")
            logger.info(f"   Título: {oferta.get('titulo')}")
            logger.info(f"   Preço: {oferta.get('preco')}")
            logger.info(f"   URL: {oferta.get('url_produto')}")
            logger.info(f"   Loja: {oferta.get('loja')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar o scraper do Magazine Luiza: {e}")
        return False

def test_telegram_connection():
    """Testa a conexão com a API do Telegram."""
    logger.info("\n📱 Testando conexão com a API do Telegram...")
    
    try:
        # Tenta importar as configurações do Telegram
        try:
            import config
            if not hasattr(config, 'TELEGRAM_BOT_TOKEN'):
                logger.warning("⚠️ TELEGRAM_BOT_TOKEN não definido no arquivo config.py")
                return False
            
            token = config.TELEGRAM_BOT_TOKEN
            
            # Faz uma requisição para a API do Telegram
            url = f"https://api.telegram.org/bot{token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and data.get('result'):
                    bot_username = data['result'].get('username')
                    logger.info(f"✅ Conexão com o bot @{bot_username} estabelecida com sucesso!")
                    return True
                else:
                    logger.error(f"❌ Resposta inesperada da API do Telegram: {data}")
            else:
                logger.error(f"❌ Falha na conexão com a API do Telegram. Status code: {response.status_code}")
                logger.error(f"Resposta: {response.text}")
            
        except ImportError:
            logger.error("❌ Arquivo config.py não encontrado ou inválido")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar a conexão com o Telegram: {e}")
        return False

def main():
    """Função principal."""
    logger.info("🚀 Iniciando testes do Garimpeiro Geek")
    logger.info("=" * 60)
    
    # Executa os testes
    testes = [
        ("Banco de Dados", test_database_connection()),
        ("Scraper Magazine Luiza", test_magalu_scraper()),
        ("Conexão com o Telegram", test_telegram_connection())
    ]
    
    # Exibe o resumo
    logger.info("\n📊 RESUMO DOS TESTES")
    logger.info("=" * 60)
    
    todos_passaram = True
    for nome, resultado in testes:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        logger.info(f"{status} - {nome}")
        if not resultado:
            todos_passaram = False
    
    if todos_passaram:
        logger.info("\n🎉 Todos os testes foram concluídos com sucesso!")
    else:
        logger.warning("\n⚠️ Alguns testes falharam. Verifique os logs para mais detalhes.")
    
    logger.info("\n🔍 Consulte o arquivo simple_test.log para ver o relatório completo.")

if __name__ == "__main__":
    main()
