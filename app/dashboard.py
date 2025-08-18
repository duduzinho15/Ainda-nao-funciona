from __future__ import annotations
import flet as ft

ACCENT = ft.Colors.LIGHT_BLUE_ACCENT_400

def _panel_bg(page: ft.Page) -> str:
    return ft.Colors.with_opacity(0.06, ft.Colors.WHITE) if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.WHITE

def _surface(page: ft.Page) -> str:
    return ft.Colors.BLACK if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.WHITE

def _metric_card(page: ft.Page, title: str, value: str, icon: str, icon_color: str) -> ft.Card:
    return ft.Card(
        elevation=2,
        content=ft.Container(
            bgcolor=_panel_bg(page),
            padding=16,
            border_radius=14,
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                title,
                                size=14,
                                weight=ft.FontWeight.W_500,
                                color=ft.Colors.with_opacity(0.7, _surface(page)),
                            ),
                            ft.Text(
                                value,
                                size=24,
                                weight=ft.FontWeight.W_700,
                                color=_surface(page),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Container(
                        width=48,
                        height=48,
                        border_radius=12,
                        bgcolor=ft.Colors.with_opacity(0.1, icon_color),
                        content=ft.Icon(
                            icon,
                            color=icon_color,
                            size=24,
                        ),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        ),
    )

def _period_chip(page: ft.Page, text: str, is_selected: bool, on_click) -> ft.Chip:
    return ft.Chip(
        label=ft.Text(text, size=14, weight=ft.FontWeight.W_500),
        selected=is_selected,
        on_select=on_click,
        selected_color=ACCENT,
        check_color=ft.Colors.WHITE,
        bgcolor=_panel_bg(page),
    )

def _section_card(page: ft.Page, title: str, content: ft.Control) -> ft.Card:
    return ft.Card(
        elevation=1,
        content=ft.Container(
            bgcolor=_panel_bg(page),
            padding=20,
            border_radius=16,
            content=ft.Column(
                [
                    ft.Text(
                        title,
                        size=18,
                        weight=ft.FontWeight.W_600,
                        color=_surface(page),
                    ),
                    ft.Divider(height=20, color=ft.Colors.with_opacity(0.1, _surface(page))),
                    content,
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
        ),
    )

def _toggle_theme_button(page: ft.Page) -> ft.IconButton:
    return ft.IconButton(
        icon=ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.LIGHT_MODE,
        icon_color=_surface(page),
        tooltip="Alternar tema",
        on_click=lambda e: _toggle_theme(page),
    )

def _toggle_theme(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
    page.update()

def create_dashboard_app(page: ft.Page):
    """Cria a aplicação principal do dashboard com visual polido."""
    
    # Estado da aplicação
    current_tab = 0
    current_period = "24h"
    
    # Dados simulados para demonstração
    mock_ofertas = [
        {
            "titulo": "Smartphone Samsung Galaxy A54 128GB",
            "loja": "Amazon",
            "preco": 1299.99,
            "preco_original": 1599.99,
            "desconto": "19%",
            "data": "2024-01-15 14:30:00",
            "fonte": "Amazon BR"
        },
        {
            "titulo": "Fone de Ouvido JBL Tune 510BT",
            "loja": "Magazine Luiza",
            "preco": 89.90,
            "preco_original": 129.90,
            "desconto": "31%",
            "data": "2024-01-15 13:45:00",
            "fonte": "Magazine Luiza"
        },
        {
            "titulo": "Smart TV LG 55\" 4K UHD",
            "loja": "Casas Bahia",
            "preco": 2499.00,
            "preco_original": 3299.00,
            "desconto": "24%",
            "data": "2024-01-15 12:15:00",
            "fonte": "Casas Bahia"
        }
    ]
    
    # Métricas simuladas
    mock_metrics = {
        "total_ofertas": 1247,
        "ofertas_hoje": 23,
        "lojas_ativas": 8,
        "preco_medio": 456.78,
        "preco_min": 12.90,
        "preco_max": 4999.99
    }
    
    def on_tab_change(e):
        nonlocal current_tab
        current_tab = int(e.data)
        print(f"Tab mudou para: {current_tab}")
    
    def on_period_change(period: str):
        nonlocal current_period
        current_period = period
        print(f"Período mudou para: {period}")

    def build_app_bar():
        """Constrói a app bar com toggle de tema."""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.SEARCH, size=32, color=ACCENT),
                    ft.Text(
                        "Garimpeiro Geek - Dashboard",
                        size=24,
                        weight=ft.FontWeight.W_700,
                        color=_surface(page),
                    ),
                    ft.Container(expand=True),
                    _toggle_theme_button(page),
                ]
            ),
            padding=ft.padding.only(left=24, right=24, top=16, bottom=16),
            bgcolor=_panel_bg(page),
            border=ft.border.only(
                bottom=ft.BorderSide(width=1, color=ft.Colors.with_opacity(0.1, _surface(page)))
            )
        )

    def build_tabs():
        """Constrói a barra de abas com design polido."""
        return ft.Container(
            content=ft.Tabs(
                selected_index=current_tab,
                on_change=on_tab_change,
                tabs=[
                    ft.Tab(
                        text="📊 Logs e Métricas",
                        icon=ft.Icons.ANALYTICS,
                        content=build_logs_tab(),
                    ),
                    ft.Tab(
                        text="⚙️ Configurações",
                        icon=ft.Icons.SETTINGS,
                        content=build_config_tab(),
                    ),
                    ft.Tab(
                        text="🎮 Controles",
                        icon=ft.Icons.GAMEPAD,
                        content=build_controls_tab(),
                    ),
                ],
            ),
            padding=ft.padding.only(left=24, right=24, top=8),
        )

    def build_content():
        """Constrói o conteúdo da aba selecionada."""
        return ft.Container(
            content=get_tab_content(),
            expand=True,
            padding=24,
        )

    def get_tab_content():
        """Retorna o conteúdo da aba atual."""
        if current_tab == 0:
            return build_logs_tab()
        elif current_tab == 1:
            return build_config_tab()
        elif current_tab == 2:
            return build_controls_tab()
        else:
            return ft.Text("Aba não encontrada")

    def build_logs_tab():
        """Constrói a aba de logs com métricas e gráficos polidos."""
        return ft.Column(
            controls=[
                # Cards de métricas
                build_metrics_cards(),
                ft.Divider(height=32, color=ft.Colors.with_opacity(0.1, _surface(page))),
                
                # Filtros de período
                build_period_filters(),
                ft.Divider(height=32, color=ft.Colors.with_opacity(0.1, _surface(page))),
                
                # Gráfico de distribuição por loja
                build_store_chart(),
                ft.Divider(height=32, color=ft.Colors.with_opacity(0.1, _surface(page))),
                
                # Tabela de ofertas
                build_ofertas_table(),
                ft.Divider(height=32, color=ft.Colors.with_opacity(0.1, _surface(page))),
                
                # Logs em tempo real
                build_logs_viewer(),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=24,
        )

    def build_metrics_cards():
        """Constrói os cards de métricas principais com design polido."""
        return ft.Column(
            [
                ft.Text(
                    "📊 Métricas do Sistema",
                    size=20,
                    weight=ft.FontWeight.W_700,
                    color=_surface(page),
                ),
                ft.Row(
                    [
                        _metric_card(
                            page,
                            "Total de Ofertas",
                            str(mock_metrics["total_ofertas"]),
                            ft.Icons.TAG,
                            ft.Colors.BLUE
                        ),
                        _metric_card(
                            page,
                            "Ofertas Hoje",
                            str(mock_metrics["ofertas_hoje"]),
                            ft.Icons.TODAY,
                            ft.Colors.GREEN
                        ),
                        _metric_card(
                            page,
                            "Lojas Ativas",
                            str(mock_metrics["lojas_ativas"]),
                            ft.Icons.STORE,
                            ft.Colors.ORANGE
                        ),
                        _metric_card(
                            page,
                            "Preço Médio",
                            f"R$ {mock_metrics['preco_medio']:.2f}",
                            ft.Icons.ATTACH_MONEY,
                            ft.Colors.PURPLE
                        ),
                    ],
                    spacing=16,
                ),
            ],
            spacing=20,
        )

    def build_period_filters():
        """Constrói os filtros de período com chips polidos."""
        return _section_card(
            page,
            "⏰ Filtros de Período",
            ft.Row(
                [
                    _period_chip(page, "24h", current_period == "24h", lambda e: on_period_change("24h")),
                    _period_chip(page, "7 dias", current_period == "7d", lambda e: on_period_change("7d")),
                    _period_chip(page, "30 dias", current_period == "30d", lambda e: on_period_change("30d")),
                    _period_chip(page, "Tudo", current_period == "all", lambda e: on_period_change("all")),
                ],
                spacing=12,
            )
        )

    def build_store_chart():
        """Constrói o gráfico de distribuição por loja com design polido."""
        store_data = [
            {"loja": "Amazon", "ofertas": 45},
            {"loja": "Magazine Luiza", "ofertas": 32},
            {"loja": "Casas Bahia", "ofertas": 28},
            {"loja": "Americanas", "ofertas": 22},
            {"loja": "Submarino", "ofertas": 18},
        ]
        
        chart_items = []
        for store in store_data:
            chart_items.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        store["loja"],
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                        color=_surface(page)
                                    ),
                                    ft.Container(expand=True),
                                    ft.Text(
                                        str(store["ofertas"]),
                                        size=14,
                                        weight=ft.FontWeight.W_700,
                                        color=_surface(page)
                                    ),
                                ],
                                spacing=20,
                            ),
                            ft.Container(
                                content=ft.Container(
                                    width=store["ofertas"] * 3,
                                    height=20,
                                    bgcolor=ACCENT,
                                    border_radius=10,
                                ),
                                alignment=ft.alignment.center_left,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=10,
                )
            )
        
        return _section_card(
            page,
            "🏪 Distribuição por Loja",
            ft.Column(chart_items, spacing=16)
        )

    def build_ofertas_table():
        """Constrói a tabela de ofertas com design polido."""
        return _section_card(
            page,
            "📋 Últimas Ofertas",
            ft.Container(
                content=ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Data", weight=ft.FontWeight.W_600)),
                        ft.DataColumn(ft.Text("Loja", weight=ft.FontWeight.W_600)),
                        ft.DataColumn(ft.Text("Produto", weight=ft.FontWeight.W_600)),
                        ft.DataColumn(ft.Text("Preço", weight=ft.FontWeight.W_600)),
                        ft.DataColumn(ft.Text("Desconto", weight=ft.FontWeight.W_600)),
                        ft.DataColumn(ft.Text("Fonte", weight=ft.FontWeight.W_600)),
                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(oferta["data"][:16])),
                                ft.DataCell(
                                    ft.Container(
                                        content=ft.Text(oferta["loja"]),
                                        padding=8,
                                        bgcolor=ft.Colors.with_opacity(0.1, ACCENT),
                                        border_radius=8,
                                    )
                                ),
                                ft.DataCell(ft.Text(oferta["titulo"])),
                                ft.DataCell(
                                    ft.Column(
                                        [
                                            ft.Text(
                                                f"R$ {oferta['preco']:.2f}",
                                                weight=ft.FontWeight.W_700,
                                                color=_surface(page)
                                            ),
                                            ft.Text(
                                                f"R$ {oferta['preco_original']:.2f}",
                                                size=12,
                                                color=ft.Colors.with_opacity(0.6, _surface(page)),
                                            ),
                                        ],
                                        spacing=2,
                                    )
                                ),
                                ft.DataCell(
                                    ft.Container(
                                        content=ft.Text(oferta["desconto"]),
                                        padding=8,
                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                                        border_radius=8,
                                    )
                                ),
                                ft.DataCell(ft.Text(oferta["fonte"])),
                            ],
                        ) for oferta in mock_ofertas
                    ],
                ),
                padding=16,
            ),
        )

    def build_logs_viewer():
        """Constrói o viewer de logs em tempo real com design polido."""
        mock_logs = [
            "2024-01-15 15:30:45 [INFO] Sistema iniciado com sucesso",
            "2024-01-15 15:30:46 [INFO] Conectando ao banco de dados...",
            "2024-01-15 15:30:47 [INFO] Banco de dados conectado",
            "2024-01-15 15:30:48 [INFO] Iniciando scraper da Amazon...",
            "2024-01-15 15:30:49 [WARN] Timeout na requisição para Amazon",
            "2024-01-15 15:30:50 [INFO] Tentativa de reconexão...",
            "2024-01-15 15:30:51 [INFO] Reconexão bem-sucedida",
            "2024-01-15 15:30:52 [INFO] 3 ofertas encontradas na Amazon",
        ]
        
        return _section_card(
            page,
            "📝 Logs em Tempo Real",
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(expand=True),
                            ft.ElevatedButton(
                                text="🔄 Atualizar",
                                icon=ft.Icons.REFRESH,
                                on_click=lambda e: print("Atualizar logs"),
                                style=ft.ButtonStyle(
                                    bgcolor=ACCENT,
                                    color=ft.Colors.WHITE,
                                    padding=ft.padding.symmetric(horizontal=16, vertical=8)
                                )
                            ),
                            ft.ElevatedButton(
                                text="🧹 Limpar",
                                icon=ft.Icons.CLEAR_ALL,
                                on_click=lambda e: print("Limpar logs"),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.with_opacity(0.1, _surface(page)),
                                    color=_surface(page),
                                    padding=ft.padding.symmetric(horizontal=16, vertical=8)
                                )
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    log,
                                    size=12,
                                    font_family="monospace",
                                    color=ft.Colors.GREEN if "[INFO]" in log else 
                                          ft.Colors.ORANGE if "[WARN]" in log else 
                                          ft.Colors.RED if "[ERROR]" in log else 
                                          _surface(page),
                                ) for log in mock_logs
                            ],
                            spacing=6,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        padding=16,
                        bgcolor=ft.Colors.with_opacity(0.05, _surface(page)),
                        border_radius=12,
                        height=200,
                    ),
                ],
                spacing=16,
            )
        ) 

    def build_config_tab():
        """Constrói a aba de configurações com design polido."""
        return ft.Column(
            [
                ft.Text(
                    "⚙️ Configurações do Sistema",
                    size=24,
                    weight=ft.FontWeight.W_700,
                    color=_surface(page)
                ),
                ft.Divider(height=32, color=ft.Colors.with_opacity(0.1, _surface(page))),
                
                # Seção Aparência
                _section_card(
                    page,
                    "🎨 Aparência",
                    ft.Column(
                        [
                            build_config_row("Tema:", ft.Dropdown(
                                label="Tema da interface",
                                hint_text="Escolha o tema",
                                options=[
                                    ft.dropdown.Option("light", "Claro"),
                                    ft.dropdown.Option("dark", "Escuro"),
                                    ft.dropdown.Option("system", "Seguir SO"),
                                ],
                                value="light",
                                width=200,
                            )),
                            build_config_row("Densidade:", ft.Dropdown(
                                label="Densidade da UI",
                                hint_text="Escolha a densidade",
                                options=[
                                    ft.dropdown.Option("comfortable", "Confortável"),
                                    ft.dropdown.Option("compact", "Compacta"),
                                ],
                                value="comfortable",
                                width=200,
                            )),
                        ],
                        spacing=16
                    )
                ),
                
                # Seção Dados
                _section_card(
                    page,
                    "📊 Dados",
                    ft.Column(
                        [
                            build_config_row("Janela padrão:", ft.Dropdown(
                                label="Período padrão",
                                hint_text="Escolha o período",
                                options=[
                                    ft.dropdown.Option("24h", "24 horas"),
                                    ft.dropdown.Option("7d", "7 dias"),
                                    ft.dropdown.Option("30d", "30 dias"),
                                    ft.dropdown.Option("all", "Tudo"),
                                ],
                                value="24h",
                                width=200,
                            )),
                            build_config_row("Limite de ofertas:", ft.TextField(
                                label="Máximo de ofertas na tabela",
                                hint_text="Ex: 500",
                                value="500",
                                width=200,
                                keyboard_type=ft.KeyboardType.NUMBER,
                            )),
                        ],
                        spacing=16
                    )
                ),
                
                # Seção Scraper
                _section_card(
                    page,
                    "🕷️ Scraper",
                    ft.Column(
                        [
                            build_config_row("Timeout (s):", ft.TextField(
                                label="Timeout das requisições",
                                hint_text="Ex: 30",
                                value="30",
                                width=200,
                                keyboard_type=ft.KeyboardType.NUMBER,
                            )),
                            build_config_row("Retries:", ft.TextField(
                                label="Número de tentativas",
                                hint_text="Ex: 3",
                                value="3",
                                width=200,
                                keyboard_type=ft.KeyboardType.NUMBER,
                            )),
                            build_config_row("Intervalo (ms):", ft.TextField(
                                label="Intervalo entre requisições",
                                hint_text="Ex: 1000",
                                value="1000",
                                width=200,
                                keyboard_type=ft.KeyboardType.NUMBER,
                            )),
                        ],
                        spacing=16
                    )
                ),
                
                # Seção Bot
                _section_card(
                    page,
                    "🤖 Bot Telegram",
                    ft.Column(
                        [
                            build_config_row("Token:", ft.TextField(
                                label="Token do bot",
                                hint_text="Ex: 1234567890:ABC...",
                                value="",
                                width=300,
                                password=True,
                            )),
                            build_config_row("Chat ID:", ft.TextField(
                                label="ID do chat",
                                hint_text="Ex: -1001234567890",
                                value="",
                                width=200,
                            )),
                        ],
                        spacing=16
                    )
                ),
                
                # Botões de ação
                ft.Container(
                    content=ft.Row(
                        [
                            ft.ElevatedButton(
                                text="💾 Salvar e Aplicar",
                                icon=ft.Icons.SAVE,
                                on_click=lambda e: print("Configurações salvas!"),
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=ACCENT,
                                    padding=ft.padding.symmetric(horizontal=24, vertical=12)
                                ),
                            ),
                            ft.ElevatedButton(
                                text="🔄 Restaurar Padrões",
                                icon=ft.Icons.RESTORE,
                                on_click=lambda e: print("Configurações restauradas!"),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.with_opacity(0.1, _surface(page)),
                                    color=_surface(page),
                                    padding=ft.padding.symmetric(horizontal=24, vertical=12)
                                ),
                            ),
                        ],
                        spacing=16,
                    ),
                    padding=20,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=24,
        )

    def build_config_row(label: str, control):
        """Constrói uma linha de configuração."""
        return ft.Row(
            [
                ft.Text(label, width=120, color=_surface(page)),
                control,
            ],
            spacing=20,
        )

    def build_controls_tab():
        """Constrói a aba de controles com design polido."""
        return ft.Column(
            [
                ft.Text(
                    "🎮 Controles do Sistema",
                    size=24,
                    weight=ft.FontWeight.W_700,
                    color=_surface(page)
                ),
                ft.Divider(height=32, color=ft.Colors.with_opacity(0.1, _surface(page))),
                
                # Status do sistema
                _section_card(
                    page,
                    "📊 Status do Sistema",
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.GREEN, size=16),
                                ft.Text("Sistema Ativo", size=16, weight=ft.FontWeight.W_600, color=_surface(page)),
                            ]
                        ),
                        padding=16,
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                        border_radius=12,
                    ),
                ),
                
                # Controles principais
                _section_card(
                    page,
                    "🎛️ Controles Principais",
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                text="▶️ Iniciar Coleta",
                                icon=ft.Icons.PLAY_ARROW,
                                on_click=lambda e: print("🟢 Sistema iniciado!"),
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.GREEN,
                                    padding=ft.padding.symmetric(horizontal=24, vertical=12)
                                ),
                            ),
                            ft.ElevatedButton(
                                text="⏹️ Parar Coleta",
                                icon=ft.Icons.STOP,
                                on_click=lambda e: print("🔴 Sistema parado!"),
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.RED,
                                    padding=ft.padding.symmetric(horizontal=24, vertical=12)
                                ),
                            ),
                        ],
                        spacing=16,
                    ),
                ),
                
                # Estatísticas
                _section_card(
                    page,
                    "📈 Estatísticas",
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("Total de Ofertas", size=12, color=ft.Colors.with_opacity(0.7, _surface(page))),
                                        ft.Text(
                                            str(mock_metrics["total_ofertas"]),
                                            size=24,
                                            weight=ft.FontWeight.W_700,
                                            color=_surface(page)
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                padding=20,
                                bgcolor=ft.Colors.with_opacity(0.05, _surface(page)),
                                border_radius=12,
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("Ofertas Postadas", size=12, color=ft.Colors.with_opacity(0.7, _surface(page))),
                                        ft.Text(
                                            str(mock_metrics["ofertas_hoje"]),
                                            size=24,
                                            weight=ft.FontWeight.W_700,
                                            color=_surface(page)
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                padding=20,
                                bgcolor=ft.Colors.with_opacity(0.05, _surface(page)),
                                border_radius=12,
                                expand=True,
                            ),
                        ],
                        spacing=16,
                    ),
                ),
                
                # Ações rápidas
                _section_card(
                    page,
                    "🚀 Ações Rápidas",
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        text="🔄 Recarregar Métricas",
                                        icon=ft.Icons.REFRESH,
                                        on_click=lambda e: print("📊 Métricas recarregadas!"),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.with_opacity(0.1, _surface(page)),
                                            color=_surface(page),
                                            padding=ft.padding.symmetric(horizontal=20, vertical=10)
                                        ),
                                    ),
                                    ft.ElevatedButton(
                                        text="🧹 Limpar Logs",
                                        icon=ft.Icons.CLEANING_SERVICES,
                                        on_click=lambda e: print("🧹 Logs limpos!"),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.with_opacity(0.1, _surface(page)),
                                            color=_surface(page),
                                            padding=ft.padding.symmetric(horizontal=20, vertical=10)
                                        ),
                                    ),
                                ],
                                spacing=16,
                            ),
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        text="📁 Abrir Pasta de Logs",
                                        icon=ft.Icons.FOLDER_OPEN,
                                        on_click=lambda e: print("📁 Pasta de logs aberta!"),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.with_opacity(0.1, _surface(page)),
                                            color=_surface(page),
                                            padding=ft.padding.symmetric(horizontal=20, vertical=10)
                                        ),
                                    ),
                                    ft.ElevatedButton(
                                        text="📊 Exportar CSV",
                                        icon=ft.Icons.DOWNLOAD,
                                        on_click=lambda e: print("📊 CSV exportado!"),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.with_opacity(0.1, _surface(page)),
                                            color=_surface(page),
                                            padding=ft.padding.symmetric(horizontal=20, vertical=10)
                                        ),
                                    ),
                                ],
                                spacing=16,
                            ),
                        ],
                        spacing=16,
                    ),
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=24,
        )

    def build_dashboard():
        """Constrói a interface principal."""
        return ft.Column(
            [
                build_app_bar(),
                build_tabs(),
                build_content()
            ],
            expand=True,
            spacing=0
        )

    # Retornar o dashboard construído
    return build_dashboard()

def main(page: ft.Page):
    """Função principal do dashboard."""
    # Configurar página
    page.title = "Garimpeiro Geek - Dashboard"
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.window_width = 1400
    page.window_height = 900
    page.window_resizable = True
    page.padding = 0
    page.bgcolor = ft.Colors.with_opacity(0.02, ft.Colors.WHITE)

    # Criar e adicionar dashboard
    dashboard = create_dashboard_app(page)
    page.add(dashboard)

    # Atualizar página
    page.update()

if __name__ == "__main__":
    ft.app(target=main) 
