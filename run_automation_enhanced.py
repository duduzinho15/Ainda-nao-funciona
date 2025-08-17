"""
Script de Execução Automática Aprimorado - Garimpeiro Geek

Este script executa todos os scrapers de forma coordenada e inteligente:
- Execução paralela quando possível
- Tratamento de erros robusto
- Logs detalhados
- Relatórios de performance
- Integração com o bot do Telegram
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import sys
import os

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'automation_enhanced_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger('automation_enhanced')

class EnhancedAutomationRunner:
    """Executor automático aprimorado para todos os scrapers"""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        self.total_ofertas = 0
        self.errors = []
        
        # Configuração dos scrapers
        self.scrapers_config = {
            'Magazine Luiza': {
                'enabled': True,
                'priority': 1,
                'max_ofertas': 30,
                'min_desconto': 15,
                'timeout': 300  # 5 minutos
            },
            'Amazon': {
                'enabled': True,
                'priority': 2,
                'max_ofertas': 25,
                'min_desconto': 20,
                'timeout': 300
            },
            'Shopee': {
                'enabled': True,
                'priority': 3,
                'max_ofertas': 20,
                'min_desconto': 15,
                'timeout': 240
            },
            'Promobit': {
                'enabled': True,
                'priority': 4,
                'max_ofertas': 25,
                'min_desconto': 10,
                'timeout': 180
            },
            'AliExpress': {
                'enabled': True,
                'priority': 5,
                'max_ofertas': 20,
                'min_desconto': 25,
                'timeout': 300
            },
            'Awin': {
                'enabled': True,
                'priority': 6,
                'max_ofertas': 15,
                'min_desconto': 20,
                'timeout': 240
            },
            'Mercado Livre': {
                'enabled': True,
                'priority': 7,
                'max_ofertas': 25,
                'min_desconto': 15,
                'timeout': 300
            },
            'Zoom': {
                'enabled': True,
                'priority': 8,
                'max_ofertas': 15,
                'min_desconto': 15,
                'timeout': 180
            },
            'Pelando': {
                'enabled': True,
                'priority': 9,
                'max_ofertas': 20,
                'min_desconto': 10,
                'timeout': 180
            }
        }
    
    async def run_magalu_scraper(self) -> Dict[str, Any]:
        """Executa o scraper do Magazine Luiza"""
        try:
            logger.info("🏪 Iniciando scraper Magazine Luiza...")
            
            from magalu_scraper_advanced import MagazineLuizaAdvancedScraper
            
            scraper = MagazineLuizaAdvancedScraper(headless=True)
            await scraper.initialize()
            
            # Busca ofertas em categorias específicas
            categorias = ['informatica', 'componentes_pc', 'setup_gamer', 'games']
            ofertas = await scraper.buscar_ofertas_categorias(
                categorias=categorias,
                max_paginas=2,
                min_desconto=self.scrapers_config['Magazine Luiza']['min_desconto']
            )
            
            await scraper.cleanup()
            
            logger.info(f"✅ Magazine Luiza: {len(ofertas)} ofertas encontradas")
            return {
                'status': 'success',
                'ofertas': ofertas,
                'count': len(ofertas),
                'execution_time': time.time() - self.start_time
            }
            
        except Exception as e:
            error_msg = f"Erro no scraper Magazine Luiza: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return {
                'status': 'error',
                'error': str(e),
                'ofertas': [],
                'count': 0
            }
    
    async def run_amazon_scraper(self) -> Dict[str, Any]:
        """Executa o scraper da Amazon"""
        try:
            logger.info("📦 Iniciando scraper Amazon...")
            
            from amazon_scraper_stealth import AmazonStealthScraper
            
            scraper = AmazonStealthScraper(headless=True)
            await scraper.initialize()
            
            # Busca ofertas em categorias específicas
            categorias = ['electronics', 'computers', 'gaming']
            ofertas = await scraper.buscar_ofertas_categorias(
                categorias=categorias,
                max_paginas=2,
                min_desconto=self.scrapers_config['Amazon']['min_desconto']
            )
            
            await scraper.cleanup()
            
            logger.info(f"✅ Amazon: {len(ofertas)} ofertas encontradas")
            return {
                'status': 'success',
                'ofertas': ofertas,
                'count': len(ofertas),
                'execution_time': time.time() - self.start_time
            }
            
        except Exception as e:
            error_msg = f"Erro no scraper Amazon: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return {
                'status': 'error',
                'error': str(e),
                'ofertas': [],
                'count': 0
            }
    
    async def run_promobit_scraper(self) -> Dict[str, Any]:
        """Executa o scraper do Promobit"""
        try:
            logger.info("🔥 Iniciando scraper Promobit...")
            
            from promobit_scraper import buscar_ofertas_promobit

            ofertas = await buscar_ofertas_promobit(
                max_paginas=3,
                min_desconto=self.scrapers_config['Promobit']['min_desconto']
            )
            
            logger.info(f"✅ Promobit: {len(ofertas)} ofertas encontradas")
            return {
                'status': 'success',
                'ofertas': ofertas,
                'count': len(ofertas),
                'execution_time': time.time() - self.start_time
            }
            
        except Exception as e:
            error_msg = f"Erro no scraper Promobit: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return {
                'status': 'error',
                'error': str(e),
                'ofertas': [],
                'count': 0
            }
    
    async def run_mercadolivre_scraper(self) -> Dict[str, Any]:
        """Executa o scraper do Mercado Livre"""
        try:
            logger.info("🏪 Iniciando scraper Mercado Livre...")
            
            from mercadolivre_scraper import buscar_ofertas_mercadolivre
            
            ofertas = await buscar_ofertas_mercadolivre(
                max_ofertas=self.scrapers_config['Mercado Livre']['max_ofertas'],
                min_desconto=self.scrapers_config['Mercado Livre']['min_desconto'],
                categorias=['informatica', 'games', 'eletronicos'],
                palavras_chave=['notebook gamer', 'placa de video', 'smartphone']
            )
            
            logger.info(f"✅ Mercado Livre: {len(ofertas)} ofertas encontradas")
            return {
                'status': 'success',
                'ofertas': ofertas,
                'count': len(ofertas),
                'execution_time': time.time() - self.start_time
            }
            
        except Exception as e:
            error_msg = f"Erro no scraper Mercado Livre: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return {
                'status': 'error',
                'error': str(e),
                'ofertas': [],
                'count': 0
            }
    
    async def run_awin_integration(self) -> Dict[str, Any]:
        """Executa a integração com Awin"""
        try:
            logger.info("🔗 Iniciando integração Awin...")
            
            from awin_api import buscar_ofertas_awin
            
            ofertas = await buscar_ofertas_awin(
                max_ofertas=self.scrapers_config['Awin']['max_ofertas'],
                min_desconto=self.scrapers_config['Awin']['min_desconto']
            )
            
            logger.info(f"✅ Awin: {len(ofertas)} ofertas encontradas")
            return {
                'status': 'success',
                'ofertas': ofertas,
                'count': len(ofertas),
                'execution_time': time.time() - self.start_time
            }
            
        except Exception as e:
            error_msg = f"Erro na integração Awin: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return {
                'status': 'error',
                'error': str(e),
                'ofertas': [],
                'count': 0
            }
    
    async def run_aliexpress_integration(self) -> Dict[str, Any]:
        """Executa a integração com AliExpress"""
        try:
            logger.info("🌏 Iniciando integração AliExpress...")
            
            from aliexpress_integration import buscar_ofertas_aliexpress
            
            # Palavras-chave para busca
            palavras_chave = ['smartphone', 'notebook', 'gaming', 'tech']
            todas_ofertas = []
            
            for palavra in palavras_chave:
                ofertas = await buscar_ofertas_aliexpress(
                    palavra_chave=palavra,
                    max_resultados=5
                )
                if ofertas:
                    todas_ofertas.extend(ofertas)
            
            logger.info(f"✅ AliExpress: {len(todas_ofertas)} ofertas encontradas")
            return {
                'status': 'success',
                'ofertas': todas_ofertas,
                'count': len(todas_ofertas),
                'execution_time': time.time() - self.start_time
            }
            
        except Exception as e:
            error_msg = f"Erro na integração AliExpress: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return {
                'status': 'error',
                'error': str(e),
                'ofertas': [],
                'count': 0
            }
    
    async def run_all_scrapers(self) -> Dict[str, Any]:
        """Executa todos os scrapers de forma coordenada"""
        logger.info("🚀 Iniciando execução automática de todos os scrapers...")
        
        # Lista de tarefas para execução
        tasks = [
            self.run_magalu_scraper(),
            self.run_amazon_scraper(),
            self.run_promobit_scraper(),
            self.run_mercadolivre_scraper(),
            self.run_awin_integration(),
            self.run_aliexpress_integration()
        ]
        
        # Executa todas as tarefas
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa resultados
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Tarefa {i} falhou com exceção: {result}")
                self.errors.append(f"Tarefa {i}: {result}")
            else:
                self.results[list(self.scrapers_config.keys())[i]] = result
                if result['status'] == 'success':
                    self.total_ofertas += result['count']
        
        return self.results
    
    def generate_report(self) -> str:
        """Gera relatório detalhado da execução"""
        end_time = time.time()
        execution_time = end_time - self.start_time
        
        report = f"""
