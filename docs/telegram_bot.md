# 🤖 **Bot do Telegram - Garimpeiro Geek**

## 🎯 **Visão Geral**

O **Garimpeiro Geek Bot** é um sistema completo de postagem automática de ofertas no Telegram, similar aos bots de ofertas como [@SamuelF3lipePromo](https://t.me/SamuelF3lipePromo) e [@bizoi_ofertas](https://t.me/bizoi_ofertas).

## ✨ **Funcionalidades Principais**

### **🔄 Sistema de Postagem Automática**
- ✅ **Validação automática** de links de afiliados
- ✅ **Postagem imediata** ou **agendada**
- ✅ **Fila de ofertas** com moderação
- ✅ **Integração completa** com PostingManager

### **📱 Comandos do Bot**
- `/start` - Inicia o bot e mostra comandos disponíveis
- `/help` - Ajuda e instruções de uso
- `/status` - Status do sistema e métricas
- `/post` - Posta oferta imediatamente
- `/schedule` - Agenda post para depois
- `/queue` - Mostra fila de ofertas
- `/approve` - Aprova oferta pendente
- `/reject` - Rejeita oferta

### **⏰ Sistema de Agendamento**
- **1 hora** - Post em 1 hora
- **3 horas** - Post em 3 horas  
- **6 horas** - Post em 6 horas
- **Amanhã 9h** - Post às 9h do dia seguinte
- **Amanhã 18h** - Post às 18h do dia seguinte

## 🚀 **Como Funciona**

### **1. Recebimento de Ofertas**
```
👤 Admin envia link → 🤖 Bot processa → ✅ Valida com PostingManager → 📋 Adiciona à fila
```

### **2. Validação Automática**
- **Detecção de plataforma** (Amazon, Shopee, ML, etc.)
- **Validação de afiliados** (formato correto, tracking)
- **Bloqueio de URLs inválidas** (categorias, produtos brutos)
- **Métricas em tempo real** (sucessos, falhas, bloqueios)

### **3. Postagem no Canal**
- **Formatação automática** com emojis e botões
- **Botões inline** para ver oferta e compartilhar
- **Tracking de métricas** (cliques, avaliações)
- **Logs completos** de todas as ações

## 🔧 **Configuração**

### **1. Criar Bot no Telegram**
```bash
# 1. Fale com @BotFather no Telegram
# 2. Use /newbot
# 3. Escolha nome e username
# 4. Copie o token fornecido
```

### **2. Configurar Arquivo de Configuração**
```python
# src/core/config.py
TELEGRAM_BOT_TOKEN = "SEU_TOKEN_AQUI"
TELEGRAM_CHANNEL_ID = "@seu_canal_ofertas"
TELEGRAM_ADMIN_IDS = [123456789, 987654321]  # Seus IDs de admin
```

### **3. Instalar Dependências**
```bash
make install
# ou
pip install python-telegram-bot
```

### **4. Iniciar o Bot**
```bash
make bot-start
# ou
python scripts/start_bot.py
```

## 📊 **Estrutura das Mensagens**

### **Formato de Oferta**
```
🔥 **OFERTA IMPERDÍVEL!** 🔥

🛒 **AMAZON**

🔗 **Link:** https://amzn.to/...

📝 **Descrição:** Oferta especial selecionada pelo Garimpeiro Geek!

⏰ **Válida até:** 15/01/2025 14:30

💡 **Dica:** Clique no link para aproveitar!

---
🤖 *Postado automaticamente pelo @garimpeirogeek_bot*
```

### **Botões Inline**
- **🛒 Ver Oferta** - Link direto para a oferta
- **📱 Canal** - Link para o canal principal
- **⭐️ Avaliar** - Sistema de avaliação
- **📤 Compartilhar** - Compartilhamento da oferta

## 🏪 **Plataformas Suportadas**

| Plataforma | Emoji | Status | Validação |
|------------|-------|--------|-----------|
| **Amazon** | 🛒 | ✅ | ASIN + tag + language |
| **Shopee** | 🛍️ | ✅ | Shortlinks apenas |
| **Mercado Livre** | 📱 | ✅ | Shortlinks + sociais |
| **Magazine Luiza** | 🏪 | ✅ | Vitrine apenas |
| **AliExpress** | 🌏 | ✅ | Shortlinks apenas |
| **Awin** | 🔗 | ✅ | Deeplinks + parâmetros |
| **Rakuten** | 🎯 | ✅ | Links validados |

## 📈 **Métricas e Monitoramento**

### **Métricas do Bot**
- `bot_start` - Bot iniciado
- `offer_received` - Oferta recebida
- `post_scheduled` - Post agendado
- `channel_post` - Oferta postada no canal

### **Métricas dos Validadores**
- **Shopee**: `shortlink_success`, `shortlink_fail`, `category_blocked`
- **ML**: `short_success`, `short_fail`, `social_accepted`, `product_blocked`
- **Magalu**: `vitrine_accepted`, `domain_blocked`

### **Logs do Sistema**
- **Arquivo**: `logs/bot.log`
- **Nível**: INFO, DEBUG, ERROR
- **Formato**: Timestamp + Nível + Mensagem

## 🚀 **Deploy em Produção**

### **1. Configuração de Ambiente**
```bash
# Variáveis de ambiente
export TELEGRAM_BOT_TOKEN="seu_token_real"
export TELEGRAM_CHANNEL_ID="@seu_canal_real"
export TELEGRAM_ADMIN_IDS="123456789,987654321"
export DEBUG="False"
```

### **2. Verificação Pré-Deploy**
```bash
# Testar sistema completo
make test-all

# Verificar métricas
make test-metrics

# Validar exemplos
make validate-examples
```

### **3. Iniciar em Produção**
```bash
# Iniciar bot
make bot-start

# Monitorar logs
tail -f logs/bot.log
```

### **4. Monitoramento Contínuo**
- **Status do bot**: `/status` no Telegram
- **Logs em tempo real**: `logs/bot.log`
- **Métricas**: Dashboard Flet
- **Alertas**: Notificações automáticas

## 🔒 **Segurança e Controle de Acesso**

### **Controle de Administradores**
- ✅ **Apenas admins** podem usar comandos do bot
- ✅ **IDs configuráveis** via arquivo de configuração
- ✅ **Logs de todas as ações** para auditoria
- ✅ **Validação de URLs** antes de processar

### **Validação de Conteúdo**
- ✅ **PostingManager** valida todos os links
- ✅ **Bloqueio automático** de URLs inválidas
- ✅ **Detecção de plataformas** não suportadas
- ✅ **Filtros de conteúdo** configuráveis

## 📱 **Interface do Usuário**

### **Comandos Administrativos**
```
🤖 **Garimpeiro Geek Bot - Sistema de Ofertas**

**Comandos disponíveis:**
📝 /post - Postar oferta imediatamente
⏰ /schedule - Agendar post para depois
📋 /queue - Ver fila de ofertas
✅ /approve - Aprovar oferta pendente
❌ /reject - Rejeitar oferta
📊 /status - Status do sistema

**Status:** ✅ Sistema operacional
**Ofertas na fila:** 5 ofertas
```

### **Interface de Agendamento**
```
⏰ **Agendar Post**

Escolha quando deseja publicar a próxima oferta da fila:

[⏰ 1 hora] [⏰ 3 horas] [⏰ 6 horas]
[🌅 Amanhã 9h] [🌅 Amanhã 18h]
[❌ Cancelar]
```

## 🧪 **Testes e Validação**

### **Testes Implementados**
- ✅ **Bot funcionando** e respondendo comandos
- ✅ **Validação de links** integrada com PostingManager
- ✅ **Sistema de agendamento** funcionando
- ✅ **Postagem no canal** funcionando
- ✅ **Métricas registrando** eventos

### **Como Testar**
```bash
# Teste rápido
make quick-test

# Teste completo
make test-all

# Teste do bot
python scripts/start_bot.py
```

## 📋 **Checklist de Deploy**

### **✅ Pré-Requisitos**
- [ ] Bot criado no @BotFather
- [ ] Token configurado em `src/core/config.py`
- [ ] Canal criado e ID configurado
- [ ] IDs de administradores configurados
- [ ] Dependências instaladas (`make install`)

### **✅ Verificações**
- [ ] Sistema de validação funcionando (`make test-all`)
- [ ] Métricas funcionando (`make test-metrics`)
- [ ] Bot iniciando sem erros (`make bot-start`)
- [ ] Comandos respondendo corretamente
- [ ] Postagem no canal funcionando

### **✅ Produção**
- [ ] Variáveis de ambiente configuradas
- [ ] Logs sendo gerados em `logs/bot.log`
- [ ] Métricas sendo registradas
- [ ] Sistema estável e responsivo
- [ ] Monitoramento ativo

## 🎉 **Status Atual**

### **✅ IMPLEMENTADO E FUNCIONANDO**
1. **Bot do Telegram** com todos os comandos
2. **Sistema de validação** integrado
3. **Postagem automática** no canal
4. **Sistema de agendamento** funcional
5. **Métricas e logs** em tempo real
6. **Interface administrativa** completa

### **🚀 PRONTO PARA PRODUÇÃO**
- **Funcionalidades**: 100% implementadas
- **Testes**: Passando com sucesso
- **Segurança**: Controle de acesso implementado
- **Monitoramento**: Métricas e logs ativos
- **Documentação**: Completa e atualizada

---

## 📞 **Suporte e Contato**

- **Documentação**: Este arquivo
- **Issues**: GitHub do projeto
- **Telegram**: @garimpeirogeek_support
- **Email**: suporte@garimpeirogeek.com

---

*Documento atualizado em: Janeiro 2025*  
*Versão: 1.0 - Bot Implementado e Funcionando*  
*Status: ✅ PRODUÇÃO READY*

