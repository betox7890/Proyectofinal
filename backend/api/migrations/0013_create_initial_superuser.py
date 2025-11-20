"""
Migración personalizada para crear un superusuario inicial.
Esta migración crea un superusuario si no existe.
"""
from django.db import migrations
from django.contrib.auth.models import User
import os


def create_initial_superuser(apps, schema_editor):
    """Crear superusuario inicial si no existe"""
    # Obtener credenciales de variables de entorno
    username = os.getenv('SUPERUSER_USERNAME', 'admin')
    email = os.getenv('SUPERUSER_EMAIL', 'admin@example.com')
    password = os.getenv('SUPERUSER_PASSWORD', None)
    
    # Si no hay contraseña en variables de entorno, usar una por defecto
    # IMPORTANTE: Cambia esto en producción
    if not password:
        password = os.getenv('SUPERUSER_PASSWORD_DEFAULT', 'admin123')
    
    # Verificar si el usuario ya existe
    if User.objects.filter(username=username).exists():
        print(f'El usuario "{username}" ya existe. Saltando creación.')
        return
    
    # Crear el superusuario
    try:
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f'Superusuario "{username}" creado exitosamente.')
        print(f'Email: {email}')
        print(f'⚠️  IMPORTANTE: Cambia la contraseña después del primer login.')
    except Exception as e:
        print(f'Error al crear superusuario: {str(e)}')
        # No lanzar excepción para que la migración no falle
        # El usuario puede crearse manualmente después


def reverse_create_initial_superuser(apps, schema_editor):
    """Eliminar el superusuario inicial (opcional)"""
    username = os.getenv('SUPERUSER_USERNAME', 'admin')
    try:
        User.objects.filter(username=username, is_superuser=True).delete()
        print(f'Superusuario "{username}" eliminado.')
    except Exception as e:
        print(f'Error al eliminar superusuario: {str(e)}')


class Migration(migrations.Migration):

    dependencies = [
        ('kanban', '0012_task_reminder_sent'),
    ]

    operations = [
        migrations.RunPython(
            create_initial_superuser,
            reverse_create_initial_superuser
        ),
    ]

