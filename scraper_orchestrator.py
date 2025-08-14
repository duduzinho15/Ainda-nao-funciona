"""
Orquestrador Unificado de Scrapers - Integra Selenium e Playwright Stealth
"""
import asyncio
import logging
import time
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import threading

# Importa os scrapers
from magalu_scraper import MagazineLuizaScraper
from amazon_scraper import AmazonScraper
from shopee_scraper import ShopeeScraper
from promobit_scraper import buscar_ofertas_promobit
from magalu_scraper_stealth import MagazineLuizaStealthScraper
from amazon_scraper_stealth import AmazonStealthScraper
from magalu_scraper_advanced import MagazineLuizaAdvancedScraper

# Importa a integração com Awin
try:
    from awin_api import buscar_ofertas_awin
    AWIN_API_AVAILABLE = True
except ImportError as e:
    logging.warning(f"API da Awin não disponível: {e}")
    AWIN_API_AVAILABLE = False

# Importa o scraper do Mercado Livre
try:
    from mercadolivre_scraper import buscar_ofertas_mercadolivre
    MERCADOLIVRE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Scraper do Mercado Livre não disponível: {e}")
    MERCADOLIVRE_AVAILABLE = False

# Importa o sistema de logging centralizado
from logger_config import get_logger, log_scraping_start, log_scraping_complete, log_product_found, log_error, log_info, log_warning, log_automation_cycle

# Configuração de logging
logger = get_logger("orchestrator")

