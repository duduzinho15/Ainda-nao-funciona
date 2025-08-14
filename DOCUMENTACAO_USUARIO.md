# 📚 DOCUMENTAÇÃO COMPLETA DO SISTEMA DE RECOMENDAÇÕES DE OFERTAS TELEGRAM

## 🎯 **VISÃO GERAL**

O **Sistema de Recomendações de Ofertas Telegram** é um bot inteligente que monitora múltiplas plataformas de e-commerce, identifica ofertas e promoções em tempo real, e recomenda produtos personalizados baseado nas preferências dos usuários.

## 🚀 **FUNCIONALIDADES PRINCIPAIS**

### **1. Sistema de Cache Inteligente**
- **Cache em Memória**: Reduz requisições repetidas
- **Persistência em Disco**: Mantém dados entre reinicializações
- **TTL Configurável**: Tempo de vida personalizável para diferentes tipos de dados
- **Limpeza Automática**: Remove dados expirados automaticamente

### **2. Rate Limiting Inteligente**
- **Múltiplas Estratégias**: Janela fixa, deslizante, adaptativa
- **Limites por Domínio**: Configurações específicas para cada loja
- **Detecção de Bloqueios**: Identifica e responde a bloqueios automaticamente
- **Backoff Exponencial**: Ajusta automaticamente a frequência de requisições

### **3. Monitoramento de Saúde**
- **Verificações em Tempo Real**: Monitora saúde de todos os serviços
- **Alertas Automáticos**: Notifica sobre problemas detectados
- **Métricas de Performance**: Coleta dados de resposta e disponibilidade
- **Histórico de Problemas**: Mantém registro de incidentes

### **4. Métricas de Performance**
- **Coleta em Tempo Real**: Monitora performance do sistema
- **Detecção de Anomalias**: Identifica problemas automaticamente
- **Dashboard de Métricas**: Visualização em tempo real
- **Persistência de Dados**: Armazena histórico para análise

### **5. Sistema de Categorias de Usuários**
- **Preferências Personalizadas**: Usuários definem categorias de interesse
- **Notificações Inteligentes**: Alerta apenas sobre ofertas relevantes
- **Histórico de Preferências**: Rastreia mudanças ao longo do tempo
- **Recomendações Baseadas em Comportamento**: Sugere categorias similares

### **6. Histórico de Preços**
- **Rastreamento de Preços**: Monitora mudanças de preço ao longo do tempo
- **Análise de Tendências**: Identifica padrões e sazonalidade
- **Alertas de Preço**: Notifica sobre mudanças significativas
- **Estatísticas Avançadas**: Média, mediana, desvio padrão, volatilidade

### **7. Comparador de Preços**
- **Comparação Entre Lojas**: Encontra o melhor preço disponível
- **Algoritmo de Similaridade**: Identifica produtos similares
- **Recomendações Inteligentes**: Sugere alternativas baseadas em preço
- **Histórico de Comparações**: Mantém registro de análises

### **8. Sistema de Reviews**
- **Avaliações de Produtos**: Usuários podem avaliar produtos
- **Moderação de Conteúdo**: Sistema de aprovação para reviews
- **Métricas de Produto**: Rating médio, distribuição de notas
- **Histórico de Reviews**: Rastreia mudanças e ações de moderação

## 👥 **COMANDOS DISPONÍVEIS**

### **Comandos para Todos os Usuários**

#### **`/start`** - Iniciar o Bot
```
Inicia o bot e exibe mensagem de boas-vindas com instruções básicas
```

#### **`/notificacoes`** - Configurar Notificações
```
Configura preferências de notificação:
- Categorias de interesse
- Faixa de preço
- Frequência de notificações
- Lojas preferidas
```

#### **`/favoritos`** - Gerenciar Lojas Favoritas
```
Gerencia lojas favoritas para receber notificações prioritárias
```

#### **`/categorias`** - Configurar Categorias
```
Define categorias de produtos de interesse:
- Eletrônicos
- Informática
- Casa e Jardim
- Moda
- Esportes
- etc.
```

#### **`/historico_preco`** - Ver Histórico de Preços
```
Visualiza histórico de preços de um produto específico:
- Gráfico de evolução
- Estatísticas de preço
- Tendências identificadas
```

