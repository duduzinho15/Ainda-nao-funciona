"""
Aba de configurações do dashboard Garimpeiro Geek.
"""

import flet as ft
from typing import Callable, Optional
from core.settings import SystemConfig
from core.storage import ConfigStorage


def create_config_tab(
    config_storage: ConfigStorage,
    on_config_changed: Optional[Callable[[SystemConfig], None]] = None,
) -> ft.Control:
    """Cria a aba de configurações do sistema."""
    
    # Estado (será implementado quando necessário)

    def build_config_tab():
        """Constrói a interface da aba."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    build_header(),
                    ft.Divider(),
                    build_appearance_section(),
                    ft.Divider(),
                    build_data_section(),
                    ft.Divider(),
                    build_scraper_section(),
                    ft.Divider(),
                    build_bot_section(),
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
                        "⚙️ Configurações do Sistema", size=24, weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        "Configure as preferências do dashboard e comportamento do sistema",
                        size=14,
                        color=ft.colors.ON_SURFACE_VARIANT,
                    ),
                ]
            ),
            padding=ft.padding.only(bottom=20),
        )

    def build_appearance_section() -> ft.Control:
        """Constrói a seção de aparência."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("🎨 Aparência", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.Text("Tema:", width=120),
                            ft.Dropdown(
                                label="Tema da interface",
                                hint_text="Escolha o tema",
                                options=[
                                    ft.dropdown.Option("light", "Claro"),
                                    ft.dropdown.Option("dark", "Escuro"),
                                    ft.dropdown.Option("system", "Seguir SO"),
                                ],
                                value="light",
                                width=200,
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Text("Densidade:", width=120),
                            ft.Dropdown(
                                label="Densidade da UI",
                                hint_text="Escolha a densidade",
                                options=[
                                    ft.dropdown.Option("comfortable", "Confortável"),
                                    ft.dropdown.Option("compact", "Compacta"),
                                ],
                                value="comfortable",
                                width=200,
                            ),
                        ]
                    ),
                ],
                spacing=15,
            ),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=8,
        )

    def build_data_section() -> ft.Control:
        """Constrói a seção de dados."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("📊 Dados", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.Text("Janela padrão:", width=120),
                            ft.Dropdown(
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
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Text("Limite de ofertas:", width=120),
                            ft.TextField(
                                label="Máximo de ofertas na tabela",
                                hint_text="Ex: 500",
                                value="500",
                                width=200,
                                keyboard_type=ft.KeyboardType.NUMBER,
                            ),
                        ]
                    ),
                ],
                spacing=15,
            ),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=8,
        )

    def build_scraper_section() -> ft.Control:
        """Constrói a seção do scraper."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("🕷️ Scraper", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.Text("Timeout (s):", width=120),
                            ft.TextField(
                                label="Timeout das requisições",
                                hint_text="Ex: 30",
                                value="30",
                                width=200,
                                keyboard_type=ft.KeyboardType.NUMBER,
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Text("Retries:", width=120),
                            ft.TextField(
                                label="Número de tentativas",
                                hint_text="Ex: 3",
                                value="3",
                                width=200,
                                keyboard_type=ft.KeyboardType.NUMBER,
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Text("Intervalo (ms):", width=120),
                            ft.TextField(
                                label="Intervalo entre requisições",
                                hint_text="Ex: 1000",
                                value="1000",
                                width=200,
                                keyboard_type=ft.KeyboardType.NUMBER,
                            ),
                        ]
                    ),
                ],
                spacing=15,
            ),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=8,
        )

    def build_bot_section() -> ft.Control:
        """Constrói a seção do bot."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("🤖 Bot Telegram", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.Text("Token:", width=120),
                            ft.TextField(
                                label="Token do bot",
                                hint_text="Ex: 1234567890:ABC...",
                                value="",
                                width=300,
                                password=True,
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Text("Chat ID:", width=120),
                            ft.TextField(
                                label="ID do chat",
                                hint_text="Ex: -1001234567890",
                                value="",
                                width=200,
                            ),
                        ]
                    ),
                ],
                spacing=15,
            ),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=8,
        )

    def build_actions_section() -> ft.Control:
        """Constrói a seção de ações."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("⚡ Ações", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                text="💾 Salvar e Aplicar",
                                icon=ft.icons.SAVE,
                                on_click=on_save_click,
                                style=ft.ButtonStyle(
                                    color=ft.colors.ON_PRIMARY,
                                    bgcolor=ft.colors.PRIMARY,
                                ),
                            ),
                            ft.OutlinedButton(
                                text="🔄 Restaurar Padrões",
                                icon=ft.icons.RESTORE,
                                on_click=on_reset_click,
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

    def on_save_click(e):
        """Chamado quando o botão salvar é clicado."""
        print("Configurações salvas!")
        if on_config_changed:
            # Por enquanto, criar uma configuração padrão
            on_config_changed(SystemConfig())

    def on_reset_click(e):
        """Chamado quando o botão reset é clicado."""
        print("Configurações restauradas para padrão!")

    # Retornar a aba construída
    return build_config_tab()
