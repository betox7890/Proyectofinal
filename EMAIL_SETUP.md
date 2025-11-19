# Configuración de Envío de Correos Electrónicos

Este proyecto incluye un sistema de recordatorios por correo electrónico para tareas y subtareas próximas a vencer, utilizando Django + Celery + Redis.

## Características

- ✅ Envía recordatorios para tareas que vencen en 1, 3 y 7 días
- ✅ Envía recordatorios para subtareas próximas a vencer
- ✅ Incluye información sobre subtareas pendientes relacionadas
- ✅ Mensajes personalizados según la urgencia
- ✅ Logging completo de todas las operaciones

## Requisitos Previos

1. **Redis** debe estar ejecutándose en `127.0.0.1:6379`
2. **Celery** y **django-celery-beat** instalados (ya están en requirements.txt)

## Configuración

### 1. Configuración de Correo para Desarrollo

Por defecto, el sistema usa el backend de consola que muestra los correos en la terminal. No requiere configuración adicional.

### 2. Configuración de Correo para Producción (SMTP)

Edita `proyectofinal/settings.py` y descomenta/ajusta la configuración SMTP:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # o tu servidor SMTP
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-contraseña-de-aplicacion'
DEFAULT_FROM_EMAIL = 'tu-email@gmail.com'
```

**Nota para Gmail:** Necesitarás usar una "Contraseña de aplicación" en lugar de tu contraseña normal. Ve a tu cuenta de Google > Seguridad > Contraseñas de aplicaciones.

### 3. Configuración mediante Variables de Entorno

También puedes configurar usando variables de entorno:

```bash
# Windows
set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
set EMAIL_HOST=smtp.gmail.com
set EMAIL_PORT=587
set EMAIL_USE_TLS=True
set EMAIL_HOST_USER=tu-email@gmail.com
set EMAIL_HOST_PASSWORD=tu-contraseña
set DEFAULT_FROM_EMAIL=tu-email@gmail.com

# Linux/Mac
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USE_TLS=True
export EMAIL_HOST_USER=tu-email@gmail.com
export EMAIL_HOST_PASSWORD=tu-contraseña
export DEFAULT_FROM_EMAIL=tu-email@gmail.com
```

## Iniciar el Sistema

### 1. Iniciar Redis

**Windows:**
- Descarga Redis desde: https://github.com/microsoftarchive/redis/releases
- Ejecuta `redis-server.exe`

**Linux/Mac:**
```bash
sudo systemctl start redis
# o
redis-server
```

### 2. Iniciar Celery Worker y Celery Beat

**Windows:**
```bash
start_celery.bat
```

**Linux/Mac:**
```bash
chmod +x start_celery.sh
./start_celery.sh
```

O manualmente:
```bash
# Terminal 1: Celery Worker
celery -A proyectofinal worker --loglevel=info

# Terminal 2: Celery Beat
celery -A proyectofinal beat --loglevel=info
```

### 3. Iniciar el Servidor Django

```bash
# Windows
run_server.bat

# Linux/Mac
./run_server.sh
```

## Funcionamiento

- **Frecuencia:** La tarea se ejecuta cada 24 horas (configurable en `settings.py`)
- **Días de recordatorio:** 1, 3 y 7 días antes de la fecha de vencimiento
- **Destinatarios:** 
  - Para tareas: El usuario que creó la tarea
  - Para subtareas: El usuario que creó la subtarea, o si no tiene email, el creador de la tarea padre

## Pruebas

Para probar el sistema sin esperar 24 horas:

```python
# En el shell de Django
python manage.py shell

from kanban.tasks import send_due_date_reminders
result = send_due_date_reminders()
print(result)
```

O ejecuta directamente:
```bash
celery -A proyectofinal call kanban.tasks.send_due_date_reminders
```

## Logs

Los logs se guardan en:
- Archivo: `logs/kanban.log`
- También se muestran en la consola cuando ejecutas Celery

## Solución de Problemas

### Redis no está disponible
- Verifica que Redis esté ejecutándose: `redis-cli ping` (debe responder "PONG")
- Verifica la configuración en `settings.py`: `CELERY_BROKER_URL`

### Los correos no se envían
- Verifica los logs de Celery para ver errores
- En desarrollo, verifica la consola donde se ejecuta Celery
- En producción, verifica la configuración SMTP
- Asegúrate de que los usuarios tengan email configurado

### La tarea no se ejecuta automáticamente
- Verifica que Celery Beat esté ejecutándose
- Verifica el schedule en `CELERY_BEAT_SCHEDULE` en `settings.py`
- Revisa los logs de Celery Beat

## Personalización

### Cambiar la frecuencia de ejecución

En `proyectofinal/settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'send-task-reminders-daily': {
        'task': 'kanban.tasks.send_due_date_reminders',
        'schedule': crontab(hour=9, minute=0),  # Ejecutar a las 9 AM diariamente
    },
}
```

### Cambiar los días de recordatorio

En `kanban/tasks.py`, modifica:

```python
days_ahead = [1, 3, 7]  # Cambia estos valores según necesites
```

