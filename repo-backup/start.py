#!/usr/bin/env python3
"""
Script de Inicialização do Garimpeiro Geek
Inicia todos os componentes do sistema
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional
import signal
import time

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.logging_setup import setup_logging
from src.core.storage import PreferencesStorage
from src.core.database import Database
from src.core.metrics import MetricsCollector
from src.app.bot.telegram_bot import TelegramBot
from config import TELEGRAM_CONFIG, SYSTEM_CONFIG

class GarimpeiroGeek:
    """Classe principal do sistema"""
    
    def __init__(self):
        self.logger = logging.getLogger("garimpeiro_geek")
        self.components = {}
        self.running = False
        self.start_time = None
        
        # Configurar logging
        setup_logging()
        
        # Configurar handlers de sinal
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Inicializar componentes
        self._init_components()
    
    def _signal_handler(self, signum, frame):
        """Handler para sinais de interrupção"""
        self.logger.info(f"Recebido sinal {signum}, iniciando shutdown...")
        self.running = False
    
    def _init_components(self):
        """Inicializa todos os componentes do sistema"""
        try:
            # 1. Storage de preferências
            self.logger.info("Inicializando sistema de preferências...")
            self.components['storage'] = PreferencesStorage()
            
            # 2. Banco de dados
            self.logger.info("Inicializando banco de dados...")
            self.components['database'] = Database()
            
            # 3. Coletor de métricas
            self.logger.info("Inicializando coletor de métricas...")
            self.components['metrics'] = MetricsCollector()
            
            # 4. Bot do Telegram (se configurado)
            if TELEGRAM_CONFIG.get('enabled', False):
                self.logger.info("Inicializando bot do Telegram...")
                try:
                    self.components['telegram'] = TelegramBot(
                        token=TELEGRAM_CONFIG['bot_token'],
                        chat_id=TELEGRAM_CONFIG.get('chat_id')
                    )
                except Exception as e:
                    self.logger.warning(f"Erro ao inicializar bot Telegram: {e}")
                    self.components['telegram'] = None
            else:
                self.logger.info("Bot do Telegram desabilitado")
                self.components['telegram'] = None
            
            self.logger.info("✅ Todos os componentes inicializados com sucesso")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar componentes: {e}")
            raise
    
    async def start_components(self):
        """Inicia todos os componentes assíncronos"""
        try:
            # Iniciar bot do Telegram
            if self.components.get('telegram'):
                self.logger.info("Iniciando bot do Telegram...")
                await self.components['telegram'].start()
                self.logger.info("✅ Bot do Telegram iniciado")
            
            # Iniciar coletor de métricas
            if self.components.get('metrics'):
                self.logger.info("Iniciando coletor de métricas...")
                self.components['metrics'].start()
                self.logger.info("✅ Coletor de métricas iniciado")
            
            self.logger.info("🚀 Todos os componentes iniciados com sucesso")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao iniciar componentes: {e}")
            raise
    
    async def stop_components(self):
        """Para todos os componentes assíncronos"""
        try:
            # Parar bot do Telegram
            if self.components.get('telegram'):
                self.logger.info("Parando bot do Telegram...")
                await self.components['telegram'].stop()
                self.logger.info("✅ Bot do Telegram parado")
            
            # Parar coletor de métricas
            if self.components.get('metrics'):
                self.logger.info("Parando coletor de métricas...")
                self.components['metrics'].stop()
                self.logger.info("✅ Coletor de métricas parado")
            
            self.logger.info("🛑 Todos os componentes parados")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao parar componentes: {e}")
    
    async def run(self):
        """Executa o sistema principal"""
        try:
            self.running = True
            self.start_time = time.time()
            
            self.logger.info("🚀 Iniciando Garimpeiro Geek...")
            self.logger.info(f"📁 Diretório de trabalho: {Path.cwd()}")
            self.logger.info(f"🐍 Versão Python: {sys.version}")
            
            # Iniciar componentes
            await self.start_components()
            
            # Loop principal
            self.logger.info("🔄 Sistema em execução... (Ctrl+C para parar)")
            
            while self.running:
                try:
                    # Verificar saúde dos componentes
                    await self._health_check()
                    
                    # Aguardar próximo ciclo
                    await asyncio.sleep(SYSTEM_CONFIG.get('health_check_interval', 30))
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Erro no loop principal: {e}")
                    await asyncio.sleep(5)
            
        except KeyboardInterrupt:
            self.logger.info("Interrupção recebida do usuário")
        except Exception as e:
            self.logger.error(f"Erro fatal no sistema: {e}")
        finally:
            await self.shutdown()
    
    async def _health_check(self):
        """Verifica a saúde dos componentes"""
        try:
            # Verificar banco de dados
            if self.components.get('database'):
                db_status = self.components['database'].check_connection()
                if not db_status:
                    self.logger.warning("⚠️ Problema com conexão do banco de dados")
            
            # Verificar bot do Telegram
            if self.components.get('telegram'):
                bot_status = await self.components['telegram'].get_status()
                if bot_status != "running":
                    self.logger.warning(f"⚠️ Bot do Telegram com status: {bot_status}")
            
            # Verificar métricas
            if self.components.get('metrics'):
                metrics_status = self.components['metrics'].is_running()
                if not metrics_status:
                    self.logger.warning("⚠️ Coletor de métricas parado")
            
        except Exception as e:
            self.logger.error(f"Erro no health check: {e}")
    
    async def shutdown(self):
        """Desliga o sistema de forma limpa"""
        try:
            self.logger.info("🛑 Iniciando shutdown do sistema...")
            
            # Parar componentes
            await self.stop_components()
            
            # Calcular tempo de execução
            if self.start_time:
                uptime = time.time() - self.start_time
                self.logger.info(f"⏱️ Tempo de execução: {uptime:.1f} segundos")
            
            # Salvar estado final
            if self.components.get('storage'):
                self.components['storage'].save_preferences()
                self.logger.info("💾 Preferências salvas")
            
            self.logger.info("👋 Garimpeiro Geek encerrado")
            
        except Exception as e:
            self.logger.error(f"❌ Erro durante shutdown: {e}")

def print_banner():
    """Imprime banner do sistema"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🎯 GARIMPEIRO GEEK 🎯                    ║
    ║              Sistema de Recomendações de Ofertas            ║
    ║                        via Telegram                         ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_menu():
    """Imprime menu de opções"""
    menu = """
    📋 OPÇÕES DISPONÍVEIS:
    
    1. 🚀 Iniciar sistema completo
    2. 🤖 Apenas bot Telegram
    3. 📊 Apenas dashboard
    4. 🔍 Apenas scrapers
    5. 🧪 Executar testes
    6. 📦 Criar backup
    7. 📊 Monitor do sistema
    8. ⚙️  Configurações
    0. ❌ Sair
    
    Escolha uma opção: """
    return input(menu).strip()

