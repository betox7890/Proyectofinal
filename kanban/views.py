from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max, Prefetch, Q
from django.urls import reverse
from django.contrib import messages
from datetime import datetime, timedelta
from pathlib import Path
import json
import base64
import logging
from io import BytesIO

from django.templatetags.static import static
from django.utils import timezone

from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

import pyotp
import qrcode

logger = logging.getLogger(__name__)

from .models import (
    List,
    Task,
    Subtask,
    Invitation,
    Activity,
    ActivityComment,
    BoardPreference,
    TwoFactorProfile,
    TaskAttachment,
    SubtaskAttachment,
)
from django.contrib.auth.models import User

BOARD_COLORS = [
    '#4c1d95',  # Purple (actual)
    '#1d4ed8',  # Azul
    '#0f766e',  # Verde aguamarina
    '#b91c1c',  # Rojo oscuro
    '#f97316',  # Naranja
    '#0f172a',  # Azul oscuro
    '#1f2937',  # Gris oscuro
]

def hex_to_rgba(hex_color, alpha=0.65):
    if not hex_color:
        return 'transparent'
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])
    try:
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return 'transparent'
    return f'rgba({r}, {g}, {b}, {alpha})'

DEFAULT_LISTS = [
    {'name': 'Pendiente', 'color': 'yellow', 'order': 0},
    {'name': 'En Progreso', 'color': 'green', 'order': 1},
    {'name': 'Finalizado', 'color': 'black', 'order': 2},
]


def get_board_preference(user):
    preference, _ = BoardPreference.objects.get_or_create(user=user, defaults={'color': 'transparent'})
    return preference


def get_board_color(user):
    preference = get_board_preference(user)
    return preference.color


def ensure_default_lists(board_user):
    """Garantiza que existan las listas básicas del tablero"""
    for data in DEFAULT_LISTS:
        list_obj, created = List.objects.get_or_create(
            user=board_user,
            name=data['name'],
            defaults={
                'color': data['color'],
                'order': data['order'],
            }
        )
        updated = False
        if list_obj.color != data['color']:
            list_obj.color = data['color']
            updated = True
        if list_obj.order != data['order']:
            list_obj.order = data['order']
            updated = True
        if updated:
            list_obj.save(update_fields=['color', 'order'])


def get_shared_admin_user():
    """Obtiene o crea el usuario compartido para administradores"""
    username = 'admin_shared'
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'is_staff': True,
            'is_superuser': True,
        }
    )
    return user


def get_user_for_board(user):
    """Retorna el usuario apropiado para mostrar el tablero"""
    # Si el usuario es administrador, usar el usuario compartido
    if user.is_staff or user.is_superuser:
        return get_shared_admin_user()
    # Si el estudiante tiene una invitación aceptada, usar el tablero compartido
    if Invitation.objects.filter(student=user, accepted=True).exists():
        return get_shared_admin_user()
    # Si no es administrador ni tiene invitación, usar su propio usuario
    return user


def can_delete(user):
    """Verifica si un usuario puede eliminar elementos"""
    # Solo los administradores pueden eliminar
    return user.is_staff or user.is_superuser


def get_user_type(user):
    """Retorna el tipo de usuario como string"""
    if user.is_staff or user.is_superuser:
        return 'Administrador'
    return 'Estudiante'


def get_two_factor_profile(user, ensure_secret=False):
    """Obtiene (y opcionalmente inicializa) el perfil 2FA de un usuario"""
    profile, _ = TwoFactorProfile.objects.get_or_create(user=user)
    if ensure_secret and not profile.secret:
        profile.secret = pyotp.random_base32()
        profile.save(update_fields=['secret', 'updated_at'])
    return profile


def generate_qr_code_base64(data):
    """Genera una imagen QR en base64 a partir de un string"""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
    return f"data:image/png;base64,{encoded}"


def log_activity(user, activity_type, description, task=None, list_obj=None, subtask=None):
    """
    Registra una actividad realizada por un usuario invitado (no administrador).
    Solo registra actividades de usuarios que tienen una invitación aceptada.
    """
    if not (user.is_staff or user.is_superuser):
        if not Invitation.objects.filter(student=user, accepted=True).exists():
            return
    
    # Crear el registro de actividad
    activity = Activity.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        task=task,
        list=list_obj,
        subtask=subtask
    )

    # Enviar notificación en tiempo real a través de WebSocket
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            # Obtener información de manera segura (puede que algunos objetos ya hayan sido eliminados)
            task_id = None
            task_title = None
            subtask_id = None
            subtask_title = None
            list_id = None
            list_name = None
            
            try:
                if activity.task:
                    task_id = activity.task.id
                    task_title = activity.task.title
            except Exception:
                pass  # La tarea puede haber sido eliminada
            
            try:
                if activity.subtask:
                    subtask_id = activity.subtask.id
                    subtask_title = activity.subtask.title
            except Exception:
                pass  # La subtarea puede haber sido eliminada
            
            try:
                if activity.list:
                    list_id = activity.list.id
                    list_name = activity.list.name
            except Exception:
                pass  # La lista puede haber sido eliminada
            
            payload = {
                'type': 'activity',
                'activity_id': activity.id,
                'user': activity.user.username,
                'activity_type': activity.get_activity_type_display(),
                'description': activity.description,
                'created_at': activity.created_at.strftime('%d/%m/%Y %H:%M:%S'),
                'task_id': task_id,
                'task_title': task_title,
                'subtask_id': subtask_id,
                'subtask_title': subtask_title,
                'list_id': list_id,
                'list_name': list_name,
            }
            async_to_sync(channel_layer.group_send)(
                'activities',
                {
                    'type': 'activity_broadcast',
                    'payload': payload,
                }
            )
            logger.info(f"Notificación de actividad enviada: {activity.activity_type} por {activity.user.username}")
        else:
            logger.warning("Channel layer no disponible. Las notificaciones en tiempo real no funcionarán.")
    except Exception as e:
        logger.error(f"Error al enviar notificación en tiempo real: {e}", exc_info=True)


