"""
Sistema de Recomendações ML para o Garimpeiro Geek.
Implementa algoritmos colaborativos e baseados em conteúdo.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import json
from pathlib import Path

# Importações locais
try:
    from .database import get_session, Offer, User, ProductReview
    from .price_parser import parse_price
except ImportError:
    # Para teste direto
    from database import get_session, Offer, User, ProductReview
    from price_parser import parse_price

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Motor de recomendações baseado em ML."""
    
    def __init__(self):
        self.user_profiles = {}
        self.product_embeddings = {}
        self.collaborative_filter = None
        self.content_based_filter = None
        
        # Configurações
        self.min_interactions = 3
        self.similarity_threshold = 0.3
        self.max_recommendations = 20
        
        # Cache de recomendações
        self.recommendation_cache = {}
        self.cache_ttl = timedelta(hours=1)
        
        logger.info("✅ Motor de recomendações inicializado")
    
    def train_model(self, force_retrain: bool = False) -> bool:
        """
        Treina modelo de recomendação baseado em dados históricos.
        
        Args:
            force_retrain: Forçar retreinamento mesmo se modelo recente
            
        Returns:
            bool: True se treinamento bem-sucedido
        """
        try:
            logger.info("🚀 Iniciando treinamento do modelo de recomendações...")
            
            # Carregar dados
            user_data, product_data, interaction_data = self._load_training_data()
            
            if not interaction_data:
                logger.warning("⚠️ Dados insuficientes para treinamento")
                return False
            
            # Treinar filtro colaborativo
            self.collaborative_filter = self._train_collaborative_filter(
                user_data, product_data, interaction_data
            )
            
            # Treinar filtro baseado em conteúdo
            self.content_based_filter = self._train_content_based_filter(
                product_data, interaction_data
            )
            
            # Gerar perfis de usuários
            self._generate_user_profiles(user_data, interaction_data)
            
            # Gerar embeddings de produtos
            self._generate_product_embeddings(product_data)
            
            # Salvar modelo treinado
            self._save_model()
            
            logger.info("✅ Modelo de recomendações treinado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro no treinamento: {e}")
            return False
    
    def _load_training_data(self) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Carrega dados para treinamento."""
        try:
            with get_session() as session:
                # Usuários
                users = session.query(User).filter(User.is_active == True).all()
                user_data = [
                    {
                        'id': u.id,
                        'telegram_id': u.telegram_id,
                        'username': u.username,
                        'preferred_categories': json.loads(u.preferred_categories) if u.preferred_categories else [],
                        'preferred_stores': json.loads(u.preferred_stores) if u.preferred_stores else []
                    }
                    for u in users
                ]
                
                # Produtos/Ofertas
                offers = session.query(Offer).filter(Offer.is_active == True).all()
                product_data = [
                    {
                        'id': o.id,
                        'title': o.title,
                        'category': o.category,
                        'store': o.store,
                        'brand': o.brand,
                        'price': o.price,
                        'original_price': o.original_price
                    }
                    for o in offers
                ]
                
                # Interações (reviews, visualizações)
                reviews = session.query(ProductReview).filter(ProductReview.is_verified == True).all()
                interaction_data = [
                    {
                        'user_id': r.user_id,
                        'product_id': r.offer_id,
                        'rating': r.rating,
                        'timestamp': r.created_at,
                        'type': 'review'
                    }
                    for r in reviews
                ]
                
                # Adicionar interações implícitas (baseadas em preços)
                for offer in offers:
                    if offer.price and offer.original_price:
                        discount = ((offer.original_price - offer.price) / offer.original_price) * 100
                        if discount > 20:  # Desconto significativo
                            interaction_data.append({
                                'user_id': 0,  # Usuário genérico
                                'product_id': offer.id,
                                'rating': min(5, 3 + (discount / 20)),  # Rating baseado no desconto
                                'timestamp': offer.created_at,
                                'type': 'discount'
                            })
                
                logger.info(f"📊 Dados carregados: {len(user_data)} usuários, {len(product_data)} produtos, {len(interaction_data)} interações")
                return user_data, product_data, interaction_data
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados: {e}")
            return [], [], []
    
    def _train_collaborative_filter(self, user_data: List[Dict], 
                                  product_data: List[Dict], 
                                  interaction_data: List[Dict]) -> Dict:
        """Treina filtro colaborativo baseado em usuários similares."""
        try:
            # Criar matriz de interações
            user_ids = [u['id'] for u in user_data]
            product_ids = [p['id'] for p in product_data]
            
            # Matriz de ratings
            rating_matrix = np.zeros((len(user_ids), len(product_ids)))
            
            for interaction in interaction_data:
                if interaction['user_id'] in user_ids and interaction['product_id'] in product_ids:
                    user_idx = user_ids.index(interaction['user_id'])
                    product_idx = product_ids.index(interaction['product_id'])
                    rating_matrix[user_idx, product_idx] = interaction['rating']
            
            # Calcular similaridade entre usuários (correlação de Pearson)
            user_similarity = np.corrcoef(rating_matrix)
            np.fill_diagonal(user_similarity, 0)  # Remover auto-similaridade
            
            # Normalizar similaridades
            user_similarity = np.nan_to_num(user_similarity, 0)
            
            collaborative_filter = {
                'user_ids': user_ids,
                'product_ids': product_ids,
                'rating_matrix': rating_matrix,
                'user_similarity': user_similarity,
                'trained_at': datetime.now().isoformat()
            }
            
            logger.info("✅ Filtro colaborativo treinado")
            return collaborative_filter
            
        except Exception as e:
            logger.error(f"❌ Erro no filtro colaborativo: {e}")
            return {}
    
    def _train_content_based_filter(self, product_data: List[Dict], 
                                  interaction_data: List[Dict]) -> Dict:
        """Treina filtro baseado em conteúdo dos produtos."""
        try:
            # Criar features dos produtos
            product_features = []
            
            for product in product_data:
                features = {
                    'id': product['id'],
                    'category': product.get('category', 'unknown'),
                    'store': product.get('store', 'unknown'),
                    'brand': product.get('brand', 'unknown'),
                    'price_range': self._get_price_range(product.get('price', 0)),
                    'discount_level': self._get_discount_level(
                        product.get('price', 0), 
                        product.get('original_price', 0)
                    )
                }
                product_features.append(features)
            
            # Calcular similaridade entre produtos
            product_similarity = {}
            
            for i, p1 in enumerate(product_features):
                product_similarity[p1['id']] = {}
                for j, p2 in enumerate(product_features):
                    if i != j:
                        similarity = self._calculate_product_similarity(p1, p2)
                        if similarity > self.similarity_threshold:
                            product_similarity[p1['id']][p2['id']] = similarity
            
            content_based_filter = {
                'product_features': product_features,
                'product_similarity': product_similarity,
                'trained_at': datetime.now().isoformat()
            }
            
            logger.info("✅ Filtro baseado em conteúdo treinado")
            return content_based_filter
            
        except Exception as e:
            logger.error(f"❌ Erro no filtro baseado em conteúdo: {e}")
            return {}
    
    def _get_price_range(self, price: float) -> str:
        """Categoriza preço em faixas."""
        if price <= 50:
            return 'low'
        elif price <= 200:
            return 'medium'
        elif price <= 500:
            return 'high'
        else:
            return 'premium'
    
    def _get_discount_level(self, price: float, original_price: float) -> str:
        """Categoriza nível de desconto."""
        if not original_price or original_price <= 0:
            return 'none'
        
        discount = ((original_price - price) / original_price) * 100
        
        if discount <= 10:
            return 'low'
        elif discount <= 30:
            return 'medium'
        elif discount <= 50:
            return 'high'
        else:
            return 'extreme'
    
    def _calculate_product_similarity(self, p1: Dict, p2: Dict) -> float:
        """Calcula similaridade entre dois produtos."""
        similarity = 0.0
        total_weight = 0.0
        
        # Categoria (peso alto)
        if p1['category'] == p2['category']:
            similarity += 0.4
        total_weight += 0.4
        
        # Loja (peso médio)
        if p1['store'] == p2['store']:
            similarity += 0.2
        total_weight += 0.2
        
        # Marca (peso médio)
        if p1['brand'] == p2['brand']:
            similarity += 0.2
        total_weight += 0.2
        
        # Faixa de preço (peso baixo)
        if p1['price_range'] == p2['price_range']:
            similarity += 0.1
        total_weight += 0.1
        
        # Nível de desconto (peso baixo)
        if p1['discount_level'] == p2['discount_level']:
            similarity += 0.1
        total_weight += 0.1
        
        return similarity / total_weight if total_weight > 0 else 0.0
    
    def _generate_user_profiles(self, user_data: List[Dict], interaction_data: List[Dict]):
        """Gera perfis de usuários baseados em interações."""
        try:
            for user in user_data:
                user_id = user['id']
                
                # Interações do usuário
                user_interactions = [
                    i for i in interaction_data if i['user_id'] == user_id
                ]
                
                if len(user_interactions) < self.min_interactions:
                    continue
                
                # Preferências baseadas em interações
                category_preferences = defaultdict(float)
                store_preferences = defaultdict(float)
                price_preferences = defaultdict(float)
                
                for interaction in user_interactions:
                    # Buscar dados do produto
                    product = next((p for p in self.content_based_filter.get('product_features', []) 
                                  if p['id'] == interaction['product_id']), None)
                    
                    if product:
                        weight = interaction['rating'] / 5.0
                        
                        # Categoria
                        category_preferences[product['category']] += weight
                        
                        # Loja
                        store_preferences[product['store']] += weight
                        
                        # Faixa de preço
                        price_preferences[product['price_range']] += weight
                
                # Normalizar preferências
                total_weight = sum(category_preferences.values())
                if total_weight > 0:
                    category_preferences = {k: v/total_weight for k, v in category_preferences.items()}
                
                total_weight = sum(store_preferences.values())
                if total_weight > 0:
                    store_preferences = {k: v/total_weight for k, v in store_preferences.items()}
                
                total_weight = sum(price_preferences.values())
                if total_weight > 0:
                    price_preferences = {k: v/total_weight for k, v in price_preferences.items()}
                
                # Perfil do usuário
                self.user_profiles[user_id] = {
                    'category_preferences': dict(category_preferences),
                    'store_preferences': dict(store_preferences),
                    'price_preferences': dict(price_preferences),
                    'last_updated': datetime.now().isoformat()
                }
            
            logger.info(f"✅ Perfis gerados para {len(self.user_profiles)} usuários")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar perfis: {e}")
    
    def _generate_product_embeddings(self, product_data: List[Dict]):
        """Gera embeddings vetoriais para produtos."""
        try:
            for product in product_data:
                # Embedding baseado em features categóricas
                embedding = []
                
                # Categoria (one-hot encoding simplificado)
                categories = ['electronics', 'computers', 'gaming', 'accessories', 'books', 'clothing']
                category_vector = [1.0 if product.get('category') == cat else 0.0 for cat in categories]
                embedding.extend(category_vector)
                
                # Loja (one-hot encoding simplificado)
                stores = ['amazon', 'magalu', 'shopee', 'aliexpress', 'kabum', 'terabyte']
                store_vector = [1.0 if product.get('store') == store else 0.0 for store in stores]
                embedding.extend(store_vector)
                
                # Preço normalizado (0-1)
                price = product.get('price', 0)
                normalized_price = min(1.0, price / 1000.0) if price > 0 else 0.0
                embedding.append(normalized_price)
                
                # Desconto normalizado (0-1)
                original_price = product.get('original_price', 0)
                if original_price and price:
                    discount = (original_price - price) / original_price
                    embedding.append(discount)
                else:
                    embedding.append(0.0)
                
                self.product_embeddings[product['id']] = {
                    'embedding': embedding,
                    'features': product
                }
            
            logger.info(f"✅ Embeddings gerados para {len(self.product_embeddings)} produtos")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar embeddings: {e}")
    
    def _save_model(self):
        """Salva modelo treinado em arquivo."""
        try:
            model_data = {
                'collaborative_filter': self.collaborative_filter,
                'content_based_filter': self.content_based_filter,
                'user_profiles': self.user_profiles,
                'product_embeddings': self.product_embeddings,
                'trained_at': datetime.now().isoformat()
            }
            
            # Salvar em arquivo
            model_dir = Path(".data/models")
            model_dir.mkdir(parents=True, exist_ok=True)
            
            model_file = model_dir / "recommendation_model.json"
            with open(model_file, 'w') as f:
                json.dump(model_data, f, indent=2, default=str)
            
            logger.info(f"✅ Modelo salvo em {model_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar modelo: {e}")
    
    def get_recommendations(self, user_id: int, limit: int = 10, 
                           category: Optional[str] = None) -> List[Dict]:
        """
        Retorna recomendações personalizadas para o usuário.
        
        Args:
            user_id: ID do usuário
            limit: Número máximo de recomendações
            category: Categoria específica (opcional)
            
        Returns:
            List[Dict]: Lista de produtos recomendados
        """
        try:
            # Verificar cache
            cache_key = f"{user_id}_{category or 'all'}_{limit}"
            if cache_key in self.recommendation_cache:
                cache_entry = self.recommendation_cache[cache_key]
                if datetime.now() - cache_entry['timestamp'] < self.cache_ttl:
                    logger.info(f"📋 Recomendações do cache para usuário {user_id}")
                    return cache_entry['recommendations']
            
            # Verificar se modelo está treinado
            if not self.collaborative_filter or not self.content_based_filter:
                logger.warning("⚠️ Modelo não treinado, treinando agora...")
                if not self.train_model():
                    return self._get_fallback_recommendations(limit, category)
            
            # Gerar recomendações
            recommendations = []
            
            # 1. Recomendações colaborativas
            collaborative_recs = self._get_collaborative_recommendations(user_id, limit//2)
            recommendations.extend(collaborative_recs)
            
            # 2. Recomendações baseadas em conteúdo
            content_recs = self._get_content_based_recommendations(user_id, limit//2)
            recommendations.extend(content_recs)
            
            # 3. Recomendações baseadas em popularidade (fallback)
            if len(recommendations) < limit:
                popularity_recs = self._get_popularity_recommendations(limit - len(recommendations), category)
                recommendations.extend(popularity_recs)
            
            # Filtrar por categoria se especificado
            if category:
                recommendations = [r for r in recommendations if r.get('category') == category]
            
            # Remover duplicatas e limitar
            seen_ids = set()
            unique_recommendations = []
            for rec in recommendations:
                if rec['id'] not in seen_ids and len(unique_recommendations) < limit:
                    seen_ids.add(rec['id'])
                    unique_recommendations.append(rec)
            
            # Cache das recomendações
            self.recommendation_cache[cache_key] = {
                'recommendations': unique_recommendations,
                'timestamp': datetime.now()
            }
            
            logger.info(f"✅ {len(unique_recommendations)} recomendações geradas para usuário {user_id}")
            return unique_recommendations
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar recomendações: {e}")
            return self._get_fallback_recommendations(limit, category)
    
    def _get_collaborative_recommendations(self, user_id: int, limit: int) -> List[Dict]:
        """Gera recomendações colaborativas."""
        try:
            if not self.collaborative_filter:
                return []
            
            user_ids = self.collaborative_filter['user_ids']
            if user_id not in user_ids:
                return []
            
            user_idx = user_ids.index(user_id)
            user_similarity = self.collaborative_filter['user_similarity'][user_idx]
            
            # Encontrar usuários similares
            similar_users = []
            for i, similarity in enumerate(user_similarity):
                if similarity > self.similarity_threshold and i != user_idx:
                    similar_users.append((user_ids[i], similarity))
            
            # Ordenar por similaridade
            similar_users.sort(key=lambda x: x[1], reverse=True)
            
            # Coletar produtos dos usuários similares
            product_scores = defaultdict(float)
            rating_matrix = self.collaborative_filter['rating_matrix']
            
            for similar_user_id, similarity in similar_users[:5]:  # Top 5 usuários similares
                similar_user_idx = user_ids.index(similar_user_id)
                user_ratings = rating_matrix[similar_user_idx]
                
                for product_idx, rating in enumerate(user_ratings):
                    if rating > 0:  # Produto avaliado positivamente
                        product_id = self.collaborative_filter['product_ids'][product_idx]
                        product_scores[product_id] += rating * similarity
            
            # Ordenar produtos por score
            sorted_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Retornar produtos recomendados
            recommendations = []
            for product_id, score in sorted_products[:limit]:
                product_info = self.product_embeddings.get(product_id, {}).get('features', {})
                if product_info:
                    recommendations.append({
                        'id': product_id,
                        'title': product_info.get('title', ''),
                        'category': product_info.get('category', ''),
                        'store': product_info.get('store', ''),
                        'price': product_info.get('price', 0),
                        'score': score,
                        'type': 'collaborative'
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Erro nas recomendações colaborativas: {e}")
            return []
    
    def _get_content_based_recommendations(self, user_id: int, limit: int) -> List[Dict]:
        """Gera recomendações baseadas em conteúdo."""
        try:
            if not self.content_based_filter or user_id not in self.user_profiles:
                return []
            
            user_profile = self.user_profiles[user_id]
            product_similarity = self.content_based_filter['product_similarity']
            
            # Calcular scores para produtos
            product_scores = defaultdict(float)
            
            for product_id, similarities in product_similarity.items():
                score = 0.0
                
                # Score baseado em similaridade com produtos que o usuário gosta
                for similar_product_id, similarity in similarities.items():
                    if similar_product_id in self.user_profiles.get(user_id, {}).get('liked_products', []):
                        score += similarity
                
                # Score baseado em preferências do usuário
                product_info = self.product_embeddings.get(int(product_id), {}).get('features', {})
                if product_info:
                    category = product_info.get('category', '')
                    store = product_info.get('store', '')
                    price_range = self._get_price_range(product_info.get('price', 0))
                    
                    score += user_profile['category_preferences'].get(category, 0) * 0.3
                    score += user_profile['store_preferences'].get(store, 0) * 0.2
                    score += user_profile['price_preferences'].get(price_range, 0) * 0.1
                
                if score > 0:
                    product_scores[product_id] = score
            
            # Ordenar produtos por score
            sorted_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Retornar produtos recomendados
            recommendations = []
            for product_id, score in sorted_products[:limit]:
                product_info = self.product_embeddings.get(int(product_id), {}).get('features', {})
                if product_info:
                    recommendations.append({
                        'id': int(product_id),
                        'title': product_info.get('title', ''),
                        'category': product_info.get('category', ''),
                        'store': product_info.get('store', ''),
                        'price': product_info.get('price', 0),
                        'score': score,
                        'type': 'content_based'
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Erro nas recomendações baseadas em conteúdo: {e}")
            return []
    
    def _get_popularity_recommendations(self, limit: int, category: Optional[str] = None) -> List[Dict]:
        """Gera recomendações baseadas em popularidade."""
        try:
            with get_session() as session:
                query = session.query(Offer).filter(Offer.is_active == True)
                
                if category:
                    query = query.filter(Offer.category == category)
                
                # Ordenar por desconto e data de criação
                offers = query.order_by(
                    Offer.discount_percentage.desc(),
                    Offer.created_at.desc()
                ).limit(limit).all()
                
                recommendations = []
                for offer in offers:
                    recommendations.append({
                        'id': offer.id,
                        'title': offer.title,
                        'category': offer.category,
                        'store': offer.store,
                        'price': offer.price,
                        'original_price': offer.original_price,
                        'score': offer.discount_percentage or 0,
                        'type': 'popularity'
                    })
                
                return recommendations
                
        except Exception as e:
            logger.error(f"❌ Erro nas recomendações de popularidade: {e}")
            return []
    
    def _get_fallback_recommendations(self, limit: int, category: Optional[str] = None) -> List[Dict]:
        """Recomendações de fallback quando ML falha."""
        try:
            with get_session() as session:
                query = session.query(Offer).filter(Offer.is_active == True)
                
                if category:
                    query = query.filter(Offer.category == category)
                
                offers = query.order_by(Offer.created_at.desc()).limit(limit).all()
                
                return [
                    {
                        'id': offer.id,
                        'title': offer.title,
                        'category': offer.category,
                        'store': offer.store,
                        'price': offer.price,
                        'score': 0,
                        'type': 'fallback'
                    }
                    for offer in offers
                ]
                
        except Exception as e:
            logger.error(f"❌ Erro nas recomendações de fallback: {e}")
            return []


# Instância global
recommendation_engine = RecommendationEngine()

# Funções de conveniência
def train_recommendation_model(force_retrain: bool = False) -> bool:
    """Treina modelo de recomendação."""
    return recommendation_engine.train_model(force_retrain)

def get_recommendations(user_id: int, limit: int = 10, category: Optional[str] = None) -> List[Dict]:
    """Retorna recomendações para usuário."""
    return recommendation_engine.get_recommendations(user_id, limit, category)


if __name__ == "__main__":
    print("🧪 Testando Sistema de Recomendações ML")
    print("=" * 50)
    
    # Treinar modelo
    if train_recommendation_model():
        print("✅ Modelo treinado com sucesso!")
        
        # Testar recomendações
        recommendations = get_recommendations(user_id=1, limit=5)
        print(f"📋 {len(recommendations)} recomendações geradas:")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec['title'][:50]}... (Score: {rec['score']:.2f})")
    else:
        print("❌ Falha no treinamento do modelo")
    
    print("\n✅ Teste de recomendações concluído!")