#### **`/comparar_preco`** - Comparar Preços
```
Compara preços de um produto entre diferentes lojas:
- Melhor preço disponível
- Alternativas similares
- Recomendações de compra
```

#### **`/review`** - Adicionar Review
```
Adiciona avaliação a um produto:
- Nota de 1 a 5 estrelas
- Comentário detalhado
- Categorias de avaliação
```

#### **`/reviews`** - Ver Reviews de Produto
```
Visualiza todas as avaliações de um produto específico:
- Rating médio
- Distribuição de notas
- Comentários dos usuários
```

#### **`/minhas_reviews`** - Ver Suas Reviews
```
Lista todas as suas avaliações:
- Produtos avaliados
- Notas dadas
- Status das reviews
```

### **Comandos Apenas para Administradores**

#### **`/buscar`** - Forçar Busca por Ofertas
```
Executa busca manual por ofertas em todas as plataformas
```

#### **`/oferta`** - Publicar Oferta Manualmente
```
Publica oferta específica no canal do Telegram
```

#### **`/status`** - Status do Sistema
```
Exibe status geral do sistema:
- Saúde dos serviços
- Performance atual
- Problemas detectados
```

#### **`/metrics`** - Métricas de Performance
```
Mostra métricas detalhadas:
- Cache hit rate
- Tempo de resposta
- Uso de recursos
- Anomalias detectadas
```

#### **`/cache`** - Gerenciar Cache
```
Gerencia sistema de cache:
- Estatísticas de uso
- Limpeza manual
- Configurações
```

#### **`/health`** - Saúde dos Serviços
```
Monitora saúde de todos os serviços:
- Status de cada componente
- Problemas detectados
- Recomendações
```

#### **`/moderar_review`** - Moderar Reviews
```
Modera reviews pendentes:
- Aprovar reviews
- Rejeitar conteúdo inadequado
- Marcar como spam
```

## ⚙️ **CONFIGURAÇÃO DO SISTEMA**

### **Variáveis de Ambiente Necessárias**

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=id_do_canal

# Amazon PA-API (Opcional)
AMAZON_ACCESS_KEY=sua_access_key
AMAZON_SECRET_KEY=sua_secret_key
AMAZON_PARTNER_TAG=seu_partner_tag
AMAZON_REGION=us-east-1

# AliExpress API (Opcional)
ALIEXPRESS_APP_KEY=sua_app_key
ALIEXPRESS_APP_SECRET=sua_app_secret

# Awin API (Opcional)
AWIN_API_TOKEN=seu_token_aqui
AWIN_PUBLISHER_ID=seu_publisher_id

