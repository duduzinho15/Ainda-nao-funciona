# Makefile para Garimpeiro Geek
# Sistema de Recomendações de Ofertas via Telegram

.PHONY: help tree refactor-dry refactor-apply lint tests ui-ci clean install dev-install

# Variáveis
PYTHON = python
PIP = pip
PYTEST = pytest
RUFF = ruff
PYRIGHT = pyright

# Cores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Mostra esta ajuda
	@echo "$(GREEN)🎯 Garimpeiro Geek - Comandos Disponíveis$(NC)"
	@echo ""
	@echo "$(YELLOW)Estrutura e Refatoração:$(NC)"
	@echo "  make tree           - Mostra árvore resumida do projeto"
	@echo "  make refactor-dry   - Executa refatoração em modo dry-run"
	@echo "  make refactor-apply - Aplica movimentos de refatoração"
	@echo ""
	@echo "$(YELLOW)Qualidade e Testes:$(NC)"
	@echo "  make lint           - Executa linting (ruff + pyright)"
	@echo "  make tests          - Executa testes com pytest"
	@echo "  make ui-ci          - UI Reporter determinístico"
	@echo ""
	@echo "$(YELLOW)Desenvolvimento:$(NC)"
	@echo "  make install        - Instala dependências de produção"
	@echo "  make dev-install    - Instala dependências de desenvolvimento"
	@echo "  make clean          - Limpa arquivos temporários"
	@echo ""
	@echo "$(YELLOW)Execução:$(NC)"
	@echo "  make dashboard      - Executa dashboard"
	@echo "  make bot            - Executa bot Telegram"
	@echo "  make smoke          - Executa smoke tests"

tree: ## Mostra árvore resumida do projeto
	@echo "$(GREEN)📁 Estrutura do Projeto Garimpeiro Geek$(NC)"
	@echo ""
	@echo "$(YELLOW)src/$(NC)"
	@echo "├── app/"
	@echo "│   ├── dashboard/     # Flet UI + UI Reporter"
	@echo "│   └── bot/           # Telegram bot"
	@echo "├── core/              # Módulos principais"
	@echo "├── scrapers/          # Scrapers HTML/Playwright/Selenium"
	@echo "├── providers/         # APIs oficiais/SDKs"
	@echo "├── recommender/       # Regras de ranking/score"
	@echo "├── posting/           # Saída (telegram, canais)"
	@echo "├── diagnostics/       # UI Reporter, smoke, health"
	@echo "└── tests/             # Testes unitários e integração"
	@echo ""
	@echo "$(YELLOW)Pastas auxiliares:$(NC)"
	@echo "├── config/            # .env, scrapers.json, tokens"
	@echo "├── data/              # Dados não versionados"
	@echo "├── exports/           # CSVs exportados"
	@echo "├── logs/              # Logs do sistema"
	@echo "├── backups/           # Backups automáticos"
	@echo "├── samples/           # HTML capturados, JSONs"
	@echo "├── _archive/          # Arquivos legados"
	@echo "├── scripts/           # Scripts utilitários"
	@echo "└── deployment/        # Docker, compose"

refactor-dry: ## Executa refatoração em modo dry-run
	@echo "$(YELLOW)🔄 Executando refatoração em modo DRY-RUN...$(NC)"
	$(PYTHON) tools/refactor/move_and_update_imports.py --dry-run
	@echo "$(GREEN)✅ Dry-run concluído. Verifique o plano antes de aplicar.$(NC)"

refactor-apply: ## Aplica movimentos de refatoração
	@echo "$(YELLOW)⚠️  ATENÇÃO: Esta operação irá mover arquivos!$(NC)"
	@echo "$(YELLOW)Confirme que você executou 'make refactor-dry' e revisou o plano.$(NC)"
	@read -p "Pressione Enter para continuar ou Ctrl+C para cancelar..."
	@echo "$(GREEN)🚀 Aplicando refatoração...$(NC)"
	$(PYTHON) tools/refactor/move_and_update_imports.py --apply
	@echo "$(GREEN)✅ Refatoração aplicada com sucesso!$(NC)"

lint: ## Executa linting (ruff + pyright)
	@echo "$(YELLOW)🔍 Executando linting...$(NC)"
	@echo "$(YELLOW)Executando ruff...$(NC)"
	$(RUFF) check src/
	@echo "$(YELLOW)Executando pyright...$(NC)"
	$(PYRIGHT) src/
	@echo "$(GREEN)✅ Linting concluído!$(NC)"

