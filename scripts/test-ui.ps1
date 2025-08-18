# UI Reporter - Teste Automatizado (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "🚀 UI Reporter - Teste Automatizado" -ForegroundColor Green
Write-Host "Executando checks completos..." -ForegroundColor Yellow

# Configurar ambiente determinístico
$env:GG_REPORT = "1"
$env:GG_STRICT = "1"
$env:GG_JUNIT = "1"
$env:GG_SEED = "1337"
$env:GG_FREEZE_TIME = "2025-01-01T00:00:00Z"

# Executar UI Reporter com todas as opções
python -m app.dashboard --report --json --junit --strict --exit-after-report | Tee-Object -FilePath ui_summary.json

# Verificar baseline
Write-Host "🔍 Verificando baseline..." -ForegroundColor Yellow
python diagnostics/verify_snapshot.py

Write-Host "✅ Todos os testes passaram!" -ForegroundColor Green
Write-Host "📁 Arquivos gerados:" -ForegroundColor Cyan
Write-Host "  - ui_snapshot.txt (snapshot visual)" -ForegroundColor White
Write-Host "  - ui_summary.json (resumo JSON)" -ForegroundColor White
Write-Host "  - ui_reporter.junit.xml (JUnit XML)" -ForegroundColor White
Write-Host "  - ui_snapshot.diff (se houver diferenças)" -ForegroundColor White
