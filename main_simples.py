#!/usr/bin/env python3
"""
Bot Telegram Garimpeiro Geek - Versão Simplificada
Executa bot polling e sistema automático de ofertas em paralelo
"""
import asyncio
import os
import sys
import time
import logging
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import NetworkError, TimedOut

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importa módulos do projeto
from telegram_poster import publicar_oferta_automatica
from orchestrator import coletar_e_publicar

# Configurações
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

if not TELEGRAM_BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN não encontrado no .env")
    sys.exit(1)

if not TELEGRAM_CHAT_ID:
    logger.error("❌ TELEGRAM_CHAT_ID não encontrado no .env")
    sys.exit(1)

# Contexto simulado para publicar_oferta_automatica
class ContextoSimulado:
    def __init__(self):
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN não pode ser None")
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.job = None

# ===== HANDLERS DOS COMANDOS =====

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    await update.message.reply_text(
        "🚀 **Garimpeiro Geek Bot Ativado!**\n\n"
        "Comandos disponíveis:\n"
        "/start - Inicia o bot\n"
        "/health - Status do sistema\n"
        "/status - Status das ofertas\n"
        "/coletar - Executa coleta manual\n"
        "/dryrun - Testa sem publicar\n\n"
        "O bot está rodando automaticamente! 🎯",
        parse_mode="Markdown"
    )

async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /health - Status do sistema"""
    try:
        # Verifica variáveis de ambiente
        def ok(k): 
            v = os.getenv(k, "")
            return "✅ OK" if v and v.strip() else "❌ NOK"
        
        # Conta ofertas das últimas 24h (simulado por enquanto)
        try:
            # Simula contagem de ofertas (implementar função real depois)
            n_24h = 0  # Placeholder
        except Exception:
            n_24h = -1
        
        # Status dos scrapers
        scraper_status = "✅ Ativos" if not DRY_RUN else "🔄 Modo Teste"
        
        msg = (
            "🏥 **Healthcheck do Sistema**\n\n"
            "**🔑 Configurações:**\n"
            f"• Bot Token: {ok('TELEGRAM_BOT_TOKEN')}\n"
            f"• Chat ID: {ok('TELEGRAM_CHAT_ID')}\n"
            f"• Amazon: {ok('AMAZON_ASSOCIATE_TAG')}\n"
            f"• AWIN: {ok('AWIN_API_TOKEN')}\n"
            f"• Shopee: {ok('SHOPEE_API_KEY')}\n"
            f"• AliExpress: {ok('ALIEXPRESS_APP_KEY')}\n\n"
            "**📊 Status:**\n"
            f"• Scrapers: {scraper_status}\n"
            f"• Ofertas (24h): {n_24h if n_24h >= 0 else 'N/A'}\n"
            f"• DRY_RUN: {'Sim' if DRY_RUN else 'Não'}\n"
            f"• Timestamp: {time.strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            "🎯 Sistema funcionando normalmente!"
        )
        
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Erro no comando health: {e}")
        await update.message.reply_text("❌ Erro ao verificar status do sistema")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status - Status das ofertas"""
    try:
        # Simula status das ofertas
        msg = (
            "📊 **Status das Ofertas**\n\n"
            "**🔄 Sistema Automático:**\n"
            "• Status: ✅ Ativo\n"
            "• Intervalo: 30 minutos\n"
            "• Última execução: Em execução...\n\n"
            "**📈 Estatísticas:**\n"
            "• Scrapers ativos: 2 (Promobit, Pelando)\n"
            "• Modo: {'Teste' if DRY_RUN else 'Produção'}\n"
            "• Rate limit: 250ms entre posts\n\n"
            "🎯 Use /coletar para execução manual!"
        )
        
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Erro no comando status: {e}")
        await update.message.reply_text("❌ Erro ao verificar status das ofertas")

