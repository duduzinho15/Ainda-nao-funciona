# flet_app/main.py
import argparse
import os
import time
import threading
import asyncio
from typing import Optional, Literal
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import flet as ft
from flet_app.ui_tokens import tokens
from ui.theme import theme_manager
from ui.components import (
    create_metric_card, create_filter_chip, create_skeleton_card,
    create_bar_chart, create_log_entry, create_status_chip,
    create_snackbar, create_loading_spinner, create_empty_state
)
from services.metrics import metrics_service
from services.config_service import config_service
from services.control_service import control_service
from services.log_service import log_service

APP_TITLE = "Garimpeiro Geek - Dashboard"

class DashboardState:
    """Estado centralizado do dashboard"""
    def __init__(self):
        self.theme_mode: Literal["light", "dark"] = "dark"
        self.range_key: Literal["24h", "7d", "30d", "all"] = "24h"
        self.loading_metrics: bool = False
        self.last_metrics: Optional[dict] = None
        self.last_loaded_at: Optional[float] = None

class Dashboard:
    def __init__(self, page: ft.Page):
        self.page = page
        
        # Carrega preferências
        self.prefs = theme_manager.load_prefs()
        self.state = DashboardState()
        self.state.theme_mode = self.prefs.theme
        self.state.range_key = self.prefs.period_filter if self.prefs.period_filter in ["24h", "7d", "30d", "all"] else "24h"
        self.t = tokens(self.state.theme_mode)
        
        # Thread pool único para métricas
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="metrics")
        
        # Referências de controles para tema
        self.header_container = None
        self.header_title = None
        self.metric_cards = []
        self.chart_container = None
        self.logs_container = None
        
        # Estados
        self.logs_lv: Optional[ft.ListView] = None
        self.metrics_cards = []
        
        # Configurações
        self.config_fields = {}
        
        # Controles
        self.status_text = None
        
        # Captura o loop principal para callbacks
        try:
            self._main_loop = asyncio.get_event_loop()
        except RuntimeError:
            self._main_loop = None
        
        # Controle de sequência para evitar race conditions
        self._req_seq = 0
        
        # Inicializa serviços
        self._setup_services()
    
    # --- Helpers de feedback/tema ---
    def _snack(self, msg: str, ok: bool = True):
        try:
            sb = ft.SnackBar(ft.Text(msg))
            sb.bgcolor = "#16A34A" if ok else "#DC2626"
            self.page.snack_bar = sb
            self.page.snack_bar.open = True
            self.page.update()
        except Exception:
            print(f"[SNACK] {msg}")

    def _show_loading_ui(self):
        # skeletons nos cards
        if hasattr(self, "metric_cards"):
            self.metric_cards.controls.clear()
            for _ in range(4):
                self.metric_cards.controls.append(create_skeleton_card(self.t))
        # spinner no gráfico
        if self.chart_container:
            self.chart_container.content = ft.Row(
                [ft.ProgressRing(), ft.Text("Carregando...")],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        self.page.update()

    def _recolor_chart(self):
        ch = getattr(self.chart_container, "content", None)
        if not ch:
            return
        if isinstance(ch, ft.BarChart):
            ch.bgcolor = self.t.surface
            try:
                ch.left_axis.label_style = ft.TextStyle(color=self.t.text_muted)
                ch.bottom_axis.label_style = ft.TextStyle(color=self.t.text_muted)
                # margem e grade discreta ajudam no Dark
                ch.horizontal_grid_lines = ft.ChartGridLines(color=self.t.border)
                ch.border = ft.border.all(0, "transparent")
            except Exception:
                pass
            for g in ch.bar_groups or []:
                for r in getattr(g, "bar_rods", []):
                    r.color = self.t.primary

    def _recolor_period_chips(self) -> None:
        if not getattr(self, "period_chips", None):
            return
        for key, ch in self.period_chips.items():
            sel = ch.selected
            try:
                ch.bgcolor = self.t.primary if sel else self.t.surface
                if isinstance(ch.label, ft.Text):
                    ch.label.color = self.t.on_primary if sel else self.t.text
                    ch.label.weight = ft.FontWeight.W_700 if sel else None
                ch.side = ft.BorderSide(0 if sel else 1, "transparent" if sel else self.t.border)
            except Exception:
                pass

    def apply_theme(self):
        # atualizar tokens para o modo atual
        self.t = tokens("dark" if self.page.theme_mode == ft.ThemeMode.DARK else "light")
        # header
        if self.header_container:
            self.header_container.bgcolor = self.t.surface
        if self.header_title:
            self.header_title.color = self.t.text
        if getattr(self, "theme_label", None):
            self.theme_label.value = f"Tema: {self.state.theme_mode.title()}"
            self.theme_label.color = self.t.text_muted
        if getattr(self, "theme_btn", None):
            self.theme_btn.icon = "dark_mode" if self.state.theme_mode == "light" else "light_mode"
            self.theme_btn.style = ft.ButtonStyle(
                color={ft.ControlState.DEFAULT: self.t.text},
            )
        # cards
        if hasattr(self, "metric_cards"):
            for c in getattr(self.metric_cards, "controls", []):
                c.bgcolor = self.t.surface
                try:
                    c.border = ft.border.all(1, self.t.border)
                except Exception:
                    pass
        # gráfico e logs
        for cont in (self.chart_container, self.logs_container):
            if cont:
                cont.bgcolor = self.t.surface
                try:
                    cont.border = ft.border.all(1, self.t.border)
                except Exception:
                    pass
        # toolbar de logs (estilo)
        for b in (getattr(self, "btn_reload", None), getattr(self, "btn_open", None), getattr(self, "btn_clear", None)):
            if b:
                b.style = ft.ButtonStyle(
                    color={ft.ControlState.DEFAULT: self.t.text},
                    side={ft.ControlState.DEFAULT: ft.BorderSide(1, self.t.border)},
                    shape=ft.RoundedRectangleBorder(radius=8),
                )
        # chips e gráfico
        self._recolor_period_chips()
        self._recolor_chart()
        self.page.update()

    def toggle_theme(self, _=None):
        self.state.theme_mode = "dark" if self.state.theme_mode == "light" else "light"
        self.page.theme_mode = ft.ThemeMode.DARK if self.state.theme_mode == "dark" else ft.ThemeMode.LIGHT
        self.apply_theme()
    

    
    def _setup_services(self):
        """Configura serviços e callbacks"""
        # Controle
        control_service.add_status_callback(self._on_status_change)
        
        # Logs
        log_service.add_log_callback(self._on_new_log)
        
        # Inicia monitoramento de logs
        log_service.start_monitoring()
    
    def _on_status_change(self, status):
        """Callback para mudanças de status do sistema"""
        if self.status_text:
            self._update_status_ui(status)
    
    def _on_new_log(self, log_line):
        """Callback para novas linhas de log"""
        if self.logs_lv:
            self._add_log_entry(log_line)
    
    def _update_status_ui(self, status):
        """Atualiza UI de status na thread principal"""
        if self.status_text:
            self.status_text.value = f"Status: {status.value}"
            self.status_text.color = self.t.text_muted
            self.page.update()
    
    def _add_log_entry(self, log_line):
        """Adiciona entrada de log na thread principal"""
        if self.logs_lv and hasattr(self.logs_lv, 'controls'):
            try:
                self.logs_lv.controls.append(create_log_entry(log_line, self.t))
                # Limita a 1000 entradas para não sobrecarregar a memória
                if len(self.logs_lv.controls) > 1000:
                    # Remove entradas antigas de forma segura
                    excess = len(self.logs_lv.controls) - 1000
                    for _ in range(excess):
                        if self.logs_lv.controls:
                            self.logs_lv.controls.pop(0)
                self.page.update()
            except Exception as e:
                print(f"Erro ao adicionar log: {e}")
    
    # Método apply_theme duplicado removido - mantido apenas o primeiro
    

    
    def build(self):
        """Constrói a interface principal"""
        self.page.title = APP_TITLE
        self.page.theme_mode = ft.ThemeMode.DARK if self.state.theme_mode == "dark" else ft.ThemeMode.LIGHT
        self.page.padding = 12
        self.page.scroll = ft.ScrollMode.AUTO  # habilita rolagem vertical
        # self.page.window_min_width = 1000  # Não disponível nesta versão
        # self.page.window_min_height = 700  # Não disponível nesta versão
        
        # AppBar
        self.header_title = ft.Text(APP_TITLE, size=24, weight="bold", color=self.t.text)
        self.theme_label = ft.Text(f"Tema: {self.state.theme_mode.title()}", color=self.t.text_muted)
        self.theme_btn = ft.IconButton(
            icon="dark_mode" if self.state.theme_mode == "light" else "light_mode",
            tooltip="Alternar tema",
            style=ft.ButtonStyle(color={ft.ControlState.DEFAULT: self.t.text}),
            on_click=self.toggle_theme,
        )

        self.header_container = ft.Container(
            bgcolor=self.t.surface,
            border=ft.border.all(1, self.t.border) if hasattr(ft, 'border') else None,
            border_radius=12,
            padding=16,
            content=ft.Row(
                controls=[
                    self.header_title,
                    ft.Row(spacing=16, controls=[self.theme_label, self.theme_btn]),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        )
        
        # Abas
        tabs = ft.Tabs(
            selected_index=self.prefs.last_tab,
            indicator_color=self.t.primary,
            on_change=self._on_tab_change,
            tabs=[
                ft.Tab(text="Logs", content=self._build_logs_tab()),
                ft.Tab(text="Configurações", content=self._build_config_tab()),
                ft.Tab(text="Controles", content=self._build_controls_tab()),
            ],
        )
        
        self.page.controls.clear()
        self.page.add(self.header_container, ft.Container(height=16), tabs)
        self.page.update()
        
        # Carrega métricas iniciais
        self._load_metrics()
    
    def _build_logs_tab(self):
        """Constrói aba de logs"""
        # Filtros de período (chips estáveis)
        period_filters = ft.Row(
            spacing=8,
            wrap=True,
            run_spacing=8,
            controls=[
                self._make_chip("24h", "24h"),
                self._make_chip("7d", "7d"),
                self._make_chip("30d", "30d"),
                self._make_chip("all", "Tudo"),
            ],
        )
        self._recolor_period_chips()
        
        # Cards de métricas
        self.metric_cards = ft.Row(
            spacing=12,
            run_spacing=12,
            wrap=True,
            controls=[
                create_skeleton_card(self.t),
                create_skeleton_card(self.t),
                create_skeleton_card(self.t),
                create_skeleton_card(self.t),
            ],
        )
        
        # Gráfico
        self.chart_container = ft.Container(
            content=create_loading_spinner(self.t),
            bgcolor=self.t.surface,
            border=ft.border.all(1, self.t.border),
            border_radius=12,
            padding=16,
            height=380,  # altura fixa ajuda no layout em janelas menores
        )
        
        # Lista de logs
        self.logs_lv = ft.ListView(expand=True, auto_scroll=True, spacing=4, padding=8)
        
        # Carrega logs existentes
        recent_logs = log_service.get_recent_logs(20)
        for log_line in recent_logs:
            self.logs_lv.controls.append(create_log_entry(log_line, self.t))
        
        # Botões de ação para logs (guarde referências)
        self.btn_reload = ft.OutlinedButton(
            "Recarregar", icon="refresh", on_click=self._reload_logs,
            style=ft.ButtonStyle(color={ft.ControlState.DEFAULT: self.t.text}),
        )
        self.btn_open = ft.OutlinedButton(
            "Abrir Pasta", icon="folder_open", on_click=self._open_logs_folder,
            style=ft.ButtonStyle(color={ft.ControlState.DEFAULT: self.t.text}),
        )
        self.btn_clear = ft.OutlinedButton(
            "Limpar", icon="clear_all", on_click=self._clear_logs,
            style=ft.ButtonStyle(color={ft.ControlState.DEFAULT: self.t.text}),
        )

        logs_actions = ft.Row(spacing=8, controls=[self.btn_reload, self.btn_open, self.btn_clear])
        
        self.logs_container = ft.Container(
            bgcolor=self.t.surface,
            border=ft.border.all(1, self.t.border),
            border_radius=12,
            padding=16,
            content=ft.Column([
                ft.Row([
                    ft.Text("Logs do Sistema", size=18, weight=ft.FontWeight.W_700, color=self.t.text),
                    ft.Container(width=20),  # Espaçador simples
                    logs_actions,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.logs_lv
            ], spacing=12),
        )
        
        return ft.Column(
            spacing=16,
            controls=[
                ft.Text("Visão Geral", size=20, weight=ft.FontWeight.W_700, color=self.t.text),
                period_filters,
                self.metric_cards,
                ft.Text("Gráfico de Distribuição", size=18, weight=ft.FontWeight.W_700, color=self.t.text),
                self.chart_container,
                ft.Text("Logs em Tempo Real", size=18, weight=ft.FontWeight.W_700, color=self.t.text),
                self.logs_container,
            ],
        )
    
    def _build_config_tab(self):
        """Constrói aba de configurações"""
        config = config_service.get_config()
        
        # Campos de configuração
        self.config_fields = {
            "search_interval": ft.TextField(
                label="Intervalo de busca (minutos)",
                value=str(config.search_interval),
                border_radius=8,
                bgcolor=self.t.surface,
                color=self.t.text,
            ),
            "discount_threshold": ft.TextField(
                label="Desconto mínimo (%)",
                value=str(config.discount_threshold),
                border_radius=8,
                bgcolor=self.t.surface,
                color=self.t.text,
            ),
            "commission_threshold": ft.TextField(
                label="Comissão mínima (%)",
                value=str(config.commission_threshold),
                border_radius=8,
                bgcolor=self.t.surface,
                color=self.t.text,
            ),
            "max_products": ft.TextField(
                label="Máximo de produtos",
                value=str(config.max_products),
                border_radius=8,
                bgcolor=self.t.surface,
                color=self.t.text,
            ),
            "telegram_chat_id": ft.TextField(
                label="Chat ID do Telegram",
                value=config.telegram_chat_id,
                border_radius=8,
                bgcolor=self.t.surface,
                color=self.t.text,
            ),
            "telegram_bot_token": ft.TextField(
                label="Token do Bot",
                value=config.telegram_bot_token,
                password=True,
                can_reveal_password=True,
                border_radius=8,
                bgcolor=self.t.surface,
                color=self.t.text,
            ),
        }
        
        # Layout dos campos
        fields_layout = ft.Column(
            spacing=16,
            controls=[
                ft.Text("Configurações do Sistema", size=20, weight=ft.FontWeight.W_700, color=self.t.text),
                
                # Scraping
                ft.Container(
                    bgcolor=self.t.card,
                    border_radius=8,
                    padding=16,
                    content=ft.Column([
                        ft.Text("Scraping", size=16, weight=ft.FontWeight.W_600, color=self.t.text),
                        ft.Row([
                            self.config_fields["search_interval"],
                            self.config_fields["discount_threshold"],
                        ], spacing=12),
                        ft.Row([
                            self.config_fields["commission_threshold"],
                            self.config_fields["max_products"],
                        ], spacing=12),
                    ], spacing=12)
                ),
                
                # Telegram
                ft.Container(
                    bgcolor=self.t.card,
                    border_radius=8,
                    padding=16,
                    content=ft.Column([
                        ft.Text("Telegram", size=16, weight=ft.FontWeight.W_600, color=self.t.text),
                        self.config_fields["telegram_chat_id"],
                        self.config_fields["telegram_bot_token"],
                    ], spacing=12)
                ),
                
                # Botões
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.FilledButton(
                            "Salvar Configurações",
                            style=ft.ButtonStyle(
                                bgcolor={ft.ControlState.DEFAULT: self.t.primary},
                                color={ft.ControlState.DEFAULT: self.t.surface},
                            ),
                            on_click=self._save_config,
                        ),
                        ft.OutlinedButton(
                            "Restaurar Padrão",
                            style=ft.ButtonStyle(
                                color={ft.ControlState.DEFAULT: self.t.text},
                            ),
                            on_click=self._reset_config,
                        ),
                        ft.OutlinedButton(
                            "Validar",
                            style=ft.ButtonStyle(
                                color={ft.ControlState.DEFAULT: self.t.text},
                            ),
                            on_click=self._validate_config,
                        ),
                    ],
                ),
            ],
        )
        
        return ft.Container(
            bgcolor=self.t.surface,
            border=ft.border.all(1, self.t.border),
            border_radius=12,
            padding=20,
            content=fields_layout,
        )
    
    def _build_controls_tab(self):
        """Constrói aba de controles"""
        # Status grande e claro
        current_status = control_service.get_status()
        status_color = {
            "running": self.t.success,
            "stopped": self.t.danger,
            "error": self.t.danger,  # Usa danger para erro também
        }.get(current_status.value, self.t.text_muted)
        
        status_header = ft.Container(
            bgcolor=status_color,
            border_radius=12,
            padding=20,
            content=ft.Column([
                ft.Text(
                    f"Status: {current_status.value.upper()}",
                    size=24,
                    weight=ft.FontWeight.W_700,
                    color=self.t.surface,
                ),
                ft.Text(
                    f"Última atualização: {datetime.now().strftime('%H:%M:%S')}",
                    size=14,
                    color=self.t.surface,
                ),
            ], spacing=8),
        )
        
        self.status_text = ft.Text(
            f"Status: {current_status.value}",
            color=self.t.text_muted,
            size=16,
        )
        
        # Controles principais
        main_controls = ft.Row(
            spacing=16,
            controls=[
                ft.FilledButton(
                    "Iniciar Sistema",
                    style=ft.ButtonStyle(
                        bgcolor={ft.ControlState.DEFAULT: self.t.success},
                        color={ft.ControlState.DEFAULT: self.t.surface},
                    ),
                    on_click=self._start_system,
                ),
                ft.FilledButton(
                    "Parar Sistema",
                    style=ft.ButtonStyle(
                        bgcolor={ft.ControlState.DEFAULT: self.t.danger},
                        color={ft.ControlState.DEFAULT: self.t.surface},
                    ),
                    on_click=self._stop_system,
                ),
            ],
        )
        
        # Ações rápidas
        quick_actions = ft.Row(
            spacing=12,
            controls=[
                ft.OutlinedButton(
                    "Forçar Coleta",
                    style=ft.ButtonStyle(
                        color={ft.ControlState.DEFAULT: self.t.text},
                    ),
                    on_click=self._force_collection,
                ),
                ft.OutlinedButton(
                    "Verificar Saúde",
                    style=ft.ButtonStyle(
                        color={ft.ControlState.DEFAULT: self.t.text},
                    ),
                    on_click=self._check_health,
                ),
                ft.OutlinedButton(
                    "Limpar Logs",
                    style=ft.ButtonStyle(
                        color={ft.ControlState.DEFAULT: self.t.text},
                    ),
                    on_click=self._clear_logs,
                ),
            ],
        )
        
        # Estatísticas
        stats = control_service.get_stats()
        stats_text = ft.Text(
            f"Ofertas encontradas: {stats['ofertas_encontradas']} | "
            f"Postadas: {stats['ofertas_postadas']} | "
            f"Erros: {stats['erros']}",
            color=self.t.text_muted,
            size=14,
        )
        
        return ft.Container(
            bgcolor=self.t.surface,
            border=ft.border.all(1, self.t.border),
            border_radius=12,
            padding=20,
            content=ft.Column(
                spacing=20,
                controls=[
                    ft.Text("Controles do Sistema", size=20, weight=ft.FontWeight.W_700, color=self.t.text),
                    status_header,
                    main_controls,
                    ft.Divider(color=self.t.border),
                    ft.Text("Ações Rápidas", size=16, weight=ft.FontWeight.W_600, color=self.t.text),
                    quick_actions,
                    ft.Divider(color=self.t.border),
                    ft.Text("Estatísticas", size=16, weight=ft.FontWeight.W_600, color=self.t.text),
                    stats_text,
                ],
            ),
        )
    
    def _change_period(self, period: str) -> None:
        if period not in ("24h", "7d", "30d", "all"):
            return
        for k, ch in self.period_chips.items():
            ch.selected = (k == period)
        self.state.range_key = period
        self._recolor_period_chips()
        self._load_metrics(period)

    def _load_metrics(self, period: str | None = None) -> None:
        import threading
        period = period or self.state.range_key
        self._req_seq += 1
        req_id = self._req_seq
        self._show_loading_ui()

        def work() -> None:
            data = metrics_service.get_metrics(period)
            self.page.call_from_thread(
                lambda: self._on_metrics_loaded(req_id, period, data)
            )

        threading.Thread(target=work, daemon=True).start()

    def _on_metrics_loaded(self, req_id: int, period: str, data: dict) -> None:
        if req_id != self._req_seq:   # ignora respostas antigas
            return
        self._update_metrics_ui(data)
        self._recolor_chart()
    

    

    

    

    

    
    def _update_metrics_ui(self, data: dict):
        """Atualiza UI das métricas na thread principal"""
        try:
            # Atualiza cards
            self.metric_cards.controls = [
                create_metric_card("Ofertas", str(data["total"]), "shopping_cart", self.t.primary, self.t),
                create_metric_card("Lojas Ativas", str(data["stores"]), "store", self.t.success, self.t),
                create_metric_card("Preço Médio", f"R$ {data['avg']:.2f}", "attach_money", self.t.warning, self.t),
                create_metric_card("Período", self.state.range_key.upper(), "schedule", self.t.text_muted, self.t),
            ]
            
            # Atualiza gráfico
            if data["chart"] and not data["empty"]:
                max_value = max(value for _, value in data["chart"])
                self.chart_container.content = create_bar_chart(data["chart"], max_value, self.t)
            else:
                self.chart_container.content = create_empty_state("Sem dados para o período", "bar_chart", self.t)
            
        except Exception as e:
            print(f"Erro ao atualizar UI das métricas: {e}")
            # Em caso de erro, mostra estado de erro
            self.chart_container.content = create_empty_state("Erro ao carregar dados", "error", self.t)
        finally:
            # Sempre limpa o estado de loading
            self.state.loading_metrics = False
            self.page.update()
    

    
    def _on_tab_change(self, e):
        """Callback para mudança de aba"""
        self.prefs.last_tab = e.control.selected_index
        theme_manager.update_last_tab(self.prefs, e.control.selected_index)
    
    def _save_config(self, _):
        """Salva configurações"""
        try:
            # Valida campos
            config = config_service.get_config()
            
            config.search_interval = int(self.config_fields["search_interval"].value)
            config.discount_threshold = float(self.config_fields["discount_threshold"].value)
            config.commission_threshold = float(self.config_fields["commission_threshold"].value)
            config.max_products = int(self.config_fields["max_products"].value)
            config.telegram_chat_id = self.config_fields["telegram_chat_id"].value
            config.telegram_bot_token = self.config_fields["telegram_bot_token"].value
            
            # Valida
            is_valid, message = config_service.validate_config(config)
            if not is_valid:
                self._snack(f"Erro: {message}", ok=False)
                return
            
            # Salva
            if config_service.save_config(config):
                self._snack("Configurações salvas com sucesso!")
            else:
                self._snack("Erro ao salvar configurações", ok=False)
                
        except ValueError as e:
            self._snack("Erro: Valores inválidos nos campos", ok=False)
        except Exception as e:
            self._snack(f"Erro: {str(e)}", ok=False)
    
    def _reset_config(self, _):
        """Reseta configurações para padrão"""
        config = config_service.reset_to_defaults()
        
        # Atualiza campos
        self.config_fields["search_interval"].value = str(config.search_interval)
        self.config_fields["discount_threshold"].value = str(config.discount_threshold)
        self.config_fields["commission_threshold"].value = str(config.commission_threshold)
        self.config_fields["max_products"].value = str(config.max_products)
        self.config_fields["telegram_chat_id"].value = config.telegram_chat_id
        self.config_fields["telegram_bot_token"].value = config.telegram_bot_token
        
        self.page.update()
        self._snack("Configurações resetadas para padrão")
    
    def _validate_config(self, _):
        """Valida configurações sem salvar"""
        try:
            # Cria config temporário para validação
            temp_config = config_service.get_config()
            temp_config.search_interval = int(self.config_fields["search_interval"].value)
            temp_config.discount_threshold = float(self.config_fields["discount_threshold"].value)
            temp_config.commission_threshold = float(self.config_fields["commission_threshold"].value)
            temp_config.max_products = int(self.config_fields["max_products"].value)
            temp_config.telegram_chat_id = self.config_fields["telegram_chat_id"].value
            temp_config.telegram_bot_token = self.config_fields["telegram_bot_token"].value
            
            # Valida
            is_valid, message = config_service.validate_config(temp_config)
            if is_valid:
                self._snack("Configurações válidas!")
            else:
                self._snack(f"Erro de validação: {message}", ok=False)
                
        except ValueError as e:
            self._snack("Erro: Valores inválidos nos campos", ok=False)
        except Exception as e:
            self._snack(f"Erro: {str(e)}", ok=False)
    
    def _start_system(self, _):
        """Inicia o sistema"""
        if control_service.start_system():
            self._snack("Sistema iniciado com sucesso!")
        else:
            self._snack("Erro ao iniciar sistema", ok=False)
    
    def _stop_system(self, _):
        """Para o sistema"""
        if control_service.stop_system():
            self._snack("Sistema parado com sucesso!")
        else:
            self._snack("Erro ao parar sistema", ok=False)
    
    def _force_collection(self, _):
        """Força coleta imediata"""
        if control_service.force_collection():
            self._snack("Coleta forçada iniciada!")
        else:
            self._snack("Erro na coleta forçada", ok=False)
    
    def _check_health(self, _):
        """Verifica saúde do sistema"""
        health = control_service.check_health()
        message = f"Status: {health['status']} - {health['message']}"
        
        if health['healthy']:
            self._snack(message)
        else:
            self._snack(message, ok=False)
    
    def _reload_logs(self, _=None):
        from pathlib import Path
        p = Path("logs/dashboard.log")
        try:
            txt = p.read_text(encoding="utf-8") if p.exists() else "[INFO] Arquivo de log não encontrado. Sistema iniciando...\n"
            if hasattr(self, "logs_text"):
                self.logs_text.value = txt
            elif hasattr(self, "logs_lv"):
                self.logs_lv.controls.clear()
                for line in txt.splitlines()[-500:]:
                    self.logs_lv.controls.append(ft.Text(line, color=self.t.text))
            self.page.update()
            self._snack("Logs recarregados!")
        except Exception as e:
            self._snack(f"Erro: {e}", ok=False)

    def _open_logs_folder(self, _=None):
        import os, sys, subprocess
        from pathlib import Path
        folder = str(Path("logs").resolve())
        Path(folder).mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            self._snack("Pasta de logs aberta!")
        except Exception as e:
            self._snack(f"Erro ao abrir pasta: {e}", ok=False)

    def _clear_logs(self, _=None):
        from pathlib import Path
        p = Path("logs/dashboard.log")
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("", encoding="utf-8")
            if hasattr(self, "logs_text"):
                self.logs_text.value = "[INFO] Logs limpos.\n"
            self.page.update()
            self._snack("Logs limpos!")
        except Exception as e:
            self._snack(f"Erro: {e}", ok=False)
    

    
    # =========================
    # PERIOD FILTERS & METRICS
    # =========================

    # dicionário para manter referências dos chips
    period_chips: dict[str, ft.Chip] = {}

    def _make_chip(self, key: str, label: str) -> ft.Chip:
        ch = ft.Chip(
            label=ft.Text(label),                       # Chip usa 'label', não 'text'
            selected=(key == self.state.range_key),
            on_select=lambda e, k=key: self._change_period(k),
        )
        self.period_chips[key] = ch
        return ch

    def _recolor_period_chips(self) -> None:
        if not getattr(self, "period_chips", None):
            return
        for _, ch in self.period_chips.items():
            sel = ch.selected
            try:
                ch.bgcolor = self.t.primary if sel else self.t.surface
                if isinstance(ch.label, ft.Text):
                    ch.label.color = self.t.on_primary if sel else self.t.text
                    ch.label.weight = ft.FontWeight.W_700 if sel else None
                ch.side = ft.BorderSide(0 if sel else 1, "transparent" if sel else self.t.border)
            except Exception:
                pass

    def _change_period(self, period: str) -> None:
        # NÃO chame on_period_change: ela não existe.
        if period not in ("24h", "7d", "30d", "all"):
            return
        # feedback visual imediato
        for k, ch in self.period_chips.items():
            ch.selected = (k == period)
        self.state.range_key = period
        self._recolor_period_chips()
        # carrega métricas
        self._load_metrics(period)

    def _show_loading_ui(self) -> None:
        # skeletons nos cards
        if hasattr(self, "metric_cards"):
            self.metric_cards.controls.clear()
            for _ in range(4):
                self.metric_cards.controls.append(create_skeleton_card(self.t))
        # spinner no gráfico
        if getattr(self, "chart_container", None):
            self.chart_container.content = ft.Row(
                [ft.ProgressRing(), ft.Text("Carregando...", color=self.t.text_muted)],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        self.page.update()

    def _load_metrics(self, period: str | None = None) -> None:
        import threading
        period = period or self.state.range_key
        # anti-stale
        if not hasattr(self, "_req_seq"):
            self._req_seq = 0
        self._req_seq += 1
        req_id = self._req_seq
        self._show_loading_ui()

        def work() -> None:
            data = metrics_service.get_metrics(period)
            # Usa uma abordagem compatível com versões mais antigas do Flet
            try:
                # Tenta usar call_from_thread se disponível
                if hasattr(self.page, 'call_from_thread'):
                    self.page.call_from_thread(lambda: self._on_metrics_loaded(req_id, period, data))
                else:
                    # Fallback para versões mais antigas - executa diretamente
                    self._on_metrics_loaded(req_id, period, data)
            except Exception as e:
                print(f"Erro ao atualizar UI: {e}")
                # Fallback direto
                self._on_metrics_loaded(req_id, period, data)

        threading.Thread(target=work, daemon=True).start()

    def _on_metrics_loaded(self, req_id: int, period: str, data: dict) -> None:
        # ignora respostas antigas
        if req_id != getattr(self, "_req_seq", 0):
            return
        self._update_metrics_ui(data)
        self._recolor_chart()

    # =========================
    # THEME HELPERS
    # =========================

    def _recolor_chart(self) -> None:
        if not getattr(self, "chart_container", None) or not getattr(self.chart_container, "content", None):
            return
        ch = self.chart_container.content
        if isinstance(ch, ft.BarChart):
            ch.bgcolor = self.t.surface
            try:
                ch.left_axis.label_style = ft.TextStyle(color=self.t.text_muted)
                ch.bottom_axis.label_style = ft.TextStyle(color=self.t.text_muted)
            except Exception:
                pass
            for g in ch.bar_groups or []:
                for r in getattr(g, "bar_rods", []):
                    r.color = self.t.primary

    def apply_theme(self) -> None:
        # atualiza tokens pelo tema atual
        self.t = tokens("dark" if self.page.theme_mode == ft.ThemeMode.DARK else "light")

        # header
        if getattr(self, "header_container", None):
            self.header_container.bgcolor = self.t.surface
        if getattr(self, "header_title", None):
            self.header_title.color = self.t.text
        if getattr(self, "theme_label", None):
            self.theme_label.value = f"Tema: {self.state.theme_mode.title()}"
            self.theme_label.color = self.t.text_muted
        if getattr(self, "theme_btn", None):
            self.theme_btn.icon = "dark_mode" if self.state.theme_mode == "light" else "light_mode"
            self.theme_btn.style = ft.ButtonStyle(color={ft.ControlState.DEFAULT: self.t.text})

        # cards
        if hasattr(self, "metric_cards"):
            for c in getattr(self.metric_cards, "controls", []):
                c.bgcolor = self.t.surface
                try:
                    c.border = ft.border.all(1, self.t.border)
                except Exception:
                    pass

        # containers grandes
        for cont in (getattr(self, "chart_container", None), getattr(self, "logs_container", None)):
            if cont:
                cont.bgcolor = self.t.surface
                try:
                    cont.border = ft.border.all(1, self.t.border)
                except Exception:
                    pass

        # toolbar de logs
        for b in (getattr(self, "btn_reload", None), getattr(self, "btn_open", None), getattr(self, "btn_clear", None)):
            if b:
                b.style = ft.ButtonStyle(
                    color={ft.ControlState.DEFAULT: self.t.text},
                    side={ft.ControlState.DEFAULT: ft.BorderSide(1, self.t.border)},
                    shape=ft.RoundedRectangleBorder(radius=8),
                )

        # chips e gráfico
        self._recolor_period_chips()
        self._recolor_chart()
        self.page.update()

    def toggle_theme(self, _=None) -> None:
        self.state.theme_mode = "dark" if self.state.theme_mode == "light" else "light"
        self.page.theme_mode = ft.ThemeMode.DARK if self.state.theme_mode == "dark" else ft.ThemeMode.LIGHT
        self.apply_theme()

    # =========================
    # LOGS TOOLBAR (resiliente)
    # =========================

    def _snack(self, msg: str, ok: bool = True) -> None:
        try:
            sb = ft.SnackBar(ft.Text(msg))
            sb.bgcolor = "#16A34A" if ok else "#DC2626"
            self.page.snack_bar = sb
            self.page.snack_bar.open = True
            self.page.update()
        except Exception:
            print(f"[SNACK] {msg}")

    def _reload_logs(self, _=None) -> None:
        from pathlib import Path
        p = Path("logs/dashboard.log")
        try:
            txt = p.read_text(encoding="utf-8") if p.exists() else "[INFO] Arquivo de log não encontrado. Sistema iniciando...\n"
            if hasattr(self, "logs_text"):
                self.logs_text.value = txt
            elif hasattr(self, "logs_lv"):
                self.logs_lv.controls.clear()
                for line in txt.splitlines()[-500:]:
                    self.logs_lv.controls.append(ft.Text(line, color=self.t.text))
            self.page.update()
            self._snack("Logs recarregados!")
        except Exception as e:
            self._snack(f"Erro: {e}", ok=False)

    def _open_logs_folder(self, _=None) -> None:
        import os, sys, subprocess
        from pathlib import Path
        folder = str(Path("logs").resolve())
        Path(folder).mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            self._snack("Pasta de logs aberta!")
        except Exception as e:
            self._snack(f"Erro ao abrir pasta: {e}", ok=False)

    def _clear_logs(self, _=None) -> None:
        from pathlib import Path
        p = Path("logs/dashboard.log")
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("", encoding="utf-8")
            if hasattr(self, "logs_text"):
                self.logs_text.value = "[INFO] Logs limpos.\n"
            self.page.update()
            self._snack("Logs limpos!")
        except Exception as e:
            self._snack(f"Erro: {e}", ok=False)

def flet_main(page: ft.Page):
    """Função principal do Flet"""
    app = Dashboard(page)
    app.build()

def parse_args():
    """Parse argumentos da linha de comando"""
    p = argparse.ArgumentParser()
    p.add_argument("--host", default=os.environ.get("DASHBOARD_HOST", "127.0.0.1"))
    p.add_argument("--port", type=int, default=int(os.environ.get("DASHBOARD_PORT", "8550")))
    p.add_argument("--headless", action="store_true", help="Executar como web server headless")
    p.add_argument("--desktop", action="store_true", help="Abrir janela desktop nativa")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    if args.desktop:
        # Janela nativa (Flutter)
        ft.app(target=flet_main, assets_dir=None)
    else:
        # Server web (para o supervisor)
        ft.app(target=flet_main, view=None, host=args.host, port=args.port)