def login_view(request):
    """Vista de inicio de sesión"""
    if request.user.is_authenticated:
        return redirect('kanban:board')

    error_message = None
    requires_2fa = False
    username = ''

    if request.method == 'POST':
        step = request.POST.get('step', 'password')

        if step == 'totp':
            pending_user = get_pending_2fa_user(request)
            backend = request.session.get('pending_2fa_backend')
            username = request.session.get('pending_2fa_username', '')

            if not pending_user:
                error_message = 'La sesión de verificación expiró. Ingresa tus credenciales nuevamente.'
                clear_pending_2fa_session(request)
            else:
                profile = get_two_factor_profile(pending_user)
                if not profile.enabled or not profile.secret:
                    login_with_backend(request, pending_user, backend)
                    clear_pending_2fa_session(request)
                    return redirect('kanban:board')

                code = request.POST.get('code', '').strip().replace(' ', '')
                totp = pyotp.TOTP(profile.secret)

                if totp.verify(code, valid_window=1):
                    login_with_backend(request, pending_user, backend)
                    clear_pending_2fa_session(request)
                    return redirect('kanban:board')
                else:
                    error_message = 'Código inválido. Intenta nuevamente.'
                    requires_2fa = True
        else:
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                backend = getattr(user, 'backend', 'django.contrib.auth.backends.ModelBackend')
                profile = TwoFactorProfile.objects.filter(user=user, enabled=True).first()

                if profile:
                    request.session['pending_2fa_user'] = user.id
                    request.session['pending_2fa_backend'] = backend
                    request.session['pending_2fa_username'] = username
                    requires_2fa = True
                else:
                    clear_pending_2fa_session(request)
                    login(request, user)
                    return redirect('kanban:board')
            else:
                error_message = "Usuario o contraseña incorrectos."
                clear_pending_2fa_session(request)
    else:
        clear_pending_2fa_session(request)

    context = {
        'error_message': error_message,
        'username': username,
        'requires_2fa': requires_2fa,
    }
    return render(request, 'kanban/login.html', context)


def clear_pending_2fa_session(request):
    request.session.pop('pending_2fa_user', None)
    request.session.pop('pending_2fa_backend', None)


def get_pending_2fa_user(request):
    pending_user_id = request.session.get('pending_2fa_user')
    if not pending_user_id:
        return None
    try:
        return User.objects.get(id=pending_user_id)
    except User.DoesNotExist:
        return None


def login_with_backend(request, user, backend_path):
    backend = backend_path or 'django.contrib.auth.backends.ModelBackend'
    user.backend = backend
    login(request, user)


@login_required
def two_factor_setup(request):
    """Configurar la autenticación de dos pasos para el usuario autenticado"""
    profile = get_two_factor_profile(request.user, ensure_secret=True)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'enable':
            code = request.POST.get('code', '').strip().replace(' ', '')
            totp = pyotp.TOTP(profile.secret)
            if totp.verify(code, valid_window=1):
                if not profile.enabled:
                    profile.enabled = True
                    profile.save(update_fields=['enabled', 'updated_at'])
                messages.success(request, 'Autenticación de dos pasos habilitada correctamente.')
            else:
                messages.error(request, 'El código proporcionado no es válido. Intenta nuevamente.')
        elif action == 'regenerate':
            profile.secret = pyotp.random_base32()
            profile.enabled = False
            profile.save(update_fields=['secret', 'enabled', 'updated_at'])
            messages.success(request, 'Se generó un nuevo código secreto. Debes escanear el nuevo código QR antes de habilitar 2FA.')
        elif action == 'disable':
            if profile.enabled:
                profile.enabled = False
                profile.save(update_fields=['enabled', 'updated_at'])
            messages.success(request, 'Autenticación de dos pasos deshabilitada.')
        else:
            messages.error(request, 'Acción no reconocida.')

        profile.refresh_from_db()

    totp = pyotp.TOTP(profile.secret)
    provisioning_uri = totp.provisioning_uri(name=request.user.username, issuer_name='Kanban Board')
    qr_data_uri = generate_qr_code_base64(provisioning_uri)

    context = {
        'profile': profile,
        'provisioning_uri': provisioning_uri,
        'qr_code_data_uri': qr_data_uri,
        'totp_interval': totp.interval,
    }
    return render(request, 'kanban/two_factor_setup.html', context)


@login_required
def system_logs_view(request):
    """Muestra los logs de la aplicación para administradores"""
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden('No tienes permisos para ver los registros del sistema.')

    log_file = getattr(settings, 'LOG_FILE_PATH', None)
    log_lines = []
    file_exists = False

    if log_file and Path(log_file).exists():
        try:
            with open(log_file, 'r', encoding='utf-8', errors='replace') as fh:
                lines = fh.readlines()
                log_lines = lines[-500:] if lines else []
            file_exists = True
        except OSError as exc:
            log_lines = [f'No se pudo leer el archivo de logs: {exc}']
    else:
        log_lines = ['El archivo de logs aún no ha sido creado.']

    context = {
        'log_lines': log_lines,
        'file_exists': file_exists,
        'log_file_path': log_file,
    }
    return render(request, 'kanban/system_logs.html', context)


@login_required
@require_POST
def add_task(request):
    """Añadir una nueva tarea a una lista"""
    list_id = request.POST.get('list_id')
    title = request.POST.get('title', 'Nueva Tarea')
    
    # Usar usuario compartido si es administrador
    board_user = get_user_for_board(request.user)
    list_obj = get_object_or_404(List, id=list_id, user=board_user)
    
    # Obtener el máximo orden actual y sumar 1
    max_order = list_obj.tasks.aggregate(Max('order'))['order__max'] or 0
    
    task = Task.objects.create(
        title=title,
        list=list_obj,
        order=max_order + 1,
        created_by=request.user
    )
    
    # Registrar actividad
    log_activity(
        request.user,
        'create_task',
        f'{title} - Creada por {request.user.username}',
        task=task,
        list_obj=list_obj
    )
    
    return JsonResponse({
        'success': True,
        'task_id': task.id,
        'task_title': task.title
    })


@login_required
@require_POST
def add_list(request):
    """Añadir una nueva lista al tablero"""
    name = request.POST.get('name', 'Nueva Lista')
    
    # Usar usuario compartido si es administrador
    board_user = get_user_for_board(request.user)
    
    # Obtener el máximo orden actual y sumar 1
    max_order = List.objects.filter(user=board_user).aggregate(Max('order'))['order__max'] or 0
    
    list_obj = List.objects.create(
        name=name,
        user=board_user,
        order=max_order + 1,
        color='purple',
        created_by=request.user
    )
    
    # Registrar actividad
    log_activity(
        request.user,
        'create_list',
        f'{name} - Creada por {request.user.username}',
        list_obj=list_obj
    )
    
    return JsonResponse({
        'success': True,
        'list_id': list_obj.id,
        'list_name': list_obj.name
    })


@login_required
@require_POST
def update_task(request, task_id):
    """Actualizar una tarea existente"""
    # Usar usuario compartido si es administrador
    board_user = get_user_for_board(request.user)
    task = get_object_or_404(Task, id=task_id, list__user=board_user)
    old_title = task.title
    old_due_date = task.due_date
    title = request.POST.get('title')
    due_date_str = request.POST.get('due_date', '').strip()

    changes = []
    if title is not None:
        title = title.strip()
        if title:
            task.title = title
            if title != old_title:
                changes.append(f'título a "{title}"')
        else:
            return JsonResponse({'success': False, 'error': 'El título no puede estar vacío'}, status=400)

    # Manejar cambios de fecha (incluyendo cuando se elimina la fecha)
    if 'due_date' in request.POST:
        if due_date_str:
            try:
                new_due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                if new_due_date != old_due_date:
                    task.due_date = new_due_date
                    changes.append(f'fecha de vencimiento a {new_due_date.strftime("%d/%m/%Y")}')
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Formato de fecha inválido'}, status=400)
        else:
            # Se está eliminando la fecha
            if old_due_date:
                task.due_date = None
                changes.append('fecha de vencimiento (eliminada)')

    task.save()

    # Registrar actividad si hay cambios
    if changes:
        log_activity(
            request.user,
            'edit_task',
            f'Actualizó {" y ".join(changes)} para la tarea "{task.title}"',
            task=task,
            list_obj=task.list
        )

    return JsonResponse({
        'success': True,
        'task_id': task.id,
        'task_title': task.title,
        'due_date': task.due_date.strftime('%Y-%m-%d')
    })


