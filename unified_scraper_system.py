#!/usr/bin/env python3
"""
Sistema Unificado de Scrapers para Múltiplas Lojas
Integra scrapers de diferentes e-commerces em um sistema único
"""

import asyncio
import logging
import time
import json
from typing import List, Dict

# Configuração de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UnifiedScraperSystem:
    """Sistema unificado para gerenciar múltiplos scrapers"""

    def __init__(self):
        self.scrapers = {}
        self.results = {}
        self.status = {}

        # Configurações das lojas
        self.stores_config = {
            "amazon": {
                "enabled": True,
                "priority": 1,
                "categories": ["smartphone", "notebook", "fone de ouvido", "smart tv"],
            },
            "magazine_luiza": {
                "enabled": True,
                "priority": 2,
                "categories": ["smartphone", "notebook", "fone de ouvido", "smart tv"],
            },
            "zoom": {
                "enabled": True,
                "priority": 3,
                "categories": ["smartphone", "notebook", "fone de ouvido", "smart tv"],
            },
            "shopee": {
                "enabled": False,  # Desabilitado devido aos bloqueios
                "priority": 4,
                "categories": ["smartphone", "notebook", "fone de ouvido", "smart tv"],
                "status": "BLOCKED",
            },
        }

    async def initialize_scrapers(self):
        """Inicializa todos os scrapers disponíveis"""
        try:
            logger.info("🚀 Inicializando sistema unificado de scrapers...")

            # Inicializa scrapers baseados em Playwright
            if self.stores_config["amazon"]["enabled"]:
                try:
                    from amazon_integration import AmazonIntegration

                    self.scrapers["amazon"] = AmazonIntegration()
                    logger.info("✅ Scraper da Amazon inicializado")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao inicializar Amazon: {e}")
                    self.stores_config["amazon"]["enabled"] = False

            if self.stores_config["magazine_luiza"]["enabled"]:
                try:
                    from magalu_scraper_stealth import MagazineLuizaStealthScraper

                    self.scrapers["magazine_luiza"] = MagazineLuizaStealthScraper()
                    logger.info("✅ Scraper do Magazine Luiza inicializado")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao inicializar Magazine Luiza: {e}")
                    self.stores_config["magazine_luiza"]["enabled"] = False

            if self.stores_config["zoom"]["enabled"]:
                try:
                    from zoom_scraper import ZoomScraper

                    self.scrapers["zoom"] = ZoomScraper()
                    logger.info("✅ Scraper da Zoom inicializado")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao inicializar Zoom: {e}")
                    self.stores_config["zoom"]["enabled"] = False

            # Status da Shopee
            if not self.stores_config["shopee"]["enabled"]:
                logger.warning("⚠️ Shopee desabilitada devido aos bloqueios anti-bot")
                self.status["shopee"] = "BLOCKED"

            logger.info(f"🎯 Total de scrapers ativos: {len(self.scrapers)}")

        except Exception as e:
            logger.error(f"❌ Erro ao inicializar scrapers: {e}")

    async def run_store_scraper(self, store_name: str, scraper) -> List[Dict]:
        """Executa scraper de uma loja específica"""
        try:
            logger.info(f"🔍 Executando scraper da {store_name}...")

            if hasattr(scraper, "buscar_ofertas_gerais"):
                # Scrapers baseados em Playwright
                ofertas = await scraper.buscar_ofertas_gerais()
            elif hasattr(scraper, "search_products"):
                # Scrapers baseados em requests/BeautifulSoup
                ofertas = await scraper.search_products()
            else:
                logger.warning(f"⚠️ Interface não reconhecida para {store_name}")
                return []

            # Adiciona metadados da loja
            for oferta in ofertas:
                oferta["loja"] = store_name
                oferta["timestamp"] = time.time()

            logger.info(f"✅ {store_name}: {len(ofertas)} ofertas encontradas")
            return ofertas

        except Exception as e:
            logger.error(f"❌ Erro no scraper da {store_name}: {e}")
            self.status[store_name] = "ERROR"
            return []

    async def run_all_scrapers(self) -> Dict[str, List[Dict]]:
        """Executa todos os scrapers ativos"""
        try:
            logger.info("🚀 INICIANDO EXECUÇÃO DE TODOS OS SCRAPERS")
            logger.info("=" * 60)

            all_results = {}

            # Executa scrapers em paralelo
            tasks = []
            for store_name, scraper in self.scrapers.items():
                if self.stores_config[store_name]["enabled"]:
                    task = self.run_store_scraper(store_name, scraper)
                    tasks.append((store_name, task))

            # Executa tarefas
            for store_name, task in tasks:
                try:
                    ofertas = await task
                    all_results[store_name] = ofertas
                    self.status[store_name] = "SUCCESS"

                    # Delay entre lojas para evitar sobrecarga
                    await asyncio.sleep(2)

                except Exception as e:
                    logger.error(f"❌ Erro na execução da {store_name}: {e}")
                    self.status[store_name] = "ERROR"
                    all_results[store_name] = []

            # Status da Shopee
            if not self.stores_config["shopee"]["enabled"]:
                all_results["shopee"] = []
                self.status["shopee"] = "BLOCKED"

            self.results = all_results
            return all_results

        except Exception as e:
            logger.error(f"❌ Erro na execução geral: {e}")
            return {}

    def consolidate_results(self) -> List[Dict]:
        """Consolida resultados de todas as lojas"""
        try:
            all_ofertas = []

            for store_name, ofertas in self.results.items():
                if ofertas:
                    all_ofertas.extend(ofertas)

            # Remove duplicatas baseado no título e loja
            unique_ofertas = []
            seen_combinations = set()

            for oferta in all_ofertas:
                # Cria chave única baseada no título e loja
                key = f"{oferta['titulo'].lower()}_{oferta['loja'].lower()}"

                if key not in seen_combinations:
                    unique_ofertas.append(oferta)
                    seen_combinations.add(key)

            logger.info(
                f"🎯 Total de ofertas únicas consolidadas: {len(unique_ofertas)}"
            )
            return unique_ofertas

        except Exception as e:
            logger.error(f"❌ Erro ao consolidar resultados: {e}")
            return []

    def save_consolidated_results(
        self, ofertas: List[Dict], filename: str = None
    ) -> str:
        """Salva resultados consolidados em arquivo JSON"""
        try:
            if not filename:
                timestamp = int(time.time())
                filename = f"ofertas_consolidadas_{timestamp}.json"

            # Organiza por loja
            organized_results = {}
            for oferta in ofertas:
                loja = oferta["loja"]
                if loja not in organized_results:
                    organized_results[loja] = []
                organized_results[loja].append(oferta)

            # Adiciona metadados
            final_data = {
                "metadata": {
                    "timestamp": time.time(),
                    "total_ofertas": len(ofertas),
                    "lojas_ativas": list(organized_results.keys()),
                    "status_geral": self.status,
                },
                "ofertas_por_loja": organized_results,
                "ofertas_consolidadas": ofertas,
            }

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)

            logger.info(f"💾 Resultados salvos em: {filename}")
            return filename

        except Exception as e:
            logger.error(f"❌ Erro ao salvar resultados: {e}")
            return None

    def generate_status_report(self) -> str:
        """Gera relatório de status do sistema"""
        try:
            report = []
            report.append("📊 RELATÓRIO DE STATUS DO SISTEMA UNIFICADO")
            report.append("=" * 60)

            total_ofertas = sum(len(ofertas) for ofertas in self.results.values())
            report.append(f"🎯 Total de ofertas coletadas: {total_ofertas}")
            report.append(f"🏪 Lojas ativas: {len(self.scrapers)}")
            report.append("")

            for store_name, config in self.stores_config.items():
                status = self.status.get(store_name, "UNKNOWN")
                ofertas_count = len(self.results.get(store_name, []))

                if config["enabled"]:
                    report.append(
                        f"✅ {store_name.upper()}: {ofertas_count} ofertas - Status: {status}"
                    )
                else:
                    report.append(
                        f"❌ {store_name.upper()}: DESABILITADA - Status: {status}"
                    )

            report.append("")
            report.append("📈 Resumo por categoria:")

            # Agrupa ofertas por categoria
            categorias = {}
            for store_name, ofertas in self.results.items():
                for oferta in ofertas:
                    categoria = oferta.get("categoria", "Sem categoria")
                    if categoria not in categorias:
                        categorias[categoria] = 0
                    categorias[categoria] += 1

            for categoria, count in sorted(
                categorias.items(), key=lambda x: x[1], reverse=True
            ):
                report.append(f"   📂 {categoria}: {count} ofertas")

            return "\n".join(report)

        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório: {e}")
            return "Erro ao gerar relatório"

    async def cleanup(self):
        """Limpa recursos dos scrapers"""
        try:
            logger.info("🧹 Limpando recursos dos scrapers...")

            for store_name, scraper in self.scrapers.items():
                try:
                    if hasattr(scraper, "close_browser"):
                        await scraper.close_browser()
                    elif hasattr(scraper, "close"):
                        await scraper.close()
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao limpar {store_name}: {e}")

            logger.info("✅ Limpeza concluída")

        except Exception as e:
            logger.error(f"❌ Erro na limpeza: {e}")


