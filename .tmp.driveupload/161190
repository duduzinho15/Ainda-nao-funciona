"""
Sistema de métricas e agregação de dados do sistema Garimpeiro Geek.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict
from .models import Oferta, MetricsSnapshot

logger = logging.getLogger(__name__)


class MetricsAggregator:
    """Agrega e calcula métricas das ofertas."""

    def __init__(self):
        """Inicializa o agregador de métricas."""
        self._ofertas: List[Oferta] = []
        self._cache: Dict[str, MetricsSnapshot] = {}

    def update(self, ofertas: List[Oferta]) -> MetricsSnapshot:
        """
        Atualiza as ofertas e calcula métricas.

        Args:
            ofertas: Lista de ofertas para processar.

        Returns:
            Snapshot das métricas calculadas.
        """
        try:
            self._ofertas = ofertas.copy()
            self._cache.clear()  # Limpar cache ao atualizar dados

            # Calcular métricas para período "Tudo"
            snapshot = self._calculate_metrics("Tudo")
            self._cache["Tudo"] = snapshot

            logger.info(f"Métricas atualizadas: {len(ofertas)} ofertas processadas")
            return snapshot

        except Exception as e:
            logger.error(f"Erro ao atualizar métricas: {e}")
            # Retornar métricas vazias em caso de erro
            return self._get_empty_snapshot("Tudo")

    def compute_from_period(self, periodo: str) -> MetricsSnapshot:
        """
        Calcula métricas para um período específico.

        Args:
            periodo: Período para calcular ("24h", "7d", "30d", "Tudo").

        Returns:
            Snapshot das métricas para o período.
        """
        try:
            # Verificar cache primeiro
            if periodo in self._cache:
                return self._cache[periodo]

            # Calcular métricas para o período
            snapshot = self._calculate_metrics(periodo)
            self._cache[periodo] = snapshot

            return snapshot

        except Exception as e:
            logger.error(f"Erro ao calcular métricas para período {periodo}: {e}")
            return self._get_empty_snapshot(periodo)

    def _calculate_metrics(self, periodo: str) -> MetricsSnapshot:
        """
        Calcula métricas para um período específico.

        Args:
            periodo: Período para calcular.

        Returns:
            Snapshot das métricas calculadas.
        """
        try:
            # Filtrar ofertas por período
            ofertas_filtradas = self._filter_ofertas_by_period(periodo)

            if not ofertas_filtradas:
                return self._get_empty_snapshot(periodo)

            # Calcular métricas básicas
            total_ofertas = len(ofertas_filtradas)
            lojas_ativas = len(set(oferta.loja for oferta in ofertas_filtradas))

            # Calcular preço médio (ignorando valores None)
            precos_validos = [
                oferta.preco for oferta in ofertas_filtradas if oferta.preco is not None
            ]
            preco_medio = (
                sum(precos_validos) / len(precos_validos) if precos_validos else None
            )

            # Calcular distribuição por loja
            distribucao_lojas = defaultdict(int)
            for oferta in ofertas_filtradas:
                distribucao_lojas[oferta.loja] += 1

            # Ordenar por quantidade (maior para menor)
            distribucao_ordenada = dict(
                sorted(distribucao_lojas.items(), key=lambda x: x[1], reverse=True)
            )

            return MetricsSnapshot(
                total_ofertas=total_ofertas,
                lojas_ativas=lojas_ativas,
                preco_medio=round(preco_medio, 2) if preco_medio else None,
                periodo=periodo,
                distribucao_lojas=distribucao_ordenada,
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Erro ao calcular métricas: {e}")
            return self._get_empty_snapshot(periodo)

    def _filter_ofertas_by_period(self, periodo: str) -> List[Oferta]:
        """
        Filtra ofertas por período.

        Args:
            periodo: Período para filtrar.

        Returns:
            Lista de ofertas filtradas.
        """
        try:
            now = datetime.now()

            if periodo == "Tudo":
                return self._ofertas

            elif periodo == "24h":
                cutoff = now - timedelta(hours=24)
            elif periodo == "7d":
                cutoff = now - timedelta(days=7)
            elif periodo == "30d":
                cutoff = now - timedelta(days=30)
            else:
                logger.warning(f"Período desconhecido: {periodo}, usando 'Tudo'")
                return self._ofertas

            return [oferta for oferta in self._ofertas if oferta.created_at >= cutoff]

        except Exception as e:
            logger.error(f"Erro ao filtrar ofertas por período: {e}")
            return self._ofertas

    def _get_empty_snapshot(self, periodo: str) -> MetricsSnapshot:
        """
        Retorna snapshot vazio para um período.

        Args:
            periodo: Período do snapshot.

        Returns:
            Snapshot vazio.
        """
        return MetricsSnapshot(
            total_ofertas=0,
            lojas_ativas=0,
            preco_medio=None,
            periodo=periodo,
            distribucao_lojas={},
            timestamp=datetime.now(),
        )

    def get_ofertas(self) -> List[Oferta]:
        """Retorna todas as ofertas carregadas."""
        return self._ofertas.copy()

    def get_ofertas_by_store(self, loja: str) -> List[Oferta]:
        """
        Retorna ofertas de uma loja específica.

        Args:
            loja: Nome da loja.

        Returns:
            Lista de ofertas da loja.
        """
        return [oferta for oferta in self._ofertas if oferta.loja == loja]

    def get_ofertas_by_price_range(
        self, min_price: float, max_price: float
    ) -> List[Oferta]:
        """
        Retorna ofertas dentro de uma faixa de preço.

        Args:
            min_price: Preço mínimo.
            max_price: Preço máximo.

        Returns:
            Lista de ofertas na faixa de preço.
        """
        return [
            oferta
            for oferta in self._ofertas
            if oferta.preco is not None and min_price <= oferta.preco <= max_price
        ]

    def get_recent_ofertas(self, limit: int = 10) -> List[Oferta]:
        """
        Retorna as ofertas mais recentes.

        Args:
            limit: Número máximo de ofertas.

        Returns:
            Lista das ofertas mais recentes.
        """
        sorted_ofertas = sorted(self._ofertas, key=lambda x: x.created_at, reverse=True)
        return sorted_ofertas[:limit]

    def get_stats_summary(self) -> Dict[str, any]:
        """
        Retorna resumo estatístico das ofertas.

        Returns:
            Dicionário com estatísticas resumidas.
        """
        try:
            if not self._ofertas:
                return {
                    "total_ofertas": 0,
                    "lojas_ativas": 0,
                    "preco_medio": None,
                    "oferta_mais_cara": None,
                    "oferta_mais_barata": None,
                    "ultima_atualizacao": None,
                }

            # Estatísticas básicas
            total_ofertas = len(self._ofertas)
            lojas_ativas = len(set(oferta.loja for oferta in self._ofertas))

            # Preços
            precos_validos = [
                oferta.preco for oferta in self._ofertas if oferta.preco is not None
            ]
            preco_medio = (
                sum(precos_validos) / len(precos_validos) if precos_validos else None
            )

            # Ofertas extremas
            oferta_mais_cara = (
                max(self._ofertas, key=lambda x: x.preco or 0)
                if precos_validos
                else None
            )
            oferta_mais_barata = (
                min(self._ofertas, key=lambda x: x.preco or float("inf"))
                if precos_validos
                else None
            )

            return {
                "total_ofertas": total_ofertas,
                "lojas_ativas": lojas_ativas,
                "preco_medio": round(preco_medio, 2) if preco_medio else None,
                "oferta_mais_cara": {
                    "titulo": oferta_mais_cara.titulo,
                    "preco": oferta_mais_cara.preco,
                    "loja": oferta_mais_cara.loja,
                }
                if oferta_mais_cara
                else None,
                "oferta_mais_barata": {
                    "titulo": oferta_mais_barata.titulo,
                    "preco": oferta_mais_barata.preco,
                    "loja": oferta_mais_barata.loja,
                }
                if oferta_mais_barata
                else None,
                "ultima_atualizacao": max(oferta.created_at for oferta in self._ofertas)
                if self._ofertas
                else None,
            }

        except Exception as e:
            logger.error(f"Erro ao calcular resumo estatístico: {e}")
            return {
                "total_ofertas": 0,
                "lojas_ativas": 0,
                "preco_medio": None,
                "oferta_mais_cara": None,
                "oferta_mais_barata": None,
                "ultima_atualizacao": None,
            }

    def clear_cache(self):
        """Limpa o cache de métricas."""
        self._cache.clear()
        logger.info("Cache de métricas limpo")

    def get_cache_info(self) -> Dict[str, any]:
        """Retorna informações sobre o cache."""
        return {
            "periodos_cacheados": list(self._cache.keys()),
            "total_cache_entries": len(self._cache),
            "ultima_atualizacao": max(
                (snapshot.timestamp for snapshot in self._cache.values()), default=None
            ),
        }
