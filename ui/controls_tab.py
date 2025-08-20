"""
Aba de controles do dashboard com toggle mestre e toggles por fonte.
"""

from __future__ import annotations
import flet as ft
from core.storage import PreferencesStorage
from core import scraper_registry as reg
from core import scrape_runner as runner


def create_controls_tab(page: ft.Page) -> ft.Container:
    """Cria a aba de controles com toggles do sistema."""
    storage = PreferencesStorage()
    
    # Garante runner e overrides carregados
    runner.init_runner(storage)

    # Toggle mestre
    master_switch = ft.Switch(
        key="toggle_master",
        label="Sistema de coleta (ligar/desligar)",
        value=runner.get_master_enabled(),
        tooltip="Controla se o sistema de coleta está ativo"
    )

    def on_master_change(e: ft.ControlEvent):
        """Callback para mudança do toggle mestre."""
        runner.set_master_enabled(master_switch.value)
        if master_switch.value and not runner.is_running():
            runner.start_scraping()
        if not master_switch.value and runner.is_running():
            runner.stop_scraping()
        
        # Mostrar feedback
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Sistema: " + ("Ligado" if master_switch.value else "Desligado"))
        )
        page.snack_bar.open = True
        page.update()

    master_switch.on_change = on_master_change

    # Lista de fontes
    sources = reg.list_sources()
    compliance_off = not reg.scraping_allowed()
    tooltip = "Desativado em modo CI ou sem GG_ALLOW_SCRAPING=1" if compliance_off else None

    rows: list[ft.Control] = []
    names: list[str] = []
    
    for s in sources:
        name = s["name"]
        names.append(name)
        
        # Criar switch para cada fonte
        sw = ft.Switch(
            key=f"toggle_src_{name}",
            label=f"{name} (prioridade: {s['priority']})",
            value=s["enabled_effective"],
            disabled=compliance_off,
            tooltip=tooltip,
        )

        def _make_handler(src_name: str):
            """Cria handler para mudança de fonte específica."""
            def _h(e: ft.ControlEvent):
                reg.set_enabled(src_name, e.control.value, storage=storage)
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Fonte '{src_name}': " + ("ativada" if e.control.value else "desativada"))
                )
                page.snack_bar.open = True
                page.update()
            return _h

        sw.on_change = _make_handler(name)
        
        # Criar linha com switch e informações
        row = ft.Row([
            sw,
            ft.Container(
                content=ft.Text(
                    s.get("description", ""),
                    size=12,
                    color=ft.Colors.ON_SURFACE_VARIANT
                ),
                expand=True
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        rows.append(row)

    # Ações em massa
    def bulk_set(val: bool):
        """Define todas as fontes de uma vez."""
        reg.set_all_enabled(names, val, storage=storage)
        
        # Atualiza switches na tela
        for r in rows:
            sw = r.controls[0]
            if not sw.disabled:
                sw.value = val
                sw.update()
        
        # Mostrar feedback
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Todas as fontes " + ("ativadas" if val else "desativadas"))
        )
        page.snack_bar.open = True
        page.update()

    btn_all_on = ft.TextButton(
        "Ativar todos", 
        on_click=lambda e: bulk_set(True), 
        disabled=compliance_off, 
        tooltip=tooltip
    )
    
    btn_all_off = ft.TextButton(
        "Desativar todos", 
        on_click=lambda e: bulk_set(False),
        tooltip="Desativa todas as fontes"
    )

    # Status do sistema
    status_text = ft.Text(
        f"Status: {runner.status().title()}",
        size=14,
        weight=ft.FontWeight.W_500,
        color=ft.Colors.PRIMARY
    )

    return ft.Container(
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                # Cabeçalho
                ft.Text("Controles do Sistema", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                # Toggle mestre
                ft.Text("Controle Geral", size=16, weight=ft.FontWeight.W_500),
                ft.Row([
                    master_switch,
                    status_text
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Divider(),
                
                # Controles de fontes
                ft.Text("Fontes de Dados", size=16, weight=ft.FontWeight.W_500),
                ft.Text(
                    "Habilite/desabilite as fontes de coleta:",
                    size=12,
                    color=ft.Colors.ON_SURFACE_VARIANT
                ),
                
                # Botões de ação em massa
                ft.Row([
                    btn_all_on,
                    btn_all_off
                ], alignment=ft.MainAxisAlignment.START),
                
                # Lista de fontes com scroll
                ft.Container(
                    expand=True,
                    content=ft.ListView(
                        expand=True,
                        controls=rows,
                        spacing=8
                    ),
                ),
                
                # Informações de compliance
                ft.Divider(),
                ft.Container(
                    content=ft.Text(
                        "ℹ️ Em modo CI ou sem GG_ALLOW_SCRAPING=1, os toggles individuais ficam desabilitados",
                        size=12,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=ft.padding.all(8)
                ) if compliance_off else ft.Container(height=0)
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO  # Scroll apenas nesta aba
        ),
        padding=ft.padding.all(16),
        expand=True
    )
