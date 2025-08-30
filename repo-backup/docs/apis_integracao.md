# 📚 **INTEGRAÇÃO DAS APIS OFICIAIS**

Este documento descreve a implementação das APIs oficiais das redes de afiliados no sistema Garimpeiro Geek.

## 🎯 **APIS IMPLEMENTADAS**

### **1. AliExpress Open Platform**
- **Status**: ✅ **IMPLEMENTADA**
- **Cliente**: `src/affiliate/aliexpress_api_client.py`
- **Autenticação**: HMAC-SHA256 + Access Token
- **Funcionalidades**:
  - Geração de links de afiliado
  - Busca de produtos
  - Produtos em alta
  - Smart match por imagem
  - Detalhes de produto/SKU

### **2. Rakuten Advertising**
- **Status**: ✅ **IMPLEMENTADA**
- **Cliente**: `src/affiliate/rakuten_api.py`
- **Autenticação**: OAuth2 Client Credentials
- **Funcionalidades**:
  - Deep links programáticos
  - Busca de produtos
  - Lista de anunciantes
  - Relatórios de conversão
  - Eventos de tracking

### **3. Shopee Affiliate Open API**
- **Status**: ✅ **IMPLEMENTADA**
- **Cliente**: `src/affiliate/shopee_api.py`
- **Autenticação**: SHA256 + App ID + Secret
- **Funcionalidades**:
  - Criação de shortlinks
  - Lista de ofertas
  - Ofertas por produto/marca
  - Relatórios de conversão
  - Relatórios de validação

### **4. Awin Publisher API**
- **Status**: ✅ **IMPLEMENTADA**
- **Cliente**: `src/affiliate/awin_api.py`
- **Autenticação**: Bearer Token
- **Funcionalidades**:
  - Geração de links de afiliado
  - Geração em lote
  - Product Feed
  - Relatórios de performance

## 🔧 **CONFIGURAÇÃO**

### **Variáveis de Ambiente**

```bash
# AliExpress Open Platform
ALI_APP_KEY=517956
ALI_APP_SECRET=okv8nzEGIvWqV0XxONcN9loPNrYwWDsm
ALI_ACCESS_TOKEN=
ALI_REFRESH_TOKEN=
USE_API_ALIEXPRESS=true

# Rakuten Advertising
RKTN_CLIENT_ID=
RKTN_CLIENT_SECRET=
RKTN_ACCESS_TOKEN=
USE_API_RAKUTEN=false

# Shopee Affiliate Open API
SHOPEE_APP_ID=
SHOPEE_SECRET=
SHOPEE_ACCESS_TOKEN=
USE_API_SHOPEE=false

# Awin Publisher API
AWIN_PUBLISHER_ID=
AWIN_ACCESS_TOKEN=
USE_API_AWIN=false
```

### **Verificação de Configuração**

```bash
# Verificar APIs disponíveis
make test-apis-config

# Verificar configuração via Python
python -c "
from src.core.settings import Settings
print('APIs disponíveis:', Settings.get_available_apis())
print('Configuração completa:', Settings.get_api_config())
"
```

## 🚀 **USO BÁSICO**

### **Inicialização dos Clientes**

```python
from src.affiliate.aliexpress_api_client import get_aliexpress_client
from src.affiliate.rakuten_api import get_rakuten_client
from src.affiliate.shopee_api import get_shopee_client
from src.affiliate.awin_api import get_awin_client

# Clientes configurados automaticamente
aliexpress = get_aliexpress_client()
rakuten = get_rakuten_client()
shopee = get_shopee_client()
awin = get_awin_client()
```

### **Exemplos de Uso**

#### **AliExpress - Geração de Link**

```python
if aliexpress:
    # Gerar link de afiliado
    affiliate_url = await aliexpress.generate_affiliate_link(
        url="https://pt.aliexpress.com/item/123.html",
        tracking_id="telegram"
    )
    print(f"Link gerado: {affiliate_url}")
    
    # Buscar produtos
    products = await aliexpress.search_products(
        query="smartphone",
        limit=20,
        ship_to_country="BR",
        currency="BRL"
    )
    print(f"Produtos encontrados: {len(products)}")
```

