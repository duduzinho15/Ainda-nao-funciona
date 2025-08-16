#!/usr/bin/env python3
"""
Orquestrador Inteligente de Scrapers
Coordena todos os scrapers usando o sistema anti-duplicidade
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Sistema Anti-Duplicidade
from duplicate_prevention_system import DuplicatePreventionSystem

# Scrapers
from promobit_scraper_fixed import buscar_ofertas_promobit
from pelando_scraper_fixed import buscar_ofertas_pelando
from zoom_scraper import ZoomScraper
from meupc_scraper import buscar_ofertas_meupc
from buscape_scraper_fixed import buscar_ofertas_buscape
from magalu_scraper import MagazineLuizaScraper

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('intelligent_orchestrator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('intelligent_orchestrator')

@dataclass
class ScraperConfig:
    """Configuração de um scraper"""
    name: str
    domain: str
    function_name: str
    enabled: bool = True
    priority: float = 1.0
    max_retries: int = 3
    retry_delay: int = 300  # segundos

@dataclass
class ScrapingResult:
    """Resultado de uma execução de scraper"""
    scraper_name: str
    domain: str
    success: bool
    products_found: int
    unique_products: int
    execution_time: float
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class IntelligentScraperOrchestrator:
    """Orquestrador inteligente de scrapers"""
    
    def __init__(self):
        self.dps = DuplicatePreventionSystem()
        self.scrapers: Dict[str, ScraperConfig] = {}
        self.results_history: List[ScrapingResult] = []
        self.running = False
        
        # Inicializa configurações dos scrapers
        self.initialize_scrapers()
        
        # Estatísticas
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_products_found": 0,
            "total_unique_products": 0,
            "start_time": datetime.now(),
            "last_execution": datetime.now()
        }
    
    def initialize_scrapers(self):
        """Inicializa configurações dos scrapers"""
        self.scrapers = {
            "promobit": ScraperConfig(
                name="Promobit",
                domain="promobit.com.br",
                function_name="promobit",
                priority=1.5,  # Alta prioridade (ofertas mudam rápido)
                max_retries=3
            ),
            "pelando": ScraperConfig(
                name="Pelando",
                domain="pelando.com.br",
                function_name="pelando",
                priority=1.5,  # Alta prioridade
                max_retries=3
            ),
            "meupc": ScraperConfig(
                name="MeuPC.net",
                domain="meupc.net",
                function_name="meupc",
                priority=1.1,  # Média prioridade
                max_retries=2
            ),
            "buscape": ScraperConfig(
                name="Buscapé",
                domain="buscape.com.br",
                function_name="buscape",
                priority=1.0,  # Prioridade padrão
                max_retries=2
            ),
            "magalu": ScraperConfig(
                name="Magazine Luiza",
                domain="magazineluiza.com.br",
                function_name="magalu",
                priority=0.9,  # Prioridade menor
                max_retries=2
            )
        }
    
    async def start(self):
        """Inicia o orquestrador"""
        logger.info("🚀 Iniciando Orquestrador Inteligente de Scrapers")
        self.running = True
        self.stats["start_time"] = datetime.now()
        
        # Executa um ciclo inicial forçado
        logger.info("🚀 Executando ciclo inicial forçado...")
        await self.run_cycle_forced()
        
        try:
            while self.running:
                await self.run_cycle()
                await asyncio.sleep(60)  # Aguarda 1 minuto entre ciclos
                
        except KeyboardInterrupt:
            logger.info("👋 Encerrando orquestrador...")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Erro fatal no orquestrador: {e}")
            self.running = False
    
    async def run_cycle(self):
        """Executa um ciclo de scraping"""
        logger.info("🔄 Iniciando ciclo de scraping...")
        
        # Obtém fila de processamento
        queue = self.dps.get_processing_queue()
        
        if not queue:
            logger.info("⏰ Nenhum site disponível para processamento")
            # Aguarda um pouco e tenta novamente
            await asyncio.sleep(30)
            return
        
        # Filtra scrapers habilitados e disponíveis
        available_scrapers = []
        for scraper_id, scraper_config in self.scrapers.items():
            if not scraper_config.enabled:
                continue
            
            # Verifica se o domínio do scraper está na fila de processamento
            if scraper_config.domain in [item["domain"] for item in queue]:
                available_scrapers.append((scraper_id, scraper_config))
                logger.info(f"✅ {scraper_config.name} disponível para execução")
            else:
                logger.debug(f"⏳ {scraper_config.name} não disponível ainda")
        
        if not available_scrapers:
            logger.info("⚠️ Nenhum scraper disponível para execução")
            # Aguarda um pouco e tenta novamente
            await asyncio.sleep(30)
            return
        
        # Ordena por prioridade
        available_scrapers.sort(key=lambda x: x[1].priority, reverse=True)
        
        logger.info(f"🎯 Executando {len(available_scrapers)} scrapers disponíveis")
        
        # Executa scrapers em paralelo (máximo 3 simultâneos)
        semaphore = asyncio.Semaphore(3)
        
        tasks = []
        for scraper_id, scraper_config in available_scrapers:
            task = asyncio.create_task(
                self.execute_scraper_with_semaphore(semaphore, scraper_id, scraper_config)
            )
            tasks.append(task)
        
        # Aguarda conclusão de todos
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa resultados
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌ Erro na execução: {result}")
            elif isinstance(result, ScrapingResult):
                self.process_result(result)
            else:
                logger.warning(f"⚠️ Resultado inesperado: {type(result)}")
        
        # Atualiza estatísticas
        self.update_stats()
        
        # Salva cache
        self.dps.save_cache()
        
        logger.info("✅ Ciclo de scraping concluído")
    
    async def run_cycle_forced(self):
        """Executa um ciclo de scraping forçado (ignora intervalos de tempo)"""
        logger.info("🚀 Executando ciclo inicial forçado...")
        
        # Executa todos os scrapers habilitados
        available_scrapers = []
        for scraper_id, scraper_config in self.scrapers.items():
            if scraper_config.enabled:
                available_scrapers.append((scraper_id, scraper_config))
                logger.info(f"✅ {scraper_config.name} incluído no ciclo inicial")
        
        if not available_scrapers:
            logger.warning("⚠️ Nenhum scraper habilitado para execução")
            return
        
        # Executa scrapers em paralelo (máximo 3 simultâneos)
        semaphore = asyncio.Semaphore(3)
        
        tasks = []
        for scraper_id, scraper_config in available_scrapers:
            task = asyncio.create_task(
                self.execute_scraper_with_semaphore(semaphore, scraper_id, scraper_config)
            )
            tasks.append(task)
        
        # Aguarda conclusão de todos
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa resultados
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌ Erro na execução: {result}")
            elif isinstance(result, ScrapingResult):
                self.process_result(result)
            else:
                logger.warning(f"⚠️ Resultado inesperado: {type(result)}")
        
        # Atualiza estatísticas
        self.update_stats()
        
        # Salva cache
        self.dps.save_cache()
        
        logger.info("✅ Ciclo inicial forçado concluído")
    
    async def execute_scraper_with_semaphore(self, semaphore: asyncio.Semaphore, 
                                           scraper_id: str, scraper_config: ScraperConfig):
        """Executa um scraper com controle de concorrência"""
        async with semaphore:
            return await self.execute_scraper(scraper_id, scraper_config)
    
    async def execute_scraper(self, scraper_id: str, scraper_config: ScraperConfig) -> ScrapingResult:
        """Executa um scraper específico"""
        start_time = time.time()
        logger.info(f"🔍 Executando {scraper_config.name} ({scraper_config.domain})")
        
        try:
            # Executa scraper
            products = await self.run_scraper_function(scraper_config.function_name)
            
            if products:
                # Filtra produtos duplicados
                unique_products = self.dps.filter_duplicate_products(products, scraper_config.domain)
                
                # Marca site como processado
                self.dps.mark_site_processed(scraper_config.domain, len(unique_products))
                
                execution_time = time.time() - start_time
                
                result = ScrapingResult(
                    scraper_name=scraper_config.name,
                    domain=scraper_config.domain,
                    success=True,
                    products_found=len(products),
                    unique_products=len(unique_products),
                    execution_time=execution_time,
                    timestamp=datetime.now()
                )
                
                logger.info(f"✅ {scraper_config.name}: {len(unique_products)} produtos únicos "
                           f"de {len(products)} encontrados em {execution_time:.2f}s")
                
                return result
            else:
                # Nenhum produto encontrado
                self.dps.mark_site_processed(scraper_config.domain, 0)
                
                execution_time = time.time() - start_time
                
                result = ScrapingResult(
                    scraper_name=scraper_config.name,
                    domain=scraper_config.domain,
                    success=True,
                    products_found=0,
                    unique_products=0,
                    execution_time=execution_time,
                    timestamp=datetime.now()
                )
                
                logger.info(f"⚠️ {scraper_config.name}: Nenhum produto encontrado em {execution_time:.2f}s")
                
                return result
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"❌ {scraper_config.name}: Erro - {error_msg}")
            
            # Marca como processado mesmo com erro para evitar loop infinito
            self.dps.mark_site_processed(scraper_config.domain, 0)
            
            result = ScrapingResult(
                scraper_name=scraper_config.name,
                domain=scraper_config.domain,
                success=False,
                products_found=0,
                unique_products=0,
                execution_time=execution_time,
                error_message=error_msg,
                timestamp=datetime.now()
            )
            
            return result
    
    async def run_scraper_function(self, function_name: str) -> List[Dict[str, Any]]:
        """Executa função de scraper específica"""
        try:
            if function_name == "promobit":
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    return await buscar_ofertas_promobit(session)
            elif function_name == "pelando":
                # Usa o scraper com Selenium para o Pelando
                from pelando_scraper_selenium_fixed import buscar_ofertas_pelando_selenium
                return await buscar_ofertas_pelando_selenium()
            elif function_name == "meupc":
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    return await buscar_ofertas_meupc(session)
            elif function_name == "buscape":
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    return await buscar_ofertas_buscape(session)
            elif function_name == "magalu":
                scraper = MagazineLuizaScraper(headless=True)
                return await asyncio.to_thread(scraper.buscar_ofertas, max_paginas=2)
            else:
                logger.warning(f"⚠️ Função de scraper '{function_name}' não implementada")
                return []
                
        except Exception as e:
            logger.error(f"❌ Erro ao executar {function_name}: {e}")
            return []
    
    def process_result(self, result: ScrapingResult):
        """Processa resultado de um scraper"""
        self.results_history.append(result)
        
        # Mantém apenas os últimos 1000 resultados
        if len(self.results_history) > 1000:
            self.results_history = self.results_history[-1000:]
        
        # Atualiza estatísticas
        self.stats["total_executions"] += 1
        
        if result.success:
            self.stats["successful_executions"] += 1
        else:
            self.stats["failed_executions"] += 1
        
        self.stats["total_products_found"] += result.products_found
        self.stats["total_unique_products"] += result.unique_products
        self.stats["last_execution"] = result.timestamp
    
    def update_stats(self):
        """Atualiza estatísticas gerais"""
        if self.stats["start_time"]:
            uptime = datetime.now() - self.stats["start_time"]
            self.stats["uptime"] = str(uptime).split('.')[0]  # Remove microssegundos
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas"""
        stats = self.stats.copy()
        
        # Adiciona estatísticas do sistema anti-duplicidade
        dps_stats = self.dps.get_site_statistics()
        stats["duplicate_prevention"] = dps_stats
        
        # Estatísticas por scraper
        scraper_stats = {}
        for scraper_id, scraper_config in self.scrapers.items():
            scraper_results = [r for r in self.results_history if r.domain == scraper_config.domain]
            
            if scraper_results:
                scraper_stats[scraper_id] = {
                    "total_executions": len(scraper_results),
                    "successful_executions": len([r for r in scraper_results if r.success]),
                    "failed_executions": len([r for r in scraper_results if not r.success]),
                    "total_products_found": sum(r.products_found for r in scraper_results),
                    "total_unique_products": sum(r.unique_products for r in scraper_results),
                    "average_execution_time": sum(r.execution_time for r in scraper_results) / len(scraper_results),
                    "last_execution": max((r.timestamp for r in scraper_results if r.timestamp is not None), default=None) if scraper_results else None
                }
        
        stats["scrapers"] = scraper_stats
        
        return stats
    
    def print_status(self):
        """Imprime status atual do orquestrador"""
        print("\n" + "="*60)
        print("🎯 STATUS DO ORQUESTRADOR INTELIGENTE")
        print("="*60)
        
        # Status geral
        print(f"🔄 Status: {'🟢 Executando' if self.running else '🔴 Parado'}")
        if self.stats["start_time"]:
            print(f"⏰ Iniciado em: {self.stats['start_time'].strftime('%d/%m/%Y %H:%M:%S')}")
            if "uptime" in self.stats:
                print(f"⏱️  Uptime: {self.stats['uptime']}")
        
        print(f"📊 Total de execuções: {self.stats['total_executions']}")
        print(f"✅ Sucessos: {self.stats['successful_executions']}")
        print(f"❌ Falhas: {self.stats['failed_executions']}")
        print(f"📦 Produtos encontrados: {self.stats['total_products_found']}")
        print(f"💎 Produtos únicos: {self.stats['total_unique_products']}")
        
        # Fila de processamento
        print(f"\n🔄 Fila de Processamento:")
        queue = self.dps.get_processing_queue()
        for item in queue:
            print(f"   {item['name']} ({item['domain']}) - Prioridade: {item['priority']:.2f}")
        
        # Status dos scrapers
        print(f"\n🔧 Status dos Scrapers:")
        for scraper_id, scraper_config in self.scrapers.items():
            status = "🟢" if scraper_config.enabled else "🔴"
            print(f"   {status} {scraper_config.name}: {'Habilitado' if scraper_config.enabled else 'Desabilitado'}")
        
        print("="*60)

async def main():
    """Função principal"""
    print("🚀 INICIANDO ORQUESTRADOR INTELIGENTE DE SCRAPERS")
    print("=" * 60)
    
    # Cria orquestrador
    orchestrator = IntelligentScraperOrchestrator()
    
    # Mostra status inicial
    orchestrator.print_status()
    
    try:
        # Inicia orquestrador
        await orchestrator.start()
        
    except KeyboardInterrupt:
        print("\n👋 Encerrando orquestrador...")
        orchestrator.running = False
        
        # Mostra estatísticas finais
        print("\n📊 Estatísticas Finais:")
        final_stats = orchestrator.get_detailed_stats()
        for key, value in final_stats.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for sub_key, sub_value in value.items():
                    print(f"     {sub_key}: {sub_value}")
            else:
                print(f"   {key}: {value}")
    
    print("\n✅ Orquestrador encerrado com sucesso!")

if __name__ == "__main__":
    asyncio.run(main())
