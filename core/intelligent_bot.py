"""
Bot Inteligente do Telegram para o Garimpeiro Geek.
Implementa NLP, sugestões personalizadas e comandos avançados.
"""

import logging
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Importações locais
from .database import get_session, Offer, User
from .recommendation_engine import get_recommendations
from .price_intelligence import analyze_product_prices, get_price_alerts
from .auth import UserRole, create_access_token, verify_token

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Tipos de intenção do usuário."""
    SEARCH_PRODUCTS = "search_products"
    GET_RECOMMENDATIONS = "get_recommendations"
    PRICE_ALERT = "price_alert"
    MARKET_INSIGHTS = "market_insights"
    USER_PREFERENCES = "user_preferences"
    HELP = "help"
    UNKNOWN = "unknown"


class CommandType(Enum):
    """Tipos de comando."""
    TEXT = "text"
    INLINE_QUERY = "inline_query"
    CALLBACK_QUERY = "callback_query"


@dataclass
class UserIntent:
    """Intenção detectada do usuário."""
    intent: IntentType
    confidence: float
    entities: Dict[str, Any]
    original_text: str


class NLPProcessor:
    """Processador de linguagem natural."""
    
    def __init__(self):
        # Padrões de intenção
        self.intent_patterns = {
            IntentType.SEARCH_PRODUCTS: [
                r'\b(buscar|encontrar|procurar|achar)\b.*\b(produto|oferta|item)\b',
                r'\b(preço|valor)\b.*\b(baixo|bom|ótimo)\b',
                r'\b(quero|preciso|estou procurando)\b.*\b(produto|oferta)\b',
                r'\b(desconto|promoção|oferta)\b.*\b(boa|ótima|excelente)\b'
            ],
            IntentType.GET_RECOMMENDATIONS: [
                r'\b(recomendação|sugestão|indicação)\b',
                r'\b(me recomenda|sugira|indique)\b',
                r'\b(o que|quais)\b.*\b(comprar|adquirir)\b',
                r'\b(melhor|top)\b.*\b(produto|oferta)\b'
            ],
            IntentType.PRICE_ALERT: [
                r'\b(alerta|notificação|aviso)\b.*\b(preço|valor)\b',
                r'\b(quando|quando o preço)\b.*\b(baixar|cair|diminuir)\b',
                r'\b(monitorar|acompanhar)\b.*\b(preço|valor)\b',
                r'\b(notifique|avise)\b.*\b(preço|valor)\b'
            ],
            IntentType.MARKET_INSIGHTS: [
                r'\b(mercado|tendência|análise)\b',
                r'\b(como está|estado do)\b.*\b(mercado|preços)\b',
                r'\b(insights|informações)\b.*\b(mercado|preços)\b',
                r'\b(estatísticas|dados)\b.*\b(mercado|preços)\b'
            ],
            IntentType.USER_PREFERENCES: [
                r'\b(preferência|gosto|interesse)\b',
                r'\b(categoria|loja|marca)\b.*\b(preferida|favorita)\b',
                r'\b(quero|gosto de)\b.*\b(categoria|loja|marca)\b',
                r'\b(meu perfil|minhas preferências)\b'
            ],
            IntentType.HELP: [
                r'\b(ajuda|help|socorro|como usar)\b',
                r'\b(comando|instrução|tutorial)\b',
                r'\b(o que|como)\b.*\b(fazer|usar|funciona)\b'
            ]
        }
        
        # Padrões de entidades
        self.entity_patterns = {
            'category': [
                r'\b(eletrônicos|computadores|games|acessórios|livros|roupas)\b',
                r'\b(notebook|laptop|smartphone|tablet|console)\b',
                r'\b(processador|memória|ssd|placa de vídeo)\b'
            ],
            'price_range': [
                r'\b(barato|econômico|acessível)\b',
                r'\b(caro|luxo|premium)\b',
                r'\b(abaixo de|até|máximo)\b.*\b(\d+)\b',
                r'\b(entre|de)\b.*\b(\d+)\b.*\b(e|até)\b.*\b(\d+)\b'
            ],
            'store': [
                r'\b(amazon|magalu|shopee|aliexpress|kabum|terabyte)\b',
                r'\b(loja|site|marketplace)\b'
            ],
            'brand': [
                r'\b(samsung|lg|apple|asus|msi|intel|amd)\b',
                r'\b(marca|fabricante)\b'
            ]
        }
        
        logger.info("✅ Processador NLP inicializado")
    
    def detect_intent(self, text: str) -> UserIntent:
        """
        Detecta a intenção do usuário a partir do texto.
        
        Args:
            text: Texto da mensagem
            
        Returns:
            UserIntent: Intenção detectada
        """
        try:
            text_lower = text.lower().strip()
            
            # Detectar intenção
            best_intent = IntentType.UNKNOWN
            best_confidence = 0.0
            
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, text_lower)
                    if matches:
                        confidence = len(matches) / len(patterns[intent])
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_intent = intent
            
            # Extrair entidades
            entities = self._extract_entities(text_lower)
            
            # Ajustar confiança baseado em entidades encontradas
            if entities:
                best_confidence = min(1.0, best_confidence + 0.2)
            
            return UserIntent(
                intent=best_intent,
                confidence=best_confidence,
                entities=entities,
                original_text=text
            )
            
        except Exception as e:
            logger.error(f"❌ Erro na detecção de intenção: {e}")
            return UserIntent(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities={},
                original_text=text
            )
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extrai entidades do texto."""
        entities = {}
        
        try:
            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        if entity_type not in entities:
                            entities[entity_type] = []
                        entities[entity_type].extend(matches)
            
            # Limpar e normalizar entidades
            for entity_type in entities:
                entities[entity_type] = list(set(entities[entity_type]))  # Remover duplicatas
            
        except Exception as e:
            logger.error(f"❌ Erro na extração de entidades: {e}")
        
        return entities


