"""
Sistema de matching para produtos
Mapeia produtos internos com fontes externas (Zoom/Buscapé)
"""

import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProductMatch:
    """Resultado de um match de produto"""

    external_url: str
    confidence: float  # 0.0 a 1.0
    match_type: str  # 'ean', 'model', 'title', 'fuzzy'
    source: str  # 'zoom' ou 'buscape'
    metadata: Optional[Dict] = None


class ProductMatcher:
    """Sistema de matching de produtos"""

    def __init__(self):
        # Configurações de matching
        self.min_confidence = 0.85
        self.max_title_length_diff = 0.3  # 30% de diferença máxima no título

        # Categorias com matching mais restritivo
        self.restrictive_categories = {
            "cabo",
            "película",
            "case",
            "capa",
            "protetor",
            "suporte",
            "adaptador",
            "carregador",
            "fone",
            "mouse",
            "teclado",
        }

        # Palavras-chave que indicam produto específico
        self.specific_keywords = {
            "iphone",
            "samsung",
            "lg",
            "sony",
            "asus",
            "lenovo",
            "dell",
            "intel",
            "amd",
            "nvidia",
            "corsair",
            "kingston",
            "western digital",
            "rtx",
            "gtx",  # Adicionar RTX/GTX para placas de vídeo
        }

        # Padrões para extração de modelo
        self.model_patterns = [
            r"([A-Z]{2,3}\d{3,4}[A-Z]?)",  # LG34GP63A, ASUS TUF
            r"([A-Z]{2,4}-\d{3,4}[A-Z]?)",  # RTX-3080, GTX-1660
            r"(\d{4}[A-Z]{2,4})",  # 2021MacBook, 2020iPad
            r"([A-Z]{2,4}\d{2,3}[A-Z]?)",  # iPhone14, GalaxyS22
            r"(\d{2,3}[A-Z]{2,4})",  # 14Pro, 22Ultra
            r"(\d{2,3}[A-Z]{2,3}[A-Z]?)",  # 34GP63A, 22Ultra
            r"(\d{2,3}[A-Z]{2,4}[A-Z]?)",  # 34GP63A, 22Ultra
            r"(\d{2,3}[A-Z]{2,3}[A-Z]?)",  # 34GP63A, 22Ultra
        ]

        logger.info("ProductMatcher inicializado")

    def normalize_title(self, title: str) -> str:
        """
        Normaliza título para comparação

        Args:
            title: Título original

        Returns:
            Título normalizado
        """
        if not title:
            return ""

        # Converter para minúsculas
        normalized = title.lower()

        # Remover caracteres especiais (mas manter números)
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        # Remover apenas versões como 2.1, 3.0, mas manter números como 14, 22, 256
        normalized = re.sub(r"\b\d+\.\d+\b", "", normalized)

        # Remover palavras comuns que não ajudam no matching
        stop_words = {
            "com",
            "para",
            "compatível",
            "universal",
            "multiplataforma",
            "original",
            "genuíno",
            "oficial",
            "novo",
            "usado",
            "recondicionado",
        }

        words = normalized.split()
        filtered_words = [
            w
            for w in words
            if w not in stop_words
            and (len(w) > 2 or w.isdigit() or w in ["lg", "hp", "tv"])
        ]

        return " ".join(filtered_words)

    def extract_model(self, title: str) -> Optional[str]:
        """
        Extrai modelo do título

        Args:
            title: Título do produto

        Returns:
            Modelo extraído ou None
        """
        if not title:
            return None

        # Tentar padrões de modelo
        for pattern in self.model_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1).upper()

        # Padrão específico para 34GP63A
        specific_match = re.search(r"(\d{2,3}[A-Z]{2,3}[A-Z]?)", title, re.IGNORECASE)
        if specific_match:
            return specific_match.group(1).upper()

        # Padrão específico para 34GP63A-B
        specific_match2 = re.search(
            r"(\d{2,3}[A-Z]{2,3}[A-Z]?-[A-Z])", title, re.IGNORECASE
        )
        if specific_match2:
            return specific_match2.group(1).upper()

        # Tentar extrair números seguidos de letras (ex: 14 Pro, 22 Ultra)
        model_match = re.search(r"(\d{2,3})\s*([A-Za-z]{3,})", title)
        if model_match:
            return f"{model_match.group(1)}{model_match.group(2).upper()}"

        return None

    def extract_brand(self, title: str) -> Optional[str]:
        """
        Extrai marca do título

        Args:
            title: Título do produto

        Returns:
            Marca extraída ou None
        """
        if not title:
            return None

        # Marcas conhecidas
        known_brands = {
            "apple",
            "samsung",
            "lg",
            "sony",
            "asus",
            "lenovo",
            "dell",
            "hp",
            "acer",
            "msi",
            "gigabyte",
            "intel",
            "amd",
            "nvidia",
            "corsair",
            "kingston",
            "western digital",
            "seagate",
            "crucial",
            "adata",
            "iphone",
            "ipad",
            "macbook",  # Produtos Apple
        }

        title_lower = title.lower()

        # Mapeamento especial para Apple
        apple_products = {"iphone", "ipad", "macbook", "mac", "airpods", "apple watch"}
        if any(product in title_lower for product in apple_products):
            return "Apple"

        # Outras marcas
        for brand in known_brands:
            if brand in title_lower:
                # Capitalização especial para algumas marcas
                if brand.upper() in ["LG", "HP", "TV"]:
                    return brand.upper()
                else:
                    return brand.title()

        return None

    def calculate_similarity(self, title1: str, title2: str) -> float:
        """
        Calcula similaridade entre dois títulos

        Args:
            title1: Primeiro título
            title2: Segundo título

        Returns:
            Similaridade de 0.0 a 1.0
        """
        if not title1 or not title2:
            return 0.0

        # Normalizar títulos
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)

        if not norm1 or not norm2:
            return 0.0

        # Usar SequenceMatcher para similaridade
        similarity = SequenceMatcher(None, norm1, norm2).ratio()

        # Penalizar diferenças grandes de comprimento
        len_diff = abs(len(norm1) - len(norm2)) / max(len(norm1), len(norm2))
        if len_diff > self.max_title_length_diff:
            similarity *= 0.8

        return similarity

    def is_restrictive_category(self, title: str) -> bool:
        """
        Verifica se o produto é de categoria restritiva

        Args:
            title: Título do produto

        Returns:
            True se for categoria restritiva
        """
        title_lower = title.lower()
        return any(cat in title_lower for cat in self.restrictive_categories)

    def has_specific_keywords(self, title: str) -> bool:
        """
        Verifica se o título tem palavras-chave específicas

        Args:
            title: Título do produto

        Returns:
            True se tiver palavras-chave específicas
        """
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in self.specific_keywords)

    def choose_best_match(
        self,
        candidates: List[Dict],
        target_title: str,
        target_sku: Optional[str] = None,
    ) -> Optional[ProductMatch]:
        """
        Escolhe o melhor match entre candidatos

        Args:
            candidates: Lista de candidatos com 'title', 'url', 'source'
            target_title: Título do produto alvo
            target_sku: SKU do produto alvo (opcional)

        Returns:
            Melhor match ou None
        """
        if not candidates or not target_title:
            return None

        best_match = None
        best_score = 0.0

        # Extrair informações do produto alvo
        target_model = self.extract_model(target_title)
        target_brand = self.extract_brand(target_title)

        logger.debug(f"Procurando match para: {target_title}")
        logger.debug(f"Modelo extraído: {target_model}, Marca: {target_brand}")

        for candidate in candidates:
            candidate_title = candidate.get("title", "")
            candidate_url = candidate.get("url", "")
            candidate_source = candidate.get("source", "unknown")

            if not candidate_title or not candidate_url:
                continue

            # Calcular score baseado em diferentes critérios
            score = 0.0
            match_type = "fuzzy"

            # 1. Matching por EAN/SKU (se disponível)
            if target_sku and candidate.get("sku") == target_sku:
                score = 1.0
                match_type = "ean"
                logger.debug(f"Match perfeito por SKU: {target_sku}")

            # 2. Matching por modelo
            elif target_model:
                candidate_model = self.extract_model(candidate_title)
                if candidate_model and candidate_model == target_model:
                    score = 0.95
                    match_type = "model"
                    logger.debug(f"Match por modelo: {target_model}")

                    # Bônus se a marca também bater
                    if target_brand and target_brand.lower() in candidate_title.lower():
                        score += 0.03

            # 3. Matching por similaridade de título
            else:
                similarity = self.calculate_similarity(target_title, candidate_title)
                score = similarity

                # Ajustar score baseado em características do produto
                if self.is_restrictive_category(target_title):
                    # Produtos de categoria restritiva precisam de match mais preciso
                    if similarity < 0.9:
                        score *= 0.7
                        logger.debug(
                            f"Produto restritivo - score reduzido para {score}"
                        )

                elif self.has_specific_keywords(target_title):
                    # Produtos com palavras-chave específicas ganham bônus
                    score += 0.1
                    logger.debug(f"Produto específico - bônus aplicado: {score}")

                match_type = "title"

            # Aplicar threshold mínimo
            if score < self.min_confidence:
                logger.debug(
                    f"Candidato rejeitado - score {score} < {self.min_confidence}"
                )
                continue

            # Atualizar melhor match se necessário
            if score > best_score:
                best_score = score
                best_match = ProductMatch(
                    external_url=candidate_url,
                    confidence=score,
                    match_type=match_type,
                    source=candidate_source,
                    metadata={
                        "candidate_title": candidate_title,
                        "target_title": target_title,
                        "score": score,
                    },
                )

                logger.debug(f"Novo melhor match: {score} ({match_type})")

        if best_match:
            logger.info(
                f"Match encontrado: {best_match.confidence:.2f} ({best_match.match_type})"
            )
        else:
            logger.info("Nenhum match adequado encontrado")

        return best_match

    def batch_match(
        self, products: List[Dict], candidates: List[Dict]
    ) -> List[ProductMatch]:
        """
        Faz matching em lote de produtos

        Args:
            products: Lista de produtos internos
            candidates: Lista de candidatos externos

        Returns:
            Lista de matches encontrados
        """
        matches = []

        logger.info(
            f"Iniciando matching em lote: {len(products)} produtos vs {len(candidates)} candidatos"
        )

        for product in products:
            title = product.get("title", "")
            sku = product.get("sku")

            if not title:
                continue

            match = self.choose_best_match(candidates, title, sku)
            if match:
                matches.append(match)

        logger.info(f"Matching em lote concluído: {len(matches)} matches encontrados")
        return matches

    def validate_match(self, match: ProductMatch, target_title: str) -> bool:
        """
        Valida se um match é válido

        Args:
            match: Match a validar
            target_title: Título do produto alvo

        Returns:
            True se o match for válido
        """
        if not match or match.confidence < self.min_confidence:
            return False

        # Validações específicas por tipo de match
        if match.match_type == "ean":
            return True  # EAN é sempre confiável

        elif match.match_type == "model":
            return match.confidence >= 0.95

        elif match.match_type == "title":
            # Para matching por título, verificar se não é muito genérico
            if self.is_restrictive_category(target_title):
                return match.confidence >= 0.9
            else:
                return match.confidence >= 0.85

        return False


# Instância global para uso em outros módulos
product_matcher = ProductMatcher()


def normalize_title(title: str) -> str:
    """Função de conveniência para normalização de título"""
    return product_matcher.normalize_title(title)


def extract_model(title: str) -> Optional[str]:
    """Função de conveniência para extração de modelo"""
    return product_matcher.extract_model(title)


def calculate_similarity(title1: str, title2: str) -> float:
    """Função de conveniência para cálculo de similaridade"""
    return product_matcher.calculate_similarity(title1, title2)


def choose_best_match(
    candidates: List[Dict], target_title: str, target_sku: Optional[str] = None
) -> Optional[ProductMatch]:
    """Função de conveniência para escolha de melhor match"""
    return product_matcher.choose_best_match(candidates, target_title, target_sku)
