# 🚀 Guía Paso a Paso: Desplegar en Render

## 📋 Paso 1: Crear Cuenta en Render

1. Ve a **https://render.com**
2. Click en **"Get Started for Free"** o **"Sign Up"**
3. Elige **"Sign up with GitHub"** (recomendado)
4. Autoriza a Render a acceder a tus repositorios

---

## 📋 Paso 2: Desplegar con Blueprint (Automático)

### Opción A: Usando el archivo `render.yaml` (Recomendado)

1. En Render Dashboard, click en **"New +"** (arriba a la derecha)
2. Selecciona **"Blueprint"**
3. Render te pedirá conectar un repositorio:
   - Si no está conectado, click en **"Connect account"** o **"Configure GitHub"**
   - Busca y selecciona: **`betox7890/Proyectofinal`**
4. Render detectará automáticamente el archivo `render.yaml`
5. Verás una vista previa de los servicios que se crearán:
   - ✅ **proyectofinal-db** (PostgreSQL)
   - ✅ **proyectofinal-backend** (Web Service - Django)
   - ✅ **proyectofinal-frontend** (Static Site - React)
6. Click en **"Apply"** (abajo a la derecha)
7. ⏳ Espera 5-10 minutos mientras Render:
   - Crea la base de datos
   - Instala dependencias del backend
   - Ejecuta migraciones
   - Construye el frontend
   - Despliega todo

---

## 📋 Paso 3: Verificar el Despliegue

### Backend
1. Ve a **Dashboard** → **proyectofinal-backend**
2. Espera a que el estado sea **"Live"** (verde)
3. Anota la URL: `https://proyectofinal-backend.onrender.com`

### Frontend
1. Ve a **Dashboard** → **proyectofinal-frontend**
2. Espera a que el estado sea **"Live"** (verde)
3. Anota la URL: `https://proyectofinal-frontend.onrender.com`

### Base de Datos
1. Ve a **Dashboard** → **proyectofinal-db**
2. Verifica que esté **"Available"**

---

## 📋 Paso 4: Configurar Variables de Entorno

### Backend - Variables de Entorno

1. Ve a **proyectofinal-backend** → **Environment**
2. Verifica/Actualiza estas variables:

```bash
# Ya configuradas automáticamente por render.yaml:
PYTHON_VERSION=3.11.0
SECRET_KEY=<generado automáticamente>
DEBUG=False
ALLOWED_HOSTS=proyectofinal-backend.onrender.com
DATABASE_URL=<configurado automáticamente desde la BD>
CORS_ALLOWED_ORIGINS=https://proyectofinal-frontend.onrender.com
CSRF_TRUSTED_ORIGINS=https://proyectofinal-frontend.onrender.com,https://proyectofinal-backend.onrender.com
USE_HTTPS=True
```

**⚠️ IMPORTANTE:** Si el frontend tiene una URL diferente, actualiza:
- `CORS_ALLOWED_ORIGINS` con la URL real del frontend
- `CSRF_TRUSTED_ORIGINS` con ambas URLs (frontend y backend)

### Frontend - Variables de Entorno

1. Ve a **proyectofinal-frontend** → **Environment**
2. Verifica esta variable:

```bash
VITE_API_BASE_URL=https://proyectofinal-backend.onrender.com
```

**⚠️ IMPORTANTE:** Si el backend tiene una URL diferente, actualiza `VITE_API_BASE_URL` con la URL real del backend.

---

## 📋 Paso 5: Crear Superusuario

1. Ve a **proyectofinal-backend** → **Shell** (en el menú lateral)
2. Se abrirá una terminal
3. Ejecuta:
   ```bash
   python manage.py createsuperuser
   ```
4. Sigue las instrucciones:
   ```
   Username: admin
   Email address: admin@example.com (o déjalo vacío)
   Password: admin123
   Password (again): admin123
   ```
5. Presiona Enter

---

## 📋 Paso 6: Verificar que Todo Funciona

### 1. Probar el Backend
Abre en tu navegador:
```
https://proyectofinal-backend.onrender.com/admin/
```
- Deberías ver la página de login de Django Admin

### 2. Probar el Frontend
Abre en tu navegador:
```
https://proyectofinal-frontend.onrender.com
```
- Deberías ver tu aplicación React
- Intenta hacer login con:
  - Username: `admin`
  - Password: `admin123`

---

## 🔧 Solución de Problemas

### El backend no inicia
1. Ve a **proyectofinal-backend** → **Logs**
2. Revisa los errores
3. Verifica que `DATABASE_URL` esté configurada
4. Verifica que `SECRET_KEY` esté configurada

### Error de CORS
1. Verifica que `CORS_ALLOWED_ORIGINS` tenga la URL exacta del frontend
2. Asegúrate de que ambas URLs usen HTTPS
3. Verifica que `USE_HTTPS=True`

### El frontend muestra error de conexión
1. Verifica que `VITE_API_BASE_URL` apunte a la URL correcta del backend
2. Reconstruye el frontend: **proyectofinal-frontend** → **Manual Deploy** → **Clear build cache & deploy**

### Error 404 en el frontend
1. Verifica que `staticPublishPath` sea `frontend/dist`
2. Verifica que el build se haya completado correctamente

### El servicio está "Sleeping"
- Esto es normal en el plan gratuito
- La primera petición después de dormir puede tardar ~30 segundos
- Es gratis, así que es esperado

---

## ✅ URLs Finales

Después del despliegue tendrás:
- **Frontend**: `https://proyectofinal-frontend.onrender.com`
- **Backend**: `https://proyectofinal-backend.onrender.com`
- **Admin Django**: `https://proyectofinal-backend.onrender.com/admin/`

---

## 🔄 Actualizaciones Futuras

Cada vez que hagas `git push` a tu repositorio:
1. Render detectará automáticamente los cambios
2. Reconstruirá y redesplegará los servicios
3. Esto puede tardar 3-5 minutos

Para forzar un redeploy manual:
1. Ve al servicio en Render Dashboard
2. Click en **"Manual Deploy"** → **"Deploy latest commit"**

---

## 📝 Notas Importantes

1. **Plan Gratuito:**
   - Los servicios se "duermen" después de 15 minutos de inactividad
   - La primera petición después de dormir puede tardar ~30 segundos
   - 750 horas gratis por mes (suficiente para desarrollo)

2. **Base de Datos:**
   - PostgreSQL gratuito por 90 días
   - Si no hay actividad, se elimina automáticamente
   - Para producción seria, considera el plan Starter ($7/mes)

3. **SSL/HTTPS:**
   - Render proporciona SSL automáticamente
   - Todas las URLs usan HTTPS

---

## 🎉 ¡Listo!

Tu proyecto está desplegado y funcionando. Puedes compartir las URLs con tu profesor o compañeros.