@login_required
@require_POST
def delete_task(request, task_id):
    """Eliminar una tarea"""
    # Verificar permisos de eliminación
    if not can_delete(request.user):
        return JsonResponse({
            'success': False,
            'error': 'No tienes permisos para eliminar tareas'
        }, status=403)
    
    # Usar usuario compartido si es administrador
    board_user = get_user_for_board(request.user)
    task = get_object_or_404(Task, id=task_id, list__user=board_user)
    task_title = task.title
    task_list = task.list
    
    # Registrar actividad antes de eliminar
    log_activity(
        request.user,
        'delete_task',
        f'Eliminó/cerró la tarea "{task_title}" de la lista "{task_list.name}"',
        task=task,
        list_obj=task_list
    )
    
    task.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Tarea eliminada exitosamente'
    })


@login_required
@require_POST
def change_list_color(request, list_id):
    """Cambiar el color de una lista"""
    try:
        data = json.loads(request.body)
        new_color = data.get('color')
        
        # Colores válidos
        valid_colors = ['green', 'yellow', 'black', 'purple']
        
        if not new_color:
            return JsonResponse({
                'success': False,
                'error': 'Color no especificado'
            }, status=400)
        
        if new_color not in valid_colors:
            return JsonResponse({
                'success': False,
                'error': f'Color no válido: {new_color}. Colores válidos: {", ".join(valid_colors)}'
            }, status=400)
        
        # Usar usuario compartido si es administrador
        board_user = get_user_for_board(request.user)
        list_obj = get_object_or_404(List, id=list_id, user=board_user)
        old_color = list_obj.color
        list_obj.color = new_color
        list_obj.save()
        
        # Verificar que se guardó correctamente
        list_obj.refresh_from_db()
        
        # Registrar actividad
        log_activity(
            request.user,
            'edit_list',
            f'Cambió el color de la lista "{list_obj.name}" de {old_color} a {new_color}',
            list_obj=list_obj
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Color de lista cambiado de {old_color} a {new_color}',
            'color': list_obj.color
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': error_trace
        }, status=400)


@login_required
@require_POST
def delete_list(request, list_id):
    """Eliminar una lista y todas sus tareas y subtareas"""
    # Verificar permisos de eliminación
    if not can_delete(request.user):
        return JsonResponse({
            'success': False,
            'error': 'No tienes permisos para eliminar listas'
        }, status=403)
    
    # Usar usuario compartido si es administrador
    board_user = get_user_for_board(request.user)
    list_obj = get_object_or_404(List, id=list_id, user=board_user)
    
    # Guardar información antes de eliminar para el registro de actividad
    list_name = list_obj.name
    list_id = list_obj.id
    task_count = list_obj.tasks.count()
    subtask_count = Subtask.objects.filter(task__list=list_obj).count()
    
    # Registrar actividad antes de eliminar (pasar el objeto antes de eliminarlo)
    log_activity(
        request.user,
        'delete_list',
        f'Eliminó la lista "{list_name}" con {task_count} tarea(s) y {subtask_count} subtarea(s)',
        list_obj=list_obj
    )
    
    # Eliminar la lista (CASCADE eliminará automáticamente tareas y subtareas)
    list_obj.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Lista eliminada exitosamente. Se eliminaron {task_count} tareas y {subtask_count} subtareas.'
    })


@login_required
@require_POST
def move_task(request, task_id):
    """Mover una tarea a otra lista"""
    # Usar usuario compartido si es administrador
    board_user = get_user_for_board(request.user)
    task = get_object_or_404(Task, id=task_id, list__user=board_user)
    old_list = task.list
    new_list_id = request.POST.get('list_id')
    
    new_list = get_object_or_404(List, id=new_list_id, user=board_user)
    
    # Obtener el máximo orden en la nueva lista y sumar 1
    max_order = new_list.tasks.aggregate(Max('order'))['order__max'] or 0
    
    task.list = new_list
    task.order = max_order + 1
    task.save()
    
    # Registrar actividad
    log_activity(
        request.user,
        'move_task',
        f'Movió la tarea "{task.title}" de "{old_list.name}" a "{new_list.name}"',
        task=task,
        list_obj=new_list
    )
    
    return JsonResponse({
        'success': True,
        'task_id': task.id,
        'new_list_id': new_list.id
    })


@login_required
@require_POST
def add_subtask(request, task_id):
    """Agregar una nueva subtarea a una tarea"""
    # Usar usuario compartido si es administrador
    board_user = get_user_for_board(request.user)
    task = get_object_or_404(Task, id=task_id, list__user=board_user)
    title = request.POST.get('title', 'Nueva Subtarea')
    
    # Obtener el máximo orden actual y sumar 1
    max_order = task.subtasks.aggregate(Max('order'))['order__max'] or 0
    
    subtask = Subtask.objects.create(
        title=title,
        task=task,
        order=max_order + 1,
        completed=False,
        created_by=request.user
    )
    
    # Registrar actividad
    log_activity(
        request.user,
        'create_subtask',
        f'{title} - Creada por {request.user.username}',
        task=task,
        list_obj=task.list,
        subtask=subtask
    )
    
    return JsonResponse({
        'success': True,
        'subtask_id': subtask.id,
        'subtask_title': subtask.title
    })


