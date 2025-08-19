# app/dashboard.py
from __future__ import annotations
import flet as ft
import sys
import os
import random
import asyncio
from datetime import datetime, timezone

# Determinismo para CI: congelar seed e tempo
SEED = int(os.getenv("GG_SEED", "1337"))
random.seed(SEED)

def now():
    """Retorna tempo atual ou tempo congelado para CI"""
    freeze = os.getenv("GG_FREEZE_TIME")  # ex: 2025-01-01T00:00:00Z
    if freeze:
        return datetime.fromisoformat(freeze.replace("Z","+00:00"))
    return datetime.now(timezone.utc)

# ---------- Design tokens ----------
SPACING = {
    "small": 8,
    "medium": 16,
    "large": 24,
    "xlarge": 32
}

RADIUS = 12
CARD_HEIGHT = 120

# ---------- Importações core ----------
try:
    from core.data_service import DataService
    from core.storage import config_storage
    from core.csv_exporter import csv_exporter
    from core.live_logs import live_log_reader
    from core.models import Periodo
except ImportError:
    print("Módulos core não encontrados, usando mock data")
    DataService = None
    config_storage = None
    csv_exporter = None
    live_log_reader = None

# ---------- Estado global ----------
data_service = DataService() if DataService else None
current_ofertas = []
current_periodo = "7d"  # Valor padrão
current_metrics = None

# ---------- Componentes UI ----------
def build_header(page: ft.Page) -> ft.Container:
    """Header com título e ações"""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    "Garimpeiro Geek - Dashboard",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.ON_SURFACE
                ),
                ft.Container(expand=True),  # Spacer
                ft.IconButton(
                    icon=ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.LIGHT_MODE,
                    on_click=lambda e: toggle_theme(page),
                    tooltip="Alternar tema"
                ),
                ft.FilledButton(
                    "Exportar CSV",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=lambda e: export_csv_clicked(page),
                    key="csv_botao_presente"
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        padding=ft.padding.all(SPACING["large"]),
        bgcolor=ft.Colors.SURFACE,
        border_radius=RADIUS
    )

def build_metric_card(title: str, value: str, icon: str, key: str = None) -> ft.Container:
    """Card de métrica individual"""
    return ft.Container(
        key=key,
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(
                        icon,
                        size=32,
                        color=ft.Colors.PRIMARY
                    ),
                    padding=ft.padding.all(SPACING["medium"])
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            title,
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=ft.Colors.ON_SURFACE_VARIANT
                        ),
                        ft.Text(
                            value,
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ON_SURFACE
                        )
                    ],
                    spacing=SPACING["small"]
                )
            ],
            alignment=ft.MainAxisAlignment.START
        ),
        height=CARD_HEIGHT,
        padding=ft.padding.all(SPACING["medium"]),
        bgcolor=ft.Colors.SURFACE,
        border_radius=RADIUS,
        border=ft.border.all(1, ft.Colors.OUTLINE)
    )

def build_metrics_row() -> ft.ResponsiveRow:
    """Linha responsiva com cards de métricas"""
    return ft.ResponsiveRow(
        controls=[
            build_metric_card(
                "Ofertas",
                str(current_metrics.total_ofertas if current_metrics else 0),
                ft.Icons.SHOPPING_CART,
                "card_ofertas"
            ),
            build_metric_card(
                "Lojas Ativas",
                str(current_metrics.lojas_ativas if current_metrics else 0),
                ft.Icons.STORE,
                "card_lojas"
            ),
            build_metric_card(
                "Preço Médio",
                current_metrics.preco_medio_formatado() if current_metrics else "R$ 0,00",
                ft.Icons.ATTACH_MONEY,
                "card_preco"
            ),
            build_metric_card(
                "Período",
                current_periodo.upper(),
                ft.Icons.SCHEDULE,
                "card_periodo"
            )
        ],
        spacing=SPACING["medium"]
    )

