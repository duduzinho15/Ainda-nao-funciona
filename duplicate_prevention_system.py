#!/usr/bin/env python3
"""
Sistema Anti-Duplicidade para Scrapers
Evita processamento duplicado de sites e produtos
"""
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('duplicate_prevention.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('duplicate_prevention')

class SiteType(Enum):
    """Tipos de sites para categorização"""
    PRICE_COMPARISON = "price_comparison"      # Buscapé, Zoom, etc.
    DEAL_AGGREGATOR = "deal_aggregator"       # Promobit, Pelando, etc.
    ECOMMERCE = "ecommerce"                   # Amazon, Shopee, etc.
    HARDWARE_SPECIALIST = "hardware_specialist"  # MeuPC.net, etc.
    MARKETPLACE = "marketplace"               # MercadoLivre, etc.

@dataclass
class SiteInfo:
    """Informações sobre um site"""
    domain: str
    name: str
    site_type: SiteType
    last_processed: datetime
    processing_frequency: timedelta  # Frequência mínima entre processamentos
    is_active: bool = True
    total_products_found: int = 0
    unique_products_ratio: float = 0.0  # % de produtos únicos

@dataclass
class ProductHash:
    """Hash único de um produto para detecção de duplicatas"""
    title_hash: str
    price_hash: str
    store_hash: str
    combined_hash: str
    first_seen: datetime
    last_seen: datetime
    seen_count: int = 1
    platforms: Optional[List[str]] = None

class DuplicatePreventionSystem:
    """Sistema principal para prevenir duplicidade"""
    
    def __init__(self, cache_file: str = "duplicate_cache.json"):
        self.cache_file = cache_file
        self.sites_registry: Dict[str, SiteInfo] = {}
        self.product_hashes: Dict[str, ProductHash] = {}
        self.processed_urls: Set[str] = set()
        self.site_processing_history: Dict[str, List[datetime]] = {}
        
        # Configurações
        self.min_processing_interval = timedelta(minutes=30)  # Intervalo mínimo entre processamentos
        self.max_product_age = timedelta(days=7)  # Produtos mais antigos que isso são considerados "novos"
        self.similarity_threshold = 0.85  # Threshold para considerar produtos similares
        
        # Carrega cache existente
        self.load_cache()
        
        # Inicializa registro de sites
        self.initialize_sites_registry()
    
    def initialize_sites_registry(self):
        """Inicializa o registro de sites conhecidos"""
        known_sites = {
            "buscape.com.br": {
                "name": "Buscapé",
                "site_type": SiteType.PRICE_COMPARISON,
                "processing_frequency": timedelta(hours=2)
            },
            "zoom.com.br": {
                "name": "Zoom",
                "site_type": SiteType.PRICE_COMPARISON,
                "processing_frequency": timedelta(hours=1)
            },
            "promobit.com.br": {
                "name": "Promobit",
                "site_type": SiteType.DEAL_AGGREGATOR,
                "processing_frequency": timedelta(minutes=30)
            },
            "pelando.com.br": {
                "name": "Pelando",
                "site_type": SiteType.DEAL_AGGREGATOR,
                "processing_frequency": timedelta(minutes=30)
            },
            "meupc.net": {
                "name": "MeuPC.net",
                "site_type": SiteType.HARDWARE_SPECIALIST,
                "processing_frequency": timedelta(hours=1)
            },
            "amazon.com.br": {
                "name": "Amazon",
                "site_type": SiteType.ECOMMERCE,
                "processing_frequency": timedelta(hours=1)
            },
            "shopee.com.br": {
                "name": "Shopee",
                "site_type": SiteType.MARKETPLACE,
                "processing_frequency": timedelta(hours=1)
            },
            "mercadolivre.com.br": {
                "name": "MercadoLivre",
                "site_type": SiteType.MARKETPLACE,
                "processing_frequency": timedelta(hours=1)
            },
            "aliexpress.com": {
                "name": "AliExpress",
                "site_type": SiteType.ECOMMERCE,
                "processing_frequency": timedelta(hours=2)
            }
        }
        
        for domain, info in known_sites.items():
            if domain not in self.sites_registry:
                self.sites_registry[domain] = SiteInfo(
                    domain=domain,
                    name=info["name"],
                    site_type=info["site_type"],
                    last_processed=datetime.now() - timedelta(days=1),  # Permite processamento imediato
                    processing_frequency=info["processing_frequency"]
                )
    
    def can_process_site(self, domain: str) -> bool:
        """Verifica se um site pode ser processado baseado na frequência"""
        if domain not in self.sites_registry:
            # Site desconhecido, permite processamento
            return True
        
        site_info = self.sites_registry[domain]
        if not site_info.is_active:
            return False
        
        time_since_last = datetime.now() - site_info.last_processed
        return time_since_last >= site_info.processing_frequency
    
    def mark_site_processed(self, domain: str, products_found: int = 0):
        """Marca um site como processado"""
        if domain not in self.sites_registry:
            # Cria entrada para site desconhecido
            self.sites_registry[domain] = SiteInfo(
                domain=domain,
                name=domain,
                site_type=SiteType.ECOMMERCE,  # Default
                last_processed=datetime.now(),
                processing_frequency=self.min_processing_interval
            )
        
        site_info = self.sites_registry[domain]
        site_info.last_processed = datetime.now()
        site_info.total_products_found += products_found
        
        # Atualiza histórico de processamento
        if domain not in self.site_processing_history:
            self.site_processing_history[domain] = []
        
        self.site_processing_history[domain].append(datetime.now())
        
        # Mantém apenas os últimos 100 processamentos
        if len(self.site_processing_history[domain]) > 100:
            self.site_processing_history[domain] = self.site_processing_history[domain][-100:]
        
        logger.info(f"✅ Site {domain} marcado como processado. Produtos encontrados: {products_found}")
    
    def generate_product_hash(self, product: Dict[str, Any]) -> str:
        """Gera hash único para um produto"""
        # Extrai campos principais
        title = str(product.get('titulo', product.get('title', ''))).lower().strip()
        price = str(product.get('preco_atual', product.get('price', 0)))
        store = str(product.get('loja', product.get('store', ''))).lower().strip()
        
        # Remove palavras comuns e normaliza
        common_words = ['o', 'a', 'de', 'da', 'do', 'em', 'para', 'com', 'sem', 'por']
        title_words = [word for word in title.split() if word not in common_words and len(word) > 2]
        normalized_title = ' '.join(title_words[:5])  # Primeiras 5 palavras significativas
        
        # Gera hash combinado
        combined_string = f"{normalized_title}|{price}|{store}"
        return hashlib.md5(combined_string.encode('utf-8')).hexdigest()
    
    def is_duplicate_product(self, product: Dict[str, Any], platform: str) -> bool:
        """Verifica se um produto é duplicado - versão menos restritiva"""
        product_hash = self.generate_product_hash(product)
        
        if product_hash in self.product_hashes:
            existing_product = self.product_hashes[product_hash]
            
            # Verifica se já foi visto nesta plataforma E é muito recente (menos de 30 minutos)
            platforms_list = existing_product.platforms or []
            if platform in platforms_list:
                time_since_last = datetime.now() - existing_product.last_seen
                if time_since_last < timedelta(minutes=30):
                    return True
                # Se passou mais de 30 minutos, permite reprocessar
                existing_product.last_seen = datetime.now()
                existing_product.seen_count += 1
                return False
            
            # Verifica se é muito recente (menos de 15 minutos) em qualquer plataforma
            time_since_first = datetime.now() - existing_product.first_seen
            if time_since_first < timedelta(minutes=15):
                return True
            
            # Atualiza informações do produto existente
            existing_product.last_seen = datetime.now()
            existing_product.seen_count += 1
            if existing_product.platforms is None:
                existing_product.platforms = []
            if platform not in existing_product.platforms:
                existing_product.platforms.append(platform)
            
            return False
        else:
            # Produto novo, adiciona ao registro
            self.product_hashes[product_hash] = ProductHash(
                title_hash=product_hash,
                price_hash=str(product.get('preco_atual', product.get('price', 0))),
                store_hash=str(product.get('loja', product.get('store', ''))),
                combined_hash=product_hash,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                platforms=[platform]
            )
            return False
    
    def filter_duplicate_products(self, products: List[Dict[str, Any]], platform: str) -> List[Dict[str, Any]]:
        """Filtra produtos duplicados de uma lista"""
        unique_products = []
        duplicates_found = 0
        
        for product in products:
            if not self.is_duplicate_product(product, platform):
                unique_products.append(product)
            else:
                duplicates_found += 1
        
        logger.info(f"🔍 Filtrados {duplicates_found} produtos duplicados de {platform}. "
                   f"Produtos únicos: {len(unique_products)}")
        
        return unique_products
    
    def get_site_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas dos sites processados"""
        stats = {
            "total_sites": len(self.sites_registry),
            "active_sites": len([s for s in self.sites_registry.values() if s.is_active]),
            "total_products": len(self.product_hashes),
            "sites_by_type": {},
            "processing_frequency": {},
            "duplicate_rates": {}
        }
        
        # Estatísticas por tipo de site
        for site_info in self.sites_registry.values():
            site_type = site_info.site_type.value
            if site_type not in stats["sites_by_type"]:
                stats["sites_by_type"][site_type] = 0
            stats["sites_by_type"][site_type] += 1
        
        # Frequência de processamento
        for domain, site_info in self.sites_registry.items():
            if domain in self.site_processing_history:
                recent_processings = [
                    p for p in self.site_processing_history[domain]
                    if datetime.now() - p < timedelta(days=7)
                ]
                stats["processing_frequency"][domain] = len(recent_processings)
        
        # Taxa de duplicatas por site
        for domain in self.sites_registry:
            if domain in self.site_processing_history:
                total_processed = len(self.site_processing_history[domain])
                if total_processed > 0:
                    # Calcula taxa baseada em produtos únicos vs total
                    site_info = self.sites_registry[domain]
                    if site_info.total_products_found > 0:
                        duplicate_rate = 1 - (len(self.product_hashes) / site_info.total_products_found)
                        stats["duplicate_rates"][domain] = round(duplicate_rate, 2)
        
        return stats
    
    def cleanup_old_products(self, max_age_days: int = 30):
        """Remove produtos antigos do cache"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        old_products = []
        
        for product_hash, product_info in list(self.product_hashes.items()):
            if product_info.last_seen < cutoff_date:
                old_products.append(product_hash)
                del self.product_hashes[product_hash]
        
        if old_products:
            logger.info(f"🧹 Removidos {len(old_products)} produtos antigos do cache")
    
    def save_cache(self):
        """Salva o cache em arquivo"""
        try:
            cache_data = {
                "sites_registry": {
                    domain: {
                        **asdict(site_info),
                        "last_processed": site_info.last_processed.isoformat(),
                        "processing_frequency": site_info.processing_frequency.total_seconds(),
                        "site_type": site_info.site_type.value  # Converte enum para string
                    }
                    for domain, site_info in self.sites_registry.items()
                },
                "product_hashes": {
                    hash_key: {
                        **asdict(product_info),
                        "first_seen": product_info.first_seen.isoformat(),
                        "last_seen": product_info.last_seen.isoformat()
                    }
                    for hash_key, product_info in self.product_hashes.items()
                },
                "site_processing_history": {
                    domain: [p.isoformat() for p in timestamps]
                    for domain, timestamps in self.site_processing_history.items()
                }
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Cache salvo em {self.cache_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar cache: {e}")
    
    def load_cache(self):
        """Carrega o cache do arquivo"""
        if not os.path.exists(self.cache_file):
            logger.info("📁 Cache não encontrado, iniciando com dados vazios")
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Restaura sites registry
            for domain, site_data in cache_data.get("sites_registry", {}).items():
                self.sites_registry[domain] = SiteInfo(
                    domain=domain,
                    name=site_data["name"],
                    site_type=SiteType(site_data["site_type"]),
                    last_processed=datetime.fromisoformat(site_data["last_processed"]),
                    processing_frequency=timedelta(seconds=site_data["processing_frequency"]),
                    is_active=site_data.get("is_active", True),
                    total_products_found=site_data.get("total_products_found", 0),
                    unique_products_ratio=site_data.get("unique_products_ratio", 0.0)
                )
            
            # Restaura product hashes
            for hash_key, product_data in cache_data.get("product_hashes", {}).items():
                self.product_hashes[hash_key] = ProductHash(
                    title_hash=product_data["title_hash"],
                    price_hash=product_data["price_hash"],
                    store_hash=product_data["store_hash"],
                    combined_hash=product_data["combined_hash"],
                    first_seen=datetime.fromisoformat(product_data["first_seen"]),
                    last_seen=datetime.fromisoformat(product_data["last_seen"]),
                    seen_count=product_data.get("seen_count", 1),
                    platforms=product_data.get("platforms", [])
                )
            
            # Restaura histórico de processamento
            for domain, timestamps in cache_data.get("site_processing_history", {}).items():
                self.site_processing_history[domain] = [
                    datetime.fromisoformat(ts) for ts in timestamps
                ]
            
            logger.info(f"📁 Cache carregado: {len(self.sites_registry)} sites, {len(self.product_hashes)} produtos")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar cache: {e}")
    
    def get_next_processing_time(self, domain: str) -> Optional[datetime]:
        """Retorna quando um site pode ser processado novamente"""
        if domain not in self.sites_registry:
            return datetime.now()
        
        site_info = self.sites_registry[domain]
        return site_info.last_processed + site_info.processing_frequency
    
    def get_processing_queue(self) -> List[Dict[str, Any]]:
        """Retorna fila de sites que podem ser processados"""
        queue = []
        current_time = datetime.now()
        
        for domain, site_info in self.sites_registry.items():
            if not site_info.is_active:
                continue
            
            next_processing = site_info.last_processed + site_info.processing_frequency
            if current_time >= next_processing:
                queue.append({
                    "domain": domain,
                    "name": site_info.name,
                    "site_type": site_info.site_type.value,
                    "priority": self.calculate_priority(site_info),
                    "time_since_last": current_time - site_info.last_processed
                })
        
        # Ordena por prioridade (maior primeiro)
        queue.sort(key=lambda x: x["priority"], reverse=True)
        return queue
    
    def calculate_priority(self, site_info: SiteInfo) -> float:
        """Calcula prioridade de processamento de um site"""
        base_priority = 1.0
        
        # Ajusta por tipo de site
        type_priorities = {
            SiteType.DEAL_AGGREGATOR: 1.5,      # Alta prioridade (ofertas mudam rápido)
            SiteType.PRICE_COMPARISON: 1.2,     # Média-alta prioridade
            SiteType.HARDWARE_SPECIALIST: 1.1,  # Média prioridade
            SiteType.ECOMMERCE: 1.0,            # Prioridade padrão
            SiteType.MARKETPLACE: 0.9           # Prioridade menor
        }
        
        base_priority *= type_priorities.get(site_info.site_type, 1.0)
        
        # Ajusta por frequência de processamento
        if site_info.processing_frequency < timedelta(hours=1):
            base_priority *= 1.3  # Sites que mudam rápido têm prioridade
        
        # Ajusta por tempo desde último processamento
        time_since_last = datetime.now() - site_info.last_processed
        if time_since_last > timedelta(days=1):
            base_priority *= 1.5  # Sites não processados há muito tempo
        
        return base_priority

def main():
    """Função principal para teste"""
    print("🚀 TESTANDO SISTEMA ANTI-DUPLICIDADE")
    print("=" * 50)
    
    # Cria sistema
    dps = DuplicatePreventionSystem()
    
    # Simula processamento de sites
    test_sites = ["buscape.com.br", "promobit.com.br", "meupc.net"]
    
    for site in test_sites:
        print(f"\n🔍 Testando site: {site}")
        
        if dps.can_process_site(site):
            print(f"   ✅ Pode ser processado")
            
            # Simula produtos encontrados
            test_products = [
                {"titulo": "Smartphone Samsung Galaxy", "preco_atual": "999.99", "loja": "Amazon"},
                {"titulo": "Notebook Gamer", "preco_atual": "2999.99", "loja": "Kabum"},
                {"titulo": "Mouse Gaming RGB", "preco_atual": "199.99", "loja": "Terabyte"}
            ]
            
            # Filtra duplicatas
            unique_products = dps.filter_duplicate_products(test_products, site)
            print(f"   📦 Produtos únicos: {len(unique_products)}")
            
            # Marca como processado
            dps.mark_site_processed(site, len(unique_products))
            
        else:
            next_time = dps.get_next_processing_time(site)
            print(f"   ⏰ Próximo processamento: {next_time.strftime('%H:%M:%S')}")
    
    # Mostra estatísticas
    print(f"\n📊 Estatísticas:")
    stats = dps.get_site_statistics()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                print(f"     {sub_key}: {sub_value}")
        else:
            print(f"   {key}: {value}")
    
    # Mostra fila de processamento
    print(f"\n🔄 Fila de Processamento:")
    queue = dps.get_processing_queue()
    for item in queue:
        print(f"   {item['name']} ({item['domain']}) - Prioridade: {item['priority']:.2f}")
    
    # Salva cache
    dps.save_cache()
    print(f"\n💾 Cache salvo com sucesso!")

if __name__ == "__main__":
    main()
