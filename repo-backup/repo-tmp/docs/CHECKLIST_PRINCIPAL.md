# ✅ Checklist Principal - Garimpeiro Geek

## 🎯 **TAREFAS CRÍTICAS - FASE 1 (1-2 dias)**

### **1. Testes E2E**
- [ ] Criar `tests/e2e/test_affiliates_e2e.py`
- [ ] Implementar asserts para todos os exemplos de links
- [ ] Validar fluxo: URL → conversor → validador → PostingManager
- [ ] Garantir 100% de bloqueio de URLs inválidas
- [ ] Testar deduplicação e rate limiting

### **2. Validação de Bloqueios**
- [ ] Shopee: categorias bloqueadas
- [ ] Mercado Livre: produtos brutos bloqueados
- [ ] Magalu: domínios fora da vitrine bloqueados
- [ ] Amazon: sem ASIN bloqueado
- [ ] AliExpress: produtos brutos bloqueados

### **3. Testes de Conversão**
- [ ] URL bruta → Shortlink (Shopee, ML, AliExpress)
- [ ] Validação de formato (todos os conversores)
- [ ] 100% de sucesso na conversão

---

## 🔥 **TAREFAS CRÍTICAS - FASE 2 (3-4 dias)**

### **4. Message Formatter**
- [ ] Criar `src/posting/message_formatter.py`
- [ ] Templates por plataforma com emojis
- [ ] Título, preço, desconto, cupom, loja, link
- [ ] Mensagens idênticas aos bots de referência

### **5. Scheduler de Postagem**
- [ ] Jobs: collect_offers (90s), enrich_prices (15min)
- [ ] Jobs: post_queue (45s), price_aggregate (30min)
- [ ] Sistema assíncrono com timeouts e backoff
- [ ] Retry automático para jobs falhados

### **6. Bot do Telegram**
- [ ] Comandos: /on, /off, /status, /testpost
- [ ] Modo DRY_RUN para testes
- [ ] Postagem automática no canal
- [ ] Fila de ofertas com moderação

---

## 🎯 **CRITÉRIOS DE ACEITE FINAL**

### **Funcionalidade (100%)**
- [ ] Bot posta automaticamente no canal do Telegram
- [ ] 100% dos links passam na validação de afiliados
- [ ] Dashboard mostra métricas em tempo real
- [ ] Sistema de alertas funciona automaticamente

### **Qualidade (≥95%)**
- [ ] Testes passam com cobertura completa
- [ ] Código segue padrões (type hints, docstrings)
- [ ] Logs estruturados e legíveis
- [ ] Tratamento de erros robusto

### **Performance**
- [ ] Postagem de 1-3 ofertas/minuto
- [ ] Latência < 2s para validação
- [ ] Uptime ≥ 99.9%
- [ ] Cache eficiente

---

## 📅 **CRONOGRAMA RESUMIDO**

- **Dias 1-2**: Fase 1 - Finalização dos Testes
- **Dias 3-5**: Fase 2 - Sistema de Postagem
- **Dias 6-7**: Testes finais e validação

**Total**: 7 dias para 100% funcional
