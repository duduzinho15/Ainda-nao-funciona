#!/usr/bin/env python3
"""
Sistema de Postagem Automática no Canal do Telegram
Posta ofertas geek/nerd/tech periodicamente
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import random

# Telegram Bot
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.constants import ParseMode

# APIs e Scrapers
from shopee_integration_system import ShopeeAPIIntegration, SortType, ListType
from aliexpress_api import AliExpressAPI
from config import *

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('geek_auto_poster.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GeekAutoPoster:
    """Sistema de postagem automática de ofertas geek"""
    
    def __init__(self):
        self.bot_token: str = TELEGRAM_BOT_TOKEN
        self.chat_id: str = TELEGRAM_CHAT_ID
        
        # Inicializa o bot corretamente
        self.bot: Optional[Bot] = None
        try:
            self.bot = Bot(token=self.bot_token)
            logger.info("✅ Bot do Telegram inicializado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar bot do Telegram: {e}")
            self.bot = None
        
        # Inicializa APIs
        self.shopee_api = ShopeeAPIIntegration(
            app_id="18330800803",
            app_secret="IOMXMSUM5KDOLSYKXQERKCU42SNMJERR"
        )
        
        # Inicializa API do AliExpress
        self.aliexpress_api = AliExpressAPI()
        
        # Configurações de postagem
        self.posting_schedule = {
            "morning": "08:00",      # Manhã - pessoas indo trabalhar
            "lunch": "12:00",       # Almoço - pausa para ver ofertas
            "afternoon": "15:00",   # Tarde - pausa do café
            "evening": "19:00",     # Noite - pessoas em casa
            "night": "21:00"        # Noite - tempo livre
        }
        
        # Categorias para postar
        self.categories_to_post = [
            "smartphone", "notebook", "gamer", "gaming", "tech",
            "fone", "headphone", "mouse", "teclado", "monitor"
        ]
        
        # Cache de produtos já postados
        self.posted_products = set()
        self.cache_expiry = timedelta(hours=6)  # 6 horas
        
        # Estatísticas
        self.stats = {
            "total_posts": 0,
            "total_products": 0,
            "total_commissions": 0.0,
            "last_post": None,
            "posts_today": 0
        }
        
        # Controle de agendamento
        self.running = True
        self.last_daily_reset = datetime.now().date()
    
    async def post_geek_offers(self, category: Optional[str] = None, limit: int = 3):
        """Posta ofertas geek no canal"""
        try:
            # Verifica se o bot está disponível
            if not self.bot:
                logger.error("❌ Bot do Telegram não está disponível")
                return False
                
            logger.info(f"🔍 Buscando ofertas para postar (categoria: {category or 'geral'})")
            
            all_products = []
            
            # Busca produtos da Shopee
            try:
                if category:
                    # Busca produtos específicos da categoria
                    shopee_products = self.shopee_api.search_products(category, page=0, limit=limit * 2)
                else:
                    # Busca melhores ofertas gerais
                    shopee_products = self.shopee_api.get_product_offers(
                        page=0, 
                        limit=limit * 2, 
                        sort_type=SortType.COMMISSION_HIGH_LOW
                    )
                
                if shopee_products:
                    # Filtra produtos geek da Shopee
                    geek_shopee = self.filter_geek_products(shopee_products)
                    all_products.extend(geek_shopee)
                    
            except Exception as e:
                logger.warning(f"Erro ao buscar na Shopee: {e}")
            
            # Busca produtos do AliExpress
            try:
                if category:
                    aliexpress_products = self.aliexpress_api.search_products(category, page_size=limit * 2)
                else:
                    aliexpress_products = self.aliexpress_api.search_products("tech", page_size=limit * 2)
                
                if aliexpress_products:
                    # Converte produtos do AliExpress para formato compatível
                    converted_aliexpress = self.convert_aliexpress_products(aliexpress_products)
                    all_products.extend(converted_aliexpress)
                    
            except Exception as e:
                logger.warning(f"Erro ao buscar no AliExpress: {e}")
            
            if not all_products:
                logger.warning("❌ Nenhum produto encontrado para postar")
                return False
            
            # Filtra produtos não postados
            new_products = self.filter_new_products(all_products)
            
            if not new_products:
                logger.info("✅ Todos os produtos já foram postados")
                return False
            
            # Seleciona produtos para postar
            products_to_post = new_products[:limit]
            
            # Posta cada produto
            for i, product in enumerate(products_to_post, 1):
                await self.post_single_product(product, i, len(products_to_post))
                
                # Delay entre posts para não sobrecarregar
                await asyncio.sleep(random.uniform(2, 5))
            
            # Atualiza estatísticas
            self.update_stats(products_to_post)
            
            logger.info(f"✅ {len(products_to_post)} produtos postados com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao postar ofertas: {e}")
            return False
    
    def filter_geek_products(self, products) -> List:
        """Filtra produtos geek/nerd/tech"""
        geek_products = []
        
        for product in products:
            if self.is_geek_product(product):
                geek_products.append(product)
        
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
    
    def filter_new_products(self, products) -> List:
        """Filtra produtos que ainda não foram postados"""
        new_products = []
        
        for product in products:
            # Cria uma chave única para o produto
            product_key = f"{product.shop_name}_{product.price}_{product.commission}"
            
            if product_key not in self.posted_products:
                new_products.append(product)
        
        return new_products
    
    def convert_aliexpress_products(self, aliexpress_products) -> List:
        """Converte produtos do AliExpress para formato compatível"""
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
                
                # Cria um objeto similar ao da Shopee para compatibilidade
                converted_product = type('AliExpressProduct', (), {
                    'shop_name': product.get('shop_name', 'AliExpress'),
                    'price': float(product.get('target_sale_price', product.get('promotion_price', 0))),
                    'commission': float(product.get('target_sale_price', product.get('promotion_price', 0))) * float(product.get('commission_rate', 0.05)),
                    'commission_rate': float(product.get('commission_rate', 0.05)),
                    'rating_star': float(product.get('evaluate_rate', 0)),
                    'offer_link': product.get('promotion_link', product.get('product_detail_url', '')),
                    'timestamp': datetime.now()
                })()
                
                converted_products.append(converted_product)
                
            except Exception as e:
                logger.warning(f"Erro ao converter produto AliExpress: {e}")
                continue
        
        return converted_products
    
    async def _send_telegram_message(self, text: str, reply_markup=None, parse_mode=ParseMode.MARKDOWN):
        """Método auxiliar para enviar mensagens no Telegram"""
        if not self.bot:
            logger.error("❌ Bot do Telegram não está disponível")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            return True
        except TelegramError as e:
            logger.error(f"❌ Erro do Telegram ao enviar mensagem: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            return False
    
    async def post_single_product(self, product, index: int, total: int):
        """Posta um produto individual no canal"""
        try:
            # Verifica se o bot está disponível
            if not self.bot:
                logger.error("❌ Bot do Telegram não está disponível")
                return
            
            # Formata a mensagem
            message = self.format_product_message(product, index, total)
            
            # Botão para ver a oferta
            keyboard = [[InlineKeyboardButton("🛒 Ver Oferta", url=product.offer_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Posta no canal usando método auxiliar
            success = await self._send_telegram_message(message, reply_markup)
            
            if success:
                # Adiciona ao cache de produtos postados
                product_key = f"{product.shop_name}_{product.price}_{product.commission}"
                self.posted_products.add(product_key)
                
                logger.info(f"✅ Produto {index}/{total} postado: {product.shop_name}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao postar produto: {e}")
    
    def format_product_message(self, product, index: int, total: int) -> str:
        """Formata mensagem do produto para o canal"""
        # Determina o tipo de mensagem baseado na comissão
        if product.commission_rate >= 0.15:
            message_type = "🔥🔥 **OFERTA IMPERDÍVEL!** 🔥🔥"
            urgency = "💎 **Nunca esteve tão barato!**"
            cta = "**APROVEITAR AGORA!**"
        elif product.commission_rate >= 0.10:
            message_type = "📉 **ALERTA DE PREÇO BAIXO!** 📉"
            urgency = "✨ **Oferta especial!**"
            cta = "**Ver a Oferta**"
        else:
            message_type = "🔥 **Oferta Garimpada!** 🔥"
            urgency = "💰 **Boa oportunidade!**"
            cta = "**Ver a Oferta**"
        
        # Calcula desconto simulado
        original_price = product.price * 1.1
        discount = ((original_price - product.price) / original_price) * 100
        
        # Formata categoria
        category = self.get_product_category(product)
        category_emoji = self.get_category_emoji(category)
        
        message = f"""
{message_type}

