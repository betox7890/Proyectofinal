@echo off
echo ========================================
echo Iniciando servidor Django con Daphne (ASGI)
echo Esto es necesario para que funcionen los WebSockets
echo ========================================
echo.

REM Verificar si Daphne está instalado
python -c "import daphne" 2>nul
if errorlevel 1 (
    echo ERROR: Daphne no está instalado.
    echo Instalando Daphne...
    pip install daphne
    if errorlevel 1 (
        echo ERROR: No se pudo instalar Daphne.
        pause
        exit /b 1
    )
)

echo.
echo Iniciando servidor en http://127.0.0.1:8000
echo Presiona Ctrl+C para detener el servidor
echo.

daphne -b 0.0.0.0 -p 8000 proyectofinal.asgi:application

pause

