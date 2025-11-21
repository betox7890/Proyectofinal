# 🚀 Guía de Despliegue en Render (Gratis)

## 📋 Requisitos Previos

1. Cuenta en [Render.com](https://render.com) (gratis)
2. Tu proyecto en GitHub (ya lo tienes: `https://github.com/betox7890/Proyectofinal`)

---

## 🎯 Opción 1: Despliegue Automático con `render.yaml` (Recomendado)

### Paso 1: Actualizar configuración del frontend

El archivo `render.yaml` ya está creado. Solo necesitas:

1. **Actualizar `frontend/vite.config.js`** para Render:
   ```javascript
   base: "/",  // Cambiar de "/Proyectofinal/" a "/"
   ```

2. **Actualizar `frontend/src/config/api.js`** para detectar Render:
   ```javascript
   if (window.location.host.includes('render.com')) {
     return 'https://proyectofinal-backend.onrender.com';
   }
   ```

### Paso 2: Subir cambios a GitHub

```bash
git add .
git commit -m "Configuración para Render"
git push origin main
```

### Paso 3: Desplegar en Render

1. Ve a [Render Dashboard](https://dashboard.render.com)
2. Click en **"New +"** → **"Blueprint"**
3. Conecta tu repositorio de GitHub: `betox7890/Proyectofinal`
4. Render detectará automáticamente el archivo `render.yaml`
5. Click en **"Apply"**
6. Render creará automáticamente:
   - ✅ Base de datos PostgreSQL
   - ✅ Servicio Backend (Django)
   - ✅ Servicio Frontend (React)

### Paso 4: Configurar Variables de Entorno

Después del despliegue, ve a cada servicio y configura:

**Backend:**
- `SECRET_KEY`: Genera uno nuevo (usa: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- `DEBUG`: `False`
- `ALLOWED_HOSTS`: `proyectofinal-backend.onrender.com`
- `CORS_ALLOWED_ORIGINS`: `https://proyectofinal-frontend.onrender.com`
- `CSRF_TRUSTED_ORIGINS`: `https://proyectofinal-frontend.onrender.com,https://proyectofinal-backend.onrender.com`
- `USE_HTTPS`: `True`

**Frontend:**
- `VITE_API_BASE_URL`: `https://proyectofinal-backend.onrender.com`

### Paso 5: Crear Superusuario

1. Ve al servicio Backend en Render
2. Click en **"Shell"** (terminal)
3. Ejecuta:
   ```bash
   python manage.py createsuperuser
   ```
4. Sigue las instrucciones (username: `admin`, password: `admin123`)

---

## 🎯 Opción 2: Despliegue Manual (Paso a Paso)

### 1. Desplegar Base de Datos PostgreSQL

1. En Render Dashboard → **"New +"** → **"PostgreSQL"**
2. Nombre: `proyectofinal-db`
3. Plan: **Free**
4. Click **"Create Database"**
5. Copia la **"Internal Database URL"** (la necesitarás después)

### 2. Desplegar Backend (Django)

1. **"New +"** → **"Web Service"**
2. Conecta tu repositorio: `betox7890/Proyectofinal`
3. Configuración:
   - **Name**: `proyectofinal-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `cd backend && pip install -r requirements.txt && python manage.py migrate`
   - **Start Command**: `cd backend && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT`
   - **Plan**: **Free**

4. **Variables de Entorno**:
   ```
   PYTHON_VERSION=3.11.0
   SECRET_KEY=<genera uno nuevo>
   DEBUG=False
   ALLOWED_HOSTS=proyectofinal-backend.onrender.com
   DATABASE_URL=<pega la Internal Database URL de PostgreSQL>
   CORS_ALLOWED_ORIGINS=https://proyectofinal-frontend.onrender.com
   CSRF_TRUSTED_ORIGINS=https://proyectofinal-frontend.onrender.com,https://proyectofinal-backend.onrender.com
   USE_HTTPS=True
   ```

5. Click **"Create Web Service"**

### 3. Desplegar Frontend (React)

1. **"New +"** → **"Static Site"**
2. Conecta tu repositorio: `betox7890/Proyectofinal`
3. Configuración:
   - **Name**: `proyectofinal-frontend`
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`
   - **Plan**: **Free**

4. **Variables de Entorno**:
   ```
   VITE_API_BASE_URL=https://proyectofinal-backend.onrender.com
   ```

5. Click **"Create Static Site"**

### 4. Actualizar URLs del Backend

Después de que el frontend esté desplegado, actualiza en el backend:
- `CORS_ALLOWED_ORIGINS`: Agrega la URL real del frontend
- `CSRF_TRUSTED_ORIGINS`: Agrega la URL real del frontend

---

## 🔧 Configuración Adicional

### Actualizar `frontend/vite.config.js` para Render

```javascript
export default defineConfig({
  plugins: [react()],
  base: "/",  // Cambiar a "/" para Render
  server: { port: 5173 }
});
```

### Actualizar `frontend/src/config/api.js` para Render

```javascript
const getApiBaseUrl = () => {
  // Render
  if (window.location.host.includes('render.com')) {
    return 'https://proyectofinal-backend.onrender.com';
  }
  // GitHub Pages
  if (window.location.host.includes('github.io')) {
    return 'https://proyectofinal-production-bfac.up.railway.app';
  }
  // Variable de entorno
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  // Desarrollo local
  return 'http://localhost:8000';
};
```

---

## ✅ Ventajas de Render

- ✅ **Gratis** (con limitaciones razonables)
- ✅ **PostgreSQL gratuito** incluido
- ✅ **SSL/HTTPS automático**
- ✅ **Despliegue automático** desde GitHub
- ✅ **Logs en tiempo real**
- ✅ **Shell/Terminal** para comandos Django
- ✅ **Variables de entorno** fáciles de configurar

---

## ⚠️ Limitaciones del Plan Gratuito

- El servicio se "duerme" después de 15 minutos de inactividad
- La primera petición después de dormir puede tardar ~30 segundos
- 750 horas gratis por mes (suficiente para desarrollo)
- Base de datos PostgreSQL: 90 días de datos (luego se elimina si no hay actividad)

---

## 🔗 URLs Finales

Después del despliegue tendrás:
- **Frontend**: `https://proyectofinal-frontend.onrender.com`
- **Backend**: `https://proyectofinal-backend.onrender.com`
- **Base de Datos**: PostgreSQL (solo accesible desde el backend)

---

## 🆘 Solución de Problemas

### El backend no inicia
- Verifica que `DATABASE_URL` esté correctamente configurada
- Revisa los logs en Render Dashboard

### Error de CORS
- Asegúrate de que `CORS_ALLOWED_ORIGINS` incluya la URL exacta del frontend
- Verifica que `USE_HTTPS=True` en producción

### Error 404 en el frontend
- Verifica que `base: "/"` en `vite.config.js`
- Asegúrate de que `Publish Directory` sea `frontend/dist`

---

## 📝 Notas Finales

- Render hace **auto-deploy** cada vez que haces `git push`
- Los servicios gratuitos pueden tardar ~2 minutos en iniciar después de dormir
- Para producción seria, considera el plan **Starter** ($7/mes por servicio)