📊 RELATÓRIO DE EXECUÇÃO AUTOMÁTICA - GARIMPEIRO GEEK
{'='*80}

⏱️  Tempo total de execução: {execution_time:.2f} segundos
📦 Total de ofertas encontradas: {self.total_ofertas}
🏪 Scrapers executados: {len(self.results)}
❌ Erros encontrados: {len(self.errors)}

📋 RESULTADOS POR SCRAPER:
{'-'*50}
"""
        
        for scraper_name, result in self.results.items():
            if result['status'] == 'success':
                report += f"✅ {scraper_name}: {result['count']} ofertas\n"
            else:
                report += f"❌ {scraper_name}: {result.get('error', 'Erro desconhecido')}\n"
        
        if self.errors:
            report += f"\n🚨 ERROS ENCONTRADOS:\n{'-'*30}\n"
            for error in self.errors:
                report += f"• {error}\n"
        
        report += f"\n🎯 ESTATÍSTICAS:\n{'-'*30}\n"
        report += f"• Taxa de sucesso: {(len([r for r in self.results.values() if r['status'] == 'success']) / len(self.results) * 100):.1f}%\n"
        report += f"• Ofertas por minuto: {(self.total_ofertas / (execution_time / 60)):.1f}\n"
        report += f"• Tempo médio por scraper: {(execution_time / len(self.results)):.1f}s\n"
        
        return report
    
    async def save_to_database(self):
        """Salva as ofertas encontradas no banco de dados"""
        try:
            logger.info("💾 Salvando ofertas no banco de dados...")
            
            from database import adicionar_oferta
            
            ofertas_salvas = 0
            for scraper_name, result in self.results.items():
                if result['status'] == 'success' and result['ofertas']:
                    for oferta in result['ofertas']:
                        try:
                            # Adiciona informações do scraper
                            oferta['fonte'] = f"{scraper_name} - {oferta.get('fonte', 'Automation')}"
                            
                            # Salva no banco
                            success = adicionar_oferta(
                                id_produto=oferta['id_produto'],
                                loja=oferta['loja'],
                                titulo=oferta['titulo'],
                                preco=oferta['preco'],
                                preco_original=oferta.get('preco_original'),
                                url_produto=oferta['url_produto'],
                                url_afiliado=oferta['url_afiliado'],
                                url_imagem=oferta.get('url_imagem'),
                                fonte=oferta['fonte']
                            )
                            
                            if success:
                                ofertas_salvas += 1
                                
                        except Exception as e:
                            logger.warning(f"Erro ao salvar oferta: {e}")
                            continue
            
            logger.info(f"✅ {ofertas_salvas} ofertas salvas no banco de dados")
            return ofertas_salvas
            
        except Exception as e:
            logger.error(f"Erro ao salvar no banco de dados: {e}")
            return 0

async def main():
    """Função principal"""
    print("🚀 Execução Automática Aprimorada - Garimpeiro Geek")
    print("=" * 80)
    
    # Cria e executa o runner
    runner = EnhancedAutomationRunner()
    
    try:
        # Executa todos os scrapers
        results = await runner.run_all_scrapers()
        
        # Gera relatório
        report = runner.generate_report()
        print(report)
        
        # Salva no banco de dados
        ofertas_salvas = await runner.save_to_database()
        print(f"\n💾 Ofertas salvas no banco: {ofertas_salvas}")
        
        # Salva relatório em arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"relatorio_automacao_{timestamp}.txt", "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\n📄 Relatório salvo em: relatorio_automacao_{timestamp}.txt")
        
        return 0
        
    except Exception as e:
        logger.error(f"Erro crítico na execução: {e}")
        print(f"\n❌ ERRO CRÍTICO: {e}")
        return 1

if __name__ == "__main__":
    # Executa a automação
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
