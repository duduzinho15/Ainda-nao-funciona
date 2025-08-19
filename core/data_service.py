"""
Data service for integrating all scrapers and APIs
"""
import os
import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import asyncio

from .models import Oferta, Periodo, MetricsSnapshot, ScraperSettings
from .normalize import deduplicate_ofertas, get_deduplication_stats

class DataService:
    """Serviço centralizado para dados de todos os scrapers"""
    
    def __init__(self):
        self._cache = {}
        self._last_update = {}
        
    async def load_ofertas(self, periodo: str, use_registry: bool = True) -> List[Oferta]:
        """
        Carrega ofertas de todos os scrapers para o período especificado.
        
        Args:
            periodo: Período para coleta (24h, 7d, 30d, all)
            use_registry: Se deve usar o registry de scrapers
            
        Returns:
            Lista de ofertas coletadas
        """
        # Verificar se estamos em modo determinístico (CI)
        is_deterministic = os.getenv("GG_SEED") and os.getenv("GG_FREEZE_TIME")
        
        if is_deterministic:
            print("🔒 Modo CI: usando dados determinísticos")
            return self._get_deterministic_ofertas(periodo)
        
        # Modo normal - tentar dados reais
        if use_registry:
            try:
                return await self._load_real_ofertas_via_registry(periodo)
            except Exception as e:
                print(f"❌ Erro ao carregar dados via registry: {e}")
                return self._get_fallback_ofertas(periodo)
        else:
            try:
                return await self._load_real_ofertas(periodo)
            except Exception as e:
                print(f"❌ Erro ao carregar dados reais: {e}")
                return self._get_fallback_ofertas(periodo)
    
    def _get_deterministic_ofertas(self, periodo: str) -> List[Oferta]:
        """Gera ofertas determinísticas para CI"""
        seed = int(os.getenv("GG_SEED", "1337"))
        random.seed(seed)
        
        # Timestamp fixo para CI
        freeze_time = os.getenv("GG_FREEZE_TIME", "2025-01-01T00:00:00Z")
        base_time = datetime.fromisoformat(freeze_time.replace("Z", "+00:00"))
        
        # Dados determinísticos baseados no período
        period_data = {
            "24h": {"count": 8, "days_back": 1},
            "7d": {"count": 25, "days_back": 7},
            "30d": {"count": 89, "days_back": 30},
            "all": {"count": 156, "days_back": 90}
        }
        
        config = period_data.get(periodo, period_data["all"])
        ofertas = []
        
        lojas = ["Amazon", "Magalu", "Shopee", "AliExpress", "Promobit", "Pelando", "MeuPC", "Buscape"]
        
        for i in range(config["count"]):
            # Preço determinístico baseado no índice
            preco = 50.0 + (i * 2.5) + (random.randint(0, 100) / 10)
            preco_original = preco * (1 + random.uniform(0.1, 0.3))
            
            # Timestamp determinístico
            days_offset = random.randint(0, config["days_back"])
            created_at = base_time - timedelta(days=days_offset)
            
            oferta = Oferta(
                titulo=f"Produto {i+1} - Oferta Especial",
                loja=lojas[i % len(lojas)],
                preco=round(preco, 2),
                preco_original=round(preco_original, 2),
                url=f"https://exemplo.com/produto-{i+1}",
                imagem_url=f"https://exemplo.com/img-{i+1}.jpg",
                created_at=created_at,
                fonte="deterministic"
            )
            ofertas.append(oferta)
        
        return ofertas
    
    async def _load_real_ofertas(self, periodo: str) -> List[Oferta]:
        """Carrega ofertas reais de todos os scrapers"""
        ofertas = []
        
        # Calcular período de tempo
        now = datetime.now(timezone.utc)
        if periodo == "24h":
            start_time = now - timedelta(days=1)
        elif periodo == "7d":
            start_time = now - timedelta(days=7)
        elif periodo == "30d":
            start_time = now - timedelta(days=30)
        else:  # all
            start_time = now - timedelta(days=365)
        
        # Carregar de diferentes fontes
        sources = [
            self._load_amazon_ofertas,
            self._load_magalu_ofertas,
            self._load_shopee_ofertas,
            self._load_aliexpress_ofertas,
            self._load_promobit_ofertas,
            self._load_pelando_ofertas,
            self._load_meupc_ofertas,
            self._load_buscape_ofertas
        ]
        
        # Executar scrapers em paralelo
        tasks = [source(start_time, now) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                ofertas.extend(result)
            elif isinstance(result, Exception):
                print(f"Erro em scraper: {result}")
        
        # Filtrar por período e ordenar
        ofertas = [o for o in ofertas if o.created_at >= start_time]
        ofertas.sort(key=lambda x: x.created_at, reverse=True)
        
        # Aplicar deduplicação
        ofertas_unicas = deduplicate_ofertas(ofertas)
        stats = get_deduplication_stats(ofertas)
        
        print(f"Deduplicação: {stats['total']} -> {stats['unicas']} ofertas ({stats['reducao_percentual']}% redução)")
        
        return ofertas_unicas
    
    def _get_fallback_ofertas(self, periodo: str) -> List[Oferta]:
        """Ofertas de fallback quando scrapers falham"""
        return self._get_deterministic_ofertas(periodo)
    
    async def _load_real_ofertas_via_registry(self, periodo: str) -> List[Oferta]:
        """Carrega ofertas reais usando o registry de scrapers."""
        try:
            # Importar registry
            from .scraper_registry import scraper_registry
            
            print(f"🔄 Carregando ofertas via registry para período: {periodo}")
            
            # Coletar de todos os scrapers habilitados
            ofertas_raw = await scraper_registry.collect_from_all(periodo)
            
            if not ofertas_raw:
                print("⚠️ Nenhuma oferta coletada via registry")
                return []
            
            # Converter para objetos Oferta
            ofertas = []
            for oferta_raw in ofertas_raw:
                try:
                    if isinstance(oferta_raw, dict):
                        oferta = self._dict_to_oferta(oferta_raw)
                    else:
                        oferta = self._object_to_oferta(oferta_raw)
                    
                    if oferta:
                        ofertas.append(oferta)
                        
                except Exception as e:
                    print(f"⚠️ Erro ao converter oferta: {e}")
                    continue
            
            print(f"✅ {len(ofertas)} ofertas convertidas via registry")
            
            # Aplicar deduplicação
            ofertas_unicas = deduplicate_ofertas(ofertas)
            stats = get_deduplication_stats(ofertas)
            
            print(f"🎯 Deduplicação: {stats['total']} -> {stats['unicas']} ofertas ({stats['reducao_percentual']}% redução)")
            
            return ofertas_unicas
            
        except Exception as e:
            print(f"❌ Erro ao carregar via registry: {e}")
            raise
    
    def _dict_to_oferta(self, oferta_dict: Dict[str, Any]) -> Optional[Oferta]:
        """Converte dicionário para objeto Oferta."""
        try:
            # Extrair campos básicos
            titulo = oferta_dict.get('titulo', '')
            loja = oferta_dict.get('loja', '')
            preco = oferta_dict.get('preco', 0.0)
            preco_original = oferta_dict.get('preco_original', preco)
            url = oferta_dict.get('url', '')
            imagem_url = oferta_dict.get('imagem_url', '')
            fonte = oferta_dict.get('fonte', 'registry')
            
            # Converter timestamp
            created_at = None
            if 'created_at' in oferta_dict:
                timestamp = oferta_dict['created_at']
                if isinstance(timestamp, str):
                    try:
                        created_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        created_at = datetime.now()
                elif hasattr(timestamp, 'isoformat'):
                    created_at = timestamp
                else:
                    created_at = datetime.now()
            else:
                created_at = datetime.now()
            
            # Criar objeto Oferta
            return Oferta(
                titulo=titulo,
                loja=loja,
                preco=float(preco) if preco else 0.0,
                preco_original=float(preco_original) if preco_original else 0.0,
                url=url,
                imagem_url=imagem_url,
                created_at=created_at,
                fonte=fonte
            )
            
        except Exception as e:
            print(f"⚠️ Erro ao converter dicionário para Oferta: {e}")
            return None
    
    def _object_to_oferta(self, oferta_obj: Any) -> Optional[Oferta]:
        """Converte objeto para Oferta."""
        try:
            # Tentar extrair atributos do objeto
            titulo = getattr(oferta_obj, 'titulo', '') or getattr(oferta_obj, 'title', '')
            loja = getattr(oferta_obj, 'loja', '') or getattr(oferta_obj, 'store', '')
            preco = getattr(oferta_obj, 'preco', 0.0) or getattr(oferta_obj, 'price', 0.0)
            preco_original = getattr(oferta_obj, 'preco_original', preco) or getattr(oferta_obj, 'original_price', preco)
            url = getattr(oferta_obj, 'url', '')
            imagem_url = getattr(oferta_obj, 'imagem_url', '') or getattr(oferta_obj, 'image_url', '')
            fonte = getattr(oferta_obj, 'fonte', 'registry')
            
            # Converter timestamp
            created_at = None
            if hasattr(oferta_obj, 'created_at'):
                timestamp = oferta_obj.created_at
                if timestamp:
                    created_at = timestamp
                else:
                    created_at = datetime.now()
            else:
                created_at = datetime.now()
            
            # Criar objeto Oferta
            return Oferta(
                titulo=str(titulo) if titulo else '',
                loja=str(loja) if loja else '',
                preco=float(preco) if preco else 0.0,
                preco_original=float(preco_original) if preco_original else 0.0,
                url=str(url) if url else '',
                imagem_url=str(imagem_url) if imagem_url else '',
                created_at=created_at,
                fonte=str(fonte) if fonte else 'registry'
            )
            
        except Exception as e:
            print(f"⚠️ Erro ao converter objeto para Oferta: {e}")
            return None
    
    async def _load_amazon_ofertas(self, start_time: datetime, end_time: datetime) -> List[Oferta]:
        """Carrega ofertas da Amazon"""
        try:
            # Tentar importar amazon_scraper
            from amazon_scraper import get_ofertas
            urls = ["https://amazon.com.br/ofertas"]
            settings = ScraperSettings()
            return await get_ofertas(urls, settings)
        except ImportError:
            return self._mock_ofertas("Amazon", 12, start_time, end_time)
    
    async def _load_magalu_ofertas(self, start_time: datetime, end_time: datetime) -> List[Oferta]:
        """Carrega ofertas do Magalu"""
        try:
            from magalu_scraper import scrape_ofertas
            return await scrape_ofertas()
        except ImportError:
            return self._mock_ofertas("Magalu", 8, start_time, end_time)
    
    async def _load_shopee_ofertas(self, start_time: datetime, end_time: datetime) -> List[Oferta]:
        """Carrega ofertas da Shopee"""
        try:
            from shopee_api import get_ofertas
            return await get_ofertas()
        except ImportError:
            return self._mock_ofertas("Shopee", 15, start_time, end_time)
    
    async def _load_aliexpress_ofertas(self, start_time: datetime, end_time: datetime) -> List[Oferta]:
        """Carrega ofertas do AliExpress"""
        try:
            from aliexpress_api import get_ofertas
            return await get_ofertas()
        except ImportError:
            return self._mock_ofertas("AliExpress", 10, start_time, end_time)
    
    async def _load_promobit_ofertas(self, start_time: datetime, end_time: datetime) -> List[Oferta]:
        """Carrega ofertas do Promobit"""
        try:
            from promobit_scraper import scrape_ofertas
            return await scrape_ofertas()
        except ImportError:
            return self._mock_ofertas("Promobit", 6, start_time, end_time)
    
    async def _load_pelando_ofertas(self, start_time: datetime, end_time: datetime) -> List[Oferta]:
        """Carrega ofertas do Pelando"""
        try:
            from pelando_scraper import scrape_ofertas
            return await scrape_ofertas()
        except ImportError:
            return self._mock_ofertas("Pelando", 9, start_time, end_time)
    
    async def _load_meupc_ofertas(self, start_time: datetime, end_time: datetime) -> List[Oferta]:
        """Carrega ofertas do MeuPC"""
        try:
            from meupc_scraper import scrape_ofertas
            return await scrape_ofertas()
        except ImportError:
            return self._mock_ofertas("MeuPC", 7, start_time, end_time)
    
    async def _load_buscape_ofertas(self, start_time: datetime, end_time: datetime) -> List[Oferta]:
        """Carrega ofertas do Buscapé"""
        try:
            from buscape_scraper import scrape_ofertas
            return await scrape_ofertas()
        except ImportError:
            return self._mock_ofertas("Buscape", 5, start_time, end_time)
    
    def _mock_ofertas(self, loja: str, count: int, start_time: datetime, end_time: datetime) -> List[Oferta]:
        """Gera ofertas mock para uma loja específica"""
        ofertas = []
        for i in range(count):
            preco = 30.0 + (i * 3.0) + random.uniform(0, 50)
            preco_original = preco * (1 + random.uniform(0.1, 0.4))
            
            # Timestamp aleatório no período
            time_diff = (end_time - start_time).total_seconds()
            random_seconds = random.uniform(0, time_diff)
            created_at = start_time + timedelta(seconds=random_seconds)
            
            oferta = Oferta(
                titulo=f"Produto {i+1} - {loja}",
                loja=loja,
                preco=round(preco, 2),
                preco_original=round(preco_original, 2),
                url=f"https://{loja.lower()}.com/produto-{i+1}",
                imagem_url=f"https://{loja.lower()}.com/img-{i+1}.jpg",
                created_at=created_at,
                fonte="mock"
            )
            ofertas.append(oferta)
        
        return ofertas
    
    def get_metrics_snapshot(self, ofertas: List[Oferta], periodo: str) -> MetricsSnapshot:
        """Gera snapshot de métricas das ofertas"""
        if not ofertas:
            return MetricsSnapshot(
                total_ofertas=0,
                lojas_ativas=0,
                preco_medio=None,
                periodo=Periodo(periodo),
                timestamp=datetime.now(timezone.utc),
                distribuicao_lojas={}
            )
        
        # Calcular métricas
        total_ofertas = len(ofertas)
        lojas_ativas = len(set(o.loja for o in ofertas))
        
        # Preço médio (ignorando None)
        precos_validos = [o.preco for o in ofertas if o.preco is not None]
        preco_medio = sum(precos_validos) / len(precos_validos) if precos_validos else None
        
        # Distribuição por loja
        distribuicao = {}
        for oferta in ofertas:
            distribuicao[oferta.loja] = distribuicao.get(oferta.loja, 0) + 1
        
        return MetricsSnapshot(
            total_ofertas=total_ofertas,
            lojas_ativas=lojas_ativas,
            preco_medio=preco_medio,
            periodo=Periodo(periodo),
            timestamp=datetime.now(timezone.utc),
            distribuicao_lojas=distribuicao
        )

