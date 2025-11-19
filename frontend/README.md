# Frontend React - Tablero Kanban

Frontend del proyecto Kanban desarrollado con React y Vite.

## Instalación

```bash
npm install
```

## Desarrollo

```bash
npm run dev
```

El servidor de desarrollo se iniciará en `http://localhost:5173`

## Construcción para Producción

```bash
npm run build
```

Los archivos se generarán en la carpeta `dist/`

## Configuración

Crea un archivo `.env` basado en `.env.example` para configurar la URL de la API:

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Estructura del Proyecto

```
frontend/
├── src/
│   ├── pages/          # Páginas principales
│   │   ├── Login.jsx
│   │   ├── Board.jsx
│   │   └── Calendar.jsx
│   ├── services/       # Servicios API
│   │   └── api.js
│   ├── config/         # Configuración
│   │   └── api.js
│   ├── App.jsx         # Componente principal
│   └── main.jsx        # Punto de entrada
├── public/             # Archivos estáticos
└── package.json
```

## Notas Importantes

⚠️ **Este frontend requiere que Django tenga endpoints API JSON configurados.**

Actualmente, Django solo tiene endpoints que devuelven HTML. Para que el frontend React funcione completamente, necesitas:

1. Crear endpoints API JSON en Django (usando Django REST Framework o vistas JSON simples)
2. O modificar las vistas existentes para que acepten `Accept: application/json` y devuelvan JSON

## Próximos Pasos

1. Instalar Django REST Framework o crear vistas JSON
2. Implementar autenticación con tokens o mantener sesiones
3. Completar los componentes del tablero Kanban
4. Implementar WebSockets para notificaciones en tiempo real
