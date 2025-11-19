@echo off
echo ========================================
echo Script de Despliegue - Proyecto Kanban
echo ========================================
echo.

REM Verificar si git está instalado
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git no está instalado.
    echo Por favor instala Git desde: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [1/5] Verificando repositorio Git...
if not exist .git (
    echo Inicializando repositorio Git...
    git init
    git branch -M main
)

echo.
echo [2/5] Preparando para subir a GitHub...
echo.
echo IMPORTANTE: Necesitas tener un repositorio creado en GitHub primero.
echo.
echo Pasos:
echo 1. Ve a https://github.com/new
echo 2. Crea un repositorio (NO marques README, .gitignore o licencia)
echo 3. Copia la URL del repositorio
echo.
set /p REPO_URL="Ingresa la URL de tu repositorio de GitHub: "

if "%REPO_URL%"=="" (
    echo ERROR: URL no proporcionada.
    pause
    exit /b 1
)

echo.
echo Configurando repositorio remoto...
git remote remove origin 2>nul
git remote add origin %REPO_URL%
if errorlevel 1 (
    echo ERROR: No se pudo agregar el repositorio remoto.
    pause
    exit /b 1
)

echo.
echo [3/5] Agregando archivos...
git add .
if errorlevel 1 (
    echo ERROR: No se pudieron agregar los archivos.
    pause
    exit /b 1
)

echo.
echo [4/5] Creando commit...
git commit -m "Preparado para despliegue en Render y Vercel" 2>nul
if errorlevel 1 (
    echo Creando commit inicial...
    git commit -m "Initial commit: Proyecto Kanban con Django y React"
)

echo.
echo [5/5] Subiendo a GitHub...
echo Esto puede pedirte tus credenciales de GitHub.
echo.
git push -u origin main
if errorlevel 1 (
    echo.
    echo ERROR: No se pudo subir a GitHub.
    echo.
    echo Posibles causas:
    echo - Credenciales incorrectas
    echo - El repositorio no existe
    echo - Problemas de autenticación
    echo.
    echo Intenta manualmente con:
    echo   git push -u origin main
    pause
    exit /b 1
)

echo.
echo ========================================
echo ¡Proyecto subido exitosamente a GitHub!
echo ========================================
echo.
echo Siguiente paso: Sigue la guía en GUIA_DESPLIEGUE_RAPIDA.md
echo.
echo URLs importantes:
echo - Render (Backend): https://dashboard.render.com
echo - Vercel (Frontend): https://vercel.com/dashboard
echo.
pause

