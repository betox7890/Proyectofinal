# Configuración del Frontend React

Este proyecto ahora incluye un frontend React separado que se comunica con el backend Django a través de una API.

## Estructura del Proyecto

```
ProyectoFinal/
├── frontend/              # Proyecto React (Vite)
│   ├── src/
│   │   ├── pages/        # Páginas principales
│   │   ├── services/     # Servicios API
│   │   └── config/       # Configuración
│   └── package.json
├── kanban/               # Backend Django
└── proyectofinal/        # Configuración Django
```

## Instalación

### 1. Instalar dependencias de Python (si no lo has hecho)

```bash
pip install -r requirements.txt
```

Esto instalará `django-cors-headers` que es necesario para permitir peticiones desde React.

### 2. Instalar dependencias de React

```bash
cd frontend
npm install
```

### 3. Configurar variables de entorno (opcional)

Crea un archivo `.env` en la carpeta `frontend/`:

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Ejecución

### Opción 1: Scripts automáticos

**Windows:**
```bash
start_frontend.bat
```

**Linux/Mac:**
```bash
chmod +x start_frontend.sh
./start_frontend.sh
```

### Opción 2: Manual

**Terminal 1 - Backend Django:**
```bash
# Windows
run_server.bat

# Linux/Mac
./run_server.sh
```

**Terminal 2 - Frontend React:**
```bash
cd frontend
npm run dev
```

## Acceso

- **Frontend React:** http://localhost:5173
- **Backend Django:** http://127.0.0.1:8000

## Estado Actual

✅ **Completado:**
- Proyecto React creado con Vite
- Configuración CORS en Django
- Estructura básica de componentes
- Servicios API configurados
- Página de Login
- Páginas básicas de Board y Calendar
- Routing configurado

⚠️ **Pendiente:**
- Crear endpoints API JSON en Django (actualmente solo hay HTML)
- Implementar componentes completos del tablero Kanban
- Integrar WebSockets para notificaciones en tiempo real
- Completar funcionalidad de autenticación

## Próximos Pasos

### 1. Crear Endpoints API JSON en Django

Actualmente, Django solo devuelve HTML. Necesitas crear endpoints que devuelvan JSON. Opciones:

**Opción A: Django REST Framework (Recomendado)**
```bash
pip install djangorestframework
```

**Opción B: Vistas JSON simples**
Modificar las vistas existentes para que acepten `Accept: application/json` y devuelvan JSON.

### 2. Implementar Componentes del Tablero

- Componente de Lista
- Componente de Tarea
- Componente de Subtarea
- Drag and Drop
- Modales para crear/editar

### 3. WebSockets en React

Para las notificaciones en tiempo real, necesitarás:
- Instalar `@stomp/stompjs` o similar
- Conectar al WebSocket de Django Channels
- Manejar eventos en tiempo real

## Configuración CORS

CORS ya está configurado en `settings.py` para permitir peticiones desde:
- http://localhost:3000
- http://localhost:5173
- http://127.0.0.1:3000
- http://127.0.0.1:5173

Si necesitas agregar más orígenes, edita `CORS_ALLOWED_ORIGINS` en `settings.py`.

## Desarrollo

### Hot Module Replacement (HMR)

Vite incluye HMR por defecto. Los cambios en los archivos React se reflejarán automáticamente en el navegador.

### Debugging

- Usa las DevTools del navegador para ver las peticiones de red
- Revisa la consola del navegador para errores de JavaScript
- Revisa los logs de Django para errores del backend

## Construcción para Producción

```bash
cd frontend
npm run build
```

Los archivos estáticos se generarán en `frontend/dist/`. Puedes servir estos archivos con Django o cualquier servidor web estático.

## Notas Importantes

1. **Autenticación:** Actualmente usa sesiones de Django. Para producción, considera usar tokens JWT.

2. **CSRF Token:** El frontend obtiene automáticamente el CSRF token de las cookies y lo incluye en las peticiones.

3. **CORS:** Asegúrate de que CORS esté configurado correctamente en producción.

4. **WebSockets:** Para notificaciones en tiempo real, necesitarás configurar la conexión WebSocket desde React.

