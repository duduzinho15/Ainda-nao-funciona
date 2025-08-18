"""
Aba de controles do dashboard Garimpeiro Geek.
"""

import flet as ft
from typing import Callable, Optional
from core.metrics import MetricsAggregator


def create_controls_tab(
    metrics_aggregator: MetricsAggregator,
    on_status_changed: Optional[Callable[[str], None]] = None,
) -> ft.Control:
    """Cria a aba de controles do sistema."""
    
    # Estado do sistema
    is_scraping = False

    def build_controls_tab():
        """Constrói a interface da aba."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    build_header(),
                    ft.Divider(),
                    build_status_section(),
                    ft.Divider(),
                    build_controls_section(),
                    ft.Divider(),
                    build_stats_section(),
                    ft.Divider(),
                    build_actions_section(),
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=20,
            ),
            padding=20,
        )

    def build_header() -> ft.Control:
        """Constrói o cabeçalho da aba."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "🎮 Controles do Sistema", size=24, weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        "Gerencie o sistema de scraping e visualize estatísticas",
                        size=14,
                        color=ft.colors.ON_SURFACE_VARIANT,
                    ),
                ]
            ),
            padding=ft.padding.only(bottom=20),
        )

    def build_status_section() -> ft.Control:
        """Constrói a seção de status."""
        status_indicator = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(name=ft.icons.CIRCLE, color=ft.colors.RED, size=16),
                    ft.Text("Parado", size=16, weight=ft.FontWeight.BOLD),
                ]
            ),
            padding=10,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=8,
            bgcolor=ft.colors.SURFACE_VARIANT,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("📊 Status do Sistema", size=18, weight=ft.FontWeight.BOLD),
                    status_indicator,
                ]
            ),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=8,
        )

    def build_controls_section() -> ft.Control:
        """Constrói a seção de controles principais."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("🎛️ Controles Principais", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                text="▶️ Iniciar Coleta",
                                icon=ft.icons.PLAY_ARROW,
                                on_click=on_start_click,
                                style=ft.ButtonStyle(
                                    color=ft.colors.ON_PRIMARY,
                                    bgcolor=ft.colors.PRIMARY,
                                ),
                            ),
                            ft.ElevatedButton(
                                text="⏹️ Parar Coleta",
                                icon=ft.icons.STOP,
                                on_click=on_stop_click,
                                style=ft.ButtonStyle(
                                    color=ft.colors.ON_PRIMARY,
                                    bgcolor=ft.colors.ERROR,
                                ),
                            ),
                        ],
                        spacing=20,
                    ),
                ],
                spacing=15,
            ),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=8,
        )

    def build_stats_section() -> ft.Control:
        """Constrói a seção de estatísticas."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("📈 Estatísticas", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("Total de Ofertas", size=12),
                                        ft.Text("0", size=24, weight=ft.FontWeight.BOLD),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                padding=20,
                                border=ft.border.all(1, ft.colors.OUTLINE),
                                border_radius=8,
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("Ofertas Postadas", size=12),
                                        ft.Text("0", size=24, weight=ft.FontWeight.BOLD),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                padding=20,
                                border=ft.border.all(1, ft.colors.OUTLINE),
                                border_radius=8,
                                expand=True,
                            ),
                        ],
                        spacing=20,
                    ),
                ],
                spacing=15,
            ),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=8,
        )

    def build_actions_section() -> ft.Control:
        """Constrói a seção de ações rápidas."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("⚡ Ações Rápidas", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.OutlinedButton(
                                text="🔄 Recarregar Métricas",
                                icon=ft.icons.REFRESH,
                                on_click=on_reload_metrics,
                            ),
                            ft.OutlinedButton(
                                text="🧹 Limpar Logs",
                                icon=ft.icons.CLEANING_SERVICES,
                                on_click=on_clear_logs,
                            ),
                        ],
                        spacing=20,
                    ),
                    ft.Row(
                        [
                            ft.OutlinedButton(
                                text="📁 Abrir Pasta de Logs",
                                icon=ft.icons.FOLDER_OPEN,
                                on_click=on_open_logs_folder,
                            ),
                            ft.OutlinedButton(
                                text="📊 Exportar CSV",
                                icon=ft.icons.DOWNLOAD,
                                on_click=on_export_csv,
                            ),
                        ],
                        spacing=20,
                    ),
                ],
                spacing=15,
            ),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=8,
        )

    def on_start_click(e):
        """Chamado quando o botão iniciar é clicado."""
        nonlocal is_scraping
        if not is_scraping:
            is_scraping = True
            print("🟢 Sistema iniciado!")
            if on_status_changed:
                on_status_changed("running")

    def on_stop_click(e):
        """Chamado quando o botão parar é clicado."""
        nonlocal is_scraping
        if is_scraping:
            is_scraping = False
            print("🔴 Sistema parado!")
            if on_status_changed:
                on_status_changed("stopped")

    def on_reload_metrics(e):
        """Chamado quando o botão recarregar métricas é clicado."""
        print("📊 Métricas recarregadas!")

    def on_clear_logs(e):
        """Chamado quando o botão limpar logs é clicado."""
        print("🧹 Logs limpos!")

    def on_open_logs_folder(e):
        """Chamado quando o botão abrir pasta de logs é clicado."""
        print("📁 Pasta de logs aberta!")

    def on_export_csv(e):
        """Chamado quando o botão exportar CSV é clicado."""
        print("📊 CSV exportado!")

    # Retornar a aba construída
    return build_controls_tab()
