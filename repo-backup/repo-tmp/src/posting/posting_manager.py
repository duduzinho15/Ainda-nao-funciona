"""
Gerenciador de validação e postagem de ofertas.
"""

import logging
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.core.enhanced_metrics import enhanced_metrics
from src.core.metrics import Metrics
from src.core.models import Offer
from src.core.performance_logger import (
    log_affiliate_invalid,
    log_post_blocked,
    log_post_success,
)

logger = logging.getLogger(__name__)


@dataclass
class PostingValidationResult:
    """Resultado da validação de postagem"""

    is_valid: bool
    platform: str
    affiliate_url: str
    validation_errors: List[str]
    blocked_reason: Optional[str] = None


class PostingManager:
    """Gerenciador de postagem com validação de afiliados"""

    def __init__(self):
        self.metrics = Metrics()

        # Regex de validação por plataforma (consolidado conforme especificação)
        self.validation_regex = {
            "awin": r"^https?://(www\.)?awin1\.com/cread\.php\?.*awinmid=.*&.*awinaffid=.*&.*ued=.*$",
            "mercadolivre": (
                r"^https?://(www\.)?mercadolivre\.com(\.br)?/sec/.+|"
                r"^https?://www\.mercadolivre\.com\.br/social/garimpeirogeek.+$"
            ),
            "magalu": r"^https?://(?:www\.)?magazinevoce\.com\.br/magazinegarimpeirogeek/.+$",
            "amazon": r"^https?://(www\.)?amazon\.com\.br/.+tag=garimpeirogee-20.*language=pt_BR",
            "shopee": r"^https?://s\.shopee\.com\.br/.+$",
            "aliexpress": r"^https?://s\.click\.aliexpress\.com/e/[A-Za-z0-9_-]{6,}$",
            "rakuten": r"^https?://click\.linksynergy\.com/deeplink\?(.+)$",
        }

        # Regras específicas por plataforma
        self.platform_rules = {
            "amazon": {
                "require_asin": True,
                "require_tag": "garimpeirogee-20",
                "require_language": "pt_BR",
            },
            "awin": {
                "require_awinmid": True,
                "require_awinaffid": True,
                "require_ued": True,
            },
            "shopee": {"require_shortlink": True, "block_categories": True},
            "mercadolivre": {
                "require_shortlink_or_social": True,
                "block_products": True,
            },
            "magalu": {"require_vitrine": True, "block_magazineluiza": True},
            "aliexpress": {"require_shortlink": True, "block_raw_products": True},
        }

    def validate_affiliate_url(
        self, affiliate_url: str, platform: str
    ) -> PostingValidationResult:
        """
        Valida se o link de afiliado segue o formato correto da plataforma

        Args:
            affiliate_url: URL de afiliado a ser validada
            platform: Nome da plataforma

        Returns:
            Resultado da validação
        """
        start_time = time.time()
        validation_errors = []

        # Normalizar plataforma para lowercase
        platform_normalized = platform.lower() if platform else "unknown"

        # Verificar se a plataforma é suportada
        if platform_normalized not in self.validation_regex:
            validation_errors.append(f"Plataforma '{platform}' não suportada")
            self._log_validation_event(
                "plataforma_nao_suportada", platform_normalized, affiliate_url
            )
            return PostingValidationResult(
                is_valid=False,
                platform=platform,
                affiliate_url=affiliate_url,
                validation_errors=validation_errors,
                blocked_reason="plataforma_nao_suportada",
            )

        # Verificar se o link não está vazio
        if not affiliate_url or not affiliate_url.strip():
            validation_errors.append("Link de afiliado está vazio")
            return PostingValidationResult(
                is_valid=False,
                platform=platform,
                affiliate_url=affiliate_url,
                validation_errors=validation_errors,
                blocked_reason="link_vazio",
            )

        # Verificar se o link não é uma URL bruta da loja
        if self._is_raw_store_url(affiliate_url, platform_normalized):
            validation_errors.append(
                "Link é URL bruta da loja, não deeplink de afiliado"
            )
            # Log do evento para métricas
            log_affiliate_invalid(platform_normalized, affiliate_url, "url_bruta_loja")
            self._log_validation_event(
                "affiliate_format_invalid", platform_normalized, affiliate_url
            )
            return PostingValidationResult(
                is_valid=False,
                platform=platform,
                affiliate_url=affiliate_url,
                validation_errors=validation_errors,
                blocked_reason="url_bruta_loja",
            )

        # Aplicar regras específicas da plataforma
        platform_validation = self._validate_platform_specific_rules(
            affiliate_url, platform_normalized
        )
        if not platform_validation["is_valid"]:
            validation_errors.extend(platform_validation["errors"])
            self._log_validation_event(
                "affiliate_format_invalid", platform_normalized, affiliate_url
            )
            return PostingValidationResult(
                is_valid=False,
                platform=platform,
                affiliate_url=affiliate_url,
                validation_errors=validation_errors,
                blocked_reason=platform_validation["blocked_reason"],
            )

        # Validar formato geral com regex
        if not re.match(self.validation_regex[platform_normalized], affiliate_url):
            validation_errors.append(
                f"Formato de link de afiliado inválido para {platform}"
            )
            self._log_validation_event(
                "affiliate_format_invalid", platform_normalized, affiliate_url
            )
            return PostingValidationResult(
                is_valid=False,
                platform=platform,
                affiliate_url=affiliate_url,
                validation_errors=validation_errors,
                blocked_reason="formato_invalido",
            )

        # Calcular latência de validação
        validation_latency = int((time.time() - start_time) * 1000)
        self._log_validation_event(
            "deeplink_latency_ms", platform_normalized, str(validation_latency)
        )

        # Validação bem-sucedida
        return PostingValidationResult(
            is_valid=True,
            platform=platform,
            affiliate_url=affiliate_url,
            validation_errors=[],
            blocked_reason=None,
        )

    def _validate_platform_specific_rules(
        self, affiliate_url: str, platform: str
    ) -> Dict:
        """
        Valida regras específicas da plataforma conforme especificação
        """
        rules = self.platform_rules.get(platform, {})
        errors = []
        blocked_reason = None

        try:
            if platform == "amazon":
                # Amazon: ASIN obrigatório + tag=garimpeirogee-20 + language=pt_BR
                if rules.get("require_asin"):
                    # Verificar se há ASIN na URL
                    try:
                        from src.utils.affiliate_validator import (
                            validate_amazon_asin_format,
                        )
                        from src.utils.url_utils import extract_asin_from_url

                        asin = extract_asin_from_url(affiliate_url)
                        if not asin:
                            errors.append(
                                "ASIN obrigatório não encontrado na URL Amazon"
                            )
                            blocked_reason = "amazon_sem_asin"
                        elif not validate_amazon_asin_format(asin):
                            errors.append(f"Formato de ASIN inválido: {asin}")
                            blocked_reason = "amazon_asin_invalido"
                    except ImportError:
                        errors.append(
                            "Erro interno: módulo de extração de ASIN não disponível"
                        )
                        blocked_reason = "amazon_erro_interno"

                if (
                    rules.get("require_tag")
                    and "tag=garimpeirogee-20" not in affiliate_url
                ):
                    errors.append("Tag de afiliado 'garimpeirogee-20' é obrigatória")
                    blocked_reason = "amazon_affiliate_invalido"

                if (
                    rules.get("require_language")
                    and "language=pt_BR" not in affiliate_url
                ):
                    errors.append("Parâmetro 'language=pt_BR' é obrigatório")
                    blocked_reason = "amazon_affiliate_invalido"

            elif platform == "awin":
                # Awin: cread.php com awinmid, awinaffid, ued (URL-encoded)
                if rules.get("require_awinmid") and "awinmid=" not in affiliate_url:
                    errors.append("Parâmetro 'awinmid' é obrigatório")
                    blocked_reason = "awin_deeplink_invalido"

                if rules.get("require_awinaffid") and "awinaffid=" not in affiliate_url:
                    errors.append("Parâmetro 'awinaffid' é obrigatório")
                    blocked_reason = "awin_deeplink_invalido"

                if rules.get("require_ued") and "ued=" not in affiliate_url:
                    errors.append("Parâmetro 'ued' é obrigatório")
                    blocked_reason = "awin_deeplink_invalido"

            elif platform == "shopee":
                # Shopee: somente https://s.shopee.com.br/... com formato válido
                if rules.get("require_shortlink"):
                    # Verificar se é shortlink válido com formato correto
                    import re

                    shortlink_pattern = (
                        r"^https?://s\.shopee\.com\.br/[A-Za-z0-9]{4,20}$"
                    )
                    if not re.match(shortlink_pattern, affiliate_url):
                        errors.append(
                            "Shopee requer shortlink válido: s.shopee.com.br/[4-20 caracteres alfanuméricos]"
                        )
                        blocked_reason = "shopee_shortlink_invalido"

            elif platform == "mercadolivre":
                # Mercado Livre: somente /sec/ ou /social/garimpeirogeek
                if rules.get("require_shortlink_or_social"):
                    import re

                    # Verificar shortlinks válidos
                    shortlink_pattern = r"^https?://(?:www\.)?mercadolivre\.com(?:\.br)?/sec/[A-Za-z0-9]+$"
                    # Verificar páginas sociais válidas
                    social_pattern = (
                        r"^https?://(?:www\.)?mercadolivre\.com\.br/social/garimpeirogeek\?.*"
                        r"matt_word=garimpeirogeek"
                    )

                    is_shortlink = re.match(shortlink_pattern, affiliate_url)
                    is_social = re.match(social_pattern, affiliate_url)

                    if not (is_shortlink or is_social):
                        errors.append(
                            "ML requer shortlink /sec/[código] ou página social garimpeirogeek com matt_word"
                        )
                        blocked_reason = "ml_affiliate_invalido"

            elif platform == "magalu":
                # Magalu: somente vitrine magazinegarimpeirogeek (com ou sem www)
                if rules.get("require_vitrine"):
                    import re

                    vitrine_pattern = r"^https?://(?:www\.)?magazinevoce\.com\.br/magazinegarimpeirogeek/"
                    if not re.match(vitrine_pattern, affiliate_url):
                        errors.append(
                            "Magalu requer vitrine magazinevoce.com.br/magazinegarimpeirogeek/..."
                        )
                        blocked_reason = "magalu_vitrine_invalida"

            elif platform == "aliexpress":
                # AliExpress: somente s.click.aliexpress.com/e/...
                if rules.get("require_shortlink") and not affiliate_url.startswith(
                    "https://s.click.aliexpress.com/e/"
                ):
                    errors.append(
                        "AliExpress requer shortlink https://s.click.aliexpress.com/e/..."
                    )
                    blocked_reason = "aliexpress_shortlink_invalido"

        except Exception as e:
            logger.error(
                f"Erro ao validar regras específicas da plataforma {platform}: {e}"
            )
            errors.append(f"Erro interno na validação: {e}")
            blocked_reason = "erro_interno"

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "blocked_reason": blocked_reason,
        }

    def _is_raw_store_url(self, url: str, platform: str) -> bool:
        """
        Verifica se é uma URL bruta da loja (não deeplink de afiliado)
        """
        raw_url_patterns = {
            "amazon": [
                r"^https?://(www\.)?amazon\.com\.br/[^?]*$",  # Sem parâmetros
                r"^https?://(www\.)?amazon\.com\.br/[^?]*\?[^=]*$",  # Sem tag
            ],
            "shopee": [
                r"^https?://(www\.)?shopee\.com\.br/i\.\d+\.\d+",  # Produto bruto
                r"^https?://(www\.)?shopee\.com\.br/cat\.",  # Categoria
            ],
            "mercadolivre": [
                r"^https?://(www\.)?mercadolivre\.com\.br/.*?/p/MLB",  # Produto bruto /p/MLB
                r"^https?://produto\.mercadolivre\.com\.br/MLB-",  # Produto bruto domínio produto.
                r"^https?://(www\.)?mercadolivre\.com\.br/.*?/up/MLB",  # Produto bruto /up/MLB
                r"^https?://(www\.)?mercadolivre\.com\.br/.*?/item/MLB",  # Produto bruto /item/MLB
                r"^https?://(www\.)?mercadolivre\.com\.br/.*?MLB[U]?[0-9]",  # Qualquer produto com MLB/MLBU
                r"^https?://(www\.)?mercadolivre\.com\.br/categoria/",  # Categorias
                r"^https?://(www\.)?mercadolivre\.com\.br/search\?",  # Buscas
            ],
            "magalu": [
                r"^https?://(www\.)?magazineluiza\.com\.br/",  # Domínio bloqueado
            ],
            "aliexpress": [
                r"^https?://pt\.aliexpress\.com/item/\d+\.html",  # Produto bruto pt.aliexpress.com
                r"^https?://(?:www\.)?aliexpress\.com/item/\d+\.html",  # Produto bruto aliexpress.com
                r"^https?://pt\.aliexpress\.com/store/",  # Loja pt.aliexpress.com
                r"^https?://(?:www\.)?aliexpress\.com/store/",  # Loja aliexpress.com
                r"^https?://pt\.aliexpress\.com/category/",  # Categoria pt.aliexpress.com
                r"^https?://(?:www\.)?aliexpress\.com/category/",  # Categoria aliexpress.com
                r"^https?://pt\.aliexpress\.com/wholesale/",  # Busca wholesale
                r"^https?://(?:www\.)?aliexpress\.com/wholesale/",  # Busca wholesale
            ],
        }

        patterns = raw_url_patterns.get(platform, [])
        for pattern in patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return True

        return False

    def _log_validation_event(self, event_type: str, platform: str, details: str):
        """
        Registra eventos de validação padronizados
        """
        try:
            if event_type == "affiliate_format_invalid":
                enhanced_metrics.log_affiliate_validation_failure(
                    platform=platform, url=details, reason="formato_invalido"
                )
                logger.warning(f"Formato de afiliado inválido - {platform}: {details}")

            elif event_type == "deeplink_latency_ms":
                # Registrar latência como métrica de performance
                enhanced_metrics.log_asin_extraction_attempt(
                    url=f"latency_{platform}",
                    strategy="validation",
                    success=True,
                    duration_ms=int(details),
                )

            elif event_type in ["plataforma_nao_suportada", "url_bruta_loja"]:
                enhanced_metrics.log_affiliate_validation_failure(
                    platform=platform, url=details, reason=event_type
                )
                logger.warning(
                    f"Erro de validação - {platform}: {event_type} - {details}"
                )

        except Exception as e:
            logger.error(f"Erro ao registrar evento de validação: {e}")

    def validate_and_post_offer(self, offer: Offer) -> PostingValidationResult:
        """
        Valida e posta uma oferta (método principal)
        """
        try:
            # Validar link de afiliado
            if not offer.affiliate_url:
                return PostingValidationResult(
                    is_valid=False,
                    platform=offer.store or "unknown",
                    affiliate_url="",
                    validation_errors=["Oferta não possui link de afiliado"],
                    blocked_reason="sem_link_afiliado",
                )

            # Usar store como plataforma se não houver platform específica
            platform = getattr(offer, "platform", None) or offer.store or "unknown"

            validation_result = self.validate_affiliate_url(
                offer.affiliate_url, platform
            )

            if not validation_result.is_valid:
                # Log do bloqueio
                log_post_blocked(
                    platform,
                    validation_result.blocked_reason or "validacao_falhou",
                    {"affiliate_url": offer.affiliate_url, "title": offer.title},
                )

                # Registrar métrica de bloqueio
                enhanced_metrics.log_posting_block(
                    platform=platform,
                    url=offer.affiliate_url,
                    block_reason=validation_result.blocked_reason or "validacao_falhou",
                )

                return validation_result

            # Validação bem-sucedida - logar sucesso
            log_post_success(platform, offer.title, "telegram")
            enhanced_metrics.log_posting_block(
                platform=platform,
                url=offer.affiliate_url,
                block_reason="success",  # Usar log_posting_block com sucesso
            )

            return validation_result

        except Exception as e:
            logger.error(f"Erro ao validar e postar oferta: {e}")
            enhanced_metrics.log_posting_block(
                platform=getattr(offer, "platform", offer.store) or "unknown",
                url=offer.affiliate_url or "",
                block_reason="erro_interno",
            )

            return PostingValidationResult(
                is_valid=False,
                platform=getattr(offer, "platform", offer.store) or "unknown",
                affiliate_url=offer.affiliate_url or "",
                validation_errors=[f"Erro interno: {e}"],
                blocked_reason="erro_interno",
            )

    def _log_blocked_posting(
        self, offer: Offer, validation_result: PostingValidationResult
    ):
        """Registra postagem bloqueada nas métricas"""
        try:
            self.metrics.record_event(
                "perf",
                "affiliate_format_invalid",
                {
                    "store": offer.store or "unknown",
                    "platform": validation_result.platform,
                    "blocked_reason": validation_result.blocked_reason,
                    "affiliate_url": validation_result.affiliate_url,
                    "validation_errors": validation_result.validation_errors,
                },
            )
        except Exception as e:
            logger.error(f"Erro ao registrar bloqueio: {e}")

    def _log_successful_posting(
        self, offer: Offer, validation_result: PostingValidationResult
    ):
        """Registra postagem bem-sucedida nas métricas"""
        try:
            self.metrics.record_event(
                "perf",
                "offer_posted_successfully",
                {
                    "store": offer.store or "unknown",
                    "platform": validation_result.platform,
                    "affiliate_url": validation_result.affiliate_url,
                },
            )
        except Exception as e:
            logger.error(f"Erro ao registrar sucesso: {e}")

    def _send_admin_warning(
        self, offer: Offer, validation_result: PostingValidationResult
    ):
        """Envia aviso para o admin sobre postagem bloqueada"""
        try:
            # Aqui seria enviado o aviso real para o admin
            # Por enquanto, apenas log
            warning_msg = (
                f"🚫 POSTAGEM BLOQUEADA\n"
                f"Store: {offer.store}\n"
                f"Motivo: {validation_result.blocked_reason}\n"
                f"URL: {validation_result.affiliate_url}\n"
                f"Erros: {', '.join(validation_result.validation_errors)}"
            )
            logger.warning(warning_msg)

        except Exception as e:
            logger.error(f"Erro ao enviar aviso para admin: {e}")

    def get_validation_stats(self) -> Dict:
        """Retorna estatísticas de validação"""
        try:
            # Buscar estatísticas do banco
            blocked_count = self.metrics.get_event_count(
                "perf", "affiliate_format_invalid"
            )
            success_count = self.metrics.get_event_count(
                "perf", "offer_posted_successfully"
            )

            return {
                "blocked_posts": blocked_count,
                "successful_posts": success_count,
                "total_attempts": blocked_count + success_count,
                "block_rate": (
                    blocked_count / (blocked_count + success_count)
                    if (blocked_count + success_count) > 0
                    else 0
                ),
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}


# Instância global
posting_manager = PostingManager()


def validate_affiliate_url(url: str, platform: str) -> PostingValidationResult:
    """Função de conveniência para validar URL de afiliado"""
    return posting_manager.validate_affiliate_url(url, platform)


def post_offer(offer: Offer, channel_id: str) -> bool:
    """Função de conveniência para postar oferta"""
    # Usar o método validate_and_post_offer que existe
    validation_result = posting_manager.validate_and_post_offer(offer)
    return validation_result.is_valid


__all__ = [
    "PostingManager",
    "PostingValidationResult",
    "posting_manager",
    "validate_affiliate_url",
    "post_offer",
]
