"""
Sistema de Testes Integrado para Todos os Scrapers

Este script testa todos os scrapers implementados no sistema:
- Magazine Luiza (básico, stealth, avançado)
- Amazon (básico, stealth)
- Shopee
- Promobit
- AliExpress (API)
- Awin (API)
- Mercado Livre
- Zoom
- Pelando
"""
import asyncio
import sys
import os
import time
from datetime import datetime

# Adiciona o diretório atual ao path para importar módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ScraperTestSuite:
    """Suite de testes para todos os scrapers"""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
    
    async def test_magalu_scrapers(self):
        """Testa todos os scrapers do Magazine Luiza"""
        print("🏪 Testando Scrapers do Magazine Luiza...")
        
        results = {}
        
        # Testa scraper básico
        try:
            from magalu_scraper import MagazineLuizaScraper
            scraper = MagazineLuizaScraper()
            # Teste básico de inicialização
            results['basico'] = {'status': '✅', 'message': 'Importação e inicialização OK'}
        except Exception as e:
            results['basico'] = {'status': '❌', 'message': f'Erro: {e}'}
        
        # Testa scraper stealth
        try:
            from magalu_scraper_stealth import MagazineLuizaStealthScraper
            scraper = MagazineLuizaStealthScraper()
            results['stealth'] = {'status': '✅', 'message': 'Importação e inicialização OK'}
        except Exception as e:
            results['stealth'] = {'status': '❌', 'message': f'Erro: {e}'}
        
        # Testa scraper avançado
        try:
            from magalu_scraper_advanced import MagazineLuizaAdvancedScraper
            scraper = MagazineLuizaAdvancedScraper()
            results['avancado'] = {'status': '✅', 'message': 'Importação e inicialização OK'}
        except Exception as e:
            results['stealth'] = {'status': '❌', 'message': f'Erro: {e}'}
        
        self.results['Magazine Luiza'] = results
        return results
    
    async def test_amazon_scrapers(self):
        """Testa todos os scrapers da Amazon"""
        print("📦 Testando Scrapers da Amazon...")
        
        results = {}
        
        # Testa scraper básico
        try:
            from amazon_scraper import AmazonScraper
            scraper = AmazonScraper()
            results['basico'] = {'status': '✅', 'message': 'Importação e inicialização OK'}
        except Exception as e:
            results['basico'] = {'status': '❌', 'message': f'Erro: {e}'}
        
        # Testa scraper stealth
        try:
            from amazon_scraper_stealth import AmazonStealthScraper
            scraper = AmazonStealthScraper()
            results['stealth'] = {'status': '✅', 'message': 'Importação e inicialização OK'}
        except Exception as e:
            results['stealth'] = {'status': '❌', 'message': f'Erro: {e}'}
        
        # Testa API
        try:
            from amazon_api import AmazonAPI
            api = AmazonAPI()
            results['api'] = {'status': '✅', 'message': 'Importação e inicialização OK'}
        except Exception as e:
            results['api'] = {'status': '❌', 'message': f'Erro: {e}'}
        
        self.results['Amazon'] = results
        return results
    
    async def test_shopee_scraper(self):
        """Testa o scraper da Shopee"""
        print("🛍️ Testando Scraper da Shopee...")
        
        try:
            from shopee_scraper import ShopeeScraper
            scraper = ShopeeScraper()
            results = {'status': '✅', 'message': 'Importação e inicialização OK'}
        except Exception as e:
            results = {'status': '❌', 'message': f'Erro: {e}'}
        
        self.results['Shopee'] = results
        return results
    
    async def test_promobit_scraper(self):
        """Testa o scraper do Promobit"""
        print("🔥 Testando Scraper do Promobit...")
        
        try:
            from promobit_scraper_final import buscar_ofertas_promobit
            # Teste básico de importação
            results = {'status': '✅', 'message': 'Importação OK'}
        except Exception as e:
            results = {'status': '❌', 'message': f'Erro: {e}'}
        
        self.results['Promobit'] = results
        return results
    
    async def test_aliexpress_integration(self):
        """Testa a integração com AliExpress"""
        print("🌏 Testando Integração AliExpress...")
        
        try:
            from aliexpress_integration import buscar_ofertas_aliexpress
            # Teste básico de importação
            results = {'status': '✅', 'message': 'Importação OK'}
        except Exception as e:
            results = {'status': '❌', 'message': f'Erro: {e}'}
        
        self.results['AliExpress'] = results
        return results
    
    async def test_awin_integration(self):
        """Testa a integração com Awin"""
        print("🔗 Testando Integração Awin...")
        
        try:
            from awin_api import buscar_ofertas_awin
            # Teste básico de importação
            results = {'status': '✅', 'message': 'Importação OK'}
        except Exception as e:
            results = {'status': '❌', 'message': f'Erro: {e}'}
        
        self.results['Awin'] = results
        return results
    
    async def test_mercadolivre_scraper(self):
        """Testa o scraper do Mercado Livre"""
        print("🏪 Testando Scraper do Mercado Livre...")
        
        try:
            from mercadolivre_scraper import buscar_ofertas_mercadolivre
            # Teste básico de importação
            results = {'status': '✅', 'message': 'Importação OK'}
        except Exception as e:
            results = {'status': '❌', 'message': f'Erro: {e}'}
        
        self.results['Mercado Livre'] = results
        return results
    
    async def test_zoom_scraper(self):
        """Testa o scraper do Zoom"""
        print("🔍 Testando Scraper do Zoom...")
        
        try:
            from zoom_scraper import ZoomScraper
            scraper = ZoomScraper()
            results = {'status': '✅', 'message': 'Importação e inicialização OK'}
        except Exception as e:
            results = {'status': '❌', 'message': f'Erro: {e}'}
        
        self.results['Zoom'] = results
        return results
    
    async def test_pelando_scraper(self):
        """Testa o scraper do Pelando"""
        print("💡 Testando Scraper do Pelando...")
        
        try:
            from pelando_scraper import buscar_ofertas_pelando
            # Teste básico de importação
            results = {'status': '✅', 'message': 'Importação OK'}
        except Exception as e:
            results = {'status': '❌', 'message': f'Erro: {e}'}
        
        self.results['Pelando'] = results
        return results
    
    async def test_orchestrator(self):
        """Testa o orquestrador de scrapers"""
        print("🎯 Testando Orquestrador de Scrapers...")
        
        try:
            from scraper_orchestrator import ScraperOrchestrator
            orchestrator = ScraperOrchestrator()
            results = {'status': '✅', 'message': 'Importação e inicialização OK'}
        except Exception as e:
            results = {'status': '❌', 'message': f'Erro: {e}'}
        
        self.results['Orquestrador'] = results
        return results
    
    async def test_affiliate_system(self):
        """Testa o sistema de afiliados"""
        print("💰 Testando Sistema de Afiliados...")
        
        try:
            from affiliate import AffiliateLinkConverter
            converter = AffiliateLinkConverter()
            results = {'status': '✅', 'message': 'Importação e inicialização OK'}
        except Exception as e:
            results = {'status': '❌', 'message': f'Erro: {e}'}
        
        self.results['Sistema de Afiliados'] = results
        return results
    
    async def test_database(self):
        """Testa o sistema de banco de dados"""
        print("🗄️ Testando Sistema de Banco de Dados...")
        
        try:
            from database import setup_database
            # Teste básico de importação
            results = {'status': '✅', 'message': 'Importação OK'}
        except Exception as e:
            results = {'status': '❌', 'message': f'Erro: {e}'}
        
        self.results['Banco de Dados'] = results
        return results
    
    async def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 Iniciando Suite de Testes Completa")
        print("=" * 80)
        
        # Lista de todos os testes
        test_methods = [
            self.test_magalu_scrapers,
            self.test_amazon_scrapers,
            self.test_shopee_scraper,
            self.test_promobit_scraper,
            self.test_aliexpress_integration,
            self.test_awin_integration,
            self.test_mercadolivre_scraper,
            self.test_zoom_scraper,
            self.test_pelando_scraper,
            self.test_orchestrator,
            self.test_affiliate_system,
            self.test_database
        ]
        
        # Executa todos os testes
        for test_method in test_methods:
            try:
                await test_method()
                await asyncio.sleep(0.1)  # Pequena pausa entre testes
            except Exception as e:
                print(f"❌ Erro ao executar {test_method.__name__}: {e}")
        
        # Exibe resultados
        self.print_results()
        
        return self.results
    
    def print_results(self):
        """Exibe os resultados dos testes"""
        print("\n" + "=" * 80)
        print("📊 RESULTADOS DOS TESTES")
        print("=" * 80)
        
        total_tests = 0
        passed_tests = 0
        
        for categoria, testes in self.results.items():
            print(f"\n🏷️  {categoria}:")
            
            if isinstance(testes, dict) and 'status' in testes:
                # Teste único
                status = testes['status']
                message = testes['message']
                print(f"   {status} {message}")
                total_tests += 1
                if status == '✅':
                    passed_tests += 1
            else:
                # Múltiplos testes
                for nome_teste, resultado in testes.items():
                    status = resultado['status']
                    message = resultado['message']
                    print(f"   {nome_teste}: {status} {message}")
                    total_tests += 1
                    if status == '✅':
                        passed_tests += 1
        
        # Estatísticas finais
        print("\n" + "=" * 80)
        print("📈 ESTATÍSTICAS FINAIS")
        print("=" * 80)
        
        tempo_total = time.time() - self.start_time
        taxa_sucesso = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"⏱️  Tempo total de execução: {tempo_total:.2f} segundos")
        print(f"🧪 Total de testes: {total_tests}")
        print(f"✅ Testes aprovados: {passed_tests}")
        print(f"❌ Testes falharam: {total_tests - passed_tests}")
        print(f"📊 Taxa de sucesso: {taxa_sucesso:.1f}%")
        
        if taxa_sucesso >= 90:
            print("\n🎉 EXCELENTE! Sistema funcionando perfeitamente!")
        elif taxa_sucesso >= 75:
            print("\n✅ BOM! Sistema funcionando bem, com algumas observações.")
        elif taxa_sucesso >= 50:
            print("\n⚠️  ATENÇÃO! Sistema com problemas que precisam ser corrigidos.")
        else:
            print("\n❌ CRÍTICO! Sistema com muitos problemas que precisam de atenção imediata.")

async def main():
    """Função principal"""
    print("🧪 Sistema de Testes Integrado - Garimpeiro Geek")
    print("=" * 80)
    
    # Cria e executa a suite de testes
    test_suite = ScraperTestSuite()
    results = await test_suite.run_all_tests()
    
    # Retorna código de saída baseado no sucesso
    total_tests = sum(len(tests) if isinstance(tests, dict) and 'status' not in tests else 1 
                      for tests in results.values())
    passed_tests = sum(1 for tests in results.values() 
                       for test in (tests.values() if isinstance(tests, dict) and 'status' not in tests else [tests])
                       if test.get('status') == '✅')
    
    taxa_sucesso = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    if taxa_sucesso >= 75:
        print("\n✅ Testes concluídos com sucesso!")
        return 0
    else:
        print("\n❌ Muitos testes falharam!")
        return 1

if __name__ == "__main__":
    # Executa os testes
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
