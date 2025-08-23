# 🎯 Garimpeiro Geek - Sistema de Recomendações de Ofertas

> **Sistema inteligente para monitorar e recomendar as melhores ofertas de produtos tecnológicos**

## 🚀 Características Principais

- **🔍 Scraping Inteligente**: Coleta automática de ofertas de múltiplas lojas
- **🤖 Bot Telegram**: Notificações em tempo real das melhores ofertas
- **📊 Dashboard Interativo**: Interface moderna para monitoramento e controle
- **💰 Sistema de Afiliados**: Conversão automática de links para monetização
- **📈 Métricas Avançadas**: Análise detalhada de performance e dados
- **🔄 Backup Automático**: Sistema robusto de backup e recuperação
- **🧪 Testes Automatizados**: Qualidade garantida com testes unitários

## 🏗️ Arquitetura do Sistema

```
garimpeiro-geek/
├── src/                          # 🆕 Pacote principal
│   ├── app/                      # Interface do usuário
│   │   ├── dashboard/            # Dashboard Flet + UI Reporter
│   │   │   ├── dashboard.py      # Dashboard principal
│   │   │   └── __init__.py
│   │   └── bot/                  # Bot Telegram
│   │       ├── telegram_bot.py   # Bot principal
│   │       └── __init__.py
│   ├── core/                     # Módulos principais
│   │   ├── storage.py            # Gerenciamento de preferências
│   │   ├── database.py           # Banco de dados SQLite
│   │   ├── metrics.py            # Coleta de métricas
│   │   ├── live_logs.py          # Logs em tempo real
│   │   ├── logging_setup.py      # Configuração de logs
│   │   ├── affiliate_converter.py # Conversor de links afiliados
│   │   └── __init__.py
│   ├── scrapers/                 # Módulos de scraping
│   │   ├── base_scraper.py       # Classe base para scrapers
│   │   ├── amazon/               # Scrapers específicos
│   │   ├── shopee/
│   │   ├── aliexpress/
│   │   └── ...                   # Outros scrapers
│   ├── providers/                # Integrações com APIs
│   │   ├── base_api.py           # Classe base para APIs
│   │   ├── mercadolivre/
│   │   ├── shopee_api/
│   │   └── aliexpress_api/
│   ├── recommender/              # Regras de ranking/score
│   ├── posting/                  # Saída (telegram, canais)
│   ├── diagnostics/              # UI Reporter, smoke, health
│   └── tests/                    # Testes automatizados
│       ├── unit/                 # Testes unitários
│       └── integration/          # Testes de integração
├── config/                       # 🆕 Configurações centralizadas
│   ├── .env                      # Variáveis de ambiente
│   ├── requirements.txt          # Dependências Python
│   ├── scrapers.json            # Configuração de scrapers
│   └── SETUP_GITHUB.md          # Guia de configuração
├── data/                         # 🆕 Dados não versionados
├── exports/                      # 🆕 CSVs exportados
├── logs/                         # 🆕 Logs do sistema
├── backups/                      # 🆕 Backups automáticos
├── samples/                      # 🆕 Exemplos e capturas
│   ├── html/                     # HTML capturado
│   └── json/                     # JSONs de resposta
├── _archive/                     # 🆕 Arquivos legados
├── scripts/                      # 🆕 Scripts utilitários
├── deployment/                   # 🆕 Docker e compose
├── tools/                        # 🆕 Ferramentas de desenvolvimento
│   └── refactor/                 # Scripts de refatoração
├── pyproject.toml               # 🆕 Configuração do pacote
├── Makefile                     # 🆕 Comandos automatizados
├── install.py                   # Script de instalação
├── backup.py                    # Sistema de backup
├── start.py                     # Ponto de entrada principal
└── README.md                    # Este arquivo
```

## 🛠️ Instalação

### Pré-requisitos
- Python 3.8+
- Git
- Conexão com internet

### Instalação Automatizada (Recomendado)
```bash
# 1. Clone o repositório
git clone <seu-repositorio>
cd garimpeiro-geek

# 2. Execute o instalador
python install.py
```

### Instalação Manual
```bash
# 1. Clone o repositório
git clone <seu-repositorio>
cd garimpeiro-geek

# 2. Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 3. Instale dependências
pip install -r config/requirements.txt

# 4. Configure o ambiente
cp config/env_example.txt .env
# Edite o arquivo .env com suas configurações
```

## ⚙️ Configuração

### 1. Configuração Básica
Copie o arquivo de exemplo e configure suas chaves:
```bash
cp env_example.txt .env
```

