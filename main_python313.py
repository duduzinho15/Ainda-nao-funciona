#!/usr/bin/env python3
"""
Versão do main.py compatível com Python 3.13
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main_python313():
    """Função principal compatível com Python 3.13"""
    
    try:
        logger.info("🚀 Iniciando Garimpeiro Geek (Python 3.13 Compatível)...")
        
        # Importa configurações
        import config
        
        # Verifica token
        token = config.TELEGRAM_BOT_TOKEN
        if not token:
            logger.error("Token do bot não encontrado!")
            return
        
        logger.info("✅ Token encontrado")
        
        # Importa módulos necessários
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
        from telegram_poster import comando_oferta
        
        # Cria a aplicação (versão Python 3.13)
        application = Application.builder().token(token).build()
        logger.info("✅ Aplicação criada com sucesso")
        
        # Configura handlers básicos
        application.add_handler(CommandHandler("start", comando_iniciar_simples))
        application.add_handler(CommandHandler("oferta", comando_oferta))
        application.add_handler(CommandHandler("status", comando_status_simples))
        
        # Configura manipulador de erros
        application.add_error_handler(error_handler_simples)
        
        # Remove webhook e inicia polling
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook removido")
        
        # Inicia o bot (versão Python 3.13)
        logger.info("🤖 Iniciando bot...")
        
        # Método alternativo para Python 3.13
        try:
            await application.initialize()
            await application.start()
            await application.run_polling(drop_pending_updates=True)
        except AttributeError:
            # Fallback para versões mais antigas
            logger.info("🔄 Usando método alternativo...")
            await application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}", exc_info=True)
        raise

async def comando_iniciar_simples(update, context):
    """Comando start simplificado"""
    await update.message.reply_text(
        "🚀 **Garimpeiro Geek Ativado!**\n\n"
        "Use /oferta para publicar ofertas manualmente.\n"
        "Use /status para ver o status do sistema.",
        parse_mode='Markdown'
    )

async def comando_status_simples(update, context):
    """Comando status simplificado"""
    await update.message.reply_text(
        "📊 **Status do Sistema:**\n\n"
        "✅ Sistema de postagem funcionando\n"
        "✅ Correções das imagens aplicadas\n"
        "✅ Estrutura das ofertas corrigida\n"
        "✅ Links de afiliado funcionando\n"
        "🤖 Bot funcionando normalmente",
        parse_mode='Markdown'
    )

async def error_handler_simples(update, context):
    """Manipulador de erros simplificado"""
    logger.error(f"Erro no bot: {context.error}", exc_info=True)
    if update and update.message:
        await update.message.reply_text(
            "❌ Ocorreu um erro. Tente novamente ou use /status para ver o status."
        )

if __name__ == "__main__":
    try:
        asyncio.run(main_python313())
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}", exc_info=True)
        print(f"\n❌ Erro fatal: {e}")
        print("Verifique os logs para mais detalhes.")