class ScraperOrchestrator:
    """Orquestrador que gerencia todos os scrapers disponíveis"""
    
    def __init__(self, use_stealth: bool = True, max_workers: int = 3):
        self.use_stealth = use_stealth
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Configuração dos scrapers
        self.scrapers_config = {
            'Magazine Luiza': {
                'selenium': MagazineLuizaScraper,
                'stealth': MagazineLuizaStealthScraper,
                'advanced': MagazineLuizaAdvancedScraper,
                'enabled': True,
                'priority': 1
            },
            'Amazon': {
                'selenium': AmazonScraper,
                'stealth': AmazonStealthScraper,
                'advanced': None,
                'enabled': True,
                'priority': 2
            },
            'Shopee': {
                'selenium': ShopeeScraper,
                'stealth': None,  # Shopee não tem versão stealth ainda
                'advanced': None,
                'enabled': True,
                'priority': 3
            },
            'Promobit': {
                'selenium': None,  # Promobit usa requests/BeautifulSoup
                'stealth': None,
                'advanced': None,
                'enabled': True,
                'priority': 4
            },
            'Awin': {
                'selenium': None,  # Awin usa API
                'stealth': None,
                'advanced': None,
                'enabled': AWIN_API_AVAILABLE,
                'priority': 5
            },
            'Mercado Livre': {
                'selenium': None,  # Mercado Livre usa requests/BeautifulSoup
                'stealth': None,
                'advanced': None,
                'enabled': MERCADOLIVRE_AVAILABLE,
                'priority': 6
            }
        }
    
    def get_scraper_instance(self, store_name: str, use_stealth: bool = None, use_advanced: bool = False):
        """Retorna a instância do scraper apropriado"""
        if use_stealth is None:
            use_stealth = self.use_stealth
            
        config = self.scrapers_config.get(store_name)
        if not config or not config['enabled']:
            return None
            
        if use_advanced and config['advanced']:
            return config['advanced']()
        elif use_stealth and config['stealth']:
            return config['stealth']()
        elif config['selenium']:
            return config['selenium']()
        else:
            return None
    
    async def scrape_store_async(self, store_name: str, use_stealth: bool = None, use_advanced: bool = False) -> Tuple[str, List[Dict]]:
        """Executa scraping de uma loja de forma assíncrona"""
        try:
            log_scraping_start(store_name, 1)  # Assumindo 1 fonte por loja
            logger.info(f"🚀 Iniciando scraping de {store_name}")
            start_time = time.time()
            
            if store_name == 'Promobit':
                # Promobit usa função síncrona
                ofertas = buscar_ofertas_promobit(max_paginas=2)
            elif store_name == 'Awin':
                # Awin usa API
                if AWIN_API_AVAILABLE:
                    ofertas = await buscar_ofertas_awin(max_ofertas=max_ofertas, min_desconto=15)
                else:
                    log_error(f"SCRAPING {store_name}", Exception("API da Awin não disponível"), "Configuração inválida")
                    logger.error(f"❌ API da Awin não disponível")
                    return store_name, []
            elif store_name == 'Mercado Livre':
                # Mercado Livre usa requests/BeautifulSoup
                if MERCADOLIVRE_AVAILABLE:
                    ofertas = await buscar_ofertas_mercadolivre(
                        max_ofertas=max_ofertas,
                        min_desconto=15,
                        categorias=['informatica', 'games', 'eletronicos'],
                        palavras_chave=['notebook gamer', 'placa de video', 'smartphone']
                    )
                else:
                    log_error(f"SCRAPING {store_name}", Exception("Scraper do Mercado Livre não disponível"), "Configuração inválida")
                    logger.error(f"❌ Scraper do Mercado Livre não disponível")
                    return store_name, []
            else:
                # Outras lojas usam classes
                scraper = self.get_scraper_instance(store_name, use_stealth, use_advanced)
                if not scraper:
                    log_error(f"SCRAPING {store_name}", Exception("Scraper não disponível"), "Configuração inválida")
                    logger.error(f"❌ Scraper não disponível para {store_name}")
                    return store_name, []
                
                if hasattr(scraper, 'buscar_ofertas'):
                    if asyncio.iscoroutinefunction(scraper.buscar_ofertas):
                        ofertas = await scraper.buscar_ofertas()
                    else:
                        # Executa função síncrona em thread separada
                        loop = asyncio.get_event_loop()
                        ofertas = await loop.run_in_executor(
                            self.executor, 
                            scraper.buscar_ofertas
                        )
                elif hasattr(scraper, 'scrape_all_categories'):
                    # Scraper avançado
                    if asyncio.iscoroutinefunction(scraper.scrape_all_categories):
                        ofertas = await scraper.scrape_all_categories()
                    else:
                        # Executa função síncrona em thread separada
                        loop = asyncio.get_event_loop()
                        ofertas = await loop.run_in_executor(
                            self.executor, 
                            scraper.scrape_all_categories
                        )
                else:
                    log_error(f"SCRAPING {store_name}", Exception("Método não encontrado"), "Interface incompatível")
                    logger.error(f"❌ Método de scraping não encontrado em {store_name}")
                    return store_name, []
            
            elapsed_time = time.time() - start_time
            log_scraping_complete(store_name, len(ofertas), elapsed_time)
            logger.info(f"✅ {store_name}: {len(ofertas)} ofertas em {elapsed_time:.2f}s")
            
            return store_name, ofertas
            
        except Exception as e:
            elapsed_time = time.time() - start_time if 'start_time' in locals() else 0
            log_error(f"SCRAPING {store_name}", e, f"Duração: {elapsed_time:.2f}s")
            logger.error(f"❌ Erro ao fazer scraping de {store_name}: {e}")
            return store_name, []
    
    async def scrape_all_stores(self, use_stealth: bool = None, use_advanced: bool = False) -> Dict[str, List[Dict]]:
        """Executa scraping de todas as lojas habilitadas"""
        if use_stealth is None:
            use_stealth = self.use_stealth
            
        logger.info(f"🎯 Iniciando scraping de todas as lojas (Stealth: {use_stealth}, Advanced: {use_advanced})")
        
        # Filtra lojas habilitadas e ordena por prioridade
        enabled_stores = [
            (name, config) for name, config in self.scrapers_config.items()
            if config['enabled']
        ]
        enabled_stores.sort(key=lambda x: x[1]['priority'])
        
        # Executa scraping em paralelo
        tasks = []
        for store_name, config in enabled_stores:
            task = self.scrape_store_async(store_name, use_stealth, use_advanced)
            tasks.append(task)
        
        # Aguarda todas as tarefas
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa resultados
        all_ofertas = {}
        total_ofertas = 0
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌ Erro em scraping: {result}")
                continue
                
            store_name, ofertas = result
            if ofertas:
                all_ofertas[store_name] = ofertas
                total_ofertas += len(ofertas)
        
        logger.info(f"🎯 Scraping concluído: {total_ofertas} ofertas de {len(all_ofertas)} lojas")
        return all_ofertas
    
    def merge_and_filter_ofertas(self, all_ofertas: Dict[str, List[Dict]], 
                                min_desconto: int = 0,
                                max_preco: float = None,
                                categoria_filtro: str = None) -> List[Dict]:
        """Combina e filtra ofertas de todas as lojas"""
        logger.info("🔍 Combinando e filtrando ofertas...")
        
        merged_ofertas = []
        
        for store_name, ofertas in all_ofertas.items():
            for oferta in ofertas:
                # Adiciona informações da loja se não existir
                if 'loja' not in oferta:
                    oferta['loja'] = store_name
                
                # Aplica filtros
                if min_desconto > 0:
                    desconto = oferta.get('desconto', 0)
                    if not desconto or desconto < min_desconto:
                        continue
                
                if max_preco:
                    try:
                        preco = float(oferta.get('preco', '0').replace(',', '.'))
                        if preco > max_preco:
                            continue
                    except (ValueError, AttributeError):
                        continue
                
                if categoria_filtro:
                    categoria = oferta.get('categoria', '').lower()
                    if categoria_filtro.lower() not in categoria:
                        continue
                
                merged_ofertas.append(oferta)
        
        # Remove duplicatas baseado no título e preço
        unique_ofertas = []
        seen = set()
        
        for oferta in merged_ofertas:
            # Cria chave única baseada no título e preço
            key = f"{oferta.get('titulo', '')}_{oferta.get('preco', '')}"
            if key not in seen:
                seen.add(key)
                unique_ofertas.append(oferta)
        
        logger.info(f"✅ {len(unique_ofertas)} ofertas únicas após filtros")
        return unique_ofertas
    
    async def run_complete_scraping(self, 
                                   use_stealth: bool = None,
                                   use_advanced: bool = False,
                                   min_desconto: int = 0,
                                   max_preco: float = None,
                                   categoria_filtro: str = None) -> List[Dict]:
        """Executa scraping completo com filtros"""
        try:
            log_info("ORQUESTRADOR", f"Iniciando scraping completo (Stealth: {use_stealth}, Advanced: {use_advanced})")
            
            # Executa scraping de todas as lojas
            all_ofertas = await self.scrape_all_stores(use_stealth, use_advanced)
            
            # Combina e filtra ofertas
            final_ofertas = self.merge_and_filter_ofertas(
                all_ofertas, min_desconto, max_preco, categoria_filtro
            )
            
            log_info("ORQUESTRADOR", f"Scraping completo finalizado: {len(final_ofertas)} ofertas filtradas")
            return final_ofertas
            
        except Exception as e:
            log_error("ORQUESTRADOR", e, "Erro no scraping completo")
            logger.error(f"❌ Erro no scraping completo: {e}")
            return []
    
    def close(self):
        """Fecha recursos do orquestrador"""
        if self.executor:
            self.executor.shutdown(wait=True)

