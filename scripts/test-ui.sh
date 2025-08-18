#!/usr/bin/env bash
set -euo pipefail

echo "🚀 UI Reporter - Teste Automatizado"
echo "Executando checks completos..."

# Configurar ambiente determinístico
export GG_REPORT=1
export GG_STRICT=1
export GG_JUNIT=1
export GG_SEED=1337
export GG_FREEZE_TIME=2025-01-01T00:00:00Z

# Executar UI Reporter com todas as opções
python -m app.dashboard --report --json --junit --strict --exit-after-report | tee ui_summary.json

# Verificar baseline
echo "🔍 Verificando baseline..."
python diagnostics/verify_snapshot.py

echo "✅ Todos os testes passaram!"
echo "📁 Arquivos gerados:"
echo "  - ui_snapshot.txt (snapshot visual)"
echo "  - ui_summary.json (resumo JSON)"
echo "  - ui_reporter.junit.xml (JUnit XML)"
echo "  - ui_snapshot.diff (se houver diferenças)"
