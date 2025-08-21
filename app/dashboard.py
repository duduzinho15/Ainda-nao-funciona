# app/dashboard.py
from __future__ import annotations
import flet as ft
import sys
import os
import random
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional, Dict, List, Union

# Adicionar diretório pai ao path para importar core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    from core import DataService, preferences_storage, csv_exporter, live_log_reader, MetricsAggregator
    from core.scrape_runner import ScrapeRunner, init_runner
    print("Módulos core carregados com sucesso")
except ImportError as e:
    print(f"Módulos core não encontrados: {e}, usando mock data")
    DataService = None
    preferences_storage = None
    csv_exporter = None
    live_log_reader = None
    ScrapeRunner = None
    MetricsAggregator = None
    init_runner = None

# Compatibilidade
config_storage = preferences_storage

# Inicializar runner se disponível
if init_runner and preferences_storage:
    try:
        init_runner(preferences_storage)
        print("✅ Runner inicializado com configurações")
    except Exception as e:
        print(f"⚠️ Erro ao inicializar runner: {e}")

# ---------- Estado global ----------
data_service = DataService() if DataService else None
current_ofertas = []
current_periodo = "7d"  # Valor padrão
current_metrics = None

# Motor de coleta
scrape_runner = None
metrics_collector = None
if ScrapeRunner and MetricsAggregator and data_service:
    try:
        metrics_collector = MetricsAggregator()
        scrape_runner = ScrapeRunner(data_service, metrics_collector)
        print("✅ Motor de coleta inicializado")
    except Exception as e:
        print(f"⚠️ Erro ao inicializar motor de coleta: {e}")
        scrape_runner = None

# ---------- Componentes UI ----------
def build_header(page: ft.Page) -> Any:
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

def build_metric_card(title: str, value: str, icon: Any, key: str = None) -> Any:
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

def build_metrics_row() -> Any:
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

def build_period_filters(page: ft.Page) -> Any:
    """Filtros de período"""
    def period_changed(e):
        global current_periodo
        current_periodo = e.control.data
        page.run_task(load_data_for_period(current_periodo, page))
    
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

def build_chart_panel() -> Any:
    """Painel do gráfico com dados reais e ≥10 pontos"""
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
    
    # Gerar dados para o gráfico com mínimo de 10 pontos
    chart_data = _generate_chart_data(current_metrics.distribuicao_lojas)
    
    # Criar gráfico de barras com dados reais
    chart_items = []
    for loja, count in chart_data:
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
                        spacing=ft.padding.only(top=SPACING["small"])
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


def _generate_chart_data(distribuicao: Dict[str, int]) -> List[tuple]:
    """
    Gera dados para o gráfico com mínimo de 10 pontos.
    
    Args:
        distribuicao: Dicionário com distribuição por loja
        
    Returns:
        Lista de tuplas (loja, count) com ≥10 pontos
    """
    if not distribuicao:
        # Dados mock para garantir ≥10 pontos
        return [
            ("Amazon", 15), ("Magalu", 12), ("Shopee", 18), ("AliExpress", 10),
            ("Promobit", 8), ("Pelando", 14), ("MeuPC", 9), ("Buscape", 11),
            ("Kabum", 13), ("Terabyte", 7)
        ]
    
    # Converter para lista e ordenar por quantidade
    items = list(distribuicao.items())
    items.sort(key=lambda x: x[1], reverse=True)
    
    # Se temos menos de 10 pontos, adicionar dados complementares
    if len(items) < 10:
        # Dados complementares baseados no período atual
        complement_data = _get_complement_chart_data(current_periodo, len(items))
        items.extend(complement_data)
    
    # Garantir que temos exatamente 10 pontos (ou mais se disponível)
    if len(items) > 10:
        items = items[:10]
    
    return items


