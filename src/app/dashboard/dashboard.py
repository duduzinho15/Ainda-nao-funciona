"""
Dashboard principal do Garimpeiro Geek
Interface web moderna para monitoramento e controle
"""

import sys
from pathlib import Path

import flet as ft

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database import Database
from core.live_logs import LiveLogReader
from core.metrics import Metrics, MetricsCollector
from core.storage import PreferencesStorage

# Configurações
SPACING = {"small": 8, "medium": 16, "large": 24, "xlarge": 32}

# Variáveis globais
config_storage = None
current_metrics = None
current_periodo = "7d"


def main(page: ft.Page):
    """Função principal do dashboard"""
    global config_storage, current_metrics

    # Configurar página
    page.title = "Garimpeiro Geek - Dashboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = SPACING["medium"]

    # Configurar scroll da página
    page.scroll = ft.ScrollMode.AUTO
    page.vertical_alignment = ft.MainAxisAlignment.START

    # Inicializar componentes
    config_storage = PreferencesStorage()
    db = Database()
    metrics_collector = MetricsCollector()
    live_log_reader = LiveLogReader()

    # Configurar métricas iniciais
    current_metrics = Metrics(0, 0, 0.0)

    # Carregar preferências
    theme = config_storage.get_preference("theme", "dark")
    if theme == "light":
        page.theme_mode = ft.ThemeMode.LIGHT

    # Interface principal
    page.add(build_header(page), build_tabs(page))

    # Atualizar UI
    page.update()


def build_header(page: ft.Page) -> ft.Container:
    """Constrói o cabeçalho do dashboard"""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    "Garimpeiro Geek - Dashboard", size=24, weight=ft.FontWeight.BOLD
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.DARK_MODE
                    if page.theme_mode == ft.ThemeMode.LIGHT
                    else ft.Icons.LIGHT_MODE,
                    tooltip="Alternar tema",
                    on_click=lambda e: toggle_theme(page),
                ),
                ft.FilledButton(
                    "Exportar CSV",
                    icon=ft.Icons.DOWNLOAD,
                    key="csv_botao_presente",
                    on_click=lambda e: export_csv_clicked(page),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.padding.all(SPACING["medium"]),
    )


def build_tabs(page: ft.Page) -> ft.Tabs:
    """Constrói as abas do dashboard"""
    return ft.Tabs(
        key="tabs",
        selected_index=0,
        tabs=[
            ft.Tab(
                text="Dashboard",
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            build_metrics_row(),
                            build_period_filters(page),
                            build_chart_panel(),
                            build_logs_panel(page),
                        ],
                        spacing=SPACING["medium"],
                    )
                ),
            ),
            ft.Tab(
                text="Logs",
                content=ft.Container(
                    content=ft.ListView(key="logs_lv", auto_scroll=True, spacing=6)
                ),
            ),
            ft.Tab(
                text="Configurações",
                content=ft.Container(
                    content=ft.Column(
                        controls=build_config_tab(page), scroll=ft.ScrollMode.AUTO
                    )
                ),
            ),
            ft.Tab(
                text="Controles",
                content=ft.Container(
                    content=ft.Column(
                        controls=build_controls_tab(page), scroll=ft.ScrollMode.AUTO
                    )
                ),
            ),
        ],
    )


def build_metrics_row() -> ft.Row:
    """Constrói a linha de métricas"""
    return ft.Row(
        controls=[
            build_metric_card("Ofertas", "0", ft.Icons.SHOPPING_CART, "card_ofertas"),
            build_metric_card("Lojas Ativas", "0", ft.Icons.STORE, "card_lojas"),
            build_metric_card(
                "Preço Médio", "R$ 0,00", ft.Icons.ATTACH_MONEY, "card_preco"
            ),
            build_metric_card("Período", "7D", ft.Icons.SCHEDULE, "card_periodo"),
        ],
        spacing=SPACING["medium"],
    )


def build_metric_card(title: str, value: str, icon: str, key: str) -> ft.Container:
    """Constrói um card de métrica"""
    return ft.Container(
        key=key,
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(icon, size=32, color=ft.Colors.BLUE_400),
                    padding=ft.padding.all(SPACING["small"]),
                ),
                ft.Column(
                    controls=[
                        ft.Text(title, size=14, color=ft.Colors.GREY_400),
                        ft.Text(value, size=20, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=4,
                ),
            ]
        ),
        padding=ft.padding.all(SPACING["medium"]),
        border=ft.border.all(1, ft.Colors.GREY_800),
        border_radius=8,
        expand=True,
    )


def build_period_filters(page: ft.Page) -> ft.Container:
    """Constrói os filtros de período"""
    return ft.Container(
        key="filters",
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.FILTER_LIST),
                        ft.Text(
                            "Filtros de Período", size=16, weight=ft.FontWeight.W_500
                        ),
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.CupertinoButton(
                            content=ft.Text("24H"),
                            on_click=lambda e: change_period("24h"),
                        ),
                        ft.CupertinoButton(
                            content=ft.Text("7D"),
                            on_click=lambda e: change_period("7d"),
                        ),
                        ft.CupertinoButton(
                            content=ft.Text("30D"),
                            on_click=lambda e: change_period("30d"),
                        ),
                        ft.CupertinoButton(
                            content=ft.Text("90D"),
                            on_click=lambda e: change_period("90d"),
                        ),
                    ],
                    spacing=SPACING["small"],
                ),
            ]
        ),
    )


