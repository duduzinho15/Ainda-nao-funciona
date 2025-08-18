"""
Dashboard principal do Garimpeiro Geek.
Integra todas as abas e funcionalidades.
"""

import flet as ft


def create_dashboard_app(page: ft.Page):
    """Cria a aplicação principal do dashboard."""
    
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
    
    def build_dashboard():
        """Constrói a interface principal."""
        return ft.Container(
            content=ft.Column(
                [build_header(), build_tabs(), build_content()]
            ),
            expand=True,
        )

    def build_header():
        """Constrói o cabeçalho da aplicação."""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.SEARCH, size=32, color=ft.Colors.PRIMARY),
                    ft.Text(
                        "Garimpeiro Geek - Dashboard",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PRIMARY,
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.SETTINGS,
                        tooltip="Configurações",
                        on_click=on_settings_click,
                    ),
                ]
            ),
            padding=20,
            bgcolor=ft.Colors.ON_SURFACE_VARIANT,
        )

    def build_tabs():
        """Constrói a barra de abas."""
        return ft.Tabs(
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
        )

    def build_content():
        """Constrói o conteúdo da aba selecionada."""
        return ft.Container(content=get_tab_content(), expand=True, padding=20)

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
        """Constrói a aba de logs com métricas e gráficos."""
        return ft.Column(
            controls=[
                # Cards de métricas
                build_metrics_cards(),
                ft.Divider(height=20),
                
                # Filtros de período
                build_period_filters(),
                ft.Divider(height=20),
                
                # Gráfico de distribuição por loja
                build_store_chart(),
                ft.Divider(height=20),
                
                # Tabela de ofertas
                build_ofertas_table(),
                ft.Divider(height=20),
                
                # Logs em tempo real
                build_logs_viewer(),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
        )

    def build_metrics_cards():
        """Constrói os cards de métricas principais."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("📊 Métricas do Sistema", size=20, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            build_metric_card(
                                "Total de Ofertas",
                                str(mock_metrics["total_ofertas"]),
                                ft.Icons.TAG,
                                ft.Colors.BLUE
                            ),
                            build_metric_card(
                                "Ofertas Hoje",
                                str(mock_metrics["ofertas_hoje"]),
                                ft.Icons.TODAY,
                                ft.Colors.GREEN
                            ),
                            build_metric_card(
                                "Lojas Ativas",
                                str(mock_metrics["lojas_ativas"]),
                                ft.Icons.STORE,
                                ft.Colors.ORANGE
                            ),
                            build_metric_card(
                                "Preço Médio",
                                f"R$ {mock_metrics['preco_medio']:.2f}",
                                ft.Icons.ATTACH_MONEY,
                                ft.Colors.PURPLE
                            ),
                        ],
                        spacing=20,
                    ),
                ],
                spacing=15,
            ),
            padding=20,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
        )

    def build_metric_card(title: str, value: str, icon: str, color: str):
        """Constrói um card de métrica individual."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=32, color=color),
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(title, size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=20,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
            expand=True,
            bgcolor=ft.Colors.SURFACE,
        )

    def build_period_filters():
        """Constrói os filtros de período."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("⏰ Filtros de Período", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                text="24h",
                                on_click=lambda e: on_period_change("24h"),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.PRIMARY if current_period == "24h" else ft.Colors.SURFACE,
                                    color=ft.Colors.ON_PRIMARY if current_period == "24h" else ft.Colors.ON_SURFACE,
                                ),
                            ),
                            ft.ElevatedButton(
                                text="7 dias",
                                on_click=lambda e: on_period_change("7d"),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.PRIMARY if current_period == "7d" else ft.Colors.SURFACE,
                                    color=ft.Colors.ON_PRIMARY if current_period == "7d" else ft.Colors.ON_SURFACE,
                                ),
                            ),
                            ft.ElevatedButton(
                                text="30 dias",
                                on_click=lambda e: on_period_change("30d"),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.PRIMARY if current_period == "30d" else ft.Colors.SURFACE,
                                    color=ft.Colors.ON_PRIMARY if current_period == "30d" else ft.Colors.ON_SURFACE,
                                ),
                            ),
                            ft.ElevatedButton(
                                text="Tudo",
                                on_click=lambda e: on_period_change("all"),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.PRIMARY if current_period == "all" else ft.Colors.SURFACE,
                                    color=ft.Colors.ON_PRIMARY if current_period == "all" else ft.Colors.ON_SURFACE,
                                ),
                            ),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=15,
            ),
            padding=20,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
        )

    def build_store_chart():
        """Constrói o gráfico de distribuição por loja."""
        # Dados simulados para o gráfico
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
                                    ft.Text(store["loja"], size=14, weight=ft.FontWeight.NORMAL),
                                    ft.Container(expand=True),
                                    ft.Text(str(store["ofertas"]), size=14, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=20,
                            ),
                            ft.Container(
                                content=ft.Container(
                                    width=store["ofertas"] * 3,  # Barra proporcional
                                    height=20,
                                    bgcolor=ft.Colors.PRIMARY,
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
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("🏪 Distribuição por Loja", size=18, weight=ft.FontWeight.BOLD),
                    *chart_items,
                ],
                spacing=15,
            ),
            padding=20,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
        )

    def build_ofertas_table():
        """Constrói a tabela de ofertas."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("📋 Últimas Ofertas", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("Data")),
                                ft.DataColumn(ft.Text("Loja")),
                                ft.DataColumn(ft.Text("Produto")),
                                ft.DataColumn(ft.Text("Preço")),
                                ft.DataColumn(ft.Text("Desconto")),
                                ft.DataColumn(ft.Text("Fonte")),
                            ],
                            rows=[
                                ft.DataRow(
                                    cells=[
                                        ft.DataCell(ft.Text(oferta["data"][:16])),
                                        ft.DataCell(
                                            ft.Container(
                                                content=ft.Text(oferta["loja"]),
                                                padding=5,
                                                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                                                border_radius=5,
                                            )
                                        ),
                                        ft.DataCell(ft.Text(oferta["titulo"])),
                                        ft.DataCell(
                                            ft.Column(
                                                [
                                                    ft.Text(f"R$ {oferta['preco']:.2f}", weight=ft.FontWeight.BOLD),
                                                    ft.Text(f"R$ {oferta['preco_original']:.2f}", 
                                                           size=12, 
                                                           color=ft.Colors.ON_SURFACE_VARIANT),
                                                ],
                                                spacing=2,
                                            )
                                        ),
                                        ft.DataCell(
                                            ft.Container(
                                                content=ft.Text(oferta["desconto"]),
                                                padding=5,
                                                bgcolor=ft.Colors.GREEN,
                                                border_radius=5,
                                            )
                                        ),
                                        ft.DataCell(ft.Text(oferta["fonte"])),
                                    ],
                                ) for oferta in mock_ofertas
                            ],
                        ),
                        padding=10,
                    ),
                ],
                spacing=15,
            ),
            padding=20,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
        )

    def build_logs_viewer():
        """Constrói o viewer de logs em tempo real."""
        # Logs simulados
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
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("📝 Logs em Tempo Real", size=18, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.ElevatedButton(
                                text="🔄 Atualizar",
                                icon=ft.Icons.REFRESH,
                                on_click=on_refresh_logs,
                            ),
                            ft.ElevatedButton(
                                text="🧹 Limpar",
                                icon=ft.Icons.CLEAR_ALL,
                                on_click=on_clear_logs,
                            ),
                        ],
                        spacing=20,
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
                                          ft.Colors.ON_SURFACE,
                                ) for log in mock_logs
                            ],
                            spacing=5,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        padding=10,
                        bgcolor=ft.Colors.SURFACE,
                        border_radius=5,
                        height=200,
                    ),
                ],
                spacing=15,
            ),
            padding=20,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
        )

    def build_config_tab():
        """Constrói a aba de configurações."""
        return ft.Column(
            controls=[
                ft.Text("⚙️ Configurações do Sistema", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                
                # Seção Aparência
                build_config_section(
                    "🎨 Aparência",
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
                    ]
                ),
                
                # Seção Dados
                build_config_section(
                    "📊 Dados",
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
                    ]
                ),
                
                # Seção Scraper
                build_config_section(
                    "🕷️ Scraper",
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
                    ]
                ),
                
                # Seção Bot
                build_config_section(
                    "🤖 Bot Telegram",
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
                    ]
                ),
                
                # Botões de ação
                ft.Container(
                    content=ft.Row(
                        [
                            ft.ElevatedButton(
                                text="💾 Salvar e Aplicar",
                                icon=ft.Icons.SAVE,
                                on_click=on_save_config,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.ON_PRIMARY,
                                    bgcolor=ft.Colors.PRIMARY,
                                ),
                            ),
                            ft.ElevatedButton(
                                text="🔄 Restaurar Padrões",
                                icon=ft.Icons.RESTORE,
                                on_click=on_reset_config,
                            ),
                        ],
                        spacing=20,
                    ),
                    padding=20,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
        )

    def build_config_section(title: str, controls: list):
        """Constrói uma seção de configuração."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                    *controls,
                ],
                spacing=15,
            ),
            padding=20,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
        )

    def build_config_row(label: str, control):
        """Constrói uma linha de configuração."""
        return ft.Row(
            [
                ft.Text(label, width=120),
                control,
            ],
            spacing=20,
        )

    def build_controls_tab():
        """Constrói a aba de controles."""
        return ft.Column(
            controls=[
                ft.Text("🎮 Controles do Sistema", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                
                # Status do sistema
                build_controls_section(
                    "📊 Status do Sistema",
                    [
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.GREEN, size=16),
                                    ft.Text("Sistema Ativo", size=16, weight=ft.FontWeight.BOLD),
                                ]
                            ),
                            padding=10,
                            border=ft.border.all(1, ft.Colors.OUTLINE),
                            border_radius=8,
                            bgcolor=ft.Colors.SURFACE,
                        ),
                    ]
                ),
                
                # Controles principais
                build_controls_section(
                    "🎛️ Controles Principais",
                    [
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    text="▶️ Iniciar Coleta",
                                    icon=ft.Icons.PLAY_ARROW,
                                    on_click=on_start_scraping,
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.ON_PRIMARY,
                                        bgcolor=ft.Colors.GREEN,
                                    ),
                                ),
                                ft.ElevatedButton(
                                    text="⏹️ Parar Coleta",
                                    icon=ft.Icons.STOP,
                                    on_click=on_stop_scraping,
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.ON_PRIMARY,
                                        bgcolor=ft.Colors.RED,
                                    ),
                                ),
                            ],
                            spacing=20,
                        ),
                    ]
                ),
                
                # Estatísticas
                build_controls_section(
                    "📈 Estatísticas",
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text("Total de Ofertas", size=12),
                                            ft.Text(str(mock_metrics["total_ofertas"]), 
                                                   size=24, 
                                                   weight=ft.FontWeight.BOLD),
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                    padding=20,
                                    border=ft.border.all(1, ft.Colors.OUTLINE),
                                    border_radius=8,
                                    expand=True,
                                ),
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text("Ofertas Postadas", size=12),
                                            ft.Text(str(mock_metrics["ofertas_hoje"]), 
                                                   size=24, 
                                                   weight=ft.FontWeight.BOLD),
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                    padding=20,
                                    border=ft.border.all(1, ft.Colors.OUTLINE),
                                    border_radius=8,
                                    expand=True,
                                ),
                            ],
                            spacing=20,
                        ),
                    ]
                ),
                
                # Ações rápidas
                build_controls_section(
                    "🚀 Ações Rápidas",
                    [
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    text="🔄 Recarregar Métricas",
                                    icon=ft.Icons.REFRESH,
                                    on_click=on_reload_metrics,
                                ),
                                ft.ElevatedButton(
                                    text="🧹 Limpar Logs",
                                    icon=ft.Icons.CLEANING_SERVICES,
                                    on_click=on_clear_logs,
                                ),
                            ],
                            spacing=20,
                        ),
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    text="📁 Abrir Pasta de Logs",
                                    icon=ft.Icons.FOLDER_OPEN,
                                    on_click=on_open_logs_folder,
                                ),
                                ft.ElevatedButton(
                                    text="📊 Exportar CSV",
                                    icon=ft.Icons.DOWNLOAD,
                                    on_click=on_export_csv,
                                ),
                            ],
                            spacing=20,
                        ),
                    ]
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
        )

    def build_controls_section(title: str, controls: list):
        """Constrói uma seção de controles."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                    *controls,
                ],
                spacing=15,
            ),
            padding=20,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
        )

    # Event handlers
    def on_tab_change(e):
        """Chamado quando a aba muda."""
        nonlocal current_tab
        current_tab = int(e.data)
        print(f"Tab mudou para: {current_tab}")

    def on_period_change(period: str):
        """Chamado quando o período muda."""
        nonlocal current_period
        current_period = period
        print(f"Período mudou para: {period}")

    def on_settings_click(e):
        """Chamado quando o botão de configurações é clicado."""
        print("Configurações rápidas")

    def on_save_config(e):
        """Chamado quando o botão salvar é clicado."""
        print("Configurações salvas!")

    def on_reset_config(e):
        """Chamado quando o botão reset é clicado."""
        print("Configurações restauradas para padrão!")

    def on_start_scraping(e):
        """Chamado quando o botão iniciar é clicado."""
        print("🟢 Sistema iniciado!")

    def on_stop_scraping(e):
        """Chamado quando o botão parar é clicado."""
        print("🔴 Sistema parado!")

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

    def on_refresh_logs(e):
        """Chamado quando o botão atualizar logs é clicado."""
        print("🔄 Logs atualizados!")

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

    # Criar e adicionar dashboard
    dashboard = create_dashboard_app(page)
    page.add(dashboard)

    # Atualizar página
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
