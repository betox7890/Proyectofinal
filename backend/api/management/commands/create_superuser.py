"""
Comando de management para crear un superusuario automáticamente.
Uso: python manage.py create_superuser --username admin --email admin@example.com --password secret123
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os


class Command(BaseCommand):
    help = 'Crea un superusuario automáticamente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default=os.getenv('SUPERUSER_USERNAME', 'admin'),
            help='Nombre de usuario del superusuario'
        )
        parser.add_argument(
            '--email',
            type=str,
            default=os.getenv('SUPERUSER_EMAIL', 'admin@example.com'),
            help='Email del superusuario'
        )
        parser.add_argument(
            '--password',
            type=str,
            default=os.getenv('SUPERUSER_PASSWORD', None),
            help='Contraseña del superusuario'
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='No pedir confirmación interactiva'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        no_input = options['no_input']

        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'El usuario "{username}" ya existe. Saltando creación.')
            )
            return

        # Si no hay contraseña, generar una aleatoria o pedirla
        if not password:
            if no_input:
                # En modo no-interactivo, generar contraseña aleatoria
                import secrets
                password = secrets.token_urlsafe(16)
                self.stdout.write(
                    self.style.WARNING(f'No se proporcionó contraseña. Generada automáticamente.')
                )
            else:
                # Pedir contraseña interactivamente
                password = self.get_password()

        # Crear el superusuario
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superusuario "{username}" creado exitosamente.')
            )
            if not no_input:
                self.stdout.write(f'Email: {email}')
                self.stdout.write(f'Contraseña: {password}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear superusuario: {str(e)}')
            )
            raise

    def get_password(self):
        """Obtener contraseña de forma segura"""
        import getpass
        password = getpass.getpass('Contraseña: ')
        password_confirm = getpass.getpass('Confirmar contraseña: ')
        
        if password != password_confirm:
            self.stdout.write(self.style.ERROR('Las contraseñas no coinciden.'))
            return self.get_password()
        
        if len(password) < 8:
            self.stdout.write(self.style.ERROR('La contraseña debe tener al menos 8 caracteres.'))
            return self.get_password()
        
        return password

