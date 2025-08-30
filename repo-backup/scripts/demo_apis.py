#!/usr/bin/env python3
"""
Script de demonstração das APIs oficiais implementadas
Mostra funcionalidades de AliExpress, Rakuten, Shopee e Awin
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def demo_aliexpress_api():
    """Demonstra funcionalidades da API AliExpress"""
    try:
        from src.affiliate.aliexpress_api_client import get_aliexpress_client
        
        client = get_aliexpress_client()
        if not client:
            logger.warning("Cliente AliExpress não configurado")
            return
        
        logger.info("🚀 Demonstração AliExpress API")
        logger.info("=" * 50)
        
        # Verificar configuração
        stats = client.get_stats()
        logger.info(f"Configuração: {json.dumps(stats, indent=2, default=str)}")
        
        # Simular busca de produtos (mock)
        logger.info("📱 Simulando busca de produtos...")
        mock_products = [
            {
                "product_id": "1000001234567",
                "title": "Smartphone Android 128GB",
                "price": 899.99,
                "product_url": "https://pt.aliexpress.com/item/1000001234567.html"
            }
        ]
        
        logger.info(f"Produtos encontrados: {len(mock_products)}")
        for product in mock_products:
            logger.info(f"  - {product['title']}: R$ {product['price']:.2f}")
        
        # Simular geração de link
        logger.info("🔗 Simulando geração de link de afiliado...")
        mock_affiliate_url = "https://s.click.aliexpress.com/deeplink?aff_short_key=abc123"
        logger.info(f"Link gerado: {mock_affiliate_url}")
        
        logger.info("✅ Demonstração AliExpress concluída\n")
        
    except Exception as e:
        logger.error(f"Erro na demonstração AliExpress: {e}")


async def demo_rakuten_api():
    """Demonstra funcionalidades da API Rakuten"""
    try:
        from src.affiliate.rakuten_api import get_rakuten_client
        
        client = get_rakuten_client()
        if not client:
            logger.warning("Cliente Rakuten não configurado")
            return
        
        logger.info("🎯 Demonstração Rakuten API")
        logger.info("=" * 50)
        
        # Verificar configuração
        stats = client.get_stats()
        logger.info(f"Configuração: {json.dumps(stats, indent=2, default=str)}")
        
        # Simular deep link
        logger.info("🔗 Simulando geração de deep link...")
        mock_deeplink = "https://click.linksynergy.com/deeplink?id=123&mid=456&murl=https://example.com"
        logger.info(f"Deep link: {mock_deeplink}")
        
        # Simular lista de anunciantes
        logger.info("🏪 Simulando lista de anunciantes...")
        mock_advertisers = [
            {"id": "123", "name": "Loja Exemplo 1", "deep_links": True},
            {"id": "456", "name": "Loja Exemplo 2", "deep_links": True}
        ]
        logger.info(f"Anunciantes com deep links: {len(mock_advertisers)}")
        
        logger.info("✅ Demonstração Rakuten concluída\n")
        
    except Exception as e:
        logger.error(f"Erro na demonstração Rakuten: {e}")


async def demo_shopee_api():
    """Demonstra funcionalidades da API Shopee"""
    try:
        from src.affiliate.shopee_api import get_shopee_client
        
        client = get_shopee_client()
        if not client:
            logger.warning("Cliente Shopee não configurado")
            return
        
        logger.info("🛍️ Demonstração Shopee API")
        logger.info("=" * 50)
        
        # Verificar configuração
        stats = client.get_stats()
        logger.info(f"Configuração: {json.dumps(stats, indent=2, default=str)}")
        
        # Simular criação de shortlink
        logger.info("🔗 Simulando criação de shortlink...")
        mock_shortlink = "https://s.shopee.com.br/abc123"
        logger.info(f"Shortlink: {mock_shortlink}")
        
        # Simular ofertas
        logger.info("📦 Simulando busca de ofertas...")
        mock_offers = [
            {"id": "1", "title": "Produto Shopee 1", "price": 99.99},
            {"id": "2", "title": "Produto Shopee 2", "price": 149.99}
        ]
        logger.info(f"Ofertas encontradas: {len(mock_offers)}")
        
        logger.info("✅ Demonstração Shopee concluída\n")
        
    except Exception as e:
        logger.error(f"Erro na demonstração Shopee: {e}")


async def demo_awin_api():
    """Demonstra funcionalidades da API Awin"""
    try:
        from src.affiliate.awin_api import get_awin_client
        
        client = get_awin_client()
        if not client:
            logger.warning("Cliente Awin não configurado")
            return
        
        logger.info("🔗 Demonstração Awin API")
        logger.info("=" * 50)
        
        # Verificar configuração
        stats = client.get_stats()
        logger.info(f"Configuração: {json.dumps(stats, indent=2, default=str)}")
        
        # Simular geração de link
        logger.info("🔗 Simulando geração de link de afiliado...")
        mock_affiliate_url = "https://www.awin1.com/cread.php?awinmid=123&awinaffid=456&clickref=telegram&p=https://example.com"
        logger.info(f"Link Awin: {mock_affiliate_url}")
        
        # Simular geração em lote
        logger.info("📦 Simulando geração em lote...")
        mock_batch_results = [
            {"advertiserId": "17729", "url": "https://kabum.com.br/product/1", "status": "success"},
            {"advertiserId": "23377", "url": "https://comfy.com.br/product/2", "status": "success"}
        ]
        logger.info(f"Links em lote processados: {len(mock_batch_results)}")
        
        logger.info("✅ Demonstração Awin concluída\n")
        
    except Exception as e:
        logger.error(f"Erro na demonstração Awin: {e}")


async def demo_pipeline_ingestion():
    """Demonstra pipeline de ingestão"""
    try:
        from src.pipelines.ingest_offers_api import APIOfferIngestionPipeline
        
        logger.info("🔄 Demonstração Pipeline de Ingestão")
        logger.info("=" * 50)
        
        # Inicializar pipeline
        pipeline = APIOfferIngestionPipeline()
        
        # Verificar fontes disponíveis
        available_sources = pipeline.get_available_sources()
        logger.info(f"Fontes de API disponíveis: {available_sources}")
        
        # Simular ingestão
        logger.info("📥 Simulando ingestão de ofertas...")
        
        # Mock de ofertas coletadas
        mock_offers = [
            {
                "id": "1",
                "title": "Produto via API 1",
                "price": 199.99,
                "source": "API_ALIEXPRESS"
            },
            {
                "id": "2", 
                "title": "Produto via API 2",
                "price": 299.99,
                "source": "API_RAKUTEN"
            }
        ]
        
        logger.info(f"Ofertas coletadas: {len(mock_offers)}")
        for offer in mock_offers:
            logger.info(f"  - {offer['title']} ({offer['source']}): R$ {offer['price']:.2f}")
        
        # Estatísticas
        stats = pipeline.get_ingestion_stats()
        logger.info(f"Estatísticas de ingestão: {json.dumps(stats, indent=2, default=str)}")
        
        logger.info("✅ Demonstração Pipeline concluída\n")
        
    except Exception as e:
        logger.error(f"Erro na demonstração Pipeline: {e}")


async def demo_pipeline_enrichment():
    """Demonstra pipeline de enriquecimento"""
    try:
        from src.pipelines.enrich_offers_api import APIOfferEnrichmentPipeline
        from src.pipelines.ingest_offers_api import APIOffer
        
        logger.info("✨ Demonstração Pipeline de Enriquecimento")
        logger.info("=" * 50)
        
        # Inicializar pipeline
        pipeline = APIOfferEnrichmentPipeline()
        
        # Mock de ofertas da API
        mock_api_offers = [
            APIOffer(
                id="1",
                title="Smartphone Android",
                price=899.99,
                original_price=999.99,
                discount=100.00,
                image_url="https://example.com/image1.jpg",
                product_url="https://example.com/product1",
                affiliate_url="https://affiliate.example.com/link1",
                store="Loja Exemplo",
                category="Smartphones",
                source="API_ALIEXPRESS",
                collected_at=datetime.now(),
                metadata={"query": "smartphone"}
            ),
            APIOffer(
                id="2",
                title="Notebook Intel",
                price=2499.99,
                original_price=2999.99,
                discount=500.00,
                image_url="https://example.com/image2.jpg",
                product_url="https://example.com/product2",
                affiliate_url="https://affiliate.example.com/link2",
                store="Loja Exemplo 2",
                category="Notebooks",
                source="API_RAKUTEN",
                collected_at=datetime.now(),
                metadata={"query": "notebook"}
            )
        ]
        
        logger.info(f"Ofertas para enriquecimento: {len(mock_api_offers)}")
        
        # Enriquecer ofertas
        enriched_offers = pipeline.enrich_offers_batch(mock_api_offers)
        
        logger.info(f"Ofertas enriquecidas: {len(enriched_offers)}")
        for offer in enriched_offers:
            logger.info(f"  - {offer.title}")
            logger.info(f"    Preço: R$ {offer.price:.2f}")
            logger.info(f"    Desconto: {offer.discount_percentage:.1f}%" if offer.discount_percentage else "    Desconto: N/A")
            logger.info(f"    Frescor: {offer.data_freshness}")
            logger.info(f"    Validação: {offer.validation_status}")
            logger.info(f"    Fonte: {offer.source}")
            logger.info("")  # Linha em branco
        
        # Estatísticas
        stats = pipeline.get_enrichment_stats()
        logger.info(f"Estatísticas de enriquecimento: {json.dumps(stats, indent=2, default=str)}")
        
        logger.info("✅ Demonstração Pipeline de Enriquecimento concluída\n")
        
    except Exception as e:
        logger.error(f"Erro na demonstração Pipeline de Enriquecimento: {e}")


async def demo_configuration():
    """Demonstra configuração das APIs"""
    try:
        from src.core.settings import Settings
        
        logger.info("⚙️ Demonstração Configuração das APIs")
        logger.info("=" * 50)
        
        # Configuração das APIs
        api_config = Settings.get_api_config()
        logger.info("Configuração das APIs:")
        logger.info(json.dumps(api_config, indent=2, default=str))
        
        # APIs disponíveis
        available_apis = Settings.get_available_apis()
        logger.info("\nAPIs disponíveis:")
        logger.info(json.dumps(available_apis, indent=2, default=str))
        
        # Resumo
        enabled_apis = [name for name, enabled in available_apis.items() if enabled]
        logger.info(f"\n📊 Resumo: {len(enabled_apis)} APIs habilitadas")
        for api in enabled_apis:
            logger.info(f"  ✅ {api}")
        
        disabled_apis = [name for name, enabled in available_apis.items() if not enabled]
        if disabled_apis:
            logger.info(f"\n❌ {len(disabled_apis)} APIs desabilitadas:")
            for api in disabled_apis:
                logger.info(f"  ❌ {api}")
        
        logger.info("✅ Demonstração Configuração concluída\n")
        
    except Exception as e:
        logger.error(f"Erro na demonstração Configuração: {e}")


async def main():
    """Função principal da demonstração"""
    logger.info("🎉 INICIANDO DEMONSTRAÇÃO DAS APIS OFICIAIS")
    logger.info("=" * 60)
    logger.info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    logger.info("")  # Linha em branco
    
    try:
        # Demonstrações individuais
        await demo_configuration()
        await demo_aliexpress_api()
        await demo_rakuten_api()
        await demo_shopee_api()
        await demo_awin_api()
        
        # Demonstrações dos pipelines
        await demo_pipeline_ingestion()
        await demo_pipeline_enrichment()
        
        logger.info("🎊 DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        logger.info("=" * 60)
        logger.info("📚 Consulte docs/apis_integracao.md para mais detalhes")
        logger.info("🧪 Execute 'make test-apis' para executar os testes")
        logger.info("⚙️ Execute 'make test-apis-config' para verificar configuração")
        
    except Exception as e:
        logger.error(f"Erro na demonstração: {e}")
        logger.error("Verifique se todas as dependências estão instaladas")
        logger.error("Execute 'pip install -r requirements.txt' se necessário")


if __name__ == "__main__":
    # Executar demonstração
    asyncio.run(main())
