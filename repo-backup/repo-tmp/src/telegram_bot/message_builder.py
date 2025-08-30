#!/usr/bin/env python3
"""
Message Builder para o Bot Telegram do Garimpeiro Geek
Sistema de formatação de mensagens com templates por plataforma
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.core.models import Offer
from src.utils.affiliate_validator import detect_platform


class MessageBuilder:
    """
    Construtor de mensagens para o Telegram com templates por plataforma
    """

    def __init__(self):
        self.logger = logging.getLogger("telegram.message_builder")

        # Configurações de formatação
        self.max_title_length = 80
        self.max_description_length = 200

        # Emojis por categoria
        self.emojis = {
            "tech": [
                "💻",
                "🖥️",
                "📱",
                "⌨️",
                "🖱️",
                "🎮",
                "🎧",
                "📺",
                "📷",
                "📹",
                "🔋",
                "⚡",
                "🌐",
                "📡",
                "🛰️",
            ],
            "gaming": [
                "🎮",
                "🕹️",
                "🎯",
                "🏆",
                "⚡",
                "🔥",
                "💎",
                "🌟",
                "🚀",
                "🎪",
                "🎲",
                "🎭",
                "🎨",
                "🎪",
                "🏅",
            ],
            "discount": [
                "💰",
                "💸",
                "🎁",
                "🏷️",
                "💯",
                "🔥",
                "⚡",
                "🎯",
                "💎",
                "🌟",
                "🎊",
                "🎉",
                "🏆",
                "💫",
                "✨",
            ],
            "store": [
                "🏪",
                "🛒",
                "🛍️",
                "📦",
                "🚚",
                "💳",
                "🎫",
                "🏷️",
                "⭐",
                "💫",
                "🛍️",
                "🛒",
                "🏬",
                "🏭",
                "🏢",
            ],
            "general": [
                "📢",
                "🔔",
                "📣",
                "💬",
                "📝",
                "📋",
                "📊",
                "📈",
                "🎯",
                "✅",
                "🔍",
                "📌",
                "📍",
                "🎪",
                "🎭",
            ],
            "quality": [
                "🏆",
                "💎",
                "⭐",
                "🌟",
                "✨",
                "💫",
                "🔥",
                "⚡",
                "🎯",
                "🎪",
                "🏅",
                "🥇",
                "🥈",
                "🥉",
                "🎖️",
            ],
            "urgency": [
                "⏰",
                "🚨",
                "⚡",
                "🔥",
                "💥",
                "🎯",
                "🎪",
                "🏆",
                "💎",
                "🌟",
                "✨",
                "💫",
                "🎊",
                "🎉",
                "🎁",
            ],
            "category": [
                "💻",
                "🎮",
                "📱",
                "⌨️",
                "🖱️",
                "🎧",
                "📺",
                "📷",
                "📹",
                "🔋",
                "⚡",
                "🌐",
                "📡",
                "🎪",
                "🎭",
            ],
            "shipping": [
                "🚚",
                "📦",
                "✈️",
                "🚢",
                "🚛",
                "🛵",
                "🚲",
                "🚁",
                "🚀",
                "⛵",
                "🚂",
                "🚌",
                "🚗",
                "🚕",
                "🚙",
            ],
            "payment": [
                "💳",
                "💰",
                "💸",
                "🏦",
                "💎",
                "💵",
                "💴",
                "💶",
                "💷",
                "🪙",
                "💱",
                "💲",
                "🪙",
                "💳",
                "🏧",
            ],
            "time": [
                "⏰",
                "🕐",
                "🕑",
                "🕒",
                "🕓",
                "🕔",
                "🕕",
                "🕖",
                "🕗",
                "🕘",
                "🕙",
                "🕚",
                "🕛",
                "⏳",
                "⌛",
            ],
            "status": [
                "✅",
                "❌",
                "⚠️",
                "ℹ️",
                "🔴",
                "🟡",
                "🟢",
                "🔵",
                "🟣",
                "⚫",
                "⚪",
                "🟤",
                "🟠",
                "🟡",
                "🟢",
            ],
        }

        # Badges de qualidade
        self.quality_badges = {
            "best_price_90d": "🏆 MENOR PREÇO 90 DIAS",
            "best_price_30d": "💎 MENOR PREÇO 30 DIAS",
            "price_drop": "📉 QUEDA DE PREÇO",
            "flash_sale": "⚡ OFERTA RELÂMPAGO",
            "limited_stock": "📦 ESTOQUE LIMITADO",
            "new_arrival": "🆕 NOVIDADE",
            "trending": "🔥 EM ALTA",
            "exclusive": "💫 EXCLUSIVO",
            "premium": "⭐ PREMIUM",
            "vip": "👑 VIP",
            "free_shipping": "🚚 FRETE GRÁTIS",
            "fast_delivery": "⚡ ENTREGA RÁPIDA",
            "trusted_store": "✅ LOJA CONFIÁVEL",
            "best_seller": "🏆 MAIS VENDIDO",
            "customer_choice": "👥 ESCOLHA DOS CLIENTES",
            "limited_time": "⏰ TEMPO LIMITADO",
            "last_chance": "🚨 ÚLTIMA CHANCE",
            "hot_deal": "🔥 OFERTA QUENTE",
            "clearance": "🧹 LIQUIDAÇÃO",
            "seasonal": "🌺 OFERTA SAZONAL",
        }

        # Emojis específicos por categoria de produto
        self.category_emojis = {
            "smartphone": "📱",
            "laptop": "💻",
            "desktop": "🖥️",
            "gaming": "🎮",
            "audio": "🎧",
            "camera": "📷",
            "tv": "📺",
            "tablet": "📱",
            "keyboard": "⌨️",
            "mouse": "🖱️",
            "monitor": "🖥️",
            "headphones": "🎧",
            "speaker": "🔊",
            "microphone": "🎤",
            "webcam": "📹",
            "router": "📡",
            "storage": "💾",
            "memory": "🧠",
            "processor": "⚡",
            "graphics": "🎨",
            "motherboard": "🔌",
            "power_supply": "🔋",
            "case": "📦",
            "cooling": "❄️",
            "network": "🌐",
            "security": "🔒",
            "software": "💿",
            "accessories": "🔧",
            "gaming_chair": "🪑",
            "gaming_desk": "🪑",
            "gaming_mousepad": "🖱️",
            "gaming_headset": "🎧",
            "gaming_keyboard": "⌨️",
            "gaming_mouse": "🖱️",
            "gaming_controller": "🎮",
            "gaming_console": "🎮",
            "gaming_laptop": "💻",
            "gaming_desktop": "🖥️",
            "gaming_monitor": "🖥️",
            "gaming_speaker": "🔊",
            "gaming_microphone": "🎤",
            "gaming_webcam": "📹",
            "gaming_router": "📡",
            "gaming_storage": "💾",
            "gaming_memory": "🧠",
            "gaming_processor": "⚡",
            "gaming_graphics": "🎨",
            "gaming_motherboard": "🔌",
            "gaming_power_supply": "🔋",
            "gaming_case": "📦",
            "gaming_cooling": "❄️",
            "gaming_network": "🌐",
            "gaming_security": "🔒",
            "gaming_software": "💿",
            "gaming_accessories": "🔧",
        }

        # Emojis de status de entrega
        self.shipping_emojis = {
            "free": "🚚",
            "paid": "💳",
            "fast": "⚡",
            "standard": "📦",
            "express": "✈️",
            "same_day": "🚀",
            "next_day": "⚡",
            "pickup": "🏪",
            "digital": "💻",
            "download": "⬇️",
        }

        # Emojis de método de pagamento
        self.payment_emojis = {
            "credit_card": "💳",
            "debit_card": "💳",
            "pix": "📱",
            "boleto": "📄",
            "paypal": "💳",
            "crypto": "₿",
            "installments": "💳",
            "cash": "💰",
            "transfer": "🏦",
            "wallet": "👛",
        }

        # Configurações de scoring
        self.scoring_weights = {
            "discount_percentage": 0.3,
            "price_drop_90d": 0.25,
            "price_drop_30d": 0.2,
            "stock_availability": 0.15,
            "brand_reputation": 0.1,
        }

        # Templates por plataforma
        self.platform_templates = {
            "awin": self._build_awin_template,
            "amazon": self._build_amazon_template,
            "mercadolivre": self._build_mercadolivre_template,
            "shopee": self._build_shopee_template,
            "magazineluiza": self._build_magazineluiza_template,
            "aliexpress": self._build_aliexpress_template,
            "default": self._build_default_template,
        }

    def build_welcome_message(self) -> str:
        """Constrói mensagem de boas-vindas"""
        return """
