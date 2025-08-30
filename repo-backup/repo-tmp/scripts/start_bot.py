#!/usr/bin/env python3
"""
Script para iniciar o bot do Telegram - Garimpeiro Geek

Uso:
    python scripts/start_bot.py

Ou:
    python -m scripts.start_bot
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.bot.telegram_bot import GarimpeiroGeekBot
from src.core.config import validate_config

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Função principal para iniciar o bot"""
    try:
        # Validar configurações
        logger.info("🔧 Validando configurações...")
        validate_config()
        logger.info("✅ Configurações válidas!")
        
        # Criar diretório de logs se não existir
        os.makedirs('logs', exist_ok=True)
        
        # Iniciar bot
        logger.info("🤖 Iniciando Garimpeiro Geek Bot...")
        bot = GarimpeiroGeekBot()
        
        # Iniciar polling
        await bot.start_polling()
        
        logger.info("🚀 Bot iniciado com sucesso!")
        logger.info("📱 Use Ctrl+C para parar o bot")
        
        # Manter o bot rodando
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Recebido sinal de parada...")
            await bot.stop()
            logger.info("✅ Bot parado com sucesso!")
            
    except ValueError as e:
        logger.error(f"❌ Erro de configuração: {e}")
        logger.error("💡 Configure as variáveis de ambiente ou edite src/core/config.py")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🤖 Garimpeiro Geek Bot - Sistema de Ofertas")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)

