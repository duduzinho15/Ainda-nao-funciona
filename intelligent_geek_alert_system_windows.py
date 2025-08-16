#!/usr/bin/env python3
"""
Sistema Inteligente de Alertas Geek - Versão Windows
Busca ofertas constantemente e posta automaticamente baseado em métricas inteligentes
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import random
import sqlite3
import json
import signal
import sys

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
        logging.FileHandler('intelligent_alerts.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PriceHistoryTracker:
    """Rastreador de histórico de preços para análise inteligente"""
    
    def __init__(self, db_path="price_history.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa banco de dados para histórico de preços"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabela de produtos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT UNIQUE,
                    title TEXT,
                    platform TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de histórico de preços
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT,
                    price REAL,
                    original_price REAL,
                    discount_percentage REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (product_id)
                )
            ''')
            
            # Índices para performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_id ON price_history(product_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON price_history(timestamp)')
            
            conn.commit()
            conn.close()
            logger.info("✅ Banco de dados de histórico de preços inicializado")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar banco de dados: {e}")
    
    def add_product(self, product_id: str, title: str, platform: str, category: str):
        """Adiciona novo produto ao rastreador"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO products (product_id, title, platform, category)
                VALUES (?, ?, ?, ?)
            ''', (product_id, title, platform, category))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar produto: {e}")
    
    def record_price(self, product_id: str, price: float, original_price: float, discount_percentage: float):
        """Registra novo preço no histórico"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO price_history (product_id, price, original_price, discount_percentage)
                VALUES (?, ?, ?, ?)
            ''', (product_id, price, original_price, discount_percentage))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar preço: {e}")
    
    def get_price_history(self, product_id: str, days: int = 90) -> List[Dict]:
        """Obtém histórico de preços dos últimos N dias"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT price, original_price, discount_percentage, timestamp
                FROM price_history 
                WHERE product_id = ? AND timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            '''.format(days), (product_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'price': row[0],
                    'original_price': row[1],
                    'discount_percentage': row[2],
                    'timestamp': row[3]
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter histórico de preços: {e}")
            return []
    
    def is_lowest_price_ever(self, product_id: str, current_price: float) -> bool:
        """Verifica se o preço atual é o menor já registrado"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT MIN(price) FROM price_history WHERE product_id = ?
            ''', (product_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return current_price <= result[0]
            return True  # Primeiro preço registrado
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar menor preço: {e}")
            return False
    
    def is_lowest_price_recent(self, product_id: str, current_price: float, days: int = 90) -> bool:
        """Verifica se o preço atual é o menor dos últimos N dias"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT MIN(price) FROM price_history 
                WHERE product_id = ? AND timestamp >= datetime('now', '-{} days')
            '''.format(days), (product_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return current_price <= result[0]
            return True  # Primeiro preço registrado no período
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar menor preço recente: {e}")
            return False

class IntelligentGeekAlertSystem:
    """Sistema inteligente de alertas geek com busca constante - Versão Windows"""
    
    def __init__(self):
        self.bot_token: str = TELEGRAM_BOT_TOKEN
        self.chat_id: str = TELEGRAM_CHAT_ID
        
        # Inicializa o bot
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
        self.aliexpress_api = AliExpressAPI()
        
        # Rastreador de preços
        self.price_tracker = PriceHistoryTracker()
        
        # Configurações de alertas inteligentes
        self.alert_criteria = {
            "discount_threshold": 0.15,  # 15% de desconto mínimo
            "price_drop_threshold": 0.20,  # 20% de queda de preço
            "lowest_price_ever": True,  # Alerta para menor preço histórico
            "lowest_price_3months": True,  # Alerta para menor preço em 3 meses
            "lowest_price_6months": True,  # Alerta para menor preço em 6 meses
            "commission_threshold": 0.10,  # 10% de comissão mínima
        }
        
        # Cache de produtos já alertados
        self.alerted_products = set()
        self.alert_cooldown = timedelta(hours=6)  # 6 horas entre alertas do mesmo produto
        
        # Estatísticas
        self.stats = {
            "total_alerts": 0,
            "total_products_analyzed": 0,
            "alerts_today": 0,
            "last_alert": None,
            "search_cycles": 0
        }
        
        # Controle de execução
        self.running = True
        self.search_interval = 300  # 5 minutos entre buscas
        
        # Configuração de sinais para Windows
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Manipula sinais para parar o sistema graciosamente"""
        logger.info(f"📡 Sinal {signum} recebido. Parando sistema...")
        self.running = False
    
    def should_alert_product(self, product) -> tuple[bool, str]:
        """Determina se um produto deve gerar alerta baseado em critérios inteligentes"""
        try:
            # Cria ID único do produto
            product_id = f"{product.shop_name}_{product.price}_{product.offer_link}"
            
            # Verifica se já foi alertado recentemente
            if product_id in self.alerted_products:
                return False, "Produto já alertado recentemente"
            
            # Calcula desconto
            if hasattr(product, 'original_price') and product.original_price:
                original_price = product.original_price
            else:
                # Simula preço original se não disponível
                original_price = product.price * 1.15
            
            discount_percentage = ((original_price - product.price) / original_price) * 100
            
            # Critério 1: Desconto mínimo
            if discount_percentage < (self.alert_criteria["discount_threshold"] * 100):
                return False, f"Desconto insuficiente: {discount_percentage:.1f}%"
            
            # Critério 2: Comissão mínima
            if hasattr(product, 'commission_rate') and product.commission_rate:
                if product.commission_rate < self.alert_criteria["commission_threshold"]:
                    return False, f"Comissão baixa: {product.commission_rate:.1%}"
            
            # Critério 3: Menor preço histórico
            if self.alert_criteria["lowest_price_ever"]:
                if self.price_tracker.is_lowest_price_ever(product_id, product.price):
                    return True, f"🔥 MENOR PREÇO HISTÓRICO! Desconto: {discount_percentage:.1f}%"
            
            # Critério 4: Menor preço em 3 meses
            if self.alert_criteria["lowest_price_3months"]:
                if self.price_tracker.is_lowest_price_recent(product_id, product.price, 90):
                    return True, f"📉 MENOR PREÇO EM 3 MESES! Desconto: {discount_percentage:.1f}%"
            
            # Critério 5: Menor preço em 6 meses
            if self.alert_criteria["lowest_price_6months"]:
                if self.price_tracker.is_lowest_price_recent(product_id, product.price, 180):
                    return True, f"📊 MENOR PREÇO EM 6 MESES! Desconto: {discount_percentage:.1f}%"
            
            # Critério 6: Desconto excepcional
            if discount_percentage >= 30:
                return True, f"💎 DESCONTO EXCEPCIONAL! {discount_percentage:.1f}%"
            
            # Critério 7: Desconto alto
            if discount_percentage >= 20:
                return True, f"🔥 DESCONTO ALTO! {discount_percentage:.1f}%"
            
            return False, f"Critérios não atendidos. Desconto: {discount_percentage:.1f}%"
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar produto: {e}")
            return False, f"Erro na análise: {e}"
    
    async def search_and_analyze_products(self):
        """Busca e analisa produtos constantemente"""
        try:
            logger.info("🔍 Iniciando busca inteligente de produtos...")
            
            all_products = []
            
            # Busca produtos da Shopee
            try:
                shopee_products = self.shopee_api.get_product_offers(
                    page=0, 
                    limit=20,  # Mais produtos para análise
                    sort_type=SortType.COMMISSION_HIGH_LOW
                )
                
                if shopee_products:
                    all_products.extend(shopee_products)
                    logger.info(f"✅ {len(shopee_products)} produtos da Shopee encontrados")
                    
            except Exception as e:
                logger.warning(f"Erro ao buscar na Shopee: {e}")
            
            # Busca produtos do AliExpress
            try:
                aliexpress_products = self.aliexpress_api.search_products("tech", page_size=20)
                
                if aliexpress_products:
                    converted_aliexpress = self.convert_aliexpress_products(aliexpress_products)
                    all_products.extend(converted_aliexpress)
                    logger.info(f"✅ {len(converted_aliexpress)} produtos do AliExpress encontrados")
                    
            except Exception as e:
                logger.warning(f"Erro ao buscar no AliExpress: {e}")
            
            if not all_products:
                logger.warning("❌ Nenhum produto encontrado para análise")
                return
            
            # Analisa cada produto
            products_to_alert = []
            
            for product in all_products:
                try:
                    # Registra produto no rastreador
                    product_id = f"{product.shop_name}_{product.price}_{product.offer_link}"
                    self.price_tracker.add_product(
                        product_id, 
                        getattr(product, 'shop_name', 'Produto'),
                        getattr(product, 'platform', 'shopee'),
                        'tech'
                    )
                    
                    # Registra preço atual
                    if hasattr(product, 'original_price') and product.original_price:
                        original_price = product.original_price
                    else:
                        original_price = product.price * 1.15
                    
                    discount_percentage = ((original_price - product.price) / original_price) * 100
                    
                    self.price_tracker.record_price(
                        product_id,
                        product.price,
                        original_price,
                        discount_percentage
                    )
                    
                    # Verifica se deve gerar alerta
                    should_alert, reason = self.should_alert_product(product)
                    
                    if should_alert:
                        products_to_alert.append((product, reason))
                        logger.info(f"🚨 ALERTA GERADO: {product.shop_name} - {reason}")
                    
                    self.stats["total_products_analyzed"] += 1
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao analisar produto: {e}")
                    continue
            
            # Posta alertas se necessário
            if products_to_alert:
                await self.post_alerts(products_to_alert)
            else:
                logger.info("✅ Nenhum produto atendeu aos critérios de alerta")
            
            self.stats["search_cycles"] += 1
            
        except Exception as e:
            logger.error(f"❌ Erro na busca e análise: {e}")
    
    async def post_alerts(self, products_to_alert: List[tuple]):
        """Posta alertas no canal do Telegram"""
        try:
            logger.info(f"📢 Postando {len(products_to_alert)} alertas...")
            
            for i, (product, reason) in enumerate(products_to_alert, 1):
                try:
                    # Formata mensagem do alerta
                    message = self.format_alert_message(product, reason, i, len(products_to_alert))
                    
                    # Botão para ver a oferta
                    keyboard = [[InlineKeyboardButton("🛒 Ver Oferta", url=product.offer_link)]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # Posta no canal
                    if self.bot:
                        await self.bot.send_message(
                            chat_id=self.chat_id,
                            text=message,
                            reply_markup=reply_markup,
                            parse_mode=ParseMode.MARKDOWN
                        )
                        
                        # Adiciona ao cache de produtos alertados
                        product_id = f"{product.shop_name}_{product.price}_{product.offer_link}"
                        self.alerted_products.add(product_id)
                        
                        # Atualiza estatísticas
                        self.stats["total_alerts"] += 1
                        self.stats["alerts_today"] += 1
                        self.stats["last_alert"] = datetime.now()
                        
                        logger.info(f"✅ Alerta {i}/{len(products_to_alert)} postado: {product.shop_name}")
                        
                        # Delay entre posts
                        await asyncio.sleep(random.uniform(3, 7))
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao postar alerta {i}: {e}")
                    continue
            
            logger.info(f"✅ {len(products_to_alert)} alertas postados com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao postar alertas: {e}")
    
    def format_alert_message(self, product, reason: str, index: int, total: int) -> str:
        """Formata mensagem do alerta inteligente"""
        # Determina urgência baseada no motivo
        if "MENOR PREÇO HISTÓRICO" in reason:
            urgency_emoji = "🔥🔥🔥"
            urgency_text = "🚨 **ALERTA MÁXIMO - MENOR PREÇO HISTÓRICO!** 🚨"
        elif "MENOR PREÇO EM 3 MESES" in reason:
            urgency_emoji = "🔥🔥"
            urgency_text = "📉 **ALERTA ALTO - MENOR PREÇO EM 3 MESES!** 📉"
        elif "DESCONTO EXCEPCIONAL" in reason:
            urgency_emoji = "💎"
            urgency_text = "💎 **DESCONTO EXCEPCIONAL!** 💎"
        else:
            urgency_emoji = "🔥"
            urgency_text = "🔥 **OFERTA IMPERDÍVEL!** 🔥"
        
        # Calcula desconto
        if hasattr(product, 'original_price') and product.original_price:
            original_price = product.original_price
        else:
            original_price = product.price * 1.15
        
        discount_percentage = ((original_price - product.price) / original_price) * 100
        
        # Formata categoria
        category = self.get_product_category(product)
        category_emoji = self.get_category_emoji(category)
        
        message = f"""
{urgency_emoji} {urgency_text}

{reason}

{category_emoji} **Produto da {product.shop_name or 'Shopee'}**
💰 De ~R$ {original_price:.2f}~ por
💵 **R$ {product.price:.2f}** ({discount_percentage:.0f}% de desconto)

🏪 Vendido pela: **{product.shop_name or 'Shopee'}**
💸 Comissão: **R$ {getattr(product, 'commission', 0):.2f}** ({getattr(product, 'commission_rate', 0):.1%})
⭐ Avaliação: **{getattr(product, 'rating_star', 'N/A')}**

🛒 **APROVEITAR AGORA!**

---
*Alerta {index} de {total} • Sistema Inteligente Geek*
        """
        
        return message.strip()
    
    def get_product_category(self, product) -> str:
        """Determina a categoria do produto"""
        if not hasattr(product, 'offer_link') or not product.offer_link:
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
    
    def convert_aliexpress_products(self, aliexpress_products) -> List:
        """Converte produtos do AliExpress para formato compatível"""
        converted_products = []
        
        # Verifica se aliexpress_products é uma lista ou se precisa extrair os produtos
        if isinstance(aliexpress_products, dict):
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
                    'timestamp': datetime.now(),
                    'platform': 'aliexpress'
                })()
                
                converted_products.append(converted_product)
                
            except Exception as e:
                logger.warning(f"Erro ao converter produto AliExpress: {e}")
                continue
        
        return converted_products
    
    async def run_continuous_search(self):
        """Executa busca contínua de ofertas - Versão Windows otimizada"""
        try:
            logger.info("🚀 Iniciando Sistema Inteligente de Alertas Geek")
            logger.info("🔍 Busca contínua ativada - analisando produtos a cada 5 minutos")
            
            if not self.bot:
                logger.error("❌ Bot do Telegram não está disponível. Verifique o token.")
                return
            
            # Primeira busca imediata
            await self.search_and_analyze_products()
            
            # Loop principal de busca contínua
            while self.running:
                try:
                    # Aguarda intervalo configurado usando time.sleep para Windows
                    for _ in range(self.search_interval):
                        if not self.running:
                            break
                        await asyncio.sleep(1)
                    
                    if not self.running:
                        break
                    
                    # Executa nova busca
                    await self.search_and_analyze_products()
                    
                    # Log de status
                    logger.info(f"🔄 Ciclo de busca {self.stats['search_cycles']} concluído")
                    logger.info(f"📊 Estatísticas: {self.stats['total_alerts']} alertas, {self.stats['total_products_analyzed']} produtos analisados")
                    
                except Exception as e:
                    logger.error(f"❌ Erro no ciclo de busca: {e}")
                    # Aguarda 1 minuto em caso de erro
                    for _ in range(60):
                        if not self.running:
                            break
                        await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("⏹️ Sistema interrompido pelo usuário")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Erro no sistema: {e}")
            self.running = False
        finally:
            logger.info("🛑 Sistema de alertas inteligentes parado")
    
    def stop(self):
        """Para o sistema"""
        self.running = False
        logger.info("⏹️ Sistema de alertas inteligentes parado")

def main():
    """Função principal"""
    print("🚀 SISTEMA INTELIGENTE DE ALERTAS GEEK - VERSÃO WINDOWS")
    print("=" * 70)
    print("🎯 Busca contínua com critérios inteligentes")
    print("📊 Análise de preços históricos")
    print("🚨 Alertas automáticos baseados em métricas")
    print("🖥️  Otimizado para Windows")
    print("=" * 70)
    
    try:
        # Cria sistema
        alert_system = IntelligentGeekAlertSystem()
        
        # Executa busca contínua
        asyncio.run(alert_system.run_continuous_search())
        
    except KeyboardInterrupt:
        print("\n⏹️ Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro no sistema: {e}")
        logger.error(f"Erro detalhado: {e}", exc_info=True)

if __name__ == "__main__":
    main()
