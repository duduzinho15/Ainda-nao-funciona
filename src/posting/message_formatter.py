"""
Message Formatter para o sistema Garimpeiro Geek.
Formata ofertas para postagem no Telegram com templates profissionais.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import re
from dataclasses import dataclass

from src.core.models import Offer


@dataclass
class MessageTemplate:
    """Template de mensagem para uma plataforma."""
    platform: str
    emoji: str
    format_string: str
    required_fields: List[str]
    optional_fields: List[str]


class MessageFormatter:
    """Formata ofertas para postagem no Telegram."""
    
    def __init__(self):
        """Inicializa o formatter com templates padrão."""
        self.templates = self._create_default_templates()
        self.emojis = self._create_emoji_mapping()
        self.quality_badges = self._create_quality_badges()
    
    def _create_default_templates(self) -> Dict[str, MessageTemplate]:
        """Cria templates padrão para cada plataforma."""
        return {
            "amazon": MessageTemplate(
                platform="Amazon",
                emoji="📦",
                format_string=(
                    "{emoji} **{title}**\n\n"
                    "💰 **Preço Atual**: R$ {price}\n"
                    "💸 **Preço Original**: R$ {original_price}\n"
                    "🎯 **Desconto**: {discount_percentage}%\n"
                    "{coupon_info}"
                    "{price_history_badge}\n"
                    "🏪 **Loja**: {store}\n"
                    "📂 **Categoria**: {category}\n"
                    "🔗 **Link**: {affiliate_url}\n"
                    "{urgency_badge}"
                ),
                required_fields=["title", "price", "affiliate_url"],
                optional_fields=["original_price", "discount_percentage", "store", "category", "coupon_code", "stock_quantity"]
            ),
            "mercadolivre": MessageTemplate(
                platform="Mercado Livre",
                emoji="🛒",
                format_string=(
                    "{emoji} **{title}**\n\n"
                    "💰 **Preço Atual**: R$ {price}\n"
                    "💸 **Preço Original**: R$ {original_price}\n"
                    "🎯 **Desconto**: {discount_percentage}%\n"
                    "{coupon_info}"
                    "{price_history_badge}\n"
                    "🏪 **Loja**: {store}\n"
                    "📂 **Categoria**: {category}\n"
                    "🔗 **Link**: {affiliate_url}\n"
                    "{urgency_badge}"
                ),
                required_fields=["title", "price", "affiliate_url"],
                optional_fields=["original_price", "discount_percentage", "store", "category", "coupon_code", "stock_quantity"]
            ),
            "shopee": MessageTemplate(
                platform="Shopee",
                emoji="🛍️",
                format_string=(
                    "{emoji} **{title}**\n\n"
                    "💰 **Preço Atual**: R$ {price}\n"
                    "💸 **Preço Original**: R$ {original_price}\n"
                    "🎯 **Desconto**: {discount_percentage}%\n"
                    "{coupon_info}"
                    "{price_history_badge}\n"
                    "🏪 **Loja**: {store}\n"
                    "📂 **Categoria**: {category}\n"
                    "🔗 **Link**: {affiliate_url}\n"
                    "{urgency_badge}"
                ),
                required_fields=["title", "price", "affiliate_url"],
                optional_fields=["original_price", "discount_percentage", "store", "category", "coupon_code", "stock_quantity"]
            ),
            "magazineluiza": MessageTemplate(
                platform="Magazine Luiza",
                emoji="🏪",
                format_string=(
                    "{emoji} **{title}**\n\n"
                    "💰 **Preço Atual**: R$ {price}\n"
                    "💸 **Preço Original**: R$ {original_price}\n"
                    "🎯 **Desconto**: {discount_percentage}%\n"
                    "{coupon_info}"
                    "{price_history_badge}\n"
                    "🏪 **Loja**: {store}\n"
                    "📂 **Categoria**: {category}\n"
                    "🔗 **Link**: {affiliate_url}\n"
                    "{urgency_badge}"
                ),
                required_fields=["title", "price", "affiliate_url"],
                optional_fields=["original_price", "discount_percentage", "store", "category", "coupon_code", "stock_quantity"]
            ),
            "aliexpress": MessageTemplate(
                platform="AliExpress",
                emoji="🌏",
                format_string=(
                    "{emoji} **{title}**\n\n"
                    "💰 **Preço Atual**: R$ {price}\n"
                    "💸 **Preço Original**: R$ {original_price}\n"
                    "🎯 **Desconto**: {discount_percentage}%\n"
                    "{coupon_info}"
                    "{price_history_badge}\n"
                    "🏪 **Loja**: {store}\n"
                    "📂 **Categoria**: {category}\n"
                    "🔗 **Link**: {affiliate_url}\n"
                    "{urgency_badge}"
                ),
                required_fields=["title", "price", "affiliate_url"],
                optional_fields=["original_price", "discount_percentage", "store", "category", "coupon_code", "stock_quantity"]
            ),
            "awin": MessageTemplate(
                platform="Awin",
                emoji="🔗",
                format_string=(
                    "{emoji} **{title}**\n\n"
                    "💰 **Preço Atual**: R$ {price}\n"
                    "💸 **Preço Original**: R$ {original_price}\n"
                    "🎯 **Desconto**: {discount_percentage}%\n"
                    "{coupon_info}"
                    "{price_history_badge}\n"
                    "🏪 **Loja**: {store}\n"
                    "📂 **Categoria**: {category}\n"
                    "🔗 **Link**: {affiliate_url}\n"
                    "{urgency_badge}"
                ),
                required_fields=["title", "price", "affiliate_url"],
                optional_fields=["original_price", "discount_percentage", "store", "category", "coupon_code", "stock_quantity"]
            ),
            "rakuten": MessageTemplate(
                platform="Rakuten",
                emoji="🎯",
                format_string=(
                    "{emoji} **{title}**\n\n"
                    "💰 **Preço Atual**: R$ {price}\n"
                    "💸 **Preço Original**: R$ {original_price}\n"
                    "🎯 **Desconto**: {discount_percentage}%\n"
                    "{coupon_info}"
                    "{price_history_badge}\n"
                    "🏪 **Loja**: {store}\n"
                    "📂 **Categoria**: {category}\n"
                    "🔗 **Link**: {affiliate_url}\n"
                    "{urgency_badge}"
                ),
                required_fields=["title", "price", "affiliate_url"],
                optional_fields=["original_price", "discount_percentage", "store", "category", "coupon_code", "stock_quantity"]
            )
        }
    
    def _create_emoji_mapping(self) -> Dict[str, str]:
        """Cria mapeamento de emojis por categoria."""
        return {
            "price": {
                "high": "👑",
                "medium": "💰",
                "low": "💎"
            },
            "discount": {
                "high": "🔥",
                "medium": "💎",
                "low": "💰"
            },
            "urgency": {
                "high": "⚡",
                "medium": "🎯",
                "low": "📌"
            },
            "quality": {
                "excellent": "🏆",
                "good": "⭐",
                "average": "📊"
            }
        }
    
    def _create_quality_badges(self) -> Dict[str, str]:
        """Cria badges de qualidade."""
        return {
            "menor_preco_90d": "🏆 **MENOR PREÇO DOS ÚLTIMOS 90 DIAS!**",
            "menor_preco_30d": "💎 **BOM PREÇO!**",
            "preco_estavel": "📊 **Preço estável**",
            "preco_em_alta": "📈 **Preço em alta**"
        }
    
    def format_offer(self, offer: Offer, platform: Optional[str] = None) -> str:
        """
        Formata uma oferta para postagem no Telegram.
        
        Args:
            offer: Oferta a ser formatada
            platform: Plataforma específica (opcional)
            
        Returns:
            Mensagem formatada para o Telegram
        """
        if not offer:
            raise ValueError("Oferta não pode ser nula")
        
        # Determinar plataforma
        if not platform:
            platform = "generic"
        
        # Obter template
        template = self.templates.get(platform.lower(), self.templates["amazon"])
        
        # Preparar dados para formatação
        format_data = self._prepare_format_data(offer, template)
        
        # Aplicar template
        message = template.format_string.format(**format_data)
        
        # Validar campos obrigatórios
        self._validate_required_fields(format_data, template.required_fields)
        
        return message
    
    def _prepare_format_data(self, offer: Offer, template: MessageTemplate) -> Dict[str, Any]:
        """Prepara dados para formatação da mensagem."""
        # Emoji da plataforma
        emoji = template.emoji
        
        # Formatação de preços
        current_price = self._format_price(offer.price)
        original_price = self._format_price(offer.original_price) if offer.original_price else None
        
        # Cálculo de desconto
        discount_percentage = self._calculate_discount(offer.price, offer.original_price)
        
        # Informações de cupom
        coupon_info = self._format_coupon_info(offer)
        
        # Badge de histórico de preços
        price_history_badge = self._get_price_history_badge(offer)
        
        # Badge de urgência
        urgency_badge = self._get_urgency_badge(offer)
        
        # Loja e categoria
        store = offer.store or "Loja Oficial"
        category = offer.category or "Geral"
        
        # Link de afiliado
        affiliate_url = offer.affiliate_url or "Link não disponível"
        
        return {
            "emoji": emoji,
            "title": offer.title or "Produto sem título",
            "price": current_price,
            "original_price": original_price or "N/A",
            "discount_percentage": discount_percentage,
            "coupon_info": coupon_info,
            "price_history_badge": price_history_badge,
            "store": store,
            "category": category,
            "affiliate_url": affiliate_url,
            "urgency_badge": urgency_badge
        }
    
    def _format_price(self, price: Optional[Decimal]) -> str:
        """Formata preço para exibição."""
        if not price:
            return "0.00"
        
        return f"{float(price):.2f}".replace(".", ",")
    
    def _calculate_discount(self, price: Optional[Decimal], original_price: Optional[Decimal]) -> str:
        """Calcula percentual de desconto."""
        if not price or not original_price:
            return "0"
        
        if original_price <= price:
            return "0"
        
        discount = ((original_price - price) / original_price) * 100
        return f"{discount:.0f}"
    
    def _format_coupon_info(self, offer: Offer) -> str:
        """Formata informações de cupom."""
        if not offer.coupon_code:
            return ""
        
        coupon_text = f"🎫 **CUPOM**: {offer.coupon_code}"
        
        if offer.coupon_discount:
            coupon_text += f" ({offer.coupon_discount}% OFF)"
        
        if offer.coupon_valid_until:
            coupon_text += f" - Válido até {offer.coupon_valid_until.strftime('%d/%m/%Y')}"
        
        return coupon_text + "\n"
    
    def _get_price_history_badge(self, offer: Offer) -> str:
        """Obtém badge de histórico de preços."""
        # Simulação de análise de preços
        # Em produção, isso viria de um sistema de análise de preços
        
        if hasattr(offer, 'price_history') and offer.price_history:
            # Lógica para determinar se é menor preço
            return self.quality_badges.get("menor_preco_90d", "")
        
        return ""
    
    def _get_urgency_badge(self, offer: Offer) -> str:
        """Obtém badge de urgência."""
        if hasattr(offer, 'stock_quantity') and offer.stock_quantity:
            if offer.stock_quantity <= 5:
                return f"\n⚠️ **ESTOQUE BAIXO**: Apenas {offer.stock_quantity} unidades!"
            elif offer.stock_quantity <= 20:
                return f"\n🎯 **Estoque limitado**: {offer.stock_quantity} unidades"
        
        return ""
    
    def _validate_required_fields(self, format_data: Dict[str, Any], required_fields: List[str]):
        """Valida campos obrigatórios."""
        missing_fields = []
        
        for field in required_fields:
            if not format_data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing_fields)}")
    
    def format_multiple_offers(self, offers: List[Offer], max_per_message: int = 3) -> List[str]:
        """
        Formata múltiplas ofertas em mensagens separadas.
        
        Args:
            offers: Lista de ofertas
            max_per_message: Máximo de ofertas por mensagem
            
        Returns:
            Lista de mensagens formatadas
        """
        if not offers:
            return []
        
        messages = []
        current_message = ""
        current_count = 0
        
        for offer in offers:
            try:
                formatted_offer = self.format_offer(offer)
                
                # Adicionar separador se não for a primeira oferta
                if current_count > 0:
                    current_message += "\n\n" + "─" * 40 + "\n\n"
                
                current_message += formatted_offer
                current_count += 1
                
                # Verificar se atingiu o limite por mensagem
                if current_count >= max_per_message:
                    messages.append(current_message)
                    current_message = ""
                    current_count = 0
                    
            except Exception as e:
                # Log do erro e continuar com a próxima oferta
                print(f"Erro ao formatar oferta: {e}")
                continue
        
        # Adicionar última mensagem se houver conteúdo
        if current_message:
            messages.append(current_message)
        
        return messages
    
    def get_platform_templates(self) -> Dict[str, MessageTemplate]:
        """Retorna todos os templates disponíveis."""
        return self.templates.copy()
    
    def add_custom_template(self, platform: str, template: MessageTemplate):
        """Adiciona template customizado para uma plataforma."""
        self.templates[platform.lower()] = template
    
    def validate_template(self, template: MessageTemplate) -> bool:
        """Valida se um template é válido."""
        try:
            # Testar formatação com dados de exemplo
            test_data = {
                "emoji": "📦",
                "title": "Produto Teste",
                "price": "99.99",
                "original_price": "199.99",
                "discount_percentage": "50",
                "coupon_info": "",
                "price_history_badge": "",
                "store": "Loja Teste",
                "category": "Teste",
                "affiliate_url": "https://exemplo.com",
                "urgency_badge": ""
            }
            
            template.format_string.format(**test_data)
            return True
            
        except Exception:
            return False


# Instância global para uso em todo o sistema
message_formatter = MessageFormatter()

