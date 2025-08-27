"""
Pipeline de enriquecimento e normalização de ofertas via APIs
Normaliza dados para models.Offer e faz merge com scrapers existentes
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.core.models import Offer
from src.pipelines.ingest_offers_api import APIOffer
from src.utils.affiliate_validator import validate_affiliate_link

logger = logging.getLogger(__name__)


@dataclass
class EnrichedOffer:
    """Oferta enriquecida e normalizada"""

    id: str
    title: str
    price: float
    original_price: Optional[float]
    discount_percentage: Optional[float]
    image_url: Optional[str]
    product_url: str
    affiliate_url: str
    store: str
    category: Optional[str]
    source: str  # API_* ou SCRAPER
    data_freshness: str  # FRESH, STALE, UNKNOWN
    validation_status: str  # VALID, INVALID, PENDING
    collected_at: datetime
    enriched_at: datetime
    metadata: Dict[str, Any]


class APIOfferEnrichmentPipeline:
    """Pipeline para enriquecimento e normalização de ofertas via API"""

    def __init__(self):
        """Inicializa o pipeline de enriquecimento"""
        self.enrichment_stats = {
            "total_processed": 0,
            "enriched": 0,
            "normalized": 0,
            "validated": 0,
            "errors": 0,
            "last_run": None,
        }

    def normalize_price(self, price: Any) -> float:
        """
        Normaliza preço para float

        Args:
            price: Preço em qualquer formato

        Returns:
            Preço normalizado como float
        """
        try:
            if isinstance(price, str):
                # Remover símbolos de moeda e espaços
                price = (
                    price.replace("R$", "")
                    .replace("$", "")
                    .replace(" ", "")
                    .replace(",", ".")
                )
                return float(price)
            elif isinstance(price, (int, float)):
                return float(price)
            else:
                return 0.0
        except (ValueError, TypeError):
            return 0.0

    def calculate_discount_percentage(
        self, original_price: float, current_price: float
    ) -> Optional[float]:
        """
        Calcula percentual de desconto

        Args:
            original_price: Preço original
            current_price: Preço atual

        Returns:
            Percentual de desconto ou None
        """
        try:
            if (
                original_price > 0
                and current_price > 0
                and original_price > current_price
            ):
                discount = ((original_price - current_price) / original_price) * 100
                return round(discount, 2)
            return None
        except Exception:
            return None

    def assess_data_freshness(self, collected_at: datetime) -> str:
        """
        Avalia frescor dos dados

        Args:
            collected_at: Data de coleta

        Returns:
            Classificação de frescor (FRESH, STALE, UNKNOWN)
        """
        try:
            if not collected_at:
                return "UNKNOWN"

            now = datetime.now()
            age = now - collected_at

            if age <= timedelta(hours=1):
                return "FRESH"
            elif age <= timedelta(hours=24):
                return "STALE"
            else:
                return "STALE"
        except Exception:
            return "UNKNOWN"

    def validate_affiliate_url(self, affiliate_url: str, source: str) -> str:
        """
        Valida URL de afiliado

        Args:
            affiliate_url: URL de afiliado
            source: Fonte da oferta

        Returns:
            Status de validação (VALID, INVALID, PENDING)
        """
        try:
            if not affiliate_url:
                return "INVALID"

            # Validar via validador central
            is_valid = validate_affiliate_link(affiliate_url)

            if is_valid:
                return "VALID"
            else:
                return "INVALID"

        except Exception as e:
            logger.error(f"Erro na validação de URL: {e}")
            return "PENDING"

    def normalize_store_name(self, store: str, source: str) -> str:
        """
        Normaliza nome da loja

        Args:
            store: Nome da loja
            source: Fonte da oferta

        Returns:
            Nome da loja normalizado
        """
        if not store:
            return "Loja não informada"

        # Normalizações específicas por fonte
        store = store.strip()

        if source == "API_ALIEXPRESS":
            if "aliexpress" in store.lower():
                return "AliExpress"
            elif "official" in store.lower():
                return "Loja Oficial AliExpress"

        elif source == "API_SHOPEE":
            if "shopee" in store.lower():
                return "Shopee"
            elif "mall" in store.lower():
                return "Shopee Mall"

        elif source == "API_AWIN":
            # Mapear IDs de anunciantes para nomes conhecidos
            store_mapping = {
                "17729": "KaBuM!",
                "23377": "Comfy",
                "33061": "LG",
                "12345": "Magazine Luiza",
                "67890": "Americanas",
            }

            if store in store_mapping:
                return store_mapping[store]

        return store

    def normalize_category(self, category: str) -> Optional[str]:
        """
        Normaliza categoria do produto

        Args:
            category: Categoria original

        Returns:
            Categoria normalizada
        """
        if not category:
            return None

        # Mapeamento de categorias
        category_mapping = {
            "smartphone": "Smartphones",
            "celular": "Smartphones",
            "mobile": "Smartphones",
            "notebook": "Notebooks",
            "laptop": "Notebooks",
            "computador": "Computadores",
            "pc": "Computadores",
            "headphone": "Fones de Ouvido",
            "fone": "Fones de Ouvido",
            "smartwatch": "Smartwatches",
            "relógio": "Smartwatches",
            "watch": "Smartwatches",
        }

        category_lower = category.lower()

        for key, value in category_mapping.items():
            if key in category_lower:
                return value

        return category

    def enrich_offer(self, api_offer: APIOffer) -> EnrichedOffer:
        """
        Enriquece uma oferta da API

        Args:
            api_offer: Oferta da API

        Returns:
            Oferta enriquecida
        """
        try:
            # Normalizar preços
            price = self.normalize_price(api_offer.price)
            original_price = (
                self.normalize_price(api_offer.original_price)
                if api_offer.original_price
                else None
            )

            # Calcular desconto
            discount_percentage = None
            if original_price and price:
                discount_percentage = self.calculate_discount_percentage(
                    original_price, price
                )

            # Avaliar frescor dos dados
            data_freshness = self.assess_data_freshness(api_offer.collected_at)

            # Validar URL de afiliado
            validation_status = self.validate_affiliate_url(
                api_offer.affiliate_url, api_offer.source
            )

            # Normalizar nome da loja
            store = self.normalize_store_name(api_offer.store, api_offer.source)

            # Normalizar categoria
            category = self.normalize_category(api_offer.category)

            # Criar oferta enriquecida
            enriched_offer = EnrichedOffer(
                id=api_offer.id,
                title=(
                    api_offer.title.strip()
                    if api_offer.title
                    else "Título não disponível"
                ),
                price=price,
                original_price=original_price,
                discount_percentage=discount_percentage,
                image_url=api_offer.image_url,
                product_url=api_offer.product_url,
                affiliate_url=api_offer.affiliate_url or api_offer.product_url,
                store=store,
                category=category,
                source=api_offer.source,
                data_freshness=data_freshness,
                validation_status=validation_status,
                collected_at=api_offer.collected_at,
                enriched_at=datetime.now(),
                metadata=api_offer.metadata.copy(),
            )

            # Adicionar metadados de enriquecimento
            enriched_offer.metadata.update(
                {
                    "enrichment_version": "1.0",
                    "enrichment_timestamp": datetime.now().isoformat(),
                    "original_source": api_offer.source,
                    "price_normalized": price,
                    "discount_calculated": discount_percentage,
                }
            )

            return enriched_offer

        except Exception as e:
            logger.error(f"Erro ao enriquecer oferta {api_offer.id}: {e}")
            raise

    def enrich_offers_batch(self, api_offers: List[APIOffer]) -> List[EnrichedOffer]:
        """
        Enriquece um lote de ofertas

        Args:
            api_offers: Lista de ofertas da API

        Returns:
            Lista de ofertas enriquecidas
        """
        enriched_offers = []
        errors = 0

        logger.info(f"Iniciando enriquecimento de {len(api_offers)} ofertas")

        for api_offer in api_offers:
            try:
                enriched_offer = self.enrich_offer(api_offer)
                enriched_offers.append(enriched_offer)

            except Exception as e:
                logger.error(f"Erro ao enriquecer oferta {api_offer.id}: {e}")
                errors += 1
                continue

        # Atualizar estatísticas
        self.enrichment_stats["total_processed"] += len(api_offers)
        self.enrichment_stats["enriched"] += len(enriched_offers)
        self.enrichment_stats["errors"] += errors

        logger.info(
            f"Enriquecimento concluído: {len(enriched_offers)} sucessos, {errors} erros"
        )

        return enriched_offers

    def convert_to_offer_model(self, enriched_offer: EnrichedOffer) -> Offer:
        """
        Converte oferta enriquecida para model.Offer

        Args:
            enriched_offer: Oferta enriquecida

        Returns:
            Instância de Offer
        """
        try:
            # Criar instância de Offer
            offer = Offer(
                id=enriched_offer.id,
                title=enriched_offer.title,
                price=enriched_offer.price,
                original_price=enriched_offer.original_price,
                discount_percentage=enriched_offer.discount_percentage,
                image_url=enriched_offer.image_url,
                product_url=enriched_offer.product_url,
                affiliate_url=enriched_offer.affiliate_url,
                store=enriched_offer.store,
                category=enriched_offer.category,
                source=enriched_offer.source,
                collected_at=enriched_offer.collected_at,
                metadata=enriched_offer.metadata,
            )

            return offer

        except Exception as e:
            logger.error(f"Erro ao converter para model.Offer: {e}")
            raise

    def merge_with_existing_offers(
        self, new_offers: List[EnrichedOffer], existing_offers: List[Offer]
    ) -> List[Offer]:
        """
        Faz merge de novas ofertas com ofertas existentes

        Args:
            new_offers: Novas ofertas enriquecidas
            existing_offers: Ofertas existentes

        Returns:
            Lista mesclada de ofertas
        """
        merged_offers = existing_offers.copy()

        logger.info(
            f"Fazendo merge de {len(new_offers)} novas ofertas com {len(existing_offers)} existentes"
        )

        for new_offer in new_offers:
            # Verificar se já existe oferta similar
            existing_offer = self._find_similar_offer(new_offer, existing_offers)

            if existing_offer:
                # Atualizar oferta existente se a nova for mais fresca
                if self._should_update_existing_offer(new_offer, existing_offer):
                    self._update_existing_offer(existing_offer, new_offer)
                    logger.debug(f"Oferta {new_offer.id} atualizada")
                else:
                    logger.debug(
                        f"Oferta {new_offer.id} ignorada (dados existentes mais frescos)"
                    )
            else:
                # Adicionar nova oferta
                offer_model = self.convert_to_offer_model(new_offer)
                merged_offers.append(offer_model)
                logger.debug(f"Oferta {new_offer.id} adicionada")

        logger.info(f"Merge concluído: {len(merged_offers)} ofertas no total")
        return merged_offers

    def _find_similar_offer(
        self, new_offer: EnrichedOffer, existing_offers: List[Offer]
    ) -> Optional[Offer]:
        """
        Encontra oferta similar entre as existentes

        Args:
            new_offer: Nova oferta
            existing_offers: Ofertas existentes

        Returns:
            Oferta similar ou None
        """
        for existing_offer in existing_offers:
            # Verificar por ID
            if existing_offer.id == new_offer.id:
                return existing_offer

            # Verificar por URL do produto
            if existing_offer.product_url == new_offer.product_url:
                return existing_offer

            # Verificar por título similar (fuzzy match simples)
            if self._titles_are_similar(existing_offer.title, new_offer.title):
                return existing_offer

        return None

    def _titles_are_similar(
        self, title1: str, title2: str, threshold: float = 0.8
    ) -> bool:
        """
        Verifica se títulos são similares

        Args:
            title1: Primeiro título
            title2: Segundo título
            threshold: Limite de similaridade

        Returns:
            True se títulos são similares
        """
        try:
            if not title1 or not title2:
                return False

            # Normalizar títulos
            title1_norm = title1.lower().strip()
            title2_norm = title2.lower().strip()

            # Verificar se um título está contido no outro
            if title1_norm in title2_norm or title2_norm in title1_norm:
                return True

            # Verificar palavras-chave comuns
            words1 = set(title1_norm.split())
            words2 = set(title2_norm.split())

            if len(words1) > 0 and len(words2) > 0:
                common_words = words1.intersection(words2)
                similarity = len(common_words) / max(len(words1), len(words2))
                return similarity >= threshold

            return False

        except Exception:
            return False

    def _should_update_existing_offer(
        self, new_offer: EnrichedOffer, existing_offer: Offer
    ) -> bool:
        """
        Verifica se deve atualizar oferta existente

        Args:
            new_offer: Nova oferta
            existing_offer: Oferta existente

        Returns:
            True se deve atualizar
        """
        try:
            # Se a nova oferta é mais fresca, atualizar
            if (
                new_offer.data_freshness == "FRESH"
                and existing_offer.metadata.get("data_freshness") != "FRESH"
            ):
                return True

            # Se preço mudou significativamente, atualizar
            if new_offer.price > 0 and existing_offer.price > 0:
                price_change = (
                    abs(new_offer.price - existing_offer.price) / existing_offer.price
                )
                if price_change > 0.1:  # 10% de mudança
                    return True

            # Se URL de afiliado é mais válida, atualizar
            if (
                new_offer.validation_status == "VALID"
                and existing_offer.metadata.get("validation_status") != "VALID"
            ):
                return True

            return False

        except Exception:
            return False

    def _update_existing_offer(self, existing_offer: Offer, new_offer: EnrichedOffer):
        """
        Atualiza oferta existente com dados da nova

        Args:
            existing_offer: Oferta existente a ser atualizada
            new_offer: Nova oferta com dados atualizados
        """
        try:
            # Atualizar campos básicos
            existing_offer.title = new_offer.title
            existing_offer.price = new_offer.price
            existing_offer.original_price = new_offer.original_price
            existing_offer.discount_percentage = new_offer.discount_percentage
            existing_offer.image_url = new_offer.image_url
            existing_offer.affiliate_url = new_offer.affiliate_url
            existing_offer.store = new_offer.store
            existing_offer.category = new_offer.category
            existing_offer.collected_at = new_offer.collected_at

            # Atualizar metadados
            existing_offer.metadata.update(new_offer.metadata)
            existing_offer.metadata["last_updated"] = datetime.now().isoformat()
            existing_offer.metadata["update_source"] = new_offer.source

        except Exception as e:
            logger.error(f"Erro ao atualizar oferta existente: {e}")

    def get_enrichment_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do enriquecimento"""
        return self.enrichment_stats.copy()

    def reset_stats(self):
        """Reseta estatísticas do pipeline"""
        self.enrichment_stats = {
            "total_processed": 0,
            "enriched": 0,
            "normalized": 0,
            "validated": 0,
            "errors": 0,
            "last_run": None,
        }


# Função de conveniência
def enrich_api_offers(api_offers: List[APIOffer]) -> List[EnrichedOffer]:
    """
    Enriquece ofertas da API de forma simplificada

    Args:
        api_offers: Lista de ofertas da API

    Returns:
        Lista de ofertas enriquecidas
    """
    pipeline = APIOfferEnrichmentPipeline()
    return pipeline.enrich_offers_batch(api_offers)