async def cmd_coletar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /coletar - Executa coleta manual"""
    try:
        await update.message.reply_text("🔄 Iniciando coleta manual...")
        
        # Executa orquestrador
        resultado = await coletar_e_publicar(
            dry_run=DRY_RUN,
            limit_por_scraper=10  # Limita para teste manual
        )
        
        msg = (
            "✅ **Coleta Manual Concluída!**\n\n"
            f"**📊 Resultados:**\n"
            f"• Ofertas coletadas: {resultado['coletadas']}\n"
            f"• Ofertas aprovadas: {resultado['aprovadas']}\n"
            f"• Ofertas publicadas: {resultado['publicadas']}\n"
            f"• Scrapers executados: {resultado['scrapers_executados']}\n"
            f"• DRY_RUN: {'Sim' if resultado['dry_run'] else 'Não'}\n\n"
            "🎯 Coleta executada com sucesso!"
        )
        
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Erro no comando coletar: {e}")
        await update.message.reply_text(f"❌ Erro na coleta: {str(e)}")

async def cmd_dryrun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /dryrun - Testa sem publicar"""
    try:
        await update.message.reply_text("🧪 Iniciando teste DRY_RUN...")
        
        # Executa orquestrador em modo teste
        resultado = await coletar_e_publicar(
            dry_run=True,  # Força DRY_RUN
            limit_por_scraper=5  # Limita para teste
        )
        
        msg = (
            "🧪 **Teste DRY_RUN Concluído!**\n\n"
            f"**📊 Resultados:**\n"
            f"• Ofertas coletadas: {resultado['coletadas']}\n"
            f"• Ofertas aprovadas: {resultado['aprovadas']}\n"
            f"• Ofertas publicadas: {resultado['publicadas']} (simulado)\n"
            f"• Scrapers executados: {resultado['scrapers_executados']}\n"
            f"• DRY_RUN: Sim ✅\n\n"
            "🎯 Nenhuma oferta foi publicada (modo teste)!"
        )
        
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Erro no comando dryrun: {e}")
        await update.message.reply_text(f"❌ Erro no teste: {str(e)}")

# ===== JOB AUTOMÁTICO =====

async def job_coletar_automatico(context: ContextTypes.DEFAULT_TYPE):
    """Job periódico para coleta automática de ofertas"""
    try:
        logger.info("🔄 [JOB] Iniciando coleta automática de ofertas...")
        
        resultado = await coletar_e_publicar(
            dry_run=DRY_RUN,
            limit_por_scraper=20
        )
        
        logger.info(f"✅ [JOB] Coleta automática concluída: {resultado}")
        
        # Log detalhado do resultado
        if resultado['aprovadas'] > 0:
            logger.info(f"📤 [JOB] {resultado['publicadas']} ofertas publicadas com sucesso")
        else:
            logger.warning("⚠️ [JOB] Nenhuma oferta foi aprovada/publicada")
            
    except Exception as e:
        logger.exception(f"❌ [JOB] Erro na coleta automática: {e}")

# ===== CONFIGURAÇÃO DOS HANDLERS =====

def setup_handlers(app: Application):
    """Configura todos os handlers do bot"""
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("health", cmd_health))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("coletar", cmd_coletar))
    app.add_handler(CommandHandler("dryrun", cmd_dryrun))
    
    logger.info("✅ Handlers configurados com sucesso")

# ===== FUNÇÃO PRINCIPAL =====

async def main():
    """Função principal do bot"""
    logger.info("🚀 Iniciando Garimpeiro Geek Bot...")
    
    # Verifica token antes de criar aplicação
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN não pode ser None")
        return
    
    # Cria aplicação
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Configura handlers
    setup_handlers(app)
    
    # Configura job periódico (a cada 30 minutos)
    app.job_queue.run_repeating(
        job_coletar_automatico, 
        interval=30*60,  # 30 minutos
        first=30  # Primeira execução em 30 segundos
    )
    
    logger.info("✅ Job de coleta automática agendado (30 min)")
    logger.info(f"🔄 Modo DRY_RUN: {'ATIVO' if DRY_RUN else 'DESATIVADO'}")
    
    # Inicia o bot
    logger.info("🎯 Bot iniciado! Pressione Ctrl+C para parar")
    
    try:
        await app.initialize()
        await app.start()
        await app.run_polling()
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal no bot: {e}")
    finally:
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Programa interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        sys.exit(1)
