# Solución: Error de Deployment en Render

## 🔴 Error Actual

```
Deploy failed for 2767988: Corregir buildCommand: agregar migraciones
Exited with status 1 while building your code
```

## 🔍 Pasos para Diagnosticar

### 1. Ver los Logs de Render

1. En Render Dashboard, ve al servicio **kanban-backend**
2. Ve a la pestaña **Logs**
3. Busca el error específico (generalmente aparece en rojo)
4. Copia el error completo

**Errores comunes:**
- `ModuleNotFoundError`: Dependencia faltante
- `django.db.utils.OperationalError`: Problema con la base de datos
- `CommandError`: Error en un comando de Django
- `ImportError`: Error de importación

### 2. Verificar Variables de Entorno

1. Ve al servicio **kanban-backend**
2. Ve a la pestaña **Environment**
3. Verifica que estas variables estén configuradas:

```
PYTHON_VERSION=3.11.0
SECRET_KEY=<debe estar configurado>
DEBUG=False
ALLOWED_HOSTS=kanban-backend.onrender.com,*.onrender.com
USE_HTTPS=True
DATABASE_URL=<debe tener la URL de la base de datos>
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://heiner2001.github.io,https://heiner2001.github.io/ProyectoFinal
CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://heiner2001.github.io,https://heiner2001.github.io/ProyectoFinal
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SAMESITE=None
CSRF_COOKIE_SECURE=True
```

### 3. Verificar que la Base de Datos Esté Creada

1. En Render Dashboard, verifica que exista un servicio **PostgreSQL**
2. Si no existe, créala:
   - **New +** → **PostgreSQL**
   - Name: `kanban-database`
   - Plan: Free
   - Crea la base de datos
3. Copia la **Internal Database URL**
4. En el servicio **kanban-backend**, agrega la variable `DATABASE_URL` con esa URL

## 🔧 Soluciones Comunes

### Solución 1: DATABASE_URL No Configurada

**Error típico:**
```
django.db.utils.OperationalError: could not connect to server
```

**Solución:**
1. Crea la base de datos PostgreSQL en Render
2. Copia la **Internal Database URL**
3. En **kanban-backend** → **Environment**, agrega:
   ```
   DATABASE_URL=<pega la URL aquí>
   ```
4. Haz clic en **Manual Deploy** para volver a intentar

### Solución 2: Error en Migraciones

**Error típico:**
```
CommandError: No migrations to apply
```

**Solución temporal:**
Si las migraciones fallan, puedes modificar el `buildCommand` para que no falle si no hay migraciones:

1. En Render, ve a **Settings** del servicio
2. Cambia el **Build Command** a:
   ```
   pip install -r requirements.txt && python manage.py migrate --run-syncdb || true && python manage.py collectstatic --noinput
   ```

### Solución 3: Dependencias Faltantes

**Error típico:**
```
ModuleNotFoundError: No module named 'X'
```

**Solución:**
1. Verifica que `requirements.txt` tenga todas las dependencias
2. Asegúrate de que el archivo esté en la raíz del proyecto
3. Haz push de los cambios a GitHub
4. Render desplegará automáticamente

### Solución 4: Error en collectstatic

**Error típico:**
```
CommandError: Error collecting static files
```

**Solución:**
1. Verifica que `STATIC_ROOT` esté configurado en `settings.py`
2. Asegúrate de que WhiteNoise esté en `INSTALLED_APPS` (no necesario, está en MIDDLEWARE)
3. Si el error persiste, puedes hacer el build sin collectstatic temporalmente:
   ```
   pip install -r requirements.txt && python manage.py migrate
   ```

## 📝 Pasos Recomendados

1. **Revisa los Logs primero** para ver el error específico
2. **Verifica DATABASE_URL** - este es el error más común
3. **Verifica todas las variables de entorno** están configuradas
4. **Intenta Manual Deploy** después de corregir los problemas

## ✅ Después de Corregir

Una vez que el deployment sea exitoso:
1. Ve a **Logs** y verifica que el servidor esté corriendo
2. Abre: `https://kanban-backend-9wbt.onrender.com/api/user/`
3. Debe responder (aunque sea error 401)
4. Crea usuarios con: `python manage.py createsuperuser` en **Shell**

