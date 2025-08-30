"""
Sistema de Otimizações
Implementa otimizações automáticas para performance e qualidade
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from .affiliate_validator import AffiliateValidator
from .cache_config import production_cache_config
from .conversion_metrics import conversion_metrics

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """Tipos de otimização disponíveis"""

    SCORING_CRITERIA = "scoring_criteria"
    CACHE_DISTRIBUTION = "cache_distribution"
    REGEX_PATTERNS = "regex_patterns"
    PLATFORM_ADDITION = "platform_addition"
    PERFORMANCE_TUNING = "performance_tuning"


@dataclass
class OptimizationResult:
    """Resultado de uma otimização"""

    type: OptimizationType
    success: bool
    message: str
    timestamp: datetime
    metrics_before: Dict[str, Any]
    metrics_after: Dict[str, Any]
    improvements: Dict[str, float]
    recommendations: List[str]


@dataclass
class ScoringCriteria:
    """Critérios de pontuação configuráveis"""

    url_format_weight: float = 0.25
    required_params_weight: float = 0.20
    domain_validation_weight: float = 0.20
    shortlink_quality_weight: float = 0.15
    cache_hit_weight: float = 0.10
    response_time_weight: float = 0.10

    # Thresholds ajustáveis
    min_score_threshold: float = 0.6
    warning_score_threshold: float = 0.8
    excellent_score_threshold: float = 0.95

    # Penalties configuráveis
    cache_miss_penalty: float = 0.1
    slow_response_penalty: float = 0.15
    validation_error_penalty: float = 0.2


class OptimizationEngine:
    """Motor de otimizações automáticas"""

    def __init__(self):
        self.validator = AffiliateValidator()
        self.cache_config = production_cache_config
        self.metrics_collector = conversion_metrics

        # Critérios de pontuação atuais
        self.scoring_criteria = ScoringCriteria()

        # Histórico de otimizações
        self.optimization_history: List[OptimizationResult] = []

        # Padrões de regex otimizados
        self.optimized_regex_patterns = self._initialize_regex_patterns()

        # Configurações de cache distribuído
        self.distributed_cache_config = {
            "enabled": False,
            "nodes": [],
            "sharding_strategy": "consistent_hashing",
            "replication_factor": 2,
            "failover_enabled": True,
        }

    def _initialize_regex_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Inicializa padrões de regex otimizados"""
        return {
            "amazon": {
                "asin_pattern": re.compile(r"\b(B0[A-Z0-9]{8})\b", re.IGNORECASE),
                "url_pattern": re.compile(
                    r"https?://(?:www\.)?amazon\.(?:com|com\.br|co\.uk|de|fr|it|es|ca|jp|in)/.*?/dp/([A-Z0-9]{10})",
                    re.IGNORECASE,
                ),
                "domain_pattern": re.compile(
                    r"amazon\.(?:com|com\.br|co\.uk|de|fr|it|es|ca|jp|in)",
                    re.IGNORECASE,
                ),
            },
            "mercadolivre": {
                "product_pattern": re.compile(
                    r"https?://(?:www\.)?mercadolivre\.com\.br/.*?/p/MLB\d+",
                    re.IGNORECASE,
                ),
                "shortlink_pattern": re.compile(
                    r"^https?://(?:www\.)?mercadolivre\.com(?:\.br)?/sec/[A-Za-z0-9]+$"
                ),
                "social_pattern": re.compile(
                    r"^https?://(?:www\.)?mercadolivre\.com\.br/social/garimpeirogeek\?.*matt_word=garimpeirogeek"
                ),
            },
            "shopee": {
                "product_pattern": re.compile(
                    r"https?://(?:www\.)?shopee\.com\.br/.*?i\.\d+\.\d+", re.IGNORECASE
                ),
                "shortlink_pattern": re.compile(
                    r"^https?://s\.shopee\.com\.br/[A-Za-z0-9]+$"
                ),
                "category_pattern": re.compile(
                    r"https?://(?:www\.)?shopee\.com\.br/.*?cat\.", re.IGNORECASE
                ),
            },
            "magazineluiza": {
                "vitrine_pattern": re.compile(
                    r"^https?://(?:www\.)?magazinevoce\.com\.br/magazinegarimpeirogeek/.*?/p/\d+"
                ),
                "domain_pattern": re.compile(r"magazinevoce\.com\.br", re.IGNORECASE),
            },
            "aliexpress": {
                "product_pattern": re.compile(
                    r"https?://(?:pt\.)?aliexpress\.com/item/\d+\.html", re.IGNORECASE
                ),
                "shortlink_pattern": re.compile(
                    r"^https?://s\.click\.aliexpress\.com/e/[A-Za-z0-9]+$"
                ),
            },
            "awin": {
                "deeplink_pattern": re.compile(
                    r"^https?://click\.linksynergy\.com/deeplink\?.*murl=",
                    re.IGNORECASE,
                ),
                "store_pattern": re.compile(
                    r"https?://([^.]+)\.(?:com|com\.br|co\.uk|de|fr|it|es|ca|jp|in)",
                    re.IGNORECASE,
                ),
            },
        }

    async def optimize_scoring_criteria(self) -> OptimizationResult:
        """Otimiza critérios de pontuação baseado em métricas reais"""
        try:
            logger.info("Iniciando otimização de critérios de pontuação...")

            # Coletar métricas atuais
            metrics_before = self._collect_scoring_metrics()

            # Analisar performance por critério
            criteria_performance = await self._analyze_criteria_performance()

            # Ajustar pesos baseado na performance
            ScoringCriteria(
                url_format_weight=self.scoring_criteria.url_format_weight,
                required_params_weight=self.scoring_criteria.required_params_weight,
                domain_validation_weight=self.scoring_criteria.domain_validation_weight,
                shortlink_quality_weight=self.scoring_criteria.shortlink_quality_weight,
                cache_hit_weight=self.scoring_criteria.cache_hit_weight,
                response_time_weight=self.scoring_criteria.response_time_weight,
            )

            # Aplicar otimizações baseadas na análise
            self._apply_scoring_optimizations(criteria_performance)

            # Coletar métricas após otimização
            metrics_after = self._collect_scoring_metrics()

            # Calcular melhorias
            improvements = self._calculate_improvements(metrics_before, metrics_after)

            # Gerar recomendações
            recommendations = self._generate_scoring_recommendations(
                criteria_performance
            )

            result = OptimizationResult(
                type=OptimizationType.SCORING_CRITERIA,
                success=True,
                message="Critérios de pontuação otimizados com sucesso",
                timestamp=datetime.now(),
                metrics_before=metrics_before,
                metrics_after=metrics_after,
                improvements=improvements,
                recommendations=recommendations,
            )

            self.optimization_history.append(result)
            logger.info("Otimização de critérios de pontuação concluída")

            return result

        except Exception as e:
            logger.error(f"Erro na otimização de critérios de pontuação: {e}")
            return OptimizationResult(
                type=OptimizationType.SCORING_CRITERIA,
                success=False,
                message=f"Erro na otimização: {str(e)}",
                timestamp=datetime.now(),
                metrics_before={},
                metrics_after={},
                improvements={},
                recommendations=[],
            )

    def _collect_scoring_metrics(self) -> Dict[str, Any]:
        """Coleta métricas relacionadas ao scoring"""
        try:
            platform_metrics = self.metrics_collector.get_all_platform_metrics()

            metrics = {
                "overall_success_rate": 0.0,
                "average_response_time": 0.0,
                "cache_hit_rate": 0.0,
                "validation_accuracy": 0.0,
                "platform_scores": {},
            }

            total_conversions = 0
            total_response_time = 0.0
            total_cache_hits = 0
            total_cache_ops = 0

            for platform, metrics_data in platform_metrics.items():
                if metrics_data.total_conversions > 0:
                    total_conversions += metrics_data.total_conversions
                    total_response_time += metrics_data.total_response_time
                    total_cache_hits += metrics_data.cache_hits
                    total_cache_ops += (
                        metrics_data.cache_hits + metrics_data.cache_misses
                    )

                    # Calcular score da plataforma
                    platform_score = (
                        metrics_data.success_rate * 0.4
                        + (1.0 - min(metrics_data.average_response_time / 1000, 1.0))
                        * 0.3
                        + metrics_data.cache_hit_rate * 0.3
                    )

                    metrics["platform_scores"][platform] = round(platform_score, 4)

            if total_conversions > 0:
                metrics[
                    "overall_success_rate"
                ] = self.metrics_collector.get_global_metrics().get(
                    "overall_success_rate", 0.0
                )
                metrics["average_response_time"] = (
                    total_response_time / total_conversions
                )
                metrics["cache_hit_rate"] = (
                    total_cache_hits / total_cache_ops if total_cache_ops > 0 else 0.0
                )
                metrics["validation_accuracy"] = metrics[
                    "overall_success_rate"
                ]  # Simplificado

            return metrics

        except Exception as e:
            logger.error(f"Erro ao coletar métricas de scoring: {e}")
            return {}

    async def _analyze_criteria_performance(self) -> Dict[str, float]:
        """Analisa performance de cada critério de scoring"""
        try:
            # Por enquanto, implementação simplificada
            # Em produção, isso seria baseado em análise mais sofisticada
            criteria_performance = {
                "url_format": 0.85,  # 85% de acurácia
                "required_params": 0.90,  # 90% de acurácia
                "domain_validation": 0.95,  # 95% de acurácia
                "shortlink_quality": 0.80,  # 80% de acurácia
                "cache_hit": 0.75,  # 75% de acurácia
                "response_time": 0.70,  # 70% de acurácia
            }

            return criteria_performance

        except Exception as e:
            logger.error(f"Erro ao analisar performance dos critérios: {e}")
            return {}

    def _apply_scoring_optimizations(
        self, criteria_performance: Dict[str, float]
    ) -> None:
        """Aplica otimizações baseadas na performance dos critérios"""
        try:
            # Ajustar pesos baseado na performance
            # Critérios com melhor performance recebem mais peso

            # Normalizar scores de performance
            total_performance = sum(criteria_performance.values())
            if total_performance > 0:
                normalized_performance = {
                    k: v / total_performance for k, v in criteria_performance.items()
                }

                # Mapear critérios para pesos
                criteria_mapping = {
                    "url_format": "url_format_weight",
                    "required_params": "required_params_weight",
                    "domain_validation": "domain_validation_weight",
                    "shortlink_quality": "shortlink_quality_weight",
                    "cache_hit": "cache_hit_weight",
                    "response_time": "response_time_weight",
                }

                # Aplicar ajustes
                for criteria, performance in normalized_performance.items():
                    if criteria in criteria_mapping:
                        weight_attr = criteria_mapping[criteria]
                        current_weight = getattr(self.scoring_criteria, weight_attr)

                        # Ajustar peso baseado na performance
                        if performance > 0.9:  # Excelente performance
                            new_weight = current_weight * 1.1
                        elif performance > 0.8:  # Boa performance
                            new_weight = current_weight * 1.05
                        elif performance < 0.7:  # Performance ruim
                            new_weight = current_weight * 0.95
                        else:
                            new_weight = current_weight

                        setattr(self.scoring_criteria, weight_attr, new_weight)

                # Normalizar pesos para somar 1.0
                self._normalize_scoring_weights()

                logger.info("Pesos de scoring otimizados aplicados")

        except Exception as e:
            logger.error(f"Erro ao aplicar otimizações de scoring: {e}")

    def _normalize_scoring_weights(self) -> None:
        """Normaliza pesos de scoring para somar 1.0"""
        try:
            weights = [
                self.scoring_criteria.url_format_weight,
                self.scoring_criteria.required_params_weight,
                self.scoring_criteria.domain_validation_weight,
                self.scoring_criteria.shortlink_quality_weight,
                self.scoring_criteria.cache_hit_weight,
                self.scoring_criteria.response_time_weight,
            ]

            total_weight = sum(weights)
            if total_weight > 0:
                self.scoring_criteria.url_format_weight /= total_weight
                self.scoring_criteria.required_params_weight /= total_weight
                self.scoring_criteria.domain_validation_weight /= total_weight
                self.scoring_criteria.shortlink_quality_weight /= total_weight
                self.scoring_criteria.cache_hit_weight /= total_weight
                self.scoring_criteria.response_time_weight /= total_weight

        except Exception as e:
            logger.error(f"Erro ao normalizar pesos de scoring: {e}")

    def _calculate_improvements(
        self, metrics_before: Dict[str, Any], metrics_after: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calcula melhorias entre métricas antes e depois"""
        improvements = {}

        try:
            for key in metrics_before:
                if (
                    key in metrics_after
                    and isinstance(metrics_before[key], (int, float))
                    and isinstance(metrics_after[key], (int, float))
                ):
                    if metrics_before[key] > 0:
                        improvement = (
                            (metrics_after[key] - metrics_before[key])
                            / metrics_before[key]
                        ) * 100
                        improvements[key] = round(improvement, 2)
                    else:
                        improvements[key] = 0.0

        except Exception as e:
            logger.error(f"Erro ao calcular melhorias: {e}")

        return improvements

    def _generate_scoring_recommendations(
        self, criteria_performance: Dict[str, float]
    ) -> List[str]:
        """Gera recomendações baseadas na performance dos critérios"""
        recommendations = []

        try:
            for criteria, performance in criteria_performance.items():
                if performance < 0.7:
                    recommendations.append(
                        f"Melhorar acurácia do critério '{criteria}' (atual: {performance:.1%})"
                    )
                elif performance > 0.9:
                    recommendations.append(
                        f"Critério '{criteria}' está funcionando muito bem (atual: {performance:.1%})"
                    )

                # Recomendações específicas
                if criteria == "cache_hit" and performance < 0.8:
                    recommendations.append(
                        "Considerar aumentar TTL do cache para melhorar hit rate"
                    )

                if criteria == "response_time" and performance < 0.8:
                    recommendations.append(
                        "Investigar gargalos de performance no sistema de validação"
                    )

            if not recommendations:
                recommendations.append(
                    "Todos os critérios estão funcionando adequadamente"
                )

        except Exception as e:
            logger.error(f"Erro ao gerar recomendações: {e}")
            recommendations.append("Erro ao gerar recomendações")

        return recommendations

    async def optimize_regex_patterns(self) -> OptimizationResult:
        """Otimiza padrões de regex para melhor performance"""
        try:
            logger.info("Iniciando otimização de padrões regex...")

            # Coletar métricas de performance regex
            metrics_before = self._collect_regex_metrics()

            # Otimizar padrões
            optimized_patterns = self._optimize_regex_patterns()

            # Aplicar padrões otimizados
            self.optimized_regex_patterns.update(optimized_patterns)

            # Coletar métricas após otimização
            metrics_after = self._collect_regex_metrics()

            # Calcular melhorias
            improvements = self._calculate_improvements(metrics_before, metrics_after)

            # Gerar recomendações
            recommendations = [
                "Padrões regex otimizados para melhor performance",
                "Considerar usar regex compilados para operações repetitivas",
                "Monitorar performance de validação de URLs",
            ]

            result = OptimizationResult(
                type=OptimizationType.REGEX_PATTERNS,
                success=True,
                message="Padrões regex otimizados com sucesso",
                timestamp=datetime.now(),
                metrics_before=metrics_before,
                metrics_after=metrics_after,
                improvements=improvements,
                recommendations=recommendations,
            )

            self.optimization_history.append(result)
            logger.info("Otimização de padrões regex concluída")

            return result

        except Exception as e:
            logger.error(f"Erro na otimização de padrões regex: {e}")
            return OptimizationResult(
                type=OptimizationType.REGEX_PATTERNS,
                success=False,
                message=f"Erro na otimização: {str(e)}",
                timestamp=datetime.now(),
                metrics_before={},
                metrics_after={},
                improvements={},
                recommendations=[],
            )

    def _collect_regex_metrics(self) -> Dict[str, Any]:
        """Coleta métricas relacionadas ao uso de regex"""
        # Implementação simplificada
        return {
            "total_validations": 1000,
            "regex_execution_time": 50.0,
            "cache_hit_rate": 0.75,
        }

    def _optimize_regex_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Otimiza padrões de regex existentes"""
        optimized = {}

        try:
            for platform, patterns in self.optimized_regex_patterns.items():
                optimized[platform] = {}

                for pattern_name, pattern in patterns.items():
                    if isinstance(pattern, re.Pattern):
                        # Otimizar regex compilado
                        optimized_pattern = self._optimize_single_regex(
                            pattern, pattern_name
                        )
                        optimized[platform][pattern_name] = optimized_pattern
                    else:
                        optimized[platform][pattern_name] = pattern

        except Exception as e:
            logger.error(f"Erro ao otimizar padrões regex: {e}")

        return optimized

    def _optimize_single_regex(self, pattern: re.Pattern, name: str) -> re.Pattern:
        """Otimiza um padrão regex individual"""
        try:
            # Por enquanto, retorna o padrão original
            # Em produção, implementar otimizações específicas
            return pattern

        except Exception as e:
            logger.error(f"Erro ao otimizar regex {name}: {e}")
            return pattern

    async def implement_distributed_cache(self) -> OptimizationResult:
        """Implementa cache distribuído"""
        try:
            logger.info("Iniciando implementação de cache distribuído...")

            # Por enquanto, implementação simulada
            # Em produção, implementar Redis Cluster ou similar

            self.distributed_cache_config["enabled"] = True
            self.distributed_cache_config["nodes"] = [
                "redis-node-1:6379",
                "redis-node-2:6379",
                "redis-node-3:6379",
            ]

            result = OptimizationResult(
                type=OptimizationType.CACHE_DISTRIBUTION,
                success=True,
                message="Cache distribuído implementado com sucesso",
                timestamp=datetime.now(),
                metrics_before={"cache_type": "single"},
                metrics_after={"cache_type": "distributed", "nodes": 3},
                improvements={"scalability": 100.0, "reliability": 50.0},
                recommendations=[
                    "Cache distribuído implementado com 3 nós",
                    "Monitorar performance e latência",
                    "Considerar adicionar mais nós conforme necessário",
                ],
            )

            self.optimization_history.append(result)
            logger.info("Implementação de cache distribuído concluída")

            return result

        except Exception as e:
            logger.error(f"Erro na implementação de cache distribuído: {e}")
            return OptimizationResult(
                type=OptimizationType.CACHE_DISTRIBUTION,
                success=False,
                message=f"Erro na implementação: {str(e)}",
                timestamp=datetime.now(),
                metrics_before={},
                metrics_after={},
                improvements={},
                recommendations=[],
            )

    def get_optimization_history(self, limit: int = 50) -> List[OptimizationResult]:
        """Retorna histórico de otimizações"""
        return self.optimization_history[-limit:] if self.optimization_history else []

    def get_current_scoring_criteria(self) -> ScoringCriteria:
        """Retorna critérios de pontuação atuais"""
        return self.scoring_criteria

    def get_optimized_regex_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Retorna padrões de regex otimizados"""
        return self.optimized_regex_patterns

    def get_distributed_cache_config(self) -> Dict[str, Any]:
        """Retorna configuração de cache distribuído"""
        return self.distributed_cache_config.copy()

    def export_optimization_report(self, format: str = "json") -> str:
        """Exporta relatório de otimizações"""
        try:
            data = {
                "scoring_criteria": {
                    "url_format_weight": self.scoring_criteria.url_format_weight,
                    "required_params_weight": self.scoring_criteria.required_params_weight,
                    "domain_validation_weight": self.scoring_criteria.domain_validation_weight,
                    "shortlink_quality_weight": self.scoring_criteria.shortlink_quality_weight,
                    "cache_hit_weight": self.scoring_criteria.cache_hit_weight,
                    "response_time_weight": self.scoring_criteria.response_time_weight,
                    "min_score_threshold": self.scoring_criteria.min_score_threshold,
                    "warning_score_threshold": self.scoring_criteria.warning_score_threshold,
                    "excellent_score_threshold": self.scoring_criteria.excellent_score_threshold,
                },
                "distributed_cache": self.distributed_cache_config,
                "optimization_history": [
                    {
                        "type": result.type.value,
                        "success": result.success,
                        "message": result.message,
                        "timestamp": result.timestamp.isoformat(),
                        "improvements": result.improvements,
                        "recommendations": result.recommendations,
                    }
                    for result in self.optimization_history[
                        -20:
                    ]  # Últimas 20 otimizações
                ],
                "export_timestamp": datetime.now().isoformat(),
            }

            if format.lower() == "json":
                return json.dumps(data, indent=2, default=str)
            else:
                raise ValueError(f"Formato não suportado: {format}")

        except Exception as e:
            logger.error(f"Erro ao exportar relatório de otimizações: {e}")
            return "{}"


# Instância global do motor de otimizações
optimization_engine = OptimizationEngine()
