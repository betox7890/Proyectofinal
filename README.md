# ProyectoFinal - Sistema de Gestión Kanban

## 📋 Descripción

Sistema completo de gestión de tareas tipo Trello desarrollado con Django (Backend) y React + Vite (Frontend). Permite crear tableros Kanban con listas, tareas, subtareas, comentarios, actividades, calendario, recordatorios y autenticación de dos factores (2FA).

**Repositorio:** https://github.com/betox7890/ProyectoFinal

## 🛠️ Tecnologías

### Backend
- **Django 4.2+**: Framework web de Python
- **Django REST Framework**: API REST para comunicación con el frontend
- **PostgreSQL/SQLite**: Base de datos (PostgreSQL en Railway, SQLite en desarrollo)
- **WhiteNoise**: Servir archivos estáticos en producción
- **django-cors-headers**: Configuración CORS para permitir peticiones desde React
- **Celery + Redis**: Tareas asíncronas (recordatorios)
- **Channels**: WebSockets para actualizaciones en tiempo real
- **Gunicorn**: Servidor WSGI para producción

### Frontend
- **React 19**: Biblioteca de JavaScript para interfaces de usuario
- **Vite**: Herramienta de construcción y desarrollo
- **React Router**: Navegación entre páginas
- **Axios**: Cliente HTTP para peticiones al backend

## 📁 Estructura del Proyecto

```
ProyectoFinal/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── Procfile
│   ├── core/              # Proyecto Django
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── api/               # App con lógica del tablero
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── api_views.py
│   │   └── ...
│   ├── staticfiles/       # Archivos estáticos (generados)
│   ├── media/             # Archivos subidos por usuarios
│   └── logs/               # Logs de la aplicación
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── services/
│   │   └── config/
│   ├── dist/               # Build de producción (generado)
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 🚀 Instalación

### Backend

1. **Navegar a la carpeta backend:**
   ```bash
   cd backend
   ```

2. **Crear entorno virtual (recomendado):**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Aplicar migraciones:**
   ```bash
   python manage.py migrate
   ```

5. **Crear superusuario (opcional):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Iniciar servidor de desarrollo:**
   ```bash
   python manage.py runserver
   ```

   El servidor estará disponible en `http://localhost:8000`

### Frontend

1. **Navegar a la carpeta frontend:**
   ```bash
   cd frontend
   ```

2. **Instalar dependencias:**
   ```bash
   npm install
   ```

3. **Iniciar servidor de desarrollo:**
   ```bash
   npm run dev
   ```

   El servidor estará disponible en `http://localhost:5173`

## 🌐 Despliegue

### Backend en Railway