{category_emoji} **Produto da {product.shop_name or 'Shopee'}**
💰 De ~R$ {original_price:.2f}~ por
💵 **R$ {product.price:.2f}** ({discount:.0f}% de desconto)

🏪 Vendido pela: **{product.shop_name or 'Shopee'}**
💸 Comissão: **R$ {product.commission:.2f}** ({product.commission_rate:.1%})
⭐ Avaliação: **{product.rating_star:.1f}** (se disponível)

🛒 {cta}

---
*Oferta {index} de {total} • Postado automaticamente*
        """
        
        return message.strip()
    
    def get_product_category(self, product) -> str:
        """Determina a categoria do produto"""
        if not product.offer_link:
            return "tech"
        
        link_lower = product.offer_link.lower()
        
        if any(word in link_lower for word in ["smartphone", "celular", "telefone"]):
            return "smartphone"
        elif any(word in link_lower for word in ["notebook", "laptop", "computador"]):
            return "notebook"
        elif any(word in link_lower for word in ["gamer", "gaming", "game"]):
            return "gaming"
        elif any(word in link_lower for word in ["fone", "headphone", "mouse", "teclado"]):
            return "tech_accessories"
        else:
            return "tech"
    
    def get_category_emoji(self, category: str) -> str:
        """Retorna emoji para a categoria"""
        emoji_map = {
            "smartphone": "📱",
            "notebook": "💻",
            "gaming": "🎮",
            "tech_accessories": "🎧",
            "tech": "💻"
        }
        return emoji_map.get(category, "💻")
    
    def update_stats(self, products):
        """Atualiza estatísticas de postagem"""
        self.stats["total_posts"] += 1
        self.stats["total_products"] += len(products)
        self.stats["total_commissions"] += sum(p.commission for p in products)
        self.stats["last_post"] = datetime.now()
        self.stats["posts_today"] += 1
    
    async def post_morning_offers(self):
        """Posta ofertas da manhã"""
        logger.info("🌅 Postando ofertas da manhã...")
        await self.post_geek_offers(category="smartphone", limit=2)
    
    async def post_lunch_offers(self):
        """Posta ofertas do almoço"""
        logger.info("🍽️ Postando ofertas do almoço...")
        await self.post_geek_offers(category="notebook", limit=2)
    
    async def post_afternoon_offers(self):
        """Posta ofertas da tarde"""
        logger.info("☕ Postando ofertas da tarde...")
        await self.post_geek_offers(category="gaming", limit=2)
    
    async def post_evening_offers(self):
        """Posta ofertas da noite"""
        logger.info("🌆 Postando ofertas da noite...")
        await self.post_geek_offers(category="tech", limit=3)
    
    async def post_night_offers(self):
        """Posta ofertas da madrugada"""
        logger.info("🌙 Postando ofertas da madrugada...")
        await self.post_geek_offers(limit=3)  # Ofertas gerais
    
    async def post_daily_summary(self):
        """Posta resumo diário de ofertas"""
        try:
            # Verifica se o bot está disponível
            if not self.bot:
                logger.error("❌ Bot do Telegram não está disponível")
                return
                
            logger.info("📊 Postando resumo diário...")
            
            summary_message = f"""
