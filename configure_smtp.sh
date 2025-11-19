#!/bin/bash

echo "========================================"
echo "Configuración de SMTP para envío de correos"
echo "========================================"
echo ""

echo "Este script te ayudará a configurar las variables de entorno para SMTP."
echo ""
echo "IMPORTANTE: Estas variables solo estarán activas en esta sesión de terminal."
echo "Para hacerlas permanentes, agrégalas a ~/.bashrc o ~/.zshrc"
echo ""

read -p "Ingresa tu email (ej: tu-email@gmail.com): " EMAIL_HOST_USER
read -sp "Ingresa tu contraseña de aplicación: " EMAIL_HOST_PASSWORD
echo ""
read -p "Servidor SMTP (Enter para Gmail: smtp.gmail.com): " EMAIL_HOST
read -p "Puerto SMTP (Enter para 587): " EMAIL_PORT
read -p "Usar TLS? (Enter para True): " EMAIL_USE_TLS

EMAIL_HOST=${EMAIL_HOST:-smtp.gmail.com}
EMAIL_PORT=${EMAIL_PORT:-587}
EMAIL_USE_TLS=${EMAIL_USE_TLS:-True}

export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST
export EMAIL_PORT
export EMAIL_USE_TLS
export EMAIL_HOST_USER
export EMAIL_HOST_PASSWORD
export DEFAULT_FROM_EMAIL=$EMAIL_HOST_USER

echo ""
echo "========================================"
echo "Configuración aplicada:"
echo "========================================"
echo "EMAIL_BACKEND=$EMAIL_BACKEND"
echo "EMAIL_HOST=$EMAIL_HOST"
echo "EMAIL_PORT=$EMAIL_PORT"
echo "EMAIL_USE_TLS=$EMAIL_USE_TLS"
echo "EMAIL_HOST_USER=$EMAIL_HOST_USER"
echo "DEFAULT_FROM_EMAIL=$DEFAULT_FROM_EMAIL"
echo "========================================"
echo ""

echo "Para usar estas variables, ejecuta el servidor en esta misma sesión de terminal."
echo "O copia estos comandos export y ejecútalos antes de iniciar el servidor."
echo ""

