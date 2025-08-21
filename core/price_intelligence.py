"""
Sistema de Análise Inteligente de Preços para o Garimpeiro Geek.
Detecta anomalias, prevê tendências e identifica oportunidades.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import json
from pathlib import Path
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Importações locais
try:
    from .database import get_session, Offer, PriceHistory
    from .price_parser import parse_price
except ImportError:
    # Para teste direto
    from database import get_session, Offer, PriceHistory
    from price_parser import parse_price

logger = logging.getLogger(__name__)


class PriceIntelligence:
    """Sistema inteligente de análise de preços."""
    
    def __init__(self):
        self.price_history = {}
        self.trend_analyzer = None
        self.anomaly_detector = None
        self.price_patterns = {}
        
        # Configurações
        self.min_data_points = 10
        self.anomaly_threshold = 0.95
        self.trend_confidence = 0.8
        
        # Cache de análises
        self.analysis_cache = {}
        self.cache_ttl = timedelta(hours=2)
        
        logger.info("✅ Sistema de inteligência de preços inicializado")
    
    def analyze_price_history(self, product_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Analisa histórico de preços de um produto.
        
        Args:
            product_id: ID do produto
            force_refresh: Forçar nova análise
            
        Returns:
            Dict: Análise completa do produto
        """
        try:
            # Verificar cache
            if not force_refresh and product_id in self.analysis_cache:
                cache_entry = self.analysis_cache[product_id]
                if datetime.now() - cache_entry['timestamp'] < self.cache_ttl:
                    logger.info(f"📊 Análise do cache para produto {product_id}")
                    return cache_entry['analysis']
            
            # Carregar histórico de preços
            price_data = self._load_price_history(product_id)
            
            if len(price_data) < self.min_data_points:
                logger.warning(f"⚠️ Dados insuficientes para produto {product_id}")
                return self._get_basic_analysis(product_id)
            
            # Análises
            analysis = {
                'product_id': product_id,
                'data_points': len(price_data),
                'current_price': price_data[-1]['price'] if price_data else 0,
                'price_trend': self._analyze_price_trend(price_data),
                'volatility': self._calculate_volatility(price_data),
                'anomalies': self._detect_price_anomalies(price_data),
                'seasonality': self._detect_seasonality(price_data),
                'price_prediction': self._predict_price_movement(price_data),
                'opportunity_score': self._calculate_opportunity_score(price_data),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Cache da análise
            self.analysis_cache[product_id] = {
                'analysis': analysis,
                'timestamp': datetime.now()
            }
            
            logger.info(f"✅ Análise completa para produto {product_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise do produto {product_id}: {e}")
            return self._get_basic_analysis(product_id)
    
    def _load_price_history(self, product_id: int) -> List[Dict]:
        """Carrega histórico de preços do banco."""
        try:
            with get_session() as session:
                # Buscar oferta
                offer = session.query(Offer).filter(Offer.id == product_id).first()
                if not offer:
                    return []
                
                # Buscar histórico de preços
                price_history = session.query(PriceHistory).filter(
                    PriceHistory.offer_id == product_id
                ).order_by(PriceHistory.timestamp).all()
                
                # Converter para formato padrão
                price_data = []
                
                # Adicionar preço atual
                if offer.price:
                    price_data.append({
                        'price': offer.price,
                        'original_price': offer.original_price,
                        'timestamp': offer.updated_at or offer.created_at,
                        'source': 'current'
                    })
                
                # Adicionar histórico
                for ph in price_history:
                    price_data.append({
                        'price': ph.price,
                        'original_price': ph.original_price,
                        'timestamp': ph.timestamp,
                        'source': 'history'
                    })
                
                # Ordenar por timestamp
                price_data.sort(key=lambda x: x['timestamp'])
                
                return price_data
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar histórico: {e}")
            return []
    
    def _analyze_price_trend(self, price_data: List[Dict]) -> Dict[str, Any]:
        """Analisa tendência de preços."""
        try:
            if len(price_data) < 2:
                return {'trend': 'stable', 'slope': 0, 'confidence': 0}
            
            # Extrair preços e timestamps
            prices = [p['price'] for p in price_data]
            timestamps = [p['timestamp'] for p in price_data]
            
            # Converter timestamps para números (dias desde o início)
            start_time = timestamps[0]
            time_days = [(t - start_time).days for t in timestamps]
            
            # Regressão linear
            slope, intercept, r_value, p_value, std_err = stats.linregress(time_days, prices)
            
            # Determinar tendência
            if abs(slope) < 0.01:  # Mudança menor que 1 centavo por dia
                trend = 'stable'
            elif slope > 0:
                trend = 'increasing'
            else:
                trend = 'decreasing'
            
            # Calcular confiança
            confidence = r_value ** 2
            
            return {
                'trend': trend,
                'slope': slope,
                'intercept': intercept,
                'confidence': confidence,
                'p_value': p_value,
                'r_squared': r_value ** 2
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de tendência: {e}")
            return {'trend': 'unknown', 'slope': 0, 'confidence': 0}
    
    def _calculate_volatility(self, price_data: List[Dict]) -> Dict[str, float]:
        """Calcula volatilidade dos preços."""
        try:
            prices = [p['price'] for p in price_data]
            
            if len(prices) < 2:
                return {'std': 0, 'cv': 0, 'range': 0}
            
            # Estatísticas básicas
            mean_price = np.mean(prices)
            std_price = np.std(prices)
            
            # Coeficiente de variação
            cv = (std_price / mean_price) * 100 if mean_price > 0 else 0
            
            # Range de preços
            price_range = max(prices) - min(prices)
            
            return {
                'std': std_price,
                'cv': cv,
                'range': price_range,
                'mean': mean_price
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de volatilidade: {e}")
            return {'std': 0, 'cv': 0, 'range': 0}
    
    def _detect_price_anomalies(self, price_data: List[Dict]) -> List[Dict]:
        """Detecta anomalias nos preços."""
        try:
            if len(price_data) < 5:
                return []
            
            prices = np.array([p['price'] for p in price_data]).reshape(-1, 1)
            
            # Detector de anomalias (Isolation Forest)
            iso_forest = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            
            # Treinar modelo
            iso_forest.fit(prices)
            
            # Detectar anomalias
            anomaly_scores = iso_forest.decision_function(prices)
            anomaly_predictions = iso_forest.predict(prices)
            
            # Identificar anomalias
            anomalies = []
            for i, (score, prediction) in enumerate(zip(anomaly_scores, anomaly_predictions)):
                if prediction == -1:  # Anomalia detectada
                    anomalies.append({
                        'index': i,
                        'price': price_data[i]['price'],
                        'timestamp': price_data[i]['timestamp'],
                        'anomaly_score': score,
                        'severity': 'high' if score < -0.5 else 'medium'
                    })
            
            # Ordenar por severidade
            anomalies.sort(key=lambda x: x['anomaly_score'])
            
            return anomalies
            
        except Exception as e:
            logger.error(f"❌ Erro na detecção de anomalias: {e}")
            return []
    
    def _detect_seasonality(self, price_data: List[Dict]) -> Dict[str, Any]:
        """Detecta padrões sazonais nos preços."""
        try:
            if len(price_data) < 30:  # Pelo menos 30 dias
                return {'has_seasonality': False, 'pattern': 'insufficient_data'}
            
            # Agrupar por mês
            monthly_prices = defaultdict(list)
            for price_point in price_data:
                month_key = price_point['timestamp'].strftime('%Y-%m')
                monthly_prices[month_key].append(price_point['price'])
            
            # Calcular preço médio por mês
            monthly_avg = {month: np.mean(prices) for month, prices in monthly_prices.items()}
            
            if len(monthly_avg) < 3:
                return {'has_seasonality': False, 'pattern': 'insufficient_data'}
            
            # Calcular variação entre meses
            months = sorted(monthly_avg.keys())
            month_values = [monthly_avg[month] for month in months]
            
            # Teste de sazonalidade simples (variação significativa entre meses)
            month_std = np.std(month_values)
            month_mean = np.mean(month_values)
            variation_coefficient = (month_std / month_mean) * 100 if month_mean > 0 else 0
            
            has_seasonality = variation_coefficient > 15  # Mais de 15% de variação
            
            # Identificar padrão
            if has_seasonality:
                if len(month_values) >= 12:  # Ano completo
                    # Verificar se há padrão anual
                    first_half = month_values[:6]
                    second_half = month_values[6:]
                    
                    if abs(np.mean(first_half) - np.mean(second_half)) > month_std:
                        pattern = 'annual'
                    else:
                        pattern = 'monthly'
                else:
                    pattern = 'monthly'
            else:
                pattern = 'none'
            
            return {
                'has_seasonality': has_seasonality,
                'pattern': pattern,
                'variation_coefficient': variation_coefficient,
                'monthly_averages': dict(monthly_avg)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na detecção de sazonalidade: {e}")
            return {'has_seasonality': False, 'pattern': 'error'}
    
    def _predict_price_movement(self, price_data: List[Dict]) -> Dict[str, Any]:
        """Prevê movimento futuro dos preços."""
        try:
            if len(price_data) < 10:
                return {'prediction': 'insufficient_data', 'confidence': 0}
            
            # Análise de tendência
            trend_analysis = self._analyze_price_trend(price_data)
            
            if trend_analysis['confidence'] < self.trend_confidence:
                return {'prediction': 'low_confidence', 'confidence': trend_analysis['confidence']}
            
            # Previsão simples baseada na tendência
            current_price = price_data[-1]['price']
            slope = trend_analysis['slope']
            
            # Previsão para próximos 7 dias
            days_ahead = 7
            predicted_change = slope * days_ahead
            predicted_price = current_price + predicted_change
            
            # Calcular confiança da previsão
            prediction_confidence = trend_analysis['confidence'] * 0.8  # Reduzir confiança para previsão
            
            # Determinar direção
            if abs(predicted_change) < 0.01:
                direction = 'stable'
            elif predicted_change > 0:
                direction = 'increase'
            else:
                direction = 'decrease'
            
            return {
                'prediction': direction,
                'current_price': current_price,
                'predicted_price': predicted_price,
                'predicted_change': predicted_change,
                'confidence': prediction_confidence,
                'timeframe': f'{days_ahead} days',
                'method': 'linear_trend'
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na previsão de preços: {e}")
            return {'prediction': 'error', 'confidence': 0}
    
    def _calculate_opportunity_score(self, price_data: List[Dict]) -> Dict[str, Any]:
        """Calcula score de oportunidade de compra."""
        try:
            if len(price_data) < 2:
                return {'score': 0, 'factors': [], 'recommendation': 'insufficient_data'}
            
            current_price = price_data[-1]['price']
            factors = []
            total_score = 0
            
            # 1. Desconto atual
            if 'original_price' in price_data[-1] and price_data[-1]['original_price']:
                original_price = price_data[-1]['original_price']
                discount = ((original_price - current_price) / original_price) * 100
                
                if discount > 50:
                    discount_score = 25
                    factors.append(f"Desconto extremo: {discount:.1f}%")
                elif discount > 30:
                    discount_score = 20
                    factors.append(f"Desconto alto: {discount:.1f}%")
                elif discount > 20:
                    discount_score = 15
                    factors.append(f"Desconto bom: {discount:.1f}%")
                elif discount > 10:
                    discount_score = 10
                    factors.append(f"Desconto moderado: {discount:.1f}%")
                else:
                    discount_score = 0
                    factors.append(f"Desconto baixo: {discount:.1f}%")
                
                total_score += discount_score
            
            # 2. Tendência de preços
            trend_analysis = self._analyze_price_trend(price_data)
            if trend_analysis['trend'] == 'decreasing' and trend_analysis['confidence'] > 0.7:
                trend_score = 20
                factors.append("Preços em queda")
            elif trend_analysis['trend'] == 'stable':
                trend_score = 10
                factors.append("Preços estáveis")
            else:
                trend_score = 0
                factors.append("Preços em alta")
            
            total_score += trend_score
            
            # 3. Volatilidade
            volatility = self._calculate_volatility(price_data)
            if volatility['cv'] > 20:
                volatility_score = 15
                factors.append("Alta volatilidade - oportunidade de timing")
            elif volatility['cv'] > 10:
                volatility_score = 10
                factors.append("Volatilidade moderada")
            else:
                volatility_score = 5
                factors.append("Preços estáveis")
            
            total_score += volatility_score
            
            # 4. Anomalias (oportunidades)
            anomalies = self._detect_price_anomalies(price_data)
            if anomalies:
                anomaly_score = 20
                factors.append(f"Anomalia detectada - possível oportunidade")
            else:
                anomaly_score = 0
            
            total_score += anomaly_score
            
            # 5. Histórico de preços
            min_price = min(p['price'] for p in price_data)
            max_price = max(p['price'] for p in price_data)
            
            if current_price <= min_price * 1.05:  # Dentro de 5% do preço mínimo
                history_score = 20
                factors.append("Próximo ao preço mínimo histórico")
            elif current_price <= min_price * 1.15:  # Dentro de 15% do preço mínimo
                history_score = 15
                factors.append("Próximo ao preço mínimo histórico")
            else:
                history_score = 0
            
            total_score += history_score
            
            # Normalizar score para 0-100
            final_score = min(100, total_score)
            
            # Recomendação
            if final_score >= 80:
                recommendation = "EXCELENTE oportunidade"
            elif final_score >= 60:
                recommendation = "Boa oportunidade"
            elif final_score >= 40:
                recommendation = "Oportunidade moderada"
            elif final_score >= 20:
                recommendation = "Oportunidade baixa"
            else:
                recommendation = "Não recomendado no momento"
            
            return {
                'score': final_score,
                'factors': factors,
                'recommendation': recommendation,
                'breakdown': {
                    'discount': discount_score if 'discount_score' in locals() else 0,
                    'trend': trend_score,
                    'volatility': volatility_score,
                    'anomalies': anomaly_score,
                    'history': history_score
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de oportunidade: {e}")
            return {'score': 0, 'factors': ['Erro na análise'], 'recommendation': 'error'}
    
    def _get_basic_analysis(self, product_id: int) -> Dict[str, Any]:
        """Análise básica quando dados são insuficientes."""
        return {
            'product_id': product_id,
            'data_points': 0,
            'current_price': 0,
            'price_trend': {'trend': 'unknown', 'confidence': 0},
            'volatility': {'std': 0, 'cv': 0, 'range': 0},
            'anomalies': [],
            'seasonality': {'has_seasonality': False, 'pattern': 'insufficient_data'},
            'price_prediction': {'prediction': 'insufficient_data', 'confidence': 0},
            'opportunity_score': {'score': 0, 'factors': ['Dados insuficientes'], 'recommendation': 'insufficient_data'},
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def get_price_alerts(self, min_opportunity_score: float = 70) -> List[Dict]:
        """
        Retorna alertas de preços com alta oportunidade.
        
        Args:
            min_opportunity_score: Score mínimo para alerta
            
        Returns:
            List[Dict]: Lista de alertas
        """
        try:
            alerts = []
            
            with get_session() as session:
                # Buscar ofertas ativas
                offers = session.query(Offer).filter(Offer.is_active == True).all()
                
                for offer in offers:
                    # Analisar produto
                    analysis = self.analyze_price_history(offer.id)
                    
                    if analysis['opportunity_score']['score'] >= min_opportunity_score:
                        alert = {
                            'product_id': offer.id,
                            'title': offer.title,
                            'store': offer.store,
                            'current_price': offer.price,
                            'opportunity_score': analysis['opportunity_score']['score'],
                            'recommendation': analysis['opportunity_score']['recommendation'],
                            'factors': analysis['opportunity_score']['factors'],
                            'price_trend': analysis['price_trend']['trend'],
                            'prediction': analysis['price_prediction']['prediction']
                        }
                        alerts.append(alert)
            
            # Ordenar por score de oportunidade
            alerts.sort(key=lambda x: x['opportunity_score'], reverse=True)
            
            logger.info(f"🚨 {len(alerts)} alertas de preço gerados")
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar alertas: {e}")
            return []
    
    def get_market_insights(self) -> Dict[str, Any]:
        """Retorna insights gerais do mercado."""
        try:
            insights = {
                'total_products': 0,
                'price_trends': {'increasing': 0, 'decreasing': 0, 'stable': 0},
                'opportunity_distribution': {'high': 0, 'medium': 0, 'low': 0},
                'top_categories': [],
                'top_stores': [],
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            with get_session() as session:
                offers = session.query(Offer).filter(Offer.is_active == True).all()
                insights['total_products'] = len(offers)
                
                # Analisar cada produto
                for offer in offers:
                    analysis = self.analyze_price_history(offer.id)
                    
                    # Contar tendências
                    trend = analysis['price_trend']['trend']
                    if trend in insights['price_trends']:
                        insights['price_trends'][trend] += 1
                    
                    # Contar oportunidades
                    score = analysis['opportunity_score']['score']
                    if score >= 70:
                        insights['opportunity_distribution']['high'] += 1
                    elif score >= 40:
                        insights['opportunity_distribution']['medium'] += 1
                    else:
                        insights['opportunity_distribution']['low'] += 1
            
            logger.info("📊 Insights de mercado gerados")
            return insights
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar insights: {e}")
            return {}


# Instância global
price_intelligence = PriceIntelligence()

# Funções de conveniência
def analyze_product_prices(product_id: int, force_refresh: bool = False) -> Dict[str, Any]:
    """Analisa preços de um produto."""
    return price_intelligence.analyze_price_history(product_id, force_refresh)

def get_price_alerts(min_opportunity_score: float = 70) -> List[Dict]:
    """Retorna alertas de preços."""
    return price_intelligence.get_price_alerts(min_opportunity_score)

def get_market_insights() -> Dict[str, Any]:
    """Retorna insights de mercado."""
    return price_intelligence.get_market_insights()


if __name__ == "__main__":
    print("🧪 Testando Sistema de Inteligência de Preços")
    print("=" * 50)
    
    # Testar análise de produto
    analysis = analyze_product_prices(product_id=1)
    print(f"📊 Análise do produto 1:")
    print(f"   Tendência: {analysis['price_trend']['trend']}")
    print(f"   Oportunidade: {analysis['opportunity_score']['score']}/100")
    print(f"   Recomendação: {analysis['opportunity_score']['recommendation']}")
    
    # Testar alertas
    alerts = get_price_alerts(min_opportunity_score=50)
    print(f"🚨 {len(alerts)} alertas de preço encontrados")
    
    # Testar insights
    insights = get_market_insights()
    print(f"📈 Total de produtos: {insights['total_products']}")
    
    print("\n✅ Teste de inteligência de preços concluído!")