def build_period_filters(page: ft.Page) -> ft.Container:
    """Filtros de período"""
    def period_changed(e):
        global current_periodo
        current_periodo = e.control.data
        asyncio.create_task(load_data_for_period(current_periodo, page))
    
    return ft.Container(
        key="filters",
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.FILTER_LIST),
                        ft.Text("Filtros de Período", weight=ft.FontWeight.W_500)
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.CupertinoButton(
                            content=ft.Text("24h"),
                            data="24h",
                            on_click=period_changed,
                            color=ft.Colors.PRIMARY if current_periodo == "24h" else ft.Colors.ON_SURFACE
                        ),
                        ft.CupertinoButton(
                            content=ft.Text("7 dias"),
                            data="7d",
                            on_click=period_changed,
                            color=ft.Colors.PRIMARY if current_periodo == "7d" else ft.Colors.ON_SURFACE
                        ),
                        ft.CupertinoButton(
                            content=ft.Text("30 dias"),
                            data="30d",
                            on_click=period_changed,
                            color=ft.Colors.PRIMARY if current_periodo == "30d" else ft.Colors.ON_SURFACE
                        ),
                        ft.CupertinoButton(
                            content=ft.Text("Tudo"),
                            data="all",
                            on_click=period_changed,
                            color=ft.Colors.PRIMARY if current_periodo == "all" else ft.Colors.ON_SURFACE
                        )
                    ],
                    spacing=SPACING["small"]
                )
            ],
            spacing=SPACING["medium"]
        ),
        padding=ft.padding.all(SPACING["large"]),
        bgcolor=ft.Colors.SURFACE,
        border_radius=RADIUS
    )

def build_chart_panel() -> ft.Container:
    """Painel do gráfico"""
    if not current_metrics or not current_metrics.distribuicao_lojas:
        return ft.Container(
            key="chart",
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Distribuição por Loja",
                        size=18,
                        weight=ft.FontWeight.W_500
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Nenhum dado disponível",
                            color=ft.Colors.ON_SURFACE_VARIANT
                        ),
                        padding=ft.padding.all(SPACING["large"])
                    )
                ],
                spacing=SPACING["medium"]
            ),
            height=320,
            padding=ft.padding.all(SPACING["large"]),
            bgcolor=ft.Colors.SURFACE,
            border_radius=RADIUS,
            border=ft.border.all(1, ft.Colors.OUTLINE)
        )
    
    # Criar gráfico de barras simples
    chart_items = []
    for loja, count in current_metrics.distribuicao_lojas.items():
        chart_items.append(
            ft.Row(
                controls=[
                    ft.Text(loja, size=14, weight=ft.FontWeight.W_500),
                    ft.Container(expand=True),
                    ft.Text(str(count), size=16, weight=ft.FontWeight.BOLD)
                ],
                spacing=SPACING["medium"]
            )
        )
    
    return ft.Container(
        key="chart",
        content=ft.Column(
            controls=[
                ft.Text(
                    "Distribuição por Loja",
                    size=18,
                    weight=ft.FontWeight.W_500
                ),
                ft.Container(
                    content=ft.Column(
                        controls=chart_items,
                        spacing=SPACING["small"]
                    ),
                    padding=ft.padding.all(SPACING["medium"])
                )
            ],
            spacing=SPACING["medium"]
        ),
        height=320,
        padding=ft.padding.all(SPACING["large"]),
        bgcolor=ft.Colors.SURFACE,
        border_radius=RADIUS,
        border=ft.border.all(1, ft.Colors.OUTLINE)
    )

def build_logs_panel(page: ft.Page) -> ft.Container:
    """Painel de logs ao vivo"""
    logs_list = ft.ListView(
        spacing=SPACING["small"],
        height=300,
        auto_scroll=True,
        key="logs_list"
    )
    
    # Carregar logs iniciais
    if live_log_reader:
        initial_logs = live_log_reader.get_current_logs()
        for log_line in initial_logs:
            logs_list.controls.append(
                ft.Text(
                    log_line.strip(),
                    size=12,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    font_family="monospace"
                )
            )
    
    return ft.Container(
        key="logs",
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.LIST_ALT),
                        ft.Text("Logs do Sistema", weight=ft.FontWeight.W_500),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            on_click=lambda e: refresh_logs(page),
                            tooltip="Atualizar logs"
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLEAR,
                            on_click=lambda e: clear_logs(page),
                            tooltip="Limpar logs"
                        )
                    ]
                ),
                ft.Container(
                    content=logs_list,
                    expand=True
                )
            ],
            spacing=SPACING["medium"]
        ),
        padding=ft.padding.all(SPACING["large"]),
        bgcolor=ft.Colors.SURFACE,
        border_radius=RADIUS,
        border=ft.border.all(1, ft.Colors.OUTLINE)
    )

