"""
Modelos de dados para o sistema Garimpeiro Geek
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class Offer:
    """
    Modelo padrão para ofertas retornadas pelos scrapers

    Todos os scrapers devem retornar instâncias desta classe
    """

    # Campos obrigatórios
    title: str
    price: Decimal
    url: str
    store: str

    # Campos opcionais mas recomendados
    original_price: Optional[Decimal] = None
    discount_percentage: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None

    # Metadados
    scraped_at: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None  # Nome do scraper/comunidade
    affiliate_url: Optional[str] = None  # URL convertida para afiliado

    # Dados adicionais específicos da loja
    store_data: Dict[str, Any] = field(default_factory=dict)

    # Campos específicos da Amazon
    asin: Optional[str] = None  # Amazon Standard Identification Number

    # Campos de cupom e promoção
    coupon_code: Optional[str] = None  # Código do cupom
    coupon_discount: Optional[float] = None  # Desconto do cupom em %
    coupon_valid_until: Optional[str] = None  # Data de validade do cupom

    # Campos de estoque
    stock_quantity: Optional[int] = None  # Quantidade em estoque

    # Campos de validação
    is_complete: bool = True  # Se a oferta está completa para publicação
    incomplete_reason: Optional[str] = None  # Motivo da incompletude

    # Validação
    def __post_init__(self):
        """Valida os dados da oferta após inicialização"""
        if not self.title or not self.title.strip():
            raise ValueError("Título é obrigatório")

        if self.price <= 0:
            raise ValueError("Preço deve ser maior que zero")

        if not self.url or not self.url.startswith(("http://", "https://")):
            raise ValueError("URL deve ser válida")

        if not self.store or not self.store.strip():
            raise ValueError("Nome da loja é obrigatório")

        # Calcular desconto se não fornecido
        if self.original_price and not self.discount_percentage:
            if self.original_price > self.price:
                self.discount_percentage = float(
                    ((self.original_price - self.price) / self.original_price) * 100
                )

    @property
    def has_discount(self) -> bool:
        """Verifica se a oferta tem desconto"""
        return self.discount_percentage is not None and self.discount_percentage > 0

    @property
    def price_formatted(self) -> str:
        """Retorna o preço formatado em reais"""
        return f"R$ {self.price:.2f}".replace(".", ",")

    @property
    def original_price_formatted(self) -> str:
        """Retorna o preço original formatado"""
        if self.original_price:
            return f"R$ {self.original_price:.2f}".replace(".", ",")
        return ""

    @property
    def discount_formatted(self) -> str:
        """Retorna o desconto formatado"""
        if self.discount_percentage:
            return f"{self.discount_percentage:.0f}% OFF"
        return ""

    def to_dict(self) -> Dict[str, Any]:
        """Converte a oferta para dicionário"""
        return {
            "title": self.title,
            "price": float(self.price),
            "original_price": (
                float(self.original_price) if self.original_price else None
            ),
            "discount_percentage": self.discount_percentage,
            "url": self.url,
            "affiliate_url": self.affiliate_url,
            "store": self.store,
            "description": self.description,
            "image_url": self.image_url,
            "category": self.category,
            "brand": self.brand,
            "model": self.model,
            "scraped_at": self.scraped_at.isoformat(),
            "source": self.source,
            "store_data": self.store_data,
            "asin": self.asin,
            "is_complete": self.is_complete,
            "incomplete_reason": self.incomplete_reason,
            "has_discount": self.has_discount,
            "price_formatted": self.price_formatted,
            "original_price_formatted": self.original_price_formatted,
            "discount_formatted": self.discount_formatted,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Offer":
        """Cria uma oferta a partir de um dicionário"""
        # Converter preços para Decimal
        if "price" in data and isinstance(data["price"], (int, float)):
            data["price"] = Decimal(str(data["price"]))

        if (
            "original_price" in data
            and data["original_price"]
            and isinstance(data["original_price"], (int, float))
        ):
            data["original_price"] = Decimal(str(data["original_price"]))

        # Converter timestamp para datetime
        if "scraped_at" in data and isinstance(data["scraped_at"], str):
            data["scraped_at"] = datetime.fromisoformat(data["scraped_at"])

        return cls(**data)

    def __str__(self) -> str:
        """Representação string da oferta"""
        discount_str = f" ({self.discount_formatted})" if self.has_discount else ""
        return f"{self.title} - {self.price_formatted}{discount_str} - {self.store}"

    def __repr__(self) -> str:
        """Representação detalhada da oferta"""
        return f"Offer(title='{self.title}', price={self.price}, store='{self.store}')"


@dataclass
class ScrapingResult:
    """Resultado de uma operação de scraping"""

    offers: List[Offer]
    total_found: int
    success: bool = True
    error_message: Optional[str] = None
    execution_time: Optional[float] = None  # em segundos

    def __post_init__(self):
        """Validação pós-inicialização"""
        if self.success and not self.offers:
            self.success = False
            self.error_message = "Nenhuma oferta encontrada"

    @property
    def offers_count(self) -> int:
        """Número de ofertas retornadas"""
        return len(self.offers)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "offers": [offer.to_dict() for offer in self.offers],
            "total_found": self.total_found,
            "success": self.success,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "offers_count": self.offers_count,
        }


@dataclass
class StoreConfig:
    """Configuração de uma loja para scraping"""

    name: str
    enabled: bool = True
    base_url: Optional[str] = None
    search_url: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_attempts: int = 3
    delay_between_requests: float = 1.0

    def __post_init__(self):
        """Validação pós-inicialização"""
        if not self.name or not self.name.strip():
            raise ValueError("Nome da loja é obrigatório")

        if self.timeout <= 0:
            raise ValueError("Timeout deve ser maior que zero")

        if self.retry_attempts < 0:
            raise ValueError("Tentativas de retry não podem ser negativas")

        if self.delay_between_requests < 0:
            raise ValueError("Delay entre requisições não pode ser negativo")

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "base_url": self.base_url,
            "search_url": self.search_url,
            "headers": self.headers,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts,
            "delay_between_requests": self.delay_between_requests,
        }
