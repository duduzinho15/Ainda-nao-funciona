# 🚀 Melhorias Técnicas do Bot Garimpeiro Geek

Este documento descreve as melhorias técnicas implementadas para otimizar o desempenho, confiabilidade e monitoramento do sistema de recomendações de ofertas.

## 📋 Índice

1. [Sistema de Cache Inteligente](#sistema-de-cache-inteligente)
2. [Rate Limiting Inteligente](#rate-limiting-inteligente)
3. [Monitoramento de Saúde dos Scrapers](#monitoramento-de-saúde-dos-scrapers)
4. [Métricas de Performance em Tempo Real](#métricas-de-performance-em-tempo-real)
5. [Integração e Configuração](#integração-e-configuração)
6. [Comandos de Administração](#comandos-de-administração)
7. [Monitoramento e Alertas](#monitoramento-e-alertas)

## 💾 Sistema de Cache Inteligente

### Características

- **Cache em Memória**: Sistema de cache otimizado com TTL configurável
- **Múltiplos Tipos**: Cache específico para diferentes tipos de dados
- **Persistência**: Backup automático em disco para dados importantes
- **Limpeza Automática**: Remoção automática de itens expirados
- **Métricas**: Estatísticas detalhadas de performance do cache

### Tipos de Cache

1. **Cache Principal** (`cache`)
   - Tamanho máximo: 2000 itens
   - TTL padrão: 30 minutos
   - Limpeza: a cada 5 minutos
   - Persistência: habilitada

2. **Cache HTTP** (`http_cache`)
   - Tamanho máximo: 500 itens
   - TTL padrão: 15 minutos
   - Limpeza: a cada 3 minutos
   - Persistência: desabilitada

3. **Cache de Scrapers** (`scraper_cache`)
   - Tamanho máximo: 1000 itens
   - TTL padrão: 1 hora
   - Limpeza: a cada 10 minutos
   - Persistência: habilitada

### Uso

```python
from cache_system import cache, cached

# Uso direto
cache.set("chave", "valor", ttl=3600)
valor = cache.get("chave")

# Decorator automático
@cached(ttl=1800, key_prefix="scraper")
def buscar_produtos(query):
    # Função será cacheada automaticamente
    pass
```

## 🚦 Rate Limiting Inteligente

### Estratégias Implementadas

1. **Janela Fixa** (`FixedWindowStrategy`)
   - Limite fixo de requisições por janela de tempo
   - Ideal para APIs com limites estáticos

2. **Janela Deslizante** (`SlidingWindowStrategy`)
   - Janela que se move continuamente
   - Mais preciso para controle de tráfego

3. **Adaptativa** (`AdaptiveStrategy`)
   - Ajusta limites baseado no histórico de respostas
   - Reduz automaticamente em caso de erros

4. **Backoff Exponencial** (`ExponentialBackoffStrategy`)
   - Aumenta tempo de espera após falhas
   - Protege contra sobrecarga de serviços

### Configurações por Domínio

- **Amazon**: 20 req/hora (adaptativo)
- **AliExpress**: 50 req/hora (fixo)
- **Magazine Luiza**: 20 req/5min (deslizante)
- **Promobit**: 15 req/5min (adaptativo)
- **Awin**: 200 req/hora (fixo)

### Uso

```python
from rate_limiter import rate_limited, check_rate_limit

# Decorator automático
@rate_limited("amazon")
async def buscar_amazon():
    # Rate limiting aplicado automaticamente
    pass

# Verificação manual
if check_rate_limit("aliexpress"):
    # Executa requisição
    pass
```

## 🏥 Monitoramento de Saúde dos Scrapers

### Verificadores Implementados

1. **Recursos do Sistema**
   - CPU, memória e disco
   - Verificação a cada 30 segundos

2. **Conectividade de Internet**
   - Testa múltiplos serviços
   - Verificação a cada 1 minuto

3. **Banco de Dados**
   - Conexão e queries básicas
   - Verificação a cada 2 minutos

4. **Scrapers Específicos**
   - Amazon, AliExpress, Magazine Luiza, Promobit, Awin
   - Verificação a cada 5 minutos

### Status de Saúde

- **🟢 Healthy**: Funcionando normalmente
- **🟡 Warning**: Problemas menores detectados
- **🔴 Critical**: Problemas graves, intervenção necessária
- **❓ Unknown**: Status não determinado

### Uso

```python
from health_monitor import add_scraper_health_check, get_system_health_summary

# Adiciona verificador personalizado
add_scraper_health_check("meu_scraper", minha_funcao_verificacao, 300)

# Obtém resumo geral
summary = get_system_health_summary()
```

## 📊 Métricas de Performance em Tempo Real

### Tipos de Métricas

1. **Contadores** (`COUNTER`)
   - Valores que só aumentam
   - Ex: total de requisições

2. **Gauges** (`GAUGE`)
   - Valores que podem variar
   - Ex: uso de CPU, memória

3. **Histogramas** (`HISTOGRAM`)
   - Distribuição de valores
   - Ex: tempo de resposta

4. **Timers** (`TIMER`)
   - Medição de duração
   - Ex: tempo de execução de funções

### Métricas Coletadas

- **Sistema**: CPU, memória, disco, rede
- **Aplicação**: Requisições, sucessos, falhas, tempo de resposta
- **Cache**: Hit rate, uso, evictions
- **Rate Limiting**: Taxa de sucesso, bloqueios
- **Saúde**: Uptime dos serviços

### Uso

```python
from performance_metrics import track_performance, record_metric

# Decorator automático
@track_performance("buscar_produtos")
async def buscar_produtos():
    # Métricas coletadas automaticamente
    pass

# Registro manual
record_metric("app.custom_metric", 42.5)
```

## 🔧 Integração e Configuração

### Arquivos de Configuração

- `config_improvements.py`: Configurações centralizadas
- `cache_system.py`: Sistema de cache
- `rate_limiter.py`: Sistema de rate limiting
- `health_monitor.py`: Monitoramento de saúde
- `performance_metrics.py`: Métricas de performance

### Inicialização Automática

Os sistemas são inicializados automaticamente no `main.py`:

```python
# Monitoramento de saúde
start_health_monitoring()

# Coleta de métricas
start_metrics_collection()

# Verificadores de saúde
add_scraper_health_check("amazon_scraper", lambda: True, 300)
```

### Jobs Agendados

- **Limpeza de Cache**: A cada 6 horas
- **Backup de Métricas**: A cada 12 horas
- **Verificações com Rate Limiting**: A cada 2-3 horas

## 👑 Comandos de Administração

### Comandos Disponíveis

1. **`/status`** - Status geral do sistema
   - Saúde dos serviços
   - Estatísticas de cache
   - Métricas de rate limiting

2. **`/metrics`** - Métricas de performance
   - Métricas do sistema
   - Métricas da aplicação
   - Alertas críticos

3. **`/cache`** - Gerenciamento de cache
   - Estatísticas detalhadas
   - Limpeza manual
   - Informações de uso

4. **`/health`** - Saúde dos serviços
   - Status individual de cada serviço
   - Histórico de falhas
   - Tempo desde última verificação

### Exemplos de Uso

```bash
/status          # Mostra status geral
/metrics         # Mostra métricas de performance
/cache stats     # Estatísticas detalhadas do cache
/cache clear     # Limpa todo o cache
/health          # Saúde de todos os serviços
```

## 🚨 Monitoramento e Alertas

### Tipos de Alertas

1. **Alertas de Saúde**
   - Mudanças de status (healthy → warning → critical)
   - Falhas consecutivas
   - Timeouts de verificação

2. **Alertas de Performance**
   - Anomalias detectadas (z-score > 2.0)
   - Métricas acima de thresholds
   - Degradação de performance

3. **Alertas de Rate Limiting**
   - Domínios bloqueados
   - Taxa de bloqueio alta
   - Falhas de requisições

### Notificações

- **Logs**: Todos os alertas são registrados
- **Telegram**: Alertas críticos enviados para admin
- **Callbacks**: Sistema de callbacks para integração externa

### Configuração de Alertas

```python
# Callback para alertas de saúde
health_monitor.add_alert_callback(meu_callback_saude)

# Callback para anomalias de performance
performance_metrics.add_anomaly_callback(meu_callback_anomalia)
```

## 📈 Benefícios das Melhorias

### Performance

- **Cache**: Redução de 60-80% nas requisições repetidas
- **Rate Limiting**: Prevenção de bloqueios e melhor distribuição de carga
- **Métricas**: Identificação rápida de gargalos

### Confiabilidade

- **Monitoramento**: Detecção proativa de problemas
- **Alertas**: Notificação imediata de falhas
- **Saúde**: Visibilidade completa do sistema

### Manutenibilidade

- **Configuração Centralizada**: Fácil ajuste de parâmetros
- **Logs Estruturados**: Debugging e troubleshooting simplificados
- **Métricas Históricas**: Análise de tendências e problemas recorrentes

## 🚀 Como Usar

### 1. Instalação

```bash
pip install -r requirements.txt
```

### 2. Configuração

Edite `config_improvements.py` conforme suas necessidades.

### 3. Execução

```bash
python main.py
```

### 4. Monitoramento

Use os comandos de administração para monitorar o sistema:

```bash
/status    # Status geral
/metrics   # Métricas de performance
/cache     # Gerenciar cache
/health    # Saúde dos serviços
```

## 🔍 Troubleshooting

### Problemas Comuns

1. **Cache não funcionando**
   - Verifique permissões de escrita
   - Confirme configurações em `config_improvements.py`

2. **Rate limiting muito restritivo**
   - Ajuste limites em `RATE_LIMITER_CONFIG`
   - Use estratégias adaptativas para APIs instáveis

3. **Métricas não sendo coletadas**
   - Verifique se `start_metrics_collection()` foi chamado
   - Confirme dependências instaladas (psutil)

4. **Alertas não sendo enviados**
   - Verifique configuração do bot do Telegram
   - Confirme callbacks registrados

### Logs

Todos os sistemas geram logs detalhados:

- **Cache**: `cache_system.log`
- **Rate Limiting**: `rate_limiter.log`
- **Saúde**: `health_monitor.log`
- **Métricas**: `performance_metrics.log`

## 📚 Recursos Adicionais

### Documentação

- [Python Telegram Bot](https://python-telegram-bot.readthedocs.io/)
- [psutil Documentation](https://psutil.readthedocs.io/)
- [SQLite Documentation](https://docs.python.org/3/library/sqlite3.html)

### Exemplos

- `test_cache_system.py`: Testes do sistema de cache
- `test_rate_limiter.py`: Testes do rate limiting
- `test_health_monitor.py`: Testes do monitoramento
- `test_performance_metrics.py`: Testes das métricas

### Suporte

Para dúvidas ou problemas:

1. Verifique os logs do sistema
2. Use os comandos de administração
3. Consulte a documentação
4. Abra uma issue no repositório

---

**🎯 Objetivo**: Transformar o Bot Garimpeiro Geek em um sistema robusto, confiável e de alta performance para recomendações de ofertas.

**🔄 Status**: Implementação completa das melhorias técnicas básicas. Pronto para produção e monitoramento contínuo.