def build_tabs(page: ft.Page) -> ft.Tabs:
    """Abas do dashboard"""
    return ft.Tabs(
        key="tabs",
        selected_index=0,
        tabs=[
            ft.Tab(
                text="Logs",
                content=ft.Column(
                    controls=[
                        build_metrics_row(),
                        build_period_filters(page),
                        build_chart_panel(),
                        build_logs_panel(page)
                    ],
                    spacing=SPACING["large"]
                )
            ),
            ft.Tab(
                text="Configurações",
                content=ft.Container(
                    content=ft.Text("Configurações em desenvolvimento..."),
                    padding=ft.padding.all(SPACING["large"])
                )
            ),
            ft.Tab(
                text="Controles",
                content=ft.Container(
                    content=ft.Text("Controles em desenvolvimento..."),
                    padding=ft.padding.all(SPACING["large"])
                )
            )
        ]
    )

# ---------- Funções de dados ----------
async def load_data_for_period(periodo: str, page: ft.Page):
    """Carrega dados para o período especificado"""
    global current_ofertas, current_metrics, current_periodo
    
    try:
        if data_service:
            current_ofertas = await data_service.load_ofertas(periodo)
            current_metrics = data_service.get_metrics_snapshot(current_ofertas, periodo)
        else:
            # Mock data
            current_ofertas = []
            current_metrics = None
        
        current_periodo = periodo
        
        # Atualizar UI
        await update_ui(page)
        
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        # Mostrar erro na UI
        if page:
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Erro ao carregar dados: {e}"))
            )

async def update_ui(page: ft.Page):
    """Atualiza a interface do usuário"""
    if not page:
        return
    
    try:
        # Atualizar cards de métricas
        metrics_row = build_metrics_row()
        
        # Atualizar gráfico
        chart_panel = build_chart_panel()
        
        # Atualizar filtros
        filters_panel = build_period_filters(page)
        
        # Encontrar e atualizar controles na página
        for control in page.controls:
            if isinstance(control, ft.Column):
                for child in control.controls:
                    if hasattr(child, 'key') and child.key == "metrics_row":
                        child.controls = metrics_row.controls
                    elif hasattr(child, 'key') and child.key == "chart":
                        child.controls = chart_panel.controls
                    elif hasattr(child, 'key') and child.key == "filters":
                        child.controls = filters_panel.controls
        
        await page.update_async()
        
    except Exception as e:
        print(f"Erro ao atualizar UI: {e}")

# ---------- Funções de eventos ----------
def toggle_theme(page: ft.Page):
    """Alterna entre tema claro e escuro"""
    if page.theme_mode == ft.ThemeMode.LIGHT:
        page.theme_mode = ft.ThemeMode.DARK
        page.update()
    else:
        page.theme_mode = ft.ThemeMode.LIGHT
        page.update()

async def export_csv_clicked(page: ft.Page):
    """Exporta dados para CSV"""
    try:
        if csv_exporter and current_ofertas:
            filepath = csv_exporter.export_ofertas(current_ofertas)
            
            # Mostrar notificação de sucesso
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"CSV exportado com sucesso: {filepath}"),
                    action="Abrir pasta",
                    on_action=lambda e: open_export_folder()
                )
            )
        else:
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Nenhum dado para exportar"))
            )
    except Exception as e:
        page.show_snack_bar(
            ft.SnackBar(content=ft.Text(f"Erro ao exportar CSV: {e}"))
        )

def open_export_folder():
    """Abre a pasta de exportação"""
    try:
        import subprocess
        import platform
        
        if platform.system() == "Windows":
            subprocess.run(["explorer", csv_exporter.get_export_path()])
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", csv_exporter.get_export_path()])
        else:  # Linux
            subprocess.run(["xdg-open", csv_exporter.get_export_path()])
    except Exception as e:
        print(f"Erro ao abrir pasta: {e}")

async def refresh_logs(page: ft.Page):
    """Atualiza logs manualmente"""
    if live_log_reader:
        logs = live_log_reader.get_current_logs()
        # Atualizar lista de logs na UI
        await update_logs_ui(page, logs)