@login_required
@require_POST
def update_subtask(request, subtask_id):
    """Actualizar una subtarea existente"""
    # Usar usuario compartido si es administrador
    board_user = get_user_for_board(request.user)
    subtask = get_object_or_404(Subtask, id=subtask_id, task__list__user=board_user)
    old_title = subtask.title
    old_completed = subtask.completed
    old_due_date = subtask.due_date
    title = request.POST.get('title')
    completed = request.POST.get('completed')
    due_date_str = request.POST.get('due_date', '').strip()

    changes = []

    if title is not None:
        title = title.strip()
        if title:
            subtask.title = title
            if title != old_title:
                changes.append(f'título a "{title}"')
        else:
            return JsonResponse({'success': False, 'error': 'El título de la subtarea no puede estar vacío'}, status=400)

    if completed is not None:
        subtask.completed = completed.lower() in ('true', '1', 'on')
        if subtask.completed != old_completed:
            estado_texto = 'completada' if subtask.completed else 'pendiente'
            changes.append(f'estado a {estado_texto}')

    # Manejar cambios de fecha (incluyendo cuando se elimina la fecha)
    if 'due_date' in request.POST:
        if due_date_str:
            try:
                new_due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                if new_due_date != old_due_date:
                    subtask.due_date = new_due_date
                    changes.append(f'fecha de vencimiento a {new_due_date.strftime("%d/%m/%Y")}')
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Formato de fecha inválido'}, status=400)
        else:
            # Se está eliminando la fecha
            if old_due_date:
                subtask.due_date = None
                changes.append('fecha de vencimiento (eliminada)')

    subtask.save()

    # Registrar actividad si hay cambios
    if changes:
        log_activity(
            request.user,
            'edit_subtask',
            f'Actualizó {" y ".join(changes)} en la subtarea "{subtask.title}"',
            task=subtask.task,
            list_obj=subtask.task.list,
            subtask=subtask
        )

    return JsonResponse({
        'success': True,
        'subtask_id': subtask.id,
        'subtask_title': subtask.title,
        'subtask_completed': subtask.completed,
        'due_date': subtask.due_date.strftime('%Y-%m-%d')
    })


@login_required
@require_POST
def delete_subtask(request, subtask_id):
    """Eliminar una subtarea"""
    # Verificar permisos de eliminación
    if not can_delete(request.user):
        return JsonResponse({
            'success': False,
            'error': 'No tienes permisos para eliminar subtareas'
        }, status=403)
    
    # Usar usuario compartido si es administrador
    board_user = get_user_for_board(request.user)
    subtask = get_object_or_404(Subtask, id=subtask_id, task__list__user=board_user)
    subtask_title = subtask.title
    subtask_task = subtask.task
    subtask_list = subtask.task.list
    
    # Registrar actividad antes de eliminar
    log_activity(
        request.user,
        'delete_subtask',
        f'Eliminó la subtarea "{subtask_title}" de la tarea "{subtask_task.title}"',
        task=subtask_task,
        list_obj=subtask_list,
        subtask=subtask
    )
    
    subtask.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Subtarea eliminada exitosamente'
    })


@login_required
@require_POST
def toggle_subtask(request, subtask_id):
    """Cambiar el estado de completado de una subtarea"""
    # Usar usuario compartido si es administrador
    board_user = get_user_for_board(request.user)
    subtask = get_object_or_404(Subtask, id=subtask_id, task__list__user=board_user)
    old_completed = subtask.completed
    subtask.completed = not subtask.completed
    subtask.save()
    
    # Registrar actividad
    status_text = "completó" if subtask.completed else "descompletó"
    log_activity(
        request.user,
        'toggle_subtask',
        f'{status_text.capitalize()} la subtarea "{subtask.title}" de la tarea "{subtask.task.title}"',
        task=subtask.task,
        list_obj=subtask.task.list,
        subtask=subtask
    )
    
    return JsonResponse({
        'success': True,
        'subtask_id': subtask.id,
        'completed': subtask.completed
    })


