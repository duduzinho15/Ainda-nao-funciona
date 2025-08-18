.PHONY: help ui ui-json ui-ci baseline clean

help: ## Mostrar ajuda
	@echo "UI Reporter - Comandos disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

ui: ## Snapshot rápido
	python -m app.dashboard --report

ui-json: ## Snapshot + JSON
	python -m app.dashboard --report --json

ui-ci: ## Estrito + JUnit (para CI local)
	GG_REPORT=1 GG_STRICT=1 GG_JUNIT=1 GG_SEED=1337 GG_FREEZE_TIME=2025-01-01T00:00:00Z \
	python -m app.dashboard --report --json --junit --strict --exit-after-report && \
	python diagnostics/verify_snapshot.py

baseline: ## Aceitar snapshot atual como baseline
	cp ui_snapshot.txt tests/baselines/ui_snapshot.txt
	@echo "✅ Baseline atualizado com sucesso!"

clean: ## Limpar arquivos gerados
	rm -f ui_snapshot.txt ui_summary.json ui_reporter.junit.xml ui_snapshot.diff
	@echo "🧹 Arquivos limpos!"

test-all: ## Executar todos os testes
	@echo "🚀 Executando suite completa de testes..."
	@$(MAKE) ui-ci
	@echo "✅ Todos os testes passaram!"

# Comandos específicos para Windows (PowerShell)
ui-ps: ## UI Reporter via PowerShell (Windows)
	powershell -ExecutionPolicy Bypass -File scripts\test-ui.ps1

# Comandos específicos para Linux/Mac (Bash)
ui-bash: ## UI Reporter via Bash (Linux/Mac)
	./scripts/test-ui.sh
