@echo off
echo 🚀 INICIANDO APLICAÇÃO FLET MODERNA - SISTEMA GEEK ALERT
echo ============================================================
echo.
echo 🎨 Interface moderna com Flet
echo 🌙 Suporte nativo para temas claro/escuro
echo 🎮 Design clean e minimalista
echo 📱 Componentes modernos e responsivos
echo.
echo 💡 Carregando aplicação...
echo.

REM Ativa ambiente virtual
call venv\Scripts\activate.bat

REM Verifica se Flet está instalado
echo 🔍 Verificando dependências...
pip show flet >nul 2>&1
if errorlevel 1 (
    echo ❌ Flet não encontrado. Instalando...
    pip install flet
    if errorlevel 1 (
        echo ❌ Erro ao instalar Flet!
        pause
        exit /b 1
    )
    echo ✅ Flet instalado com sucesso!
) else (
    echo ✅ Flet já está instalado!
)

echo.
echo 🚀 Executando aplicação Flet...
echo.

REM Executa aplicação Flet corrigida
flet run app_flet_fixed.py

echo.
echo 🛑 Aplicação encerrada.
pause
