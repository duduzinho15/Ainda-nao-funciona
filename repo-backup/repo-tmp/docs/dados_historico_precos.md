# Sistema de Histórico de Preços - Garimpeiro Geek

Este documento descreve o sistema de coleta, armazenamento e análise de histórico de preços implementado no projeto Garimpeiro Geek.

---

## 📊 Visão Geral

O sistema de histórico de preços é composto por três componentes principais:

1. **Coleta Nativa**: Preços coletados pelos scrapers das lojas ativas
2. **Enriquecimento Externo**: Preços de fontes externas (Zoom e Buscapé)
3. **Agregação e Análise**: Processamento diário para métricas e badges

---

## 🏗️ Arquitetura

### Bancos de Dados

#### `aff_cache.sqlite`
- **Propósito**: Cache de shortlinks e deeplinks
- **Tabela principal**: `shortlinks`
- **Uso**: Evitar regeneração de links de afiliado

#### `analytics.sqlite`
- **Propósito**: Dados de produtos, preços e métricas
- **Tabelas principais**:
  - `products`: Produtos normalizados
  - `price_history`: Histórico nativo de preços
  - `external_price_points`: Preços de fontes externas
  - `price_daily`: Agregados diários nativos
  - `external_price_daily`: Agregados diários externos
  - `perf`: Métricas de performance
  - `offers_posted`: Ofertas publicadas
  - `revenue`: Receita estimada

---

## 🔄 Fluxo de Dados

### 1. Coleta Nativa (`price_collect.py`)

```
Scrapers de Lojas → Objetos Offer → Pipeline de Coleta → Banco Analytics
```

**Processo**:
1. Scrapers retornam objetos `Offer`
2. Pipeline identifica plataforma e loja da URL
3. Upsert em `products` (platform + canonical_url)
4. Inserção em `price_history`
5. Atualização de `last_seen_at`

**Fontes Ativas**:
- **Awin**: KaBuM!, LG, Comfy, Trocafy, Ninja, Samsung
- **Mercado Livre**: shortlink + etiqueta garimpeirogeek
- **Magazine Luiza**: vitrine magazinegarimpeirogeek
- **Amazon**: tag=garimpeirogee-20
- **Shopee**: shortlink via painel + cache
- **AliExpress**: shortlink via portal + cache

### 2. Enriquecimento Externo (`price_enrich.py`)

```
Produtos Recentes → Matching → Scrapers Externos → Banco Analytics
```

**Processo**:
1. Seleção de produtos vistos nos últimos N dias
2. Matching com fontes externas usando `core/matchers.py`
3. Coleta de preços via Zoom e Buscapé
4. Inserção em `external_price_points`
5. Atualização de `external_product_map`

**Fontes Externas**:
- **Zoom**: `www.zoom.com.br`
- **Buscapé**: `www.buscape.com.br`

### 3. Agregação Diária (`price_aggregate.py`)

```
Pontos de Preço → Agregação → Métricas Diárias → Badges
```

**Processo**:
1. Agregação de `price_history` → `price_daily`
2. Agregação de `external_price_points` → `external_price_daily`
3. Cálculo de min/max/média por produto e dia
4. Geração de métricas para dashboard

---

## 🎯 Sistema de Matching

### Estratégias de Matching

#### 1. Matching por EAN/SKU (Confiança: 100%)
- **Prioridade**: Máxima
- **Uso**: Quando disponível, garante match perfeito

#### 2. Matching por Modelo (Confiança: 95%)
- **Prioridade**: Alta
- **Padrões reconhecidos**:
  - `LG34GP63A` → Monitor LG
  - `RTX-3080` → Placa de vídeo
  - `iPhone14` → Smartphone Apple

#### 3. Matching por Título (Confiança: 85%+)
- **Prioridade**: Média
- **Processo**:
  1. Normalização (lowercase, remoção de stop words)
  2. Cálculo de similaridade (SequenceMatcher)
  3. Ajustes por categoria de produto

### Categorias Restritivas

Produtos que precisam de matching mais preciso:
- Cabos, películas, cases, capas
- Protetores, suportes, adaptadores
- Carregadores, fones, mouse, teclado

**Threshold**: 90% de confiança

### Produtos Específicos

Produtos com palavras-chave que ganham bônus:
- iPhone, Samsung, LG, Sony
- ASUS, Lenovo, Dell, HP
- Intel, AMD, NVIDIA
- Corsair, Kingston, Western Digital

**Bônus**: +10% no score de confiança

---

## 🏷️ Sistema de Badges

### Política de Badges

#### "Menor Preço em 90d (interno)"
- **Condição**: Confirmado por `price_daily`
- **Uso**: Quando há histórico interno suficiente

#### "Menor Preço em 90d (interno+externo)"
- **Condição**: Interno e externo concordam
- **Uso**: Máxima confiabilidade

#### "Abaixo da Média (30d)"
- **Condição**: Divergência entre interno e externo
- **Uso**: Quando há discrepância significativa

### Cálculo de Métricas

#### Preço Mínimo
```sql
SELECT MIN(price_cents) FROM price_daily 
WHERE product_id = ? AND day >= date('now', '-90 days')
```

#### Preço Médio
```sql
SELECT AVG(avg_cents) FROM price_daily 
WHERE product_id = ? AND day >= date('now', '-30 days')
```

#### Variação de Preço
```sql
SELECT 
    (MAX(max_cents) - MIN(min_cents)) / MIN(min_cents) * 100 as variation_percent
FROM price_daily 
WHERE product_id = ? AND day >= date('now', '-90 days')
```

---

## 🛡️ Anti-Bot e Rate Limiting

### Estratégias Implementadas