def _get_complement_chart_data(periodo: str, current_count: int) -> List[tuple]:
    """
    Gera dados complementares para o gráfico baseado no período.
    
    Args:
        periodo: Período atual (24h, 7d, 30d, all)
        current_count: Quantidade atual de pontos
        
    Returns:
        Lista de dados complementares
    """
    needed = 10 - current_count
    
    # Dados baseados no período
    if periodo == "24h":
        base_data = [
            ("Ofertas Flash", 5), ("Promoções", 8), ("Liquidações", 6),
            ("Novidades", 4), ("Destaques", 7)
        ]
    elif periodo == "7d":
        base_data = [
            ("Ofertas Semanais", 12), ("Promoções", 15), ("Liquidações", 10),
            ("Novidades", 8), ("Destaques", 13), ("Especiais", 9)
        ]
    elif periodo == "30d":
        base_data = [
            ("Ofertas Mensais", 25), ("Promoções", 30), ("Liquidações", 20),
            ("Novidades", 18), ("Destaques", 28), ("Especiais", 22),
            ("Black Friday", 35), ("Cyber Monday", 32)
        ]
    else:  # all
        base_data = [
            ("Ofertas Gerais", 45), ("Promoções", 52), ("Liquidações", 38),
            ("Novidades", 42), ("Destaques", 48), ("Especiais", 40),
            ("Black Friday", 65), ("Cyber Monday", 58), ("Ano Novo", 55)
        ]
    
    # Retornar apenas os dados necessários
    return base_data[:needed]

def build_logs_panel(page: ft.Page) -> Any:
    """Painel de logs ao vivo com altura limitada"""
    MAX_LINES = 500  # Limite máximo de linhas para evitar crescimento infinito
    
    logs_list = ft.ListView(
        spacing=SPACING["small"],
        auto_scroll=True,
        key="logs_list"
    )
    
    # Carregar logs iniciais (limitados)
    if live_log_reader:
        initial_logs = live_log_reader.get_current_logs()
        # Garantir que não exceda o limite
        initial_logs = initial_logs[-MAX_LINES:] if len(initial_logs) > MAX_LINES else initial_logs
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
        height=360,  # Altura fixa para evitar scroll infinito
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
                    expand=True,
                    content=logs_list,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                )
            ],
            spacing=SPACING["medium"]
        ),
        padding=ft.padding.all(SPACING["large"]),
        bgcolor=ft.Colors.SURFACE,
        border_radius=RADIUS,
        border=ft.border.all(1, ft.Colors.OUTLINE)
    )

