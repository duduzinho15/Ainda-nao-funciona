# 🚀 Sprint Planning - Semana 1 (Fase 1 e 2)

## 📅 **Informações do Sprint**
- **Sprint**: 1
- **Data**: 16-22 Dezembro 2024
- **Objetivo**: Finalizar testes e implementar sistema de postagem básico
- **Duração**: 7 dias
- **Equipe**: 3-5 desenvolvedores

---

## 🎯 **Objetivos do Sprint**

### **Objetivo Principal**
Implementar e validar o sistema básico de postagem automática com 100% de cobertura de testes.

### **Objetivos Específicos**
1. ✅ Completar todos os testes E2E
2. ✅ Validar bloqueios por plataforma
3. ✅ Implementar message formatter
4. ✅ Configurar scheduler de postagem
5. ✅ Integrar bot do Telegram

---

## 📋 **Backlog do Sprint**

### **FASE 1: FINALIZAÇÃO DOS TESTES (Dias 1-2)**

#### **Epic: Testes E2E**
- **Story**: Implementar testes E2E para validação de afiliados
  - **Tasks**:
    - [ ] Criar `tests/e2e/test_affiliates_e2e.py`
    - [ ] Implementar asserts para todos os exemplos de links
    - [ ] Validar fluxo completo: URL → conversor → validador → PostingManager
    - [ ] Garantir 100% de bloqueio de URLs inválidas
    - [ ] Testar deduplicação e rate limiting
  - **Estimativa**: 8 pontos
  - **Responsável**: Dev 1
  - **Critério de Aceite**: Todos os testes passam, 100% de cobertura

#### **Epic: Validação de Bloqueios**
- **Story**: Validar bloqueios específicos por plataforma
  - **Tasks**:
    - [ ] Shopee: categorias bloqueadas
    - [ ] Mercado Livre: produtos brutos bloqueados
    - [ ] Magalu: domínios fora da vitrine bloqueados
    - [ ] Amazon: sem ASIN bloqueado
    - [ ] AliExpress: produtos brutos bloqueados
  - **Estimativa**: 5 pontos
  - **Responsável**: Dev 2
  - **Critério de Aceite**: 0% de falsos negativos

#### **Epic: Testes de Conversão**
- **Story**: Validar conversão de URLs para shortlinks
  - **Tasks**:
    - [ ] URL bruta → Shortlink: Shopee, ML, AliExpress
    - [ ] Validação de formato: Todos os conversores
    - [ ] Testar fallbacks para conversores offline
  - **Estimativa**: 3 pontos
  - **Responsável**: Dev 3
  - **Critério de Aceite**: 100% de sucesso na conversão

### **FASE 2: SISTEMA DE POSTAGEM (Dias 3-5)**

#### **Epic: Message Formatter**
- **Story**: Implementar formatação completa de mensagens
  - **Tasks**:
    - [ ] Criar `src/posting/message_formatter.py`
    - [ ] Templates por plataforma com emojis
    - [ ] Título, preço, desconto, cupom, loja, link
    - [ ] Validação de campos obrigatórios
  - **Estimativa**: 8 pontos
  - **Responsável**: Dev 1
  - **Critério de Aceite**: Mensagens idênticas aos bots de referência

#### **Epic: Scheduler de Postagem**
- **Story**: Configurar sistema de agendamento automático
  - **Tasks**:
    - [ ] Jobs: collect_offers (90s), enrich_prices (15min)
    - [ ] Jobs: post_queue (45s), price_aggregate (30min)
    - [ ] Sistema assíncrono com timeouts e backoff
    - [ ] Retry automático para jobs falhados
  - **Estimativa**: 8 pontos
  - **Responsável**: Dev 2
  - **Critério de Aceite**: Sistema assíncrono funcionando

#### **Epic: Bot do Telegram**
- **Story**: Implementar integração completa com Telegram
  - **Tasks**:
    - [ ] Comandos: /on, /off, /status, /testpost
    - [ ] Modo DRY_RUN para testes
    - [ ] Postagem automática no canal
    - [ ] Fila de ofertas com moderação
  - **Estimativa**: 8 pontos
  - **Responsável**: Dev 3
  - **Critério de Aceite**: Bot funcional com comandos básicos

---

## 📊 **Estimativas e Capacidade**

### **Capacidade da Equipe**
- **Dev 1**: 40 horas disponíveis
- **Dev 2**: 40 horas disponíveis  
- **Dev 3**: 40 horas disponíveis
- **Total**: 120 horas

### **Estimativas por Epic**
- **Testes E2E**: 16 pontos (16 horas)
- **Validação de Bloqueios**: 5 pontos (5 horas)
- **Testes de Conversão**: 3 pontos (3 horas)
- **Message Formatter**: 8 pontos (8 horas)
- **Scheduler de Postagem**: 8 pontos (8 horas)
- **Bot do Telegram**: 8 pontos (8 horas)
- **Total**: 48 pontos (48 horas)

### **Buffer de Segurança**
- **Buffer**: 20% (24 horas)
- **Total com Buffer**: 72 horas
- **Disponível**: 120 horas
- **Status**: ✅ **CAPACIDADE SUFICIENTE**

---

## 🎯 **Critérios de Aceite por Epic**

### **Epic: Testes E2E**
- [ ] Arquivo `tests/e2e/test_affiliates_e2e.py` criado
- [ ] Todos os exemplos de links reais passam na validação
- [ ] Fluxo completo validado: URL → conversor → validador → PostingManager
- [ ] 100% de bloqueio de URLs inválidas
- [ ] Deduplicação e rate limiting funcionando
- [ ] Cobertura de testes: 100%

