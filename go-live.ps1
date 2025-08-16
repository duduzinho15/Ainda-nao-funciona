# go-live.ps1
Write-Host "🚀 ATIVAÇÃO DE PRODUÇÃO - GARIMPEIRO GEEK" -ForegroundColor Red
Write-Host "=============================================" -ForegroundColor Red

# Confirmação do usuário
$confirma = Read-Host "Tem certeza que quer ativar a produção? (s/N)"
if ($confirma -ne "s" -and $confirma -ne "S") {
    Write-Host "❌ Ativação cancelada" -ForegroundColor Yellow
    exit
}

# Desativa DRY_RUN
$env:DRY_RUN = "0"
Write-Host "✅ DRY_RUN desativado - SISTEMA EM PRODUÇÃO!" -ForegroundColor Red

# Inicia o bot
Write-Host "`n🤖 Iniciando bot em modo produção..." -ForegroundColor Cyan
python main_simples.py
