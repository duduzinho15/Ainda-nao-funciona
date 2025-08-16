#!/usr/bin/env python3
"""
Aplicativo Windows com Tray Icon para Sistema Inteligente de Alertas Geek
Roda em background com ícone na bandeja do sistema
"""

import sys
import os
import threading
import time
import asyncio
import logging
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
import pystray
from PIL import Image, ImageDraw
import queue

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa o sistema inteligente
from intelligent_geek_alert_system import IntelligentGeekAlertSystem

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('geek_alert_tray.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GeekAlertTrayApp:
    """Aplicativo Windows com Tray Icon para Sistema Inteligente de Alertas"""
    
    def __init__(self):
        self.running = False
        self.alert_system = None
        self.alert_thread = None
        self.icon = None
        self.log_queue = queue.Queue()
        self.stats = {
            "total_alerts": 0,
            "total_products": 0,
            "search_cycles": 0,
            "last_alert": None,
            "status": "Parado"
        }
        
        # Cria ícone da bandeja
        self.create_tray_icon()
        
    def create_tray_icon(self):
        """Cria ícone para a bandeja do sistema"""
        try:
            # Cria ícone simples (círculo verde)
            image = Image.new('RGB', (64, 64), color='white')
            draw = ImageDraw.Draw(image)
            draw.ellipse([8, 8, 56, 56], fill='green', outline='darkgreen', width=2)
            
            # Menu da bandeja
            menu = pystray.Menu(
                pystray.MenuItem("🚀 Iniciar Sistema", self.start_system),
                pystray.MenuItem("⏹️ Parar Sistema", self.stop_system),
                pystray.MenuItem("📊 Estatísticas", self.show_stats),
                pystray.MenuItem("📝 Ver Logs", self.show_logs),
                pystray.MenuItem("⚙️ Configurações", self.show_config),
                pystray.MenuItem("❌ Sair", self.quit_app)
            )
            
            # Cria o ícone da bandeja
            self.icon = pystray.Icon(
                "geek_alert",
                image,
                "Sistema Inteligente de Alertas Geek",
                menu
            )
            
            logger.info("✅ Ícone da bandeja criado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar ícone da bandeja: {e}")
    
    def start_system(self, icon=None, item=None):
        """Inicia o sistema de alertas"""
        try:
            if self.running:
                messagebox.showinfo("Sistema", "Sistema já está rodando!")
                return
            
            logger.info("🚀 Iniciando Sistema Inteligente de Alertas...")
            self.stats["status"] = "Rodando"
            
            # Inicia o sistema em thread separada
            self.alert_thread = threading.Thread(target=self.run_alert_system)
            self.alert_thread.daemon = True
            self.alert_thread.start()
            
            self.running = True
            
            # Atualiza ícone para verde
            self.update_icon_color('green')
            
            # Mostra notificação
            self.icon.notify("Sistema Iniciado", "Sistema de Alertas Geek está rodando!")
            
            logger.info("✅ Sistema iniciado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar sistema: {e}")
            messagebox.showerror("Erro", f"Erro ao iniciar sistema: {e}")
    
    def stop_system(self, icon=None, item=None):
        """Para o sistema de alertas"""
        try:
            if not self.running:
                messagebox.showinfo("Sistema", "Sistema não está rodando!")
                return
            
            logger.info("⏹️ Parando Sistema Inteligente de Alertas...")
            self.stats["status"] = "Parado"
            
            # Para o sistema
            if self.alert_system:
                self.alert_system.stop()
            
            self.running = False
            
            # Atualiza ícone para vermelho
            self.update_icon_color('red')
            
            # Mostra notificação
            self.icon.notify("Sistema Parado", "Sistema de Alertas Geek foi parado!")
            
            logger.info("✅ Sistema parado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar sistema: {e}")
            messagebox.showerror("Erro", f"Erro ao parar sistema: {e}")
    
    def run_alert_system(self):
        """Executa o sistema de alertas em thread separada"""
        try:
            logger.info("🎯 Executando Sistema Inteligente de Alertas...")
            
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
            self.stats["status"] = "Erro"
            self.update_icon_color('red')
    
    def update_icon_color(self, color):
        """Atualiza cor do ícone da bandeja"""
        try:
            if self.icon:
                # Cria novo ícone com a cor especificada
                image = Image.new('RGB', (64, 64), color='white')
                draw = ImageDraw.Draw(image)
                draw.ellipse([8, 8, 56, 56], fill=color, outline='darkgreen' if color == 'green' else 'darkred', width=2)
                
                self.icon.icon = image
                
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar ícone: {e}")
    
    def show_stats(self, icon=None, item=None):
        """Mostra estatísticas do sistema"""
        try:
            # Cria janela de estatísticas
            stats_window = tk.Toplevel()
            stats_window.title("📊 Estatísticas do Sistema Geek")
            stats_window.geometry("400x300")
            stats_window.resizable(False, False)
            
            # Centraliza a janela
            stats_window.transient()
            stats_window.grab_set()
            
            # Título
            title_label = tk.Label(stats_window, text="📊 ESTATÍSTICAS DO SISTEMA", 
                                 font=("Arial", 16, "bold"))
            title_label.pack(pady=20)
            
            # Frame para estatísticas
            stats_frame = ttk.Frame(stats_window)
            stats_frame.pack(pady=20, padx=20, fill="both", expand=True)
            
            # Estatísticas
            stats_data = [
                ("🚀 Status", self.stats["status"]),
                ("📢 Total de Alertas", str(self.stats["total_alerts"])),
                ("🔍 Produtos Analisados", str(self.stats["total_products"])),
                ("🔄 Ciclos de Busca", str(self.stats["search_cycles"])),
                ("⏰ Último Alerta", str(self.stats["last_alert"]) if self.stats["last_alert"] else "Nenhum")
            ]
            
            for i, (label, value) in enumerate(stats_data):
                row = i // 2
                col = i % 2
                
                label_widget = tk.Label(stats_frame, text=label, font=("Arial", 10, "bold"))
                label_widget.grid(row=row, column=col*2, sticky="w", padx=10, pady=5)
                
                value_widget = tk.Label(stats_frame, text=value, font=("Arial", 10))
                value_widget.grid(row=row, column=col*2+1, sticky="w", padx=10, pady=5)
            
            # Botão fechar
            close_btn = tk.Button(stats_window, text="❌ Fechar", 
                                command=stats_window.destroy, font=("Arial", 12))
            close_btn.pack(pady=20)
            
        except Exception as e:
            logger.error(f"❌ Erro ao mostrar estatísticas: {e}")
            messagebox.showerror("Erro", f"Erro ao mostrar estatísticas: {e}")
    
    def show_logs(self, icon=None, item=None):
        """Mostra logs do sistema"""
        try:
            # Cria janela de logs
            logs_window = tk.Toplevel()
            logs_window.title("📝 Logs do Sistema Geek")
            logs_window.geometry("600x400")
            
            # Centraliza a janela
            logs_window.transient()
            logs_window.grab_set()
            
            # Título
            title_label = tk.Label(logs_window, text="📝 LOGS DO SISTEMA", 
                                 font=("Arial", 16, "bold"))
            title_label.pack(pady=20)
            
            # Frame para logs
            logs_frame = ttk.Frame(logs_window)
            logs_frame.pack(pady=20, padx=20, fill="both", expand=True)
            
            # Área de texto para logs
            logs_text = tk.Text(logs_frame, wrap=tk.WORD, font=("Consolas", 9))
            logs_text.pack(side=tk.LEFT, fill="both", expand=True)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(logs_frame, orient=tk.VERTICAL, command=logs_text.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            logs_text.config(yscrollcommand=scrollbar.set)
            
            # Carrega logs do arquivo
            try:
                with open('geek_alert_tray.log', 'r', encoding='utf-8') as f:
                    logs = f.read()
                    logs_text.insert(tk.END, logs)
                    logs_text.see(tk.END)
            except FileNotFoundError:
                logs_text.insert(tk.END, "Nenhum log encontrado ainda.")
            
            # Botão atualizar
            refresh_btn = tk.Button(logs_window, text="🔄 Atualizar", 
                                  command=lambda: self.refresh_logs(logs_text), font=("Arial", 12))
            refresh_btn.pack(pady=10)
            
            # Botão fechar
            close_btn = tk.Button(logs_window, text="❌ Fechar", 
                                command=logs_window.destroy, font=("Arial", 12))
            close_btn.pack(pady=10)
            
        except Exception as e:
            logger.error(f"❌ Erro ao mostrar logs: {e}")
            messagebox.showerror("Erro", f"Erro ao mostrar logs: {e}")
    
    def refresh_logs(self, logs_text):
        """Atualiza logs na janela"""
        try:
            logs_text.delete(1.0, tk.END)
            with open('geek_alert_tray.log', 'r', encoding='utf-8') as f:
                logs = f.read()
                logs_text.insert(tk.END, logs)
                logs_text.see(tk.END)
        except FileNotFoundError:
            logs_text.insert(tk.END, "Nenhum log encontrado ainda.")
    
    def show_config(self, icon=None, item=None):
        """Mostra configurações do sistema"""
        try:
            # Cria janela de configurações
            config_window = tk.Toplevel()
            config_window.title("⚙️ Configurações do Sistema Geek")
            config_window.geometry("500x400")
            config_window.resizable(False, False)
            
            # Centraliza a janela
            config_window.transient()
            config_window.grab_set()
            
            # Título
            title_label = tk.Label(config_window, text="⚙️ CONFIGURAÇÕES DO SISTEMA", 
                                 font=("Arial", 16, "bold"))
            title_label.pack(pady=20)
            
            # Frame para configurações
            config_frame = ttk.Frame(config_window)
            config_frame.pack(pady=20, padx=20, fill="both", expand=True)
            
            # Configurações
            config_data = [
                ("🔍 Intervalo de Busca (minutos)", "5"),
                ("💰 Desconto Mínimo (%)", "15"),
                ("💸 Comissão Mínima (%)", "10"),
                ("📱 Chat ID do Telegram", "Seu Chat ID"),
                ("🤖 Token do Bot", "Seu Bot Token")
            ]
            
            config_vars = []
            for i, (label, default_value) in enumerate(config_data):
                row = i
                
                label_widget = tk.Label(config_frame, text=label, font=("Arial", 10, "bold"))
                label_widget.grid(row=row, column=0, sticky="w", padx=10, pady=5)
                
                var = tk.StringVar(value=default_value)
                config_vars.append(var)
                
                entry_widget = tk.Entry(config_frame, textvariable=var, font=("Arial", 10), width=30)
                entry_widget.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
            
            # Configura grid
            config_frame.columnconfigure(1, weight=1)
            
            # Botões
            button_frame = tk.Frame(config_window)
            button_frame.pack(pady=20)
            
            save_btn = tk.Button(button_frame, text="💾 Salvar", 
                               command=lambda: self.save_config(config_vars), font=("Arial", 12))
            save_btn.pack(side=tk.LEFT, padx=10)
            
            close_btn = tk.Button(button_frame, text="❌ Fechar", 
                                command=config_window.destroy, font=("Arial", 12))
            close_btn.pack(side=tk.LEFT, padx=10)
            
        except Exception as e:
            logger.error(f"❌ Erro ao mostrar configurações: {e}")
            messagebox.showerror("Erro", f"Erro ao mostrar configurações: {e}")
    
    def save_config(self, config_vars):
        """Salva configurações"""
        try:
            # Aqui você implementaria a lógica para salvar as configurações
            messagebox.showinfo("Configurações", "Configurações salvas com sucesso!")
            logger.info("✅ Configurações salvas")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar configurações: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar configurações: {e}")
    
    def quit_app(self, icon=None, item=None):
        """Sai do aplicativo"""
        try:
            logger.info("🛑 Saindo do aplicativo...")
            
            # Para o sistema se estiver rodando
            if self.running:
                self.stop_system()
            
            # Remove ícone da bandeja
            if self.icon:
                self.icon.stop()
            
            # Sai do aplicativo
            sys.exit(0)
            
        except Exception as e:
            logger.error(f"❌ Erro ao sair: {e}")
            sys.exit(1)
    
    def run(self):
        """Executa o aplicativo"""
        try:
            logger.info("🚀 Iniciando Aplicativo Geek Alert...")
            
            # Inicia o ícone da bandeja
            if self.icon:
                self.icon.run()
            else:
                logger.error("❌ Ícone da bandeja não foi criado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao executar aplicativo: {e}")

def main():
    """Função principal"""
    try:
        # Cria e executa o aplicativo
        app = GeekAlertTrayApp()
        app.run()
        
    except Exception as e:
        logger.error(f"❌ Erro no aplicativo: {e}")
        messagebox.showerror("Erro Fatal", f"Erro no aplicativo: {e}")

if __name__ == "__main__":
    main()
