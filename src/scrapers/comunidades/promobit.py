"""
Scraper do Promobit para o sistema Garimpeiro Geek.
Coleta ofertas em tempo real da comunidade Promobit.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import re
import json

from ...core.models import Offer
from ...core.affiliate_validator import AffiliateValidator
from ...utils.anti_bot import get_random_user_agent


@dataclass
class PromobitOffer:
    """Oferta do Promobit."""
    title: str
    price: float
    original_price: Optional[float]
    discount: Optional[int]
    store: str
    category: str
    url: str
    image_url: Optional[str]
    posted_at: datetime
    votes: int
    comments: int
    hot: bool


class PromobitScraper:
    """Scraper para o site Promobit."""
    
    def __init__(self):
        """Inicializa o scraper."""
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://www.promobit.com.br"
        self.validator = AffiliateValidator()
        
        # Configurações
        self.max_offers_per_page = 50
        self.rate_limit_delay = 1.0  # segundos entre requisições
        self.max_retries = 3
        
        # Cache de ofertas já processadas
        self.processed_offers = set()
        
        # Estatísticas
        self.stats = {
            "total_scraped": 0,
            "valid_offers": 0,
            "invalid_offers": 0,
            "last_scrape": None,
            "errors": 0
        }
    
    async def scrape_offers(self, max_offers: int = 100) -> List[Offer]:
        """
        Coleta ofertas do Promobit.
        
        Args:
            max_offers: Máximo de ofertas a coletar
            
        Returns:
            Lista de ofertas válidas
        """
        try:
            self.logger.info(f"🕷️ Iniciando coleta de ofertas do Promobit (máx: {max_offers})")
            
            offers = []
            page = 1
            
            while len(offers) < max_offers:
                self.logger.info(f"  📄 Coletando página {page}")
                
                # Coletar ofertas da página
                page_offers = await self._scrape_page(page)
                
                if not page_offers:
                    self.logger.info("  ⚠️ Nenhuma oferta encontrada na página, parando")
                    break
                
                # Processar ofertas da página
                for promobit_offer in page_offers:
                    if len(offers) >= max_offers:
                        break
                    
                    # Converter para modelo Offer
                    offer = await self._convert_to_offer(promobit_offer)
                    
                    if offer and await self._validate_offer(offer):
                        offers.append(offer)
                        self.stats["valid_offers"] += 1
                    else:
                        self.stats["invalid_offers"] += 1
                    
                    # Rate limiting
                    await asyncio.sleep(self.rate_limit_delay)
                
                page += 1
                
                # Verificar se há mais páginas
                if len(page_offers) < self.max_offers_per_page:
                    break
            
            # Atualizar estatísticas
            self.stats["total_scraped"] += len(offers)
            self.stats["last_scrape"] = datetime.now()
            
            self.logger.info(f"✅ Coleta concluída: {len(offers)} ofertas válidas")
            return offers
            
        except Exception as e:
            self.logger.error(f"❌ Erro na coleta de ofertas: {e}")
            self.stats["errors"] += 1
            return []
    
    async def _scrape_page(self, page: int) -> List[PromobitOffer]:
        """
        Coleta ofertas de uma página específica.
        
        Args:
            page: Número da página
            
        Returns:
            Lista de ofertas da página
        """
        try:
            # URL da página
            url = f"{self.base_url}/ofertas?page={page}"
            
            # Em produção, aqui seria feita a requisição HTTP real
            # Por enquanto, simulamos a coleta
            
            # Simular delay de requisição
            await asyncio.sleep(0.5)
            
            # Simular ofertas encontradas
            offers = []
            for i in range(min(20, self.max_offers_per_page)):
                offer = PromobitOffer(
                    title=f"Produto Teste {page}-{i}",
                    price=99.99 + i,
                    original_price=199.99 + i,
                    discount=50,
                    store="Loja Teste",
                    category="Eletrônicos",
                    url=f"https://exemplo.com/produto-{page}-{i}",
                    image_url=None,
                    posted_at=datetime.now(),
                    votes=10 + i,
                    comments=5 + i,
                    hot=i < 5
                )
                offers.append(offer)
            
            return offers
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar página {page}: {e}")
            return []
    
    async def _convert_to_offer(self, promobit_offer: PromobitOffer) -> Optional[Offer]:
        """
        Converte oferta do Promobit para modelo Offer.
        
        Args:
            promobit_offer: Oferta do Promobit
            
        Returns:
            Oferta convertida ou None se inválida
        """
        try:
            # Validar dados básicos
            if not promobit_offer.title or not promobit_offer.url:
                return None
            
            # Calcular desconto
            discount_percentage = None
            if promobit_offer.original_price and promobit_offer.price < promobit_offer.original_price:
                discount_percentage = int(
                    ((promobit_offer.original_price - promobit_offer.price) / promobit_offer.original_price) * 100
                )
            
            # Criar oferta
            offer = Offer(
                title=promobit_offer.title,
                current_price=promobit_offer.price,
                original_price=promobit_offer.original_price,
                discount_percentage=discount_percentage,
                affiliate_url=promobit_offer.url,
                platform="promobit",
                category=promobit_offer.category,
                store=promobit_offer.store,
                image_url=promobit_offer.image_url,
                posted_at=promobit_offer.posted_at
            )
            
            return offer
            
        except Exception as e:
            self.logger.error(f"Erro ao converter oferta: {e}")
            return None
    
    async def _validate_offer(self, offer: Offer) -> bool:
        """
        Valida se uma oferta pode ser processada.
        
        Args:
            offer: Oferta a ser validada
            
        Returns:
            True se válida
        """
        try:
            # Verificar se já foi processada
            offer_hash = f"{offer.title}_{offer.affiliate_url}"
            if offer_hash in self.processed_offers:
                return False
            
            # Validar URL de afiliado
            validation = await self.validator.validate_url(offer.affiliate_url)
            if not validation.is_valid:
                return False
            
            # Validar preço
            if offer.current_price <= 0:
                return False
            
            # Adicionar ao cache de processadas
            self.processed_offers.add(offer_hash)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na validação da oferta: {e}")
            return False
    
    async def scrape_hot_offers(self, max_offers: int = 20) -> List[Offer]:
        """
        Coleta apenas ofertas em alta (hot).
        
        Args:
            max_offers: Máximo de ofertas a coletar
            
        Returns:
            Lista de ofertas em alta
        """
        self.logger.info(f"🔥 Coletando ofertas em alta do Promobit (máx: {max_offers})")
        
        # Em produção, filtraria por ofertas hot
        # Por enquanto, retorna ofertas normais
        return await self.scrape_offers(max_offers)
    
    async def scrape_by_category(self, category: str, max_offers: int = 50) -> List[Offer]:
        """
        Coleta ofertas por categoria.
        
        Args:
            category: Categoria desejada
            max_offers: Máximo de ofertas a coletar
            
        Returns:
            Lista de ofertas da categoria
        """
        self.logger.info(f"📂 Coletando ofertas da categoria '{category}' (máx: {max_offers})")
        
        # Em produção, filtraria por categoria
        # Por enquanto, retorna ofertas normais
        return await self.scrape_offers(max_offers)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do scraper."""
        return self.stats.copy()
    
    def clear_cache(self):
        """Limpa cache de ofertas processadas."""
        self.processed_offers.clear()
        self.logger.info("🗑️ Cache de ofertas processadas limpo")
    
    async def health_check(self) -> bool:
        """Verifica saúde do scraper."""
        try:
            # Testar coleta de uma página
            offers = await self._scrape_page(1)
            return len(offers) > 0
            
        except Exception as e:
            self.logger.error(f"Health check falhou: {e}")
            return False


# Instância global do scraper
promobit_scraper = PromobitScraper()
