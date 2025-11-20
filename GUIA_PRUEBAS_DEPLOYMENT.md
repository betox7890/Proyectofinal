# 🧪 Guía de Pruebas - Deployment Completo

## ✅ Pre-requisitos Verificados

- ✅ Backend desplegado en Render
- ✅ Base de datos PostgreSQL configurada
- ✅ Variables de entorno configuradas
- ✅ Frontend desplegado en GitHub Pages

## 📋 Checklist de Verificación

### 1. Verificar que el Backend Esté Funcionando

#### Paso 1.1: Verificar Estado del Servicio

1. Ve a Render Dashboard → **kanban-backend**
2. Verifica que el estado sea **Live** o **Running** (no "Sleep" o "Failed")
3. Si está en "Sleep", haz clic para "despertarlo" o espera ~30 segundos en la primera petición

#### Paso 1.2: Probar el Endpoint de Usuario

Abre en tu navegador:
```
https://kanban-backend-9wbt.onrender.com/api/user/
```

**Resultado esperado:**
- ✅ Debe responder con JSON (aunque sea error 401, significa que funciona)
- ❌ Si no responde o da timeout: El backend no está funcionando

#### Paso 1.3: Verificar los Logs

1. Ve a **Logs** del servicio **kanban-backend**
2. Verifica que no haya errores en rojo
3. Deberías ver mensajes como:
   - "Application is live"
   - "Starting server..."

### 2. Crear Usuarios en la Base de Datos

#### Paso 2.1: Acceder al Shell de Render

1. Ve al servicio **kanban-backend** en Render
2. Ve a la pestaña **Shell**
3. Haz clic en **Connect**

#### Paso 2.2: Crear Superusuario

En el shell, ejecuta:
```bash
python manage.py createsuperuser
```

Sigue las instrucciones:
- **Username**: (ingresa un nombre de usuario, ej: `admin` o `Heiner`)
- **Email address**: (ingresa un email, ej: `heiner@example.com`)
- **Password**: (ingresa una contraseña segura)
- **Password (again)**: (confirma la contraseña)

#### Paso 2.3: Crear Usuarios Adicionales (Opcional)

Puedes crear más usuarios desde el admin de Django:
1. Abre: `https://kanban-backend-9wbt.onrender.com/admin/`
2. Inicia sesión con el superusuario que creaste
3. Ve a **Users** → **Add user**
4. Crea los usuarios que necesites

### 3. Verificar el Frontend en GitHub Pages

#### Paso 3.1: Abrir el Frontend

Abre en tu navegador:
```
https://heiner2001.github.io/ProyectoFinal/
```

**Resultado esperado:**
- ✅ Debe cargar la página de login (no en blanco)
- ❌ Si aparece en blanco: Revisa la consola del navegador (F12)

#### Paso 3.2: Verificar la Consola del Navegador

1. Abre la consola (F12)
2. Ve a la pestaña **Console**
3. Verifica que no haya errores en rojo
4. Errores comunes:
   - **CORS error**: El backend no tiene configurado CORS correctamente
   - **Failed to fetch**: El backend no está accesible
   - **404**: La URL del backend es incorrecta

### 4. Probar el Login

#### Paso 4.1: Intentar Login

1. En la página de login, ingresa:
   - **Usuario**: El usuario que creaste en el Paso 2.2
   - **Contraseña**: La contraseña que configuraste
2. Haz clic en **Continuar** o **Iniciar sesión**

#### Paso 4.2: Verificar la Petición en Network

1. Abre la consola (F12)
2. Ve a la pestaña **Network**
3. Intenta hacer login
4. Busca la petición a `/api/login/`
5. Verifica:
   - **Status**: Debe ser 200 (éxito) o 400 (error de credenciales)
   - **Request URL**: Debe ser `https://kanban-backend-9wbt.onrender.com/api/login/`
   - **Response**: Debe tener un JSON con `success` o `error`

#### Paso 4.3: Si Requiere 2FA

Si el usuario tiene 2FA habilitado:
1. Ingresa el código de 6 dígitos de tu aplicación autenticadora
2. Haz clic en **Verificar**
3. Deberías ser redirigido al tablero

### 5. Probar Funcionalidades del Tablero

#### Paso 5.1: Verificar que el Tablero Cargue

Después de hacer login exitoso:
1. Deberías ver el tablero Kanban
2. Verifica que las listas se carguen correctamente
3. Verifica que no haya errores en la consola

#### Paso 5.2: Probar Crear una Tarea

1. Haz clic en **"Añade una tarjeta"** en alguna lista
2. Ingresa el título de la tarea
3. Haz clic en **Guardar**
4. Verifica que la tarea aparezca en la lista

#### Paso 5.3: Probar Drag and Drop

1. Arrastra una tarea de una lista a otra
2. Verifica que la tarea se mueva correctamente
3. Verifica que no aparezca "Cargando tablero..." y recargue la página

### 6. Verificar CORS y Cookies

#### Paso 6.1: Verificar Cookies en el Navegador

1. Abre la consola (F12)
2. Ve a la pestaña **Application** (Chrome) o **Storage** (Firefox)
3. Ve a **Cookies** → `https://heiner2001.github.io`
4. Verifica que haya cookies:
   - `sessionid` (cookie de sesión de Django)
   - `csrftoken` (token CSRF)

#### Paso 6.2: Verificar CORS

1. Abre la consola (F12)
2. Ve a la pestaña **Network**
3. Intenta hacer login
4. Busca la petición a `/api/login/`
5. Ve a **Headers** → **Response Headers**
6. Verifica que haya:
   - `Access-Control-Allow-Origin: https://heiner2001.github.io`
   - `Access-Control-Allow-Credentials: true`

## 🔧 Solución de Problemas Comunes

### Problema: "Error de conexión" en el login

**Causa**: El backend no está accesible o hay problemas de CORS

**Solución**:
1. Verifica que el backend esté en estado "Live" en Render
2. Verifica que `CORS_ALLOWED_ORIGINS` incluya `https://heiner2001.github.io`
3. Verifica en la consola del navegador qué error aparece

### Problema: "Usuario o contraseña incorrecta"

**Causa**: Las credenciales son incorrectas o el usuario no existe en Render

**Solución**:
1. Verifica que hayas creado el usuario en Render (Paso 2.2)
2. Verifica que las credenciales sean correctas
3. Si el usuario existe en local pero no en Render, créalo en Render

### Problema: El backend está en "Sleep"

**Causa**: Plan free de Render pone servicios en sleep después de 15 min de inactividad

**Solución**:
- Es normal en el plan free
- La primera petición puede tardar ~30 segundos
- Considera hacer una petición cada 10-15 minutos para mantenerlo activo

### Problema: CORS Error

**Causa**: El backend no tiene configurado CORS correctamente

**Solución**:
1. Ve a **kanban-backend** → **Environment**
2. Verifica que `CORS_ALLOWED_ORIGINS` incluya:
   - `https://heiner2001.github.io`
   - `https://heiner2001.github.io/ProyectoFinal`
3. Guarda los cambios y espera a que Render reinicie

## ✅ Checklist Final

- [ ] Backend responde en `/api/user/`
- [ ] Usuarios creados en Render
- [ ] Frontend carga correctamente en GitHub Pages
- [ ] Login funciona correctamente
- [ ] Tablero carga después del login
- [ ] Se pueden crear tareas
- [ ] Drag and drop funciona
- [ ] Cookies se establecen correctamente
- [ ] No hay errores de CORS

## 🎉 ¡Listo!

Si todos los pasos anteriores funcionan correctamente, tu aplicación está completamente desplegada y funcionando.

