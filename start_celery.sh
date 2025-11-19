#!/bin/bash

echo "========================================"
echo "Iniciando Celery Worker y Celery Beat"
echo "Esto es necesario para las tareas programadas"
echo "========================================"
echo ""

# Verificar si Redis está ejecutándose
echo "Verificando conexión con Redis..."
if ! python -c "import redis; r = redis.Redis(host='127.0.0.1', port=6379, db=0); r.ping(); print('Redis conectado correctamente')" 2>/dev/null; then
    echo "ERROR: Redis no está ejecutándose o no está disponible."
    echo "Por favor, inicia Redis antes de continuar."
    echo ""
    echo "En Linux/Mac, puedes iniciar Redis con:"
    echo "  sudo systemctl start redis"
    echo "  o"
    echo "  redis-server"
    echo ""
    exit 1
fi

echo ""
echo "Redis está disponible."
echo ""
echo "Iniciando Celery Worker y Celery Beat..."
echo "Presiona Ctrl+C para detener ambos procesos"
echo ""

# Iniciar Celery Worker en background
celery -A proyectofinal worker --loglevel=info &
CELERY_WORKER_PID=$!

# Esperar un momento antes de iniciar Beat
sleep 3

# Iniciar Celery Beat en background
celery -A proyectofinal beat --loglevel=info &
CELERY_BEAT_PID=$!

echo ""
echo "Celery Worker (PID: $CELERY_WORKER_PID) y Celery Beat (PID: $CELERY_BEAT_PID) iniciados."
echo ""
echo "Para detener, ejecuta:"
echo "  kill $CELERY_WORKER_PID $CELERY_BEAT_PID"
echo ""

# Esperar a que se presione Ctrl+C
trap "kill $CELERY_WORKER_PID $CELERY_BEAT_PID; exit" INT TERM
wait

