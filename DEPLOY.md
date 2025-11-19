# Guía de Despliegue

Esta guía explica cómo desplegar el proyecto Kanban en producción.

## Estructura del Proyecto

- **Backend**: Django con ASGI (Daphne) - Desplegar en Render
- **Frontend**: React con Vite - Desplegar en Vercel

## Prerrequisitos

1. Cuenta en [GitHub](https://github.com)
2. Cuenta en [Render](https://render.com) (para backend)
3. Cuenta en [Vercel](https://vercel.com) (para frontend)

## Paso 1: Subir el proyecto a GitHub

1. Inicializar el repositorio Git:
```bash
git init
git add .
git commit -m "Initial commit"
```

2. Crear un repositorio en GitHub y conectarlo:
```bash
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git branch -M main
git push -u origin main
```

## Paso 2: Desplegar el Backend en Render

1. Ve a [Render Dashboard](https://dashboard.render.com)
2. Click en "New +" → "Web Service"
3. Conecta tu repositorio de GitHub
4. Configura el servicio:
   - **Name**: `kanban-backend`
   - **Region**: `Oregon (US West)`
   - **Branch**: `main`
   - **Root Directory**: `.` (raíz del proyecto)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `daphne -b 0.0.0.0 -p $PORT proyectofinal.asgi:application`
   - **Plan**: `Free`

5. Configurar Variables de Entorno:
   - `SECRET_KEY`: Genera una clave secreta (usa: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `kanban-backend.onrender.com` (se actualizará después)
   - `USE_HTTPS`: `True`
   - `CORS_ALLOWED_ORIGINS`: `https://tu-frontend.vercel.app` (se actualizará después del despliegue del frontend)
   - `CSRF_TRUSTED_ORIGINS`: `https://tu-frontend.vercel.app` (se actualizará después)

6. Click en "Create Web Service"

7. Después del despliegue, copia la URL del backend (ejemplo: `https://kanban-backend.onrender.com`)

## Paso 3: Desplegar el Frontend en Vercel

1. Ve a [Vercel Dashboard](https://vercel.com/dashboard)
2. Click en "Add New..." → "Project"
3. Importa tu repositorio de GitHub
4. Configura el proyecto:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

5. Configurar Variables de Entorno:
   - `VITE_API_BASE_URL`: `https://kanban-backend.onrender.com` (URL de tu backend en Render)

6. Click en "Deploy"

7. Después del despliegue, copia la URL del frontend (ejemplo: `https://tu-proyecto.vercel.app`)

## Paso 4: Actualizar Configuraciones

### Actualizar Backend (Render)

1. Ve a tu servicio en Render
2. Ve a "Environment"
3. Actualiza estas variables:
   - `CORS_ALLOWED_ORIGINS`: `https://tu-frontend.vercel.app`
   - `CSRF_TRUSTED_ORIGINS`: `https://tu-frontend.vercel.app`
   - `ALLOWED_HOSTS`: `kanban-backend.onrender.com,tu-frontend.vercel.app`

4. Reinicia el servicio

### Actualizar Frontend (Vercel)

1. Ve a tu proyecto en Vercel
2. Ve a "Settings" → "Environment Variables"
3. Actualiza `VITE_API_BASE_URL` si es necesario
4. Vuelve a desplegar el proyecto

## Paso 5: Configurar Base de Datos (Opcional)

El proyecto usa SQLite por defecto. Para producción, considera usar PostgreSQL:

1. En Render, crea una base de datos PostgreSQL
2. Instala `psycopg2-binary`:
   ```bash
   pip install psycopg2-binary
   ```
3. Agrega a `requirements.txt`:
   ```
   psycopg2-binary>=2.9.0
   ```
4. Actualiza `DATABASES` en `settings.py` para usar la URL de conexión de Render

## URLs del Proyecto

Después del despliegue, tendrás:
- **Backend**: `https://kanban-backend.onrender.com`
- **Frontend**: `https://tu-proyecto.vercel.app`

## Notas Importantes

- El backend en Render puede tardar algunos minutos en iniciar después de estar inactivo (plan gratuito)
- Asegúrate de configurar correctamente las variables de entorno CORS
- Las cookies funcionan correctamente con HTTPS en producción
- Para Celery y Redis, necesitarás configurar servicios adicionales en Render (no incluidos en el plan gratuito básico)

## Solución de Problemas

### Error de CORS
- Verifica que `CORS_ALLOWED_ORIGINS` incluya exactamente la URL del frontend (con https://)

### Error de CSRF
- Verifica que `CSRF_TRUSTED_ORIGINS` incluya la URL del frontend
- Asegúrate de que `USE_HTTPS` esté en `True`

### Backend no responde
- Verifica los logs en Render
- Asegúrate de que el comando de inicio sea correcto
- Verifica que todas las dependencias estén en `requirements.txt`

