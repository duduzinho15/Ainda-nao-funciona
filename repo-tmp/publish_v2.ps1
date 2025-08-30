param(
  [Parameter(Mandatory=$true)]
  [string]$RepoUrl,                       # ex: https://github.com/duduzinho15/Ainda-nao-funciona
  [string]$TempCloneDir = ".\repo-tmp",   # pasta temporária para clonar o repo antigo
  [string]$LocalV2Dir = ".",              # pasta com o código 2.0 (use "." se já estiver nela)
  [switch]$ForceDefaultMain               # opcional: tenta setar "main" como default branch via git (local)
)

function Fail($msg) { Write-Host "❌ $msg" -ForegroundColor Red; exit 1 }
function Info($msg) { Write-Host "• $msg" -ForegroundColor Cyan }
function Ok($msg) { Write-Host "✅ $msg" -ForegroundColor Green }

# 0) Validar Git
git --version | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "Git não encontrado no PATH." }

# 1) Preparar diretório temporário
if (Test-Path $TempCloneDir) {
  Info "Removendo pasta temporária existente: $TempCloneDir"
  Remove-Item -Recurse -Force $TempCloneDir
}
New-Item -ItemType Directory -Path $TempCloneDir | Out-Null

# 2) Clonar repo antigo
Info "Clonando repositório: $RepoUrl"
git clone $RepoUrl $TempCloneDir | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "Falha ao clonar $RepoUrl" }

Push-Location $TempCloneDir

# 3) Criar branch de backup 'legacy-archive'
Info "Criando e enviando branch de backup: legacy-archive"
git checkout -b legacy-archive | Out-Null
git push -u origin legacy-archive | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "Falha ao enviar legacy-archive para o remoto." }
Ok "Backup criado em: legacy-archive"

# 4) Criar 'main' órfã e limpar índice
Info "Criando branch órfã 'main'"
git checkout --orphan main | Out-Null
git rm -rf . | Out-Null

# 5) Copiar conteúdo do 2.0
Pop-Location
# Copia tudo do LocalV2Dir para TempCloneDir (exceto .git)
Info "Copiando conteúdo do 2.0 para o repositório temporário…"
robocopy $LocalV2Dir $TempCloneDir /E /XF ".git" ".gitignore_user" | Out-Null

Push-Location $TempCloneDir

# 6) Garantir .gitignore mínimo
$gitignorePath = Join-Path $TempCloneDir ".gitignore"
if (-not (Test-Path $gitignorePath)) {
@"
# venv e caches
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/

# IDE
.vscode/
.idea/

# builds
build/
dist/

# bancos e arquivos locais
*.sqlite
src/db/*.sqlite
.env
*.env
.env.*
playwright/.cache/
"@ | Set-Content -Encoding UTF8 $gitignorePath
  Ok ".gitignore criado"
} else {
  Info ".gitignore já existe – verifique se cobre .env e *.sqlite"
}

# 7) Commitar nova main
git add . | Out-Null
git commit -m "feat: substitui codebase pelo Sistema de Recomendações 2.0 (nova main)" | Out-Null

# 8) Enviar 'main' para o remoto
Info "Enviando branch 'main'…"
git push -u origin main | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "Falha ao enviar main para o remoto." }
Ok "main publicada com o 2.0"

# 9) (Opcional) Tornar 'main' a default localmente (no GitHub ajuste em Settings → Branches)
if ($ForceDefaultMain) {
  Info "Tentando definir 'main' como branch padrão local"
  git branch -M main | Out-Null
}

Pop-Location
Ok "Concluído! No GitHub, defina 'main' como default em Settings → Branches (se ainda não for)."
