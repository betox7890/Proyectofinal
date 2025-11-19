# 🚀 Guía Rápida de Despliegue - Links de Backend y Frontend

## ⚡ Pasos Rápidos para Obtener los Links

### 📦 Paso 1: Subir a GitHub (5 minutos)

1. **Crear repositorio en GitHub:**
   - Ve a: https://github.com/new
   - Nombre del repositorio: `proyecto-kanban` (o el que prefieras)
   - ⚠️ **NO marques** "Add a README file", "Add .gitignore", ni "Choose a license"
   - Click en "Create repository"

2. **Copiar la URL del repositorio** (ejemplo: `https://github.com/TU_USUARIO/proyecto-kanban.git`)

3. **En tu terminal, ejecuta:**
```bash
cd "C:\Users\Usuario\Desktop\Progra4\ProyectoFinal"
git remote add origin https://github.com/TU_USUARIO/proyecto-kanban.git
git push -u origin main
```

---

### 🔙 Paso 2: Desplegar Backend en Render (10 minutos)

1. **Ir a Render:**
   - Ve a: https://dashboard.render.com
   - Crea una cuenta si no tienes (es gratis)
   - Click en "New +" → "Web Service"

2. **Conectar GitHub:**
   - Selecciona tu repositorio `proyecto-kanban`
   - Click en "Connect"

3. **Configurar el servicio:**
   - **Name**: `kanban-backend`
   - **Region**: `Oregon (US West)`
   - **Branch**: `main`
   - **Root Directory**: `.` (dejar vacío o poner `.`)
   - **Runtime**: `Python 3`
   - **Build Command**: 
     ```
     pip install -r requirements.txt && python manage.py collectstatic --noinput
     ```
   - **Start Command**: 
     ```
     daphne -b 0.0.0.0 -p $PORT proyectofinal.asgi:application
     ```
   - **Plan**: `Free`

4. **Variables de Entorno (IMPORTANTE):**
   Click en "Advanced" → "Add Environment Variable" y agrega:

   - `SECRET_KEY`: Genera una clave ejecutando esto en tu terminal:
     ```bash
     python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
     ```
   - `DEBUG`: `False`
   - `USE_HTTPS`: `True`
   - `ALLOWED_HOSTS`: `kanban-backend.onrender.com` (se actualizará después)

5. **Click en "Create Web Service"**

6. **Esperar el despliegue** (5-10 minutos)

7. **Copiar la URL del backend:**
   - Cuando termine el despliegue, verás una URL como: `https://kanban-backend.onrender.com`
   - ⚠️ **COPIA ESTA URL** - La necesitarás para el frontend

---

### 🎨 Paso 3: Desplegar Frontend en Vercel (10 minutos)

1. **Ir a Vercel:**
   - Ve a: https://vercel.com/dashboard
   - Crea una cuenta si no tienes (usa GitHub para más fácil)
   - Click en "Add New..." → "Project"

2. **Importar repositorio:**
   - Busca y selecciona tu repositorio `proyecto-kanban`
   - Click en "Import"

3. **Configurar el proyecto:**
   - **Framework Preset**: `Vite` (o se detecta automáticamente)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (debe estar automático)
   - **Output Directory**: `dist` (debe estar automático)
   - **Install Command**: `npm install` (debe estar automático)

4. **Variables de Entorno:**
   - Click en "Environment Variables"
   - Agrega:
     - **Key**: `VITE_API_BASE_URL`
     - **Value**: La URL de tu backend de Render (ejemplo: `https://kanban-backend.onrender.com`)

5. **Click en "Deploy"**

6. **Esperar el despliegue** (2-5 minutos)

7. **Copiar la URL del frontend:**
   - Cuando termine, verás una URL como: `https://proyecto-kanban.vercel.app`
   - ⚠️ **COPIA ESTA URL**

---

### 🔄 Paso 4: Actualizar Backend con URL del Frontend (5 minutos)

1. **Volver a Render:**
   - Ve a tu servicio `kanban-backend` en Render
   - Click en "Environment"
   - Edita las siguientes variables:

2. **Actualizar Variables de Entorno:**
   - `CORS_ALLOWED_ORIGINS`: `https://tu-frontend.vercel.app` (la URL que obtuviste en el Paso 3)
   - `CSRF_TRUSTED_ORIGINS`: `https://tu-frontend.vercel.app`
   - `ALLOWED_HOSTS`: `kanban-backend.onrender.com,tu-frontend.vercel.app`

3. **Click en "Save Changes"**
   - Esto reiniciará automáticamente el servicio

4. **Esperar que el servicio se reinicie** (2-3 minutos)

---

### ✅ Paso 5: ¡Listo! Tienes tus Links

- **🔙 Backend**: `https://kanban-backend.onrender.com`
- **🎨 Frontend**: `https://tu-frontend.vercel.app`

---

## 🆘 Problemas Comunes

### Error: "git: 'remote' no es un comando"
- Asegúrate de tener Git instalado: https://git-scm.com/download/win

### Error en Render: "ModuleNotFoundError"
- Verifica que `requirements.txt` tenga todas las dependencias
- Asegúrate de que el Build Command esté correcto

### Error de CORS en el frontend
- Verifica que `CORS_ALLOWED_ORIGINS` en Render tenga exactamente la URL de Vercel (con https://)
- No olvides reiniciar el servicio después de actualizar las variables

### El backend no responde
- Verifica los logs en Render para ver qué está fallando
- Asegúrate de que el Start Command esté correcto
- Verifica que el puerto sea `$PORT` (Render lo asigna automáticamente)

---

## 📝 Notas Importantes

- ⏰ El backend en Render puede tardar 1-2 minutos en responder después de estar inactivo (plan gratuito)
- 🔒 Las cookies funcionan correctamente con HTTPS en producción
- 💾 El proyecto usa SQLite por defecto (para producción, considera PostgreSQL)

