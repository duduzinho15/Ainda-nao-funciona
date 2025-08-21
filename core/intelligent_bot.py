"""
Bot inteligente com capacidades de NLP para o Garimpeiro Geek.
Implementa processamento de linguagem natural para entender intenções do usuário.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

# Imports locais
try:
    from .database import get_session, Offer
    from .recommendation_engine import get_recommendations
except ImportError:
    # Para teste direto
    from database import get_session, Offer
    from recommendation_engine import get_recommendations

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Tipos de intenção do usuário."""
    SEARCH_PRODUCTS = "search_products"
    GET_RECOMMENDATIONS = "get_recommendations"
    SET_PRICE_ALERT = "set_price_alert"
    GET_MARKET_INSIGHTS = "get_market_insights"
    SET_PREFERENCES = "set_preferences"
    GET_HELP = "get_help"
    UNKNOWN = "unknown"

class CommandType(Enum):
    """Tipos de comando."""
    SEARCH = "search"
    RECOMMEND = "recommend"
    ALERT = "alert"
    INSIGHTS = "insights"
    PREFERENCES = "preferences"
    HELP = "help"

@dataclass
class UserIntent:
    """Representa a intenção detectada do usuário."""
    intent: IntentType
    confidence: float
    entities: Dict[str, List[str]]
    raw_text: str