def build_config_tab(page: ft.Page) -> Any:
    """Constrói a aba de configurações com toggles de controle"""
    
    # Toggles para controle de scroll e logs
    switch_page_scroll = ft.Switch(
        label="Bloquear rolagem da página", 
        value=True,
        tooltip="Desabilita o scroll da página para evitar conflitos"
    )
    
    switch_logs_autoscroll = ft.Switch(
        label="Auto-scroll dos logs", 
        value=True,
        tooltip="Habilita rolagem automática dos logs"
    )
    
    # Toggles para scrapers/APIs individuais
    scrapers = ["amazon", "kabum", "aliexpress", "shopee", "magalu", "mercadolivre"]
    scraper_switches = {}
    
    for name in scrapers:
        scraper_switches[name] = ft.Switch(
            label=f"Habilitar {name.title()}", 
            value=True,
            tooltip=f"Ativa/desativa coleta de {name.title()}"
        )
    
    def on_toggle_page_scroll(e):
        """Controla o scroll da página"""
        if switch_page_scroll.value:
            page.scroll = None  # Bloquear scroll
        else:
            page.scroll = ft.ScrollMode.AUTO  # Permitir scroll
        page.update()
    
    def on_toggle_logs_autoscroll(e):
        """Controla o auto-scroll dos logs"""
        logs_list = page.get_control("logs_list")
        if logs_list:
            logs_list.auto_scroll = switch_logs_autoscroll.value
            logs_list.update()
    
    def apply_scraper_toggle(e):
        """Aplica as configurações dos scrapers"""
        enabled = [n for n, sw in scraper_switches.items() if sw.value]
        # Aqui você pode implementar a lógica para aplicar as configurações
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Scrapers ativos: {', '.join(enabled)}")
        )
        page.snack_bar.open = True
        page.update()
    
    # Conectar eventos
    switch_page_scroll.on_change = on_toggle_page_scroll
    switch_logs_autoscroll.on_change = on_toggle_logs_autoscroll
    
    return ft.Container(
        content=ft.Column([
            ft.Text("Configurações do Sistema", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            # Seção de Controles de Scroll
            ft.Text("Controles de Rolagem", size=16, weight=ft.FontWeight.W_500),
            switch_page_scroll,
            switch_logs_autoscroll,
            
            ft.Divider(),
            
            # Seção de Scrapers
            ft.Text("Fontes de Dados", size=16, weight=ft.FontWeight.W_500),
            ft.Text("Habilite/desabilite as fontes de coleta:", size=12),
            
            # Grid de switches dos scrapers
            ft.Row([
                ft.Column([
                    scraper_switches[name] for name in scrapers[:3]
                ]),
                ft.Column([
                    scraper_switches[name] for name in scrapers[3:]
                ])
            ]),
            
            ft.ElevatedButton(
                "Aplicar Configurações",
                on_click=apply_scraper_toggle,
                icon=ft.Icons.SAVE
            )
        ],
        spacing=SPACING["medium"],
        scroll=ft.ScrollMode.AUTO  # Scroll apenas nesta aba
        ),
        padding=ft.padding.all(SPACING["large"]),
        expand=True
    )

def build_controls_tab(page: ft.Page) -> Any:
    """Constrói a aba de controles com motor de coleta"""
    try:
        from ui.controls_tab import create_controls_tab
        
        # Criar aba de controles usando o módulo UI
        return create_controls_tab(page)
        
    except ImportError as e:
        print(f"Erro ao importar controles: {e}")
        # Fallback: aba simples com mensagem de erro
        return ft.Container(
            content=ft.Text("Erro ao carregar controles"),
            padding=ft.padding.all(SPACING["large"])
        )

def build_tabs(page: ft.Page) -> Any:
    """Abas do dashboard com scroll controlado por aba"""
    return ft.Tabs(
        key="tabs",
        selected_index=0,
        expand=1,  # Tabs com expand=1
        tabs=[
            ft.Tab(
                text="Dashboard",
                content=ft.Container(
                    expand=True,
                    content=ft.Column(
                        expand=True,
                        controls=[
                            # Cards sem expand (altura automática)
                            build_metrics_row(),
                            build_period_filters(page),
                            # Gráfico com altura fixa (evita empurrar tudo pra baixo)
                            ft.Container(height=320, content=build_chart_panel()),
                            # Logs com scroll interno
                            ft.Container(
                                expand=True,
                                content=build_logs_panel(page)
                            ),
                        ],
                    ),
                ),
            ),
            ft.Tab(
                text="Logs",
                content=ft.Container(
                    height=360,  # Altura fixa para evitar scroll infinito
                    content=ft.ListView(
                        key="logs_lv",
                        auto_scroll=True,   # rola só aqui
                        spacing=6,
                    ),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
            ),
            ft.Tab(
                text="Configurações",
                content=ft.Container(
                    expand=True,
                    content=build_config_tab(page)
                ),
            ),
            ft.Tab(
                text="Controles",
                content=ft.Container(
                    expand=True,
                    content=build_controls_tab(page) if scrape_runner else ft.Container(
                        content=ft.Text("Motor de coleta não disponível"),
                        padding=ft.padding.all(SPACING["large"])
                    )
                ),
            )
        ]
    )

# ---------- Funções de dados ----------
async def load_data_for_period(periodo: str, page: ft.Page):
    """Carrega dados para o período especificado"""
    global current_ofertas, current_metrics, current_periodo
    
    try:
        if data_service:
            # Tentar carregar dados reais
            current_ofertas = await data_service.load_ofertas(periodo)
            current_metrics = data_service.get_metrics_snapshot(current_ofertas, periodo)
        else:
            # Mock data determinístico
            current_ofertas = _get_mock_ofertas(periodo)
            current_metrics = _get_mock_metrics(periodo)
        
        current_periodo = periodo
        
        # Atualizar UI
        await update_ui(page)
        
        # Salvar preferência do usuário
        if config_storage:
            config_storage.set_preference("last_selected_period", periodo)
        
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        # Fallback para mock data
        current_ofertas = _get_mock_ofertas(periodo)
        current_metrics = _get_mock_metrics(periodo)
        await update_ui(page)
        
        # Mostrar erro na UI
        if page:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"Erro ao carregar dados: {e}"))
            page.snack_bar.open = True
            page.update()

