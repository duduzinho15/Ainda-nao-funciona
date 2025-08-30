"""
Componentes UI para o Dashboard Flet
Cards, gráficos e elementos visuais para métricas
"""

import flet as ft
from typing import List, Dict, Any, Optional
import math


class MetricCard:
    """Card de métrica com valor, título e indicador de status"""
    
    def __init__(self, title: str, value: str, subtitle: str = "", 
                 color: str = ft.Colors.BLUE_400, alert: bool = False,
                 tooltip: str = ""):
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.color = color
        self.alert = alert
        self.tooltip = tooltip
    
    def build(self) -> ft.Container:
        """Constrói o card de métrica"""
        # Cor baseada no alerta
        if self.alert:
            bg_color = ft.Colors.RED_900
            border_color = ft.Colors.RED_400
        else:
            bg_color = ft.Colors.BLUE_800
            border_color = ft.Colors.BLUE_400
        
        # Ícone de alerta se necessário
        alert_icon = ft.Icon(
            ft.Icons.WARNING,
            color=ft.Colors.ORANGE_400,
            size=16
        ) if self.alert else None
        
        # Título com ícone de alerta
        title_row = ft.Row([
            ft.Text(self.title, size=14, color=ft.Colors.GREY_400),
            alert_icon
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN) if alert_icon else ft.Text(self.title, size=14, color=ft.Colors.GREY_400)
        
        content = ft.Column([
            title_row,
            ft.Text(self.value, size=28, weight=ft.FontWeight.BOLD, color=self.color),
            ft.Text(self.subtitle, size=12, color=ft.Colors.GREY_500) if self.subtitle else ft.Container()
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)
        
        card = ft.Container(
            content=content,
            width=200,
            height=120,
            bgcolor=bg_color,
            border_radius=12,
            padding=15,
            border=ft.border.all(1, border_color),
            alignment=ft.alignment.center
        )
        
        # Adicionar tooltip se fornecido
        if self.tooltip:
            card.tooltip = self.tooltip
        
        return card


class PieChart:
    """Gráfico de pizza/rosca"""
    
    def __init__(self, title: str, data: List[Dict[str, Any]], 
                 value_key: str = "value", label_key: str = "label"):
        self.title = title
        self.data = data
        self.value_key = value_key
        self.label_key = label_key
    
    def build(self) -> ft.Container:
        """Constrói o gráfico de pizza"""
        if not self.data:
            return ft.Container(
                content=ft.Column([
                    ft.Text(self.title, size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("Sem dados disponíveis", size=14, color=ft.Colors.GREY_400)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                bgcolor=ft.Colors.BLUE_800,
                border_radius=12,
                width=300,
                height=250
            )
        
        # Cores para as fatias
        colors = [
            ft.Colors.BLUE_400,
            ft.Colors.GREEN_400,
            ft.Colors.ORANGE_400,
            ft.Colors.PURPLE_400,
            ft.Colors.YELLOW_400,
            ft.Colors.RED_400
        ]
        
        # Criar fatias do gráfico
        total = sum(item[self.value_key] for item in self.data)
        sections = []
        
        for i, item in enumerate(self.data):
            if total > 0:
                percentage = (item[self.value_key] / total) * 100
                sections.append(
                    ft.PieChartSection(
                        value=item[self.value_key],
                        color=colors[i % len(colors)],
                        radius=80,
                        title=f"{percentage:.1f}%",
                        title_style=ft.TextStyle(
                            size=12,
                            color=ft.Colors.WHITE,
                            weight=ft.FontWeight.BOLD
                        )
                    )
                )
        
        # Legenda
        legend_items = []
        for i, item in enumerate(self.data):
            legend_items.append(
                ft.Row([
                    ft.Container(
                        width=12,
                        height=12,
                        bgcolor=colors[i % len(colors)],
                        border_radius=2
                    ),
                    ft.Text(f"{item[self.label_key]}: {item[self.value_key]}", size=12)
                ], spacing=8)
            )
        
        chart = ft.PieChart(
            sections=sections,
            sections_space=2,
            center_space_radius=30,
            expand=True
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text(self.title, size=18, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Container(chart, width=200, height=200),
                    ft.Column(legend_items, spacing=5)
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=20,
            bgcolor=ft.Colors.BLUE_800,
            border_radius=12,
            width=400,
            height=280
        )


class BarChart:
    """Gráfico de barras"""
    
    def __init__(self, title: str, data: List[Dict[str, Any]], 
                 x_key: str = "label", y_key: str = "value", 
                 color: str = ft.Colors.BLUE_400):
        self.title = title
        self.data = data
        self.x_key = x_key
        self.y_key = y_key
        self.color = color
    
    def build(self) -> ft.Container:
        """Constrói o gráfico de barras"""
        if not self.data:
            return ft.Container(
                content=ft.Column([
                    ft.Text(self.title, size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("Sem dados disponíveis", size=14, color=ft.Colors.GREY_400)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                bgcolor=ft.Colors.BLUE_800,
                border_radius=12,
                width=400,
                height=250
            )
        
        # Encontrar valor máximo para escala
        max_value = max(item[self.y_key] for item in self.data) if self.data else 1
        
        # Criar grupos de barras
        bar_groups = []
        for i, item in enumerate(self.data):
            bar_groups.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=item[self.y_key],
                            width=40,
                            color=self.color,
                            tooltip=f"{item[self.x_key]}: {item[self.y_key]}",
                            border_radius=0,
                        )
                    ]
                )
            )
        
        chart = ft.BarChart(
            bar_groups=bar_groups,
            border=ft.border.all(1, ft.Colors.GREY_400),
            left_axis=ft.ChartAxis(
                labels_size=40,
                title=ft.Text("Valores"),
                title_size=40,
            ),
            bottom_axis=ft.ChartAxis(
                labels_size=40,
                title=ft.Text("Categorias"),
                title_size=40,
            ),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.Colors.GREY_700, width=1, dash_pattern=[3, 3]
            ),
            tooltip_bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.GREY_300),
            max_y=max_value * 1.1,
            interactive=True,
            expand=True,
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text(self.title, size=18, weight=ft.FontWeight.BOLD),
                ft.Container(chart, height=200, expand=True)
            ], spacing=10),
            padding=20,
            bgcolor=ft.Colors.BLUE_800,
            border_radius=12,
            width=500,
            height=280
        )


class DataTable:
    """Tabela de dados"""
    
    def __init__(self, title: str, data: List[Dict[str, Any]], 
                 columns: List[Dict[str, str]]):
        self.title = title
        self.data = data
        self.columns = columns  # [{"key": "platform", "label": "Plataforma"}, ...]
    
    def build(self) -> ft.Container:
        """Constrói a tabela de dados"""
        if not self.data:
            return ft.Container(
                content=ft.Column([
                    ft.Text(self.title, size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("Sem dados disponíveis", size=14, color=ft.Colors.GREY_400)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                bgcolor=ft.Colors.BLUE_800,
                border_radius=12,
                width=600,
                height=200
            )
        
        # Criar colunas da tabela
        table_columns = [
            ft.DataColumn(ft.Text(col["label"], weight=ft.FontWeight.BOLD))
            for col in self.columns
        ]
        
        # Criar linhas da tabela
        table_rows = []
        for item in self.data:
            cells = []
            for col in self.columns:
                value = item.get(col["key"], "")
                # Formatação especial para alguns tipos
                if isinstance(value, float):
                    if col["key"].endswith("_days"):
                        formatted_value = f"{value:.1f}d"
                    elif col["key"].endswith("_ms"):
                        formatted_value = f"{value:.0f}ms"
                    else:
                        formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
                
                cells.append(ft.DataCell(ft.Text(formatted_value)))
            
            table_rows.append(ft.DataRow(cells=cells))
        
        table = ft.DataTable(
            columns=table_columns,
            rows=table_rows,
            border=ft.border.all(1, ft.Colors.GREY_600),
            border_radius=8,
            sort_column_index=0,
            sort_ascending=True,
            heading_row_color=ft.Colors.BLUE_700,
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text(self.title, size=18, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=table,
                    border_radius=8,
                    expand=True
                )
            ], spacing=10),
            padding=20,
            bgcolor=ft.Colors.BLUE_800,
            border_radius=12,
            width=700,
            height=350
        )


class AlertBanner:
    """Banner de alerta"""
    
    def __init__(self, title: str, message: str, alert_type: str = "warning"):
        self.title = title
        self.message = message
        self.alert_type = alert_type  # "warning", "error", "info", "success"
    
    def build(self) -> ft.Container:
        """Constrói o banner de alerta"""
        # Cores e ícones por tipo
        config = {
            "warning": {
                "color": ft.Colors.ORANGE_400,
                "bg_color": ft.Colors.ORANGE_900,
                "icon": ft.Icons.WARNING
            },
            "error": {
                "color": ft.Colors.RED_400,
                "bg_color": ft.Colors.RED_900,
                "icon": ft.Icons.ERROR
            },
            "info": {
                "color": ft.Colors.BLUE_400,
                "bg_color": ft.Colors.BLUE_900,
                "icon": ft.Icons.INFO
            },
            "success": {
                "color": ft.Colors.GREEN_400,
                "bg_color": ft.Colors.GREEN_900,
                "icon": ft.Icons.CHECK_CIRCLE
            }
        }
        
        alert_config = config.get(self.alert_type, config["info"])
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    alert_config["icon"],
                    color=alert_config["color"],
                    size=24
                ),
                ft.Column([
                    ft.Text(self.title, weight=ft.FontWeight.BOLD, color=alert_config["color"]),
                    ft.Text(self.message, size=12, color=ft.Colors.GREY_300)
                ], spacing=2, expand=True)
            ], spacing=15),
            padding=15,
            bgcolor=alert_config["bg_color"],
            border_radius=8,
            border=ft.border.all(1, alert_config["color"]),
            margin=ft.margin.only(bottom=10)
        )