🎮 <b>Bem-vindo ao Garimpeiro Geek!</b> 🎮

🚀 <b>Sistema de Ofertas Automático</b>
• 📱 Tecnologia e Gaming
• 🎯 Ofertas selecionadas automaticamente
• 💰 Links de afiliado otimizados
• 📊 Análise de preços em tempo real

🔧 <b>Comandos disponíveis:</b>
/start - Esta mensagem
/help - Ajuda completa
/status - Status do sistema
/ofertas - Buscar ofertas
/config - Configurações
/stats - Estatísticas

⚡ <b>Status:</b> Sistema ativo e monitorando ofertas!
        """.strip()

    def build_help_message(self, commands: Dict[str, str]) -> str:
        """Constrói mensagem de ajuda"""
        help_text = "📚 <b>Comandos do Garimpeiro Geek:</b>\n\n"

        for cmd, description in commands.items():
            help_text += f"<code>/{cmd}</code> - {description}\n"

        help_text += "\n💡 <b>Dicas:</b>\n"
        help_text += "• Envie links de produtos para análise automática\n"
        help_text += "• O sistema converte automaticamente para links de afiliado\n"
        help_text += "• Receba notificações de ofertas em tempo real\n"

        return help_text.strip()

    def build_status_message(self) -> str:
        """Constrói mensagem de status do sistema"""
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        return f"""
📊 <b>Status do Sistema Garimpeiro Geek</b>

🕐 <b>Última atualização:</b> {current_time}
🟢 <b>Status:</b> Sistema ativo
📡 <b>Monitoramento:</b> Em execução
🔗 <b>Afiliados:</b> Todos ativos

📈 <b>Métricas:</b>
• Ofertas processadas: Em desenvolvimento
• Conversões: Em desenvolvimento
• Receita: Em desenvolvimento

