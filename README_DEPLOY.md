# 🚀 Guía de Despliegue Completa

Este proyecto puede desplegarse en múltiples plataformas. Elige la que prefieras:

---

## 📍 Opción 1: Render.com (Recomendado - Gratis)

**Ventajas:**
- ✅ Frontend y Backend en la misma plataforma
- ✅ PostgreSQL gratuito incluido
- ✅ SSL/HTTPS automático
- ✅ Despliegue automático desde GitHub

**Ver guía completa:** [DEPLOY_RENDER.md](./DEPLOY_RENDER.md)

**Pasos rápidos:**
1. Crea cuenta en [Render.com](https://render.com)
2. Conecta tu repositorio: `betox7890/Proyectofinal`
3. Render detectará automáticamente `render.yaml`
4. Click en **"Apply"** y espera ~5 minutos
5. Configura variables de entorno (ver DEPLOY_RENDER.md)
6. Crea superusuario: `python manage.py createsuperuser`

**URLs resultantes:**
- Frontend: `https://proyectofinal-frontend.onrender.com`
- Backend: `https://proyectofinal-backend.onrender.com`

---

## 📍 Opción 2: Vercel (Frontend) + Railway (Backend)

**Ventajas:**
- ✅ Vercel es muy rápido para frontend
- ✅ Railway ya lo tienes configurado

**Pasos:**

### Frontend en Vercel:
1. Ve a [Vercel.com](https://vercel.com)
2. Conecta tu repositorio
3. Configuración:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Environment Variables**:
     ```
     VITE_API_BASE_URL=https://proyectofinal-production-bfac.up.railway.app
     ```

### Backend en Railway:
Ya lo tienes configurado ✅

**URLs resultantes:**
- Frontend: `https://tu-proyecto.vercel.app`
- Backend: `https://proyectofinal-production-bfac.up.railway.app`

---

## 📍 Opción 3: Netlify (Frontend) + Railway (Backend)

**Ventajas:**
- ✅ Netlify es fácil de usar
- ✅ Railway ya lo tienes configurado

**Pasos:**

### Frontend en Netlify:
1. Ve a [Netlify.com](https://netlify.com)
2. Conecta tu repositorio
3. Configuración:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`
   - **Environment Variables**:
     ```
     VITE_API_BASE_URL=https://proyectofinal-production-bfac.up.railway.app
     ```

### Backend en Railway:
Ya lo tienes configurado ✅

**URLs resultantes:**
- Frontend: `https://tu-proyecto.netlify.app`
- Backend: `https://proyectofinal-production-bfac.up.railway.app`

---

## 📍 Opción 4: Railway (Ambos)

**Ventajas:**
- ✅ Ya conoces Railway
- ✅ Todo en un solo lugar

**Pasos:**

### Backend en Railway:
Ya lo tienes configurado ✅

### Frontend en Railway:
1. En Railway Dashboard → **"New"** → **"Static Site"**
2. Conecta tu repositorio
3. Configuración:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Output Directory**: `dist`
   - **Environment Variables**:
     ```
     VITE_API_BASE_URL=https://proyectofinal-production-bfac.up.railway.app
     ```

**URLs resultantes:**
- Frontend: `https://tu-frontend.up.railway.app`
- Backend: `https://proyectofinal-production-bfac.up.railway.app`

---

## 🔧 Configuración de Variables de Entorno

### Backend (Django):
```bash
SECRET_KEY=<genera uno nuevo>
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com
DATABASE_URL=<URL de PostgreSQL>
CORS_ALLOWED_ORIGINS=https://tu-frontend.com
CSRF_TRUSTED_ORIGINS=https://tu-frontend.com,https://tu-backend.com
USE_HTTPS=True
```

### Frontend (React):
```bash
VITE_API_BASE_URL=https://tu-backend.com
```

---

## 📝 Notas Importantes

1. **CORS**: Asegúrate de que `CORS_ALLOWED_ORIGINS` incluya la URL exacta de tu frontend
2. **CSRF**: `CSRF_TRUSTED_ORIGINS` debe incluir ambas URLs (frontend y backend)
3. **HTTPS**: En producción siempre usa `USE_HTTPS=True`
4. **Base Path**: 
   - GitHub Pages: `/Proyectofinal/`
   - Render/Vercel/Netlify: `/`
5. **Superusuario**: Crea uno después del despliegue con `python manage.py createsuperuser`

---

## 🆘 Solución de Problemas

### Error de CORS
- Verifica que `CORS_ALLOWED_ORIGINS` tenga la URL exacta del frontend
- Asegúrate de que ambas URLs usen HTTPS

### Error 404 en el frontend
- GitHub Pages: Usa `base: "/Proyectofinal/"`
- Render/Vercel/Netlify: Usa `base: "/"`

### El backend no inicia
- Verifica que `DATABASE_URL` esté correctamente configurada
- Revisa los logs en la plataforma

---

## ✅ Recomendación Final

**Para desarrollo/universidad:** Render.com (Opción 1)
- Todo en un solo lugar
- PostgreSQL incluido
- Muy fácil de configurar

**Para producción seria:** Vercel (Frontend) + Railway (Backend)
- Mejor rendimiento
- Más confiable
- Mejor para escalar

