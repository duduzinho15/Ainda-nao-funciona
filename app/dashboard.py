# app/dashboard.py
from __future__ import annotations
from typing import Callable
import flet as ft
import os, sys

# ---------- Design tokens ----------
PRIMARY = ft.Colors.BLUE
RADIUS = 16
GAP = 16

def make_theme(page: ft.Page, dark: bool) -> None:
    page.theme = ft.Theme(
        color_scheme_seed=PRIMARY,
        visual_density=ft.VisualDensity.COMFORTABLE,
        use_material3=True,
    )
    page.theme_mode = ft.ThemeMode.DARK if dark else ft.ThemeMode.LIGHT
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

# ---------- Átomos de UI ----------
def stat_card(icon: str, label: str, value: str) -> ft.Container:
    chip = ft.Container(
        width=44, height=44, bgcolor=ft.Colors.with_opacity(0.12, PRIMARY),
        border_radius=12, alignment=ft.alignment.center,
        content=ft.Icon(icon, color=PRIMARY, size=22),
    )
    return ft.Container(
        bgcolor=ft.Colors.SURFACE,
        border=ft.border.all(1, ft.Colors.with_opacity(0.06, ft.Colors.BLACK)),
        border_radius=RADIUS, padding=20,
        content=ft.Row(
            [
                chip,
                ft.Column(
                    [
                        ft.Text(label, size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text(value, size=22, weight=ft.FontWeight.W_700),
                    ],
                    spacing=4, alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=14, alignment=ft.MainAxisAlignment.START,
        ),
    )

def section(title: str, icon: str) -> ft.Column:
    return ft.Column(
        controls=[
            ft.Container(
                padding=ft.padding.only(0, 8, 0, 6),
                content=ft.Row(
                    [
                        ft.Icon(icon, size=22, color=PRIMARY),
                        ft.Text(title, size=20, weight=ft.FontWeight.W_700),
                    ],
                    spacing=8,
                ),
            ),
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
        ],
        spacing=8,
    )

def chip(text: str, selected: bool, on_click: Callable[[], None]) -> ft.CupertinoButton:
    return ft.CupertinoButton(
        text,
        on_click=lambda _: on_click(),
        bgcolor=(PRIMARY if selected else ft.Colors.with_opacity(0.06, ft.Colors.BLACK)),
        color=(ft.Colors.WHITE if selected else ft.Colors.ON_SURFACE),
        padding=ft.padding.symmetric(10, 14),
        border_radius=12,
    )

# ---------- Seções (Tabs) ----------
def logs_metrics_tab(state: dict) -> ft.Column:
    # Métricas "cards"
    cards = ft.ResponsiveRow(
        columns=12, spacing=GAP, run_spacing=GAP,
        controls=[
            ft.Container(stat_card(ft.Icons.NUMBERS, "Ofertas", "14"), col={"xs":12, "md":3}, key="card_ofertas"),
            ft.Container(stat_card(ft.Icons.STORE_MALL_DIRECTORY, "Lojas ativas", "10"), col={"xs":12, "md":3}, key="card_lojas"),
            ft.Container(stat_card(ft.Icons.PRICE_CHANGE, "Preço médio", "R$ 157,91"), col={"xs":12, "md":3}, key="card_preco"),
            ft.Container(stat_card(ft.Icons.SCHEDULE, "Período", state["period"].upper()), col={"xs":12, "md":3}, key="card_periodo"),
        ],
    )

    # Filtros de período
    def set_period(p: str):
        state["period"] = p
        state["refresh"]()

    filtros = ft.Container(
        bgcolor=ft.Colors.SURFACE,
        border=ft.border.all(1, ft.Colors.with_opacity(0.06, ft.Colors.BLACK)),
        border_radius=RADIUS, padding=18,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.ALARM, color=PRIMARY),
                        ft.Text("Período", weight=ft.FontWeight.W_600),
                    ],
                    spacing=8,
                ),
                ft.Row(
                    [
                        chip("24h", state["period"] == "24h", lambda: set_period("24h")),
                        chip("7 dias", state["period"] == "7d", lambda: set_period("7d")),
                        chip("30 dias", state["period"] == "30d", lambda: set_period("30d")),
                        chip("Tudo", state["period"] == "all", lambda: set_period("all")),
                    ],
                    spacing=10, wrap=False,
                ),
            ],
            spacing=12,
        ),
        key="filters",
    )

    # Painel do gráfico (placeholder – conecte ao seu gráfico real)
    chart_panel = ft.Container(
        bgcolor=ft.Colors.SURFACE,
        border=ft.border.all(1, ft.Colors.with_opacity(0.06, ft.Colors.BLACK)),
        border_radius=RADIUS,
        padding=20, height=320,
        content=ft.Column(
            [
                ft.Text("Distribuição por Loja", weight=ft.FontWeight.W_600),
                ft.Container(
                    expand=True,
                    alignment=ft.alignment.center,
                    content=ft.Text("Gráfico aqui", color=ft.Colors.ON_SURFACE_VARIANT),
                ),
            ]
        ),
        key="chart",
    )

    # Logs (placeholder)
    logs_panel = ft.Container(
        bgcolor=ft.Colors.SURFACE,
        border=ft.border.all(1, ft.Colors.with_opacity(0.06, ft.Colors.BLACK)),
        border_radius=RADIUS, padding=16,
        content=ft.Column(
            [
                ft.Text("Logs do sistema", weight=ft.FontWeight.W_600),
                ft.Container(
                    bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
                    border_radius=12, height=60, padding=10,
                    content=ft.Text("[INFO] Arquivo de log não encontrado. Sistema iniciando..."),
                ),
            ],
            spacing=10,
        ),
        key="logs",
    )

    return ft.Column(
        controls=[
            section("Métricas do Sistema", ft.Icons.INSIGHTS),
            cards,
            ft.Container(height=GAP),
            filtros,
            ft.Container(height=GAP),
            chart_panel,
            ft.Container(height=GAP),
            logs_panel,
        ],
        spacing=GAP,
        expand=True,
    )

