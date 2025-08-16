# sanity-check.ps1
Write-Host "🧪 SANITY CHECK - GARIMPEIRO GEEK" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Configura DRY_RUN
$env:DRY_RUN = "1"
Write-Host "✅ DRY_RUN ativado (não vai postar)" -ForegroundColor Yellow

# Executa testes de scrapers
Write-Host "`n🔄 Executando testes de scrapers..." -ForegroundColor Cyan
python orchestrator.py --dry-run --limit 5

# Verifica duplicatas no DB
Write-Host "`n🔍 Verificando duplicatas no banco..." -ForegroundColor Cyan
python -c "import sqlite3; conn = sqlite3.connect('ofertas.db'); cursor = conn.cursor(); cursor.execute('SELECT offer_hash, COUNT(*) c FROM ofertas GROUP BY offer_hash HAVING c>1'); dups = cursor.fetchall(); print(f'Duplicatas: {len(dups)}') if dups else print('✅ Nenhuma duplicata'); conn.close()"

Write-Host "`n🧪 Sanity check concluído!" -ForegroundColor Green
