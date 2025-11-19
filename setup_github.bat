@echo off
echo ========================================
echo Configuracion de GitHub para el Proyecto
echo ========================================
echo.

REM Verificar si git está instalado
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git no está instalado. Por favor instala Git primero.
    echo Descarga Git desde: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo Git está instalado.
echo.

REM Verificar si ya es un repositorio git
if exist .git (
    echo Ya es un repositorio Git.
    echo.
    goto :check_remote
)

REM Inicializar repositorio git
echo Inicializando repositorio Git...
git init
if errorlevel 1 (
    echo ERROR: No se pudo inicializar el repositorio Git.
    pause
    exit /b 1
)

echo Repositorio Git inicializado.
echo.

:check_remote
REM Verificar si ya tiene un remote
git remote -v >nul 2>&1
if errorlevel 1 (
    echo No se ha configurado un repositorio remoto.
    echo.
    echo Por favor:
    echo 1. Crea un repositorio en GitHub (ve a https://github.com/new)
    echo 2. No inicialices el repositorio con README, .gitignore o licencia
    echo 3. Copia la URL del repositorio (ejemplo: https://github.com/usuario/repositorio.git)
    echo.
    set /p REPO_URL="Ingresa la URL de tu repositorio de GitHub: "
    
    if "%REPO_URL%"=="" (
        echo ERROR: URL no proporcionada.
        pause
        exit /b 1
    )
    
    echo.
    echo Agregando repositorio remoto...
    git remote add origin %REPO_URL%
    if errorlevel 1 (
        echo ERROR: No se pudo agregar el repositorio remoto.
        pause
        exit /b 1
    )
    
    echo Repositorio remoto agregado.
    echo.
) else (
    echo Repositorio remoto ya configurado.
    echo.
)

REM Agregar archivos
echo Agregando archivos al repositorio...
git add .
if errorlevel 1 (
    echo ERROR: No se pudieron agregar los archivos.
    pause
    exit /b 1
)

echo Archivos agregados.
echo.

REM Hacer commit
echo Creando commit inicial...
git commit -m "Initial commit: Proyecto Kanban con Django y React"
if errorlevel 1 (
    echo ERROR: No se pudo crear el commit.
    echo Esto puede suceder si no has configurado tu nombre y email en Git.
    echo.
    echo Configura tu nombre y email con:
    echo   git config --global user.name "Tu Nombre"
    echo   git config --global user.email "tu.email@example.com"
    pause
    exit /b 1
)

echo Commit creado.
echo.

REM Cambiar a rama main
echo Cambiando a rama main...
git branch -M main
echo.

REM Hacer push
echo Subiendo archivos a GitHub...
echo Esto puede pedirte tus credenciales de GitHub.
echo.
git push -u origin main
if errorlevel 1 (
    echo.
    echo ERROR: No se pudo subir los archivos.
    echo.
    echo Posibles causas:
    echo - Credenciales incorrectas
    echo - El repositorio remoto no existe
    echo - Problemas de conexión
    echo.
    echo Puedes intentar manualmente con:
    echo   git push -u origin main
    pause
    exit /b 1
)

echo.
echo ========================================
echo ¡Proyecto subido exitosamente a GitHub!
echo ========================================
echo.
echo Siguiente paso: Sigue las instrucciones en DEPLOY.md
echo para desplegar el backend en Render y el frontend en Vercel.
echo.
pause