class IntelligentBot:
    """Bot inteligente com capacidades avançadas."""
    
    def __init__(self):
        self.nlp_processor = NLPProcessor()
        self.intent_classifier = None
        self.command_handlers = {}
        self._setup_command_handlers()
        
        logger.info("✅ Bot inteligente inicializado")
    
    def _setup_command_handlers(self):
        """Configura handlers de comandos."""
        self.command_handlers = {
            IntentType.SEARCH_PRODUCTS: self._handle_product_search,
            IntentType.GET_RECOMMENDATIONS: self._handle_recommendations,
            IntentType.PRICE_ALERT: self._handle_price_alert,
            IntentType.MARKET_INSIGHTS: self._handle_market_insights,
            IntentType.USER_PREFERENCES: self._handle_user_preferences,
            IntentType.HELP: self._handle_help,
            IntentType.UNKNOWN: self._handle_unknown
        }
    
    async def handle_natural_language(self, message: str, user_id: int) -> str:
        """
        Processa linguagem natural e responde inteligentemente.
        
        Args:
            message: Mensagem do usuário
            user_id: ID do usuário
            
        Returns:
            str: Resposta do bot
        """
        try:
            # Detectar intenção
            intent = self.nlp_processor.detect_intent(message)
            
            logger.info(f"🧠 Intenção detectada: {intent.intent.value} (confiança: {intent.confidence:.2f})")
            
            # Verificar confiança mínima
            if intent.confidence < 0.3:
                return self._generate_low_confidence_response(message)
            
            # Processar com handler apropriado
            handler = self.command_handlers.get(intent.intent, self._handle_unknown)
            response = await handler(message, user_id, intent)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento de linguagem natural: {e}")
            return "Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?"
    
    async def _handle_product_search(self, message: str, user_id: int, intent: UserIntent) -> str:
        """Handler para busca de produtos."""
        try:
            # Extrair critérios de busca
            category = intent.entities.get('category', [None])[0]
            price_range = intent.entities.get('price_range', [None])[0]
            store = intent.entities.get('store', [None])[0]
            brand = intent.entities.get('brand', [None])[0]
            
            # Buscar produtos
            with get_session() as session:
                query = session.query(Offer).filter(Offer.is_active == True)
                
                if category:
                    query = query.filter(Offer.category.ilike(f'%{category}%'))
                
                if store:
                    query = query.filter(Offer.store.ilike(f'%{store}%'))
                
                if brand:
                    query = query.filter(Offer.brand.ilike(f'%{brand}%'))
                
                # Ordenar por desconto
                offers = query.order_by(Offer.discount_percentage.desc()).limit(5).all()
            
            if not offers:
                return "Não encontrei produtos com esses critérios. Tente ser mais específico ou usar outras palavras-chave."
            
            # Formatar resposta
            response = "🔍 **Produtos encontrados:**\n\n"
            
            for i, offer in enumerate(offers, 1):
                discount = ""
                if offer.original_price and offer.price:
                    discount_pct = ((offer.original_price - offer.price) / offer.original_price) * 100
                    discount = f" (💰 {discount_pct:.1f}% OFF)"
                
                response += f"{i}. **{offer.title[:50]}...**\n"
                response += f"   🏪 {offer.store} | 💵 R$ {offer.price:.2f}{discount}\n"
                response += f"   📍 {offer.category or 'N/A'}\n\n"
            
            response += "💡 *Use /recomendacoes para sugestões personalizadas*"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro na busca de produtos: {e}")
            return "Desculpe, tive um problema na busca. Pode tentar novamente?"
    
    async def _handle_recommendations(self, message: str, user_id: int, intent: UserIntent) -> str:
        """Handler para recomendações."""
        try:
            # Extrair categoria se especificada
            category = None
            if intent.entities.get('category'):
                category = intent.entities.get('category')[0]
            
            # Obter recomendações
            recommendations = get_recommendations(user_id=user_id, limit=5, category=category)
            
            if not recommendations:
                return "Não tenho recomendações para você no momento. Tente usar /buscar para encontrar produtos específicos."
            
            # Formatar resposta
            response = "🎯 **Recomendações personalizadas para você:**\n\n"
            
            for i, rec in enumerate(recommendations, 1):
                response += f"{i}. **{rec['title'][:50]}...**\n"
                response += f"   🏪 {rec['store']} | 💵 R$ {rec['price']:.2f}\n"
                response += f"   📍 {rec['category'] or 'N/A'} | ⭐ Score: {rec['score']:.1f}\n"
                response += f"   🧠 Tipo: {rec['type']}\n\n"
            
            response += "💡 *As recomendações são baseadas no seu perfil e histórico*"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro nas recomendações: {e}")
            return "Desculpe, tive um problema ao gerar recomendações. Pode tentar novamente?"
    
    async def _handle_price_alert(self, message: str, user_id: int, intent: UserIntent) -> str:
        """Handler para alertas de preço."""
        try:
            # Obter alertas de preço
            alerts = get_price_alerts(min_opportunity_score=70)
            
            if not alerts:
                return "Não há alertas de preço ativos no momento. Os produtos estão com preços estáveis."
            
            # Formatar resposta
            response = "🚨 **Alertas de Preço - Oportunidades Quentes:**\n\n"
            
            for i, alert in enumerate(alerts[:5], 1):
                response += f"{i}. **{alert['title'][:50]}...**\n"
                response += f"   🏪 {alert['store']} | 💵 R$ {alert['current_price']:.2f}\n"
                response += f"   ⭐ Oportunidade: {alert['opportunity_score']}/100\n"
                response += f"   📈 Tendência: {alert['price_trend']}\n"
                response += f"   🔮 Previsão: {alert['prediction']}\n\n"
            
            response += "💡 *Use /analisar [produto] para análise detalhada*"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro nos alertas de preço: {e}")
            return "Desculpe, tive um problema ao gerar alertas. Pode tentar novamente?"
    
    async def _handle_market_insights(self, message: str, user_id: int, intent: UserIntent) -> str:
        """Handler para insights de mercado."""
        try:
            # Obter insights
            insights = get_market_insights()
            
            if not insights or insights['total_products'] == 0:
                return "Não tenho dados suficientes para gerar insights de mercado no momento."
            
            # Formatar resposta
            response = "📊 **Insights do Mercado:**\n\n"
            
            response += f"📦 **Total de Produtos:** {insights['total_products']}\n\n"
            
            response += "📈 **Tendências de Preço:**\n"
            for trend, count in insights['price_trends'].items():
                if count > 0:
                    response += f"   • {trend.title()}: {count} produtos\n"
            
            response += "\n🎯 **Distribuição de Oportunidades:**\n"
            for level, count in insights['opportunity_distribution'].items():
                if count > 0:
                    response += f"   • {level.title()}: {count} produtos\n"
            
            response += f"\n⏰ *Atualizado em: {insights['analysis_timestamp']}*"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro nos insights de mercado: {e}")
            return "Desculpe, tive um problema ao gerar insights. Pode tentar novamente?"
    
    async def _handle_user_preferences(self, message: str, user_id: int, intent: UserIntent) -> str:
        """Handler para preferências do usuário."""
        try:
            with get_session() as session:
                user = session.query(User).filter(User.telegram_id == user_id).first()
                
                if not user:
                    return "Você ainda não tem um perfil configurado. Use /perfil para criar um."
                
                # Formatar resposta
                response = "👤 **Seu Perfil:**\n\n"
                
                response += f"🆔 **ID:** {user.telegram_id}\n"
                response += f"👤 **Nome:** {user.first_name or 'N/A'}\n"
                response += f"📱 **Username:** @{user.username or 'N/A'}\n"
                response += f"🔔 **Notificações:** {'Ativadas' if user.notification_enabled else 'Desativadas'}\n"
                response += f"⭐ **Plano:** {'Premium' if user.is_premium else 'Básico'}\n"
                response += f"📅 **Membro desde:** {user.created_at.strftime('%d/%m/%Y')}\n"
                response += f"🕒 **Última atividade:** {user.last_activity.strftime('%d/%m/%Y %H:%M')}\n\n"
                
                # Preferências
                if user.preferred_categories:
                    try:
                        categories = json.loads(user.preferred_categories)
                        if categories:
                            response += "📂 **Categorias Preferidas:**\n"
                            for cat in categories[:5]:
                                response += f"   • {cat}\n"
                            response += "\n"
                    except:
                        pass
                
                if user.preferred_stores:
                    try:
                        stores = json.loads(user.preferred_stores)
                        if stores:
                            response += "🏪 **Lojas Preferidas:**\n"
                            for store in stores[:5]:
                                response += f"   • {store}\n"
                            response += "\n"
                    except:
                        pass
                
                response += "💡 *Use /configurar para alterar suas preferências*"
                
                return response
                
        except Exception as e:
            logger.error(f"❌ Erro nas preferências do usuário: {e}")
            return "Desculpe, tive um problema ao carregar seu perfil. Pode tentar novamente?"
    
    async def _handle_help(self, message: str, user_id: int, intent: UserIntent) -> str:
        """Handler para ajuda."""
        response = """🤖 **Garimpeiro Geek - Bot Inteligente**

**Comandos Principais:**
• /start - Iniciar o bot
• /buscar [produto] - Buscar produtos específicos
• /recomendacoes - Sugestões personalizadas
• /alertas - Alertas de preço
• /mercado - Insights de mercado
• /perfil - Seu perfil e preferências
• /ajuda - Esta mensagem

**Como Usar:**
Você pode digitar naturalmente! Por exemplo:
• "Quero um notebook barato"
• "Me recomenda produtos de gaming"
• "Como está o mercado de eletrônicos?"
• "Quero monitorar preços de smartphones"

**Recursos Inteligentes:**
🧠 **NLP Avançado** - Entende linguagem natural
🎯 **Recomendações ML** - Baseadas no seu perfil
📊 **Análise de Preços** - Detecta oportunidades
🚨 **Alertas Inteligentes** - Notifica melhores momentos
📈 **Insights de Mercado** - Tendências e estatísticas

**Precisa de mais ajuda?**
Digite sua dúvida ou use /ajuda [tópico] para ajuda específica."""

        return response
    
    async def _handle_unknown(self, message: str, user_id: int, intent: UserIntent) -> str:
        """Handler para intenções desconhecidas."""
        response = f"""🤔 **Não entendi exatamente o que você quer...**

**Sua mensagem:** "{message}"

**Tente ser mais específico ou use um destes comandos:**

🔍 **Para buscar produtos:**
• "Quero um notebook"
• "Buscar smartphones baratos"
• "Produtos de gaming com desconto"

🎯 **Para recomendações:**
• "Me recomenda algo"
• "O que comprar agora?"
• "Sugestões para mim"

📊 **Para informações:**
• "Como está o mercado?"
• "Tendências de preços"
• "Estatísticas de produtos"

💡 **Dica:** Quanto mais específico você for, melhor posso te ajudar!"""

        return response
    
    def _generate_low_confidence_response(self, message: str) -> str:
        """Gera resposta para mensagens com baixa confiança."""
        return f"""🤷 **Não tenho certeza do que você quer...**

**Sua mensagem:** "{message}"

**Possíveis interpretações:**
• Você quer buscar produtos?
• Precisa de recomendações?
• Quer informações sobre o mercado?
• Precisa de ajuda?

**Sugestões:**
• Reformule sua mensagem de forma mais clara
• Use comandos específicos como /buscar, /recomendacoes
• Ou digite sua dúvida de outra forma

**Exemplos que funcionam bem:**
• "Quero um notebook barato"
• "Me recomenda produtos de gaming"
• "Como está o mercado de eletrônicos?""""

    async def suggest_products(self, user_query: str, user_id: int) -> List[Dict]:
        """
        Sugere produtos baseado na consulta do usuário.
        
        Args:
            user_query: Consulta do usuário
            user_id: ID do usuário
            
        Returns:
            List[Dict]: Lista de produtos sugeridos
        """
        try:
            # Detectar intenção
            intent = self.nlp_processor.detect_intent(user_query)
            
            # Se for busca de produtos, usar busca
            if intent.intent == IntentType.SEARCH_PRODUCTS:
                return await self._search_products_for_suggestion(user_query, intent)
            
            # Se for recomendações, usar engine de ML
            elif intent.intent == IntentType.GET_RECOMMENDATIONS:
                category = intent.entities.get('category', [None])[0]
                return get_recommendations(user_id=user_id, limit=10, category=category)
            
            # Caso padrão: buscar produtos relevantes
            else:
                return await self._search_products_for_suggestion(user_query, intent)
                
        except Exception as e:
            logger.error(f"❌ Erro ao sugerir produtos: {e}")
            return []
    
    async def _search_products_for_suggestion(self, query: str, intent: UserIntent) -> List[Dict]:
        """Busca produtos para sugestão."""
        try:
            with get_session() as session:
                # Construir query
                db_query = session.query(Offer).filter(Offer.is_active == True)
                
                # Filtrar por categoria se especificada
                if intent.entities.get('category'):
                    category = intent.entities.get('category')[0]
                    db_query = db_query.filter(Offer.category.ilike(f'%{category}%'))
                
                # Filtrar por loja se especificada
                if intent.entities.get('store'):
                    store = intent.entities.get('store')[0]
                    db_query = db_query.filter(Offer.store.ilike(f'%{store}%'))
                
                # Filtrar por marca se especificada
                if intent.entities.get('brand'):
                    brand = intent.entities.get('brand')[0]
                    db_query = db_query.filter(Offer.brand.ilike(f'%{brand}%'))
                
                # Buscar produtos
                offers = db_query.order_by(
                    Offer.discount_percentage.desc(),
                    Offer.created_at.desc()
                ).limit(10).all()
                
                # Converter para formato padrão
                suggestions = []
                for offer in offers:
                    suggestions.append({
                        'id': offer.id,
                        'title': offer.title,
                        'category': offer.category,
                        'store': offer.store,
                        'price': offer.price,
                        'original_price': offer.original_price,
                        'score': offer.discount_percentage or 0,
                        'type': 'search_result'
                    })
                
                return suggestions
                
        except Exception as e:
            logger.error(f"❌ Erro na busca para sugestão: {e}")
            return []


# Instância global
intelligent_bot = IntelligentBot()

# Funções de conveniência
async def handle_natural_language(message: str, user_id: int) -> str:
    """Processa linguagem natural e responde."""
    return await intelligent_bot.handle_natural_language(message, user_id)

async def suggest_products(user_query: str, user_id: int) -> List[Dict]:
    """Sugere produtos baseado na consulta."""
    return await intelligent_bot.suggest_products(user_query, user_id)


if __name__ == "__main__":
    print("🧪 Testando Bot Inteligente")
    print("=" * 50)
    
    # Testar detecção de intenção
    nlp = NLPProcessor()
    
    test_messages = [
        "Quero um notebook barato",
        "Me recomenda produtos de gaming",
        "Como está o mercado de eletrônicos?",
        "Quero monitorar preços de smartphones"
    ]
    
    for message in test_messages:
        intent = nlp.detect_intent(message)
        print(f"'{message}' -> {intent.intent.value} (confiança: {intent.confidence:.2f})")
        if intent.entities:
            print(f"  Entidades: {intent.entities}")
    
    print("\n✅ Teste do bot inteligente concluído!")