@login_required
@require_POST
def reorder_lists(request):
    """Reordenar las listas del tablero"""
    try:
        data = json.loads(request.body)
        list_ids = data.get('list_ids', [])
        
        # Usar usuario compartido si es administrador
        board_user = get_user_for_board(request.user)
        
        # Actualizar el orden de las listas
        for index, list_id in enumerate(list_ids):
            list_obj = get_object_or_404(List, id=list_id, user=board_user)
            list_obj.order = index
            list_obj.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Listas reordenadas exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def reorder_tasks(request):
    """Reordenar tareas dentro de una lista o entre listas"""
    try:
        data = json.loads(request.body)
        task_ids = data.get('task_ids', [])
        list_id = data.get('list_id')
        
        # Usar usuario compartido si es administrador
        board_user = get_user_for_board(request.user)
        
        list_obj = get_object_or_404(List, id=list_id, user=board_user)
        
        # Actualizar el orden de las tareas
        for index, task_id in enumerate(task_ids):
            task = get_object_or_404(Task, id=task_id, list__user=board_user)
            old_list = task.list
            old_list_name = old_list.name if old_list else None
            task.list = list_obj
            task.order = index + 1
            task.save()
            
            # Registrar actividad solo si la lista cambió
            if old_list and old_list != list_obj:
                log_activity(
                    request.user,
                    'move_task',
                    f'Movió la tarea "{task.title}" de "{old_list_name}" a "{list_obj.name}"',
                    task=task,
                    list_obj=list_obj
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Tareas reordenadas exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def reorder_subtasks(request):
    """Reordenar subtareas dentro de una tarea"""
    try:
        data = json.loads(request.body)
        subtask_ids = data.get('subtask_ids', [])
        task_id = data.get('task_id')
        
        # Usar usuario compartido si es administrador
        board_user = get_user_for_board(request.user)
        
        task = get_object_or_404(Task, id=task_id, list__user=board_user)
        
        # Actualizar el orden de las subtareas
        for index, subtask_id in enumerate(subtask_ids):
            subtask = get_object_or_404(Subtask, id=subtask_id, task__list__user=board_user)
            subtask.task = task
            subtask.order = index + 1
            subtask.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Subtareas reordenadas exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def board_view(request):
    """Vista principal del tablero Kanban"""
    is_admin = request.user.is_staff or request.user.is_superuser
    is_invited = False
    board_user = get_user_for_board(request.user)

    ensure_default_lists(board_user)

    comment_prefetch = Prefetch(
        'comments',
        queryset=ActivityComment.objects.select_related('author').order_by('created_at')
    )

    all_task_qs = Task.objects.filter(list__user=board_user)

    search_query = request.GET.get('q', '').strip()
    creator_filter = request.GET.get('creator', '').strip()
    due_from = request.GET.get('due_from', '').strip()
    due_to = request.GET.get('due_to', '').strip()

    # Aplicar filtros solo si hay alguno activo
    task_filters = all_task_qs

    if search_query:
        task_filters = task_filters.filter(title__icontains=search_query)

    if creator_filter:
        if creator_filter == 'none':
            task_filters = task_filters.filter(created_by__isnull=True)
        else:
            try:
                creator_id = int(creator_filter)
                task_filters = task_filters.filter(created_by_id=creator_id)
            except ValueError:
                pass

    if due_from:
        try:
            due_from_date = datetime.strptime(due_from, '%Y-%m-%d').date()
            task_filters = task_filters.filter(due_date__gte=due_from_date)
        except ValueError:
            pass

    if due_to:
        try:
            due_to_date = datetime.strptime(due_to, '%Y-%m-%d').date()
            task_filters = task_filters.filter(due_date__lte=due_to_date)
        except ValueError:
            pass

    task_filters = task_filters.select_related('created_by', 'list').order_by('order')

    task_attachment_prefetch = Prefetch(
        'attachments',
        queryset=TaskAttachment.objects.select_related('uploaded_by').order_by('-uploaded_at')
    )
    subtask_attachment_prefetch = Prefetch(
        'attachments',
        queryset=SubtaskAttachment.objects.select_related('uploaded_by').order_by('-uploaded_at')
    )
    subtask_prefetch = Prefetch(
        'subtasks',
        queryset=Subtask.objects.select_related('created_by').prefetch_related(subtask_attachment_prefetch).order_by('order')
    )
    task_filters = task_filters.prefetch_related(subtask_prefetch, task_attachment_prefetch)

    prefetch_tasks = Prefetch('tasks', queryset=task_filters, to_attr='filtered_tasks')

    lists = List.objects.filter(user=board_user).select_related('created_by').prefetch_related(prefetch_tasks)

    board_color = get_board_color(board_user)
    board_overlay_color = hex_to_rgba(board_color)
    preference = get_board_preference(board_user)
    if preference.background_image:
        board_background_image = preference.background_image.url
    else:
        board_background_image = static('kanban/img/board-bg.jpg')

    total_filtered_tasks = sum(len(getattr(lst, 'filtered_tasks', [])) for lst in lists)

    creator_ids = all_task_qs.exclude(created_by__isnull=True).values_list('created_by', flat=True).distinct()
    creators = User.objects.filter(id__in=creator_ids).order_by('username')

    # Obtener invitaciones para mostrar en el template
    pending_invitations = Invitation.objects.none()
    students = User.objects.none()
    activities = Activity.objects.none()
    can_view_activities = False
    activities_heading = 'Actividades recientes'

    if is_admin:
        # Si es administrador, mostrar estudiantes disponibles e invitaciones enviadas
        # Excluir estudiantes que ya tienen invitaciones aceptadas o pendientes de este admin
        invited_student_ids = Invitation.objects.filter(admin=request.user).values_list('student_id', flat=True)
        students = User.objects.filter(is_staff=False, is_superuser=False).exclude(id__in=invited_student_ids)
        pending_invitations = Invitation.objects.filter(admin=request.user, accepted=False)
        # Obtener actividades de todos los estudiantes invitados por este administrador
        invited_students = Invitation.objects.filter(admin=request.user, accepted=True).values_list('student_id', flat=True)
        activities = Activity.objects.filter(
            Q(user_id__in=invited_students) | Q(user=request.user)
        ).select_related(
            'user',
            'task__created_by',
            'task__list',
            'list__created_by',
            'subtask__created_by',
            'subtask__task'
        ).prefetch_related(comment_prefetch).order_by('-created_at')
        can_view_activities = True
        activities_heading = 'Actividades de usuarios invitados'
    else:
        is_invited = Invitation.objects.filter(student=request.user, accepted=True).exists()
        if is_invited:
            activities = Activity.objects.filter(user=request.user).select_related(
                'user',
                'task__created_by',
                'task__list',
                'list__created_by',
                'subtask__created_by',
                'subtask__task'
            ).prefetch_related(comment_prefetch).order_by('-created_at')
            can_view_activities = True
            activities_heading = 'Mis actividades'
        # Si es estudiante, mostrar invitaciones pendientes
        pending_invitations = Invitation.objects.filter(student=request.user, accepted=False)
    
    try:
        tf_profile = request.user.two_factor_profile
    except TwoFactorProfile.DoesNotExist:
        tf_profile = None

    context = {
        'lists': lists,
        'user_type': get_user_type(request.user),
        'can_delete': can_delete(request.user),
        'students': students,
        'pending_invitations': pending_invitations,
        'is_invited': is_invited if not is_admin else False,
        'activities': activities,
        'can_view_activities': can_view_activities,
        'activities_heading': activities_heading,
        'board_colors': BOARD_COLORS,
        'board_color': board_color,
        'board_overlay_color': board_overlay_color,
        'board_background_image': board_background_image,
        'creators': creators,
        'filters': {
            'q': search_query,
            'creator': creator_filter,
            'due_from': due_from,
            'due_to': due_to,
        },
        'has_filters': any([search_query, creator_filter, due_from, due_to]),
        'total_filtered_tasks': total_filtered_tasks,
        'two_factor_enabled': tf_profile.enabled if tf_profile else False,
        'two_factor_setup_url': reverse('kanban:two_factor_setup'),
        'attachment_max_size_mb': get_max_attachment_size() // (1024 * 1024),
    }
    return render(request, 'kanban/board.html', context)


@login_required
@require_POST
def change_board_color(request):
    """Actualizar el color de fondo del tablero"""
    color = request.POST.get('color')
    if not color:
        return JsonResponse({'success': False, 'error': 'Color no proporcionado'}, status=400)

    if color not in BOARD_COLORS and color != 'transparent':
        return JsonResponse({'success': False, 'error': 'Color no permitido'}, status=400)

    board_user = get_user_for_board(request.user)
    preference = get_board_preference(board_user)
    preference.color = color
    preference.save(update_fields=['color', 'updated_at'])

    return JsonResponse({'success': True, 'message': 'Color actualizado correctamente', 'color': color})


@login_required
@require_POST
def invite_student(request):
    """Invitar un estudiante al tablero compartido (solo administradores)"""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({
            'success': False,
            'error': 'Solo los administradores pueden invitar estudiantes'
        }, status=403)
    
    student_id = request.POST.get('student_id')
    if not student_id:
        return JsonResponse({
            'success': False,
            'error': 'ID de estudiante no especificado'
        }, status=400)
    
    try:
        student = User.objects.get(id=student_id, is_staff=False, is_superuser=False)
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Estudiante no encontrado'
        }, status=404)
    
    # Crear o obtener la invitación
    invitation, created = Invitation.objects.get_or_create(
        admin=request.user,
        student=student,
        defaults={'accepted': False}
    )
    
    if not created:
        if invitation.accepted:
            return JsonResponse({
                'success': False,
                'error': f'El estudiante {student.username} ya está invitado y ha aceptado'
            }, status=400)
        else:
            return JsonResponse({
                'success': False,
                'error': f'Ya existe una invitación pendiente para {student.username}'
            }, status=400)
    
    return JsonResponse({
        'success': True,
        'message': f'Invitación enviada a {student.username}'
    })


@login_required
@require_POST
def accept_invitation(request, invitation_id):
    """Aceptar una invitación (solo estudiantes)"""
    if request.user.is_staff or request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'error': 'Los administradores no pueden aceptar invitaciones'
        }, status=403)
    
    try:
        invitation = Invitation.objects.get(id=invitation_id, student=request.user)
        if invitation.accepted:
            return JsonResponse({
                'success': False,
                'error': 'Esta invitación ya fue aceptada'
            }, status=400)
        
        invitation.accepted = True
        invitation.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Invitación aceptada. Ahora puedes ver el tablero compartido'
        })
    except Invitation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Invitación no encontrada'
        }, status=404)


