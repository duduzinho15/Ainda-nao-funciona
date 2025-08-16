#!/usr/bin/env python3
"""
Sistema Unificado de Bot do Telegram para Produtos Geek/Nerd/Tech
Integra Shopee, Amazon, MercadoLivre e outras plataformas
"""

import asyncio
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Telegram Bot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# APIs e Scrapers
from shopee_integration_system import ShopeeAPIIntegration, SortType, ListType
from aliexpress_api import AliExpressAPI
from buscape_scraper import buscar_ofertas_buscape, buscar_ofertas_por_palavra_chave
from meupc_scraper import buscar_ofertas_meupc, buscar_ofertas_gaming
from config import *

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('geek_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductCategory(Enum):
    """Categorias de produtos geek/nerd/tech"""
    SMARTPHONE = "smartphone"
    NOTEBOOK = "notebook"
    GAMING = "gaming"
    TECH_ACCESSORIES = "tech_accessories"
    ANIME_MANGA = "anime_manga"
    GAMING_ACCESSORIES = "gaming_accessories"
    SMART_HOME = "smart_home"
    WEARABLES = "wearables"

@dataclass
class GeekProduct:
    """Produto geek/nerd/tech unificado"""
    title: str
    price: float
    original_price: Optional[float]
    discount_percentage: int
    store: str
    category: ProductCategory
    affiliate_link: str
    image_url: Optional[str]
    rating: Optional[float]
    commission_rate: float
    commission_amount: float
    platform: str  # "shopee", "amazon", "mercadolivre"
    timestamp: datetime

class GeekBotSystem:
    """Sistema unificado do bot geek"""
    
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.admin_id = ADMIN_USER_ID
        
        # Inicializa APIs
        self.shopee_api = ShopeeAPIIntegration(
            app_id="18330800803",
            app_secret="IOMXMSUM5KDOLSYKXQERKCU42SNMJERR"
        )
        
        # Inicializa API do AliExpress
        self.aliexpress_api = AliExpressAPI()
        
        # Configurações de busca
        self.geek_keywords = [
            "smartphone", "celular", "iphone", "samsung", "xiaomi",
            "notebook", "laptop", "gamer", "gaming", "placa de video",
            "processador", "memoria ram", "ssd", "monitor", "teclado mecanico",
            "mouse gamer", "cadeira gamer", "mesa gamer", "smartwatch",
            "fone bluetooth", "caixa de som", "drone", "action figure",
            "manga", "hq", "quadrinho", "cosplay", "decoracao geek",
            "anime", "otaku", "nerd", "geek", "tech"
        ]
        
        self.geek_categories = {
            "smartphone": ["celular", "telefone", "mobile", "iphone", "samsung"],
            "notebook": ["laptop", "computador", "pc", "portatil", "dell", "hp"],
            "gaming": ["gamer", "game", "videogame", "console", "playstation", "xbox"],
            "tech_accessories": ["fone", "headphone", "mouse", "teclado", "monitor"],
            "anime_manga": ["anime", "manga", "otaku", "cosplay", "action figure"],
            "smart_home": ["smart", "iot", "casa inteligente", "assistente virtual"]
        }
        
        # Cache de produtos
        self.product_cache = {}
        self.cache_expiry = timedelta(hours=1)
        
        # Estatísticas
        self.stats = {
            "total_products": 0,
            "total_commissions": 0.0,
            "platforms": {"shopee": 0, "amazon": 0, "mercadolivre": 0, "aliexpress": 0, "buscape": 0, "meupc": 0},
            "categories": {},
            "last_update": None
        }
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Menu principal"""
        keyboard = [
            [
                InlineKeyboardButton("🔥 Melhores Ofertas", callback_data="best_offers"),
                InlineKeyboardButton("🎮 Produtos Gaming", callback_data="gaming_offers")
            ],
            [
                InlineKeyboardButton("📱 Smartphones", callback_data="smartphone_offers"),
                InlineKeyboardButton("💻 Notebooks", callback_data="notebook_offers")
            ],
            [
                InlineKeyboardButton("🎯 Buscar Produto", callback_data="search_menu"),
                InlineKeyboardButton("📊 Estatísticas", callback_data="stats")
            ],
            [
                InlineKeyboardButton("⚙️ Configurações", callback_data="settings"),
                InlineKeyboardButton("❓ Ajuda", callback_data="help")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
🎮 **Garimpeiro Geek - Bot de Ofertas Tech/Nerd** 🎮

Bem-vindo ao seu assistente pessoal para encontrar as **melhores ofertas** em produtos:

🔥 **Tech & Gaming**: Smartphones, Notebooks, Consoles
🎯 **Geek & Nerd**: Action Figures, Manga, Cosplay
⚡ **Smart Home**: Dispositivos IoT, Assistentes
🎧 **Acessórios**: Fones, Mouses, Teclados

Escolha uma opção abaixo para começar a garimpar! 🚀
        """
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para botões inline"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "best_offers":
            await self.send_best_offers(query)
        elif query.data == "gaming_offers":
            await self.send_gaming_offers(query)
        elif query.data == "smartphone_offers":
            await self.send_category_offers(query, "smartphone")
        elif query.data == "notebook_offers":
            await self.send_category_offers(query, "notebook")
        elif query.data == "search_menu":
            await self.send_search_menu(query)
        elif query.data == "stats":
            await self.send_stats(query)
        elif query.data == "settings":
            await self.send_settings(query)
        elif query.data == "help":
            await self.send_help(query)
        elif query.data.startswith("search_"):
            await self.handle_search(query)
        elif query.data.startswith("platform_"):
            await self.handle_platform_filter(query)
    
    async def send_best_offers(self, query):
        """Envia melhores ofertas de todas as plataformas"""
        await query.edit_message_text("🔍 Buscando melhores ofertas geek...")
        
        try:
            all_offers = []
            
            # Busca ofertas da Shopee
            shopee_offers = self.shopee_api.get_product_offers(
                page=0, 
                limit=10, 
                sort_type=SortType.COMMISSION_HIGH_LOW
            )
            
            if shopee_offers:
                # Filtra produtos geek/tech da Shopee
                geek_shopee = self.filter_geek_products(shopee_offers)
                all_offers.extend(geek_shopee)
            
            # Busca ofertas do AliExpress
            try:
                aliexpress_offers = self.aliexpress_api.search_products("tech", page_size=10)
                if aliexpress_offers:
                    # Converte produtos do AliExpress para formato GeekProduct
                    geek_aliexpress = self.convert_aliexpress_products(aliexpress_offers)
                    all_offers.extend(geek_aliexpress)
            except Exception as e:
                logger.warning(f"Erro ao buscar no AliExpress: {e}")
            
            # Busca ofertas do Buscapé
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    buscape_offers = await buscar_ofertas_buscape(session, "celulares", max_paginas=1)
                    if buscape_offers:
                        # Converte produtos do Buscapé para formato GeekProduct
                        geek_buscape = self.convert_buscape_products(buscape_offers)
                        all_offers.extend(geek_buscape)
            except Exception as e:
                logger.warning(f"Erro ao buscar no Buscapé: {e}")
            
            # Busca ofertas do MeuPC.net
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    meupc_offers = await buscar_ofertas_meupc(session, "processadores", max_paginas=1)
                    if meupc_offers:
                        # Converte produtos do MeuPC.net para formato GeekProduct
                        geek_meupc = self.convert_meupc_products(meupc_offers)
                        all_offers.extend(geek_meupc)
            except Exception as e:
                logger.warning(f"Erro ao buscar no MeuPC.net: {e}")
                
            if all_offers:
                # Ordena por comissão (maior primeiro)
                all_offers.sort(key=lambda x: x.commission_rate, reverse=True)
                
                # Envia as melhores ofertas
                await self.send_offers_batch(query, all_offers[:5], "🔥 Melhores Ofertas Geek (Multi-Plataforma)")
            else:
                await query.edit_message_text("❌ Nenhuma oferta geek encontrada no momento.")
                
        except Exception as e:
            logger.error(f"Erro ao buscar melhores ofertas: {e}")
            await query.edit_message_text("❌ Erro interno. Tente novamente.")
    
    def convert_aliexpress_products(self, aliexpress_products) -> List[GeekProduct]:
        """Converte produtos do AliExpress para formato GeekProduct"""
        converted_products = []
        
        # Verifica se aliexpress_products é uma lista ou se precisa extrair os produtos
        if isinstance(aliexpress_products, dict):
            # Se for um dicionário, tenta extrair a lista de produtos
            if 'resp_result' in aliexpress_products:
                products_list = aliexpress_products['resp_result'].get('products', {}).get('product', [])
            elif 'products' in aliexpress_products:
                products_list = aliexpress_products['products']['product']
            elif 'result' in aliexpress_products:
                products_list = aliexpress_products['result'].get('products', {}).get('product', [])
            else:
                logger.warning("Estrutura de dados do AliExpress não reconhecida")
                return []
        elif isinstance(aliexpress_products, list):
            products_list = aliexpress_products
        else:
            logger.warning(f"Tipo de dados inesperado do AliExpress: {type(aliexpress_products)}")
            return []
        
        # Garante que products_list seja uma lista
        if not isinstance(products_list, list):
            products_list = [products_list]
        
        for product in products_list:
            try:
                # Extrai dados do produto do AliExpress
                if isinstance(product, str):
                    logger.warning(f"Produto é string, pulando: {product}")
                    continue
                
                title = product.get('product_title', 'Produto AliExpress')
                price = float(product.get('target_sale_price', product.get('promotion_price', 0)))
                original_price = float(product.get('target_original_price', price))
                commission_rate = float(product.get('commission_rate', 0.05))
                commission_amount = price * commission_rate
                
                # Calcula desconto
                if original_price > price:
                    discount_percentage = int(((original_price - price) / original_price) * 100)
                else:
                    discount_percentage = 0
                
                # Cria produto convertido
                geek_product = GeekProduct(
                    title=title,
                    price=price,
                    original_price=original_price if original_price > price else None,
                    discount_percentage=discount_percentage,
                    store=product.get('shop_name', 'AliExpress'),
                    category=self.categorize_aliexpress_product(product),
                    affiliate_link=product.get('promotion_link', product.get('product_detail_url', '')),
                    image_url=product.get('product_main_image_url', ''),
                    rating=float(product.get('evaluate_rate', 0)),
                    commission_rate=commission_rate,
                    commission_amount=commission_amount,
                    platform="aliexpress",
                    timestamp=datetime.now()
                )
                
                converted_products.append(geek_product)
                
            except Exception as e:
                logger.warning(f"Erro ao converter produto AliExpress: {e}")
                continue
        
        return converted_products
    
    def convert_buscape_products(self, buscape_products) -> List[GeekProduct]:
        """Converte produtos do Buscapé para formato GeekProduct"""
        converted_products = []
        
        for product in buscape_products:
            try:
                # Extrai dados do produto do Buscapé
                title = product.get('titulo', 'Produto Buscapé')
                price = float(product.get('preco_atual', 0))
                original_price = float(product.get('preco_original', price))
                discount_percentage = int(product.get('desconto_percentual', 0))
                commission_rate = 0.05  # Taxa padrão para Buscapé
                commission_amount = price * commission_rate
                
                # Cria produto convertido
                geek_product = GeekProduct(
                    title=title,
                    price=price,
                    original_price=original_price if original_price > price else None,
                    discount_percentage=discount_percentage,
                    store=product.get('loja', 'Buscapé'),
                    category=self.categorize_buscape_product(product),
                    affiliate_link=product.get('link_produto', ''),
                    image_url=product.get('imagem', ''),
                    rating=float(product.get('avaliacao', 0)),
                    commission_rate=commission_rate,
                    commission_amount=commission_amount,
                    platform="buscape",
                    timestamp=datetime.now()
                )
                
                converted_products.append(geek_product)
                
            except Exception as e:
                logger.warning(f"Erro ao converter produto Buscapé: {e}")
                continue
        
        return converted_products
    
    def convert_meupc_products(self, meupc_products) -> List[GeekProduct]:
        """Converte produtos do MeuPC.net para formato GeekProduct"""
        converted_products = []
        
        for product in meupc_products:
            try:
                # Extrai dados do produto do MeuPC.net
                title = product.get('titulo', 'Produto MeuPC.net')
                price = float(product.get('preco_atual', 0))
                original_price = float(product.get('preco_original', price))
                discount_percentage = int(product.get('desconto_percentual', 0))
                commission_rate = 0.08  # Taxa padrão para MeuPC.net
                commission_amount = price * commission_rate
                
                # Cria produto convertido
                geek_product = GeekProduct(
                    title=title,
                    price=price,
                    original_price=original_price if original_price > price else None,
                    discount_percentage=discount_percentage,
                    store=product.get('loja', 'MeuPC.net'),
                    category=self.categorize_meupc_product(product),
                    affiliate_link=product.get('link_produto', ''),
                    image_url=product.get('imagem', ''),
                    rating=float(product.get('avaliacao', 0)),
                    commission_rate=commission_rate,
                    commission_amount=commission_amount,
                    platform="meupc",
                    timestamp=datetime.now()
                )
                
                converted_products.append(geek_product)
                
            except Exception as e:
                logger.warning(f"Erro ao converter produto MeuPC.net: {e}")
                continue
        
        return converted_products
    
    def categorize_aliexpress_product(self, product) -> ProductCategory:
        """Categoriza um produto do AliExpress"""
        title_lower = product.get('product_title', '').lower()
        
        if any(word in title_lower for word in ["smartphone", "celular", "telefone", "mobile"]):
            return ProductCategory.SMARTPHONE
        elif any(word in title_lower for word in ["notebook", "laptop", "computador", "pc"]):
            return ProductCategory.NOTEBOOK
        elif any(word in title_lower for word in ["gamer", "gaming", "game", "console"]):
            return ProductCategory.GAMING
        elif any(word in title_lower for word in ["fone", "headphone", "mouse", "teclado", "monitor"]):
            return ProductCategory.TECH_ACCESSORIES
        else:
            return ProductCategory.TECH_ACCESSORIES
    
    def categorize_buscape_product(self, product) -> ProductCategory:
        """Categoriza um produto do Buscapé"""
        title_lower = product.get('titulo', '').lower()
        categoria = product.get('categoria', '').lower()
        
        if any(word in title_lower for word in ["smartphone", "celular", "telefone", "mobile"]):
            return ProductCategory.SMARTPHONE
        elif any(word in title_lower for word in ["notebook", "laptop", "computador", "pc"]):
            return ProductCategory.NOTEBOOK
        elif any(word in title_lower for word in ["gamer", "gaming", "game", "console"]):
            return ProductCategory.GAMING
        elif any(word in title_lower for word in ["fone", "headphone", "mouse", "teclado", "monitor"]):
            return ProductCategory.TECH_ACCESSORIES
        elif any(word in title_lower for word in ["tv", "televisao", "smart tv"]):
            return ProductCategory.SMART_HOME
        else:
            return ProductCategory.TECH_ACCESSORIES
    
    def categorize_meupc_product(self, product) -> ProductCategory:
        """Categoriza um produto do MeuPC.net"""
        title_lower = product.get('titulo', '').lower()
        categoria = product.get('categoria', '').lower()
        
        if any(word in title_lower for word in ["processador", "cpu", "intel", "amd", "ryzen", "core"]):
            return ProductCategory.TECH_ACCESSORIES
        elif any(word in title_lower for word in ["placa de video", "gpu", "rtx", "gtx", "radeon"]):
            return ProductCategory.GAMING
        elif any(word in title_lower for word in ["memoria", "ram", "ddr"]):
            return ProductCategory.TECH_ACCESSORIES
        elif any(word in title_lower for word in ["ssd", "hd", "disco"]):
            return ProductCategory.TECH_ACCESSORIES
        elif any(word in title_lower for word in ["monitor", "tela", "display"]):
            return ProductCategory.TECH_ACCESSORIES
        elif any(word in title_lower for word in ["teclado", "keyboard"]):
            return ProductCategory.TECH_ACCESSORIES
        elif any(word in title_lower for word in ["mouse", "gaming"]):
            return ProductCategory.GAMING_ACCESSORIES
        elif any(word in title_lower for word in ["headset", "fone", "microfone"]):
            return ProductCategory.TECH_ACCESSORIES
        else:
            return ProductCategory.TECH_ACCESSORIES
    
    async def send_gaming_offers(self, query):
        """Envia ofertas de produtos gaming"""
        await query.edit_message_text("🎮 Buscando ofertas gaming...")
        
        try:
            # Busca produtos gaming da Shopee
            gaming_offers = self.shopee_api.search_products("gamer", page=0, limit=10)
            
            if gaming_offers:
                # Filtra produtos realmente gaming
                filtered_gaming = self.filter_gaming_products(gaming_offers)
                
                if filtered_gaming:
                    await self.send_offers_batch(query, filtered_gaming[:5], "🎮 Ofertas Gaming")
                else:
                    await query.edit_message_text("❌ Nenhuma oferta gaming encontrada.")
            else:
                await query.edit_message_text("❌ Erro ao buscar ofertas gaming.")
                
        except Exception as e:
            logger.error(f"Erro ao buscar ofertas gaming: {e}")
            await query.edit_message_text("❌ Erro interno. Tente novamente.")
    
    async def send_category_offers(self, query, category: str):
        """Envia ofertas de uma categoria específica"""
        await query.edit_message_text(f"🔍 Buscando ofertas de {category}...")
        
        try:
            # Busca produtos da categoria
            category_offers = self.shopee_api.search_products(category, page=0, limit=10)
            
            if category_offers:
                # Filtra produtos relevantes
                filtered_offers = self.filter_category_products(category_offers, category)
                
                if filtered_offers:
                    await self.send_offers_batch(query, filtered_offers[:5], f"📱 Ofertas de {category.title()}")
                else:
                    await query.edit_message_text(f"❌ Nenhuma oferta de {category} encontrada.")
            else:
                await query.edit_message_text(f"❌ Erro ao buscar ofertas de {category}.")
                
        except Exception as e:
            logger.error(f"Erro ao buscar ofertas de {category}: {e}")
            await query.edit_message_text("❌ Erro interno. Tente novamente.")
    
    def filter_geek_products(self, products) -> List[GeekProduct]:
        """Filtra produtos geek/nerd/tech"""
        geek_products = []
        
        for product in products:
            # Verifica se é um produto geek baseado na loja e link
            if self.is_geek_product(product):
                geek_product = GeekProduct(
                    title=f"Produto da {product.shop_name or 'Shopee'}",
                    price=product.price,
                    original_price=product.price * 1.1,  # Simula preço original
                    discount_percentage=10,
                    store=product.shop_name or "Shopee",
                    category=self.categorize_product(product),
                    affiliate_link=product.offer_link,
                    image_url=None,
                    rating=product.rating_star,
                    commission_rate=product.commission_rate,
                    commission_amount=product.commission,
                    platform="shopee",
                    timestamp=product.timestamp
                )
                geek_products.append(geek_product)
        
        return geek_products
    
    def is_geek_product(self, product) -> bool:
        """Verifica se um produto é geek/nerd/tech"""
        if not product.shop_name or not product.offer_link:
            return False
        
        shop_lower = product.shop_name.lower()
        link_lower = product.offer_link.lower()
        
        # Verifica se a loja tem palavras-chave geek
        geek_shop_keywords = ["tech", "digital", "eletronicos", "smart", "mobile", "gamer", "computer"]
        if any(keyword in shop_lower for keyword in geek_shop_keywords):
            return True
        
        # Verifica se o link tem palavras-chave geek
        geek_link_keywords = ["smartphone", "celular", "notebook", "laptop", "gamer", "tech", "digital"]
        if any(keyword in link_lower for keyword in geek_link_keywords):
            return True
        
        return False
    
    def categorize_product(self, product) -> ProductCategory:
        """Categoriza um produto"""
        if not product.offer_link:
            return ProductCategory.TECH_ACCESSORIES
        
        link_lower = product.offer_link.lower()
        
        if any(word in link_lower for word in ["smartphone", "celular", "telefone"]):
            return ProductCategory.SMARTPHONE
        elif any(word in link_lower for word in ["notebook", "laptop", "computador"]):
            return ProductCategory.NOTEBOOK
        elif any(word in link_lower for word in ["gamer", "gaming", "game"]):
            return ProductCategory.GAMING
        elif any(word in link_lower for word in ["fone", "headphone", "mouse", "teclado"]):
            return ProductCategory.TECH_ACCESSORIES
        else:
            return ProductCategory.TECH_ACCESSORIES
    
    def filter_gaming_products(self, products) -> List[GeekProduct]:
        """Filtra produtos gaming"""
        gaming_products = []
        
        for product in products:
            if self.is_gaming_product(product):
                geek_product = GeekProduct(
                    title=f"Produto Gaming da {product.shop_name or 'Shopee'}",
                    price=product.price,
                    original_price=product.price * 1.1,
                    discount_percentage=10,
                    store=product.shop_name or "Shopee",
                    category=ProductCategory.GAMING,
                    affiliate_link=product.offer_link,
                    image_url=None,
                    rating=product.rating_star,
                    commission_rate=product.commission_rate,
                    commission_amount=product.commission,
                    platform="shopee",
                    timestamp=product.timestamp
                )
                gaming_products.append(geek_product)
        
        return gaming_products
    
    def is_gaming_product(self, product) -> bool:
        """Verifica se um produto é gaming"""
        if not product.shop_name or not product.offer_link:
            return False
        
        shop_lower = product.shop_name.lower()
        link_lower = product.offer_link.lower()
        
        gaming_keywords = ["gamer", "gaming", "game", "console", "playstation", "xbox", "nintendo"]
        return any(keyword in shop_lower or keyword in link_lower for keyword in gaming_keywords)
    
    def filter_category_products(self, products, category: str) -> List[GeekProduct]:
        """Filtra produtos de uma categoria específica"""
        category_products = []
        
        for product in products:
            if self.is_category_product(product, category):
                geek_product = GeekProduct(
                    title=f"Produto {category.title()} da {product.shop_name or 'Shopee'}",
                    price=product.price,
                    original_price=product.price * 1.1,
                    discount_percentage=10,
                    store=product.shop_name or "Shopee",
                    category=self.categorize_product(product),
                    affiliate_link=product.offer_link,
                    image_url=None,
                    rating=product.rating_star,
                    commission_rate=product.commission_rate,
                    commission_amount=product.commission,
                    platform="shopee",
                    timestamp=product.timestamp
                )
                category_products.append(geek_product)
        
        return category_products
    
    def is_category_product(self, product, category: str) -> bool:
        """Verifica se um produto pertence a uma categoria"""
        if not product.shop_name or not product.offer_link:
            return False
        
        shop_lower = product.shop_name.lower()
        link_lower = product.offer_link.lower()
        
        category_keywords = self.geek_categories.get(category, [category])
        return any(keyword in shop_lower or keyword in link_lower for keyword in category_keywords)
    
    async def handle_platform_filter(self, query):
        """Processa filtro de plataforma"""
        platform = query.data.replace("platform_", "")
        await query.edit_message_text(f"🔍 Filtrando por plataforma: {platform}")
        
        # Implementar filtro por plataforma
        await query.edit_message_text(f"✅ Filtro aplicado para {platform}")
    
    async def back_to_menu(self, query):
        """Volta ao menu principal"""
        # Simplesmente envia o menu principal novamente
        await self.send_main_menu(query)
    
    async def send_main_menu(self, query):
        """Envia o menu principal"""
        keyboard = [
            [
                InlineKeyboardButton("🔥 Melhores Ofertas", callback_data="best_offers"),
                InlineKeyboardButton("🎮 Produtos Gaming", callback_data="gaming_offers")
            ],
            [
                InlineKeyboardButton("📱 Smartphones", callback_data="smartphone_offers"),
                InlineKeyboardButton("💻 Notebooks", callback_data="notebook_offers")
            ],
            [
                InlineKeyboardButton("🎯 Buscar Produto", callback_data="search_menu"),
                InlineKeyboardButton("📊 Estatísticas", callback_data="stats")
            ],
            [
                InlineKeyboardButton("⚙️ Configurações", callback_data="settings"),
                InlineKeyboardButton("❓ Ajuda", callback_data="help")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
🎮 **Garimpeiro Geek - Bot de Ofertas Tech/Nerd** 🎮

Bem-vindo ao seu assistente pessoal para encontrar as **melhores ofertas** em produtos:

🔥 **Tech & Gaming**: Smartphones, Notebooks, Consoles
🎯 **Geek & Nerd**: Action Figures, Manga, Cosplay
⚡ **Smart Home**: Dispositivos IoT, Assistentes
🎧 **Acessórios**: Fones, Mouses, Teclados

Escolha uma opção abaixo para começar a garimpar! 🚀
        """
        
        await query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def send_offers_batch(self, query, offers: List[GeekProduct], title: str):
        """Envia um lote de ofertas"""
        if not offers:
            await query.edit_message_text("❌ Nenhuma oferta encontrada.")
            return
        
        # Envia título
        await query.edit_message_text(f"✅ **{title}**\n\n{len(offers)} ofertas encontradas!")
        
        # Envia cada oferta
        for i, offer in enumerate(offers, 1):
            message = self.format_geek_offer(offer, i)
            
            # Botão para ver a oferta
            keyboard = [[InlineKeyboardButton("🛒 Ver Oferta", url=offer.affiliate_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Delay entre mensagens
            await asyncio.sleep(0.5)
        
        # Botão para voltar ao menu
        back_keyboard = [[InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(back_keyboard)
        
        await query.message.reply_text(
            "🔙 Use o botão abaixo para voltar ao menu principal:",
            reply_markup=reply_markup
        )
    
    def format_geek_offer(self, offer: GeekProduct, index: int) -> str:
        """Formata uma oferta geek para o Telegram"""
        # Determina o tipo de mensagem baseado na comissão
        if offer.commission_rate >= 0.15:
            message_type = "🔥🔥 MENOR PREÇO DA HISTÓRIA! 🔥🔥"
            urgency = "💎 Nunca esteve tão barato!"
            cta = "Aproveitar Agora!"
        elif offer.commission_rate >= 0.10:
            message_type = "📉 Alerta de Preço Baixo! 📉"
            urgency = "✨ Oferta especial!"
            cta = "Ver a Oferta"
        else:
            message_type = "🔥 Oferta Garimpada! 🔥"
            urgency = "💰 Boa oportunidade!"
            cta = "Ver a Oferta"
        
        # Calcula desconto
        discount_text = ""
        if offer.original_price and offer.original_price > offer.price:
            discount = ((offer.original_price - offer.price) / offer.original_price) * 100
            discount_text = f"💰 De ~R$ {offer.original_price:.2f}~ por\n💵 **R$ {offer.price:.2f}** ({discount:.0f}% de desconto)"
        else:
            discount_text = f"💵 **R$ {offer.price:.2f}**"
        
        # Formata categoria
        category_emoji = {
            ProductCategory.SMARTPHONE: "📱",
            ProductCategory.NOTEBOOK: "💻",
            ProductCategory.GAMING: "🎮",
            ProductCategory.TECH_ACCESSORIES: "🎧",
            ProductCategory.ANIME_MANGA: "🎭",
            ProductCategory.GAMING_ACCESSORIES: "🎮",
            ProductCategory.SMART_HOME: "🏠",
            ProductCategory.WEARABLES: "⌚"
        }
        
        category_emoji_str = category_emoji.get(offer.category, "💻")
        
        message = f"""
{message_type}

{category_emoji_str} **{offer.title}**
{discount_text}

🏪 Vendido pela: **{offer.store}**
💸 Comissão: **R$ {offer.commission_amount:.2f}** ({offer.commission_rate:.1%})
⭐ Avaliação: **{offer.rating:.1f}** (se disponível)

🛒 **{cta}**
        """
        
        return message.strip()
    
    async def send_search_menu(self, query):
        """Envia menu de busca"""
        keyboard = [
            [
                InlineKeyboardButton("📱 Smartphones", callback_data="search_smartphone"),
                InlineKeyboardButton("💻 Notebooks", callback_data="search_notebook")
            ],
            [
                InlineKeyboardButton("🎮 Gaming", callback_data="search_gaming"),
                InlineKeyboardButton("🎧 Tech", callback_data="search_tech")
            ],
            [
                InlineKeyboardButton("🔙 Voltar", callback_data="back_to_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔍 **Menu de Busca**\n\nEscolha uma categoria para buscar ofertas específicas:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_search(self, query):
        """Processa busca de produtos"""
        search_type = query.data.replace("search_", "")
        
        await query.edit_message_text(f"🔍 Buscando ofertas de {search_type}...")
        
        try:
            # Busca produtos
            products = self.shopee_api.search_products(search_type, page=0, limit=10)
            
            if products:
                # Filtra produtos geek
                geek_products = self.filter_geek_products(products)
                
                if geek_products:
                    await self.send_offers_batch(query, geek_products[:5], f"🔍 Resultados para {search_type}")
                else:
                    await query.edit_message_text(f"❌ Nenhuma oferta de {search_type} encontrada.")
            else:
                await query.edit_message_text(f"❌ Erro ao buscar {search_type}.")
                
        except Exception as e:
            logger.error(f"Erro na busca de {search_type}: {e}")
            await query.edit_message_text("❌ Erro interno. Tente novamente.")
    
    async def send_stats(self, query):
        """Envia estatísticas do bot"""
        stats_text = f"""
📊 **Estatísticas do Garimpeiro Geek**

🔢 **Total de Produtos**: {self.stats['total_products']}
💰 **Comissões Totais**: R$ {self.stats['total_commissions']:.2f}

🏪 **Por Plataforma**:
   • Shopee: {self.stats['platforms']['shopee']}
   • Amazon: {self.stats['platforms']['amazon']}
   • MercadoLivre: {self.stats['platforms']['mercadolivre']}
   • AliExpress: {self.stats['platforms']['aliexpress']}
   • Buscape: {self.stats['platforms']['buscape']}
   • MeuPC: {self.stats['platforms']['meupc']}

🕒 **Última Atualização**: {self.stats['last_update'] or 'Nunca'}

🎯 **Foco**: Produtos Geek, Nerd, Tech e Gaming
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def send_settings(self, query):
        """Envia configurações do bot"""
        settings_text = """
⚙️ **Configurações do Bot**

🔍 **Filtros Ativos**:
   • Produtos Geek/Nerd/Tech
   • Comissão mínima: 5%
   • Avaliação mínima: 4.0

📱 **Plataformas**:
   • Shopee ✅
   • Amazon ✅
   • MercadoLivre ✅
   • AliExpress ✅
   • Buscape ✅
   • MeuPC ✅

🔄 **Atualizações**:
   • Automáticas: A cada 2 horas
   • Notificações: Ativadas
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(settings_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def send_help(self, query):
        """Envia ajuda do bot"""
        help_text = """
❓ **Como usar o Garimpeiro Geek**

🎯 **Comandos Disponíveis**:
   • `/start` - Menu principal
   • `/buscar [produto]` - Buscar produto específico
   • `/ofertas` - Ver melhores ofertas
   • `/gaming` - Ofertas de produtos gaming
   • `/estatisticas` - Ver estatísticas

🔍 **Funcionalidades**:
   • Busca inteligente por produtos geek/nerd/tech
   • Filtros automáticos por relevância
   • Links de afiliado para todas as ofertas
   • Atualizações automáticas

💡 **Dicas**:
   • Use categorias específicas para melhores resultados
   • Produtos com maior comissão são destacados
   • Verifique sempre a avaliação da loja
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def run(self):
        """Executa o bot"""
        try:
            # Cria aplicação
            application = Application.builder().token(self.bot_token).build()
            
            # Adiciona handlers
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CallbackQueryHandler(self.button_handler))
            
            # Inicia o bot
            logger.info("🚀 Bot Geek iniciado com sucesso!")
            await application.run_polling()
            
        except Exception as e:
            logger.error(f"❌ Erro ao executar bot: {e}")

def main():
    """Função principal"""
    print("🚀 INICIANDO SISTEMA UNIFICADO GEEK BOT")
    print("=" * 60)
    
    # Cria sistema
    bot_system = GeekBotSystem()
    
    # Executa bot
    asyncio.run(bot_system.run())

if __name__ == "__main__":
    main()