async def main():
    """Função principal para teste"""
    orchestrator = ScraperOrchestrator(use_stealth=True)
    
    try:
        print("🚀 INICIANDO SCRAPING COMPLETO")
        print("=" * 60)
        
        # Executa scraping com filtros
        ofertas = await orchestrator.run_complete_scraping(
            use_stealth=True,
            use_advanced=True,  # Ativa o modo avançado para Magazine Luiza
            min_desconto=0,  # Mudado de 10 para 0 para mostrar mais ofertas
            max_preco=5000.0,  # Aumentado para R$ 5000
            categoria_filtro=None  # Removido filtro de categoria para mostrar todas
        )
        
        print(f"\n🎯 RESULTADO FINAL: {len(ofertas)} ofertas filtradas")
        print("=" * 60)
        
        # Mostra as melhores ofertas
        for i, oferta in enumerate(ofertas[:10], 1):
            print(f"\n{i}. {oferta['titulo'][:60]}...")
            print(f"   💰 Preço: {oferta['preco']}")
            if oferta.get('desconto'):
                print(f"   🏷️ Desconto: {oferta['desconto']}%")
            print(f"   🏪 Loja: {oferta['loja']}")
            if oferta.get('categoria'):
                print(f"   📂 Categoria: {oferta['categoria']}")
        
    finally:
        orchestrator.close()

if __name__ == "__main__":
    asyncio.run(main())
