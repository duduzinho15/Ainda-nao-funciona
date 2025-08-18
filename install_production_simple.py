#!/usr/bin/env python3
"""
Script de Instalação Simplificado para Produção
Versão otimizada para Windows
"""
import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def main():
    """Instalação simplificada"""
    print("🚀 Instalador Simplificado - Sistema de Recomendações")
    print("=" * 60)
    
    current_dir = Path.cwd()
    
    # 1. Verifica Python
    print(f"\n🐍 Python: {sys.version}")
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ requerido")
        return 1
    
    # 2. Cria diretórios
    print("\n📁 Criando diretórios...")
    directories = [
        'logs',
        'backups', 
        'storage/data',
        'storage/temp',
        'deployment',
        'dashboard/templates',
        'dashboard/static'
    ]
    
    for directory in directories:
        dir_path = current_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")
    
    # 3. Gera arquivo de configuração
    print("\n⚙️ Gerando configuração...")
    config_content = """# Configuração de Produção - Sistema de Recomendações
# Configure suas credenciais reais aqui

# Telegram Bot
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHANNEL_ID=seu_canal_id_aqui
TELEGRAM_ADMIN_ID=seu_admin_id_aqui

# APIs de Afiliados
AMAZON_ASSOCIATE_TAG=sua_tag_aqui
AWIN_API_TOKEN=seu_token_aqui
SHOPEE_API_KEY=sua_api_key_aqui
SHOPEE_API_SECRET=seu_secret_aqui
ALIEXPRESS_APP_KEY=sua_app_key_aqui
ALIEXPRESS_APP_SECRET=seu_app_secret_aqui
MERCADO_LIVRE_TAG=sua_tag_aqui
MAGAZINE_LUIZA_TAG=sua_tag_aqui

# Banco de Dados
DATABASE_URL=sqlite:///production.db
DATABASE_BACKUP_PATH=./backups/
DATABASE_BACKUP_RETENTION_DAYS=30

# Servidor
HOST=0.0.0.0
PORT=8080
DEBUG=false
SECRET_KEY=chave_secreta_gerada_automaticamente

# Monitoramento
HEALTH_CHECK_INTERVAL=300
ALERT_EMAIL=seu_email@exemplo.com
ALERT_SMS_NUMBER=seu_numero_aqui
SLACK_WEBHOOK_URL=sua_webhook_aqui

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=60
MAX_REQUESTS_PER_HOUR=1000

# Logs
LOG_LEVEL=INFO
LOG_FILE=./logs/production.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Dashboard
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080
DASHBOARD_DEBUG=false

# Email para alertas
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
ALERT_EMAIL_FROM=seu_email@gmail.com
ALERT_EMAIL_PASSWORD=sua_senha_de_app_aqui

# SMS (Twilio)
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=seu_account_sid_aqui
TWILIO_AUTH_TOKEN=seu_auth_token_aqui
TWILIO_FROM_NUMBER=seu_numero_twilio_aqui

# Slack
SLACK_CHANNEL=#alerts
SLACK_USERNAME=Sistema de Alertas

# Webhook personalizado
WEBHOOK_URL=sua_url_webhook_aqui
"""
    
    config_file = current_dir / 'config_producao.env'
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    print(f"   ✅ {config_file}")
    
    # 4. Gera requirements simplificado
    print("\n📦 Gerando requirements...")
    requirements_content = """# Requirements para Produção - Sistema de Recomendações
# Dependências principais

# Bot do Telegram
python-telegram-bot==20.7

# Configuração e variáveis de ambiente
python-dotenv==1.0.0

# Requisições HTTP
aiohttp>=3.8.0
requests==2.31.0

# Web Scraping
beautifulsoup4==4.12.2
selenium==4.15.2
playwright>=1.40.0

# Sistema e monitoramento
psutil==5.9.6

# Criptografia para configurações
cryptography>=41.0.0

# Agendamento de tarefas
schedule>=1.2.0

# Dashboard Web
Flask==3.0.0
Flask-SocketIO==5.3.6
plotly>=5.17.0
pandas>=2.1.0

# WebSocket e comunicação em tempo real
python-socketio>=5.9.0
eventlet>=0.33.0

# Banco de dados
sqlalchemy>=2.0.0

# Cache e performance
redis>=5.0.0

# Logging estruturado
structlog>=23.2.0

# Validação de dados
pydantic>=2.5.0

# Testes
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Desenvolvimento e debugging
ipython>=8.17.0
black>=23.11.0

# Deploy e produção
gunicorn>=21.2.0

# Monitoramento e métricas
prometheus-client>=0.19.0

# Notificações
twilio>=8.10.0
slack-sdk>=3.26.0

# Utilitários
click>=8.1.0
rich>=13.7.0
tqdm>=4.66.0
"""
    
    requirements_file = current_dir / 'requirements_production.txt'
    with open(requirements_file, 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    print(f"   ✅ {requirements_file}")
    
    # 5. Gera script de ativação
    print("\n🔧 Gerando scripts de ativação...")
    
    # Script Windows
    if platform.system().lower() == 'windows':
        activate_script = current_dir / 'activate_production.bat'
        activate_content = f"""@echo off
echo Ativando ambiente de producao...
echo.
echo Para instalar dependencias, execute:
echo pip install -r requirements_production.txt
echo.
echo Para executar o sistema:
echo python deployment/production_setup.py
echo.
echo Para executar o dashboard:
echo python dashboard/production_dashboard.py
echo.
pause
"""
        with open(activate_script, 'w', encoding='utf-8') as f:
            f.write(activate_content)
        print(f"   ✅ {activate_script}")
    
    # 6. Gera README de produção
    print("\n📚 Gerando documentação...")
    readme_content = """# Sistema de Recomendações - Produção

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
"""
    
    readme_file = current_dir / 'README_PRODUCAO.md'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"   ✅ {readme_file}")
    
    # 7. Finaliza
    print("\n🎉 Instalação simplificada concluída!")
    print("=" * 60)
    
    print("\n📋 Próximos passos:")
    print("1. Instale as dependências:")
    print("   pip install -r requirements_production.txt")
    print("\n2. Configure suas credenciais em 'config_producao.env'")
    print("\n3. Execute o sistema:")
    print("   python deployment/production_setup.py")
    print("\n4. Inicie o dashboard:")
    print("   python dashboard/production_dashboard.py")
    
    print("\n📚 Documentação disponível em: README_PRODUCAO.md")
    print("🔧 Script de ativação: activate_production.bat")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
