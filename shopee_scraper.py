"""
Scraper para a Shopee Brasil - Coleta ofertas relâmpago usando Selenium
"""

import time
import logging
import re
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
)
from webdriver_manager.chrome import ChromeDriverManager

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShopeeScraper:
    """Scraper para a Shopee Brasil usando Selenium"""

    def __init__(self, headless: bool = True):
        self.base_url = "https://shopee.com.br"
        self.ofertas_url = "https://shopee.com.br/daily-discover"
        self.headless = headless
        self.driver = None

    def setup_driver(self):
        """Configura o driver do Chrome"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")

            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )

            # Desabilita imagens para melhor performance
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("✅ Driver do Chrome configurado com sucesso")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao configurar driver: {e}")
            return False

    def close_driver(self):
        """Fecha o driver do Chrome"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Driver do Chrome fechado")
            except Exception as e:
                logger.error(f"❌ Erro ao fechar driver: {e}")

    def wait_for_page_load(self, timeout: int = 30):
        """Aguarda o carregamento da página"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)  # Aguarda JavaScript carregar (Shopee é mais lento)
            return True
        except TimeoutException:
            logger.warning("⚠️ Timeout aguardando carregamento da página")
            return False

    def scroll_page(self, scroll_pause: float = 3.0):
        """Faz scroll da página para carregar conteúdo dinâmico"""
        try:
            # Scroll para baixo várias vezes para carregar conteúdo lazy
            for i in range(3):
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(scroll_pause)

            # Scroll para cima
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(scroll_pause)

            logger.info("✅ Scroll da página realizado")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao fazer scroll: {e}")
            return False

    def extract_product_info(self, product_element) -> Optional[Dict]:
        """Extrai informações de um produto"""
        try:
            # Tenta diferentes seletores para o título
            titulo = None
            titulo_selectors = [
                "h2",
                "h3",
                "h4",
                '[data-testid="product-title"]',
                ".product-title",
                ".product-name",
                '[class*="title"]',
                '[class*="name"]',
            ]

            for selector in titulo_selectors:
                try:
                    titulo_elem = product_element.find_element(
                        By.CSS_SELECTOR, selector
                    )
                    if titulo_elem:
                        titulo = titulo_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue

            if not titulo:
                # Fallback: procura por qualquer texto que pareça título
                try:
                    titulo_elem = product_element.find_element(
                        By.CSS_SELECTOR, '[class*="title"], [class*="name"]'
                    )
                    if titulo_elem:
                        titulo = titulo_elem.text.strip()
                except NoSuchElementException:
                    pass

            # Extrai preço
            preco = None
            preco_selectors = [
                '[data-testid="price-value"]',
                ".price-value",
                ".price",
                '[class*="price"]',
                '[class*="cost"]',
            ]

            for selector in preco_selectors:
                try:
                    preco_elem = product_element.find_element(By.CSS_SELECTOR, selector)
                    if preco_elem:
                        preco_text = preco_elem.text.strip()
                        # Remove caracteres não numéricos exceto vírgula e ponto
                        preco = re.sub(r"[^\d,.]", "", preco_text)
                        break
                except NoSuchElementException:
                    continue

            # Extrai link do produto
            link = None
            try:
                # Shopee usa URLs com formato específico
                link_elem = product_element.find_element(
                    By.CSS_SELECTOR, 'a[href*="/product/"]'
                )
                if link_elem:
                    link = link_elem.get_attribute("href")
                    if link and not link.startswith("http"):
                        link = urljoin(self.base_url, link)
            except NoSuchElementException:
                pass

            # Extrai imagem
            imagem = None
            try:
                img_elem = product_element.find_element(By.CSS_SELECTOR, "img")
                if img_elem:
                    imagem = img_elem.get_attribute("src")
            except NoSuchElementException:
                pass

            # Extrai desconto
            desconto = None
            desconto_selectors = [
                '[class*="discount"]',
                '[class*="off"]',
                ".badge",
                '[class*="sale"]',
            ]

            for selector in desconto_selectors:
                try:
                    desconto_elem = product_element.find_element(
                        By.CSS_SELECTOR, selector
                    )
                    if desconto_elem:
                        desconto_text = desconto_elem.text.strip()
                        # Extrai números do texto de desconto
                        desconto_match = re.search(r"(\d+)%?", desconto_text)
                        if desconto_match:
                            desconto = int(desconto_match.group(1))
                        break
                except NoSuchElementException:
                    continue

            # Extrai avaliação
            avaliacao = None
            try:
                rating_elem = product_element.find_element(
                    By.CSS_SELECTOR, '[class*="rating"], [class*="star"]'
                )
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    # Extrai números da avaliação
                    rating_match = re.search(r"(\d+\.?\d*)", rating_text)
                    if rating_match:
                        avaliacao = float(rating_match.group(1))
            except NoSuchElementException:
                pass

            # Extrai número de vendas
            vendas = None
            try:
                sales_elem = product_element.find_element(
                    By.CSS_SELECTOR, '[class*="sold"], [class*="sales"]'
                )
                if sales_elem:
                    sales_text = sales_elem.text.strip()
                    # Extrai números das vendas
                    sales_match = re.search(r"(\d+)", sales_text)
                    if sales_match:
                        vendas = int(sales_match.group(1))
            except NoSuchElementException:
                pass

            if titulo and preco:  # Produto válido deve ter pelo menos título e preço
                return {
                    "titulo": titulo,
                    "preco": preco,
                    "link": link,
                    "imagem": imagem,
                    "desconto": desconto,
                    "avaliacao": avaliacao,
                    "vendas": vendas,
                    "loja": "Shopee Brasil",
                    "categoria": "Ofertas Relâmpago",
                }

            return None

        except Exception as e:
            logger.error(f"❌ Erro ao extrair informações do produto: {e}")
            return None

    def buscar_ofertas(self, max_paginas: int = 3) -> List[Dict]:
        """Busca ofertas da Shopee Brasil"""
        ofertas = []

        try:
            if not self.setup_driver():
                return ofertas

            logger.info(f"🔍 Acessando: {self.ofertas_url}")
            self.driver.get(self.ofertas_url)

            if not self.wait_for_page_load():
                logger.warning("⚠️ Página não carregou completamente")

            # Faz scroll para carregar conteúdo dinâmico
            self.scroll_page()

            # Procura por produtos
            logger.info("🔍 Procurando por produtos...")

            # Tenta diferentes seletores para encontrar produtos
            product_selectors = [
                '[data-testid="product-card"]',
                'div[class*="product"]',
                'div[class*="item"]',
                'div[class*="card"]',
                ".product-card",
                ".item-card",
            ]

            produtos_encontrados = []
            for selector in product_selectors:
                try:
                    produtos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if produtos:
                        produtos_encontrados = produtos
                        logger.info(
                            f"✅ Encontrados {len(produtos)} produtos com seletor: {selector}"
                        )
                        break
                except Exception:
                    continue

            if not produtos_encontrados:
                # Fallback: procura por qualquer elemento que contenha link de produto
                try:
                    links_produto = self.driver.find_elements(
                        By.CSS_SELECTOR, 'a[href*="/product/"]'
                    )
                    if links_produto:
                        # Agrupa links por produto pai
                        produtos_encontrados = []
                        for link in links_produto:
                            try:
                                produto_pai = link.find_element(
                                    By.XPATH,
                                    './ancestor::*[contains(@class, "card") or contains(@class, "item") or contains(@class, "product")]',
                                )
                                if (
                                    produto_pai
                                    and produto_pai not in produtos_encontrados
                                ):
                                    produtos_encontrados.append(produto_pai)
                            except NoSuchElementException:
                                continue
                        logger.info(
                            f"✅ Encontrados {len(produtos_encontrados)} produtos via fallback"
                        )
                except Exception as e:
                    logger.warning(f"⚠️ Fallback falhou: {e}")

            # Extrai informações dos produtos
            if produtos_encontrados:
                logger.info(
                    f"📋 Extraindo informações de {len(produtos_encontrados)} produtos..."
                )

                for i, produto in enumerate(produtos_encontrados):
                    try:
                        info_produto = self.extract_product_info(produto)
                        if info_produto:
                            ofertas.append(info_produto)
                            logger.info(
                                f"✅ Produto {i + 1}: {info_produto['titulo'][:50]}..."
                            )
                        else:
                            logger.warning(
                                f"⚠️ Produto {i + 1}: Não foi possível extrair informações"
                            )
                    except Exception as e:
                        logger.error(f"❌ Erro ao processar produto {i + 1}: {e}")
                        continue

                    # Limita o número de produtos para evitar sobrecarga
                    if len(ofertas) >= 50:
                        logger.info("🛑 Limite de 50 produtos atingido")
                        break

            logger.info(f"🎯 Total de ofertas extraídas: {len(ofertas)}")

        except Exception as e:
            logger.error(f"❌ Erro geral na busca de ofertas: {e}")
            import traceback

            traceback.print_exc()

        finally:
            self.close_driver()

        return ofertas


def main():
    """Função principal para teste"""
    scraper = ShopeeScraper(headless=False)  # False para debug
    ofertas = scraper.buscar_ofertas()

    print(f"\n🎯 RESULTADO: {len(ofertas)} ofertas encontradas")
    print("=" * 60)

    for i, oferta in enumerate(ofertas[:5], 1):  # Mostra apenas as primeiras 5
        print(f"\n{i}. {oferta['titulo']}")
        print(f"   💰 Preço: {oferta['preco']}")
        if oferta.get("desconto"):
            print(f"   🏷️ Desconto: {oferta['desconto']}%")
        if oferta.get("avaliacao"):
            print(f"   ⭐ Avaliação: {oferta['avaliacao']}")
        if oferta.get("vendas"):
            print(f"   📊 Vendas: {oferta['vendas']}")
        print(f"   🔗 Link: {oferta.get('link', 'N/A')}")
        print(f"   🏪 Loja: {oferta['loja']}")


# ===== FUNÇÃO COMPATIBILIDADE COM SCRAPER REGISTRY =====

async def get_ofertas(periodo: str = "24h") -> List[Dict[str, Any]]:
    """
    Função de compatibilidade com o scraper registry.
    
    Args:
        periodo: Período para coleta (24h, 7d, 30d, all)
        
    Returns:
        Lista de ofertas encontradas
    """
    try:
        scraper = ShopeeScraper(headless=True)
        ofertas = scraper.buscar_ofertas()
        
        # Adicionar metadados de compatibilidade
        for oferta in ofertas:
            oferta['fonte'] = 'shopee_scraper'
            oferta['periodo'] = periodo
            oferta['timestamp'] = time.time()
        
        return ofertas
        
    except Exception as e:
        logger.error(f"❌ Erro na função get_ofertas: {e}")
        return []

# Configurações para o scraper registry
priority = 60  # Prioridade média-alta
rate_limit = 0.5  # 0.5 requisições por segundo (Shopee é mais restritiva)
description = "Scraper para a Shopee Brasil - Coleta ofertas relâmpago usando Selenium"

if __name__ == "__main__":
    main()
