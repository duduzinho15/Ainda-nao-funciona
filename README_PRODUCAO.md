# Sistema de Recomendações - Produção

## 🚀 Instalação Rápida

1. **Instale as dependências:**
   ```bash
   pip install -r requirements_production.txt
   ```

2. **Configure suas credenciais:**
   - Edite o arquivo `config_producao.env`
   - Configure todas as credenciais necessárias

3. **Execute o sistema:**
   ```bash
   python deployment/production_setup.py
   ```

4. **Inicie o dashboard:**
   ```bash
   python dashboard/production_dashboard.py
   ```

## 📋 Funcionalidades

- ✅ Sistema de configuração de produção
- ✅ Backup automático do banco de dados
- ✅ Sistema de alertas por email/SMS/Slack
- ✅ Dashboard web para monitoramento
- ✅ Métricas em tempo real
- ✅ Logs estruturados
- ✅ Rate limiting e segurança

## 🔧 Configuração

### Telegram Bot
- `TELEGRAM_BOT_TOKEN`: Token do seu bot
- `TELEGRAM_CHANNEL_ID`: ID do canal
- `TELEGRAM_ADMIN_ID`: ID do administrador

### APIs de Afiliados
- `AMAZON_ASSOCIATE_TAG`: Tag de afiliado da Amazon
- `AWIN_API_TOKEN`: Token da API AWIN
- `SHOPEE_API_KEY`: Chave da API Shopee
- `ALIEXPRESS_APP_KEY`: Chave da API AliExpress

### Monitoramento
- `ALERT_EMAIL`: Email para alertas
- `SLACK_WEBHOOK_URL`: Webhook do Slack
- `LOG_LEVEL`: Nível de logging (INFO, WARNING, ERROR)

## 📊 Dashboard

O dashboard está disponível em: http://localhost:8080

### Funcionalidades:
- Métricas do sistema em tempo real
- Status dos serviços
- Histórico de alertas
- Status dos backups
- Logs do sistema
- Gráficos de performance

## 🚨 Alertas

O sistema suporta alertas via:
- Email (SMTP)
- SMS (Twilio)
- Slack
- Telegram
- Webhook personalizado

## 💾 Backups

- Backups automáticos configuráveis
- Retenção configurável
- Verificação de integridade
- Notificações de status

## 🔒 Segurança

- Configurações criptografadas
- Rate limiting configurável
- Logs de auditoria
- Validação de configurações

## 📁 Estrutura de Diretórios

```
├── deployment/          # Sistema de produção
├── dashboard/           # Dashboard web
├── logs/               # Logs do sistema
├── backups/            # Backups automáticos
├── storage/            # Dados do sistema
└── config_producao.env # Configurações
```

## 🆘 Suporte

Para suporte técnico:
1. Verifique os logs em `./logs/`
2. Consulte a documentação
3. Execute os testes básicos
4. Verifique as configurações

## 📝 Logs

Os logs são salvos em:
- `./logs/production.log` - Log principal
- `./logs/` - Outros logs do sistema

## 🔄 Atualizações

Para atualizar o sistema:
1. Faça backup dos dados
2. Atualize o código
3. Execute `pip install -r requirements_production.txt`
4. Reinicie os serviços

---

**⚠️ IMPORTANTE:** Configure todas as credenciais antes de usar em produção!
