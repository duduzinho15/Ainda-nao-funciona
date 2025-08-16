# PowerShell Script para iniciar o Dashboard como Administrador
# Resolve problemas de firewall e inicia o dashboard

param(
    [switch]$Elevate
)

# Configurações
$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Dashboard Garimpeiro Geek - Administrador"

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
    if (-not (Test-Administrator)) {
        Write-ColorOutput "🔧 Elevando privilégios..." "Yellow"
        Start-Process PowerShell -ArgumentList "-File `"$PSCommandPath`"", "-Elevate" -Verb RunAs
        exit
    }
}

# Função para criar exceções no firewall
function New-FirewallRules {
    Write-ColorOutput "🔧 Configurando firewall..." "Cyan"
    
    try {
        # Regra para porta 8080
        $rule8080 = Get-NetFirewallRule -DisplayName "Dashboard Garimpeiro Geek" -ErrorAction SilentlyContinue
        if (-not $rule8080) {
            New-NetFirewallRule -DisplayName "Dashboard Garimpeiro Geek" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow | Out-Null
            Write-ColorOutput "✅ Exceção para porta 8080 criada!" "Green"
        } else {
            Write-ColorOutput "ℹ️ Exceção para porta 8080 já existe" "Yellow"
        }
        
        # Regra para porta 3000
        $rule3000 = Get-NetFirewallRule -DisplayName "Dashboard Garimpeiro Geek Porta 3000" -ErrorAction SilentlyContinue
        if (-not $rule3000) {
            New-NetFirewallRule -DisplayName "Dashboard Garimpeiro Geek Porta 3000" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow | Out-Null
            Write-ColorOutput "✅ Exceção para porta 3000 criada!" "Green"
        } else {
            Write-ColorOutput "ℹ️ Exceção para porta 3000 já existe" "Yellow"
        }
        
        return $true
    }
    catch {
        Write-ColorOutput "❌ Erro ao configurar firewall: $($_.Exception.Message)" "Red"
        return $false
    }
}

# Função para ativar ambiente virtual
function Start-VirtualEnvironment {
    $projectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
    $venvPath = Join-Path $projectRoot "venv\Scripts\Activate.ps1"
    
    if (Test-Path $venvPath) {
        Write-ColorOutput "🔧 Ativando ambiente virtual..." "Cyan"
        & $venvPath
        Write-ColorOutput "✅ Ambiente virtual ativado" "Green"
        return $true
    } else {
        Write-ColorOutput "❌ Ambiente virtual não encontrado em: $venvPath" "Red"
        return $false
    }
}

# Função para iniciar dashboard
function Start-Dashboard {
    Write-ColorOutput "🚀 Iniciando dashboard..." "Green"
    
    try {
        # Muda para o diretório do dashboard
        Set-Location $PSScriptRoot
        
        # Importa e inicia o app
        $code = @"
from app import app
print('✅ Dashboard iniciado com sucesso!')
print('🌐 Acesse: http://127.0.0.1:8080')
app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)
"@
        
        python -c $code
    }
    catch {
        Write-ColorOutput "❌ Erro ao iniciar dashboard: $($_.Exception.Message)" "Red"
        Write-ColorOutput "💡 Tente executar manualmente: python -c 'from app import app; app.run(host=\"127.0.0.1\", port=8080)'" "Yellow"
    }
}

# Função principal
function Main {
    Write-ColorOutput "=" * 80 "Cyan"
    Write-ColorOutput "🚀 DASHBOARD GARIMPEIRO GEEK - ADMINISTRADOR" "Cyan"
    Write-ColorOutput "=" * 80 "Cyan"
    Write-Host ""
    
    # Verifica se é administrador
    if (-not (Test-Administrator)) {
        Write-ColorOutput "⚠️ Este script deve ser executado como administrador" "Yellow"
        Start-Elevated
        return
    }
    
    Write-ColorOutput "✅ Executando como administrador" "Green"
    
    # Configura firewall
    if (New-FirewallRules) {
        Write-ColorOutput "✅ Firewall configurado com sucesso!" "Green"
    } else {
        Write-ColorOutput "⚠️ Problemas com firewall, mas continuando..." "Yellow"
    }
    
    # Ativa ambiente virtual
    if (Start-VirtualEnvironment) {
        # Inicia dashboard
        Start-Dashboard
    } else {
        Write-ColorOutput "❌ Não foi possível ativar o ambiente virtual" "Red"
        Write-ColorOutput "💡 Verifique se o ambiente virtual foi criado corretamente" "Yellow"
    }
    
    Write-Host ""
    Write-ColorOutput "=" * 80 "Cyan"
    Write-ColorOutput "🏁 SCRIPT FINALIZADO" "Cyan"
    Write-ColorOutput "=" * 80 "Cyan"
}

# Executa o script
if ($Elevate) {
    Main
} else {
    Start-Elevated
}
