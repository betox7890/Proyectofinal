#!/bin/bash

echo "========================================"
echo "Iniciando Frontend React"
echo "========================================"
echo ""

cd frontend

if [ ! -d "node_modules" ]; then
    echo "Instalando dependencias..."
    npm install
fi

echo ""
echo "Iniciando servidor de desarrollo en http://localhost:5173"
echo ""

npm run dev

