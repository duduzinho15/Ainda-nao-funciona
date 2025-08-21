"""
API RESTful para o Garimpeiro Geek.
Implementa endpoints para todas as funcionalidades do sistema.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Importações locais
from core.database import get_session, Offer, User, PriceHistory
from core.recommendation_engine import get_recommendations
from core.price_intelligence import analyze_product_prices, get_price_alerts, get_market_insights
from core.auth import verify_token, UserClaims, UserRole
from core.scrapers_config import get_all_sources, get_enabled_sources

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da API
app = FastAPI(
    title="Garimpeiro Geek API",
    description="API para sistema de recomendações de ofertas",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar apropriadamente para produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Segurança
security = HTTPBearer()

# Modelos Pydantic
class OfferResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    price: float
    original_price: Optional[float]
    discount_percentage: Optional[float]
    store: str
    category: Optional[str]
    brand: Optional[str]
    product_url: Optional[str]
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime

class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    is_premium: bool
    created_at: datetime
    last_activity: datetime

class RecommendationRequest(BaseModel):
    user_id: int
    limit: int = Field(default=10, ge=1, le=50)
    category: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    store: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    limit: int = Field(default=20, ge=1, le=100)

class PriceAnalysisResponse(BaseModel):
    product_id: int
    data_points: int
    current_price: float
    price_trend: Dict[str, Any]
    volatility: Dict[str, float]
    anomalies: List[Dict[str, Any]]
    opportunity_score: Dict[str, Any]
    analysis_timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    database: str
    services: Dict[str, str]

# Dependências
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserClaims:
    """Verifica token e retorna usuário atual."""
    try:
        token = credentials.credentials
        user_claims = verify_token(token)
        
        if not user_claims:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado"
            )
        
        return user_claims
        
    except Exception as e:
        logger.error(f"Erro na autenticação: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erro na autenticação"
        )

def require_role(required_role: UserRole):
    """Decorator para verificar role do usuário."""
    def decorator(user: UserClaims = Depends(get_current_user)):
        if user.role.value < required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente"
            )
        return user
    return decorator

# Endpoints de saúde e status
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Verifica saúde da API."""
    try:
        # Verificar banco de dados
        with get_session() as session:
            db_status = "healthy"
            try:
                session.execute("SELECT 1")
            except Exception:
                db_status = "unhealthy"
        
        # Verificar serviços
        services_status = {
            "database": db_status,
            "recommendation_engine": "healthy",
            "price_intelligence": "healthy",
            "scrapers": "healthy"
        }
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            database=db_status,
            services=services_status
        )
        
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            database="unknown",
            services={"error": str(e)}
        )

@app.get("/status")
async def system_status():
    """Status geral do sistema."""
    try:
        with get_session() as session:
            # Estatísticas básicas
            total_offers = session.query(Offer).count()
            active_offers = session.query(Offer).filter(Offer.is_active == True).count()
            total_users = session.query(User).count()
            
            # Status dos scrapers
            all_sources = get_all_sources()
            enabled_sources = get_enabled_sources()
            
            return {
                "system": "Garimpeiro Geek",
                "status": "operational",
                "timestamp": datetime.now().isoformat(),
                "statistics": {
                    "total_offers": total_offers,
                    "active_offers": active_offers,
                    "total_users": total_users
                },
                "scrapers": {
                    "total": len(all_sources),
                    "enabled": len(enabled_sources),
                    "disabled": len(all_sources) - len(enabled_sources)
                }
            }
            
    except Exception as e:
        logger.error(f"Erro no status do sistema: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter status: {str(e)}"
        )

# Endpoints de ofertas
@app.get("/api/v1/offers", response_model=List[OfferResponse])
async def get_offers(
    limit: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = Query(None),
    store: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    user: UserClaims = Depends(get_current_user)
):
    """Retorna lista de ofertas com filtros."""
    try:
        with get_session() as session:
            query = session.query(Offer).filter(Offer.is_active == True)
            
            if category:
                query = query.filter(Offer.category.ilike(f'%{category}%'))
            
            if store:
                query = query.filter(Offer.store.ilike(f'%{store}%'))
            
            if min_price is not None:
                query = query.filter(Offer.price >= min_price)
            
            if max_price is not None:
                query = query.filter(Offer.price <= max_price)
            
            offers = query.order_by(Offer.created_at.desc()).limit(limit).all()
            
            return offers
            
    except Exception as e:
        logger.error(f"Erro ao buscar ofertas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar ofertas: {str(e)}"
        )

@app.get("/api/v1/offers/{offer_id}", response_model=OfferResponse)
async def get_offer(
    offer_id: int,
    user: UserClaims = Depends(get_current_user)
):
    """Retorna oferta específica por ID."""
    try:
        with get_session() as session:
            offer = session.query(Offer).filter(Offer.id == offer_id).first()
            
            if not offer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Oferta não encontrada"
                )
            
            return offer
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar oferta {offer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar oferta: {str(e)}"
        )