class ProgressIndicator:
    """Indicador de progresso circular"""
    
    def __init__(self, title: str, value: float, max_value: float = 100, 
                 unit: str = "%", color: str = ft.Colors.BLUE_400):
        self.title = title
        self.value = value
        self.max_value = max_value
        self.unit = unit
        self.color = color
    
    def build(self) -> ft.Container:
        """Constrói o indicador de progresso"""
        percentage = (self.value / self.max_value) if self.max_value > 0 else 0
        
        # Cor baseada no valor
        if percentage >= 0.9:
            ring_color = ft.Colors.GREEN_400
        elif percentage >= 0.7:
            ring_color = ft.Colors.YELLOW_400
        else:
            ring_color = ft.Colors.RED_400
        
        progress_ring = ft.ProgressRing(
            value=percentage,
            width=80,
            height=80,
            stroke_width=8,
            color=ring_color,
            bgcolor=ft.Colors.GREY_700
        )
        
        # Texto central
        center_text = ft.Container(
            content=ft.Column([
                ft.Text(f"{self.value:.1f}", size=16, weight=ft.FontWeight.BOLD),
                ft.Text(self.unit, size=10, color=ft.Colors.GREY_400)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            alignment=ft.alignment.center
        )
        
        # Stack para sobrepor o texto no anel
        progress_stack = ft.Stack([
            progress_ring,
            center_text
        ], width=80, height=80)
        
        return ft.Container(
            content=ft.Column([
                ft.Text(self.title, size=14, color=ft.Colors.GREY_400),
                progress_stack
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=15,
            bgcolor=ft.Colors.BLUE_800,
            border_radius=12,
            width=150,
            height=140,
            alignment=ft.alignment.center
        )


class StatusIndicator:
    """Indicador de status simples"""
    
    def __init__(self, label: str, status: str, details: str = ""):
        self.label = label
        self.status = status  # "ok", "warning", "error"
        self.details = details
    
    def build(self) -> ft.Row:
        """Constrói o indicador de status"""
        # Configuração por status
        config = {
            "ok": {"color": ft.Colors.GREEN_400, "icon": ft.Icons.CHECK_CIRCLE},
            "warning": {"color": ft.Colors.ORANGE_400, "icon": ft.Icons.WARNING},
            "error": {"color": ft.Colors.RED_400, "icon": ft.Icons.ERROR},
            "critical": {"color": ft.Colors.RED_600, "icon": ft.Icons.DANGEROUS}
        }
        
        status_config = config.get(self.status, config["ok"])
        
        return ft.Row([
            ft.Icon(
                status_config["icon"],
                color=status_config["color"],
                size=16
            ),
            ft.Text(self.label, size=14),
            ft.Text(self.details, size=12, color=ft.Colors.GREY_400) if self.details else ft.Container()
        ], spacing=8)
