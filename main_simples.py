#!/usr/bin/env python3
"""
Versão simples do main.py que funciona sem Application.builder()
E INCLUI o sistema automático de verificação de ofertas
"""

import asyncio
import logging
import os
import sys
import aiohttp
from datetime import datetime, time, timedelta

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Classe para contexto simulado
class ContextoSimulado:
    def __init__(self, bot):
        self.bot = bot

async def main_simples():
    """Função principal simplificada com sistema automático"""
    
    try:
        logger.info("🚀 Iniciando Garimpeiro Geek (Versão Simples + Sistema Automático)...")
        
        # Importa configurações
        import config
        
        # Verifica token
        token = config.TELEGRAM_BOT_TOKEN
        if not token:
            logger.error("Token do bot não encontrado!")
            return
        
        logger.info("✅ Token encontrado")
        
        # Importa módulos necessários
        from telegram import Bot
        from telegram_poster import comando_oferta
        
        # Cria o bot diretamente (sem Application.builder())
        bot = Bot(token=token)
        logger.info("✅ Bot criado com sucesso")
        
        # Remove webhook
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook removido")
        
        # Inicia o sistema automático de verificação de ofertas
        logger.info("🤖 Iniciando sistema automático de ofertas...")
        
        # Cria contexto simulado para o sistema automático
        context = ContextoSimulado(bot)
        
        # Inicia tarefas em paralelo
        tasks = [
            bot_polling(bot, comando_oferta),  # Bot interativo
            sistema_automatico_ofertas(context)  # Sistema automático
        ]
        
        # Executa todas as tarefas
        await asyncio.gather(*tasks)
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}", exc_info=True)
        raise

async def bot_polling(bot, comando_oferta):
    """Função para o bot interativo"""
    logger.info("🤖 Iniciando bot com polling simples...")
    
    # Método alternativo: polling manual
    offset = 0
    while True:
        try:
            # Busca updates
            updates = await bot.get_updates(offset=offset, timeout=30)
            
            for update in updates:
                offset = update.update_id + 1
                
                # Processa comandos
                if update.message and update.message.text:
                    text = update.message.text
                    
                    if text.startswith('/start'):
                        await update.message.reply_text(
                            "🚀 **Garimpeiro Geek Ativado!**\n\n"
                            "Use /oferta para publicar ofertas manualmente.\n"
                            "Use /status para ver o status do sistema.",
                            parse_mode='Markdown'
                        )
                    
                    elif text.startswith('/status'):
                        await update.message.reply_text(
                            "📊 **Status do Sistema:**\n\n"
                            "✅ Sistema de postagem funcionando\n"
                            "✅ Correções das imagens aplicadas\n"
                            "✅ Estrutura das ofertas corrigida\n"
                            "✅ Links de afiliado funcionando\n"
                            "✅ Sistema automático ativo\n"
                            "🤖 Bot funcionando normalmente",
                            parse_mode='Markdown'
                        )
                    
                    elif text.startswith('/oferta'):
                        # Cria contexto simulado para o comando
                        context = ContextoSimulado(bot)
                        await comando_oferta(update, context)
            
            # Delay entre verificações
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Erro no polling: {e}")
            await asyncio.sleep(5)

async def sistema_automatico_ofertas(context):
    """Sistema automático de verificação de ofertas"""
    logger.info("🔄 Sistema automático de ofertas iniciado")
    
    while True:
        try:
            # Verifica ofertas a cada 1 hora
            await asyncio.sleep(3600)  # 1 hora
            
            logger.info("🔍 Verificando ofertas automaticamente...")
            
            # Importa scrapers
            try:
                from promobit_scraper_clean import buscar_ofertas_promobit
                from amazon_scraper import AmazonScraper
                from telegram_poster import publicar_oferta_automatica
                
                # Busca ofertas do Promobit
                logger.info("📊 Buscando ofertas do Promobit...")
                async with aiohttp.ClientSession() as session:
                    ofertas_promobit = await buscar_ofertas_promobit(session)
                    
                    if ofertas_promobit:
                        logger.info(f"✅ {len(ofertas_promobit)} ofertas encontradas no Promobit")
                        
                        # Publica as primeiras 3 ofertas
                        for i, oferta in enumerate(ofertas_promobit[:3]):
                            try:
                                logger.info(f"📤 Publicando oferta {i+1}: {oferta.get('titulo', 'Sem título')[:50]}...")
                                
                                # Verifica se tem imagem e título
                                if oferta.get('imagem_url') and oferta.get('titulo'):
                                    sucesso = await publicar_oferta_automatica(oferta, context)
                                    if sucesso:
                                        logger.info(f"✅ Oferta {i+1} publicada com sucesso!")
                                        # Aguarda 5 minutos entre publicações
                                        await asyncio.sleep(300)
                                    else:
                                        logger.error(f"❌ Falha ao publicar oferta {i+1}")
                                else:
                                    logger.warning(f"⚠️ Oferta {i+1} sem imagem ou título, pulando...")
                                    
                            except Exception as e:
                                logger.error(f"❌ Erro ao publicar oferta {i+1}: {e}")
                    else:
                        logger.info("ℹ️ Nenhuma oferta encontrada no Promobit")
                
                # Busca ofertas da Amazon
                logger.info("📊 Buscando ofertas da Amazon...")
                try:
                    scraper_amazon = AmazonScraper()
                    ofertas_amazon = scraper_amazon.buscar_ofertas(max_paginas=2)
                    
                    if ofertas_amazon:
                        logger.info(f"✅ {len(ofertas_amazon)} ofertas encontradas na Amazon")
                        
                        for i, oferta in enumerate(ofertas_amazon[:2]):  # Limita a 2 ofertas
                            try:
                                logger.info(f"📤 Publicando oferta Amazon {i+1}: {oferta.get('titulo', 'Sem título')[:50]}...")
                                
                                # Verifica se tem imagem e título
                                if oferta.get('imagem_url') and oferta.get('titulo'):
                                    sucesso = await publicar_oferta_automatica(oferta, context)
                                    if sucesso:
                                        logger.info(f"✅ Oferta Amazon {i+1} publicada com sucesso!")
                                        # Aguarda 5 minutos entre publicações
                                        await asyncio.sleep(300)
                                    else:
                                        logger.error(f"❌ Falha ao publicar oferta Amazon {i+1}")
                                else:
                                    logger.warning(f"⚠️ Oferta Amazon {i+1} sem imagem ou título, pulando...")
                                    
                            except Exception as e:
                                logger.error(f"❌ Erro ao publicar oferta Amazon {i+1}: {e}")
                    else:
                        logger.info("ℹ️ Nenhuma oferta encontrada na Amazon")
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao buscar ofertas da Amazon: {e}")
                
            except ImportError as e:
                logger.error(f"❌ Erro ao importar módulos: {e}")
            
            logger.info("✅ Verificação automática concluída")
            
        except Exception as e:
            logger.error(f"❌ Erro no sistema automático: {e}")
            await asyncio.sleep(300)  # Aguarda 5 minutos antes de tentar novamente

if __name__ == "__main__":
    try:
        asyncio.run(main_simples())
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}", exc_info=True)
        print(f"\n❌ Erro fatal: {e}")
        print("Verifique os logs para mais detalhes.")
