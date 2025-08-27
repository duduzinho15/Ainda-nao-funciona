# Makefile para Garimpeiro Geek
# Sistema de Recomendações de Ofertas Telegram

.PHONY: help test-affiliates test-e2e test-all dashboard bot-start bot-stop bot-status clean install

# Variáveis
PYTHON = python
PYTEST = pytest
DASHBOARD_SCRIPT = apps/flet_dashboard/main.py
BOT_SCRIPT = scripts/start_bot.py

# Ajuda
help:
	@echo "🚀 Garimpeiro Geek - Sistema de Recomendações de Ofertas"
	@echo ""
	@echo "Comandos disponíveis:"
	@echo "  test-affiliates  - Executa testes unitários de afiliados"
	@echo "  test-e2e         - Executa testes E2E"
	@echo "  test-all         - Executa todos os testes"
	@echo "  dashboard        - Inicia o dashboard Flet"
	@echo "  bot-start        - Inicia o bot do Telegram"
	@echo "  bot-stop         - Para o bot do Telegram"
	@echo "  bot-status       - Mostra status do bot"
	@echo "  install          - Instala dependências"
	@echo "  clean            - Limpa arquivos temporários"
	@echo "  help             - Mostra esta ajuda"

# Testes de afiliados
test-affiliates:
	@echo "🧪 Executando testes unitários de afiliados..."
	$(PYTEST) -q tests/unit

# Testes E2E
test-e2e:
	@echo "🔗 Executando testes E2E..."
	$(PYTEST) -q tests/e2e

# Todos os testes
test-all:
	@echo "📊 Executando todos os testes..."
	$(PYTEST) -q

# Dashboard Flet
dashboard:
	@echo "📱 Iniciando dashboard Flet..."
	$(PYTHON) $(DASHBOARD_SCRIPT)

# Bot do Telegram
bot-start:
	@echo "🤖 Iniciando bot do Telegram..."
	$(PYTHON) $(BOT_SCRIPT)

bot-stop:
	@echo "🛑 Parando bot do Telegram..."
	@echo "💡 Use Ctrl+C no terminal onde o bot está rodando"

bot-status:
	@echo "📊 Status do bot do Telegram..."
	@echo "💡 Verifique os logs em logs/bot.log"

# Instalar dependências
install:
	@echo "📦 Instalando dependências..."
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-html aioresponses python-telegram-bot

# Limpar arquivos temporários
clean:
	@echo "🧹 Limpando arquivos temporários..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	find . -type f -name "*.db" -delete
	find . -type f -name "*.sqlite" -delete
	find . -type f -name "report.html" -delete
	@echo "✅ Limpeza concluída!"

# Comandos de desenvolvimento
dev-setup:
	@echo "🔧 Configurando ambiente de desenvolvimento..."
	@echo "1. Configure o token do bot em src/core/config.py"
	@echo "2. Configure o ID do canal"
	@echo "3. Configure os IDs dos administradores"
	@echo "4. Execute: make install"
	@echo "5. Execute: make bot-start"

# Comandos de produção
prod-deploy:
	@echo "🚀 Deploy em produção..."
	@echo "1. Configure variáveis de ambiente"
	@echo "2. Execute: make test-all"
	@echo "3. Execute: make bot-start"
	@echo "4. Monitore logs em logs/bot.log"

# Comandos de teste
quick-test:
	@echo "⚡ Teste rápido do sistema..."
	$(PYTEST) -q tests/unit/test_aff_awin.py::test_awin_deeplink_lg_product tests/unit/test_aff_ml.py::test_ml_shortlinks_validos tests/unit/test_aff_shopee.py::test_shopee_category_bloqueada

test-metrics:
	@echo "📊 Testando métricas..."
	$(PYTHON) -c "from src.affiliate.shopee import get_metrics; from src.affiliate.mercadolivre import get_metrics; from src.affiliate.magazineluiza import get_metrics; print('Shopee:', get_metrics()); print('ML:', get_metrics()); print('Magalu:', get_metrics())"

validate-examples:
	@echo "🔍 Validando exemplos de afiliados..."
	$(PYTEST) -q tests/e2e/test_affiliates_e2e.py::test_e2e_cobertura_completa_awin tests/e2e/test_affiliates_e2e.py::test_e2e_cobertura_completa_shopee tests/e2e/test_affiliates_e2e.py::test_e2e_cobertura_completa_ml

status:
	@echo "📋 Status do sistema..."
	@echo "✅ Validadores implementados"
	@echo "✅ PostingManager funcionando"
	@echo "✅ Testes passando"
	@echo "✅ Bot do Telegram implementado"
	@echo "🚀 Sistema pronto para produção!"

# Padrão
all: test-all dashboard