@login_required
@require_POST
def reject_invitation(request, invitation_id):
    """Rechazar una invitación"""
    try:
        invitation = Invitation.objects.get(id=invitation_id)
        # Verificar que el usuario puede rechazar esta invitación
        if invitation.student != request.user and invitation.admin != request.user:
            return JsonResponse({
                'success': False,
                'error': 'No tienes permiso para rechazar esta invitación'
            }, status=403)
        
        invitation.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Invitación rechazada'
        })
    except Invitation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Invitación no encontrada'
        }, status=404)


@login_required
def get_activities(request):
    """Obtener actividades de usuarios invitados (solo administradores)"""
    is_admin = request.user.is_staff or request.user.is_superuser

    comment_prefetch = Prefetch(
        'comments',
        queryset=ActivityComment.objects.select_related('author').order_by('created_at')
    )

    if is_admin:
        invited_students = Invitation.objects.filter(admin=request.user, accepted=True).values_list('student_id', flat=True)
        activities = Activity.objects.filter(
            Q(user_id__in=invited_students) | Q(user=request.user)
        ).select_related(
            'user',
            'task__created_by',
            'task__list',
            'list__created_by',
            'subtask__created_by',
            'subtask__task'
        ).prefetch_related(comment_prefetch).order_by('-created_at')
    else:
        if not Invitation.objects.filter(student=request.user, accepted=True).exists():
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para ver actividades'
            }, status=403)
        activities = Activity.objects.filter(user=request.user).select_related(
            'user',
            'task__created_by',
            'task__list',
            'list__created_by',
            'subtask__created_by',
            'subtask__task'
        ).prefetch_related(comment_prefetch).order_by('-created_at')
    
    activities_data = []
    for activity in activities:
        creator = activity.related_creator.username if activity.related_creator else None
        activities_data.append({
            'id': activity.id,
            'user': activity.user.username,
            'activity_type': activity.get_activity_type_display(),
            'description': activity.description,
            'created_at': activity.created_at.strftime('%d/%m/%Y %H:%M:%S'),
            'task_id': activity.task.id if activity.task else None,
            'task_title': activity.task.title if activity.task else None,
            'creator': creator,
            'comments': [
                {
                    'id': comment.id,
                    'author': comment.author.username,
                    'comment': comment.comment,
                    'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M:%S')
                }
                for comment in activity.comments.all()
            ]
        })
    
    return JsonResponse({
        'success': True,
        'activities': activities_data
    })


@login_required
@require_POST
def add_activity_comment(request, activity_id):
    """Permitir que administradores agreguen comentarios a actividades"""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({
            'success': False,
            'error': 'Solo los administradores pueden comentar actividades'
        }, status=403)

    comment_text = request.POST.get('comment', '').strip()
    if not comment_text:
        return JsonResponse({
            'success': False,
            'error': 'El comentario no puede estar vacío'
        }, status=400)

    activity = get_object_or_404(Activity, id=activity_id)
    comment = ActivityComment.objects.create(
        activity=activity,
        author=request.user,
        comment=comment_text
    )

    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'author': comment.author.username,
            'comment': comment.comment,
            'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M:%S')
        }
    }, status=201)