@app.post("/api/v1/offers/search")
async def search_offers(
    request: SearchRequest,
    user: UserClaims = Depends(get_current_user)
):
    """Busca ofertas por texto."""
    try:
        with get_session() as session:
            query = session.query(Offer).filter(Offer.is_active == True)
            
            # Busca por texto
            if request.query:
                search_term = f"%{request.query}%"
                query = query.filter(
                    (Offer.title.ilike(search_term)) |
                    (Offer.description.ilike(search_term)) |
                    (Offer.brand.ilike(search_term))
                )
            
            # Filtros adicionais
            if request.category:
                query = query.filter(Offer.category.ilike(f'%{request.category}%'))
            
            if request.store:
                query = query.filter(Offer.store.ilike(f'%{request.store}%'))
            
            if request.min_price is not None:
                query = query.filter(Offer.price >= request.min_price)
            
            if request.max_price is not None:
                query = query.filter(Offer.price <= request.max_price)
            
            offers = query.order_by(Offer.created_at.desc()).limit(request.limit).all()
            
            return {
                "query": request.query,
                "total_results": len(offers),
                "offers": offers
            }
            
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na busca: {str(e)}"
        )

# Endpoints de recomendações
@app.post("/api/v1/recommendations")
async def get_user_recommendations(
    request: RecommendationRequest,
    user: UserClaims = Depends(get_current_user)
):
    """Retorna recomendações personalizadas para o usuário."""
    try:
        # Verificar se usuário está solicitando suas próprias recomendações
        if user.user_id != request.user_id and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Só pode solicitar suas próprias recomendações"
            )
        
        recommendations = get_recommendations(
            user_id=request.user_id,
            limit=request.limit,
            category=request.category
        )
        
        return {
            "user_id": request.user_id,
            "total_recommendations": len(recommendations),
            "recommendations": recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro nas recomendações: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar recomendações: {str(e)}"
        )

# Endpoints de análise de preços
@app.get("/api/v1/prices/analysis/{product_id}", response_model=PriceAnalysisResponse)
async def analyze_product_prices_api(
    product_id: int,
    force_refresh: bool = Query(False),
    user: UserClaims = Depends(get_current_user)
):
    """Analisa preços de um produto específico."""
    try:
        analysis = analyze_product_prices(product_id, force_refresh)
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado"
            )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na análise de preços: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na análise: {str(e)}"
        )

@app.get("/api/v1/prices/alerts")
async def get_price_alerts_api(
    min_opportunity_score: float = Query(default=70, ge=0, le=100),
    user: UserClaims = Depends(get_current_user)
):
    """Retorna alertas de preço."""
    try:
        alerts = get_price_alerts(min_opportunity_score)
        
        return {
            "min_score": min_opportunity_score,
            "total_alerts": len(alerts),
            "alerts": alerts
        }
        
    except Exception as e:
        logger.error(f"Erro nos alertas de preço: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar alertas: {str(e)}"
        )

@app.get("/api/v1/market/insights")
async def get_market_insights_api(
    user: UserClaims = Depends(get_current_user)
):
    """Retorna insights de mercado."""
    try:
        insights = get_market_insights()
        
        return insights
        
    except Exception as e:
        logger.error(f"Erro nos insights de mercado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar insights: {str(e)}"
        )

# Endpoints de usuários
@app.get("/api/v1/users/me", response_model=UserResponse)
async def get_current_user_info(user: UserClaims = Depends(get_current_user)):
    """Retorna informações do usuário atual."""
    try:
        with get_session() as session:
            db_user = session.query(User).filter(User.id == user.user_id).first()
            
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado"
                )
            
            return db_user
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar usuário: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar usuário: {str(e)}"
        )

@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: UserClaims = Depends(require_role(UserRole.ADMIN))
):
    """Retorna informações de um usuário específico (apenas admin)."""
    try:
        with get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado"
                )
            
            return user
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar usuário {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar usuário: {str(e)}"
        )

# Endpoints de administração
@app.get("/api/v1/admin/stats")
async def get_admin_stats(
    user: UserClaims = Depends(require_role(UserRole.ADMIN))
):
    """Estatísticas administrativas."""
    try:
        with get_session() as session:
            # Estatísticas gerais
            total_offers = session.query(Offer).count()
            active_offers = session.query(Offer).filter(Offer.is_active == True).count()
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.is_active == True).count()
            
            # Estatísticas de preços
            price_stats = session.query(
                Offer.price,
                Offer.original_price
            ).filter(Offer.is_active == True).all()
            
            total_discount = 0
            offers_with_discount = 0
            
            for price, original in price_stats:
                if original and price and original > price:
                    total_discount += ((original - price) / original) * 100
                    offers_with_discount += 1
            
            avg_discount = total_discount / offers_with_discount if offers_with_discount > 0 else 0
            
            return {
                "offers": {
                    "total": total_offers,
                    "active": active_offers,
                    "inactive": total_offers - active_offers
                },
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "inactive": total_users - active_users
                },
                "pricing": {
                    "offers_with_discount": offers_with_discount,
                    "average_discount": round(avg_discount, 2)
                },
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Erro nas estatísticas admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar estatísticas: {str(e)}"
        )

# Middleware de erro global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções não tratadas."""
    logger.error(f"Erro não tratado: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Erro interno do servidor",
            "timestamp": datetime.now().isoformat()
        }
    )

# Inicialização
@app.on_event("startup")
async def startup_event():
    """Evento de inicialização da API."""
    logger.info("🚀 API Garimpeiro Geek iniciando...")
    
    # Verificar conectividade com banco
    try:
        with get_session() as session:
            session.execute("SELECT 1")
        logger.info("✅ Conexão com banco estabelecida")
    except Exception as e:
        logger.error(f"❌ Erro na conexão com banco: {e}")
    
    logger.info("✅ API iniciada com sucesso!")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de encerramento da API."""
    logger.info("🛑 API Garimpeiro Geek encerrando...")

# Execução direta
if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
