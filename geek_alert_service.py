#!/usr/bin/env python3
"""
Serviço Windows para Sistema Inteligente de Alertas Geek
Roda automaticamente em background como serviço do Windows
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import time
import logging
from datetime import datetime
import asyncio
import threading

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa o sistema inteligente
from intelligent_geek_alert_system import IntelligentGeekAlertSystem

# Configuração de logging para serviço
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('geek_alert_service.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GeekAlertService(win32serviceutil.ServiceFramework):
    """Serviço Windows para Sistema Inteligente de Alertas Geek"""
    
    _svc_name_ = "GeekAlertService"
    _svc_display_name_ = "Sistema Inteligente de Alertas Geek"
    _svc_description_ = "Serviço que busca ofertas constantemente e posta alertas automáticos no Telegram"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = False
        self.alert_system = None
        self.service_thread = None
        
        # Configuração do socket para o serviço
        socket.setdefaulttimeout(60)
        
    def SvcStop(self):
        """Para o serviço"""
        logger.info("🛑 Parando serviço Geek Alert...")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        
        if self.alert_system:
            self.alert_system.stop()
        
        logger.info("✅ Serviço Geek Alert parado")
    
    def SvcDoRun(self):
        """Executa o serviço"""
        try:
            logger.info("🚀 Iniciando serviço Geek Alert...")
            self.running = True
            
            # Inicia o sistema em uma thread separada
            self.service_thread = threading.Thread(target=self.run_alert_system)
            self.service_thread.daemon = True
            self.service_thread.start()
            
            # Aguarda sinal de parada
            while self.running:
                if win32event.WaitForSingleObject(self.stop_event, 1000) == win32event.WAIT_OBJECT_0:
                    break
                    
        except Exception as e:
            logger.error(f"❌ Erro no serviço: {e}")
            self.running = False
    
    def run_alert_system(self):
        """Executa o sistema de alertas em thread separada"""
        try:
            logger.info("🎯 Iniciando Sistema Inteligente de Alertas...")
            
            # Cria e executa o sistema
            self.alert_system = IntelligentGeekAlertSystem()
            
            # Executa o sistema de forma síncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self.alert_system.run_continuous_search())
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"❌ Erro no sistema de alertas: {e}")
            self.running = False

def main():
    """Função principal para instalar/executar o serviço"""
    if len(sys.argv) == 1:
        # Executa o serviço
        try:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(GeekAlertService)
            servicemanager.StartServiceCtrlDispatcher()
        except win32service.error as e:
            logger.error(f"❌ Erro ao executar serviço: {e}")
    else:
        # Comandos de instalação/remoção
        win32serviceutil.HandleCommandLine(GeekAlertService)

if __name__ == '__main__':
    main()