def config_tab() -> ft.Column:
    return ft.Column(
        controls=[
            section("Configurações", ft.Icons.SETTINGS),
            ft.Text("Aba de Configurações (conectar aos seus forms existentes)"),
        ],
        spacing=GAP,
        expand=True,
    )

def controls_tab() -> ft.Column:
    return ft.Column(
        controls=[
            section("Controles", ft.Icons.GAMEPAD),
            ft.Text("Aba de Controles (botões de iniciar/parar, etc.)"),
        ],
        spacing=GAP,
        expand=True,
    )

# ---------- Header + Tabs ----------
def header(page: ft.Page, state: dict) -> ft.Container:
    title = ft.Text("Garimpeiro Geek - Dashboard", size=22, weight=ft.FontWeight.W_700)
    theme_label = ft.Text(f"Tema: {'Dark' if state['dark'] else 'Light'}")

    def toggle_theme(_):
        state["dark"] = not state["dark"]
        make_theme(page, state["dark"])
        theme_label.value = f"Tema: {'Dark' if state['dark'] else 'Light'}"
        state["refresh"]()

    return ft.Container(
        padding=ft.padding.symmetric(18, 18),
        content=ft.Container(
            bgcolor=ft.Colors.SURFACE,
            border=ft.border.all(1, ft.Colors.with_opacity(0.06, ft.Colors.BLACK)),
            border_radius=RADIUS, padding=18,
            content=ft.Row(
                [
                    title,
                    ft.Row(
                        [
                            theme_label,
                            ft.IconButton(
                                ft.Icons.DARK_MODE if not state["dark"] else ft.Icons.LIGHT_MODE,
                                tooltip="Alternar tema",
                                on_click=toggle_theme,
                            ),
                        ],
                        spacing=10,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        ),
    )

def tabs(page: ft.Page, state: dict) -> ft.Tabs:
    return ft.Tabs(
        selected_index=state["tab"],
        animation_duration=150,
        indicator_color=PRIMARY,
        on_change=lambda e: (state.update(tab=e.control.selected_index), state["refresh"]()),
        tabs=[
            ft.Tab(text="Logs", icon=ft.Icons.INSERT_CHART_OUTLINED),
            ft.Tab(text="Configurações", icon=ft.Icons.SETTINGS_OUTLINED),
            ft.Tab(text="Controles", icon=ft.Icons.VIDEOGAME_ASSET),
        ],
        expand=True,
        key="tabs",
    )

# ---------- App ----------
def create_dashboard_app(page: ft.Page):
    # estado simples
    state = {"dark": True, "tab": 0, "period": "all", "refresh": lambda: None}

    def refresh():
        # rebuild o conteúdo do corpo conforme a tab
        body.controls.clear()
        if state["tab"] == 0:
            body.controls.append(logs_metrics_tab(state))
        elif state["tab"] == 1:
            body.controls.append(config_tab())
        else:
            body.controls.append(controls_tab())
        page.update()

    state["refresh"] = refresh
    make_theme(page, state["dark"])

    head = header(page, state)
    nav = tabs(page, state)
    body = ft.Column(expand=True)
    refresh()

    root = ft.Column(
        controls=[
            head,
            ft.Container(
                padding=ft.padding.symmetric(0, 16),
                content=nav,
            ),
            ft.Container(
                padding=ft.padding.all(16),
                content=body,
                expand=True,
            ),
        ],
        expand=True,
        spacing=0,
    )
    return root

# Modo execução direta: `python -m app.dashboard`
def main(page: ft.Page):
    root = create_dashboard_app(page)
    page.add(root)

    want_report = ("--report" in sys.argv) or os.getenv("GG_REPORT") == "1"
    if want_report:
        try:
            # Adicionar o diretório pai ao path para importar diagnostics
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from diagnostics.ui_reporter import dump_report
            dump_report(page, json_summary=("--json" in sys.argv))
        except Exception as e:
            print(f"[UI-REPORTER] erro: {e}")
        # se quiser encerrar automaticamente em CI:
        if ("--exit-after-report" in sys.argv) or os.getenv("GG_EXIT_AFTER_REPORT") == "1":
            os._exit(0)

if __name__ == "__main__":
    ft.app(target=main) 