1. **Crear cuenta en Railway** (https://railway.app)

2. **Crear nuevo proyecto** y conectar con tu repositorio de GitHub:
   - Seleccionar el repositorio: `betox7890/ProyectoFinal`
   - Seleccionar la carpeta: `backend`

3. **Configurar variables de entorno en Railway:**

   | Variable | Valor | Descripción |
   |----------|-------|-------------|
   | `SECRET_KEY` | `tu-secret-key-generada` | Clave secreta de Django (generar nueva para producción) |
   | `DEBUG` | `False` | Desactivar modo debug en producción |
   | `ALLOWED_HOSTS` | `tu-proyecto.up.railway.app` | Dominio de Railway (se asigna automáticamente) |
   | `DATABASE_URL` | *(automático)* | Railway proporciona PostgreSQL automáticamente |
   | `CORS_ALLOWED_ORIGINS` | `https://betox7890.github.io` | URL del frontend en GitHub Pages |
   | `CSRF_TRUSTED_ORIGINS` | `https://betox7890.github.io,https://tu-proyecto.up.railway.app` | Orígenes confiables para CSRF |
   | `USE_HTTPS` | `True` | Activar HTTPS para cookies |
   | `EMAIL_HOST_USER` | `tu-email@gmail.com` | Email SMTP (opcional) |
   | `EMAIL_HOST_PASSWORD` | `tu-password` | Contraseña SMTP (opcional) |

   **Generar SECRET_KEY:**
   ```python
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

4. **Railway detectará automáticamente:**
   - `Procfile` para el comando de inicio
   - `requirements.txt` para instalar dependencias
   - `release` command en Procfile ejecutará migraciones automáticamente

5. **Obtener la URL de tu backend:**
   - Railway asignará una URL como: `https://tu-proyecto.up.railway.app`
   - Copiar esta URL para configurar el frontend

### Frontend en GitHub Pages

1. **Instalar gh-pages:**
   ```bash
   cd frontend
   npm install --save-dev gh-pages
   ```

2. **Agregar scripts al package.json:**
   ```json
   {
     "scripts": {
       "predeploy": "npm run build",
       "deploy": "gh-pages -d dist"
     }
   }
   ```

3. **Actualizar src/config/api.js con la URL de Railway:**
   ```javascript
   if (window.location.host.includes('github.io')) {
     return 'https://tu-proyecto.up.railway.app';  // Tu URL de Railway
   }
   ```

4. **Construir el proyecto:**
   ```bash
   npm run build
   ```

5. **Desplegar a GitHub Pages:**
   ```bash
   npm run deploy
   ```

6. **Configurar GitHub Pages:**
   - Ir a Settings > Pages en tu repositorio: `betox7890/ProyectoFinal`
   - Seleccionar la rama `gh-pages` como fuente
   - El sitio estará disponible en: `https://betox7890.github.io/ProyectoFinal/`

7. **Actualizar variables de entorno en Railway:**
   - `CORS_ALLOWED_ORIGINS`: `https://betox7890.github.io`
   - `CSRF_TRUSTED_ORIGINS`: `https://betox7890.github.io,https://tu-proyecto.up.railway.app`

## 🔐 Autenticación y CSRF

### En Desarrollo

- Las cookies funcionan automáticamente con `SameSite=Lax`
- El CSRF token se incluye automáticamente en todas las peticiones
- El frontend usa `withCredentials: true` para enviar cookies

### En Producción (Railway + GitHub Pages)

**Configuración necesaria:**

1. **Backend (Railway):**
   - `USE_HTTPS=True` → Activa `SESSION_COOKIE_SECURE=True` y `CSRF_COOKIE_SECURE=True`
   - `SESSION_COOKIE_SAMESITE=None` → Permite cookies cross-origin
   - `CSRF_COOKIE_SAMESITE=None` → Permite CSRF cross-origin
   - `CORS_ALLOWED_ORIGINS` debe incluir la URL de GitHub Pages
   - `CSRF_TRUSTED_ORIGINS` debe incluir ambas URLs (Railway y GitHub Pages)

2. **Frontend:**
   - `withCredentials: true` en todas las peticiones Axios
   - La URL de la API se detecta automáticamente según el host

### Cómo hacer Login en Producción

1. Abrir: `https://betox7890.github.io/ProyectoFinal/`
2. El frontend detectará automáticamente que está en GitHub Pages
3. Usará la URL de Railway configurada en `src/config/api.js`
4. Las cookies se enviarán correctamente con `SameSite=None; Secure`
5. El CSRF token se incluirá automáticamente

**Si hay problemas de CORS o CSRF:**
- Verificar que `CORS_ALLOWED_ORIGINS` incluya la URL exacta de GitHub Pages
- Verificar que `CSRF_TRUSTED_ORIGINS` incluya ambas URLs
- Verificar que `USE_HTTPS=True` en Railway
- Verificar que el frontend use `withCredentials: true`

## 📡 API Endpoints

### Autenticación
- `POST /api/login/` - Iniciar sesión
- `POST /logout/` - Cerrar sesión
- `GET /api/user/` - Obtener usuario actual

### Tablero
- `GET /api/board/` - Obtener tablero completo
- `POST /api/lists/` - Crear lista
- `POST /api/lists/<id>/delete/` - Eliminar lista
- `POST /api/lists/<id>/color/` - Cambiar color de lista

### Tareas
- `POST /api/tasks/` - Crear tarea
- `PATCH /api/tasks/<id>/` - Actualizar tarea
- `POST /api/tasks/<id>/delete/` - Eliminar tarea
- `POST /api/tasks/<id>/move/` - Mover tarea

### Subtareas
- `POST /api/tasks/<id>/subtasks/` - Crear subtarea
- `PATCH /api/subtasks/<id>/` - Actualizar subtarea
- `POST /api/subtasks/<id>/delete/` - Eliminar subtarea
- `POST /api/subtasks/<id>/toggle/` - Completar/descompletar subtarea

### Actividades
- `GET /api/activities/` - Obtener actividades
- `POST /api/add-activity-comment/<id>/` - Agregar comentario

### Calendario
- `GET /api/calendar/` - Obtener calendario
- `POST /calendar/send-reminders/` - Enviar recordatorios

## 🔧 Configuración de Desarrollo

### Backend
- Base de datos: SQLite (desarrollo) / PostgreSQL (producción en Railway)
- Puerto: 8000
- Debug: True (desarrollo) / False (producción)

### Frontend
- Puerto: 5173
- Base path: `/ProyectoFinal/` (para GitHub Pages)

## 📝 Notas Importantes

- **Base de datos**: Railway proporciona PostgreSQL automáticamente mediante `DATABASE_URL`
- **Archivos estáticos**: WhiteNoise los sirve en producción
- **Media files**: Se guardan en `/backend/media/` (considerar almacenamiento externo en producción)
- **Logs**: Se guardan en `/backend/logs/`
- **Migraciones**: Se ejecutan automáticamente en Railway mediante el comando `release` en Procfile

## 🐛 Solución de Problemas

### Error de CORS en producción
- Verificar que `CORS_ALLOWED_ORIGINS` incluya la URL exacta de GitHub Pages
- Verificar que no haya espacios en las URLs

### Error de CSRF en producción
- Verificar que `CSRF_TRUSTED_ORIGINS` incluya ambas URLs (Railway y GitHub Pages)
- Verificar que `USE_HTTPS=True`
- Verificar que el frontend incluya el header `X-CSRFToken`

### Cookies no se envían
- Verificar que `withCredentials: true` esté en todas las peticiones
- Verificar que `USE_HTTPS=True` en Railway
- Verificar que `SESSION_COOKIE_SAMESITE=None` y `SESSION_COOKIE_SECURE=True`

## 📄 Licencia

Este proyecto es parte de un trabajo académico.

---

**Desarrollado con ❤️ usando Django y React**