# Administradores
ADMIN_USER_IDS=123456,789012
```

### **Arquivos de Configuração**

#### **`config_improvements.py`**
Configurações centralizadas para todos os sistemas:
- Cache
- Rate Limiting
- Health Monitoring
- Performance Metrics
- Jobs Agendados
- Alertas

#### **`config.py`**
Configurações básicas do sistema:
- Credenciais das APIs
- Configurações do banco de dados
- Configurações do Telegram

## 🗄️ **BANCOS DE DADOS**

### **Estrutura dos Bancos**

#### **1. `cache.db`** - Sistema de Cache
- Dados em cache com TTL
- Estatísticas de uso
- Persistência em disco

#### **2. `health_monitor.db`** - Monitoramento de Saúde
- Histórico de verificações
- Métricas de serviços
- Alertas e incidentes

#### **3. `performance_metrics.db`** - Métricas de Performance
- Métricas em tempo real
- Histórico de performance
- Detecção de anomalias

#### **4. `user_categories.db`** - Categorias de Usuários
- Preferências dos usuários
- Histórico de mudanças
- Notificações configuradas

#### **5. `price_history.db`** - Histórico de Preços
- Pontos de preço ao longo do tempo
- Análise de tendências
- Alertas de preço

#### **6. `price_comparisons.db`** - Comparações de Preço
- Comparações entre lojas
- Produtos similares
- Recomendações

#### **7. `product_reviews.db`** - Reviews de Produtos
- Avaliações dos usuários
- Métricas de produto
- Histórico de moderação

## 🔧 **MANUTENÇÃO E MONITORAMENTO**

### **Logs do Sistema**

#### **Localização dos Logs**
```
logs/
├── bot_YYYYMMDD.log          # Log principal do bot
├── cache_system.log          # Log do sistema de cache
├── rate_limiter.log          # Log do rate limiting
├── health_monitor.log        # Log do monitoramento
├── performance_metrics.log   # Log das métricas
└── ...
```

#### **Níveis de Log**
- **DEBUG**: Informações detalhadas para desenvolvimento
- **INFO**: Informações gerais sobre operações
- **WARNING**: Avisos sobre situações que merecem atenção
- **ERROR**: Erros que não impedem o funcionamento
- **CRITICAL**: Erros críticos que afetam o sistema

### **Jobs Agendados**

#### **Jobs Automáticos**
1. **Limpeza de Cache**: A cada 5 minutos
2. **Backup de Métricas**: A cada hora
3. **Verificação de Saúde**: A cada 2 minutos
4. **Busca de Ofertas**: A cada 6 horas
5. **Atualização de IDs Awin**: A cada 2 horas

#### **Configuração de Jobs**
```python
# Em config_improvements.py
SCHEDULED_JOBS_CONFIG = {
    'cache_cleanup_interval': 300,      # 5 minutos
    'metrics_backup_interval': 3600,    # 1 hora
    'health_check_interval': 120,       # 2 minutos
    'offer_search_interval': 21600,     # 6 horas
    'awin_update_interval': 7200        # 2 horas
}
```

### **Monitoramento de Recursos**

#### **Métricas Coletadas**
- **CPU**: Uso de processador
- **Memória**: Uso de RAM
- **Disco**: Espaço disponível
- **Rede**: I/O de rede
- **Aplicação**: Requisições, tempo de resposta, taxa de sucesso

#### **Alertas Automáticos**
- **Uso de CPU > 80%**: Alerta de alta carga
- **Memória > 90%**: Alerta de memória baixa
- **Disco > 95%**: Alerta de espaço baixo
- **Tempo de resposta > 5s**: Alerta de performance

## 🚨 **RESOLUÇÃO DE PROBLEMAS**

### **Problemas Comuns**

#### **1. Bot Não Responde**
```bash
# Verificar logs
tail -f logs/bot_YYYYMMDD.log

# Verificar status dos serviços
python -c "import main; print('Bot funcionando')"

# Verificar conexão com Telegram
python test_telegram_connection.py
```

#### **2. Cache Lento**
```bash
# Verificar estatísticas do cache
python -c "import cache_system; print(cache_system.cache.get_stats())"

# Limpar cache manualmente
python -c "import cache_system; cache_system.cache.clear()"

# Verificar uso de memória
python -c "import psutil; print(psutil.virtual_memory())"
```

#### **3. Rate Limiting Bloqueando**
```bash
# Verificar estratégias ativas
python -c "import rate_limiter; limiter = rate_limiter.IntelligentRateLimiter(); print(limiter.strategies.keys())"

# Verificar domínios bloqueados
python -c "import rate_limiter; limiter = rate_limiter.IntelligentRateLimiter(); print(limiter.blocked_domains)"
```

#### **4. Banco de Dados Travado**
```bash
# Verificar locks
python -c "import sqlite3; conn = sqlite3.connect('user_categories.db'); print(conn.execute('PRAGMA busy_timeout').fetchone())"