tests: ## Executa testes com pytest
	@echo "$(YELLOW)🧪 Executando testes...$(NC)"
	$(PYTEST) src/tests/ -v
	@echo "$(GREEN)✅ Testes concluídos!$(NC)"

ui-ci: ## UI Reporter determinístico
	@echo "$(YELLOW)📊 Executando UI Reporter em modo CI...$(NC)"
	$(PYTHON) -m src.app.dashboard --report --strict
	@echo "$(GREEN)✅ UI Reporter executado!$(NC)"

install: ## Instala dependências de produção
	@echo "$(YELLOW)📦 Instalando dependências de produção...$(NC)"
	$(PIP) install -e .
	@echo "$(GREEN)✅ Instalação concluída!$(NC)"

dev-install: ## Instala dependências de desenvolvimento
	@echo "$(YELLOW)🔧 Instalando dependências de desenvolvimento...$(NC)"
	$(PIP) install -e ".[dev]"
	@echo "$(GREEN)✅ Instalação de desenvolvimento concluída!$(NC)"

clean: ## Limpa arquivos temporários
	@echo "$(YELLOW)🧹 Limpando arquivos temporários...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@echo "$(GREEN)✅ Limpeza concluída!$(NC)"

dashboard: ## Executa dashboard
	@echo "$(YELLOW)📊 Iniciando dashboard...$(NC)"
	$(PYTHON) -m src.app.dashboard

bot: ## Executa bot Telegram
	@echo "$(YELLOW)🤖 Iniciando bot Telegram...$(NC)"
	$(PYTHON) -m src.app.bot

smoke: ## Executa smoke tests
	@echo "$(YELLOW)💨 Executando smoke tests...$(NC)"
	$(PYTHON) -m src.diagnostics.smoke_sources --list-sources

# Comandos de desenvolvimento
format: ## Formata código com black
	@echo "$(YELLOW)🎨 Formatando código...$(NC)"
	black src/
	@echo "$(GREEN)✅ Formatação concluída!$(NC)"

check-imports: ## Verifica imports não resolvidos
	@echo "$(YELLOW)🔍 Verificando imports não resolvidos...$(NC)"
	$(PYTHON) tools/refactor/check_imports.py
	@echo "$(GREEN)✅ Verificação de imports concluída!$(NC)"

# Comandos de CI/CD
ci-setup: ## Configuração para CI
	@echo "$(YELLOW)⚙️ Configurando CI...$(NC)"
	$(PIP) install -e ".[dev]"
	@echo "$(GREEN)✅ CI configurado!$(NC)"

ci-test: ## Executa testes em CI
	@echo "$(YELLOW)🧪 Executando testes em CI...$(NC)"
	$(PYTEST) src/tests/ --cov=src --cov-report=xml
	@echo "$(GREEN)✅ Testes em CI concluídos!$(NC)"

# Comandos de backup e recuperação
backup: ## Cria backup do projeto
	@echo "$(YELLOW)💾 Criando backup...$(NC)"
	$(PYTHON) backup.py --create
	@echo "$(GREEN)✅ Backup criado!$(NC)"

restore: ## Lista backups disponíveis
	@echo "$(YELLOW)📦 Listando backups...$(NC)"
	$(PYTHON) backup.py --list

# Comandos de monitoramento
monitor: ## Executa monitor do sistema
	@echo "$(YELLOW)📊 Executando monitor...$(NC)"
	$(PYTHON) monitor.py --once

monitor-continuous: ## Executa monitor contínuo
	@echo "$(YELLOW)🔄 Executando monitor contínuo...$(NC)"
	$(PYTHON) monitor.py --continuous

# Comandos de instalação específicos
install-requirements: ## Instala requirements.txt
	@echo "$(YELLOW)📦 Instalando requirements.txt...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Requirements instalados!$(NC)"

# Comandos de verificação
verify-structure: ## Verifica estrutura do projeto
	@echo "$(YELLOW)🔍 Verificando estrutura do projeto...$(NC)"
	@test -d src/app/dashboard || (echo "$(RED)❌ src/app/dashboard não encontrado$(NC)" && exit 1)
	@test -d src/core || (echo "$(RED)❌ src/core não encontrado$(NC)" && exit 1)
	@test -d src/scrapers || (echo "$(RED)❌ src/scrapers não encontrado$(NC)" && exit 1)
	@test -f pyproject.toml || (echo "$(RED)❌ pyproject.toml não encontrado$(NC)" && exit 1)
	@echo "$(GREEN)✅ Estrutura do projeto verificada!$(NC)"

# Comando padrão
.DEFAULT_GOAL := help