async def main():
    """Função principal para teste do sistema unificado"""
    print("🚀 TESTANDO SISTEMA UNIFICADO DE SCRAPERS")
    print("=" * 60)

    # Cria sistema unificado
    unified_system = UnifiedScraperSystem()

    try:
        # Inicializa scrapers
        await unified_system.initialize_scrapers()

        # Executa todos os scrapers
        results = await unified_system.run_all_scrapers()

        # Consolida resultados
        consolidated_ofertas = unified_system.consolidate_results()

        # Gera relatório
        status_report = unified_system.generate_status_report()
        print(status_report)

        # Salva resultados
        if consolidated_ofertas:
            filename = unified_system.save_consolidated_results(consolidated_ofertas)
            if filename:
                print(f"\n💾 Resultados consolidados salvos em: {filename}")

        # Mostra algumas ofertas de exemplo
        if consolidated_ofertas:
            print("\n🎯 EXEMPLOS DE OFERTAS ENCONTRADAS:")
            print("=" * 60)

            for i, oferta in enumerate(consolidated_ofertas[:5], 1):
                print(f"\n{i}. {oferta['titulo']}")
                print(f"   💰 Preço: {oferta['preco']}")
                print(f"   🏪 Loja: {oferta['loja']}")
                print(f"   📂 Categoria: {oferta.get('categoria', 'N/A')}")
                if oferta.get("link"):
                    print(f"   🔗 Link: {oferta['link'][:80]}...")

    except Exception as e:
        print(f"❌ Erro no sistema unificado: {e}")

    finally:
        # Limpa recursos
        await unified_system.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