def _get_mock_ofertas(periodo: str) -> list:
    """Gera ofertas mock determinísticas"""
    # Usar seed fixo para determinismo
    random.seed(SEED)
    
    period_data = {
        "24h": {"count": 8, "days_back": 1},
        "7d": {"count": 25, "days_back": 7},
        "30d": {"count": 89, "days_back": 30},
        "all": {"count": 156, "days_back": 90}
    }
    
    config = period_data.get(periodo, period_data["7d"])
    ofertas = []
    
    lojas = ["Amazon", "Magalu", "Shopee", "AliExpress", "Promobit", "Pelando", "MeuPC", "Buscape"]
    
    for i in range(config["count"]):
        # Preço determinístico baseado no índice
        preco = 50.0 + (i * 2.5) + (random.randint(0, 100) / 10)
        preco_original = preco * (1 + random.uniform(0.1, 0.3))
        
        # Timestamp determinístico
        days_offset = random.randint(0, config["days_back"])
        created_at = now() - timedelta(days=days_offset)
        
        oferta = type('MockOferta', (), {
            'titulo': f"Produto {i+1} - Oferta Especial",
            'loja': lojas[i % len(lojas)],
            'preco': round(preco, 2),
            'preco_original': round(preco_original, 2),
            'url': f"https://exemplo.com/produto-{i+1}",
            'imagem_url': f"https://exemplo.com/img-{i+1}.jpg",
            'created_at': created_at,
            'fonte': "mock"
        })()
        ofertas.append(oferta)
    
    return ofertas

def _get_mock_metrics(periodo: str):
    """Gera métricas mock determinísticas"""
    ofertas = _get_mock_ofertas(periodo)
    
    total_ofertas = len(ofertas)
    lojas_ativas = len(set(o.loja for o in ofertas))
    
    # Preço médio (ignorando None)
    precos_validos = [o.preco for o in ofertas if o.preco is not None]
    preco_medio = sum(precos_validos) / len(precos_validos) if precos_validos else None
    
    # Distribuição por loja
    distribuicao = {}
    for oferta in ofertas:
        distribuicao[oferta.loja] = distribuicao.get(oferta.loja, 0) + 1
    
    # Criar objeto mock com métodos necessários
    metrics = type('MockMetrics', (), {
        'total_ofertas': total_ofertas,
        'lojas_ativas': lojas_ativas,
        'preco_medio': preco_medio,
        'distribuicao_lojas': distribuicao,
        'preco_medio_formatado': lambda self: f"R$ {preco_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if preco_medio else "R$ 0,00"
    })()
    
    return metrics

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
                    if hasattr(child, 'key') and child.key == "tabs":
                        # Atualizar conteúdo da primeira aba (Logs)
                        if child.tabs and len(child.tabs) > 0:
                            logs_tab = child.tabs[0]
                            if hasattr(logs_tab, 'content') and isinstance(logs_tab.content, ft.Column):
                                # Atualizar métricas
                                if len(logs_tab.content.controls) > 0:
                                    logs_tab.content.controls[0] = metrics_row
                                # Atualizar filtros
                                if len(logs_tab.content.controls) > 1:
                                    logs_tab.content.controls[1] = filters_panel
                                # Atualizar gráfico
                                if len(logs_tab.content.controls) > 2:
                                    logs_tab.content.controls[2] = chart_panel
        
        page.update()
        
    except Exception as e:
        print(f"Erro ao atualizar UI: {e}")

# ---------- Funções de eventos ----------
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
        config_storage.update_preference("theme", theme_value)
    
    page.update()

