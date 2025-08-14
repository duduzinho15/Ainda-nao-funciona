#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para a funcionalidade de publicação manual de ofertas.

Este script testa o comando /oferta e a publicação manual de ofertas no canal do Telegram.
"""
import asyncio
import logging
import sys
import os
import traceback
from datetime import datetime

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.abspath('.'))

# Configura o logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Formato do log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Handler para console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Handler para arquivo
file_handler = logging.FileHandler('test_manual_posting.log', mode='w', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Configura o encoding do console
if sys.platform.startswith('win'):
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logger.info("=== INICIALIZANDO TESTE DE PUBLICAÇÃO MANUAL ===")
logger.info(f"Diretório de trabalho: {os.getcwd()}")
logger.info(f"Python version: {sys.version}")

# Habilita o log do asyncio
logging.getLogger('asyncio').setLevel(logging.DEBUG)

# Importa as funções a serem testadas
import config
from telegram_poster import publicar_oferta
from database import setup_database, adicionar_oferta_manual

# Dados de teste para publicação manual
OFERTA_TESTE = {
    'titulo': 'Monitor Gamer 24" 144Hz - Teste',
    'preco': 'R$ 999,99',
    'url': 'https://www.exemplo.com/produto-teste',
    'imagem_url': 'https://via.placeholder.com/300',
    'loja': 'Loja de Teste',
    'fonte': 'Teste Manual'
}

async def testar_publicacao_manual():
    """Testa a publicação manual de uma oferta."""
    logger.info("\n=== INÍCIO DO TESTE DE PUBLICAÇÃO MANUAL ===")
    
    try:
        logger.info("1. Configurando banco de dados...")
        try:
            setup_database()
            logger.info("✅ Banco de dados configurado com sucesso.")
        except Exception as e:
            logger.error(f"❌ Falha ao configurar o banco de dados: {e}")
            logger.debug(traceback.format_exc())
            return False
        
        # Formata a mensagem
        logger.info("2. Formatando mensagem de teste...")
        try:
            mensagem = (
                f"🔥 *{OFERTA_TESTE['titulo']}*\n"
                f"💵 *Preço:* {OFERTA_TESTE['preco']}\n"
                f"🏪 *Loja:* {OFERTA_TESTE['loja']}\n"
                f"📰 *Fonte:* {OFERTA_TESTE['fonte']}\n\n"
                f"🛒 [Ver oferta]({OFERTA_TESTE['url']})"
            )
            logger.debug(f"Mensagem formatada: {mensagem}")
        except Exception as e:
            logger.error(f"❌ Falha ao formatar a mensagem: {e}")
            logger.debug(traceback.format_exc())
            return False
        
        # Publica a oferta de teste
        logger.info("3. Iniciando publicação da oferta...")
        try:
            logger.debug(f"URL da imagem: {OFERTA_TESTE['imagem_url']}")
            logger.debug(f"URL afiliado: {OFERTA_TESTE['url']}")
            logger.debug(f"Chat ID: {config.TELEGRAM_CHAT_ID}")
            
            sucesso = await publicar_oferta(
                mensagem=mensagem,
                imagem_url=OFERTA_TESTE['imagem_url'],
                url_afiliado=OFERTA_TESTE['url'],
                chat_id=config.TELEGRAM_CHAT_ID
            )
            
            if sucesso:
                logger.info("✅ Publicação manual de oferta bem-sucedida!")
            else:
                logger.error("❌ A função de publicação retornou False.")
                
            return sucesso
            
        except Exception as e:
            logger.error(f"❌ Erro durante a publicação: {e}")
            logger.debug(traceback.format_exc())
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro inesperado durante o teste de publicação manual: {e}")
        logger.debug(traceback.format_exc())
        return False
    finally:
        logger.info("=== FIM DO TESTE DE PUBLICAÇÃO MANUAL ===\n")

async def testar_comando_oferta():
    """Testa o comando /oferta com argumentos simulados."""
    logger.info("\n=== INÍCIO DO TESTE DO COMANDO /OFERTA ===")
    
    try:
        logger.info("1. Importando módulos necessários...")
        try:
            from unittest.mock import AsyncMock, MagicMock, patch
            from telegram import Update, Message, Chat, User
            from telegram_poster import comando_oferta
            logger.info("✅ Módulos importados com sucesso.")
        except ImportError as e:
            logger.error(f"❌ Falha ao importar módulos: {e}")
            logger.debug(traceback.format_exc())
            return False
        
        logger.info("2. Configurando banco de dados...")
        try:
            setup_database()
            logger.info("✅ Banco de dados configurado com sucesso.")
        except Exception as e:
            logger.error(f"❌ Falha ao configurar o banco de dados: {e}")
            logger.debug(traceback.format_exc())
            return False
        
        logger.info("3. Configurando mocks...")
        try:
            # Cria mocks para o objeto Update
            update = AsyncMock(spec=Update)
            message = MagicMock(spec=Message)
            chat = MagicMock(spec=Chat)
            user = MagicMock(spec=User)
            
            # Configura os mocks
            user.id = int(config.ADMIN_USER_ID)  # ID do administrador
            chat.id = int(config.TELEGRAM_CHAT_ID)
            message.chat = chat
            message.from_user = user
            message.text = "/oferta Monitor Teste R$ 999,99 https://www.exemplo.com/produto-teste"
            message.reply_text = AsyncMock()
            update.message = message
            
            # Cria um mock para o contexto
            context = MagicMock()
            context.args = message.text.split()[1:]  # Remove o comando
            
            logger.debug(f"Mensagem de teste: {message.text}")
            logger.debug(f"Argumentos do comando: {context.args}")
            logger.info("✅ Mocks configurados com sucesso.")
            
        except Exception as e:
            logger.error(f"❌ Falha ao configurar mocks: {e}")
            logger.debug(traceback.format_exc())
            return False
        
        logger.info("4. Executando comando /oferta...")
        try:
            # Executa o comando com os mocks
            await comando_oferta(update, context)
            logger.info("✅ Comando /oferta executado com sucesso.")
            
            # Verifica se a função de resposta foi chamada
            message.reply_text.assert_awaited()
            logger.info("✅ Resposta do comando verificada com sucesso.")
            
            # Verifica se a oferta foi adicionada ao banco de dados
            import sqlite3
            conn = sqlite3.connect('ofertas.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ofertas WHERE titulo LIKE '%Monitor Teste%'")
            oferta = cursor.fetchone()
            conn.close()
            
            if oferta:
                logger.info(f"✅ Oferta encontrada no banco de dados: {oferta}")
            else:
                logger.error("❌ Oferta não encontrada no banco de dados.")
                return False
                
            return True
            
        except AssertionError as e:
            logger.error(f"❌ Falha na verificação do comando /oferta: {e}")
            logger.debug(traceback.format_exc())
            return False
        except Exception as e:
            logger.error(f"❌ Erro durante a execução do comando /oferta: {e}")
            logger.debug(traceback.format_exc())
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro inesperado durante o teste do comando /oferta: {e}")
        logger.debug(traceback.format_exc())
        return False
    finally:
        logger.info("=== FIM DO TESTE DO COMANDO /OFERTA ===\n")

async def main():
    """Função principal do script de teste."""
    logger.info("\n" + "="*80)
    logger.info("INICIANDO TESTES DE PUBLICAÇÃO MANUAL")
    logger.info("="*80 + "\n")
    
    # Verifica se as configurações necessárias estão definidas
    logger.info("🔍 Verificando configurações...")
    config_ok = True
    
    if not hasattr(config, 'TELEGRAM_BOT_TOKEN') or not config.TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN não está definido no config.py")
        config_ok = False
    
    if not hasattr(config, 'TELEGRAM_CHAT_ID') or not config.TELEGRAM_CHAT_ID:
        logger.error("❌ TELEGRAM_CHAT_ID não está definido no config.py")
        config_ok = False
    
    if not hasattr(config, 'ADMIN_USER_ID') or not config.ADMIN_USER_ID:
        logger.error("❌ ADMIN_USER_ID não está definido no config.py")
        config_ok = False
    
    if not hasattr(config, 'DB_NAME') or not config.DB_NAME:
        logger.error("❌ DB_NAME não está definido no config.py")
        config_ok = False
    
    if not config_ok:
        logger.error("\n❌ Configurações ausentes. Por favor, verifique o arquivo config.py")
        return False
    
    logger.info("✅ Todas as configurações necessárias estão definidas.\n")
    
    # Testa a publicação manual
    logger.info("🔧 TESTANDO PUBLICAÇÃO MANUAL")
    logger.info("-" * 60)
    sucesso_publicacao = await testar_publicacao_manual()
    
    # Testa o comando /oferta
    logger.info("\n🔧 TESTANDO COMANDO /OFERTA")
    logger.info("-" * 60)
    sucesso_comando = await testar_comando_oferta()
    
    # Exibe resumo
    logger.info("\n" + "="*80)
    logger.info("RESUMO DOS TESTES")
    logger.info("="*80)
    logger.info(f"Publicação manual: {'✅' if sucesso_publicacao else '❌'}")
    logger.info(f"Comando /oferta: {'✅' if sucesso_comando else '❌'}")
    
    if sucesso_publicacao and sucesso_comando:
        logger.info("\n✅ TODOS OS TESTES FORAM BEM-SUCEDIDOS!")
        return True
    else:
        logger.error("\n❌ ALGUNS TESTES FALHARAM. Verifique os logs para mais detalhes.")
        return False

def run_tests():
    """Função para executar os testes de forma assíncrona."""
    try:
        logger.info("Iniciando execução dos testes...")
        return asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ ERRO INESPERADO DURANTE A EXECUÇÃO DOS TESTES: {e}")
        logger.debug(traceback.format_exc())
        return False
    finally:
        logger.info("\n" + "="*80)
        logger.info("EXECUÇÃO DOS TESTES CONCLUÍDA")
        logger.info("="*80)

if __name__ == "__main__":
    run_tests()