### **Epic: Validação de Bloqueios**
- [ ] Shopee: categorias bloqueadas corretamente
- [ ] Mercado Livre: produtos brutos bloqueados
- [ ] Magalu: domínios fora da vitrine bloqueados
- [ ] Amazon: sem ASIN bloqueado
- [ ] AliExpress: produtos brutos bloqueados
- [ ] 0% de falsos negativos

### **Epic: Testes de Conversão**
- [ ] URL bruta → Shortlink funcionando para Shopee, ML, AliExpress
- [ ] Validação de formato para todos os conversores
- [ ] Fallbacks para conversores offline funcionando
- [ ] 100% de sucesso na conversão

### **Epic: Message Formatter**
- [ ] Arquivo `src/posting/message_formatter.py` criado
- [ ] Templates por plataforma implementados
- [ ] Emojis e formatação profissional
- [ ] Validação de campos obrigatórios
- [ ] Mensagens idênticas aos bots de referência

### **Epic: Scheduler de Postagem**
- [ ] Jobs configurados com frequências corretas
- [ ] Sistema assíncrono funcionando
- [ ] Timeouts e backoff implementados
- [ ] Retry automático para jobs falhados
- [ ] Monitoramento de performance funcionando

### **Epic: Bot do Telegram**
- [ ] Comandos /on, /off, /status, /testpost funcionando
- [ ] Modo DRY_RUN implementado
- [ ] Postagem automática no canal funcionando
- [ ] Fila de ofertas com moderação implementada
- [ ] Bot funcional com comandos básicos

---

## 🚨 **Riscos e Mitigações**

### **Risco Alto: Complexidade dos Testes E2E**
- **Descrição**: Testes podem ser mais complexos que estimado
- **Mitigação**: Começar com testes simples e expandir gradualmente
- **Responsável**: Dev 1

### **Risco Médio: Integração com Telegram**
- **Descrição**: API do Telegram pode ter limitações
- **Mitigação**: Implementar fallbacks e tratamento de erros robusto
- **Responsável**: Dev 3

### **Risco Baixo: Scheduler de Postagem**
- **Descrição**: Jobs podem conflitar entre si
- **Mitigação**: Implementar locks e validações de estado
- **Responsável**: Dev 2

---

## 📅 **Cronograma Diário**

### **Dia 1 (Segunda-feira)**
- **Manhã**: Setup do ambiente de testes E2E
- **Tarde**: Implementação dos primeiros testes de validação

### **Dia 2 (Terça-feira)**
- **Manhã**: Finalização dos testes E2E
- **Tarde**: Validação de bloqueios por plataforma

### **Dia 3 (Quarta-feira)**
- **Manhã**: Testes de conversão
- **Tarde**: Início do message formatter

### **Dia 4 (Quinta-feira)**
- **Manhã**: Finalização do message formatter
- **Tarde**: Início do scheduler de postagem

### **Dia 5 (Sexta-feira)**
- **Manhã**: Finalização do scheduler
- **Tarde**: Início da integração com Telegram

### **Dia 6 (Sábado)**
- **Manhã**: Finalização da integração com Telegram
- **Tarde**: Testes de integração

### **Dia 7 (Domingo)**
- **Manhã**: Testes finais e validação
- **Tarde**: Preparação para o próximo sprint

---

## 📊 **Métricas de Sucesso**

### **Quantitativas**
- **Cobertura de testes**: 100%
- **Funcionalidades implementadas**: 6/6
- **Bugs críticos**: 0
- **Performance**: <2s latência

### **Qualitativas**
- **Código limpo**: Seguindo padrões
- **Documentação**: Atualizada
- **Testes**: Robustos e confiáveis
- **Integração**: Funcionando perfeitamente

---

## 🔄 **Daily Standups**

### **Horário**: 9:00 AM (15 minutos)
### **Participantes**: Dev 1, Dev 2, Dev 3
### **Formato**:
1. **O que fiz ontem?**
2. **O que farei hoje?**
3. **Quais impedimentos?**

### **Canais de Comunicação**
- **Slack**: Para comunicação rápida
- **GitHub**: Para issues e pull requests
- **Google Meet**: Para daily standups

---

## 📝 **Definição de Pronto (DoD)**

### **Para cada Epic:**
- [ ] Código implementado e testado
- [ ] Testes unitários passando
- [ ] Code review aprovado
- [ ] Documentação atualizada
- [ ] Deploy em ambiente de teste
- [ ] Validação de funcionalidade

### **Para o Sprint:**
- [ ] Todos os Epics concluídos
- [ ] Testes de integração passando
- [ ] Performance validada
- [ ] Documentação completa
- [ ] Preparação para o próximo sprint

---

## 🎉 **Sprint Review e Retrospectiva**

### **Sprint Review (Domingo - 17:00)**
- **Objetivo**: Demonstrar funcionalidades implementadas
- **Participantes**: Equipe de desenvolvimento + stakeholders
- **Duração**: 1 hora

### **Retrospectiva (Domingo - 18:00)**
- **Objetivo**: Identificar melhorias para o próximo sprint
- **Participantes**: Equipe de desenvolvimento
- **Duração**: 30 minutos

---

## 📚 **Recursos e Referências**

### **Documentação**
- `docs/TAREFAS_DESENVOLVIMENTO.md`
- `docs/ROADMAP.md`
- `README.md`

### **Código de Referência**
- `tests/unit/` - Testes unitários existentes
- `src/affiliate/` - Conversores de afiliados
- `src/core/` - Componentes principais

### **Ferramentas**
- **GitHub**: Versionamento e issues
- **Docker**: Containerização
- **Redis**: Cache e filas
- **Telegram Bot API**: Integração

---

**📝 Nota**: Este documento deve ser atualizado diariamente conforme o progresso do sprint.