#### **Rakuten - Deep Link**

```python
if rakuten:
    # Gerar deep link
    deeplink = await rakuten.build_deeplink(
        advertiser_id="12345",
        url="https://example.com/product",
        sub_id="telegram"
    )
    print(f"Deep link: {deeplink}")
    
    # Listar anunciantes com deep links
    advertisers = await rakuten.list_advertisers(deep_links=True)
    print(f"Anunciantes com deep links: {len(advertisers)}")
```

#### **Shopee - Shortlink**

```python
if shopee:
    # Criar shortlink
    shortlink = await shopee.create_shortlink(
        url="https://shopee.com.br/product/123",
        sub_id="telegram"
    )
    print(f"Shortlink: {shortlink}")
    
    # Obter ofertas
    offers = await shopee.get_offers(
        offer_type="product",
        filters={"keyword": "smartphone"},
        limit=20
    )
    print(f"Ofertas: {len(offers)}")
```

#### **Awin - Link Builder**

```python
if awin:
    # Gerar link de afiliado
    affiliate_url = await awin.generate_link(
        advertiser_id="17729",  # KaBuM
        url="https://kabum.com.br/product/123",
        sub_id="telegram"
    )
    print(f"Link Awin: {affiliate_url}")
    
    # Geração em lote
    batch_links = [
        {"advertiserId": "17729", "url": "https://kabum.com.br/product/1"},
        {"advertiserId": "23377", "url": "https://comfy.com.br/product/2"}
    ]
    results = await awin.generate_batch_links(batch_links)
    print(f"Links gerados: {len(results)}")
```

## 🔄 **PIPELINES DE INGESTÃO**

### **Pipeline de Ingestão**

```python
from src.pipelines.ingest_offers_api import run_api_ingestion

# Executar ingestão completa
offers = await run_api_ingestion(
    queries=["smartphone", "notebook", "headphone"],
    advertiser_ids=["17729", "23377", "33061"]
)

print(f"Total de ofertas coletadas: {len(offers)}")
```

### **Pipeline de Enriquecimento**

```python
from src.pipelines.enrich_offers_api import enrich_api_offers

# Enriquecer ofertas coletadas
enriched_offers = enrich_api_offers(offers)

print(f"Ofertas enriquecidas: {len(enriched_offers)}")
```

## 📊 **ESTATÍSTICAS E MONITORAMENTO**

### **Estatísticas dos Clientes**

```python
# Estatísticas de cada cliente
if aliexpress:
    stats = aliexpress.get_stats()
    print("AliExpress:", stats)

if rakuten:
    stats = rakuten.get_stats()
    print("Rakuten:", stats)

if shopee:
    stats = shopee.get_stats()
    print("Shopee:", stats)

if awin:
    stats = awin.get_stats()
    print("Awin:", stats)
```

### **Estatísticas dos Pipelines**

```python
from src.pipelines.ingest_offers_api import APIOfferIngestionPipeline
from src.pipelines.enrich_offers_api import APIOfferEnrichmentPipeline

# Pipeline de ingestão
ingestion_pipeline = APIOfferIngestionPipeline()
ingestion_stats = ingestion_pipeline.get_ingestion_stats()
print("Ingestão:", ingestion_stats)

# Pipeline de enriquecimento
enrichment_pipeline = APIOfferEnrichmentPipeline()
enrichment_stats = enrichment_pipeline.get_enrichment_stats()
print("Enriquecimento:", enrichment_stats)
```

## 🧪 **TESTES**

### **Execução dos Testes**

```bash
# Testes completos das APIs
make test-apis

# Smoke tests (assinatura/links/auth)
make test-apis-smoke

# Testes específicos
python -m pytest tests/api/test_aliexpress_api.py -v
python -m pytest tests/api/test_rakuten_api.py -v
python -m pytest tests/api/test_shopee_api.py -v
python -m pytest tests/api/test_awin_api.py -v
```

### **Testes de Integração**

