# PowerShell Script para iniciar o Dashboard Garimpeiro Geek
# Executa com privilégios elevados se necessário

param(
    [switch]$Elevate,
    [switch]$Waitress,
    [switch]$Flask,
    [switch]$Gunicorn
)

# Configurações de execução
$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Dashboard Garimpeiro Geek"

# Função para exibir mensagens coloridas
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Função para verificar se é administrador
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Função para elevar privilégios
function Start-Elevated {
    if (Test-Administrator) {
        return $false
    }
    
    Write-ColorOutput "⚠️  Privilégios de administrador podem ser necessários" "Yellow"
    Write-ColorOutput "🔧 Tentando elevar privilégios..." "Cyan"
    
    try {
        Start-Process PowerShell -ArgumentList "-File", $PSCommandPath, "-Waitress:$Waitress", "-Flask:$Flask", "-Gunicorn:$Gunicorn" -Verb RunAs
        exit
    }
    catch {
        Write-ColorOutput "❌ Não foi possível elevar privilégios" "Red"
        Write-ColorOutput "💡 Execute o script como administrador manualmente" "Yellow"
        return $false
    }
}

# Função para verificar ambiente virtual
function Test-VirtualEnvironment {
    if (-not $env:VIRTUAL_ENV) {
        Write-ColorOutput "⚠️  Ambiente virtual não detectado" "Yellow"
        Write-ColorOutput "🔧 Ativando ambiente virtual..." "Cyan"
        
        $venvPath = Join-Path $PSScriptRoot "..\venv\Scripts\Activate.ps1"
        if (Test-Path $venvPath) {
            try {
                & $venvPath
                Write-ColorOutput "✅ Ambiente virtual ativado" "Green"
                return $true
            }
            catch {
                Write-ColorOutput "❌ Erro ao ativar ambiente virtual" "Red"
                return $false
            }
        }
        else {
            Write-ColorOutput "❌ Ambiente virtual não encontrado em: $venvPath" "Red"
            return $false
        }
    }
    return $true
}

# Função para verificar dependências
function Test-Dependencies {
    Write-ColorOutput "🔍 Verificando dependências..." "Cyan"
    
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Python disponível: $pythonVersion" "Green"
        }
        else {
            Write-ColorOutput "❌ Python não encontrado" "Red"
            return $false
        }
        
        # Verifica se o Flask está instalado
        $flaskCheck = python -c "import flask; print('Flask OK')" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Flask disponível" "Green"
        }
        else {
            Write-ColorOutput "⚠️  Flask não encontrado, instalando..." "Yellow"
            pip install flask
        }
        
        return $true
    }
    catch {
        Write-ColorOutput "❌ Erro ao verificar dependências: $_" "Red"
        return $false
    }
}

# Função para verificar banco de dados
function Test-Database {
    Write-ColorOutput "🔍 Verificando banco de dados..." "Cyan"
    
    $dbPath = Join-Path $PSScriptRoot "..\ofertas.db"
    if (Test-Path $dbPath) {
        try {
            $dbSize = (Get-Item $dbPath).Length
            Write-ColorOutput "✅ Banco de dados encontrado: $dbSize bytes" "Green"
            return $true
        }
        catch {
            Write-ColorOutput "❌ Erro ao verificar banco de dados: $_" "Red"
            return $false
        }
    }
    else {
        Write-ColorOutput "⚠️  Banco de dados não encontrado em: $dbPath" "Yellow"
        return $false
    }
}

# Função para iniciar dashboard
function Start-Dashboard {
    param(
        [string]$Method = "auto"
    )
    
    Write-ColorOutput "🚀 Iniciando dashboard com método: $Method" "Green"
    
    $scriptPath = Join-Path $PSScriptRoot "run_dashboard.py"
    if (-not (Test-Path $scriptPath)) {
        Write-ColorOutput "❌ Script run_dashboard.py não encontrado" "Red"
        return $false
    }
    
    try {
        switch ($Method) {
            "waitress" { python $scriptPath -c "2" }
            "flask" { python $scriptPath -c "1" }
            "gunicorn" { python $scriptPath -c "3" }
            default { python $scriptPath -c "4" }
        }
        return $true
    }
    catch {
        Write-ColorOutput "❌ Erro ao executar dashboard: $_" "Red"
        return $false
    }
}

# Função principal
function Main {
    Write-ColorOutput "===========================================================" "Cyan"
    Write-ColorOutput "🚀 INICIADOR DO DASHBOARD GARIMPEIRO GEEK" "Cyan"
    Write-ColorOutput "===========================================================" "Cyan"
    Write-ColorOutput ""
    
    # Eleva privilégios se solicitado
    if ($Elevate) {
        if (Start-Elevated) {
            return
        }
    }
    
    # Verifica ambiente virtual
    if (-not (Test-VirtualEnvironment)) {
        Write-ColorOutput "❌ Falha ao configurar ambiente virtual" "Red"
        Read-Host "Pressione Enter para sair"
        return
    }
    
    # Verifica dependências
    if (-not (Test-Dependencies)) {
        Write-ColorOutput "❌ Dependências não satisfeitas" "Red"
        Read-Host "Pressione Enter para sair"
        return
    }
    
    # Verifica banco de dados
    Test-Database | Out-Null
    
    # Determina método de execução
    $method = "auto"
    if ($Waitress) { $method = "waitress" }
    elseif ($Flask) { $method = "flask" }
    elseif ($Gunicorn) { $method = "gunicorn" }
    
    Write-ColorOutput ""
    Write-ColorOutput "🎯 Configuração:" "Yellow"
    Write-ColorOutput "   Método: $method" "White"
    Write-ColorOutput "   Porta: 5000" "White"
    Write-ColorOutput "   URL: http://127.0.0.1:5000" "White"
    Write-ColorOutput ""
    
    # Inicia dashboard
    if (Start-Dashboard -Method $method) {
        Write-ColorOutput "✅ Dashboard iniciado com sucesso!" "Green"
    }
    else {
        Write-ColorOutput "❌ Falha ao iniciar dashboard" "Red"
        Write-ColorOutput ""
        Write-ColorOutput "💡 Dicas de solução:" "Yellow"
        Write-ColorOutput "   - Verifique se a porta 5000 está livre" "White"
        Write-ColorOutput "   - Execute como administrador se necessário" "White"
        Write-ColorOutput "   - Verifique o firewall do Windows" "White"
        Write-ColorOutput "   - Tente outro método: -Waitress, -Flask, ou -Gunicorn" "White"
    }
    
    Read-Host "`nPressione Enter para sair"
}

# Executa função principal
try {
    Main
}
catch {
    Write-ColorOutput "❌ Erro crítico: $_" "Red"
    Read-Host "Pressione Enter para sair"
}
