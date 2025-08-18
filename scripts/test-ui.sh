#!/usr/bin/env bash
set -euo pipefail

echo "🚀 UI Reporter - Teste Automatizado"
echo "Executando checks completos..."

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
