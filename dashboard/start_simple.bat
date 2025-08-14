@echo off
chcp 65001 >nul
title Dashboard Garimpeiro Geek

echo.
echo ============================================================
echo 🚀 INICIADOR SIMPLES DO DASHBOARD GARIMPEIRO GEEK
echo ============================================================
echo.

:: Ativa ambiente virtual
if not defined VIRTUAL_ENV (
    echo 🔧 Ativando ambiente virtual...
    call "..\venv\Scripts\activate.bat"
)

:: Inicia o dashboard
echo 🚀 Iniciando dashboard...
echo 💡 IMPORTANTE: Mantenha esta janela aberta!
echo 🌐 Acesse: http://127.0.0.1:8080

python -c "
from app import app
print('✅ Dashboard iniciado com sucesso!')
print('🌐 Acesse: http://127.0.0.1:8080')
app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)
"

pause