async def main():
    """Função principal"""
    print_banner()
    
    while True:
        choice = print_menu()
        
        if choice == "1":
            # Sistema completo
            print("\n🚀 Iniciando sistema completo...")
            system = GarimpeiroGeek()
            await system.run()
            break
        
        elif choice == "2":
            # Apenas bot Telegram
            print("\n🤖 Iniciando apenas bot Telegram...")
            if TELEGRAM_CONFIG.get('enabled', False):
                bot = TelegramBot(
                    token=TELEGRAM_CONFIG['bot_token'],
                    chat_id=TELEGRAM_CONFIG.get('chat_id')
                )
                await bot.start()
                print("✅ Bot iniciado. Pressione Ctrl+C para parar.")
                try:
                    await asyncio.Event().wait()  # Aguardar indefinidamente
                except KeyboardInterrupt:
                    await bot.stop()
                    print("🛑 Bot parado.")
            else:
                print("❌ Bot do Telegram desabilitado nas configurações")
        
        elif choice == "3":
            # Apenas dashboard
            print("\n📊 Iniciando dashboard...")
            print("Execute: python app/dashboard.py")
            break
        
        elif choice == "4":
            # Apenas scrapers
            print("\n🔍 Iniciando scrapers...")
            print("Execute: python -m scrapers.base_scraper")
            break
        
        elif choice == "5":
            # Executar testes
            print("\n🧪 Executando testes...")
            import subprocess
            try:
                result = subprocess.run(["python", "-m", "pytest", "tests/", "-v"], 
                                      capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print("Erros:", result.stderr)
            except Exception as e:
                print(f"❌ Erro ao executar testes: {e}")
            break
        
        elif choice == "6":
            # Criar backup
            print("\n📦 Criando backup...")
            import subprocess
            try:
                result = subprocess.run(["python", "backup.py", "--create"], 
                                      capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print("Erros:", result.stderr)
            except Exception as e:
                print(f"❌ Erro ao criar backup: {e}")
            break
        
        elif choice == "7":
            # Monitor do sistema
            print("\n📊 Iniciando monitor...")
            print("Execute: python monitor.py")
            break
        
        elif choice == "8":
            # Configurações
            print("\n⚙️ Configurações do sistema:")
            print(f"  • Bot Telegram: {'✅ Habilitado' if TELEGRAM_CONFIG.get('enabled') else '❌ Desabilitado'}")
            print(f"  • Modo debug: {'✅ Ativo' if SYSTEM_CONFIG.get('debug', False) else '❌ Inativo'}")
            print(f"  • Diretório de dados: {SYSTEM_CONFIG.get('data_dir', '.data')}")
            print(f"  • Diretório de logs: {SYSTEM_CONFIG.get('log_dir', 'logs')}")
            input("\nPressione Enter para continuar...")
        
        elif choice == "0":
            print("\n👋 Até logo!")
            break
        
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)