class NLPProcessor:
    """Processador de linguagem natural para detectar intenções."""
    
    def __init__(self):
        # Padrões para detecção de intenções
        self.patterns = {
            IntentType.SEARCH_PRODUCTS: [
                r"quero\s+(?:um|uma|uns|umas)?\s+([^,]+)",
                r"procuro\s+(?:um|uma|uns|umas)?\s+([^,]+)",
                r"busco\s+(?:um|uma|uns|umas)?\s+([^,]+)",
                r"preciso\s+(?:de\s+)?(?:um|uma|uns|umas)?\s+([^,]+)",
                r"([^,]+)\s+(?:barato|barata|econômico|econômica)",
                r"([^,]+)\s+(?:com\s+)?(?:desconto|promoção|oferta)",
            ],
            IntentType.GET_RECOMMENDATIONS: [
                r"(?:me\s+)?recomenda(?:r|ndo)?\s+([^,]+)",
                r"(?:quero\s+)?(?:sugestões|recomendações)\s+(?:de|para)\s+([^,]+)",
                r"(?:me\s+)?sugira\s+([^,]+)",
                r"(?:quero\s+)?(?:ideias|opções)\s+(?:de|para)\s+([^,]+)",
            ],
            IntentType.SET_PRICE_ALERT: [
                r"(?:quero\s+)?(?:monitorar|acompanhar)\s+(?:preços\s+)?(?:de\s+)?([^,]+)",
                r"(?:me\s+)?avise\s+(?:quando|se)\s+(?:o\s+)?(?:preço\s+)?(?:de\s+)?([^,]+)",
                r"(?:quero\s+)?(?:alerta|notificação)\s+(?:de\s+)?(?:preço\s+)?(?:para\s+)?([^,]+)",
            ],
            IntentType.GET_MARKET_INSIGHTS: [
                r"(?:como\s+)?(?:está\s+)?(?:o\s+)?(?:mercado|preços)\s+(?:de\s+)?([^,]+)",
                r"(?:quero\s+)?(?:saber|conhecer)\s+(?:sobre\s+)?(?:o\s+)?(?:mercado\s+)?(?:de\s+)?([^,]+)",
                r"(?:me\s+)?(?:informe|diga)\s+(?:sobre\s+)?(?:o\s+)?(?:mercado\s+)?(?:de\s+)?([^,]+)",
            ],
            IntentType.SET_PREFERENCES: [
                r"(?:quero\s+)?(?:definir|configurar|ajustar)\s+(?:minhas\s+)?(?:preferências|configurações)",
                r"(?:meus\s+)?(?:gostos|interesses|preferências)",
                r"(?:quero\s+)?(?:personalizar|customizar)\s+(?:minhas\s+)?(?:recomendações)",
            ],
            IntentType.GET_HELP: [
                r"(?:preciso\s+)?(?:de\s+)?(?:ajuda|socorro)",
                r"(?:como\s+)?(?:funciona|uso|faço)",
                r"(?:quais\s+)?(?:são\s+)?(?:os\s+)?(?:comandos|opções)",
                r"(?:me\s+)?(?:explique|ensine|mostre)",
            ]
        }
        
        # Categorias conhecidas
        self.categories = [
            "notebook", "laptop", "computador", "pc", "desktop",
            "smartphone", "celular", "telefone", "iphone", "android",
            "monitor", "tela", "display", "tv", "televisão",
            "fone", "headphone", "headset", "earphone", "airpods",
            "mouse", "teclado", "keyboard", "webcam", "câmera",
            "gaming", "jogos", "console", "playstation", "xbox",
            "eletrônicos", "tecnologia", "gadgets", "acessórios"
        ]
        
        # Lojas conhecidas
        self.stores = [
            "amazon", "mercadolivre", "magalu", "americanas", "submarino",
            "kabum", "terabyteshop", "pichau", "casas bahia", "extra",
            "ricardo eletro", "fast shop", "saraiva", "livraria cultura"
        ]
        
        # Marcas conhecidas
        self.brands = [
            "apple", "samsung", "lg", "sony", "asus", "acer", "lenovo",
            "dell", "hp", "msi", "gigabyte", "corsair", "logitech",
            "razer", "steelseries", "hyperx", "jbl", "bose", "sennheiser"
        ]
    
    def detect_intent(self, text: str) -> UserIntent:
        """
        Detecta a intenção do usuário baseado no texto.
        
        Args:
            text: Texto do usuário
            
        Returns:
            UserIntent: Intenção detectada
        """
        text = text.lower().strip()
        
        # Detectar intenção principal
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        best_entities = {}
        
        for intent_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    confidence = self._calculate_confidence(text, pattern, matches)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent_type
                        best_entities = self._extract_entities(text, matches)
        
        # Se não encontrou padrão específico, tentar inferir
        if best_intent == IntentType.UNKNOWN:
            best_intent, best_confidence = self._infer_intent(text)
            best_entities = self._extract_entities(text, [])
        
        return UserIntent(
            intent=best_intent,
            confidence=best_confidence,
            entities=best_entities,
            raw_text=text
        )
    
    def _calculate_confidence(self, text: str, pattern: str, matches: List[str]) -> float:
        """Calcula a confiança da detecção."""
        # Base: 0.5
        confidence = 0.5
        
        # Bônus por ter palavras-chave específicas
        if any(word in text for word in ["quero", "preciso", "procuro", "busco"]):
            confidence += 0.2
        
        # Bônus por ter entidades específicas
        if any(cat in text for cat in self.categories):
            confidence += 0.2
        
        # Bônus por ter lojas ou marcas
        if any(store in text for store in self.stores):
            confidence += 0.1
        
        if any(brand in text for brand in self.brands):
            confidence += 0.1
        
        # Limitar a 1.0
        return min(confidence, 1.0)
    
    def _extract_entities(self, text: str, matches: List[str]) -> Dict[str, List[str]]:
        """Extrai entidades do texto."""
        entities = {}
        
        # Categorias
        found_categories = []
        for category in self.categories:
            if category in text:
                found_categories.append(category)
        if found_categories:
            entities['category'] = found_categories
        
        # Lojas
        found_stores = []
        for store in self.stores:
            if store in text:
                found_stores.append(store)
        if found_stores:
            entities['store'] = found_stores
        
        # Marcas
        found_brands = []
        for brand in self.brands:
            if brand in text:
                found_brands.append(brand)
        if found_brands:
            entities['brand'] = found_brands
        
        # Produtos específicos das matches
        if matches:
            entities['product'] = [match.strip() for match in matches if match.strip()]
        
        return entities
    
    def _infer_intent(self, text: str) -> Tuple[IntentType, float]:
        """Inferência de intenção quando não há padrão específico."""
        # Palavras que sugerem busca
        search_words = ["produto", "item", "coisa", "objeto", "artigo"]
        if any(word in text for word in search_words):
            return IntentType.SEARCH_PRODUCTS, 0.3
        
        # Palavras que sugerem ajuda
        help_words = ["ajuda", "socorro", "problema", "dúvida", "questão"]
        if any(word in text for word in help_words):
            return IntentType.GET_HELP, 0.4
        
        # Padrão: busca genérica
        return IntentType.SEARCH_PRODUCTS, 0.2

