#!/bin/bash

echo "========================================"
echo "Iniciando servidor Django con Daphne (ASGI)"
echo "Esto es necesario para que funcionen los WebSockets"
echo "========================================"
echo ""

# Verificar si Daphne está instalado
if ! python -c "import daphne" 2>/dev/null; then
    echo "ERROR: Daphne no está instalado."
    echo "Instalando Daphne..."
    pip install daphne
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudo instalar Daphne."
        exit 1
    fi
fi

echo ""
echo "Iniciando servidor en http://127.0.0.1:8000"
echo "Presiona Ctrl+C para detener el servidor"
echo ""

daphne -b 0.0.0.0 -p 8000 proyectofinal.asgi:application

