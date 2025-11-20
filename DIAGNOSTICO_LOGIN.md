# Diagnóstico: Error "Usuario o contraseña incorrecta"

## 🔍 Pasos para Diagnosticar

### 1. Verificar que el Backend Esté Desplegado

Abre en tu navegador:
```
https://kanban-backend.onrender.com/api/user/
```

**Resultados posibles:**
- ✅ **Responde (aunque sea error 401)**: El backend está funcionando
- ❌ **No responde o timeout**: El backend NO está desplegado
- ❌ **Error 404**: El endpoint no existe o la URL es incorrecta

### 2. Verificar en la Consola del Navegador

1. Abre `https://heiner2001.github.io/ProyectoFinal/`
2. Abre la consola (F12)
3. Ve a la pestaña **Network**
4. Intenta hacer login
5. Busca la petición a `/api/login/`

**Verifica:**
- ¿A qué URL está intentando conectarse?
  - Debe ser: `https://kanban-backend.onrender.com/api/login/`
  - Si es otra URL, hay un problema de configuración
- ¿Qué código de estado tiene la respuesta?
  - **200**: El backend respondió correctamente
  - **401**: Credenciales incorrectas
  - **404**: Endpoint no encontrado
  - **500**: Error del servidor
  - **CORS error**: Problema de CORS
  - **Failed to fetch**: No se puede conectar al backend

### 3. Verificar las Credenciales

**Si el backend está en Render:**
- Los usuarios deben existir en la base de datos de Render
- Si acabas de desplegar, los usuarios del SQLite local NO están en Render
- Necesitas crear usuarios en la base de datos de Render

**Para crear usuarios en Render:**
1. Conecta a la base de datos de Render
2. O usa el admin de Django en Render
3. O crea un superusuario con `python manage.py createsuperuser` en Render

### 4. Verificar CORS

Si ves errores de CORS en la consola:
- El backend debe tener `https://heiner2001.github.io` en `CORS_ALLOWED_ORIGINS`
- Verifica las variables de entorno en Render

### 5. Verificar que el Backend Esté "Despierto"

Si el backend está en plan free de Render:
- Puede estar en "sleep"
- La primera petición puede tardar ~30 segundos
- Espera y vuelve a intentar

## 🔧 Soluciones

### Solución 1: Desplegar el Backend

Si el backend NO está desplegado:
1. Sigue la guía: `GUIA_DESPLIEGUE_RENDER_PASO_A_PASO.md`
2. O despliega manualmente en Render

### Solución 2: Crear Usuarios en Render

Si el backend está desplegado pero no tienes usuarios:
1. Ve a Render Dashboard
2. Abre el servicio `kanban-backend`
3. Ve a la pestaña **Shell**
4. Ejecuta: `python manage.py createsuperuser`
5. O conecta a la base de datos y crea usuarios manualmente

### Solución 3: Verificar Variables de Entorno

En Render, verifica que estas variables estén configuradas:
```
CORS_ALLOWED_ORIGINS=https://heiner2001.github.io,https://heiner2001.github.io/ProyectoFinal
CSRF_TRUSTED_ORIGINS=https://heiner2001.github.io,https://heiner2001.github.io/ProyectoFinal
USE_HTTPS=True
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_SECURE=True
```

## 📝 Información Necesaria

Para ayudarte mejor, necesito saber:

1. ¿El backend está desplegado en Render?
   - Verifica: `https://kanban-backend.onrender.com/api/user/`

2. ¿Qué aparece en la consola del navegador?
   - Abre F12 → Network → Intenta login → Ver petición

3. ¿Qué código de estado tiene la respuesta?
   - 200, 401, 404, 500, CORS error, etc.

4. ¿Las credenciales funcionan en local?
   - Si funcionan en local pero no en producción, el problema es el backend en Render

