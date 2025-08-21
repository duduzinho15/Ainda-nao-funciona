"""
Aba de controles do dashboard com toggle mestre e toggles por fonte.
"""

from __future__ import annotations
import flet as ft
import os
from core.storage import PreferencesStorage
from core import scraper_registry as reg
from core import scrape_runner as runner
from core.scrapers_config import get_global_enabled, set_global_enabled, get_enabled_map, set_source_enabled, is_scraping_allowed


def create_controls_tab(page: ft.Page) -> ft.Container:
    """Cria a aba de controles com toggles do sistema."""
    storage = PreferencesStorage()
    
    # Garante runner e overrides carregados
    runner.init_runner(storage)

    # Verificar permissões
    allow_scraping = is_scraping_allowed()
    is_ci = bool(os.getenv("GG_SEED")) and bool(os.getenv("GG_FREEZE_TIME"))
    
    # Toggle mestre
    master_switch = ft.Switch(
        key="toggle_master",
        label="Sistema de coleta (ligar/desligar)",
        value=get_global_enabled() and allow_scraping and not is_ci,
        disabled=(not allow_scraping) or is_ci,
        tooltip="Controla se o sistema de coleta está ativo" + 
                (" - Bloqueado por ambiente" if not allow_scraping else "") +
                (" - Modo CI" if is_ci else "")
    )

    def on_master_change(e: ft.ControlEvent):
        """Callback para mudança do toggle mestre."""
        if not allow_scraping or is_ci:
            return
            
        set_global_enabled(master_switch.value)
        
        if master_switch.value and not runner.is_running():
            # Iniciar scraping
            page.run_task(runner.start_scraping("7d", 10.0))
            page.snack_bar = ft.SnackBar(
                content=ft.Text("🟢 Sistema iniciado - scraping ativo")
            )
        elif not master_switch.value and runner.is_running():
            # Parar scraping
            page.run_task(runner.stop_scraping())
            page.snack_bar = ft.SnackBar(
                content=ft.Text("🔴 Sistema parado - scraping inativo")
            )
        
        page.snack_bar.open = True
        page.update()

    master_switch.on_change = on_master_change

    # Lista de fontes
    sources = reg.list_sources()
    compliance_off = not allow_scraping or is_ci
    tooltip = "Desativado em modo CI ou sem GG_ALLOW_SCRAPING=1" if compliance_off else None

    rows: list[ft.Control] = []
    names: list[str] = []
    
    for s in sources:
        name = s["name"]
        names.append(name)
        
        # Criar switch para cada fonte
        enabled_map = get_enabled_map()
        sw = ft.Switch(
            key=f"toggle_src_{name}",
            label=f"{name} (prioridade: {s['priority']})",
            value=enabled_map.get(name, True) and allow_scraping and not is_ci,
            disabled=compliance_off,
            tooltip=tooltip,
        )

        def _make_handler(src_name: str):
            """Cria handler para mudança de fonte específica."""
            def _h(e: ft.ControlEvent):
                if not allow_scraping or is_ci:
                    return
                set_source_enabled(src_name, e.control.value)
                reg.set_enabled(src_name, e.control.value, storage=storage)
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Fonte '{src_name}': " + ("ativada" if e.control.value else "desativada"))
                )
                page.snack_bar.open = True
                page.update()
            return _h

        sw.on_change = _make_handler(name)
        
        # Botão de teste para a fonte
        test_btn = ft.ElevatedButton(
            "Testar",
            key=f"test_btn_{name}",
            on_click=lambda e, src_name=name: _test_source(e, src_name),
            disabled=compliance_off,
            tooltip=f"Testar fonte {name}",
            style=ft.ButtonStyle(
                color=ft.Colors.ON_PRIMARY,
                bgcolor=ft.Colors.PRIMARY
            )
        )
        
        # Criar linha com switch, informações e botão de teste
        row = ft.Row([
            sw,
            ft.Container(
                content=ft.Text(
                    s.get("description", ""),
                    size=12,
                    color=ft.Colors.ON_SURFACE_VARIANT
                ),
                expand=True
            ),
            test_btn
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        rows.append(row)

    # Ações em massa
    def bulk_set(val: bool):
        """Define todas as fontes de uma vez."""
        if not allow_scraping or is_ci:
            return
            
        # Atualizar configuração
        for name in names:
            set_source_enabled(name, val)
        
        # Atualizar registry
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
    
    def _test_source(e, src_name: str):
        """Testa uma fonte específica."""
        if not allow_scraping or is_ci:
            return
            
        # Mostrar loading
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"🧪 Testando fonte {src_name}...")
        )
        page.snack_bar.open = True
        page.update()
        
        # Executar teste assíncrono
        async def run_test():
            try:
                from core import scraper_registry as reg
                result = reg.smoke_test_source(src_name, timeout=15.0)
                
                if result.get('success', False):
                    items = result.get('items_found', 0)
                    duration = result.get('duration', 0)
                    message = f"✅ {src_name}: {items} itens em {duration:.1f}s"
                    color = ft.Colors.GREEN
                else:
                    error = result.get('error', 'Erro desconhecido')
                    message = f"❌ {src_name}: {error}"
                    color = ft.Colors.RED
                
                # Mostrar resultado
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(message, color=color)
                )
                page.snack_bar.open = True
                page.update()
                
            except Exception as e:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ Erro ao testar {src_name}: {e}")
                )
                page.snack_bar.open = True
                page.update()
        
        page.run_task(run_test())

    # Status do sistema
    def get_runner_status():
        """Obtém status atual do runner."""
        try:
            status = runner.get_status()
            return status
        except:
            return {"running": False, "last_run": None, "tick": 0}
    
    status_data = get_runner_status()
    
    # Status visual com cor
    status_color = ft.Colors.GREEN if status_data.get("running", False) else ft.Colors.RED
    status_text = ft.Text(
        f"Status: {'Running' if status_data.get('running', False) else 'Stopped'}",
        size=14,
        weight=ft.FontWeight.W_500,
        color=status_color
    )
    
    # Última execução
    last_run_text = ft.Text(
        f"Última execução: {status_data.get('last_run', 'Nunca')}",
        size=12,
        color=ft.Colors.ON_SURFACE_VARIANT
    )
    
    # Contador de ticks
    tick_text = ft.Text(
        f"Ticks: {status_data.get('tick', 0)}",
        size=12,
        color=ft.Colors.ON_SURFACE_VARIANT
    )

    return ft.Container(
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
                
                # Informações de status
                ft.Row([
                    last_run_text,
                    tick_text
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
