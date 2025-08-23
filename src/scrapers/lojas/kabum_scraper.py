"""
Scraper para KaBuM! - Retorna ofertas no formato Offer padrão
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from urllib.parse import urljoin

from core.models import Offer
from scrapers.base_scraper import BaseScraper


class KabumScraper(BaseScraper):
    """Scraper para KaBuM! com suporte a afiliação Awin"""

    def __init__(self):
        super().__init__(
            name="kabum",
            base_url="https://www.kabum.com.br",
            enabled=True
        )
        self.logger = logging.getLogger("scraper.kabum")

    async def scrape(self, query: str = "", max_results: int = 50) -> List[Offer]:
        """
        Scraping de ofertas KaBuM!
        
        Args:
            query: Termo de busca (opcional)
            max_results: Número máximo de resultados
            
        Returns:
            Lista de objetos Offer
        """
        try:
            # Simulação de scraping para teste E2E
            # Em produção, aqui seria implementado o scraping real
            self.logger.info(f"Scraping KaBuM! - Query: {query}, Max: {max_results}")
            
            # Ofertas de exemplo para teste
            offers = [
                Offer(
                    title="Monitor Gamer Curvo LG Ultragear 34\" Ultrawide 160Hz WQHD",
                    price=Decimal("2499.99"),
                    url="https://www.kabum.com.br/produto/472908/monitor-gamer-curvo-lg-ultragear-lg-34-ultrawide-160hz-wqhd-1ms-displayport-e-hdmi-amd-freesync-premium-hdr10-99-srgb-34gp63a-b",
                    store="KaBuM!",
                    original_price=Decimal("2999.99"),
                    discount_percentage=16.67,
                    description="Monitor gamer curvo 34\" com resolução WQHD e 160Hz",
                    image_url="https://images.kabum.com.br/produtos/fotos/472908/monitor-gamer-curvo-lg-ultragear-lg-34-ultrawide-160hz-wqhd-1ms-displayport-e-hdmi-amd-freesync-premium-hdr10-99-srgb-34gp63a-b_1675784561_m.jpg",
                    category="Monitores",
                    brand="LG",
                    model="34GP63A-B",
                    scraped_at=datetime.now(),
                    affiliate_url="https://www.awin1.com/cread.php?awinmid=17729&awinaffid=2370719&ued=https%3A%2F%2Fwww.kabum.com.br%2Fproduto%2F472908%2Fmonitor-gamer-curvo-lg-ultragear-lg-34-ultrawide-160hz-wqhd-1ms-displayport-e-hdmi-amd-freesync-premium-hdr10-99-srgb-34gp63a-b"
                ),
                Offer(
                    title="SSD Kingston NV2 1TB M.2 2280 NVMe",
                    price=Decimal("199.99"),
                    url="https://www.kabum.com.br/produto/472909/ssd-kingston-nv2-1tb-m2-2280-nvme",
                    store="KaBuM!",
                    original_price=Decimal("299.99"),
                    discount_percentage=33.33,
                    description="SSD NVMe de 1TB com interface M.2",
                    image_url="https://images.kabum.com.br/produtos/fotos/472909/ssd-kingston-nv2-1tb-m2-2280-nvme_1675784562_m.jpg",
                    category="Armazenamento",
                    brand="Kingston",
                    model="NV2",
                    scraped_at=datetime.now(),
                    affiliate_url="https://www.awin1.com/cread.php?awinmid=17729&awinaffid=2370719&ued=https%3A%2F%2Fwww.kabum.com.br%2Fproduto%2F472909%2Fssd-kingston-nv2-1tb-m2-2280-nvme"
                )
            ]
            
            # Limitar resultados conforme solicitado
            offers = offers[:max_results]
            
            self.logger.info(f"Scraping KaBuM! concluído: {len(offers)} ofertas encontradas")
            return offers
            
        except Exception as e:
            self.logger.error(f"Erro no scraping KaBuM!: {e}")
            return []

    def parse_offer(self, raw_data: dict) -> Offer:
        """
        Parseia dados brutos em objeto Offer
        
        Args:
            raw_data: Dados brutos da oferta
            
        Returns:
            Objeto Offer estruturado
        """
        try:
            return Offer(
                title=raw_data.get("title", ""),
                price=Decimal(str(raw_data.get("price", 0))),
                url=raw_data.get("url", ""),
                store=raw_data.get("store", "KaBuM!"),
                original_price=Decimal(str(raw_data.get("original_price", 0))) if raw_data.get("original_price") else None,
                discount_percentage=raw_data.get("discount_percentage"),
                description=raw_data.get("description"),
                image_url=raw_data.get("image_url"),
                category=raw_data.get("category"),
                brand=raw_data.get("brand"),
                model=raw_data.get("model"),
                scraped_at=datetime.now(),
                affiliate_url=raw_data.get("affiliate_url")
            )
        except Exception as e:
            self.logger.error(f"Erro ao parsear oferta KaBuM!: {e}")
            raise

    def get_affiliate_url(self, product_url: str) -> str:
        """
        Gera URL de afiliado Awin para KaBuM!
        
        Args:
            product_url: URL original do produto
            
        Returns:
            URL de afiliado Awin
        """
        try:
            # Parâmetros Awin para KaBuM!
            awin_mid = "17729"  # Merchant ID KaBuM!
            awin_affid = "2370719"  # Affiliate ID
            
            # Codificar URL do produto
            from urllib.parse import quote
            encoded_url = quote(product_url, safe='')
            
            # Construir deeplink Awin
            affiliate_url = f"https://www.awin1.com/cread.php?awinmid={awin_mid}&awinaffid={awin_affid}&ued={encoded_url}"
            
            self.logger.info(f"URL de afiliado KaBuM! gerada: {affiliate_url}")
            return affiliate_url
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar URL de afiliado KaBuM!: {e}")
            return product_url


# Instância global para uso em outros módulos
kabum_scraper = KabumScraper()