class IntelligentBot:
    """Bot inteligente principal."""
    
    def __init__(self):
        self.nlp_processor = NLPProcessor()
        logger.info("🤖 Bot inteligente inicializado")
    
    async def handle_natural_language(self, message: str, user_id: int) -> str:
        """
        Processa mensagem em linguagem natural e responde.
        
        Args:
            message: Mensagem do usuário
            user_id: ID do usuário
            
        Returns:
            str: Resposta do bot
        """
        try:
            # Detectar intenção
            intent = self.nlp_processor.detect_intent(message)
            
            # Processar baseado na intenção
            if intent.intent == IntentType.SEARCH_PRODUCTS:
                return await self._handle_product_search(intent, user_id)
            
            elif intent.intent == IntentType.GET_RECOMMENDATIONS:
                return await self._handle_recommendations(intent, user_id)
            
            elif intent.intent == IntentType.SET_PRICE_ALERT:
                return await self._handle_price_alert(intent, user_id)
            
            elif intent.intent == IntentType.GET_MARKET_INSIGHTS:
                return await self._handle_market_insights(intent, user_id)
            
            elif intent.intent == IntentType.SET_PREFERENCES:
                return await self._handle_preferences(intent, user_id)
            
            elif intent.intent == IntentType.GET_HELP:
                return await self._handle_help(intent, user_id)
            
            else:
                return await self._handle_unknown(intent, user_id)
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {e}")
            return "Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?"
    
    async def _handle_product_search(self, intent: UserIntent, user_id: int) -> str:
        """Processa busca de produtos."""
        try:
            # Buscar produtos
            products = await self._search_products_for_suggestion(intent.raw_text, intent)
            
            if not products:
                return "Não encontrei produtos que correspondam à sua busca. Pode tentar com outras palavras?"
            
            # Formatar resposta
            response = "🔍 Encontrei estes produtos para você:\n\n"
            
            for i, product in enumerate(products[:5], 1):
                price = f"R$ {product['price']:.2f}" if product['price'] else "Preço não disponível"
                discount = f" ({product['score']:.0f}% OFF)" if product['score'] > 0 else ""
                
                response += f"{i}. **{product['title']}**\n"
                response += f"   💰 {price}{discount}\n"
                response += f"   🏪 {product['store']}\n"
                response += f"   📂 {product['category']}\n\n"
            
            if len(products) > 5:
                response += f"_... e mais {len(products) - 5} produtos encontrados._"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro na busca de produtos: {e}")
            return "Desculpe, tive um problema ao buscar produtos. Pode tentar novamente?"
    
    async def _handle_recommendations(self, intent: UserIntent, user_id: int) -> str:
        """Processa pedidos de recomendações."""
        try:
            # Obter recomendações
            recommendations = get_recommendations(user_id=user_id, limit=5)
            
            if not recommendations:
                return "Ainda não tenho recomendações personalizadas para você. Continue usando o sistema para que eu aprenda seus gostos!"
            
            # Formatar resposta
            response = "🎯 Aqui estão minhas recomendações para você:\n\n"
            
            for i, rec in enumerate(recommendations, 1):
                response += f"{i}. **{rec['title']}**\n"
                response += f"   💰 R$ {rec['price']:.2f}\n"
                response += f"   🏪 {rec['store']}\n"
                response += f"   ⭐ Score: {rec['score']:.1f}\n\n"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro nas recomendações: {e}")
            return "Desculpe, tive um problema ao gerar recomendações. Pode tentar novamente?"
    
    async def _handle_price_alert(self, intent: UserIntent, user_id: int) -> str:
        """Processa configuração de alertas de preço."""
        try:
            # Extrair produto do intent
            product = intent.entities.get('product', ['produto'])[0]
            
            # TODO: Implementar sistema de alertas
            response = f"🔔 Entendi! Você quer monitorar preços de **{product}**.\n\n"
            response += "Esta funcionalidade será implementada em breve. "
            response += "Por enquanto, você pode usar a busca de produtos para acompanhar preços manualmente."
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro no alerta de preço: {e}")
            return "Desculpe, tive um problema ao configurar o alerta. Pode tentar novamente?"
    
    async def _handle_market_insights(self, intent: UserIntent, user_id: int) -> str:
        """Processa pedidos de insights de mercado."""
        try:
            # Extrair categoria do intent
            category = intent.entities.get('category', ['eletrônicos'])[0]
            
            # TODO: Implementar análise de mercado
            response = f"📊 Você quer saber sobre o mercado de **{category}**!\n\n"
            response += "Esta funcionalidade será implementada em breve. "
            response += "Por enquanto, você pode usar a busca de produtos para ver as ofertas atuais."
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro nos insights de mercado: {e}")
            return "Desculpe, tive um problema ao gerar insights. Pode tentar novamente?"
    
    async def _handle_preferences(self, intent: UserIntent, user_id: int) -> str:
        """Processa configuração de preferências."""
        try:
            response = "⚙️ Configuração de preferências!\n\n"
            response += "Para personalizar suas recomendações, você pode:\n"
            response += "• Usar comandos específicos como '/preferences'\n"
            response += "• Responder perguntas sobre seus interesses\n"
            response += "• Ajustar configurações no dashboard\n\n"
            response += "Esta funcionalidade será implementada em breve!"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro nas preferências: {e}")
            return "Desculpe, tive um problema com as preferências. Pode tentar novamente?"
    
    async def _handle_help(self, intent: UserIntent, user_id: int) -> str:
        """Processa pedidos de ajuda."""
        try:
            response = "🤖 **Como posso te ajudar?**\n\n"
            response += "**🔍 Buscar produtos:**\n"
            response += "• 'Quero um notebook barato'\n"
            response += "• 'Procuro smartphone com desconto'\n"
            response += "• 'Preciso de monitor gaming'\n\n"
            
            response += "**🎯 Recomendações:**\n"
            response += "• 'Me recomenda produtos de gaming'\n"
            response += "• 'Sugestões para eletrônicos'\n\n"
            
            response += "**🔔 Alertas de preço:**\n"
            response += "• 'Quero monitorar preços de smartphones'\n"
            response += "• 'Me avise quando o preço baixar'\n\n"
            
            response += "**📊 Insights de mercado:**\n"
            response += "• 'Como está o mercado de notebooks?'\n"
            response += "• 'Quero saber sobre preços de eletrônicos'\n\n"
            
            response += "**⚙️ Preferências:**\n"
            response += "• 'Quero personalizar minhas recomendações'\n"
            response += "• 'Configurar meus interesses'\n\n"
            
            response += "💡 **Dica:** Quanto mais específico você for, melhor posso te ajudar!"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro na ajuda: {e}")
            return "Desculpe, tive um problema ao mostrar a ajuda. Pode tentar novamente?"
    
    async def _handle_unknown(self, intent: UserIntent, user_id: int) -> str:
        """Processa intenções desconhecidas."""
        try:
            response = "🤔 Não entendi exatamente o que você quer.\n\n"
            response += "Você pode:\n"
            response += "• Tentar ser mais específico\n"
            response += "• Usar frases como 'quero um notebook' ou 'me recomenda produtos'\n"
            response += "• Digitar '/help' para ver todas as opções\n\n"
            response += "💡 **Exemplos que funcionam bem:**\n"
            response += "• 'Quero um notebook barato'\n"
            response += "• 'Me recomenda produtos de gaming'\n"
            response += "• 'Como está o mercado de eletrônicos?'"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro no tratamento de intenção desconhecida: {e}")
            return "Desculpe, tive um problema. Pode tentar novamente ou digitar '/help'?"

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