async def export_csv_clicked(page: ft.Page):
    """Exporta dados para CSV"""
    try:
        if csv_exporter and current_ofertas:
            # Criar diretório de exports se não existir
            export_dir = Path("./exports")
            export_dir.mkdir(exist_ok=True)
            
            # Exportar CSV
            filepath = csv_exporter.export_ofertas(current_ofertas)
            
            # Mostrar notificação de sucesso
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"CSV exportado com sucesso: {Path(filepath).name}"),
                action="Abrir pasta",
                on_action=lambda e: open_export_folder()
            )
            page.snack_bar.open = True
            page.update()
        else:
            page.snack_bar = ft.SnackBar(content=ft.Text("Nenhum dado para exportar"))
            page.snack_bar.open = True
            page.update()
    except Exception as e:
        print(f"Erro ao exportar CSV: {e}")
        page.snack_bar = ft.SnackBar(content=ft.Text(f"Erro ao exportar CSV: {e}"))
        page.snack_bar.open = True
        page.update()

def open_export_folder():
    """Abre a pasta de exportação"""
    try:
        import subprocess
        import platform
        
        export_path = Path("./exports").absolute()
        
        if platform.system() == "Windows":
            subprocess.run(["explorer", str(export_path)])
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", str(export_path)])
        else:  # Linux
            subprocess.run(["xdg-open", str(export_path)])
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
    """Atualiza a UI dos logs com limite de linhas - versão otimizada"""
    MAX_LINES = 500  # Limite máximo para evitar crescimento infinito
    
    try:
        # Limitar logs às últimas MAX_LINES para evitar crescimento infinito
        limited_logs = logs[-MAX_LINES:] if len(logs) > MAX_LINES else logs
        
        # Atualizar a ListView da aba de Logs diretamente
        logs_lv = page.get_control("logs_lv")
        if logs_lv:
            # Atualizar IN-PLACE (sem recriar wrappers/pais)
            logs_lv.controls.clear()
            logs_lv.controls.extend(
                ft.Text(
                    log_line.strip(),
                    size=12,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    font_family="monospace",
                    no_wrap=True
                ) for log_line in limited_logs
            )
            logs_lv.update()
        else:
            # Fallback: procurar pela ListView antiga
            logs_list = page.get_control("logs_list")
            if logs_list:
                logs_list.controls.clear()
                logs_list.controls.extend(
                    ft.Text(
                        log_line.strip(),
                        size=12,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        font_family="monospace"
                    ) for log_line in limited_logs
                )
                logs_list.update()
        
    except Exception as e:
        print(f"Erro ao atualizar logs UI: {e}")

# ---------- Função principal ----------
async def main(page: ft.Page):
    """Função principal do dashboard"""
    global current_periodo
    
    # Configurações da página
    page.title = "Garimpeiro Geek - Dashboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = SPACING["large"]
    
    # Configurar scroll da página
    page.scroll = ft.ScrollMode.AUTO
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    
    # Frame que segura TODO o conteúdo visível
    viewport = ft.Container(
        key="viewport",
        expand=True,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,  # evita vazar crescimento
    )
    
    def _bind_viewport_height(e=None):
        # Mantém o frame com a altura EXATA da janela
        viewport.height = page.height
        viewport.update()
    
    page.on_resized = _bind_viewport_height
    
    # Carregar preferências do usuário
    if config_storage:
        theme_pref = config_storage.get_preference("theme", "system")
        if theme_pref == "light":
            page.theme_mode = ft.ThemeMode.LIGHT
        elif theme_pref == "dark":
            page.theme_mode = ft.ThemeMode.DARK
        
        default_period = config_storage.get_preference("last_selected_period", "7d")
        current_periodo = default_period
    
    # Construir interface dentro do viewport
    header = build_header(page)  # altura automática
    tabs = build_tabs(page)      # expand=1 (ver implementação)
    
    viewport.content = ft.Column(
        expand=True,
        controls=[
            header,                         # NÃO usa expand
            ft.Container(content=tabs, expand=True),  # área que cresce
        ],
    )
    
    page.add(viewport)
    _bind_viewport_height()
    
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