⚙️ <b>Componentes:</b>
• Scrapers: Ativos
• Conversores: Ativos
• Validador: Ativo
• Bot: Ativo
        """.strip()

    def build_offers_message(self, offers: List[Offer]) -> str:
        """Constrói mensagem com lista de ofertas"""
        if not offers:
            return "🔍 Nenhuma oferta encontrada no momento."

        message = f"🎯 <b>Ofertas Encontradas ({len(offers)}):</b>\n\n"

        for i, offer in enumerate(offers[:5], 1):  # Máximo 5 ofertas por mensagem
            offer_text = self._format_single_offer(offer, i)
            message += offer_text + "\n\n"

        if len(offers) > 5:
            message += f"📝 <i>... e mais {len(offers) - 5} ofertas</i>"

        return message.strip()

    def build_offers_keyboard(self, offers: List[Offer]) -> List[List[Dict[str, str]]]:
        """Constrói teclado inline para ofertas"""
        keyboard = []

        for i, _offer in enumerate(offers[:6]):  # Máximo 6 botões
            keyboard.append(
                [{"text": f"📋 Oferta {i+1}", "callback_data": f"offer_{i}"}]
            )

        # Botões de ação
        keyboard.append(
            [
                {"text": "🔄 Atualizar", "callback_data": "refresh_offers"},
                {"text": "📊 Todas", "callback_data": "all_offers"},
            ]
        )

        return keyboard

    def build_config_message(self) -> str:
        """Constrói mensagem de configurações"""
        return """
⚙️ <b>Configurações do Sistema</b>

🔧 <b>Controles:</b>
• Ativar/Desativar scrapers
• Configurar intervalos de postagem
• Definir filtros de preço
• Configurar notificações

📊 <b>Status Atual:</b>
• Sistema: Ativo
• Modo: Automático
• Notificações: Ativas
• Rate Limiting: Ativo
        """.strip()

    def build_config_keyboard(self) -> List[List[Dict[str, str]]]:
        """Constrói teclado inline para configurações"""
        return [
            [
                {"text": "🟢 Sistema ON", "callback_data": "config_system_on"},
                {"text": "🔴 Sistema OFF", "callback_data": "config_system_off"},
            ],
            [
                {"text": "📱 Scrapers", "callback_data": "config_scrapers"},
                {"text": "⏰ Agendamento", "callback_data": "config_schedule"},
            ],
            [
                {"text": "🔔 Notificações", "callback_data": "config_notifications"},
                {"text": "📊 Métricas", "callback_data": "config_metrics"},
            ],
        ]

    def build_stats_message(self) -> str:
        """Constrói mensagem de estatísticas"""
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        return f"""
📊 <b>Estatísticas do Sistema</b>

🕐 <b>Período:</b> {current_time}

📈 <b>Performance:</b>
• Ofertas processadas: Em desenvolvimento
• Taxa de conversão: Em desenvolvimento
• Receita total: Em desenvolvimento
• Custo por clique: Em desenvolvimento

🎯 <b>Plataformas:</b>
• Awin: Ativo
• Amazon: Ativo
• Mercado Livre: Ativo
• Shopee: Ativo
• Magazine Luiza: Ativo
• AliExpress: Ativo

📱 <b>Engajamento:</b>
• Mensagens enviadas: Em desenvolvimento
• Cliques recebidos: Em desenvolvimento
• Usuários ativos: Em desenvolvimento
        """.strip()

    def build_offer_message(self, offer: Offer, platform: Optional[str] = None) -> str:
        """
        Constrói mensagem completa de uma oferta específica
        Usa template específico da plataforma se disponível
        """
        if not platform:
            platform = detect_platform(offer.url)

        # Usar template específico da plataforma ou padrão
        if platform and platform in self.platform_templates:
            template_func = self.platform_templates[platform]
        else:
            template_func = self.platform_templates["default"]

        return template_func(offer)

    def _build_awin_template(self, offer: Offer) -> str:
        """Template específico para ofertas Awin"""
        store_name = offer.store_data.get("store_name", offer.store)

        # Análise de preços e scoring
        price_analysis = self._analyze_price_history(offer)
        offer_score = self._calculate_offer_score(offer, price_analysis)
        urgency_emoji = self._get_urgency_emoji(price_analysis["urgency_level"])

        # Cabeçalho com badges de qualidade
        message = f"""
{urgency_emoji} <b>OFERTA ESPECIAL - {store_name.upper()}</b>
"""

        # Adicionar badges de qualidade
        if price_analysis["badges"]:
            badges_text = " | ".join(price_analysis["badges"])
            message += f"\n{self._get_random_emoji('quality')} <b>{badges_text}</b>\n"

        # Score da oferta
        score_percentage = offer_score * 100
        score_emoji = (
            "🏆"
            if offer_score >= 0.8
            else "💎" if offer_score >= 0.6 else "⭐" if offer_score >= 0.4 else "💡"
        )
        message += (
            f"\n{score_emoji} <b>SCORE:</b> {score_percentage:.0f}% "
            f"({self._get_score_description(offer_score)})\n"
        )

        # Informações principais
        message += f"""
{self._get_random_emoji('tech')} <b>{self._truncate_title(offer.title)}</b>

💰 <b>Preço Atual:</b> {offer.price_formatted}
"""

        if offer.has_discount:
            message += f"🏷️ <b>Preço Original:</b> {offer.original_price_formatted}\n"
            message += f"🔥 <b>Desconto:</b> {offer.discount_formatted}\n"

        # Informações adicionais
        if offer.description:
            message += f"\n📝 {self._truncate_description(offer.description)}\n"

        if offer.category:
            message += f"📂 <b>Categoria:</b> {offer.category}\n"

        if offer.brand:
            message += f"🏷️ <b>Marca:</b> {offer.brand}\n"

        # Cupom e comparação de preços
        coupon_info = self._format_coupon_info(offer)
        if coupon_info:
            message += coupon_info

        price_comparison = self._format_price_comparison(offer)
        if price_comparison:
            message += price_comparison

        # Informações de estoque
        stock_info = self._format_stock_info(offer)
        if stock_info:
            message += stock_info

        # Rodapé
        message += f"""

