# Verificar URL del Backend en Render

## ⚠️ Importante

La URL del backend en Render puede ser diferente a `kanban-backend.onrender.com`.

## 🔍 Cómo Verificar la URL Correcta

### Paso 1: Obtener la URL del Backend en Render

1. Ve a Render Dashboard
2. Haz clic en el servicio **kanban-backend**
3. En la parte superior, verás la URL del servicio
4. Debe ser algo como: `https://kanban-backend-9wbt.onrender.com`
5. **Copia esta URL completa**

### Paso 2: Verificar que el Backend Responda

Abre en tu navegador la URL que copiaste:
```
https://kanban-backend-9wbt.onrender.com/api/user/
```

**Resultado esperado:**
- ✅ Debe responder con JSON (aunque sea error 401)
- ❌ Si no responde: El backend no está funcionando o la URL es incorrecta

### Paso 3: Actualizar el Frontend (Si la URL es Diferente)

Si la URL del backend es diferente a `kanban-backend-9wbt.onrender.com`, necesitas actualizarla en:

1. **frontend/src/pages/Login.jsx** (líneas ~229 y ~60)
2. **frontend/src/App.jsx** (línea ~36)
3. **frontend/src/config/api.js** (línea ~4)

Busca todas las ocurrencias de:
```javascript
'https://kanban-backend-9wbt.onrender.com'
```

Y reemplázalas con la URL correcta de tu backend.

### Paso 4: Verificar CORS en Render

1. Ve a **kanban-backend** → **Environment**
2. Verifica que `CORS_ALLOWED_ORIGINS` incluya:
   - `https://heiner2001.github.io`
   - `https://heiner2001.github.io/ProyectoFinal`
3. Si falta, agrégalo y guarda

### Paso 5: Verificar que el Usuario Exista en Render

**IMPORTANTE**: Los usuarios del SQLite local NO están en Render.

1. Ve a **kanban-backend** → **Shell**
2. Ejecuta: `python manage.py createsuperuser`
3. Crea el usuario con las mismas credenciales que usas en local
4. O verifica que el usuario exista en la base de datos de Render

## 🔧 Solución Rápida

Si el error persiste después de corregir la URL:

1. **Abre la consola del navegador** (F12) en GitHub Pages
2. Ve a la pestaña **Network**
3. Intenta hacer login
4. Busca la petición a `/api/login/`
5. Verifica:
   - **Request URL**: ¿A qué URL está intentando conectarse?
   - **Status**: ¿Qué código de estado tiene? (200, 401, 404, CORS error)
   - **Response**: ¿Qué respuesta devuelve el servidor?

## ✅ Checklist

- [ ] URL del backend verificada en Render
- [ ] Backend responde en `/api/user/`
- [ ] URL actualizada en todos los archivos del frontend
- [ ] CORS configurado correctamente
- [ ] Usuario creado en Render
- [ ] Frontend actualizado en GitHub Pages (espera 2-5 minutos después del push)

