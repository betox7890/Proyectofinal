@echo off
echo ========================================
echo Iniciando servidor React (Vite)
echo ========================================
echo.

cd /d "%~dp0frontend"

REM Verificar si node_modules existe
if not exist "node_modules" (
    echo node_modules no encontrado. Instalando dependencias...
    call npm install
    if errorlevel 1 (
        echo ERROR: No se pudieron instalar las dependencias.
        pause
        exit /b 1
    )
)

echo.
echo Iniciando servidor de desarrollo...
echo El servidor estará disponible en http://localhost:5173
echo Presiona Ctrl+C para detener el servidor
echo.

call npm run dev

pause
