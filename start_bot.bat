@echo off

REM 1. Configurar la variable de entorno BOT_TOKEN
REM Esta línea inyecta el token en el entorno de la terminal
set BOT_TOKEN=8213379352:AAHg4aGI2EownzzRy-7yCFxTJD3ml2XHRFs

REM 2. Activa el entorno virtual
REM Llama al script de activación del entorno 'venv'
call venv\Scripts\activate.bat

REM 3. Inicia el bot (Bucle de reinicio en caso de fallo)
:start
echo [INFO] Iniciando el bot...
python main.py
echo [ERROR] El bot ha fallado o se ha detenido. Reiniciando en 5 segundos...
timeout /t 5 /nobreak
goto start