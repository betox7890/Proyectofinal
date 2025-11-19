@echo off
echo ========================================
echo Iniciando Celery Worker y Celery Beat
echo Esto es necesario para las tareas programadas
echo ========================================
echo.

REM Verificar si Redis está ejecutándose
echo Verificando conexión con Redis...
python -c "import redis; r = redis.Redis(host='127.0.0.1', port=6379, db=0); r.ping(); print('Redis conectado correctamente')" 2>nul
if errorlevel 1 (
    echo ERROR: Redis no está ejecutándose o no está disponible.
    echo Por favor, inicia Redis antes de continuar.
    echo.
    echo En Windows, puedes descargar Redis desde:
    echo https://github.com/microsoftarchive/redis/releases
    echo.
    pause
    exit /b 1
)

echo.
echo Redis está disponible.
echo.
echo Iniciando Celery Worker y Celery Beat...
echo Presiona Ctrl+C para detener ambos procesos
echo.

REM Iniciar Celery Worker en una nueva ventana
start "Celery Worker" cmd /k "cd /d %~dp0 && celery -A proyectofinal worker --loglevel=info --pool=solo"

REM Esperar un momento antes de iniciar Beat
timeout /t 3 /nobreak >nul

REM Iniciar Celery Beat en otra nueva ventana
start "Celery Beat" cmd /k "cd /d %~dp0 && celery -A proyectofinal beat --loglevel=info"

echo.
echo Celery Worker y Celery Beat iniciados en ventanas separadas.
echo.
pause