🔗 <b>Link:</b> {offer.affiliate_url or offer.url}

⏰ <b>Válido até:</b> Oferta limitada
🏪 <b>Loja:</b> {store_name}
        """.strip()

        return message

    def _get_score_description(self, score: float) -> str:
        """Retorna descrição textual do score"""
        if score >= 0.9:
            return "EXCELENTE"
        elif score >= 0.8:
            return "MUITO BOM"
        elif score >= 0.7:
            return "BOM"
        elif score >= 0.6:
            return "REGULAR"
        elif score >= 0.4:
            return "BÁSICO"
        else:
            return "LIMITADO"

    def _build_amazon_template(self, offer: Offer) -> str:
        """Template específico para ofertas Amazon"""
        asin_info = f" (ASIN: {offer.asin})" if offer.asin else ""

        # Análise de preços e scoring
        price_analysis = self._analyze_price_history(offer)
        offer_score = self._calculate_offer_score(offer, price_analysis)
        urgency_emoji = self._get_urgency_emoji(price_analysis["urgency_level"])

        # Cabeçalho com badges de qualidade
        message = f"""
{urgency_emoji} <b>OFERTA AMAZON{asin_info}</b>
"""

        # Adicionar badges de qualidade
        if price_analysis["badges"]:
            badges_text = " | ".join(price_analysis["badges"])
            message += f"\n{self._get_random_emoji('quality')} <b>{badges_text}</b>\n"

        # Score da oferta
        score_percentage = offer_score * 100
        score_emoji = (
            "🏆"
            if offer_score >= 0.8
            else "💎" if offer_score >= 0.6 else "⭐" if offer_score >= 0.4 else "💡"
        )
        message += (
            f"\n{score_emoji} <b>SCORE:</b> {score_percentage:.0f}% "
            f"({self._get_score_description(offer_score)})\n"
        )

        # Informações principais
        message += f"""
{self._get_random_emoji('tech')} <b>{self._truncate_title(offer.title)}</b>

💰 <b>Preço Atual:</b> {offer.price_formatted}
"""

        if offer.has_discount:
            message += f"🏷️ <b>Preço Original:</b> {offer.original_price_formatted}\n"
            message += f"🔥 <b>Desconto:</b> {offer.discount_formatted}\n"

        # Informações adicionais
        if offer.description:
            message += f"\n📝 {self._truncate_description(offer.description)}\n"

        if offer.category:
            message += f"📂 <b>Categoria:</b> {offer.category}\n"

        if offer.brand:
            message += f"🏷️ <b>Marca:</b> {offer.brand}\n"

        # Cupom e comparação de preços
        coupon_info = self._format_coupon_info(offer)
        if coupon_info:
            message += coupon_info

        price_comparison = self._format_price_comparison(offer)
        if price_comparison:
            message += price_comparison

        # Informações de estoque
        stock_info = self._format_stock_info(offer)
        if stock_info:
            message += stock_info

        # Rodapé
        message += f"""

🔗 <b>Link:</b> {offer.affiliate_url or offer.url}

⏰ <b>Válido até:</b> Oferta limitada
🏪 <b>Loja:</b> Amazon Brasil
🚚 <b>Frete:</b> Verificar disponibilidade
        """.strip()

        return message

    def _apply_enhanced_template(
        self, offer: Offer, platform_name: str, extra_info: str = ""
    ) -> str:
        """Aplica template aprimorado com scoring e badges para qualquer plataforma"""
        # Análise de preços e scoring
        price_analysis = self._analyze_price_history(offer)
        offer_score = self._calculate_offer_score(offer, price_analysis)
        urgency_emoji = self._get_urgency_emoji(price_analysis["urgency_level"])

        # Cabeçalho com badges de qualidade
        message = f"""
{urgency_emoji} <b>OFERTA {platform_name.upper()}</b>{extra_info}
"""

        # Adicionar badges de qualidade
        if price_analysis["badges"]:
            badges_text = " | ".join(price_analysis["badges"])
            message += f"\n{self._get_random_emoji('quality')} <b>{badges_text}</b>\n"

        # Badges de tempo e confiabilidade
        time_badge = self._format_time_badge(offer)
        if time_badge:
            message += f"\n{time_badge}\n"

        trust_badge = self._format_store_trust_badge(offer)
        if trust_badge:
            message += f"\n{trust_badge}\n"

        # Score da oferta
        score_percentage = offer_score * 100
        score_emoji = (
            "🏆"
            if offer_score >= 0.8
            else "💎" if offer_score >= 0.6 else "⭐" if offer_score >= 0.4 else "💡"
        )
        message += (
            f"\n{score_percentage:.0f}% {score_emoji} <b>SCORE:</b> "
            f"{self._get_score_description(offer_score)}\n"
        )

        # Informações principais com emoji de categoria
        category_emoji = (
            self._get_category_emoji(offer.category)
            if offer.category
            else self._get_random_emoji("tech")
        )
        message += f"""
{category_emoji} <b>{self._truncate_title(offer.title)}</b>