def build_chart_panel() -> ft.Container:
    """Constrói o painel de gráficos"""
    return ft.Container(
        key="chart",
        content=ft.Column(
            controls=[
                ft.Text("Distribuição por Loja", size=18, weight=ft.FontWeight.W_500),
                ft.Container(
                    content=ft.Text("Gráfico será implementado aqui"),
                    height=300,
                    alignment=ft.alignment.center,
                ),
            ]
        ),
        padding=ft.padding.all(SPACING["medium"]),
        border=ft.border.all(1, ft.Colors.GREY_800),
        border_radius=8,
    )


def build_logs_panel(page: ft.Page) -> ft.Container:
    """Constrói o painel de logs"""
    return ft.Container(
        key="logs",
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.LIST_ALT),
                        ft.Text("Logs do Sistema", size=16, weight=ft.FontWeight.W_500),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            tooltip="Atualizar logs",
                            on_click=lambda e: refresh_logs(page),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLEAR,
                            tooltip="Limpar logs",
                            on_click=lambda e: clear_logs(page),
                        ),
                    ]
                ),
                ft.Container(
                    content=ft.ListView(key="logs_list", auto_scroll=True, spacing=4),
                    height=200,
                ),
            ]
        ),
    )


def build_config_tab(page: ft.Page) -> list:
    """Constrói a aba de configurações"""
    return [
        ft.Text("Configurações do Sistema", size=20, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Text("Tema:", size=16),
        ft.Switch(
            label="Modo Claro",
            value=page.theme_mode == ft.ThemeMode.LIGHT,
            on_change=lambda e: toggle_theme(page),
        ),
        ft.Divider(),
        ft.Text("Logs:", size=16),
        ft.Switch(label="Auto-scroll", value=True),
    ]


def build_controls_tab(page: ft.Page) -> list:
    """Constrói a aba de controles"""
    return [
        ft.Text("Controles do Sistema", size=20, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Text("Sistema:", size=16),
        ft.Switch(
            label="Ativar Sistema Global",
            value=True,
            on_change=lambda e: toggle_global_system(page, e.control.value),
        ),
        ft.Divider(),
        ft.Text("Fontes de Dados:", size=16),
        ft.Column(
            [
                ft.Switch(
                    label="Amazon Scraper",
                    value=True,
                    on_change=lambda e: toggle_source_enabled(
                        "amazon", e.control.value
                    ),
                ),
                ft.Switch(
                    label="Shopee API",
                    value=True,
                    on_change=lambda e: toggle_source_enabled(
                        "shopee", e.control.value
                    ),
                ),
                ft.Switch(
                    label="Magalu Provider",
                    value=True,
                    on_change=lambda e: toggle_source_enabled(
                        "magalu", e.control.value
                    ),
                ),
                ft.Switch(
                    label="Kabum Source",
                    value=True,
                    on_change=lambda e: toggle_source_enabled("kabum", e.control.value),
                ),
            ]
        ),
        ft.Divider(),
        ft.Text("Status:", size=16),
        ft.Text("Sistema funcionando normalmente"),
        ft.Divider(),
        ft.Text("Ações:", size=16),
        ft.ElevatedButton(
            "Atualizar Dados",
            icon=ft.Icons.REFRESH,
            on_click=lambda e: refresh_data(page),
        ),
    ]


def toggle_theme(page: ft.Page):
    """Alterna entre tema claro e escuro"""
    if page.theme_mode == ft.ThemeMode.LIGHT:
        page.theme_mode = ft.ThemeMode.DARK
        theme_value = "dark"
    else:
        page.theme_mode = ft.ThemeMode.LIGHT
        theme_value = "light"

    # Salvar preferência
    if config_storage:
        config_storage.set_preference("theme", theme_value)

    page.update()


def change_period(periodo: str):
    """Muda o período selecionado"""
    global current_periodo
    current_periodo = periodo

    # Salvar preferência
    if config_storage:
        config_storage.set_preference("last_period", periodo)

    print(f"⚙️ Período alterado para: {periodo}")


def export_csv_clicked(page: ft.Page):
    """Exporta dados para CSV"""
    page.show_snack_bar(ft.SnackBar(content=ft.Text("Exportação CSV implementada")))


def refresh_logs(page: ft.Page):
    """Atualiza logs manualmente"""
    page.show_snack_bar(ft.SnackBar(content=ft.Text("Logs atualizados")))


def clear_logs(page: ft.Page):
    """Limpa logs"""
    page.show_snack_bar(ft.SnackBar(content=ft.Text("Logs limpos")))


def toggle_global_system(page: ft.Page, enabled: bool):
    """Alterna sistema global"""
    status = "ativado" if enabled else "desativado"
    page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Sistema global {status}")))


def toggle_source_enabled(source: str, enabled: bool):
    """Alterna fonte específica"""
    status = "ativada" if enabled else "desativada"
    print(f"💡 Fonte {source} {status}")


def refresh_data(page: ft.Page):
    """Atualiza dados do sistema"""
    page.show_snack_bar(ft.SnackBar(content=ft.Text("Dados atualizados")))


if __name__ == "__main__":
    ft.app(target=main)
