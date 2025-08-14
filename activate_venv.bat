@echo off
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat
echo.
echo Ambiente virtual ativado!
echo Python path: %PYTHONPATH%
echo.
echo Para executar o bot, use: python main.py
echo Para instalar dependencias, use: pip install -r requirements.txt
echo.
cmd /k