@login_required
@require_POST
def create_user(request):
    """Crear un nuevo usuario (administrador o estudiante) desde el tablero."""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({
            'success': False,
            'error': 'Solo los administradores pueden crear usuarios'
        }, status=403)

    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()
    email = request.POST.get('email', '').strip()
    role = request.POST.get('role', '').strip().lower()

    if not username or not password or not email:
        return JsonResponse({
            'success': False,
            'error': 'Todos los campos son obligatorios'
        }, status=400)

    if role not in ['admin', 'student']:
        return JsonResponse({
            'success': False,
            'error': 'Rol inválido. Debe ser "admin" o "student"'
        }, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({
            'success': False,
            'error': 'El nombre de usuario ya existe'
        }, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({
            'success': False,
            'error': 'Ya existe un usuario con ese correo'
        }, status=400)

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email
    )

    if role == 'admin':
        user.is_staff = True
        user.is_superuser = True
        user.save(update_fields=['is_staff', 'is_superuser'])

    return JsonResponse({
        'success': True,
        'message': f'Usuario {username} creado correctamente como {"Administrador" if role == "admin" else "Estudiante"}'
    })


@login_required
@require_POST
def upload_board_background(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Solo los administradores pueden subir fondos'}, status=403)

    image = request.FILES.get('image')
    if not image:
        return JsonResponse({'success': False, 'error': 'No se recibió ninguna imagen'}, status=400)

    if image.size > 4 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': 'La imagen debe pesar menos de 4MB'}, status=400)

    valid_content_types = {'image/png', 'image/jpeg', 'image/jpg', 'image/webp'}
    if image.content_type not in valid_content_types:
        return JsonResponse({'success': False, 'error': 'Formato de imagen no soportado'}, status=400)

    board_user = get_user_for_board(request.user)
    preference = get_board_preference(board_user)

    if preference.background_image:
        preference.background_image.delete(save=False)

    preference.background_image = image
    preference.save()

    return JsonResponse({'success': True, 'image_url': preference.background_image.url})


@login_required
def calendar_view(request):
    board_user = get_user_for_board(request.user)
    ensure_default_lists(board_user)

    preference = get_board_preference(board_user)
    board_color = get_board_color(board_user)
    board_overlay_color = hex_to_rgba(board_color)
    if preference.background_image:
        board_background_image = preference.background_image.url
    else:
        board_background_image = static('kanban/img/board-bg.jpg')

    today = timezone.now().date()

    tasks = Task.objects.filter(list__user=board_user).select_related('list', 'created_by').order_by('due_date', 'order')
    subtasks = Subtask.objects.filter(task__list__user=board_user).select_related('task', 'task__list', 'created_by').order_by('due_date', 'order')

    calendar_items = []

    for task in tasks:
        due_date = task.due_date
        due_in = (due_date - today).days if due_date else None
        calendar_items.append({
            'type': 'Tarea',
            'title': task.title,
            'list_name': task.list.name,
            'parent': None,
            'created_by': task.created_by.username if task.created_by else 'Administrador',
            'due_date': due_date,
            'due_in': due_in,
            'due_in_abs': abs(due_in) if due_in is not None else None,
            'status': classify_due(due_in),
        })

    for subtask in subtasks:
        due_date = subtask.due_date
        due_in = (due_date - today).days if due_date else None
        calendar_items.append({
            'type': 'Subtarea',
            'title': subtask.title,
            'list_name': subtask.task.list.name,
            'parent': subtask.task.title,
            'created_by': subtask.created_by.username if subtask.created_by else 'Administrador',
            'due_date': due_date,
            'due_in': due_in,
            'due_in_abs': abs(due_in) if due_in is not None else None,
            'status': classify_due(due_in),
        })

    calendar_items.sort(key=lambda item: (item['due_date'], item['type']))

    event_data = []
    for item in calendar_items:
        if item['due_date']:
            event_data.append({
                'title': item['title'],
                'type': item['type'],
                'date': item['due_date'].strftime('%Y-%m-%d'),
                'status': item['status'],
                'due_in': item['due_in'],
            })

    overdue = sum(1 for item in calendar_items if item['status'] == 'overdue')
    soon = sum(1 for item in calendar_items if item['status'] == 'soon')

    context = {
        'calendar_items': calendar_items,
        'overdue_count': overdue,
        'soon_count': soon,
        'total_items': len(calendar_items),
        'board_overlay_color': board_overlay_color,
        'board_background_image': board_background_image,
        'calendar_events_json': json.dumps(event_data),
    }

    return render(request, 'kanban/calendar.html', context)


def classify_due(due_in):
    if due_in is None:
        return 'unknown'
    if due_in < 0:
        return 'overdue'
    if due_in <= 3:
        return 'soon'
    return 'ok'


def get_max_attachment_size():
    return getattr(settings, 'ATTACHMENT_MAX_SIZE', 20 * 1024 * 1024)  # 20 MB por defecto


@login_required
@require_POST
def send_calendar_reminders(request):
    """Enviar recordatorios por correo desde el calendario"""
    try:
        data = json.loads(request.body)
        send_overdue = data.get('overdue', False)
        send_soon = data.get('soon', False)
        send_week = data.get('week', False)
        
        if not (send_overdue or send_soon or send_week):
            return JsonResponse({
                'success': False,
                'error': 'Debes seleccionar al menos una opción'
            }, status=400)
        
        board_user = get_user_for_board(request.user)
        today = timezone.now().date()
        
        from django.core.mail import send_mail
        
        reminders_sent = 0
        errors = 0
        recipients_set = set()
        
        # Tareas y subtareas vencidas
        if send_overdue:
            overdue_tasks = Task.objects.filter(
                list__user=board_user,
                due_date__lt=today,
                reminder_sent=False
            ).select_related('created_by', 'list').prefetch_related('subtasks')
            
            for task in overdue_tasks:
                if task.created_by and task.created_by.email:
                    recipient = task.created_by.email
                    if recipient not in recipients_set:
                        try:
                            days_overdue = (today - task.due_date).days
                            subject = f'[URGENTE] Tarea vencida: {task.title}'
                            message = f'''Hola {task.created_by.get_full_name() or task.created_by.username},

La tarea "{task.title}" está vencida desde hace {days_overdue} día(s).

Fecha de vencimiento: {task.due_date.strftime("%d/%m/%Y")}
Lista: {task.list.name}

Por favor, revisa el tablero Kanban y completa esta tarea lo antes posible.

Saludos,
Sistema de Gestión Kanban'''
                            
                            send_mail(
                                subject,
                                message,
                                settings.DEFAULT_FROM_EMAIL,
                                [recipient],
                                fail_silently=False,
                            )
                            task.reminder_sent = True
                            task.save(update_fields=['reminder_sent'])
                            reminders_sent += 1
                            recipients_set.add(recipient)
                            logger.info(f"Recordatorio de tarea vencida enviado a {recipient}")
                        except Exception as e:
                            errors += 1
                            logger.error(f"Error al enviar recordatorio para tarea vencida '{task.title}': {e}", exc_info=True)
            
            overdue_subtasks = Subtask.objects.filter(
                task__list__user=board_user,
                due_date__lt=today,
                completed=False
            ).select_related('task', 'task__created_by', 'task__list', 'created_by')
            
            for subtask in overdue_subtasks:
                recipient = None
                if subtask.created_by and subtask.created_by.email:
                    recipient = subtask.created_by.email
                elif subtask.task.created_by and subtask.task.created_by.email:
                    recipient = subtask.task.created_by.email
                
                if recipient and recipient not in recipients_set:
                    try:
                        days_overdue = (today - subtask.due_date).days
                        subject = f'[URGENTE] Subtarea vencida: {subtask.title}'
                        message = f'''Hola {subtask.task.created_by.get_full_name() or subtask.task.created_by.username},

La subtarea "{subtask.title}" de la tarea "{subtask.task.title}" está vencida desde hace {days_overdue} día(s).

Fecha de vencimiento: {subtask.due_date.strftime("%d/%m/%Y")}
Tarea: {subtask.task.title}
Lista: {subtask.task.list.name}

Por favor, revisa el tablero Kanban y completa esta subtarea lo antes posible.

Saludos,
Sistema de Gestión Kanban'''
                        
                        send_mail(
                            subject,
                            message,
                            settings.DEFAULT_FROM_EMAIL,
                            [recipient],
                            fail_silently=False,
                        )
                        reminders_sent += 1
                        recipients_set.add(recipient)
                        logger.info(f"Recordatorio de subtarea vencida enviado a {recipient}")
                    except Exception as e:
                        errors += 1
                        logger.error(f"Error al enviar recordatorio para subtarea vencida '{subtask.title}': {e}", exc_info=True)
        
        # Tareas que vencen en 1-3 días
        if send_soon:
            for days in [1, 2, 3]:
                target_date = today + timedelta(days=days)
                soon_tasks = Task.objects.filter(
                    list__user=board_user,
                    due_date=target_date,
                    reminder_sent=False
                ).select_related('created_by', 'list')
                
                for task in soon_tasks:
                    if task.created_by and task.created_by.email:
                        recipient = task.created_by.email
                        if recipient not in recipients_set:
                            try:
                                subject = f'[URGENTE] Tarea vence en {days} día(s): {task.title}' if days == 1 else f'Recordatorio: Tarea vence en {days} días - {task.title}'
                                message = f'''Hola {task.created_by.get_full_name() or task.created_by.username},

Esta es un recordatorio de que la tarea "{task.title}" vence en {days} día(s).

Fecha de vencimiento: {task.due_date.strftime("%d/%m/%Y")}
Lista: {task.list.name}

Por favor, revisa el tablero Kanban para asegurarte de que el trabajo esté en curso.

Saludos,
Sistema de Gestión Kanban'''
                                
                                send_mail(
                                    subject,
                                    message,
                                    settings.DEFAULT_FROM_EMAIL,
                                    [recipient],
                                    fail_silently=False,
                                )
                                task.reminder_sent = True
                                task.save(update_fields=['reminder_sent'])
                                reminders_sent += 1
                                recipients_set.add(recipient)
                                logger.info(f"Recordatorio de tarea próxima enviado a {recipient}")
                            except Exception as e:
                                errors += 1
                                logger.error(f"Error al enviar recordatorio para tarea próxima '{task.title}': {e}", exc_info=True)
        
        # Tareas que vencen en 4-7 días
        if send_week:
            for days in [4, 5, 6, 7]:
                target_date = today + timedelta(days=days)
                week_tasks = Task.objects.filter(
                    list__user=board_user,
                    due_date=target_date,
                    reminder_sent=False
                ).select_related('created_by', 'list')
                
                for task in week_tasks:
                    if task.created_by and task.created_by.email:
                        recipient = task.created_by.email
                        if recipient not in recipients_set:
                            try:
                                subject = f'Recordatorio: Tarea vence en {days} días - {task.title}'
                                message = f'''Hola {task.created_by.get_full_name() or task.created_by.username},

Esta es un recordatorio de que la tarea "{task.title}" vence en {days} día(s).

Fecha de vencimiento: {task.due_date.strftime("%d/%m/%Y")}
Lista: {task.list.name}

Por favor, revisa el tablero Kanban para asegurarte de que el trabajo esté en curso.

Saludos,
Sistema de Gestión Kanban'''
                                
                                send_mail(
                                    subject,
                                    message,
                                    settings.DEFAULT_FROM_EMAIL,
                                    [recipient],
                                    fail_silently=False,
                                )
                                task.reminder_sent = True
                                task.save(update_fields=['reminder_sent'])
                                reminders_sent += 1
                                recipients_set.add(recipient)
                                logger.info(f"Recordatorio de tarea semanal enviado a {recipient}")
                            except Exception as e:
                                errors += 1
                                logger.error(f"Error al enviar recordatorio para tarea semanal '{task.title}': {e}", exc_info=True)
        
        message = f'Se enviaron {reminders_sent} recordatorio(s) exitosamente.'
        if errors > 0:
            message += f' Hubo {errors} error(es).'
        
        details = f'Correos enviados a {len(recipients_set)} destinatario(s) único(s).'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'details': details,
            'reminders_sent': reminders_sent,
            'errors': errors,
            'recipients_count': len(recipients_set)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos inválidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Error al enviar recordatorios desde calendario: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error al enviar correos: {str(e)}'
        }, status=500)


