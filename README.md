# Proyecto Final - Tablero Kanban en Django

Aplicación web de tablero Kanban desarrollada con Django que permite gestionar tareas organizadas en listas.

## Características

- Sistema de autenticación (login/logout)
- Tablero Kanban con columnas personalizables
- Añadir y gestionar tareas
- Diseño moderno con gradiente morado
- Interfaz intuitiva y responsive

## Instalación

1. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

2. Aplicar las migraciones:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. Crear un superusuario (opcional, para acceder al admin):
```bash
python manage.py createsuperuser
```

4. Ejecutar el servidor de desarrollo:

**IMPORTANTE**: Para que funcionen las notificaciones en tiempo real (WebSockets), el servidor debe ejecutarse con **Daphne** (ASGI), no con `runserver` (WSGI).

**Opción A - Usando el script (Recomendado):**
```bash
# Windows
run_server.bat

# Linux/Mac
chmod +x run_server.sh
./run_server.sh
```

**Opción B - Manualmente:**
```bash
# Instalar Daphne si no está instalado
pip install daphne

# Ejecutar con Daphne
daphne -b 0.0.0.0 -p 8000 proyectofinal.asgi:application
```

**Nota**: Si solo necesitas probar la aplicación sin notificaciones en tiempo real, puedes usar:
```bash
python manage.py runserver
```

5. Acceder a la aplicación en: http://127.0.0.1:8000/

## Uso

1. **Crear usuario**: Puedes crear un usuario desde el admin de Django o usar el siguiente comando:
```bash
python manage.py createsuperuser
```

2. **Iniciar sesión**: Ingresa con tu nombre de usuario y contraseña en la página de login.

3. **Usar el tablero**: 
   - Las listas predeterminadas se crean automáticamente: "Pendiente", "En Progreso", "Finalizado"
   - Haz clic en "Añade una tarjeta" para agregar nuevas tareas
   - Haz clic en "Añade otra lista" para crear nuevas columnas

## Estructura del Proyecto

```
ProyectoFinal/
├── manage.py
├── proyectofinal/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── kanban/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── templates/
│   │   └── kanban/
│   │       ├── base.html
│   │       ├── login.html
│   │       └── board.html
│   └── static/
│       └── kanban/
│           └── css/
│               └── style.css
└── requirements.txt
```

## Modelos

- **List**: Representa las columnas del tablero Kanban
- **Task**: Representa las tareas/tarjetas dentro de cada lista

