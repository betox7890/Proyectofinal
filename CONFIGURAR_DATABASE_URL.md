# Configurar DATABASE_URL en Render

## ✅ Base de Datos Creada

Ya tienes `kanban-database` creada. Ahora necesitas configurar `DATABASE_URL` en el servicio `kanban-backend`.

## 📋 Pasos para Configurar DATABASE_URL

### Paso 1: Obtener la Internal Database URL

1. En Render Dashboard, haz clic en el servicio **kanban-database**
2. Ve a la pestaña **Info** o **Connections**
3. Busca la sección **Internal Database URL**
4. Haz clic en el botón **Copy** o copia manualmente la URL
   - Se ve algo como: `postgresql://kanban_user:password@dpg-xxxxx-a.oregon-postgres.render.com/kanban_db`
   - ⚠️ **IMPORTANTE**: Usa la **Internal Database URL**, NO la External

### Paso 2: Agregar DATABASE_URL al Web Service

1. Ve al servicio **kanban-backend** (el web service, no la base de datos)
2. Ve a la pestaña **Environment**
3. Haz clic en **Add Environment Variable**
4. Configura:
   - **Key**: `DATABASE_URL`
   - **Value**: Pega la **Internal Database URL** que copiaste
5. Haz clic en **Save Changes**

### Paso 3: Verificar Otras Variables de Entorno

Asegúrate de que estas variables estén configuradas en **kanban-backend** → **Environment**:

```
PYTHON_VERSION=3.11.0
SECRET_KEY=<debe estar configurado automáticamente>
DEBUG=False
ALLOWED_HOSTS=kanban-backend.onrender.com,*.onrender.com
USE_HTTPS=True
DATABASE_URL=<la URL que acabas de agregar>
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://heiner2001.github.io,https://heiner2001.github.io/ProyectoFinal
CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://heiner2001.github.io,https://heiner2001.github.io/ProyectoFinal
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SAMESITE=None
CSRF_COOKIE_SECURE=True
```

### Paso 4: Hacer Manual Deploy

1. En el servicio **kanban-backend**
2. Haz clic en **Manual Deploy** (arriba a la derecha)
3. Selecciona **Deploy latest commit**
4. Espera 5-10 minutos para que se complete el build

### Paso 5: Verificar los Logs

1. Ve a la pestaña **Logs** del servicio **kanban-backend**
2. Verifica que el build sea exitoso
3. Busca mensajes como:
   - ✅ "Running migrations..."
   - ✅ "Collecting static files..."
   - ✅ "Application is live"

## 🔍 Si Aún Hay Errores

### Revisar los Logs

1. Ve a **Logs** del servicio **kanban-backend**
2. Busca errores en rojo
3. Los errores comunes son:
   - `django.db.utils.OperationalError`: DATABASE_URL incorrecta o base de datos no accesible
   - `ModuleNotFoundError`: Dependencia faltante
   - `CommandError`: Error en comando de Django

### Verificar la URL de la Base de Datos

- Asegúrate de usar la **Internal Database URL**, no la External
- La Internal URL es la que funciona dentro de Render
- Debe empezar con `postgresql://`

## ✅ Después del Deployment Exitoso

1. Ve a **Logs** y verifica que el servidor esté corriendo
2. Abre: `https://kanban-backend-9wbt.onrender.com/api/user/`
   - Debe responder (aunque sea error 401, significa que funciona)
3. Crea usuarios:
   - Ve a **Shell** del servicio **kanban-backend**
   - Ejecuta: `python manage.py createsuperuser`
   - Sigue las instrucciones para crear el usuario

## 📝 Checklist

- [ ] Internal Database URL copiada de kanban-database
- [ ] DATABASE_URL agregada en kanban-backend → Environment
- [ ] Todas las variables de entorno configuradas
- [ ] Manual Deploy ejecutado
- [ ] Logs verificados (sin errores)
- [ ] Servidor corriendo
- [ ] Endpoint `/api/user/` responde
- [ ] Usuarios creados con `createsuperuser`