{self._format_price_with_emoji(offer.price)}
"""

        if offer.has_discount and offer.discount_percentage:
            message += f"🏷️ <b>Preço Original:</b> {offer.original_price_formatted}\n"
            message += (
                f"{self._format_discount_with_emoji(offer.discount_percentage)}\n"
            )

        # Informações adicionais
        if offer.description:
            message += f"\n📝 {self._truncate_description(offer.description)}\n"

        if offer.category:
            message += f"📂 <b>Categoria:</b> {offer.category}\n"

        if offer.brand:
            message += f"🏷️ <b>Marca:</b> {offer.brand}\n"

        # Cupom e comparação de preços
        coupon_info = self._format_coupon_info(offer)
        if coupon_info:
            message += coupon_info

        price_comparison = self._format_price_comparison(offer)
        if price_comparison:
            message += price_comparison

        # Informações de estoque
        stock_info = self._format_stock_info(offer)
        if stock_info:
            message += stock_info

        # Informações de frete
        shipping_info = self._format_shipping_info(offer)
        if shipping_info:
            message += shipping_info

        # Opções de pagamento
        payment_info = self._format_payment_options(offer)
        if payment_info:
            message += payment_info

        # Rodapé
        message += f"""

🔗 <b>Link:</b> {offer.affiliate_url or offer.url}

⏰ <b>Válido até:</b> Oferta limitada
🏪 <b>Loja:</b> {offer.store}
        """.strip()

        return message

    def _build_mercadolivre_template(self, offer: Offer) -> str:
        """Template específico para ofertas Mercado Livre"""
        return self._apply_enhanced_template(offer, "MERCADO LIVRE")

    def _build_shopee_template(self, offer: Offer) -> str:
        """Template específico para ofertas Shopee"""
        return self._apply_enhanced_template(offer, "SHOPEE")

    def _build_magazineluiza_template(self, offer: Offer) -> str:
        """Template específico para ofertas Magazine Luiza"""
        return self._apply_enhanced_template(offer, "MAGAZINE LUIZA")

    def _build_aliexpress_template(self, offer: Offer) -> str:
        """Template específico para ofertas AliExpress"""
        return self._apply_enhanced_template(offer, "ALIEXPRESS")

    def _build_default_template(self, offer: Offer) -> str:
        """Template padrão para ofertas de outras plataformas"""
        return self._apply_enhanced_template(offer, "ESPECIAL")

    def _format_single_offer(self, offer: Offer, index: int) -> str:
        """Formata uma oferta individual para lista"""
        platform = detect_platform(offer.url)
        platform_emoji = self._get_platform_emoji(platform) if platform else "🛒"

        offer_text = (
            f"{index}. {platform_emoji} <b>{self._truncate_title(offer.title)}</b>\n"
        )
        offer_text += f"💰 <b>{offer.price_formatted}</b>"

        if offer.has_discount:
            offer_text += (
                f" (🏷️ {offer.original_price_formatted} - {offer.discount_formatted})"
            )

        offer_text += f"\n🏪 {offer.store}"

        if offer.affiliate_url:
            offer_text += f"\n🔗 <a href='{offer.affiliate_url}'>Ver oferta</a>"

        return offer_text

    def _truncate_title(self, title: str) -> str:
        """Trunca título se muito longo"""
        if not title or len(title) <= self.max_title_length:
            return title or ""
        return title[: self.max_title_length - 3] + "..."

    def _truncate_description(self, description: str) -> str:
        """Trunca descrição se muito longa"""
        if not description or len(description) <= self.max_description_length:
            return description or ""
        return description[: self.max_description_length - 3] + "..."

    def _get_random_emoji(self, category: str) -> str:
        """Retorna emoji aleatório da categoria"""
        import random

        emojis = self.emojis.get(category, self.emojis["general"])
        return random.choice(emojis)

    def _get_platform_emoji(self, platform: str) -> str:
        """Retorna emoji específico da plataforma"""
        if not platform:
            return "🛒"

        platform_emojis = {
            "awin": "🛒",
            "amazon": "📦",
            "mercadolivre": "🟡",
            "shopee": "🟠",
            "magazineluiza": "🟣",
            "aliexpress": "🔴",
        }
        return platform_emojis.get(platform, "🛒")

    def _analyze_price_history(self, offer: Offer) -> Dict[str, Any]:
        """Analisa histórico de preços e retorna badges de qualidade"""
        badges = []
        price_analysis = {}

        # Simular dados de histórico (em produção viria do banco)
        # Aqui você integraria com o sistema de preços históricos

        if offer.has_discount and offer.discount_percentage:
            discount = offer.discount_percentage
            if discount >= 50:
                badges.append(self.quality_badges["flash_sale"])
                price_analysis["urgency"] = "high"
            elif discount >= 30:
                badges.append(self.quality_badges["price_drop"])
                price_analysis["urgency"] = "medium"
            elif discount >= 15:
                price_analysis["urgency"] = "low"

        # Badges baseados em dados simulados
        if offer.store_data and offer.store_data.get("is_best_price_90d", False):
            badges.append(self.quality_badges["best_price_90d"])
            price_analysis["price_90d"] = "best"

        if offer.store_data and offer.store_data.get("is_best_price_30d", False):
            badges.append(self.quality_badges["best_price_30d"])
            price_analysis["price_30d"] = "best"

        if offer.store_data and offer.store_data.get("limited_stock", False):
            badges.append(self.quality_badges["limited_stock"])
            price_analysis["stock"] = "limited"

        if offer.store_data and offer.store_data.get("is_new", False):
            badges.append(self.quality_badges["new_arrival"])

        if offer.store_data and offer.store_data.get("is_trending", False):
            badges.append(self.quality_badges["trending"])

        if offer.store_data and offer.store_data.get("is_exclusive", False):
            badges.append(self.quality_badges["exclusive"])

        return {
            "badges": badges,
            "price_analysis": price_analysis,
            "urgency_level": price_analysis.get("urgency", "none"),
        }

    def _calculate_offer_score(
        self, offer: Offer, price_analysis: Dict[str, Any]
    ) -> float:
        """Calcula score da oferta baseado em múltiplos critérios"""
        score = 0.0

        # Score por desconto
        if offer.has_discount and offer.discount_percentage:
            discount_score = min(offer.discount_percentage / 100.0, 1.0)
            score += discount_score * self.scoring_weights["discount_percentage"]

        # Score por preço histórico
        if price_analysis.get("price_90d") == "best":
            score += self.scoring_weights["price_drop_90d"]

        if price_analysis.get("price_30d") == "best":
            score += self.scoring_weights["price_drop_30d"]

        # Score por estoque
        if price_analysis.get("stock") == "limited":
            score += self.scoring_weights["stock_availability"]

        # Score por marca (simulado)
        premium_brands = ["Apple", "Samsung", "Sony", "LG", "Dell", "HP", "ASUS", "MSI"]
        if offer.brand and offer.brand in premium_brands:
            score += self.scoring_weights["brand_reputation"]

        return min(score, 1.0)

    def _get_urgency_emoji(self, urgency_level: str) -> str:
        """Retorna emoji baseado no nível de urgência"""
        urgency_emojis = {"high": "🚨", "medium": "⚡", "low": "💡", "none": "ℹ️"}
        return urgency_emojis.get(urgency_level, "ℹ️")

    def _format_coupon_info(self, offer: Offer) -> str:
        """Formata informações de cupom se disponível"""
        coupon_info = ""

        if hasattr(offer, "coupon_code") and offer.coupon_code:
            coupon_info += f"\n🎫 <b>CUPOM:</b> <code>{offer.coupon_code}</code>"

            if hasattr(offer, "coupon_discount") and offer.coupon_discount:
                coupon_info += f" (-{offer.coupon_discount}%)"

            if hasattr(offer, "coupon_valid_until") and offer.coupon_valid_until:
                coupon_info += f"\n⏰ <b>Válido até:</b> {offer.coupon_valid_until}"

        return coupon_info

    def _format_price_comparison(self, offer: Offer) -> str:
        """Formata comparação de preços com outras lojas"""
        price_comparison = ""

        # Simular dados de comparação (em produção viria do sistema de preços)
        if offer.store_data and offer.store_data.get("price_comparison"):
            comparison = offer.store_data["price_comparison"]

            if comparison.get("lowest_other_store"):
                other_store = comparison["lowest_other_store"]
                other_price = comparison["lowest_other_price"]

                # Converter para Decimal para operações matemáticas
                if isinstance(other_price, (int, float)):
                    other_price = Decimal(str(other_price))

                savings = offer.price - other_price

                if savings > 0:
                    price_comparison += f"\n💡 <b>Economia vs {other_store}:</b> R$ {float(savings):.2f}"
                else:
                    price_comparison += f"\n⚠️ <b>Preço similar em {other_store}</b>"

        return price_comparison

    def _format_stock_info(self, offer: Offer) -> str:
        """Formata informações de estoque"""
        stock_info = ""

        if hasattr(offer, "stock_quantity") and offer.stock_quantity is not None:
            if offer.stock_quantity <= 0:
                stock_info += "\n❌ <b>ESGOTADO</b>"
            elif offer.stock_quantity <= 5:
                stock_info += (
                    f"\n📦 <b>ESTOQUE LIMITADO:</b> {offer.stock_quantity} unidades"
                )
            elif offer.stock_quantity <= 20:
                stock_info += (
                    f"\n📦 <b>ESTOQUE BAIXO:</b> {offer.stock_quantity} unidades"
                )

        return stock_info

    def build_price_alert_message(
        self, offer: Offer, old_price: Decimal, new_price: Decimal
    ) -> str:
        """Constrói mensagem de alerta de preço"""
        price_change = new_price - old_price
        change_percentage = (price_change / old_price) * 100

        if price_change < 0:
            emoji = "📉"
            change_text = f"queda de {abs(change_percentage):.1f}%"
        else:
            emoji = "📈"
            change_text = f"aumento de {change_percentage:.1f}%"

        message = f"""
{emoji} <b>ALERTA DE PREÇO!</b>