```python
# Teste de workflow completo
async def test_full_workflow():
    # Inicializar pipeline
    pipeline = APIOfferIngestionPipeline()
    
    # Executar ingestão
    offers = await pipeline.run_full_ingestion()
    
    # Verificar resultados
    assert len(offers) > 0
    
    # Verificar fontes
    sources = set(offer.source for offer in offers)
    assert "API_ALIEXPRESS" in sources or "API_RAKUTEN" in sources
```

## 🔒 **SEGURANÇA E AUTENTICAÇÃO**

### **AliExpress - HMAC-SHA256**

```python
# Assinatura automática
params = client._prepare_request_params("method.name", {"param": "value"})
# Inclui: method, app_key, timestamp, sign, etc.
```

### **Rakuten - OAuth2**

```python
# Renovação automática de token
await client.refresh_token()
# Headers atualizados automaticamente
```

### **Shopee - SHA256 + Timestamp**

```python
# Assinatura com timestamp
headers = client._prepare_auth_headers(payload)
# Authorization: SHA256 Credential=...,Timestamp=...,Signature=...
```

### **Awin - Bearer Token**

```python
# Token no header Authorization
headers = {"Authorization": f"Bearer {access_token}"}
```

## 📈 **MÉTRICAS E KPIs**

### **Métricas de Performance**

- **Latência por API**: Tempo de resposta médio
- **Taxa de sucesso**: % de requisições bem-sucedidas
- **Limite de rate**: Controle de chamadas por minuto
- **Cache hit rate**: Eficiência do cache local

### **Métricas de Negócio**

- **Ofertas coletadas**: Total por fonte
- **Links válidos**: % de URLs de afiliado válidas
- **Conversões**: Rastreamento via sub-IDs
- **Receita**: Estimativa baseada em clicks

## 🚨 **TRATAMENTO DE ERROS**

### **Estratégias de Retry**

```python
# Retry automático com backoff exponencial
# Timeout configurável por API
# Fallback para scrapers quando API falha
```

### **Logs e Monitoramento**

```python
# Logs estruturados para cada operação
# Métricas de erro por fonte
# Alertas para falhas críticas
```

## 🔄 **INTEGRAÇÃO COM SISTEMA EXISTENTE**

### **Compatibilidade com Scrapers**

- **Fallback automático**: APIs como fonte primária, scrapers como backup
- **Merge inteligente**: Combinação de dados de múltiplas fontes
- **Validação cruzada**: Verificação de preços e disponibilidade

### **Dashboard Flet**

- **Novos KPIs**: Métricas específicas das APIs
- **Status das APIs**: Disponibilidade e performance
- **Comparação de fontes**: API vs Scraper

## 📚 **REFERÊNCIAS**

### **Documentação Oficial**

- **AliExpress**: [Open Platform Documentation](https://open.aliexpress.com/doc.htm)
- **Rakuten**: [Advertising Developers](https://rakutenadvertising.com/developers/)
- **Shopee**: [Affiliate Open API](https://open-api.affiliate.shopee.com.br)
- **Awin**: [Publisher API](https://developers.awin.com/)

### **Exemplos de Implementação**

- **GitHub**: SDKs open-source para AliExpress
- **Stack Overflow**: Soluções para assinatura Shopee
- **Comunidade**: Casos de uso e troubleshooting

## 🎯 **PRÓXIMOS PASSOS**

### **Melhorias Planejadas**

1. **Cache inteligente**: Cache com TTL baseado na fonte
2. **Rate limiting**: Controle automático de chamadas
3. **Métricas avançadas**: Dashboard de performance
4. **Webhooks**: Notificações em tempo real
5. **Testes E2E**: Validação com URLs reais

### **Expansão de Funcionalidades**

1. **APIs adicionais**: Outras redes de afiliados
2. **Machine Learning**: Recomendações inteligentes
3. **Análise de tendências**: Insights de mercado
4. **Automação**: Posting automático de ofertas

---

**📝 Nota**: Esta implementação mantém compatibilidade total com o sistema existente, adicionando capacidades de API sem quebrar funcionalidades de scraping.
