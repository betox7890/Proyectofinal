# Crear Superusuario Automáticamente

## 📋 Opciones Disponibles

Tienes dos formas de crear un superusuario automáticamente:

### Opción 1: Usar la Migración (Automático)

La migración `0013_create_initial_superuser.py` se ejecuta automáticamente durante `python manage.py migrate`.

**Configuración en Render:**

1. Ve a **kanban-backend** → **Environment**
2. Agrega estas variables de entorno:

```
SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@example.com
SUPERUSER_PASSWORD=tu_contraseña_segura_aqui
```

3. Guarda los cambios
4. La migración se ejecutará automáticamente en el próximo deployment

**Nota**: Si no configuras `SUPERUSER_PASSWORD`, se usará `admin123` por defecto (⚠️ **CAMBIA ESTO EN PRODUCCIÓN**).

### Opción 2: Usar el Comando de Management (Manual)

Puedes ejecutar el comando manualmente desde el Shell de Render:

1. Ve a **kanban-backend** → **Shell**
2. Ejecuta:

```bash
python manage.py create_superuser --username admin --email admin@example.com --password tu_contraseña_segura
```

O usando variables de entorno:

```bash
python manage.py create_superuser
```

El comando leerá las variables de entorno:
- `SUPERUSER_USERNAME` (default: `admin`)
- `SUPERUSER_EMAIL` (default: `admin@example.com`)
- `SUPERUSER_PASSWORD` (requerido o se genera automáticamente)

### Opción 3: Comando Interactivo (Tradicional)

También puedes usar el comando tradicional de Django:

```bash
python manage.py createsuperuser
```

## 🔧 Configuración en Render

### Paso 1: Agregar Variables de Entorno

1. Ve a **kanban-backend** → **Environment**
2. Haz clic en **Add Environment Variable**
3. Agrega estas variables:

```
SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@example.com
SUPERUSER_PASSWORD=tu_contraseña_segura_aqui
```

**⚠️ IMPORTANTE**: Usa una contraseña segura. No uses `admin123` en producción.

### Paso 2: Ejecutar Migraciones

Si usas la migración automática:

1. Las migraciones se ejecutan automáticamente durante el build
2. O puedes ejecutarlas manualmente desde Shell:
   ```bash
   python manage.py migrate
   ```

### Paso 3: Verificar que el Usuario Fue Creado

1. Ve a **Shell** de Render
2. Ejecuta:
   ```bash
   python manage.py shell
   ```
3. En el shell de Python:
   ```python
   from django.contrib.auth.models import User
   User.objects.filter(is_superuser=True)
   ```
4. Deberías ver el usuario creado

## 🧪 Probar el Login

1. Abre: `https://heiner2001.github.io/ProyectoFinal/`
2. Ingresa las credenciales:
   - **Usuario**: El valor de `SUPERUSER_USERNAME` (ej: `admin`)
   - **Contraseña**: El valor de `SUPERUSER_PASSWORD`
3. Deberías poder hacer login exitosamente

## 🔒 Seguridad

### Recomendaciones

1. **Usa contraseñas seguras**: Mínimo 12 caracteres, con mayúsculas, minúsculas, números y símbolos
2. **No uses valores por defecto**: Cambia `admin` y `admin123` en producción
3. **Rota las contraseñas**: Cambia la contraseña periódicamente
4. **Usa variables de entorno**: No hardcodees contraseñas en el código

### Cambiar Contraseña Después del Primer Login

1. Haz login con el superusuario
2. Ve al admin de Django: `https://kanban-backend-9wbt.onrender.com/admin/`
3. Ve a **Users** → Selecciona tu usuario → **Change password**
4. Ingresa una nueva contraseña segura

## 📝 Ejemplo de Variables de Entorno en Render

```
SUPERUSER_USERNAME=heiner
SUPERUSER_EMAIL=heiner@example.com
SUPERUSER_PASSWORD=MiContraseñaSegura123!
```

## ✅ Checklist

- [ ] Variables de entorno configuradas en Render
- [ ] Migraciones ejecutadas (automático o manual)
- [ ] Usuario verificado en la base de datos
- [ ] Login probado desde GitHub Pages
- [ ] Contraseña cambiada después del primer login (recomendado)

