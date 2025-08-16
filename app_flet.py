#!/usr/bin/env python3
"""
Sistema Inteligente de Alertas Geek - Aplicação Desktop Moderna com Flet
Interface refatorada com design clean, moderno e minimalista
Suporte nativo para temas claro e escuro
"""

import flet as ft
import sys
import os
import threading
import time
import asyncio
import logging
import queue
import json
from datetime import datetime
from typing import Optional

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa o sistema inteligente
from intelligent_geek_alert_system import IntelligentGeekAlertSystem

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('geek_alert_flet.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GeekAlertFletApp:
    """Aplicação Desktop Moderna com Flet para Sistema Inteligente de Alertas"""
    
    def __init__(self):
        self.page: Optional[ft.Page] = None
        self.running = False
        self.alert_system: Optional[IntelligentGeekAlertSystem] = None
        self.alert_thread: Optional[threading.Thread] = None
        self.log_queue = queue.Queue()
        self.config = self.load_config()
        
        # Estatísticas do sistema
        self.stats = {
            "total_alerts": 0,
            "total_products": 0,
            "search_cycles": 0,
            "last_alert": None,
            "status": "Parado"
        }
        
        # Componentes da interface
        self.start_button: Optional[ft.FilledButton] = None
        self.stop_button: Optional[ft.FilledButton] = None
        self.status_text: Optional[ft.Text] = None
        self.quick_stats_text: Optional[ft.Text] = None
        self.logs_list: Optional[ft.ListView] = None
        self.config_fields = {}
        
        # Configurações de tema
        self.current_theme = ft.ThemeMode.LIGHT
        
    def load_config(self) -> dict:
        """Carrega configurações do arquivo"""
        try:
            if os.path.exists('geek_alert_config.json'):
                with open('geek_alert_config.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"❌ Erro ao carregar configurações: {e}")
            return {}
    
    def save_config(self) -> bool:
        """Salva configurações"""
        try:
            config = {}
            for key, field in self.config_fields.items():
                config[key] = field.value
            
            with open('geek_alert_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info("✅ Configurações salvas")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar configurações: {e}")
            return False
    
    def create_left_panel(self) -> ft.Container:
        """Cria painel lateral esquerdo com controles"""
        # Título principal
        title = ft.Text(
            "🎮 CONTROLES",
            size=24,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            color=ft.colors.PRIMARY
        )
        
        # Botão Iniciar Sistema
        self.start_button = ft.FilledButton(
            text="🚀 INICIAR SISTEMA",
            icon=ft.icons.PLAY_ARROW,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.GREEN,
                padding=20,
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            on_click=self.start_system
        )
        
        # Botão Parar Sistema
        self.stop_button = ft.FilledButton(
            text="⏹️ PARAR SISTEMA",
            icon=ft.icons.STOP,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.RED,
                padding=20,
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            on_click=self.stop_system,
            disabled=True
        )
        
        # Switch de Tema
        theme_switch = ft.Switch(
            label="🌙 Modo Escuro",
            value=False,
            on_change=self.toggle_theme,
            active_color=ft.colors.PRIMARY
        )
        
        # Separador
        separator = ft.Divider(height=1, color=ft.colors.OUTLINE)
        
        # Botão Estatísticas
        stats_button = ft.OutlinedButton(
            text="📊 ESTATÍSTICAS",
            icon=ft.icons.ANALYTICS,
            style=ft.ButtonStyle(
                padding=15,
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=self.show_stats
        )
        
        # Botão Configurações
        config_button = ft.OutlinedButton(
            text="⚙️ CONFIGURAÇÕES",
            icon=ft.icons.SETTINGS,
            style=ft.ButtonStyle(
                padding=15,
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=self.show_config
        )
        
        # Botão Limpar Logs
        clear_button = ft.OutlinedButton(
            text="🧹 LIMPAR LOGS",
            icon=ft.icons.CLEAR_ALL,
            style=ft.ButtonStyle(
                padding=15,
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=self.clear_logs
        )
        
        # Status do Sistema
        self.status_text = ft.Text(
            "⏹️ PARADO",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.RED,
            text_align=ft.TextAlign.CENTER
        )
        
        status_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("📡 Status do Sistema", weight=ft.FontWeight.BOLD, size=16),
                    self.status_text
                ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20
            ),
            elevation=5
        )
        
        # Informações Rápidas
        self.quick_stats_text = ft.Text(
            "Nenhuma atividade",
            size=12,
            text_align=ft.TextAlign.CENTER
        )
        
        info_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("📊 Info Rápida", weight=ft.FontWeight.BOLD, size=16),
                    self.quick_stats_text
                ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20
            ),
            elevation=5
        )
        
        # Layout do painel esquerdo
        left_content = ft.Column([
            title,
            ft.Container(height=20),  # Espaçamento
            self.start_button,
            ft.Container(height=10),
            self.stop_button,
            ft.Container(height=20),
            theme_switch,
            ft.Container(height=20),
            separator,
            ft.Container(height=20),
            stats_button,
            ft.Container(height=10),
            config_button,
            ft.Container(height=10),
            clear_button,
            ft.Container(height=20),
            separator,
            ft.Container(height=20),
            status_card,
            ft.Container(height=15),
            info_card
        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        return ft.Container(
            content=left_content,
            width=300,
            padding=20,
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=10,
            margin=ft.margin.only(right=10)
        )
    
    def create_main_panel(self) -> ft.Container:
        """Cria painel principal direito com abas"""
        # Título principal
        main_title = ft.Text(
            "🚀 SISTEMA INTELIGENTE DE ALERTAS GEEK",
            size=28,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            color=ft.colors.PRIMARY
        )
        
        # Aba de Logs
        self.logs_list = ft.ListView(
            expand=True,
            auto_scroll=True,
            spacing=5,
            padding=20
        )
        
        logs_tab = ft.Tab(
            text="📝 Logs em Tempo Real",
            icon=ft.icons.ARTICLE,
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Checkbox(label="Auto-scroll", value=True),
                        ft.IconButton(
                            icon=ft.icons.CLEAR,
                            tooltip="Limpar logs",
                            on_click=self.clear_logs_display
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=10),
                    ft.Container(
                        content=self.logs_list,
                        expand=True,
                        border=ft.border.all(1, ft.colors.OUTLINE),
                        border_radius=8
                    )
                ]),
                padding=20
            )
        )
        
        # Aba de Configurações
        config_tab = ft.Tab(
            text="⚙️ Configurações",
            icon=ft.icons.SETTINGS,
            content=self.create_config_tab_content()
        )
        
        # Aba de Estatísticas
        stats_tab = ft.Tab(
            text="📊 Estatísticas",
            icon=ft.icons.ANALYTICS,
            content=self.create_stats_tab_content()
        )
        
        # Tabs container
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[logs_tab, config_tab, stats_tab]
        )
        
        # Layout do painel principal
        main_content = ft.Column([
            main_title,
            ft.Container(height=20),
            tabs
        ], expand=True)
        
        return ft.Container(
            content=main_content,
            expand=True,
            padding=20,
            bgcolor=ft.colors.SURFACE,
            border_radius=10
        )
    
    def create_config_tab_content(self) -> ft.Container:
        """Cria conteúdo da aba de configurações"""
        config_data = [
            ("🔍 Intervalo de Busca (minutos)", "search_interval", "5"),
            ("💰 Desconto Mínimo (%)", "discount_threshold", "15"),
            ("💸 Comissão Mínima (%)", "commission_threshold", "10"),
            ("📱 Chat ID do Telegram", "telegram_chat_id", self.config.get("telegram_chat_id", "")),
            ("🤖 Token do Bot", "telegram_bot_token", self.config.get("telegram_bot_token", "")),
            ("🔄 Máximo de Produtos por Busca", "max_products", "20"),
            ("⏰ Cooldown entre Alertas (horas)", "alert_cooldown", "6")
        ]
        
        config_fields = []
        for label, key, default_value in config_data:
            field = ft.TextField(
                label=label,
                value=default_value,
                border=ft.InputBorder.UNDERLINE,
                expand=True,
                text_size=14
            )
            self.config_fields[key] = field
            config_fields.append(field)
        
        # Botões de ação
        save_button = ft.FilledButton(
            text="💾 Salvar Configurações",
            icon=ft.icons.SAVE,
            on_click=self.save_config_click
        )
        
        reset_button = ft.OutlinedButton(
            text="🔄 Resetar",
            icon=ft.icons.RESTORE,
            on_click=self.reset_config
        )
        
        # Layout das configurações
        config_content = ft.Column([
            ft.Text("⚙️ Configurações do Sistema", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            *config_fields,
            ft.Container(height=20),
            ft.Row([
                save_button,
                reset_button
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        ], spacing=15)
        
        return ft.Container(
            content=config_content,
            padding=20,
            expand=True
        )
    
    def create_stats_tab_content(self) -> ft.Container:
        """Cria conteúdo da aba de estatísticas"""
        # Estatísticas principais
        stats_data = [
            ("🚀 Status do Sistema", "status"),
            ("📢 Total de Alertas", "total_alerts"),
            ("🔍 Produtos Analisados", "total_products"),
            ("🔄 Ciclos de Busca", "search_cycles"),
            ("⏰ Último Alerta", "last_alert"),
            ("💰 Produtos com Desconto", "products_with_discount"),
            ("💸 Comissão Total", "total_commission")
        ]
        
        self.stats_vars = {}
        stats_grid = []
        
        for i, (label, key) in enumerate(stats_data):
            var = ft.Text("0", size=16, weight=ft.FontWeight.BOLD)
            self.stats_vars[key] = var
            
            stats_grid.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(label, size=14, color=ft.colors.ON_SURFACE_VARIANT),
                        var
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20,
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    border_radius=8,
                    expand=True
                )
            )
        
        # Botão atualizar
        refresh_button = ft.FilledButton(
            text="🔄 Atualizar Estatísticas",
            icon=ft.icons.REFRESH,
            on_click=self.refresh_stats
        )
        
        # Layout das estatísticas
        stats_content = ft.Column([
            ft.Text("📊 Estatísticas do Sistema", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.GridView(
                runs_count=2,
                max_extent=200,
                child_aspect_ratio=1.5,
                spacing=15,
                run_spacing=15,
                controls=stats_grid
            ),
            ft.Container(height=20),
            refresh_button
        ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        return ft.Container(
            content=stats_content,
            padding=20,
            expand=True
        )
    
    def toggle_theme(self, e):
        """Alterna entre tema claro e escuro"""
        if e.control.value:
            self.current_theme = ft.ThemeMode.DARK
            self.page.theme_mode = ft.ThemeMode.DARK
        else:
            self.current_theme = ft.ThemeMode.LIGHT
            self.page.theme_mode = ft.ThemeMode.LIGHT
        
        self.page.update()
        logger.info(f"🎨 Tema alterado para: {'Escuro' if e.control.value else 'Claro'}")
    
    def start_system(self, e):
        """Inicia o sistema de alertas"""
        try:
            if self.running:
                self.show_snackbar("Sistema já está rodando!", ft.colors.ORANGE)
                return
            
            logger.info("🚀 Iniciando Sistema Inteligente de Alertas...")
            self.stats["status"] = "Rodando"
            
            # Atualiza interface
            self.status_text.value = "🚀 RODANDO"
            self.status_text.color = ft.colors.GREEN
            self.start_button.disabled = True
            self.stop_button.disabled = False
            
            # Inicia o sistema em thread separada
            self.alert_thread = threading.Thread(target=self.run_alert_system)
            self.alert_thread.daemon = True
            self.alert_thread.start()
            
            self.running = True
            
            # Mostra notificação
            self.show_snackbar("Sistema iniciado com sucesso!", ft.colors.GREEN)
            self.page.update()
            
            logger.info("✅ Sistema iniciado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar sistema: {e}")
            self.show_snackbar(f"Erro ao iniciar sistema: {e}", ft.colors.RED)
    
    def stop_system(self, e):
        """Para o sistema de alertas"""
        try:
            if not self.running:
                self.show_snackbar("Sistema não está rodando!", ft.colors.ORANGE)
                return
            
            logger.info("⏹️ Parando Sistema Inteligente de Alertas...")
            self.stats["status"] = "Parado"
            
            # Para o sistema
            if self.alert_system:
                self.alert_system.stop()
            
            self.running = False
            
            # Atualiza interface
            self.status_text.value = "⏹️ PARADO"
            self.status_text.color = ft.colors.RED
            self.start_button.disabled = False
            self.stop_button.disabled = True
            
            # Mostra notificação
            self.show_snackbar("Sistema parado com sucesso!", ft.colors.BLUE)
            self.page.update()
            
            logger.info("✅ Sistema parado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar sistema: {e}")
            self.show_snackbar(f"Erro ao parar sistema: {e}", ft.colors.RED)
    
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
            
            # Atualiza interface na thread principal
            self.page.after(0, self.handle_system_error, str(e))
    
    def handle_system_error(self, error_msg: str):
        """Manipula erros do sistema na thread principal"""
        self.status_text.value = "❌ ERRO"
        self.status_text.color = ft.colors.RED
        self.start_button.disabled = False
        self.stop_button.disabled = True
        self.show_snackbar(f"Erro do sistema: {error_msg}", ft.colors.RED)
        self.page.update()
    
    def show_stats(self, e):
        """Mostra estatísticas detalhadas"""
        stats_content = self.get_detailed_stats()
        
        # Cria diálogo de estatísticas
        stats_dialog = ft.AlertDialog(
            title=ft.Text("📊 Estatísticas Detalhadas"),
            content=ft.Text(stats_content, size=14),
            actions=[
                ft.TextButton("❌ Fechar", on_click=lambda _: self.page.dialog.open = False)
            ]
        )
        
        self.page.dialog = stats_dialog
        self.page.dialog.open = True
        self.page.update()
    
    def show_config(self, e):
        """Mostra configurações"""
        # Seleciona a aba de configurações
        self.page.views[0].controls[1].controls[1].selected_index = 1
        self.page.update()
    
    def get_detailed_stats(self) -> str:
        """Obtém estatísticas detalhadas"""
        try:
            stats = {
                "Status do Sistema": self.stats["status"],
                "Total de Alertas": self.stats["total_alerts"],
                "Produtos Analisados": self.stats["total_products"],
                "Ciclos de Busca": self.stats["search_cycles"],
                "Último Alerta": str(self.stats["last_alert"]) if self.stats["last_alert"] else "Nenhum"
            }
            
            content = "📊 ESTATÍSTICAS DO SISTEMA\n"
            content += "=" * 40 + "\n\n"
            
            for key, value in stats.items():
                content += f"{key}: {value}\n"
            
            return content
            
        except Exception as e:
            return f"Erro ao obter estatísticas: {e}"
    
    def refresh_stats(self, e):
        """Atualiza estatísticas"""
        try:
            # Atualiza variáveis de estatísticas
            for key, var in self.stats_vars.items():
                if key in self.stats:
                    var.value = str(self.stats[key])
                else:
                    var.value = "0"
            
            # Atualiza estatísticas rápidas
            self.update_quick_stats()
            
            self.page.update()
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar estatísticas: {e}")
    
    def update_quick_stats(self):
        """Atualiza estatísticas rápidas"""
        try:
            if self.running:
                status_text = f"🔄 {self.stats['search_cycles']} ciclos • 📢 {self.stats['total_alerts']} alertas"
            else:
                status_text = "Sistema parado"
            
            self.quick_stats_text.value = status_text
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar estatísticas rápidas: {e}")
    
    def clear_logs(self, e):
        """Limpa arquivo de logs"""
        try:
            with open('geek_alert_flet.log', 'w', encoding='utf-8') as f:
                f.write("")
            
            self.clear_logs_display()
            self.show_snackbar("Logs limpos com sucesso!", ft.colors.GREEN)
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar logs: {e}")
            self.show_snackbar(f"Erro ao limpar logs: {e}", ft.colors.RED)
    
    def clear_logs_display(self, e=None):
        """Limpa display de logs"""
        self.logs_list.controls.clear()
        self.logs_list.controls.append(
            ft.Text("Logs limpos.", color=ft.colors.ON_SURFACE_VARIANT)
        )
        self.page.update()
    
    def save_config_click(self, e):
        """Salva configurações"""
        if self.save_config():
            self.show_snackbar("Configurações salvas com sucesso!", ft.colors.GREEN)
        else:
            self.show_snackbar("Erro ao salvar configurações!", ft.colors.RED)
    
    def reset_config(self, e):
        """Reseta configurações para padrão"""
        try:
            default_config = {
                "search_interval": "5",
                "discount_threshold": "15",
                "commission_threshold": "10",
                "telegram_chat_id": "",
                "telegram_bot_token": "",
                "max_products": "20",
                "alert_cooldown": "6"
            }
            
            for key, value in default_config.items():
                if key in self.config_fields:
                    self.config_fields[key].value = value
            
            self.show_snackbar("Configurações resetadas para padrão!", ft.colors.BLUE)
            self.page.update()
            
        except Exception as e:
            logger.error(f"❌ Erro ao resetar configurações: {e}")
            self.show_snackbar(f"Erro ao resetar configurações: {e}", ft.colors.RED)
    
    def show_snackbar(self, message: str, color: str):
        """Mostra mensagem snackbar"""
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(message),
                bgcolor=color,
                action="OK"
            )
        )
    
    def update_logs(self):
        """Atualiza logs em tempo real"""
        try:
            # Verifica se há novos logs
            try:
                with open('geek_alert_flet.log', 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Atualiza apenas se o conteúdo mudou
                    if hasattr(self, 'last_log_content') and self.last_log_content == content:
                        pass
                    else:
                        # Limpa logs antigos
                        self.logs_list.controls.clear()
                        
                        # Adiciona novos logs
                        for line in content.split('\n'):
                            if line.strip():
                                self.logs_list.controls.append(
                                    ft.Text(
                                        line,
                                        size=12,
                                        font_family="Consolas",
                                        color=ft.colors.ON_SURFACE
                                    )
                                )
                        
                        self.last_log_content = content
                        
            except FileNotFoundError:
                pass
            
            # Atualiza estatísticas
            self.refresh_stats(None)
            
            # Agenda próxima atualização
            self.page.after(1000, self.update_logs)
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar logs: {e}")
    
    def main(self, page: ft.Page):
        """Função principal da aplicação Flet"""
        self.page = page
        
        # Configuração da página
        page.title = "🚀 Sistema Inteligente de Alertas Geek"
        page.theme_mode = self.current_theme
        page.window_width = 1200
        page.window_height = 800
        page.window_resizable = True
        page.padding = 20
        page.spacing = 20
        
        # Cria layout principal
        left_panel = self.create_left_panel()
        main_panel = self.create_main_panel()
        
        # Layout principal com dois painéis
        page.add(
            ft.Row([
                left_panel,
                main_panel
            ], expand=True, spacing=20)
        )
        
        # Inicia atualização de logs
        self.update_logs()
        
        logger.info("🚀 Aplicação Flet iniciada com sucesso!")

def main():
    """Função principal"""
    try:
        app = GeekAlertFletApp()
        ft.app(target=app.main)
        
    except Exception as e:
        logger.error(f"❌ Erro na aplicação: {e}")
        print(f"❌ Erro fatal na aplicação: {e}")

if __name__ == "__main__":
    main()
