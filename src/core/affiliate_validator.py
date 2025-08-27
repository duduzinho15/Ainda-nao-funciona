"""
Sistema de Validação Unificado para Conversores de Afiliados
Valida conversões e garante qualidade dos links gerados
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Status da validação"""

    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationResult:
    """Resultado da validação"""

    status: ValidationStatus
    message: str
    details: Dict[str, Any]
    score: float = 0.0


class AffiliateValidator:
    """Validador unificado para conversores de afiliados"""

    def __init__(self):
        self.logger = logging.getLogger("affiliate_validator")

        # Padrões de validação por plataforma
        self.validation_patterns = {
            "amazon": {
                "shortlink": r"^https?://amzn\.to/[A-Za-z0-9]+$",
                "affiliate_url": r"^https?://[^/]+/dp/[A-Z0-9]+.*tag=garimpeirogeek-20",
                "required_params": ["tag"],
                "blocked_domains": ["amazon.com", "amazon.com.br", "amazon.com.mx"],
            },
            "mercadolivre": {
                "shortlink": r"^https?://mercadolivre\.com/sec/[A-Za-z0-9]+$",
                "affiliate_url": r"^https?://mercadolivre\.com\.br/social/garimpeirogeek",
                "required_params": ["matt_word"],
                "blocked_domains": [
                    "mercadolivre.com.br",
                    "produto.mercadolivre.com.br",
                ],
            },
            "shopee": {
                "shortlink": r"^https?://s\.shopee\.com\.br/[A-Za-z0-9]+$",
                "affiliate_url": r"^https?://s\.shopee\.com\.br/[A-Za-z0-9]+$",
                "required_params": [],
                "blocked_domains": ["shopee.com.br"],
            },
            "magazineluiza": {
                "shortlink": r"^https?://magazinevoce\.com\.br/magazinegarimpeirogeek/.*/p/\d+",
                "affiliate_url": r"^https?://magazinevoce\.com\.br/magazinegarimpeirogeek/.*/p/\d+",
                "required_params": [],
                "blocked_domains": ["magazineluiza.com.br"],
            },
            "aliexpress": {
                "shortlink": r"^https?://s\.click\.aliexpress\.com/e/[A-Za-z0-9_-]+$",
                "affiliate_url": r"^https?://s\.click\.aliexpress\.com/e/[A-Za-z0-9_-]+$",
                "required_params": [],
                "blocked_domains": ["aliexpress.com", "pt.aliexpress.com"],
            },
            "awin": {
                "shortlink": r"^https?://tidd\.ly/[A-Za-z0-9]+$",
                "affiliate_url": r"^https?://www\.awin1\.com/cread\.php\?awinmid=\d+&awinaffid=\d+&ued=",
                "required_params": ["awinmid", "awinaffid", "ued"],
                "blocked_domains": [],
            },
        }

        # Critérios de pontuação
        self.scoring_criteria = {
            "url_format": 0.3,
            "required_params": 0.25,
            "domain_validation": 0.2,
            "shortlink_quality": 0.15,
            "cache_hit": 0.1,
        }

    def identify_platform(self, url: str) -> Optional[str]:
        """Identifica a plataforma baseada na URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            if "amazon" in domain:
                return "amazon"
            elif "mercadolivre" in domain:
                return "mercadolivre"
            elif "shopee" in domain:
                return "shopee"
            elif "magazine" in domain:
                return "magazineluiza"
            elif "aliexpress" in domain:
                return "aliexpress"
            elif "awin" in domain or any(
                store in domain
                for store in ["comfy", "trocafy", "lg", "kabum", "ninja", "samsung"]
            ):
                return "awin"

            return None

        except Exception as e:
            self.logger.error(f"Erro ao identificar plataforma: {e}")
            return None

    def validate_conversion(
        self, original_url: str, affiliate_url: str, platform: Optional[str] = None
    ) -> ValidationResult:
        """
        Valida uma conversão de afiliado

        Args:
            original_url: URL original do produto
            affiliate_url: URL convertida para afiliado
            platform: Plataforma específica (opcional)

        Returns:
            ValidationResult com status e detalhes
        """
        if not platform:
            platform = self.identify_platform(original_url)

        if not platform:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message="Plataforma não identificada",
                details={"error": "platform_not_found"},
                score=0.0,
            )

        if platform not in self.validation_patterns:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"Plataforma {platform} não suportada",
                details={"error": "platform_not_supported"},
                score=0.0,
            )

        # Validar formato da URL de afiliado
        url_format_score = self._validate_url_format(affiliate_url, platform)

        # Validar parâmetros obrigatórios
        params_score = self._validate_required_params(affiliate_url, platform)

        # Validar domínio
        domain_score = self._validate_domain(affiliate_url, platform)

        # Validar qualidade do shortlink
        shortlink_score = self._validate_shortlink_quality(affiliate_url, platform)

        # Calcular pontuação total
        total_score = (
            url_format_score * self.scoring_criteria["url_format"]
            + params_score * self.scoring_criteria["required_params"]
            + domain_score * self.scoring_criteria["domain_validation"]
            + shortlink_score * self.scoring_criteria["shortlink_quality"]
        )

        # Determinar status baseado na pontuação
        if total_score >= 0.9:
            status = ValidationStatus.VALID
            message = "Conversão válida"
        elif total_score >= 0.7:
            status = ValidationStatus.WARNING
            message = "Conversão com avisos menores"
        elif total_score >= 0.5:
            status = ValidationStatus.WARNING
            message = "Conversão com problemas significativos"
        else:
            status = ValidationStatus.INVALID
            message = "Conversão inválida"

        return ValidationResult(
            status=status,
            message=message,
            details={
                "platform": platform,
                "url_format_score": url_format_score,
                "params_score": params_score,
                "domain_score": domain_score,
                "shortlink_score": shortlink_score,
                "total_score": total_score,
            },
            score=total_score,
        )

    def _validate_url_format(self, url: str, platform: str) -> float:
        """Valida formato da URL"""
        try:
            patterns = self.validation_patterns[platform]

            # Verificar se é shortlink
            if re.match(patterns["shortlink"], url):
                return 1.0

            # Verificar se é URL de afiliado completa
            if re.match(patterns["affiliate_url"], url):
                return 0.9

            # Verificar se é URL válida
            parsed = urlparse(url)
            if parsed.scheme and parsed.netloc:
                return 0.5

            return 0.0

        except Exception as e:
            self.logger.error(f"Erro na validação de formato: {e}")
            return 0.0

    def _validate_required_params(self, url: str, platform: str) -> float:
        """Valida parâmetros obrigatórios"""
        try:
            patterns = self.validation_patterns[platform]
            required_params = patterns["required_params"]

            if not required_params:
                return 1.0  # Sem parâmetros obrigatórios

            parsed = urlparse(url)
            query_params = parsed.query.split("&")
            param_names = [
                param.split("=")[0] for param in query_params if "=" in param
            ]

            found_params = sum(1 for param in required_params if param in param_names)
            return found_params / len(required_params)

        except Exception as e:
            self.logger.error(f"Erro na validação de parâmetros: {e}")
            return 0.0

    def _validate_domain(self, url: str, platform: str) -> float:
        """Valida domínio da URL"""
        try:
            patterns = self.validation_patterns[platform]
            blocked_domains = patterns["blocked_domains"]

            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Verificar se contém domínios bloqueados
            for blocked in blocked_domains:
                if blocked in domain:
                    return 0.0

            return 1.0

        except Exception as e:
            self.logger.error(f"Erro na validação de domínio: {e}")
            return 0.0

    def _validate_shortlink_quality(self, url: str, platform: str) -> float:
        """Valida qualidade do shortlink"""
        try:
            patterns = self.validation_patterns[platform]

            # Se é shortlink, dar pontuação alta
            if re.match(patterns["shortlink"], url):
                return 1.0

            # Se é URL de afiliado completa, pontuação média
            if re.match(patterns["affiliate_url"], url):
                return 0.7

            # Se é URL longa, pontuação baixa
            if len(url) > 200:
                return 0.3

            return 0.5

        except Exception as e:
            self.logger.error(f"Erro na validação de shortlink: {e}")
            return 0.0

    def validate_batch(
        self, conversions: List[Dict[str, str]]
    ) -> List[ValidationResult]:
        """Valida um lote de conversões"""
        results = []

        for conversion in conversions:
            original_url = conversion.get("original_url", "")
            affiliate_url = conversion.get("affiliate_url", "")

            if original_url and affiliate_url:
                result = self.validate_conversion(original_url, affiliate_url)
                results.append(result)
            else:
                results.append(
                    ValidationResult(
                        status=ValidationStatus.ERROR,
                        message="URLs inválidas",
                        details={"error": "invalid_urls"},
                        score=0.0,
                    )
                )

        return results

    def get_validation_stats(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Retorna estatísticas de validação"""
        if not results:
            return {}

        total = len(results)
        valid_count = sum(1 for r in results if r.status == ValidationStatus.VALID)
        warning_count = sum(1 for r in results if r.status == ValidationStatus.WARNING)
        invalid_count = sum(1 for r in results if r.status == ValidationStatus.INVALID)
        error_count = sum(1 for r in results if r.status == ValidationStatus.ERROR)

        avg_score = sum(r.score for r in results) / total

        return {
            "total_conversions": total,
            "valid_conversions": valid_count,
            "warning_conversions": warning_count,
            "invalid_conversions": invalid_count,
            "error_conversions": error_count,
            "success_rate": valid_count / total,
            "average_score": avg_score,
            "platforms": {},
        }