#### 1. User-Agent Rotativo
- Pool de 20+ User-Agents realistas
- Rotação automática entre requisições

#### 2. Delays e Retries
- Delay aleatório: 0.5s - 2.0s entre requisições
- Retry com backoff exponencial: 1s, 2s, 4s
- Máximo de 3 tentativas por requisição

#### 3. Timeouts Configuráveis
- Timeout padrão: 30 segundos
- Timeout de conexão: 10 segundos
- Timeout de leitura: 20 segundos

#### 4. Headers Humanizados
- Accept-Language: pt-BR,pt;q=0.9,en;q=0.8
- Accept-Encoding: gzip, deflate, br
- DNT: 1
- Upgrade-Insecure-Requests: 1

### Respeito aos ToS

- **Não** burlar CAPTCHAs
- **Não** usar endpoints privados
- **Não** fazer scraping agressivo
- **Sim** respeitar robots.txt
- **Sim** usar delays apropriados

---

## 📈 Métricas e Observabilidade

### Métricas Coletadas

#### Performance
- `latency_ms`: Tempo de resposta dos scrapers
- `success`: Taxa de sucesso das coletas
- `error`: Taxa de erro por tipo
- `items_found`: Quantidade de itens encontrados

#### Negócio
- `products_tracked`: Produtos em monitoramento
- `price_points_collected`: Pontos de preço coletados
- `external_matches`: Matches externos bem-sucedidos
- `revenue_estimated`: Receita estimada por plataforma

### Dashboard Flet

#### Toggles de Plataforma
- Awin, Mercado Livre, Magalu, Amazon, Shopee, AliExpress
- Ativar/desativar coleta por plataforma

#### Gráficos
- Preço interno vs externo por produto
- Evolução de preços ao longo do tempo
- Performance dos scrapers

#### KPIs
- Receita Hoje, 7d, 30d
- Produtos com match fraco para revisão
- Taxa de sucesso das coletas

---

## 🔧 Configuração e Execução

### Inicialização dos Bancos

```bash
# Inicializar todos os bancos
python -m src.core.db_init

# Validar schemas existentes
python -m src.core.db_init --validate
```

### Execução dos Pipelines

```bash
# Coleta nativa (rodar junto do pipeline normal)
python -m src.pipelines.price_collect

# Enriquecimento com fontes externas
python -m src.pipelines.price_enrich

# Agregação diária
python -m src.pipelines.price_aggregate
```

### Configurações

#### Variáveis de Ambiente
```bash
# Timeouts (em segundos)
SCRAPER_TIMEOUT=30
SCRAPER_DELAY_MIN=0.5
SCRAPER_DELAY_MAX=2.0

# Thresholds de matching
MATCHER_MIN_CONFIDENCE=0.85
MATCHER_RESTRICTIVE_THRESHOLD=0.90

# Retenção de dados
PRICE_HISTORY_DAYS=90
EXTERNAL_PRICE_DAYS=30
```

---

## 🧪 Testes

### Cobertura de Testes

#### Testes Unitários
- `test_db_schemas.py`: Validação de schemas
- `test_matchers.py`: Sistema de matching
- `test_price_collect.py`: Pipeline de coleta
- `test_price_enrich.py`: Pipeline de enriquecimento
- `test_price_aggregate.py`: Pipeline de agregação

#### Testes de Integração
- Criação e validação de bancos
- Inserção e consulta de dados
- Matching de produtos
- Agregação de métricas

### Execução dos Testes

```bash
# Todos os testes
python -m pytest src/tests/ -v

# Testes específicos
python -m pytest src/tests/test_matchers.py -v
python -m pytest src/tests/test_db_schemas.py -v
```

---

## 🚀 Roadmap e Evoluções

### Fase 1 (Implementado)
- ✅ Schemas dos bancos
- ✅ Sistema de matching
- ✅ Pipeline de coleta nativa
- ✅ Scrapers Zoom e Buscapé
- ✅ Agregação diária básica

### Fase 2 (Planejado)
- 🔄 Cache de HTML para evitar re-scraping
- 🔄 Endpoints JSON para gráficos de preço
- 🔄 Machine Learning para matching automático
- 🔄 Alertas de variação de preço

### Fase 3 (Futuro)
- 📊 Análise de tendências de preço
- 📊 Predição de preços futuros
- 📊 Integração com APIs oficiais
- 📊 Dashboard web avançado

---

## 📚 Referências

### Documentação Técnica
- [Especificação do Projeto](ESPECIFICACAO_GARIMPEIRO_GEEK.md)
- [Regras de Afiliação Awin](config/Regras%20de%20alguma%20afiliações%20na%20Awin.txt)
- [Informações de Geração de Links](config/Informações%20base%20de%20geração%20de%20link.txt)

### Arquivos de Código
- `src/core/db_init.py`: Inicialização dos bancos
- `src/core/matchers.py`: Sistema de matching
- `src/pipelines/price_collect.py`: Coleta de preços
- `src/utils/sqlite_helpers.py`: Helpers do SQLite
- `src/utils/anti_bot.py`: Estratégias anti-bot

### Comandos Úteis
```bash
# Verificar status dos bancos
python -m src.core.db_init --validate

# Executar todos os testes
make test

# Formatação e linting
make fmt && make lint
```

---

## 📞 Suporte

Para dúvidas ou problemas com o sistema de histórico de preços:

1. **Verificar logs**: `src/logs/`
2. **Executar testes**: `python -m pytest src/tests/ -v`
3. **Validar bancos**: `python -m src.core.db_init --validate`
4. **Consultar documentação**: Este arquivo e referências

---

*Última atualização: Agosto 2025*
*Versão do sistema: 1.0.0*