📊 **Resumo Diário - Garimpeiro Geek**

📅 **Data**: {datetime.now().strftime('%d/%m/%Y')}
🔢 **Total de Posts**: {self.stats['posts_today']}
📦 **Produtos Postados**: {self.stats['total_products']}
💰 **Comissões Totais**: R$ {self.stats['total_commissions']:.2f}

🎯 **Foco**: Produtos Geek, Nerd, Tech e Gaming
🏪 **Plataformas**: Shopee, Amazon, MercadoLivre

*Resumo gerado automaticamente às 23:00*
            """
            
            if self.bot:  # Verificação adicional para satisfazer o linter
                # Usa método auxiliar para enviar mensagem
                success = await self._send_telegram_message(summary_message)
                
                if success:
                    # Reseta contador diário
                    self.stats["posts_today"] = 0
                    
                    logger.info("✅ Resumo diário postado com sucesso!")
                else:
                    logger.error("❌ Falha ao postar resumo diário")
            else:
                logger.error("❌ Bot do Telegram não está disponível")
            
        except Exception as e:
            logger.error(f"❌ Erro ao postar resumo diário: {e}")
    
    def should_reset_daily_stats(self):
        """Verifica se deve resetar as estatísticas diárias"""
        current_date = datetime.now().date()
        if current_date > self.last_daily_reset:
            self.last_daily_reset = current_date
            self.stats["posts_today"] = 0
            return True
        return False
    
    async def check_and_execute_scheduled_posts(self):
        """Verifica e executa postagens agendadas"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # Verifica se deve resetar estatísticas diárias
        self.should_reset_daily_stats()
        
        # Verifica cada horário agendado
        if current_time == self.posting_schedule["morning"]:
            await self.post_morning_offers()
        elif current_time == self.posting_schedule["lunch"]:
            await self.post_lunch_offers()
        elif current_time == self.posting_schedule["afternoon"]:
            await self.post_afternoon_offers()
        elif current_time == self.posting_schedule["evening"]:
            await self.post_evening_offers()
        elif current_time == self.posting_schedule["night"]:
            await self.post_night_offers()
        elif current_time == "23:00":
            await self.post_daily_summary()
    
    async def run(self):
        """Executa o sistema de postagem automática"""
        try:
            logger.info("🚀 Iniciando Sistema de Postagem Automática Geek")
            
            # Verifica se o bot está disponível
            if not self.bot:
                logger.error("❌ Bot do Telegram não está disponível. Verifique o token.")
                return
            
            # Posta ofertas iniciais
            logger.info("🎯 Fazendo postagem inicial...")
            await self.post_geek_offers(limit=3)
            
            # Loop principal
            logger.info("🔄 Sistema rodando - aguardando horários agendados...")
            
            while self.running:
                # Verifica postagens agendadas
                await self.check_and_execute_scheduled_posts()
                
                # Aguarda 1 minuto antes da próxima verificação
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Sistema interrompido pelo usuário")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Erro no sistema: {e}")
            self.running = False
    
    def stop(self):
        """Para o sistema de postagem"""
        self.running = False
        logger.info("⏹️ Sistema de postagem parado")

def main():
    """Função principal"""
    print("🚀 SISTEMA DE POSTAGEM AUTOMÁTICA GEEK")
    print("=" * 60)
    
    # Cria sistema
    poster = GeekAutoPoster()
    
    # Executa
    asyncio.run(poster.run())

if __name__ == "__main__":
    main()
