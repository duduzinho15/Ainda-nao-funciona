"""
Sistema de deduplicação de ofertas para o Garimpeiro Geek.

Implementa estratégias de deduplicação baseadas em:
- URL canônica do produto
- ASIN (Amazon)
- Título normalizado + preço
- Fingerprint de conteúdo
"""

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional
from urllib.parse import parse_qs, urlparse

from src.core.models import Offer

logger = logging.getLogger(__name__)


@dataclass
class DuplicationResult:
    """Resultado da verificação de duplicação"""

    is_duplicate: bool
    duplicate_key: Optional[str] = None
    original_offer_id: Optional[str] = None
    similarity_score: float = 0.0
    deduplication_strategy: Optional[str] = None
    reason: Optional[str] = None


class OfferDeduplicator:
    """Sistema de deduplicação de ofertas"""

    def __init__(self, ttl_hours: int = 24):
        self.ttl_hours = ttl_hours
        self.seen_offers: Dict[str, Dict] = {}  # Cache em memória
        self.url_cache: Dict[str, str] = {}  # Cache de URLs normalizadas
        self.title_cache: Dict[str, str] = {}  # Cache de títulos normalizados

    def check_duplicate(self, offer: Offer) -> DuplicationResult:
        """
        Verifica se uma oferta é duplicada

        Args:
            offer: Oferta para verificar

        Returns:
            Resultado da verificação de duplicação
        """
        try:
            # Limpar cache expirado
            self._cleanup_expired_cache()

            # Estratégia 1: URL canônica (mais confiável)
            result = self._check_by_canonical_url(offer)
            if result.is_duplicate:
                return result

            # Estratégia 2: ASIN para Amazon
            if offer.asin:
                result = self._check_by_asin(offer)
                if result.is_duplicate:
                    return result

            # Estratégia 3: Título normalizado + preço + loja
            result = self._check_by_title_price_store(offer)
            if result.is_duplicate:
                return result

            # Estratégia 4: Fingerprint de conteúdo
            result = self._check_by_content_fingerprint(offer)
            if result.is_duplicate:
                return result

            # Não é duplicada - registrar no cache
            self._register_offer(offer)

            return DuplicationResult(
                is_duplicate=False, deduplication_strategy="none", reason="Oferta única"
            )

        except Exception as e:
            logger.error(f"Erro ao verificar duplicação: {e}")
            return DuplicationResult(
                is_duplicate=False, reason=f"Erro na verificação: {e}"
            )

    def _check_by_canonical_url(self, offer: Offer) -> DuplicationResult:
        """Verificar duplicação por URL canônica"""
        canonical_url = self._normalize_url(offer.url)
        cache_key = f"url:{canonical_url}"

        if cache_key in self.seen_offers:
            existing = self.seen_offers[cache_key]
            return DuplicationResult(
                is_duplicate=True,
                duplicate_key=cache_key,
                original_offer_id=existing.get("offer_id"),
                similarity_score=1.0,
                deduplication_strategy="canonical_url",
                reason="URL canônica idêntica",
            )

        return DuplicationResult(is_duplicate=False)

    def _check_by_asin(self, offer: Offer) -> DuplicationResult:
        """Verificar duplicação por ASIN (Amazon)"""
        if not offer.asin:
            return DuplicationResult(is_duplicate=False)

        cache_key = f"asin:{offer.asin}"

        if cache_key in self.seen_offers:
            existing = self.seen_offers[cache_key]
            return DuplicationResult(
                is_duplicate=True,
                duplicate_key=cache_key,
                original_offer_id=existing.get("offer_id"),
                similarity_score=1.0,
                deduplication_strategy="asin",
                reason=f"ASIN idêntico: {offer.asin}",
            )

        return DuplicationResult(is_duplicate=False)

    def _check_by_title_price_store(self, offer: Offer) -> DuplicationResult:
        """Verificar duplicação por título + preço + loja"""
        normalized_title = self._normalize_title(offer.title)
        price_range = self._get_price_range(offer.price)
        cache_key = f"title_price:{offer.store}:{normalized_title}:{price_range}"

        if cache_key in self.seen_offers:
            existing = self.seen_offers[cache_key]
            return DuplicationResult(
                is_duplicate=True,
                duplicate_key=cache_key,
                original_offer_id=existing.get("offer_id"),
                similarity_score=0.9,
                deduplication_strategy="title_price_store",
                reason="Título, preço e loja similares",
            )

        return DuplicationResult(is_duplicate=False)

    def _check_by_content_fingerprint(self, offer: Offer) -> DuplicationResult:
        """Verificar duplicação por fingerprint de conteúdo"""
        fingerprint = self._generate_content_fingerprint(offer)
        cache_key = f"fingerprint:{fingerprint}"

        if cache_key in self.seen_offers:
            existing = self.seen_offers[cache_key]
            return DuplicationResult(
                is_duplicate=True,
                duplicate_key=cache_key,
                original_offer_id=existing.get("offer_id"),
                similarity_score=0.85,
                deduplication_strategy="content_fingerprint",
                reason="Conteúdo muito similar",
            )

        return DuplicationResult(is_duplicate=False)

    def _normalize_url(self, url: str) -> str:
        """Normalizar URL para comparação"""
        if url in self.url_cache:
            return self.url_cache[url]

        try:
            parsed = urlparse(url)

            # Remover parâmetros irrelevantes
            irrelevant_params = {
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "utm_term",
                "utm_content",
                "ref",
                "referer",
                "referrer",
                "_ga",
                "gclid",
                "fbclid",
                "source",
                "campaign",
                "medium",
                "term",
                "content",
            }

            if parsed.query:
                query_params = parse_qs(parsed.query)
                filtered_params = {
                    k: v for k, v in query_params.items() if k not in irrelevant_params
                }

                # Para Amazon, manter apenas ASIN e tag
                if "amazon.com" in parsed.netloc:
                    important_params = {}
                    if "tag" in filtered_params:
                        important_params["tag"] = filtered_params["tag"]
                    filtered_params = important_params

                query_string = "&".join(
                    [f"{k}={v[0]}" for k, v in filtered_params.items()]
                )
            else:
                query_string = ""

            # Normalizar path
            path = parsed.path.rstrip("/")

            # Para Amazon, extrair apenas o ASIN
            if "amazon.com" in parsed.netloc:
                asin_match = re.search(r"/dp/([A-Z0-9]{10})", path)
                if asin_match:
                    path = f"/dp/{asin_match.group(1)}"

            normalized = f"{parsed.netloc}{path}"
            if query_string:
                normalized += f"?{query_string}"

            self.url_cache[url] = normalized
            return normalized

        except Exception as e:
            logger.warning(f"Erro ao normalizar URL {url}: {e}")
            self.url_cache[url] = url
            return url

    def _normalize_title(self, title: str) -> str:
        """Normalizar título para comparação"""
        if title in self.title_cache:
            return self.title_cache[title]

        try:
            # Converter para minúsculas
            normalized = title.lower()

            # Remover acentos e caracteres especiais
            import unicodedata

            normalized = unicodedata.normalize("NFD", normalized)
            normalized = "".join(
                c for c in normalized if unicodedata.category(c) != "Mn"
            )

            # Remover caracteres especiais e espaços extras
            normalized = re.sub(r"[^\w\s]", " ", normalized)
            normalized = re.sub(r"\s+", " ", normalized)
            normalized = normalized.strip()

            # Remover palavras comuns que não ajudam na identificação
            stop_words = {
                "oferta",
                "promocao",
                "desconto",
                "barato",
                "melhor",
                "preco",
                "produto",
                "item",
                "novo",
                "original",
                "oficial",
                "gratis",
                "frete",
                "entrega",
                "rapida",
                "amazon",
                "shopee",
                "mercadolivre",
                "com",
                "para",
                "de",
                "da",
                "do",
                "na",
                "no",
                "em",
                "por",
                "a",
                "o",
            }

            words = normalized.split()
            words = [w for w in words if w not in stop_words and len(w) > 2]

            normalized = " ".join(sorted(words))  # Ordenar para consistência

            self.title_cache[title] = normalized
            return normalized

        except Exception as e:
            logger.warning(f"Erro ao normalizar título {title}: {e}")
            self.title_cache[title] = title.lower()
            return title.lower()

    def _get_price_range(self, price: Decimal) -> str:
        """Obter faixa de preço para agrupamento"""
        try:
            price_float = float(price)

            if price_float < 50:
                return "0-50"
            elif price_float < 100:
                return "50-100"
            elif price_float < 250:
                return "100-250"
            elif price_float < 500:
                return "250-500"
            elif price_float < 1000:
                return "500-1000"
            elif price_float < 2500:
                return "1000-2500"
            else:
                return "2500+"

        except Exception:
            return "unknown"

    def _generate_content_fingerprint(self, offer: Offer) -> str:
        """Gerar fingerprint único do conteúdo da oferta"""
        try:
            # Combinar elementos-chave da oferta
            content_parts = [
                self._normalize_title(offer.title),
                offer.store.lower(),
                str(offer.price),
                offer.category.lower() if offer.category else "",
                offer.brand.lower() if offer.brand else "",
                offer.model.lower() if offer.model else "",
            ]

            content = "|".join(filter(None, content_parts))

            # Gerar hash MD5
            return hashlib.md5(content.encode("utf-8")).hexdigest()[:16]

        except Exception as e:
            logger.warning(f"Erro ao gerar fingerprint: {e}")
            return hashlib.md5(offer.title.encode("utf-8")).hexdigest()[:16]

    def _register_offer(self, offer: Offer):
        """Registrar oferta no cache de deduplicação"""
        try:
            timestamp = datetime.now()
            offer_data = {
                "offer_id": getattr(offer, "id", None) or str(hash(offer.url)),
                "title": offer.title,
                "price": str(offer.price),
                "store": offer.store,
                "timestamp": timestamp,
                "url": offer.url,
            }

            # Registrar por diferentes chaves
            canonical_url = self._normalize_url(offer.url)
            self.seen_offers[f"url:{canonical_url}"] = offer_data

            if offer.asin:
                self.seen_offers[f"asin:{offer.asin}"] = offer_data

            normalized_title = self._normalize_title(offer.title)
            price_range = self._get_price_range(offer.price)
            title_key = f"title_price:{offer.store}:{normalized_title}:{price_range}"
            self.seen_offers[title_key] = offer_data

            fingerprint = self._generate_content_fingerprint(offer)
            self.seen_offers[f"fingerprint:{fingerprint}"] = offer_data

            logger.debug(f"Oferta registrada no cache de deduplicação: {offer.title}")

        except Exception as e:
            logger.error(f"Erro ao registrar oferta no cache: {e}")

    def _cleanup_expired_cache(self):
        """Limpar cache expirado"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.ttl_hours)

            expired_keys = []
            for key, data in self.seen_offers.items():
                if data.get("timestamp", datetime.now()) < cutoff_time:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.seen_offers[key]

            if expired_keys:
                logger.debug(
                    f"Cache de deduplicação limpo: {len(expired_keys)} entradas removidas"
                )

        except Exception as e:
            logger.error(f"Erro ao limpar cache de deduplicação: {e}")

    def get_cache_stats(self) -> Dict[str, int]:
        """Obter estatísticas do cache"""
        return {
            "total_entries": len(self.seen_offers),
            "url_cache_size": len(self.url_cache),
            "title_cache_size": len(self.title_cache),
            "ttl_hours": self.ttl_hours,
        }

    def clear_cache(self):
        """Limpar todo o cache"""
        self.seen_offers.clear()
        self.url_cache.clear()
        self.title_cache.clear()
        logger.info("Cache de deduplicação limpo completamente")


# Instância global do deduplicador
offer_deduplicator = OfferDeduplicator()
