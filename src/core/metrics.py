"""
Sistema de métricas do Garimpeiro Geek
"""

import json
from datetime import datetime
from typing import Any, Dict, List


class Metrics:
    """Classe para armazenar métricas do sistema"""

    def __init__(
        self, total_ofertas: int = 0, lojas_ativas: int = 0, preco_medio: float = 0.0
    ):
        self.total_ofertas = total_ofertas
        self.lojas_ativas = lojas_ativas
        self.preco_medio = preco_medio
        self.timestamp = datetime.now()

    def preco_medio_formatado(self) -> str:
        """Retorna o preço médio formatado como moeda"""
        return f"R$ {self.preco_medio:.2f}".replace(".", ",")

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "total_ofertas": self.total_ofertas,
            "lojas_ativas": self.lojas_ativas,
            "preco_medio": self.preco_medio,
            "timestamp": self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        return f"Ofertas: {self.total_ofertas}, Lojas: {self.lojas_ativas}, Preço: {self.preco_medio_formatado()}"


class MetricsCollector:
    """Coletor de métricas do sistema"""

    def __init__(self):
        self.metrics_history: List[Metrics] = []
        self.current_metrics = Metrics()

    def update_metrics(self, total_ofertas: int, lojas_ativas: int, preco_medio: float):
        """Atualiza as métricas atuais"""
        self.current_metrics = Metrics(total_ofertas, lojas_ativas, preco_medio)
        self.metrics_history.append(self.current_metrics)

        # Manter apenas as últimas 100 métricas
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]

    def get_current_metrics(self) -> Metrics:
        """Retorna as métricas atuais"""
        return self.current_metrics

    def get_metrics_history(self, limit: int = 50) -> List[Metrics]:
        """Retorna o histórico de métricas"""
        return self.metrics_history[-limit:] if self.metrics_history else []

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna um resumo das métricas"""
        if not self.metrics_history:
            return {
                "total_ofertas": 0,
                "lojas_ativas": 0,
                "preco_medio": 0.0,
                "tendencia": "estavel",
            }

        # Calcular tendência
        if len(self.metrics_history) >= 2:
            ultima = self.metrics_history[-1]
            penultima = self.metrics_history[-2]

            if ultima.total_ofertas > penultima.total_ofertas:
                tendencia = "crescendo"
            elif ultima.total_ofertas < penultima.total_ofertas:
                tendencia = "diminuindo"
            else:
                tendencia = "estavel"
        else:
            tendencia = "estavel"

        return {
            "total_ofertas": self.current_metrics.total_ofertas,
            "lojas_ativas": self.current_metrics.lojas_ativas,
            "preco_medio": self.current_metrics.preco_medio,
            "tendencia": tendencia,
            "ultima_atualizacao": self.current_metrics.timestamp.isoformat(),
        }

    def export_metrics(self, format: str = "json") -> str:
        """Exporta métricas em diferentes formatos"""
        if format.lower() == "json":
            return json.dumps(self.get_metrics_summary(), indent=2, ensure_ascii=False)
        elif format.lower() == "csv":
            return self._export_csv()
        else:
            raise ValueError(f"Formato não suportado: {format}")

    def _export_csv(self) -> str:
        """Exporta métricas em formato CSV"""
        if not self.metrics_history:
            return "timestamp,total_ofertas,lojas_ativas,preco_medio\n"

        csv_lines = ["timestamp,total_ofertas,lojas_ativas,preco_medio\n"]

        for metric in self.metrics_history:
            csv_lines.append(
                f"{metric.timestamp.isoformat()},{metric.total_ofertas},{metric.lojas_ativas},{metric.preco_medio}\n"
            )

        return "".join(csv_lines)

    def clear_history(self):
        """Limpa o histórico de métricas"""
        self.metrics_history.clear()
        print("🗑️ Histórico de métricas limpo")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de performance"""
        if not self.metrics_history:
            return {}

        precos = [m.preco_medio for m in self.metrics_history if m.preco_medio > 0]

        if not precos:
            return {}

        return {
            "preco_minimo": min(precos),
            "preco_maximo": max(precos),
            "preco_medio_geral": sum(precos) / len(precos),
            "total_registros": len(self.metrics_history),
            "periodo_cobertura": {
                "inicio": self.metrics_history[0].timestamp.isoformat(),
                "fim": self.metrics_history[-1].timestamp.isoformat(),
            },
        }
