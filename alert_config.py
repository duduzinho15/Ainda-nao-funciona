#!/usr/bin/env python3
"""
Configuração dos Critérios de Alerta Inteligente
Personalize os parâmetros para otimizar a detecção de ofertas
"""

# ============================================================================
# 🎯 CRITÉRIOS DE ALERTA PRINCIPAIS
# ============================================================================

# Desconto mínimo para considerar uma oferta (15% = 0.15)
DISCOUNT_THRESHOLD = 0.15

# Queda de preço mínima para alerta (20% = 0.20)
PRICE_DROP_THRESHOLD = 0.20

# Comissão mínima para considerar uma oferta (10% = 0.10)
COMMISSION_THRESHOLD = 0.10

# ============================================================================
# 📊 ALERTAS DE PREÇO HISTÓRICO
# ============================================================================

# Alerta para menor preço histórico
ALERT_LOWEST_PRICE_EVER = True

# Alerta para menor preço em 3 meses
ALERT_LOWEST_PRICE_3MONTHS = True

# Alerta para menor preço em 6 meses
ALERT_LOWEST_PRICE_6MONTHS = True

# Alerta para menor preço em 1 ano
ALERT_LOWEST_PRICE_1YEAR = False

# ============================================================================
# 💎 ALERTAS DE DESCONTO EXCEPCIONAL
# ============================================================================

# Desconto excepcional (30% ou mais)
ALERT_EXCEPTIONAL_DISCOUNT = True
EXCEPTIONAL_DISCOUNT_THRESHOLD = 0.30

# Desconto alto (20% ou mais)
ALERT_HIGH_DISCOUNT = True
HIGH_DISCOUNT_THRESHOLD = 0.20

# Desconto médio (15% ou mais)
ALERT_MEDIUM_DISCOUNT = True
MEDIUM_DISCOUNT_THRESHOLD = 0.15

# ============================================================================
# ⚡ CONFIGURAÇÕES DE PERFORMANCE
# ============================================================================

# Intervalo entre buscas (em segundos)
SEARCH_INTERVAL = 300  # 5 minutos

# Número máximo de produtos por busca
MAX_PRODUCTS_PER_SEARCH = 20

# Delay entre posts de alerta (em segundos)
ALERT_POST_DELAY_MIN = 3
ALERT_POST_DELAY_MAX = 7

# Cooldown entre alertas do mesmo produto (em horas)
ALERT_COOLDOWN_HOURS = 6

# ============================================================================
# 🎮 CATEGORIAS PRIORITÁRIAS
# ============================================================================

# Categorias que recebem prioridade máxima
PRIORITY_CATEGORIES = [
    "smartphone",
    "notebook", 
    "gaming",
    "tech_accessories"
]

# Categorias com critérios mais flexíveis
FLEXIBLE_CATEGORIES = [
    "anime_manga",
    "smart_home",
    "wearables"
]

# ============================================================================
# 🏪 PLATAFORMAS E PESOS
# ============================================================================

# Peso para produtos da Shopee (maior comissão)
SHOPEE_WEIGHT = 1.0

# Peso para produtos do AliExpress
ALIEXPRESS_WEIGHT = 0.8

# Peso para produtos da Amazon
AMAZON_WEIGHT = 0.9

# Peso para produtos do MercadoLivre
MERCADOLIVRE_WEIGHT = 0.7

# ============================================================================
# 📈 MÉTRICAS DE QUALIDADE
# ============================================================================

# Avaliação mínima para considerar produto
MIN_RATING = 4.0

# Número mínimo de avaliações
MIN_REVIEWS = 10

# Preço mínimo para considerar produto
MIN_PRICE = 10.0

# Preço máximo para considerar produto (sem limite = None)
MAX_PRICE = None

# ============================================================================
# 🔍 FILTROS INTELIGENTES
# ============================================================================

# Palavras-chave que aumentam prioridade
BOOST_KEYWORDS = [
    "gamer", "gaming", "pro", "premium", "ultra", "max",
    "limited", "exclusive", "deal", "oferta", "promoção"
]

# Palavras-chave que diminuem prioridade
REDUCE_KEYWORDS = [
    "usado", "seminovo", "recondicionado", "defeito",
    "garantia", "warranty", "importado"
]

# ============================================================================
# 🚨 CONFIGURAÇÕES DE ALERTA
# ============================================================================

# Número máximo de alertas por dia
MAX_ALERTS_PER_DAY = 50

# Número máximo de alertas por hora
MAX_ALERTS_PER_HOUR = 10

# Horário de início para alertas (formato 24h)
ALERT_START_HOUR = 6  # 6:00

# Horário de fim para alertas (formato 24h)
ALERT_END_HOUR = 23   # 23:00

# ============================================================================
# 📊 CONFIGURAÇÕES DE BANCO DE DADOS
# ============================================================================

# Caminho do banco de dados de histórico
PRICE_HISTORY_DB = "price_history.db"

# Dias para manter histórico de preços
PRICE_HISTORY_DAYS = 365

# Limpeza automática de dados antigos
AUTO_CLEANUP_OLD_DATA = True

