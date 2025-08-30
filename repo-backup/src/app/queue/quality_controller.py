#!/usr/bin/env python3
"""
Controlador de Qualidade do Garimpeiro Geek
Avalia e pontua ofertas automaticamente baseado em critérios de qualidade
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List

from src.core.models import Offer

from .offer_queue import QueuePriority


class QualityScore(Enum):
    """Níveis de score de qualidade"""

    EXCELLENT = "excellent"  # 0.9 - 1.0
    VERY_GOOD = "very_good"  # 0.8 - 0.89
    GOOD = "good"  # 0.7 - 0.79
    AVERAGE = "average"  # 0.6 - 0.69
    BELOW_AVERAGE = "below_average"  # 0.5 - 0.59
    POOR = "poor"  # 0.4 - 0.49
    VERY_POOR = "very_poor"  # 0.0 - 0.39


@dataclass
class QualityMetrics:
    """Métricas de qualidade de uma oferta"""

    overall_score: float = 0.0
    price_score: float = 0.0
    discount_score: float = 0.0
    title_score: float = 0.0
    store_score: float = 0.0
    url_score: float = 0.0
    image_score: float = 0.0
    category_score: float = 0.0
    coupon_score: float = 0.0
    stock_score: float = 0.0

    # Detalhes das avaliações
    price_analysis: Dict[str, Any] = field(default_factory=dict)
    discount_analysis: Dict[str, Any] = field(default_factory=dict)
    title_analysis: Dict[str, Any] = field(default_factory=dict)
    store_analysis: Dict[str, Any] = field(default_factory=dict)
    url_analysis: Dict[str, Any] = field(default_factory=dict)
    image_analysis: Dict[str, Any] = field(default_factory=dict)
    category_analysis: Dict[str, Any] = field(default_factory=dict)
    coupon_analysis: Dict[str, Any] = field(default_factory=dict)
    stock_analysis: Dict[str, Any] = field(default_factory=dict)

    # Flags e alertas
    flags: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def get_quality_level(self) -> QualityScore:
        """Retorna o nível de qualidade baseado no score geral"""
        if self.overall_score >= 0.9:
            return QualityScore.EXCELLENT
        elif self.overall_score >= 0.8:
            return QualityScore.VERY_GOOD
        elif self.overall_score >= 0.7:
            return QualityScore.GOOD
        elif self.overall_score >= 0.6:
            return QualityScore.AVERAGE
        elif self.overall_score >= 0.5:
            return QualityScore.BELOW_AVERAGE
        elif self.overall_score >= 0.4:
            return QualityScore.POOR
        else:
            return QualityScore.VERY_POOR


class QualityController:
    """
    Controlador de qualidade que avalia e pontua ofertas automaticamente
    """

    def __init__(self):
        self.logger = logging.getLogger("queue.quality_controller")

        # Configurações de pontuação
        self.score_weights = {
            "price": 0.25,  # 25% do score total
            "discount": 0.20,  # 20% do score total
            "title": 0.15,  # 15% do score total
            "store": 0.15,  # 15% do score total
            "url": 0.10,  # 10% do score total
            "image": 0.05,  # 5% do score total
            "category": 0.05,  # 5% do score total
            "coupon": 0.03,  # 3% do score total
            "stock": 0.02,  # 2% do score total
        }

        # Critérios de avaliação
        self.quality_criteria = {
            "price": {
                "min_price": 10.0,  # Preço mínimo
                "max_price": 10000.0,  # Preço máximo
                "price_ranges": {
                    (0, 50): 0.8,  # Produtos baratos
                    (50, 200): 1.0,  # Produtos médios
                    (200, 1000): 0.9,  # Produtos caros
                    (1000, 5000): 0.7,  # Produtos muito caros
                    (5000, float("inf")): 0.5,  # Produtos premium
                },
            },
            "discount": {
                "min_discount": 5,  # Desconto mínimo
                "max_discount": 90,  # Desconto máximo
                "discount_ranges": {
                    (0, 10): 0.5,  # Desconto baixo
                    (10, 25): 0.7,  # Desconto médio
                    (25, 50): 0.9,  # Desconto alto
                    (50, 75): 1.0,  # Desconto muito alto
                    (75, 90): 0.8,  # Desconto extremo
                    (90, float("inf")): 0.3,  # Desconto suspeito
                },
            },
            "title": {
                "min_length": 10,  # Comprimento mínimo
                "max_length": 200,  # Comprimento máximo
                "required_words": [
                    "produto",
                    "item",
                    "acessório",
                ],  # Palavras obrigatórias
                "forbidden_words": [
                    "gratis",
                    "100%",
                    "milagroso",
                ],  # Palavras proibidas
                "spam_indicators": ["!!!", "???", "$$$", "###"],  # Indicadores de spam
            },
            "store": {
                "trusted_stores": [
                    "amazon",
                    "mercadolivre",
                    "magazineluiza",
                    "shopee",
                    "aliexpress",
                ],
                "store_scores": {
                    "amazon": 1.0,
                    "mercadolivre": 0.9,
                    "magazineluiza": 0.9,
                    "shopee": 0.8,
                    "aliexpress": 0.7,
                },
            },
            "url": {
                "min_length": 20,
                "max_length": 500,
                "required_protocols": ["https://"],
                "forbidden_domains": ["spam.com", "fake.com"],
            },
            "image": {
                "min_size": 100,  # Tamanho mínimo em KB
                "max_size": 5000,  # Tamanho máximo em KB
                "required_formats": [".jpg", ".jpeg", ".png", ".webp"],
            },
            "category": {
                "tech_categories": [
                    "smartphone",
                    "laptop",
                    "headphones",
                    "gaming",
                    "pc",
                ],
                "category_boost": 0.1,  # Boost para categorias tech
            },
            "coupon": {
                "min_discount": 5,
                "max_discount": 50,
                "validity_boost": 0.05,  # Boost para cupons válidos
            },
            "stock": {"low_stock_threshold": 5, "out_of_stock_penalty": 0.3},
        }

        # Histórico de avaliações
        self.evaluation_history: Dict[str, List[QualityMetrics]] = {}

        self.logger.info("QualityController inicializado")

    async def evaluate_offer(self, offer: Offer) -> QualityMetrics:
        """
        Avalia uma oferta e retorna métricas de qualidade

        Args:
            offer: Oferta a ser avaliada

        Returns:
            Métricas de qualidade da oferta
        """
        self.logger.info(f"Avaliando qualidade da oferta: {offer.title[:50]}...")

        # Criar métricas
        metrics = QualityMetrics()

        try:
            # Avaliar cada aspecto da oferta
            metrics.price_score = await self._evaluate_price(offer)
            metrics.discount_score = await self._evaluate_discount(offer)
            metrics.title_score = await self._evaluate_title(offer)
            metrics.store_score = await self._evaluate_store(offer)
            metrics.url_score = await self._evaluate_url(offer)
            metrics.image_score = await self._evaluate_image(offer)
            metrics.category_score = await self._evaluate_category(offer)
            metrics.coupon_score = await self._evaluate_coupon(offer)
            metrics.stock_score = await self._evaluate_stock(offer)

            # Calcular score geral
            metrics.overall_score = self._calculate_overall_score(metrics)

            # Gerar recomendações
            self._generate_recommendations(metrics)

            # Armazenar no histórico
            self._store_evaluation_history(offer, metrics)

            self.logger.info(
                f"Oferta avaliada com score: {metrics.overall_score:.2f} ({metrics.get_quality_level().value})"
            )

        except Exception as e:
            self.logger.error(f"Erro ao avaliar oferta: {e}")
            metrics.overall_score = 0.0
            metrics.flags.append(f"Erro na avaliação: {str(e)}")

        return metrics

    async def _evaluate_price(self, offer: Offer) -> float:
        """Avalia o preço da oferta"""
        try:
            price = float(offer.price)
            criteria = self.quality_criteria["price"]

            # Verificar limites
            if price < criteria["min_price"]:
                return 0.3  # Preço muito baixo (suspeito)

            if price > criteria["max_price"]:
                return 0.4  # Preço muito alto

            # Aplicar pontuação por faixa de preço
            for (min_price, max_price), score in criteria["price_ranges"].items():
                if min_price <= price < max_price:
                    return score

            return 0.5  # Score padrão

        except (ValueError, TypeError):
            return 0.0

    async def _evaluate_discount(self, offer: Offer) -> float:
        """Avalia o desconto da oferta"""
        try:
            if not offer.original_price or not offer.price:
                return 0.5  # Sem desconto

            original = float(offer.original_price)
            current = float(offer.price)

            if original <= current:
                return 0.3  # Sem desconto ou preço aumentou

            discount_percent = ((original - current) / original) * 100
            criteria = self.quality_criteria["discount"]

            # Verificar limites
            if discount_percent < criteria["min_discount"]:
                return 0.4  # Desconto muito baixo

            if discount_percent > criteria["max_discount"]:
                return 0.2  # Desconto suspeito

            # Aplicar pontuação por faixa de desconto
            for (min_discount, max_discount), score in criteria[
                "discount_ranges"
            ].items():
                if min_discount <= discount_percent < max_discount:
                    return score

            return 0.5  # Score padrão

        except (ValueError, TypeError):
            return 0.5

    async def _evaluate_title(self, offer: Offer) -> float:
        """Avalia o título da oferta"""
        try:
            title = offer.title.lower().strip()
            criteria = self.quality_criteria["title"]

            score = 0.5  # Score base

            # Verificar comprimento
            if len(title) < criteria["min_length"]:
                score -= 0.3
                self._add_analysis_detail(
                    offer, "title_analysis", "length", "Muito curto"
                )
            elif len(title) > criteria["max_length"]:
                score -= 0.2
                self._add_analysis_detail(
                    offer, "title_analysis", "length", "Muito longo"
                )
            else:
                score += 0.1

            # Verificar palavras obrigatórias
            has_required = any(word in title for word in criteria["required_words"])
            if has_required:
                score += 0.1
                self._add_analysis_detail(
                    offer,
                    "title_analysis",
                    "required_words",
                    "Contém palavras obrigatórias",
                )
            else:
                score -= 0.1
                self._add_analysis_detail(
                    offer,
                    "title_analysis",
                    "required_words",
                    "Faltam palavras obrigatórias",
                )

            # Verificar palavras proibidas
            has_forbidden = any(word in title for word in criteria["forbidden_words"])
            if has_forbidden:
                score -= 0.3
                self._add_analysis_detail(
                    offer,
                    "title_analysis",
                    "forbidden_words",
                    "Contém palavras proibidas",
                )

            # Verificar indicadores de spam
            spam_count = sum(
                title.count(indicator) for indicator in criteria["spam_indicators"]
            )
            if spam_count > 0:
                score -= 0.2 * spam_count
                self._add_analysis_detail(
                    offer, "title_analysis", "spam", f"{spam_count} indicadores de spam"
                )

            return max(0.0, min(1.0, score))

        except Exception:
            return 0.5

    async def _evaluate_store(self, offer: Offer) -> float:
        """Avalia a loja da oferta"""
        try:
            store = offer.store.lower().strip()
            criteria = self.quality_criteria["store"]

            # Verificar se é loja confiável
            if store in criteria["trusted_stores"]:
                score = criteria["store_scores"].get(store, 0.8)
                self._add_analysis_detail(
                    offer, "store_analysis", "trusted", "Loja confiável"
                )
                return score

            # Loja não reconhecida
            self._add_analysis_detail(
                offer, "store_analysis", "unknown", "Loja não reconhecida"
            )
            return 0.5

        except Exception:
            return 0.5

    async def _evaluate_url(self, offer: Offer) -> float:
        """Avalia a URL da oferta"""
        try:
            url = offer.url
            criteria = self.quality_criteria["url"]

            score = 0.5  # Score base

            # Verificar comprimento
            if len(url) < criteria["min_length"]:
                score -= 0.2
            elif len(url) > criteria["max_length"]:
                score -= 0.1

            # Verificar protocolo
            if not any(protocol in url for protocol in criteria["required_protocols"]):
                score -= 0.3
                self._add_analysis_detail(
                    offer, "url_analysis", "protocol", "Protocolo não seguro"
                )

            # Verificar domínios proibidos
            if any(domain in url for domain in criteria["forbidden_domains"]):
                score -= 0.5
                self._add_analysis_detail(
                    offer, "url_analysis", "forbidden_domain", "Domínio proibido"
                )

            return max(0.0, min(1.0, score))

        except Exception:
            return 0.5

    async def _evaluate_image(self, offer: Offer) -> float:
        """Avalia a imagem da oferta"""
        try:
            if not offer.image_url:
                return 0.3  # Sem imagem

            image_url = offer.image_url.lower()
            criteria = self.quality_criteria["image"]

            score = 0.5  # Score base

            # Verificar formato
            has_valid_format = any(
                format in image_url for format in criteria["required_formats"]
            )
            if has_valid_format:
                score += 0.3
            else:
                score -= 0.2

            # Verificar se é URL válida
            if image_url.startswith("http"):
                score += 0.2
            else:
                score -= 0.3

            return max(0.0, min(1.0, score))

        except Exception:
            return 0.5

    async def _evaluate_category(self, offer: Offer) -> float:
        """Avalia a categoria da oferta"""
        try:
            if not offer.category:
                return 0.5  # Sem categoria

            category = offer.category.lower()
            criteria = self.quality_criteria["category"]

            score = 0.5  # Score base

            # Verificar se é categoria tech
            if any(tech_cat in category for tech_cat in criteria["tech_categories"]):
                score += criteria["category_boost"]
                self._add_analysis_detail(
                    offer, "category_analysis", "tech", "Categoria tech"
                )

            return max(0.0, min(1.0, score))

        except Exception:
            return 0.5

    async def _evaluate_coupon(self, offer: Offer) -> float:
        """Avalia o cupom da oferta"""
        try:
            if not offer.coupon_code:
                return 0.5  # Sem cupom

            score = 0.5  # Score base
            criteria = self.quality_criteria["coupon"]

            # Verificar desconto do cupom
            if offer.coupon_discount:
                discount = float(offer.coupon_discount)
                if criteria["min_discount"] <= discount <= criteria["max_discount"]:
                    score += criteria["validity_boost"]
                    self._add_analysis_detail(
                        offer,
                        "coupon_analysis",
                        "valid_discount",
                        f"Cupom com {discount}% de desconto",
                    )
                else:
                    score -= 0.2
                    self._add_analysis_detail(
                        offer,
                        "coupon_analysis",
                        "invalid_discount",
                        f"Desconto do cupom fora do padrão: {discount}%",
                    )

            # Verificar validade
            if offer.coupon_valid_until:
                try:
                    valid_until = datetime.fromisoformat(offer.coupon_valid_until)
                    if valid_until > datetime.now():
                        score += 0.1
                        self._add_analysis_detail(
                            offer, "coupon_analysis", "valid_until", "Cupom válido"
                        )
                    else:
                        score -= 0.3
                        self._add_analysis_detail(
                            offer, "coupon_analysis", "expired", "Cupom expirado"
                        )
                except ValueError:
                    score -= 0.1
                    self._add_analysis_detail(
                        offer,
                        "coupon_analysis",
                        "invalid_date",
                        "Data de validade inválida",
                    )

            return max(0.0, min(1.0, score))

        except Exception:
            return 0.5

    async def _evaluate_stock(self, offer: Offer) -> float:
        """Avalia o estoque da oferta"""
        try:
            if not offer.stock_quantity:
                return 0.5  # Sem informação de estoque

            stock = int(offer.stock_quantity)
            criteria = self.quality_criteria["stock"]

            score = 0.5  # Score base

            if stock <= 0:
                score -= criteria["out_of_stock_penalty"]
                self._add_analysis_detail(
                    offer, "stock_analysis", "out_of_stock", "Produto sem estoque"
                )
            elif stock <= criteria["low_stock_threshold"]:
                score -= 0.1
                self._add_analysis_detail(
                    offer,
                    "stock_analysis",
                    "low_stock",
                    f"Estoque baixo: {stock} unidades",
                )
            else:
                score += 0.1
                self._add_analysis_detail(
                    offer,
                    "stock_analysis",
                    "good_stock",
                    f"Estoque adequado: {stock} unidades",
                )

            return max(0.0, min(1.0, score))

        except Exception:
            return 0.5

    def _calculate_overall_score(self, metrics: QualityMetrics) -> float:
        """Calcula o score geral baseado nos pesos"""
        try:
            overall_score = 0.0

            for aspect, weight in self.score_weights.items():
                aspect_score = getattr(metrics, f"{aspect}_score", 0.0)
                overall_score += aspect_score * weight

            return max(0.0, min(1.0, overall_score))

        except Exception:
            return 0.0

    def _generate_recommendations(self, metrics: QualityMetrics) -> None:
        """Gera recomendações baseadas na avaliação"""
        try:
            # Recomendações baseadas no score geral
            if metrics.overall_score >= 0.8:
                metrics.recommendations.append(
                    "Oferta de alta qualidade - aprovação recomendada"
                )
            elif metrics.overall_score >= 0.6:
                metrics.recommendations.append(
                    "Oferta de qualidade média - revisão recomendada"
                )
            else:
                metrics.recommendations.append(
                    "Oferta de baixa qualidade - rejeição recomendada"
                )

            # Recomendações específicas por aspecto
            if metrics.price_score < 0.5:
                metrics.recommendations.append(
                    "Verificar preço - pode estar muito baixo ou alto"
                )

            if metrics.discount_score < 0.5:
                metrics.recommendations.append("Verificar desconto - pode ser suspeito")

            if metrics.title_score < 0.5:
                metrics.recommendations.append(
                    "Título precisa de revisão - pode conter spam"
                )

            if metrics.store_score < 0.5:
                metrics.recommendations.append("Verificar confiabilidade da loja")

            if metrics.url_score < 0.5:
                metrics.recommendations.append("URL precisa de validação")

            if metrics.image_score < 0.5:
                metrics.recommendations.append("Verificar qualidade da imagem")

            if metrics.coupon_score < 0.5:
                metrics.recommendations.append("Verificar validade do cupom")

            if metrics.stock_score < 0.5:
                metrics.recommendations.append("Verificar disponibilidade do estoque")

        except Exception as e:
            self.logger.error(f"Erro ao gerar recomendações: {e}")

    def _add_analysis_detail(
        self, offer: Offer, analysis_key: str, detail_key: str, detail_value: str
    ) -> None:
        """Adiciona detalhe de análise às métricas"""
        try:
            # Esta função seria chamada durante a avaliação para adicionar detalhes
            # Por enquanto, apenas log
            self.logger.debug(f"Análise {analysis_key}: {detail_key} = {detail_value}")
        except Exception:
            pass

    def _store_evaluation_history(self, offer: Offer, metrics: QualityMetrics) -> None:
        """Armazena histórico de avaliações"""
        try:
            # Usar URL como chave única
            offer_key = offer.url

            if offer_key not in self.evaluation_history:
                self.evaluation_history[offer_key] = []

            # Adicionar avaliação ao histórico
            self.evaluation_history[offer_key].append(metrics)

            # Manter apenas as últimas 10 avaliações
            if len(self.evaluation_history[offer_key]) > 10:
                self.evaluation_history[offer_key] = self.evaluation_history[offer_key][
                    -10:
                ]

        except Exception as e:
            self.logger.error(f"Erro ao armazenar histórico: {e}")

    def get_priority_recommendation(self, metrics: QualityMetrics) -> QueuePriority:
        """
        Recomenda prioridade baseada na qualidade

        Args:
            metrics: Métricas de qualidade

        Returns:
            Prioridade recomendada
        """
        try:
            if metrics.overall_score >= 0.8:
                return QueuePriority.HIGH
            elif metrics.overall_score >= 0.6:
                return QueuePriority.NORMAL
            elif metrics.overall_score >= 0.4:
                return QueuePriority.LOW
            else:
                return QueuePriority.LOW

        except Exception:
            return QueuePriority.NORMAL

    def get_quality_summary(self, metrics: QualityMetrics) -> Dict[str, Any]:
        """
        Retorna resumo da qualidade da oferta

        Args:
            metrics: Métricas de qualidade

        Returns:
            Resumo da qualidade
        """
        try:
            return {
                "overall_score": metrics.overall_score,
                "quality_level": metrics.get_quality_level().value,
                "priority_recommendation": self.get_priority_recommendation(
                    metrics
                ).name,
                "flags": metrics.flags,
                "warnings": metrics.warnings,
                "recommendations": metrics.recommendations,
                "aspect_scores": {
                    "price": metrics.price_score,
                    "discount": metrics.discount_score,
                    "title": metrics.title_score,
                    "store": metrics.store_score,
                    "url": metrics.url_score,
                    "image": metrics.image_score,
                    "category": metrics.category_score,
                    "coupon": metrics.coupon_score,
                    "stock": metrics.stock_score,
                },
            }

        except Exception as e:
            self.logger.error(f"Erro ao gerar resumo: {e}")
            return {"error": str(e)}

    def get_evaluation_history(self, offer_url: str) -> List[QualityMetrics]:
        """
        Obtém histórico de avaliações de uma oferta

        Args:
            offer_url: URL da oferta

        Returns:
            Lista de métricas de qualidade
        """
        return self.evaluation_history.get(offer_url, [])

    def clear_evaluation_history(self, max_age_days: int = 30) -> int:
        """
        Limpa histórico de avaliações antigas

        Args:
            max_age_days: Idade máxima em dias

        Returns:
            Número de entradas removidas
        """
        try:
            datetime.now() - timedelta(days=max_age_days)
            removed_count = 0

            # Por enquanto, implementação simples
            # Em uma versão real, armazenaria timestamps das avaliações
            if len(self.evaluation_history) > 1000:  # Limite arbitrário
                # Remover entradas mais antigas
                keys_to_remove = list(self.evaluation_history.keys())[:100]
                for key in keys_to_remove:
                    del self.evaluation_history[key]
                    removed_count += 1

            return removed_count

        except Exception as e:
            self.logger.error(f"Erro ao limpar histórico: {e}")
            return 0
