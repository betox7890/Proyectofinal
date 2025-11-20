@echo off
echo Configurando variables de entorno para EmailJS...
echo.

if exist .env (
    echo El archivo .env ya existe.
    echo.
    choice /C SN /M "Deseas sobrescribirlo"
    if errorlevel 2 goto :end
)

(
    echo VITE_EMAILJS_SERVICE_ID=service_2a16hu3
    echo VITE_EMAILJS_TEMPLATE_ID=template_vlah8w9
    echo VITE_EMAILJS_PUBLIC_KEY=rpKoOd8FghRGUHKv6
) > .env

echo.
echo Archivo .env creado exitosamente!
echo.
echo Variables configuradas:
echo   - VITE_EMAILJS_SERVICE_ID=service_2a16hu3
echo   - VITE_EMAILJS_TEMPLATE_ID=template_vlah8w9
echo   - VITE_EMAILJS_PUBLIC_KEY=rpKoOd8FghRGUHKv6
echo.
echo IMPORTANTE: Reinicia el servidor de desarrollo para que los cambios surtan efecto.
echo.

:end
pause