async def clear_logs(page: ft.Page):
    """Limpa logs"""
    if live_log_reader:
        live_log_reader.clear_buffer()
        await update_logs_ui(page, ["Logs limpos..."])

async def update_logs_ui(page: ft.Page, logs: list):
    """Atualiza a UI dos logs"""
    try:
        # Encontrar lista de logs e atualizar
        for control in page.controls:
            if isinstance(control, ft.Column):
                for child in control.controls:
                    if hasattr(child, 'key') and child.key == "logs":
                        for grandchild in child.controls:
                            if hasattr(grandchild, 'key') and grandchild.key == "logs_list":
                                grandchild.controls.clear()
                                for log_line in logs:
                                    grandchild.controls.append(
                                        ft.Text(
                                            log_line.strip(),
                                            size=12,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                            font_family="monospace"
                                        )
                                    )
                                break
        
        page.update()
        
    except Exception as e:
        print(f"Erro ao atualizar logs UI: {e}")

# ---------- Função principal ----------
async def main(page: ft.Page):
    """Função principal do dashboard"""
    global current_periodo
    
    # Configurações da página
    page.title = "Garimpeiro Geek - Dashboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = SPACING["medium"]
    page.spacing = SPACING["large"]
    
    # Carregar preferências do usuário
    if config_storage:
        theme_pref = config_storage.get_preference("theme", "system")
        if theme_pref == "light":
            page.theme_mode = ft.ThemeMode.LIGHT
        elif theme_pref == "dark":
            page.theme_mode = ft.ThemeMode.DARK
        
        default_period = config_storage.get_preference("default_period", "7d")
        current_periodo = default_period
    
    # Construir interface
    page.add(
        build_header(page),
        build_tabs(page)
    )
    
    # Carregar dados iniciais
    await load_data_for_period(current_periodo, page)
    
    # Iniciar monitoramento de logs
    if live_log_reader:
        await live_log_reader.start_monitoring()
        
        # Registrar callback para atualizar logs
        async def update_logs_callback(logs):
            await update_logs_ui(page, logs)
        
        live_log_reader.add_callback(update_logs_callback)
    
    # Verificar se é modo reporter
    if "--report" in sys.argv:
        await run_reporter_mode(page)

async def run_reporter_mode(page: ft.Page):
    """Executa em modo reporter para CI"""
    try:
        # Adicionar diretório pai ao path para importar diagnostics
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from diagnostics.ui_reporter import dump_report
        
        # Aguardar um pouco para UI carregar
        await asyncio.sleep(1)
        
        # Executar UI Reporter
        summary = dump_report(page)
        
        # Exportar JUnit se solicitado
        want_junit = ("--junit" in sys.argv) or os.getenv("GG_JUNIT") == "1"
        if want_junit:
            try:
                from diagnostics.ui_reporter import emit_junit_xml
                junit_path = os.getenv("GG_JUNIT_PATH", "ui_reporter.junit.xml")
                emit_junit_xml(summary, junit_path)
                print(f"[UI-REPORTER] JUnit XML salvo em: {junit_path}")
            except Exception as e:
                print(f"[UI-REPORTER] Erro ao gerar JUnit: {e}")
        
        # Exportar CSV determinístico se solicitado
        if csv_exporter:
            try:
                csv_path = csv_exporter.export_deterministic_csv(current_periodo)
                print(f"[UI-REPORTER] CSV determinístico salvo em: {csv_path}")
            except Exception as e:
                print(f"[UI-REPORTER] Erro ao gerar CSV: {e}")
        
        # Sair se solicitado
        if "--exit-after-report" in sys.argv:
            if "--strict" in sys.argv:
                # Verificar se todos os checks passaram
                checks = summary.get("checks", {})
                if not all(checks.values()):
                    print("❌ Alguns checks falharam no modo strict")
                    os._exit(1)
                else:
                    print("✅ Todos os checks passaram no modo strict")
                    os._exit(0)
            else:
                os._exit(0)
                
    except Exception as e:
        print(f"Erro no modo reporter: {e}")
        if "--strict" in sys.argv:
            os._exit(1)

if __name__ == "__main__":
    ft.app(target=main) 