# ============================================================================
# 🔧 CONFIGURAÇÕES DE DEBUG
# ============================================================================

# Modo debug (logs mais detalhados)
DEBUG_MODE = False

# Salvar produtos analisados para debug
SAVE_ANALYZED_PRODUCTS = False

# Log de todas as decisões de alerta
LOG_ALERT_DECISIONS = True

# ============================================================================
# 📱 CONFIGURAÇÕES DO TELEGRAM
# ============================================================================

# Formato da mensagem de alerta
ALERT_MESSAGE_FORMAT = "detailed"  # "simple", "detailed", "minimal"

# Incluir estatísticas na mensagem
INCLUDE_STATS_IN_MESSAGE = True

# Incluir histórico de preços na mensagem
INCLUDE_PRICE_HISTORY = True

# Incluir comparação com concorrentes
INCLUDE_COMPETITOR_COMPARISON = False

# ============================================================================
# 🎯 FUNÇÃO PARA OBTER CONFIGURAÇÃO
# ============================================================================

def get_alert_config():
    """Retorna dicionário com todas as configurações"""
    return {
        "discount_threshold": DISCOUNT_THRESHOLD,
        "price_drop_threshold": PRICE_DROP_THRESHOLD,
        "commission_threshold": COMMISSION_THRESHOLD,
        "lowest_price_ever": ALERT_LOWEST_PRICE_EVER,
        "lowest_price_3months": ALERT_LOWEST_PRICE_3MONTHS,
        "lowest_price_6months": ALERT_LOWEST_PRICE_6MONTHS,
        "lowest_price_1year": ALERT_LOWEST_PRICE_1YEAR,
        "exceptional_discount": ALERT_EXCEPTIONAL_DISCOUNT,
        "exceptional_discount_threshold": EXCEPTIONAL_DISCOUNT_THRESHOLD,
        "high_discount": ALERT_HIGH_DISCOUNT,
        "high_discount_threshold": HIGH_DISCOUNT_THRESHOLD,
        "medium_discount": ALERT_MEDIUM_DISCOUNT,
        "medium_discount_threshold": MEDIUM_DISCOUNT_THRESHOLD,
        "search_interval": SEARCH_INTERVAL,
        "max_products_per_search": MAX_PRODUCTS_PER_SEARCH,
        "alert_post_delay_min": ALERT_POST_DELAY_MIN,
        "alert_post_delay_max": ALERT_POST_DELAY_MAX,
        "alert_cooldown_hours": ALERT_COOLDOWN_HOURS,
        "priority_categories": PRIORITY_CATEGORIES,
        "flexible_categories": FLEXIBLE_CATEGORIES,
        "platform_weights": {
            "shopee": SHOPEE_WEIGHT,
            "aliexpress": ALIEXPRESS_WEIGHT,
            "amazon": AMAZON_WEIGHT,
            "mercadolivre": MERCADOLIVRE_WEIGHT
        },
        "min_rating": MIN_RATING,
        "min_reviews": MIN_REVIEWS,
        "min_price": MIN_PRICE,
        "max_price": MAX_PRICE,
        "boost_keywords": BOOST_KEYWORDS,
        "reduce_keywords": REDUCE_KEYWORDS,
        "max_alerts_per_day": MAX_ALERTS_PER_DAY,
        "max_alerts_per_hour": MAX_ALERTS_PER_HOUR,
        "alert_start_hour": ALERT_START_HOUR,
        "alert_end_hour": ALERT_END_HOUR,
        "price_history_db": PRICE_HISTORY_DB,
        "price_history_days": PRICE_HISTORY_DAYS,
        "auto_cleanup_old_data": AUTO_CLEANUP_OLD_DATA,
        "debug_mode": DEBUG_MODE,
        "save_analyzed_products": SAVE_ANALYZED_PRODUCTS,
        "log_alert_decisions": LOG_ALERT_DECISIONS,
        "alert_message_format": ALERT_MESSAGE_FORMAT,
        "include_stats_in_message": INCLUDE_STATS_IN_MESSAGE,
        "include_price_history": INCLUDE_PRICE_HISTORY,
        "include_competitor_comparison": INCLUDE_COMPETITOR_COMPARISON
    }

def print_config_summary():
    """Imprime resumo das configurações ativas"""
    config = get_alert_config()
    
    print("🎯 CONFIGURAÇÃO DOS CRITÉRIOS DE ALERTA")
    print("=" * 50)
    print(f"📊 Desconto mínimo: {config['discount_threshold']:.0%}")
    print(f"📉 Queda de preço mínima: {config['price_drop_threshold']:.0%}")
    print(f"💰 Comissão mínima: {config['commission_threshold']:.0%}")
    print(f"⏰ Intervalo de busca: {config['search_interval']} segundos")
    print(f"🚨 Máximo de alertas por dia: {config['max_alerts_per_day']}")
    print(f"🎮 Categorias prioritárias: {', '.join(config['priority_categories'])}")
    print("=" * 50)

if __name__ == "__main__":
    print_config_summary()
