#!/bin/bash

echo "========================================"
echo "Configuración de GitHub para el Proyecto"
echo "========================================"
echo ""

# Verificar si git está instalado
if ! command -v git &> /dev/null; then
    echo "ERROR: Git no está instalado. Por favor instala Git primero."
    echo "En Ubuntu/Debian: sudo apt-get install git"
    echo "En macOS: xcode-select --install"
    exit 1
fi

echo "Git está instalado."
echo ""

# Verificar si ya es un repositorio git
if [ -d .git ]; then
    echo "Ya es un repositorio Git."
    echo ""
else
    # Inicializar repositorio git
    echo "Inicializando repositorio Git..."
    git init
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudo inicializar el repositorio Git."
        exit 1
    fi
    echo "Repositorio Git inicializado."
    echo ""
fi

# Verificar si ya tiene un remote
if git remote -v | grep -q "origin"; then
    echo "Repositorio remoto ya configurado."
    echo ""
else
    echo "No se ha configurado un repositorio remoto."
    echo ""
    echo "Por favor:"
    echo "1. Crea un repositorio en GitHub (ve a https://github.com/new)"
    echo "2. No inicialices el repositorio con README, .gitignore o licencia"
    echo "3. Copia la URL del repositorio (ejemplo: https://github.com/usuario/repositorio.git)"
    echo ""
    read -p "Ingresa la URL de tu repositorio de GitHub: " REPO_URL
    
    if [ -z "$REPO_URL" ]; then
        echo "ERROR: URL no proporcionada."
        exit 1
    fi
    
    echo ""
    echo "Agregando repositorio remoto..."
    git remote add origin "$REPO_URL"
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudo agregar el repositorio remoto."
        exit 1
    fi
    
    echo "Repositorio remoto agregado."
    echo ""
fi

# Agregar archivos
echo "Agregando archivos al repositorio..."
git add .
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudieron agregar los archivos."
    exit 1
fi

echo "Archivos agregados."
echo ""

# Hacer commit
echo "Creando commit inicial..."
git commit -m "Initial commit: Proyecto Kanban con Django y React"
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudo crear el commit."
    echo "Esto puede suceder si no has configurado tu nombre y email en Git."
    echo ""
    echo "Configura tu nombre y email con:"
    echo "  git config --global user.name 'Tu Nombre'"
    echo "  git config --global user.email 'tu.email@example.com'"
    exit 1
fi

echo "Commit creado."
echo ""

# Cambiar a rama main
echo "Cambiando a rama main..."
git branch -M main
echo ""

# Hacer push
echo "Subiendo archivos a GitHub..."
echo "Esto puede pedirte tus credenciales de GitHub."
echo ""
git push -u origin main
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: No se pudo subir los archivos."
    echo ""
    echo "Posibles causas:"
    echo "- Credenciales incorrectas"
    echo "- El repositorio remoto no existe"
    echo "- Problemas de conexión"
    echo ""
    echo "Puedes intentar manualmente con:"
    echo "  git push -u origin main"
    exit 1
fi

echo ""
echo "========================================"
echo "¡Proyecto subido exitosamente a GitHub!"
echo "========================================"
echo ""
echo "Siguiente paso: Sigue las instrucciones en DEPLOY.md"
echo "para desplegar el backend en Render y el frontend en Vercel."
echo ""

