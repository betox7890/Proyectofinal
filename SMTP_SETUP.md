# Configuración SMTP para Envío de Correos

Este documento explica cómo configurar el envío de correos electrónicos usando SMTP.

## Configuración Rápida

### Opción 1: Variables de Entorno (Recomendado)

1. Crea un archivo `.env` en la raíz del proyecto (o usa variables de entorno del sistema):

**Windows (PowerShell):**
```powershell
$env:EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
$env:EMAIL_HOST="smtp.gmail.com"
$env:EMAIL_PORT="587"
$env:EMAIL_USE_TLS="True"
$env:EMAIL_HOST_USER="tu-email@gmail.com"
$env:EMAIL_HOST_PASSWORD="tu-contraseña-de-aplicacion"
$env:DEFAULT_FROM_EMAIL="tu-email@gmail.com"
```

**Windows (CMD):**
```cmd
set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
set EMAIL_HOST=smtp.gmail.com
set EMAIL_PORT=587
set EMAIL_USE_TLS=True
set EMAIL_HOST_USER=tu-email@gmail.com
set EMAIL_HOST_PASSWORD=tu-contraseña-de-aplicacion
set DEFAULT_FROM_EMAIL=tu-email@gmail.com
```

**Linux/Mac:**
```bash
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USE_TLS=True
export EMAIL_HOST_USER=tu-email@gmail.com
export EMAIL_HOST_PASSWORD=tu-contraseña-de-aplicacion
export DEFAULT_FROM_EMAIL=tu-email@gmail.com
```

### Opción 2: Editar settings.py directamente

Edita `proyectofinal/settings.py` y modifica los valores directamente:

```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-contraseña-de-aplicacion'
DEFAULT_FROM_EMAIL = 'tu-email@gmail.com'
```

## Configuración para Gmail

### Paso 1: Habilitar verificación en 2 pasos
1. Ve a tu cuenta de Google: https://myaccount.google.com/
2. Seguridad > Verificación en 2 pasos > Activar

### Paso 2: Crear una contraseña de aplicación
1. Ve a: https://myaccount.google.com/apppasswords
2. Selecciona "Correo" y "Otro (nombre personalizado)"
3. Escribe "Kanban Board" o el nombre que prefieras
4. Copia la contraseña de 16 caracteres generada
5. Usa esta contraseña en `EMAIL_HOST_PASSWORD` (NO tu contraseña normal de Gmail)

### Paso 3: Configurar en el proyecto
```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'xxxx xxxx xxxx xxxx'  # La contraseña de aplicación de 16 caracteres
DEFAULT_FROM_EMAIL = 'tu-email@gmail.com'
```

## Configuración para Outlook/Hotmail

```python
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@outlook.com'
EMAIL_HOST_PASSWORD = 'tu-contraseña'
DEFAULT_FROM_EMAIL = 'tu-email@outlook.com'
```

## Configuración para otros proveedores

### Yahoo Mail
```python
EMAIL_HOST = 'smtp.mail.yahoo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

### SendGrid
```python
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'tu-api-key-de-sendgrid'
```

### Mailgun
```python
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'postmaster@tu-dominio.mailgun.org'
EMAIL_HOST_PASSWORD = 'tu-contraseña-de-mailgun'
```

## Verificación

### Prueba rápida desde Django Shell

```python
python manage.py shell

from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Prueba de correo',
    'Este es un correo de prueba.',
    settings.DEFAULT_FROM_EMAIL,
    ['tu-email-destino@example.com'],
    fail_silently=False,
)
```

Si recibes el correo, la configuración está correcta.

### Prueba desde el calendario

1. Ve al calendario en la aplicación
2. Haz clic en "📧 Enviar Recordatorios"
3. Selecciona las opciones deseadas
4. Haz clic en "Enviar Recordatorios"
5. Verifica que los correos lleguen a los destinatarios

## Solución de Problemas

### Error: "SMTPAuthenticationError"
- Verifica que `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD` sean correctos
- Para Gmail, asegúrate de usar una contraseña de aplicación, no tu contraseña normal
- Verifica que la verificación en 2 pasos esté activada (Gmail)

### Error: "Connection refused" o "Timeout"
- Verifica que `EMAIL_HOST` y `EMAIL_PORT` sean correctos
- Verifica tu conexión a internet
- Algunos proveedores bloquean conexiones desde ciertas IPs

### Los correos no llegan
- Revisa la carpeta de spam
- Verifica que `DEFAULT_FROM_EMAIL` sea válido
- Revisa los logs del servidor para ver errores
- Verifica que los destinatarios tengan email configurado

### Volver a modo desarrollo (consola)
Si quieres volver a ver los correos en la consola:

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

O usa la variable de entorno:
```bash
set EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## Seguridad

⚠️ **IMPORTANTE**: Nunca subas archivos `.env` o `settings.py` con contraseñas reales a repositorios públicos.

- Usa variables de entorno en producción
- Considera usar servicios como AWS SES, SendGrid, o Mailgun para producción
- Las contraseñas de aplicación son más seguras que contraseñas normales

