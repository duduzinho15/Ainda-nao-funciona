@echo off
echo 🚀 INSTALADOR DE APLICATIVOS WINDOWS - SISTEMA GEEK ALERT
echo ============================================================
echo.
echo 📦 Instalando dependências necessárias...
echo.

REM Ativa ambiente virtual
call venv\Scripts\activate.bat

REM Instala dependências para aplicativos Windows
echo 🔧 Instalando pywin32 para serviços Windows...
pip install pywin32

echo 🔧 Instalando pystray para ícone da bandeja...
pip install pystray

echo 🔧 Instalando Pillow para manipulação de imagens...
pip install Pillow

echo.
echo ✅ Instalação concluída!
echo.
echo 🎮 APLICATIVOS DISPONÍVEIS:
echo.
echo 1. 🖥️  Aplicativo Desktop Completo:
echo    python geek_alert_desktop.py
echo.
echo 2. 📱 Aplicativo com Tray Icon:
echo    python geek_alert_tray_app.py
echo.
echo 3. 🔧 Serviço Windows:
echo    python geek_alert_service.py install
echo    python geek_alert_service.py start
echo.
echo 💡 RECOMENDAÇÃO: Use o Aplicativo Desktop para começar!
echo.
pause
