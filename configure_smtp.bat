@echo off
echo ========================================
echo Configuracion de SMTP para envio de correos
echo ========================================
echo.

echo Este script te ayudara a configurar las variables de entorno para SMTP.
echo.
echo IMPORTANTE: Estas variables solo estaran activas en esta sesion de terminal.
echo Para hacerlas permanentes, configuralas en las Variables de Entorno del sistema.
echo.

set /p EMAIL_HOST_USER="Ingresa tu email (ej: tu-email@gmail.com): "
set /p EMAIL_HOST_PASSWORD="Ingresa tu contraseña de aplicacion: "
set /p EMAIL_HOST="Servidor SMTP (Enter para Gmail: smtp.gmail.com): "
set /p EMAIL_PORT="Puerto SMTP (Enter para 587): "
set /p EMAIL_USE_TLS="Usar TLS? (Enter para True): "

if "%EMAIL_HOST%"=="" set EMAIL_HOST=smtp.gmail.com
if "%EMAIL_PORT%"=="" set EMAIL_PORT=587
if "%EMAIL_USE_TLS%"=="" set EMAIL_USE_TLS=True

set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
set DEFAULT_FROM_EMAIL=%EMAIL_HOST_USER%

echo.
echo ========================================
echo Configuracion aplicada:
echo ========================================
echo EMAIL_BACKEND=%EMAIL_BACKEND%
echo EMAIL_HOST=%EMAIL_HOST%
echo EMAIL_PORT=%EMAIL_PORT%
echo EMAIL_USE_TLS=%EMAIL_USE_TLS%
echo EMAIL_HOST_USER=%EMAIL_HOST_USER%
echo DEFAULT_FROM_EMAIL=%DEFAULT_FROM_EMAIL%
echo ========================================
echo.

echo Para usar estas variables, ejecuta el servidor en esta misma ventana de terminal.
echo O copia estos comandos y ejecutalos antes de iniciar el servidor.
echo.
pause