@login_required
def api_get_current_user(request):
    """API endpoint para obtener información del usuario actual (para React)"""
    return JsonResponse({
        'success': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
        }
    })


@login_required
@require_POST
def upload_task_attachment(request, task_id):
    board_user = get_user_for_board(request.user)
    task = get_object_or_404(Task, id=task_id, list__user=board_user)

    attachment_file = request.FILES.get('file')
    if not attachment_file:
        return JsonResponse({'success': False, 'error': 'No se envió ningún archivo.'}, status=400)

    max_size = get_max_attachment_size()
    if attachment_file.size > max_size:
        return JsonResponse({'success': False, 'error': f'El archivo excede el tamaño máximo permitido ({max_size // (1024 * 1024)} MB).'}, status=400)

    attachment = TaskAttachment.objects.create(
        task=task,
        file=attachment_file,
        uploaded_by=request.user
    )

    log_activity(
        request.user,
        'add_attachment',
        f'Subió el archivo "{attachment.filename}" a la tarea "{task.title}"',
        task=task,
        list_obj=task.list
    )

    return JsonResponse({
        'success': True,
        'attachment': {
            'id': attachment.id,
            'filename': attachment.filename,
            'url': attachment.file.url,
            'uploaded_by': attachment.uploaded_by.username if attachment.uploaded_by else 'Desconocido',
            'uploaded_at': attachment.uploaded_at.strftime('%d/%m/%Y %H:%M:%S'),
        }
    }, status=201)


@login_required
@require_POST
def upload_subtask_attachment(request, subtask_id):
    board_user = get_user_for_board(request.user)
    subtask = get_object_or_404(Subtask, id=subtask_id, task__list__user=board_user)

    attachment_file = request.FILES.get('file')
    if not attachment_file:
        return JsonResponse({'success': False, 'error': 'No se envió ningún archivo.'}, status=400)

    max_size = get_max_attachment_size()
    if attachment_file.size > max_size:
        return JsonResponse({'success': False, 'error': f'El archivo excede el tamaño máximo permitido ({max_size // (1024 * 1024)} MB).'}, status=400)

    attachment = SubtaskAttachment.objects.create(
        subtask=subtask,
        file=attachment_file,
        uploaded_by=request.user
    )

    log_activity(
        request.user,
        'add_attachment',
        f'Subió el archivo "{attachment.filename}" a la subtarea "{subtask.title}"',
        task=subtask.task,
        list_obj=subtask.task.list,
        subtask=subtask
    )

    return JsonResponse({
        'success': True,
        'attachment': {
            'id': attachment.id,
            'filename': attachment.filename,
            'url': attachment.file.url,
            'uploaded_by': attachment.uploaded_by.username if attachment.uploaded_by else 'Desconocido',
            'uploaded_at': attachment.uploaded_at.strftime('%d/%m/%Y %H:%M:%S'),
        }
    }, status=201)


@login_required
@require_POST
def delete_task_attachment(request, attachment_id):
    if not can_delete(request.user):
        return JsonResponse({'success': False, 'error': 'No tienes permisos para eliminar adjuntos.'}, status=403)

    attachment = get_object_or_404(TaskAttachment, id=attachment_id)
    board_user = get_user_for_board(request.user)
    if not (request.user.is_staff or request.user.is_superuser):
        if attachment.task.list.user != board_user:
            return JsonResponse({'success': False, 'error': 'No tienes acceso a este adjunto.'}, status=403)

    # Guardar referencias antes de eliminar
    filename = attachment.filename
    task = attachment.task
    list_obj = task.list

    if attachment.file:
        attachment.file.delete(save=False)
    attachment.delete()

    log_activity(
        request.user,
        'delete_attachment',
        f'Eliminó el archivo "{filename}" de la tarea "{task.title}"',
        task=task,
        list_obj=list_obj
    )

    return JsonResponse({'success': True})


@login_required
@require_POST
def delete_subtask_attachment(request, attachment_id):
    if not can_delete(request.user):
        return JsonResponse({'success': False, 'error': 'No tienes permisos para eliminar adjuntos.'}, status=403)

    attachment = get_object_or_404(SubtaskAttachment, id=attachment_id)
    board_user = get_user_for_board(request.user)
    if not (request.user.is_staff or request.user.is_superuser):
        if attachment.subtask.task.list.user != board_user:
            return JsonResponse({'success': False, 'error': 'No tienes acceso a este adjunto.'}, status=403)

    # Guardar referencias antes de eliminar
    filename = attachment.filename
    subtask = attachment.subtask
    task = subtask.task
    list_obj = task.list

    if attachment.file:
        attachment.file.delete(save=False)
    attachment.delete()

    log_activity(
        request.user,
        'delete_attachment',
        f'Eliminó el archivo "{filename}" de la subtarea "{subtask.title}"',
        task=task,
        list_obj=list_obj,
        subtask=subtask
    )

    return JsonResponse({'success': True})