{self._get_random_emoji('tech')} <b>{self._truncate_title(offer.title)}</b>

💰 <b>Preço Anterior:</b> R$ {old_price:.2f}
💰 <b>Preço Atual:</b> R$ {new_price:.2f}
📊 <b>Variação:</b> {change_text}

🔗 <b>Link:</b> {offer.affiliate_url or offer.url}
🏪 <b>Loja:</b> {offer.store}
        """.strip()

        return message

    def build_error_message(self, error: str, context: str = "") -> str:
        """Constrói mensagem de erro"""
        message = f"""
❌ <b>ERRO NO SISTEMA</b>

🔍 <b>Contexto:</b> {context or 'Operação geral'}
💥 <b>Erro:</b> {error}

⏰ <b>Timestamp:</b> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
📱 <b>Status:</b> Sistema continua operacional
        """.strip()

        return message

    def build_success_message(self, action: str, details: str = "") -> str:
        """Constrói mensagem de sucesso"""
        message = f"""
✅ <b>OPERAÇÃO REALIZADA COM SUCESSO!</b>

🎯 <b>Ação:</b> {action}
📝 <b>Detalhes:</b> {details or 'Nenhum detalhe adicional'}

⏰ <b>Timestamp:</b> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
        """.strip()

        return message

    def _get_category_emoji(self, category: str) -> str:
        """Retorna emoji específico da categoria do produto"""
        if not category:
            return self._get_random_emoji("category")

        # Normalizar categoria para busca
        category_lower = category.lower().strip()

        # Buscar por palavras-chave
        for key, emoji in self.category_emojis.items():
            if key in category_lower:
                return emoji

        # Buscar por palavras específicas
        if any(word in category_lower for word in ["smartphone", "celular", "phone"]):
            return "📱"
        elif any(word in category_lower for word in ["laptop", "notebook", "portátil"]):
            return "💻"
        elif any(word in category_lower for word in ["desktop", "computador", "pc"]):
            return "🖥️"
        elif any(word in category_lower for word in ["gaming", "game", "jogo"]):
            return "🎮"
        elif any(word in category_lower for word in ["audio", "som", "fone"]):
            return "🎧"
        elif any(word in category_lower for word in ["camera", "câmera", "foto"]):
            return "📷"
        elif any(word in category_lower for word in ["tv", "televisão", "televisao"]):
            return "📺"
        elif any(word in category_lower for word in ["tablet", "ipad"]):
            return "📱"
        elif any(word in category_lower for word in ["keyboard", "teclado"]):
            return "⌨️"
        elif any(word in category_lower for word in ["mouse", "rato"]):
            return "🖱️"
        elif any(word in category_lower for word in ["monitor", "tela"]):
            return "🖥️"
        elif any(word in category_lower for word in ["headphones", "fone", "headset"]):
            return "🎧"
        elif any(
            word in category_lower for word in ["speaker", "alto-falante", "caixa"]
        ):
            return "🔊"
        elif any(word in category_lower for word in ["microphone", "microfone", "mic"]):
            return "🎤"
        elif any(word in category_lower for word in ["webcam", "câmera web"]):
            return "📹"
        elif any(word in category_lower for word in ["router", "roteador"]):
            return "📡"
        elif any(
            word in category_lower for word in ["storage", "armazenamento", "ssd", "hd"]
        ):
            return "💾"
        elif any(word in category_lower for word in ["memory", "memória", "ram"]):
            return "🧠"
        elif any(
            word in category_lower for word in ["processor", "processador", "cpu"]
        ):
            return "⚡"
        elif any(
            word in category_lower for word in ["graphics", "placa de vídeo", "gpu"]
        ):
            return "🎨"
        elif any(
            word in category_lower for word in ["motherboard", "placa-mãe", "placa mae"]
        ):
            return "🔌"
        elif any(word in category_lower for word in ["power", "fonte", "energia"]):
            return "🔋"
        elif any(word in category_lower for word in ["case", "gabinete", "caixa"]):
            return "📦"
        elif any(
            word in category_lower for word in ["cooling", "resfriamento", "ventilador"]
        ):
            return "❄️"
        elif any(word in category_lower for word in ["network", "rede", "internet"]):
            return "🌐"
        elif any(
            word in category_lower for word in ["security", "segurança", "seguranca"]
        ):
            return "🔒"
        elif any(
            word in category_lower for word in ["software", "programa", "aplicativo"]
        ):
            return "💿"
        elif any(
            word in category_lower
            for word in ["accessories", "acessórios", "acessorios"]
        ):
            return "🔧"

        return self._get_random_emoji("category")

    def _get_shipping_emoji(self, shipping_type: str) -> str:
        """Retorna emoji baseado no tipo de entrega"""
        if not shipping_type:
            return self._get_random_emoji("shipping")

        shipping_lower = shipping_type.lower().strip()

        for key, emoji in self.shipping_emojis.items():
            if key in shipping_lower:
                return emoji

        # Buscar por palavras específicas
        if any(word in shipping_lower for word in ["grátis", "gratis", "free"]):
            return "🚚"
        elif any(word in shipping_lower for word in ["pago", "paid", "cobrado"]):
            return "💳"
        elif any(
            word in shipping_lower for word in ["rápido", "rapido", "fast", "express"]
        ):
            return "⚡"
        elif any(word in shipping_lower for word in ["padrão", "padrao", "standard"]):
            return "📦"
        elif any(word in shipping_lower for word in ["mesmo dia", "same day"]):
            return "🚀"
        elif any(word in shipping_lower for word in ["próximo dia", "next day"]):
            return "⚡"
        elif any(word in shipping_lower for word in ["retirada", "pickup"]):
            return "🏪"
        elif any(word in shipping_lower for word in ["digital", "download"]):
            return "💻"

        return self._get_random_emoji("shipping")

    def _get_payment_emoji(self, payment_method: str) -> str:
        """Retorna emoji baseado no método de pagamento"""
        if not payment_method:
            return self._get_random_emoji("payment")

        payment_lower = payment_method.lower().strip()

        for key, emoji in self.payment_emojis.items():
            if key in payment_lower:
                return emoji

        # Buscar por palavras específicas
        if any(word in payment_lower for word in ["cartão", "card", "credit", "debit"]):
            return "💳"
        elif any(word in payment_lower for word in ["pix"]):
            return "📱"
        elif any(word in payment_lower for word in ["boleto"]):
            return "📄"
        elif any(word in payment_lower for word in ["paypal"]):
            return "💳"
        elif any(word in payment_lower for word in ["cripto", "crypto", "bitcoin"]):
            return "₿"
        elif any(word in payment_lower for word in ["parcelado", "installments"]):
            return "💳"
        elif any(word in payment_lower for word in ["dinheiro", "cash"]):
            return "💰"
        elif any(word in payment_lower for word in ["transferência", "transfer"]):
            return "🏦"
        elif any(word in payment_lower for word in ["carteira", "wallet"]):
            return "👛"

        return self._get_random_emoji("payment")

    def _format_price_with_emoji(self, price: Decimal, currency: str = "R$") -> str:
        """Formata preço com emoji baseado no valor"""
        if not price:
            return f"💰 {currency} 0,00"

        price_float = float(price)

        if price_float < 50:
            return f"💸 {currency} {price_float:.2f}".replace(".", ",")
        elif price_float < 200:
            return f"💰 {currency} {price_float:.2f}".replace(".", ",")
        elif price_float < 500:
            return f"💎 {currency} {price_float:.2f}".replace(".", ",")
        elif price_float < 1000:
            return f"🏆 {currency} {price_float:.2f}".replace(".", ",")
        else:
            return f"👑 {currency} {price_float:.2f}".replace(".", ",")

    def _format_discount_with_emoji(self, discount_percentage: float) -> str:
        """Formata desconto com emoji baseado na porcentagem"""
        if not discount_percentage or discount_percentage <= 0:
            return ""

        if discount_percentage >= 50:
            return f"🔥 DESCONTO IMPRESSIONANTE: {discount_percentage:.0f}%"
        elif discount_percentage >= 30:
            return f"⚡ DESCONTO EXCELENTE: {discount_percentage:.0f}%"
        elif discount_percentage >= 20:
            return f"💎 DESCONTO BOM: {discount_percentage:.0f}%"
        elif discount_percentage >= 10:
            return f"💰 DESCONTO: {discount_percentage:.0f}%"
        else:
            return f"💡 PEQUENO DESCONTO: {discount_percentage:.0f}%"

    def _format_time_badge(self, offer: Offer) -> str:
        """Formata badge de tempo baseado na urgência da oferta"""
        if not offer.store_data:
            return ""

        # Simular dados de tempo (em produção viria do sistema)
        if offer.store_data.get("is_flash_sale", False):
            return f"{self._get_random_emoji('time')} OFERTA RELÂMPAGO - APENAS HOJE!"
        elif offer.store_data.get("is_limited_time", False):
            return f"{self._get_random_emoji('time')} TEMPO LIMITADO - CORRA!"
        elif offer.store_data.get("is_last_chance", False):
            return f"{self._get_random_emoji('time')} ÚLTIMA CHANCE - NÃO PERCA!"
        elif offer.store_data.get("is_seasonal", False):
            return f"{self._get_random_emoji('time')} OFERTA SAZONAL - APROVEITE!"

        return ""

    def _format_store_trust_badge(self, offer: Offer) -> str:
        """Formata badge de confiabilidade da loja"""
        if not offer.store_data:
            return ""

        store_rating = offer.store_data.get("rating", 0)
        store_reviews = offer.store_data.get("reviews_count", 0)

        if store_rating >= 4.5 and store_reviews >= 1000:
            return f"{self._get_random_emoji('quality')} LOJA EXCELENTE ({store_rating:.1f}⭐)"
        elif store_rating >= 4.0 and store_reviews >= 500:
            return f"{self._get_random_emoji('quality')} LOJA CONFIÁVEL ({store_rating:.1f}⭐)"
        elif store_rating >= 3.5 and store_reviews >= 100:
            return (
                f"{self._get_random_emoji('quality')} LOJA BOA ({store_rating:.1f}⭐)"
            )

        return ""

    def _format_shipping_info(self, offer: Offer) -> str:
        """Formata informações de frete e entrega"""
        if not offer.store_data:
            return ""

        shipping_info = ""
        shipping_data = offer.store_data.get("shipping", {})

        if shipping_data.get("is_free", False):
            shipping_info += (
                f"\n{self._get_shipping_emoji('free')} <b>FRETE GRÁTIS!</b>"
            )
        elif shipping_data.get("cost"):
            cost = shipping_data["cost"]
            if cost <= 10:
                shipping_info += (
                    f"\n{self._get_shipping_emoji('paid')} <b>Frete:</b> R$ {cost:.2f}"
                )
            else:
                shipping_info += (
                    f"\n{self._get_shipping_emoji('paid')} <b>Frete:</b> R$ {cost:.2f}"
                )

        if shipping_data.get("delivery_time"):
            delivery_time = shipping_data["delivery_time"]
            if delivery_time <= 1:
                shipping_info += f"\n{self._get_shipping_emoji('same_day')} <b>Entrega:</b> Mesmo dia"
            elif delivery_time <= 2:
                shipping_info += f"\n{self._get_shipping_emoji('next_day')} <b>Entrega:</b> Próximo dia"
            elif delivery_time <= 5:
                shipping_info += f"\n{self._get_shipping_emoji('fast')} <b>Entrega:</b> {delivery_time} dias"
            else:
                shipping_info += f"\n{self._get_shipping_emoji('standard')} <b>Entrega:</b> {delivery_time} dias"

        return shipping_info

    def _format_payment_options(self, offer: Offer) -> str:
        """Formata opções de pagamento disponíveis"""
        if not offer.store_data:
            return ""

        payment_info = ""
        payment_data = offer.store_data.get("payment", {})

        if payment_data.get("installments"):
            installments = payment_data["installments"]
            if installments >= 12:
                payment_info += (
                    f"\n{self._get_payment_emoji('installments')} <b>Parcelamento:</b> "
                    f"Até {installments}x sem juros!"
                )
            elif installments >= 6:
                payment_info += f"\n{self._get_payment_emoji('installments')} <b>Parcelamento:</b> Até {installments}x"

        if payment_data.get("methods"):
            methods = payment_data["methods"]
            method_emojis = []
            for method in methods:
                method_emojis.append(self._get_payment_emoji(method))

            if method_emojis:
                payment_info += f"\n{self._get_random_emoji('payment')} <b>Pagamento:</b> {' '.join(method_emojis)}"

        return payment_info
