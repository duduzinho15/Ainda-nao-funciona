@echo off
echo 🚀 INICIANDO APLICATIVO DESKTOP - SISTEMA GEEK ALERT
echo ======================================================
echo.
echo 🖥️  Aplicativo Desktop com Interface Gráfica
echo 🎮 Controles visuais e monitoramento em tempo real
echo 📊 Estatísticas e configurações integradas
echo.
echo 💡 Carregando aplicativo...
echo.

REM Ativa ambiente virtual
call venv\Scripts\activate.bat

REM Executa aplicativo desktop
python geek_alert_desktop.py

echo.
echo 🛑 Aplicativo encerrado.
pause