# Recriar banco se necessário
rm user_categories.db
python -c "import user_categories; print('Banco recriado')"
```

### **Comandos de Diagnóstico**

#### **Teste de Integração**
```bash
python test_quick.py
```

#### **Teste de Performance**
```bash
python performance_validation.py
```

#### **Teste de Cache**
```bash
python -c "
import cache_system
cache_system.cache.set('test', 'value', 60)
print('Cache funcionando:', cache_system.cache.get('test') == 'value')
"
```

## 📊 **MÉTRICAS E RELATÓRIOS**

### **Dashboard de Métricas**

#### **Métricas em Tempo Real**
- **Cache Hit Rate**: Taxa de acerto do cache
- **Response Time**: Tempo de resposta médio
- **Error Rate**: Taxa de erros
- **Throughput**: Operações por segundo

#### **Métricas Históricas**
- **Performance ao Longo do Tempo**: Gráficos de tendência
- **Uso de Recursos**: CPU, memória, disco
- **Anomalias Detectadas**: Problemas identificados automaticamente

### **Relatórios Disponíveis**

#### **1. Relatório de Saúde**
- Status de todos os serviços
- Problemas detectados
- Recomendações de ação

#### **2. Relatório de Performance**
- Métricas de throughput
- Tempos de resposta
- Uso de recursos

#### **3. Relatório de Cache**
- Hit rate
- Tamanho do cache
- Operações por segundo

#### **4. Relatório de Rate Limiting**
- Requisições permitidas/bloqueadas
- Estratégias ativas
- Domínios bloqueados

## 🔒 **SEGURANÇA**

### **Controle de Acesso**

#### **Comandos Administrativos**
- Apenas usuários listados em `ADMIN_USER_IDS` podem executar
- Verificação automática de permissões
- Log de todas as ações administrativas

#### **Rate Limiting por Usuário**
- Limites individuais para cada usuário
- Prevenção de spam e abuso
- Detecção de comportamento suspeito

### **Proteção de Dados**

#### **Dados Sensíveis**
- Credenciais nunca são expostas nos logs
- Dados de usuário são criptografados
- Backup automático com criptografia

#### **Auditoria**
- Log de todas as ações importantes
- Histórico de mudanças de configuração
- Rastreamento de problemas

## 🚀 **ESCALABILIDADE**

### **Arquitetura Modular**

#### **Componentes Independentes**
- Cada sistema pode ser escalado independentemente
- Configurações separadas para cada módulo
- Fácil adição de novos recursos

#### **Banco de Dados Distribuído**
- Cada funcionalidade tem seu próprio banco
- Reduz conflitos e locks
- Permite otimizações específicas

### **Performance**

#### **Cache Distribuído**
- Cache em memória para máxima velocidade
- Persistência em disco para durabilidade
- Limpeza automática para controle de memória

#### **Rate Limiting Inteligente**
- Múltiplas estratégias para diferentes cenários
- Ajuste automático baseado em respostas
- Prevenção de bloqueios

## 📈 **ROADMAP FUTURO**

### **Curto Prazo (1-2 meses)**
- ✅ Testes de integração completos
- ✅ Validação de performance em produção
- ✅ Documentação de usuário e administrador
- 🔄 Treinamento da equipe de suporte

### **Médio Prazo (3-6 meses)**
- 🔄 Machine Learning para recomendações personalizadas
- 🔄 API REST para integração com outros sistemas
- 🔄 Dashboard web para administração avançada
- 🔄 Sistema de backup automático dos bancos de dados

### **Longo Prazo (6-12 meses)**
- 🔄 Integração com mais plataformas de e-commerce
- 🔄 Sistema de análise preditiva de preços
- 🔄 App mobile nativo para usuários
- 🔄 Integração com sistemas de pagamento

## 📞 **SUPORTE E CONTATO**

### **Canais de Suporte**
- **Telegram**: @admin_username
- **Email**: suporte@empresa.com
- **Documentação**: Este arquivo + README.md

### **Recursos de Ajuda**
- **Logs do Sistema**: Para diagnóstico técnico
- **Comandos de Teste**: Para verificação de funcionalidades
- **Métricas de Performance**: Para análise de problemas
- **Documentação Técnica**: Para desenvolvedores

---

## 📝 **NOTAS DE VERSÃO**

### **Versão 2.0.0** - Sistema Completo
- ✅ Todas as funcionalidades implementadas
- ✅ Testes de integração passando
- ✅ Performance validada em produção
- ✅ Documentação completa

### **Versão 1.0.0** - Sistema Básico
- ✅ Bot Telegram funcional
- ✅ Scrapers básicos
- ✅ Sistema de notificações

---

**Última Atualização**: 12 de Agosto de 2025  
**Versão**: 2.0.0  
**Status**: ✅ PRONTO PARA PRODUÇÃO
