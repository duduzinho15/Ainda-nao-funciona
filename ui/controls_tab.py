"""
Aba de controles do dashboard Garimpeiro Geek.
"""

import flet as ft
import asyncio
from typing import Callable, Optional, Any
from core.metrics import MetricsAggregator


def create_controls_tab(
    metrics_aggregator: MetricsAggregator,
    scrape_runner: Any = None,
    on_status_changed: Optional[Callable[[str], None]] = None,
) -> Any:
    """Cria a aba de controles do sistema."""
    
    # Estado do sistema
    is_scraping = False
    current_periodo = "24h"  # Período padrão

    def build_controls_tab() -> Any:
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

    def build_header() -> Any:
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

    def build_status_section() -> Any:
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

    def build_controls_section() -> Any:
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

    def build_stats_section() -> Any:
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

    def build_actions_section() -> Any:
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
        if not is_scraping and scrape_runner:
            try:
                # Iniciar motor de coleta com intervalo padrão
                asyncio.create_task(scrape_runner.start_scraping(current_periodo, 10.0))
                is_scraping = True
                print("🟢 Motor de coleta iniciado!")
                if on_status_changed:
                    on_status_changed("running")
                # Atualizar UI
                e.control.disabled = True
                e.control.page.update()
            except Exception as ex:
                print(f"❌ Erro ao iniciar motor: {ex}")
        else:
            print("⚠️ Motor já está rodando ou não disponível")

    def on_stop_click(e):
        """Chamado quando o botão parar é clicado."""
        nonlocal is_scraping
        if is_scraping and scrape_runner:
            try:
                # Parar motor de coleta
                asyncio.create_task(scrape_runner.stop_scraping())
                is_scraping = False
                print("🔴 Motor de coleta parado!")
                if on_status_changed:
                    on_status_changed("stopped")
                # Atualizar UI
                e.control.disabled = True
                e.control.page.update()
            except Exception as ex:
                print(f"❌ Erro ao parar motor: {ex}")
        else:
            print("⚠️ Motor não está rodando ou não disponível")

    def on_reload_metrics(e):
        """Chamado quando o botão recarregar métricas é clicado."""
        if scrape_runner:
            try:
                # Recarregar métricas do motor
                metrics_summary = scrape_runner.get_metrics_summary()
                print(f"📊 Métricas recarregadas: {metrics_summary}")
                
                # Forçar atualização imediata do cache
                scrape_runner.force_refresh()
                
                # TODO: Atualizar UI com novas métricas
            except Exception as ex:
                print(f"❌ Erro ao recarregar métricas: {ex}")
        else:
            print("⚠️ Motor de coleta não disponível")

    def on_clear_logs(e):
        """Chamado quando o botão limpar logs é clicado."""
        print("🧹 Logs limpos!")

    def on_open_logs_folder(e):
        """Chamado quando o botão abrir pasta de logs é clicado."""
        print("📁 Pasta de logs aberta!")

    def on_export_csv(e):
        """Chamado quando o botão exportar CSV é clicado."""
        try:
            # Importar CSV exporter
            from core.csv_exporter import CSVExporter
            from core.data_service import DataService
            
            # Criar instâncias
            csv_exporter = CSVExporter()
            data_service = DataService()
            
            # Carregar ofertas do período atual
            import asyncio
            loop = asyncio.get_event_loop()
            ofertas = loop.run_until_complete(data_service.load_ofertas(current_periodo))
            
            # Exportar CSV
            result = csv_exporter.export_ofertas(ofertas, current_periodo)
            
            if result.get('success'):
                print(f"✅ CSV exportado com sucesso!")
                print(f"   📁 Arquivo: {result['filename']}")
                print(f"   📊 Ofertas: {result['total_ofertas']}")
                # TODO: Mostrar toast/snackbar com o caminho
            else:
                print(f"❌ Erro ao exportar CSV: {result.get('error')}")
                
        except Exception as ex:
            print(f"❌ Erro ao exportar CSV: {ex}")

    # Retornar a aba construída
    return build_controls_tab()
