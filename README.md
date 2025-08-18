# 🚀 Sistema de Recomendações de Ofertas Telegram

## 📋 Descrição

Sistema automatizado para coleta e recomendação de ofertas de produtos através do Telegram, integrando múltiplas plataformas de e-commerce.

## 🛠️ Funcionalidades Principais

- **Coleta Automática**: Scraping inteligente de ofertas
- **Integração Multi-plataforma**: Amazon, AliExpress, Magazine Luiza, etc.
- **Sistema de Afiliados**: Links de rastreamento automático
- **Dashboard Web**: Interface de gerenciamento completa
- **Notificações Telegram**: Envio automático de ofertas
- **Cache Inteligente**: Sistema de armazenamento otimizado

## 🏗️ Arquitetura

### Componentes Principais

- **Scrapers**: Coletam ofertas das plataformas
- **API Integrations**: Conectam com serviços externos
- **Database**: Armazena dados de ofertas e usuários
- **Telegram Bot**: Interface de usuário
- **Dashboard**: Painel de controle administrativo

### Estrutura de Arquivos

```
├── main.py                 # Arquivo principal do bot
├── config.py              # Configurações do sistema
├── database.py            # Sistema de banco de dados
├── telegram_poster.py     # Sistema de postagem no Telegram
├── aliexpress_integration.py  # Integração com AliExpress
├── amazon_integration.py      # Integração com Amazon
├── awin_api.py            # API da Awin
├── cache_system.py        # Sistema de cache
├── rate_limiter.py        # Sistema de rate limiting
├── health_monitor.py      # Monitoramento de saúde
├── performance_metrics.py # Métricas de performance
├── notification_system.py # Sistema de notificações
├── product_reviews.py     # Sistema de reviews
└── user_categories.py     # Categorias de usuários
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.11+
- PostgreSQL ou SQLite
- Token do Bot Telegram
- Contas de afiliado nas plataformas

### Passos de Instalação

```bash
# 1. Clonar o repositório
git clone <repository-url>
cd sistema-recomendacoes-telegram

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp env_example.txt .env
# Editar .env com suas configurações

# 5. Executar migrações
python run_migrations.py

# 6. Iniciar o bot
python main.py
```

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# APIs
ALIEXPRESS_API_KEY=your_key
AMAZON_API_KEY=your_key
AWIN_API_KEY=your_key

# Configurações do Sistema
SCRAPING_INTERVAL=300
MAX_PRODUCTS_PER_POST=5
MIN_DISCOUNT_PERCENT=20
```

### Configuração do Bot

```python
# config.py
BOT_CONFIG = {
    'name': 'Garimpeiro Geek',
    'description': 'Bot de ofertas automatizado',
    'commands': [
        '/start - Iniciar bot',
        '/ofertas - Ver ofertas recentes',
        '/config - Configurar preferências',
        '/stats - Estatísticas do sistema'
    ]
}
```

## 📊 Uso

### Comandos do Bot

- **`/start`**: Inicia o bot e mostra menu principal
- **`/ofertas`**: Lista ofertas recentes
- **`/config`**: Abre configurações do usuário
- **`/stats`**: Mostra estatísticas do sistema
- **`/help`**: Ajuda e comandos disponíveis

### Dashboard Administrativo

```bash
# Acessar dashboard
python dashboard/app.py

# Dashboard em modo produção
python dashboard/production_dashboard.py
```

## 🔧 Desenvolvimento

### Estrutura de Desenvolvimento

```
├── tests/                 # Testes automatizados
├── docs/                  # Documentação
├── scripts/               # Scripts utilitários
├── migrations/            # Migrações de banco
└── deployment/            # Scripts de deploy
```

### Executando Testes

```bash
# Testes unitários
python -m pytest tests/

# Testes de integração
python -m pytest tests/integration/

# Cobertura de código
python -m pytest --cov=. tests/
```

### Scripts de Desenvolvimento

```bash
# Verificar imports
python fix_imports.py

# Validar configurações
python sanity_check.py

# Executar scrapers
python run_scrapers.py

# Backup do banco
python backup_manager.py
```

## 📈 Monitoramento

### Métricas Disponíveis

- **Performance**: Tempo de resposta dos scrapers
- **Qualidade**: Taxa de sucesso das coletas
- **Uso**: Estatísticas de usuários e comandos
- **Sistema**: Uso de recursos e saúde geral

### Logs

```bash
# Logs do sistema
tail -f logs/system.log

# Logs de scraping
tail -f logs/scraping.log

# Logs de erros
tail -f logs/error.log
```

## 🚀 Deploy

### Ambiente de Produção

```bash
# Instalar dependências de produção
pip install -r requirements_production.txt

# Configurar supervisor
python install_production.py

# Iniciar serviços
python supervisor_service.py
```

### Docker (Opcional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

## 🤝 Contribuição

### Como Contribuir

1. **Fork** o projeto
2. **Crie** uma branch para sua feature
3. **Commit** suas mudanças
4. **Push** para a branch
5. **Abra** um Pull Request

### Padrões de Código

- **Python**: PEP 8
- **Documentação**: Docstrings em português
- **Testes**: Cobertura mínima de 80%
- **Commits**: Mensagens em português

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 Suporte

### Canais de Ajuda

- **Issues**: GitHub Issues
- **Documentação**: `/docs` folder
- **Telegram**: @garimpeiro_geek_support
- **Email**: suporte@garimpeirogeek.com

### Problemas Comuns

- **Erro de conexão**: Verificar configurações de rede
- **Rate limiting**: Ajustar intervalos de scraping
- **Token inválido**: Renovar token do bot Telegram
- **Banco offline**: Verificar conexão com database

## 🔮 Roadmap

### Próximas Funcionalidades

- **Machine Learning**: Recomendações personalizadas
- **API REST**: Endpoints para integração externa
- **Mobile App**: Aplicativo nativo para mobile
- **Analytics**: Dashboard avançado de métricas
- **Integração**: Mais plataformas de e-commerce

### Melhorias Técnicas

- **Cache Redis**: Sistema de cache distribuído
- **Queue System**: Processamento assíncrono
- **Microservices**: Arquitetura modular
- **CI/CD**: Pipeline de deploy automatizado
