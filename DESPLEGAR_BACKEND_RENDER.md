# 🚀 Desplegar Backend en Render - Guía Rápida

## ✅ Pre-requisitos Completados

- ✅ `requirements.txt` actualizado con dependencias de Render
- ✅ `settings.py` configurado para PostgreSQL y WhiteNoise
- ✅ `render.yaml` configurado con todas las variables de entorno

## 📋 Pasos para Desplegar

### Paso 1: Crear Cuenta en Render

1. Ve a https://render.com
2. Haz clic en **Sign Up** (arriba a la derecha)
3. Selecciona **Sign up with GitHub**
4. Autoriza a Render para acceder a tus repositorios

### Paso 2: Crear Base de Datos PostgreSQL

1. En Render Dashboard, haz clic en **New +** (arriba a la derecha)
2. Selecciona **PostgreSQL**
3. Configura:
   - **Name**: `kanban-database`
   - **Database**: `kanban_db`
   - **User**: `kanban_user`
   - **Region**: `Oregon` (o la más cercana a ti)
   - **Plan**: `Free`
4. Haz clic en **Create Database**
5. ⚠️ **IMPORTANTE**: Copia la **Internal Database URL** (la necesitarás después)
   - Se ve algo como: `postgresql://kanban_user:password@dpg-xxxxx-a/kanban_db`

### Paso 3: Crear Web Service con Blueprint

1. En Render Dashboard, haz clic en **New +**
2. Selecciona **Blueprint**
3. Conecta tu repositorio:
   - Si no está conectado, haz clic en **Connect account**
   - Selecciona el repositorio: `Heiner2001/ProyectoFinal`
   - Haz clic en **Connect**
4. Render detectará automáticamente el archivo `render.yaml`
5. Verás una vista previa de los servicios:
   - **kanban-backend** (Web Service)
   - **kanban-database** (PostgreSQL Database) - Si no aparece, créala manualmente primero
6. Haz clic en **Apply**

### Paso 4: Configurar Variables de Entorno

Después de que Render cree los servicios:

1. Ve al servicio **kanban-backend** (haz clic en él)
2. Ve a la pestaña **Environment**
3. Verifica/agrega estas variables:

```
PYTHON_VERSION=3.11.0
SECRET_KEY=<Render lo genera automáticamente>
DEBUG=False
ALLOWED_HOSTS=kanban-backend.onrender.com,*.onrender.com
USE_HTTPS=True
DATABASE_URL=<Pega aquí la Internal Database URL que copiaste del Paso 2>
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://heiner2001.github.io,https://heiner2001.github.io/ProyectoFinal
CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://heiner2001.github.io,https://heiner2001.github.io/ProyectoFinal
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SAMESITE=None
CSRF_COOKIE_SECURE=True
```

4. Si falta alguna variable, haz clic en **Add Environment Variable** y agrégalas
5. **IMPORTANTE**: Asegúrate de que `DATABASE_URL` tenga el valor correcto de la base de datos

### Paso 5: Conectar la Base de Datos al Web Service

1. En el servicio **kanban-backend**, ve a la pestaña **Environment**
2. Verifica que `DATABASE_URL` esté configurada correctamente
3. Si no está, agrega la variable `DATABASE_URL` con el valor de la **Internal Database URL** de la base de datos

### Paso 6: Esperar el Deployment

1. Ve a la pestaña **Logs** del servicio **kanban-backend**
2. Verás el proceso de build en tiempo real:
   - Clonando repositorio...
   - Instalando dependencias...
   - Ejecutando migraciones...
   - Recolectando archivos estáticos...
   - Iniciando servidor...
3. ⏱️ Esto puede tardar 5-10 minutos
4. Cuando veas "Application is live", el backend está listo

### Paso 7: Crear Usuarios

Una vez que el backend esté desplegado:

1. Ve al servicio **kanban-backend** en Render
2. Ve a la pestaña **Shell**
3. Ejecuta:
   ```bash
   python manage.py createsuperuser
   ```
4. Sigue las instrucciones para crear el usuario
5. Repite para crear más usuarios si es necesario

### Paso 8: Verificar que Funciona

1. Copia la URL del servicio (algo como `https://kanban-backend.onrender.com`)
2. Abre en tu navegador: `https://kanban-backend.onrender.com/api/user/`
3. Debe responder (aunque sea un error 401, significa que funciona)

## ✅ Listo!

Una vez completado:
- ✅ El backend estará disponible en: `https://kanban-backend.onrender.com`
- ✅ El frontend en GitHub Pages podrá conectarse
- ✅ Podrás hacer login desde `https://heiner2001.github.io/ProyectoFinal/`

## 🔧 Solución de Problemas

### Error: "Build failed"

- Revisa los logs en Render
- Verifica que `requirements.txt` tenga todas las dependencias
- Asegúrate de que el código esté en la rama `main` de GitHub

### Error: "Database connection failed"

- Verifica que `DATABASE_URL` esté configurada correctamente
- Asegúrate de que la base de datos esté creada y en la misma región

### Error: "Application failed to start"

- Verifica que el **Start Command** sea: `daphne -b 0.0.0.0 -p $PORT proyectofinal.asgi:application`
- Revisa los logs para ver el error específico

### El servicio está en "Sleep"

- Es normal en el plan free
- La primera petición puede tardar ~30 segundos en "despertar"