### 2. Configuração do Telegram
1. Crie um bot em [@BotFather](https://t.me/botfather)
2. Obtenha o token do bot
3. Configure no arquivo `.env`:
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
```

### 3. Configuração de APIs (Opcional)
Configure chaves de API para melhor funcionalidade:
```env
GOOGLE_SHOPPING_API_KEY=sua_chave_aqui
MERCADO_LIVRE_API_KEY=sua_chave_aqui
AMAZON_API_KEY=sua_chave_aqui
```

### 4. Configuração de Afiliados
Configure suas tags de afiliado:
```env
AMAZON_AFFILIATE_TAG=garimpeirogeek-20
MERCADO_LIVRE_AFFILIATE_TAG=sua_tag_aqui
```

## 🚀 Uso

### Executar o Dashboard
```bash
# Usando o módulo Python
python -m src.app.dashboard

# Ou usando o Makefile
make dashboard
```

### Executar o Bot Telegram
```bash
# Usando o módulo Python
python -m src.app.bot

# Ou usando o Makefile
make bot
```

### Executar Scrapers
```bash
# Usando o módulo Python
python -m src.scrapers.base_scraper

# Ou usando o Makefile
make smoke
```

### Executar Testes
```bash
# Usando pytest diretamente
python -m pytest src/tests/ -v

# Ou usando o Makefile
make tests
```

### Sistema de Backup
```bash
# Criar backup
python backup.py --create

# Listar backups
python backup.py --list

# Restaurar backup
python backup.py --restore backup_20241201_143022.zip

# Backup automático
python backup.py --auto
```

## 📊 Funcionalidades do Dashboard

- **📈 Métricas em Tempo Real**: Performance do sistema e estatísticas
- **📝 Logs ao Vivo**: Monitoramento de atividades em tempo real
- **⚙️ Configurações**: Gerenciamento centralizado de configurações
- **🎮 Controles**: Controle de scrapers, APIs e notificações
- **🌓 Tema Claro/Escuro**: Interface adaptável ao seu gosto
- **📱 Responsivo**: Funciona em diferentes tamanhos de tela

## 🔧 Desenvolvimento

### Estrutura de Módulos
- **Base Classes**: `BaseScraper` e `BaseAPI` para extensibilidade
- **Core Modules**: Funcionalidades principais reutilizáveis
- **Plugin System**: Arquitetura modular para fácil expansão

### Adicionando Novos Scrapers
```python
from src.scrapers.base_scraper import BaseScraper

class MeuScraper(BaseScraper):
    def __init__(self):
        super().__init__("MeuScraper", "https://minhaloja.com")
    
    async def scrape(self, query="", max_results=50):
        # Implementar lógica de scraping
        pass
    
    def parse_offer(self, raw_data):
        # Implementar parsing dos dados
        pass
```

### Adicionando Novas APIs
```python
from src.providers.base_api import BaseAPI

class MinhaAPI(BaseAPI):
    def __init__(self):
        super().__init__("MinhaAPI", "https://api.minhaapi.com")
    
    async def search_products(self, query, limit=50):
        # Implementar busca de produtos
        pass
    
    async def get_product_details(self, product_id):
        # Implementar detalhes do produto
        pass
```

## 🧪 Testes

### Executar Todos os Testes
```bash
# Usando pytest diretamente
python -m pytest src/tests/ -v

# Ou usando o Makefile
make tests
```

### Executar Testes Específicos
```bash
# Usando pytest diretamente
python -m pytest src/tests/unit/test_core_modules.py -v
python -m pytest src/tests/unit/test_core_modules.py::TestPreferencesStorage -v

# Ou usando o Makefile
make test-unit
```

### Cobertura de Testes
```bash
# Usando pytest diretamente
python -m pytest src/tests/ --cov=src --cov-report=html

# Ou usando o Makefile
make test-coverage
```

## 📦 Sistema de Backup

### Características
- **Backup Automático**: Configurável por intervalo
- **Compressão**: Arquivos compactados para economia de espaço
- **Metadados**: Informações detalhadas de cada backup
- **Retenção**: Política configurável de limpeza automática
- **Restauração**: Processo simples de recuperação

### Configuração de Backup
```python
# Em config.py
BACKUP_CONFIG = {
    "auto_backup": True,
    "backup_interval_hours": 24,
    "retention_days": 7,
    "compress_backups": True,
    "backup_database": True,
    "backup_logs": True,
    "backup_configs": True,
    "backup_exports": True
}
```

## 🔒 Segurança

- **Variáveis de Ambiente**: Chaves sensíveis em arquivo `.env`
- **Validação de Dados**: Verificação de entrada em todas as APIs
- **Rate Limiting**: Proteção contra sobrecarga de APIs
- **Logs Seguros**: Sem informações sensíveis nos logs
- **Backup Seguro**: Metadados sem dados pessoais

## 📈 Roadmap

### Versão 1.0 (Atual)
- ✅ Sistema básico de scraping
- ✅ Dashboard funcional
- ✅ Bot Telegram básico
- ✅ Sistema de métricas
- ✅ Backup automático
- ✅ Testes unitários

### Versão 1.1 (Próxima)
- 🔄 Gráficos avançados no dashboard
- 🔄 Mais scrapers (Shopee, AliExpress)
- 🔄 Sistema de alertas inteligentes
- 🔄 API REST para integrações

### Versão 2.0 (Futuro)
- 🔮 Machine Learning para previsão de preços
- 🔮 Interface web responsiva
- 🔮 Múltiplos usuários
- 🔮 Integração com WhatsApp

## 🤝 Contribuição

1. **Fork** o projeto
2. **Crie** uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. **Abra** um Pull Request

### Padrões de Código
- **PEP 8**: Estilo de código Python
- **Type Hints**: Anotações de tipo obrigatórias
- **Docstrings**: Documentação clara das funções
- **Testes**: Cobertura mínima de 80%

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 Suporte

### Problemas Comuns
1. **Erro de dependências**: Execute `python install.py`
2. **Bot não responde**: Verifique `TELEGRAM_BOT_TOKEN` no `.env`
3. **Dashboard não carrega**: Verifique logs em `logs/`
4. **Scrapers falhando**: Verifique configurações de delay e timeout

### Canais de Suporte
- **Issues**: [GitHub Issues](link-para-issues)
- **Documentação**: [Wiki](link-para-wiki)
- **Telegram**: [@GarimpeiroGeekBot](https://t.me/GarimpeiroGeekBot)

## 🙏 Agradecimentos

- **Flet**: Framework para interface desktop
- **Python Telegram Bot**: Biblioteca para bot do Telegram
- **SQLite**: Banco de dados leve e confiável
- **Pytest**: Framework de testes
- **Comunidade Python**: Suporte e contribuições

---

**⭐ Se este projeto te ajudou, considere dar uma estrela no GitHub!**

**🔗 Links Úteis:**
- [Documentação Completa](link-para-docs)
- [Changelog](link-para-changelog)
- [Contribuir](link-para-contribuir)
- [Licença](link-para-licenca)

## 🆕 Nova Estrutura src/ (v1.0+)

### 🏗️ Layout de Pacote Python

O projeto agora usa uma estrutura `src/` padrão da comunidade Python:

```bash
# Estrutura principal
src/
├── app/           # Interface do usuário
├── core/          # Módulos principais
├── scrapers/      # Módulos de scraping
├── providers/     # Integrações com APIs
├── recommender/   # Regras de ranking
├── posting/       # Saída (telegram, canais)
├── diagnostics/   # UI Reporter, smoke, health
└── tests/         # Testes automatizados
```

### 🔧 Comandos Make Disponíveis

```bash
# Desenvolvimento
make install          # Instalar dependências
make dev-install      # Instalar em modo desenvolvimento
make lint             # Executar linting (ruff + pyright)
make format           # Formatar código (black + ruff)
make tests            # Executar todos os testes
make test-unit        # Executar testes unitários
make test-integration # Executar testes de integração
make test-coverage    # Executar testes com cobertura

# Aplicação
make dashboard        # Executar dashboard
make bot              # Executar bot Telegram
make smoke            # Executar smoke tests
make ui-ci            # Executar UI Reporter

# Utilitários
make tree             # Mostrar estrutura de diretórios
make clean            # Limpar arquivos temporários
make backup           # Criar backup
make restore          # Restaurar backup
make monitor          # Monitorar sistema
make verify-structure # Verificar estrutura do projeto
```

### 📦 Instalação em Modo Desenvolvimento

```bash
# Instalar o pacote em modo editável
pip install -e ".[dev]"

# Isso permite importar módulos diretamente
python -c "import src; print('✅ src/ importado com sucesso')"
```

### 🔄 Migração de Imports

**⚠️ IMPORTANTE:** Todos os imports foram atualizados automaticamente!

```python
# ❌ Antes (estrutura antiga)
from core.storage import PreferencesStorage
from scrapers.base_scraper import BaseScraper

# ✅ Depois (nova estrutura)
from src.core.storage import PreferencesStorage
from src.scrapers.base_scraper import BaseScraper
```

### 🔗 Shims de Compatibilidade

Para facilitar a migração, shims temporários foram criados na raiz:

```python
# amazon_scraper.py (shim temporário)
import warnings
warnings.warn("Use 'src.scrapers.amazon.amazon_scraper'", DeprecationWarning)
from src.scrapers.amazon.amazon_scraper import *
```

**⚠️ Os shims serão removidos em versões futuras!**
