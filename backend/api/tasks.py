import logging
from datetime import timedelta
from collections import defaultdict

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Q

from .models import Task, Subtask, Invitation, List
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


@shared_task
def send_due_date_reminders():
    """
    Envía recordatorios por correo electrónico para tareas y subtareas que están próximas a vencer.
    Considera tareas que vencen en 1, 3 y 7 días.
    """
    today = timezone.now().date()
    reminders_sent = 0
    errors = 0

    # Tareas próximas a vencer (1, 3 y 7 días)
    days_ahead = [1, 3, 7]
    
    for days in days_ahead:
        target_date = today + timedelta(days=days)
        
        # Obtener tareas que vencen en esta fecha y no han recibido recordatorio
        tasks = Task.objects.filter(
            due_date=target_date,
            reminder_sent=False,
        ).select_related('created_by', 'list').prefetch_related('subtasks')

        for task in tasks:
            recipient = None
            if task.created_by and task.created_by.email:
                recipient = task.created_by.email

            if not recipient:
                logger.warning(f"Tarea '{task.title}' no tiene email de destinatario")
                continue

            # Calcular días restantes
            days_remaining = (task.due_date - today).days
            
            # Preparar el asunto según la urgencia
            if days_remaining == 1:
                urgency = "URGENTE"
                subject = f'[URGENTE] Tarea vence mañana: {task.title}'
            elif days_remaining == 3:
                urgency = "Importante"
                subject = f'Recordatorio: Tarea vence en 3 días - {task.title}'
            else:
                urgency = "Recordatorio"
                subject = f'Recordatorio: Tarea vence en {days_remaining} días - {task.title}'

            # Obtener subtareas pendientes relacionadas
            pending_subtasks = task.subtasks.filter(completed=False, due_date__lte=target_date)
            
            # Crear el mensaje
            message_lines = [
                f'Hola {task.created_by.get_full_name() or task.created_by.username},',
                '',
                f'Esta es un recordatorio de que la tarea "{task.title}" vence el {task.due_date.strftime("%d/%m/%Y")}.',
                f'Quedan {days_remaining} día(s) para completarla.',
                '',
            ]
            
            if pending_subtasks.exists():
                message_lines.append('Subtareas pendientes relacionadas:')
                for subtask in pending_subtasks:
                    subtask_due = (subtask.due_date - today).days if subtask.due_date else None
                    if subtask_due is not None:
                        message_lines.append(f'  - {subtask.title} (vence en {subtask_due} día(s))')
                    else:
                        message_lines.append(f'  - {subtask.title}')
                message_lines.append('')
            
            message_lines.extend([
                f'Lista: {task.list.name}',
                '',
                'Por favor, revisa el tablero Kanban para asegurarte de que el trabajo esté en curso.',
                '',
                'Saludos,',
                'Sistema de Gestión Kanban',
            ])
            
            message = '\n'.join(message_lines)

            try:
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
                logger.info(f"Recordatorio enviado a {recipient} para tarea '{task.title}' (vence en {days_remaining} días)")
            except Exception as e:
                errors += 1
                logger.error(f"Error al enviar recordatorio para tarea '{task.title}': {e}", exc_info=True)
                # No marcamos como enviado si hay error; se intentará nuevamente

    # También enviar recordatorios para subtareas que vencen pronto
    for days in days_ahead:
        target_date = today + timedelta(days=days)
        
        subtasks = Subtask.objects.filter(
            due_date=target_date,
            completed=False,
        ).select_related('task', 'task__created_by', 'task__list', 'created_by')

        for subtask in subtasks:
            # Determinar el destinatario (prioridad: creador de subtarea, luego creador de tarea)
            recipient = None
            if subtask.created_by and subtask.created_by.email:
                recipient = subtask.created_by.email
            elif subtask.task.created_by and subtask.task.created_by.email:
                recipient = subtask.task.created_by.email

            if not recipient:
                continue

            days_remaining = (subtask.due_date - today).days
            
            if days_remaining == 1:
                subject = f'[URGENTE] Subtarea vence mañana: {subtask.title}'
            elif days_remaining == 3:
                subject = f'Recordatorio: Subtarea vence en 3 días - {subtask.title}'
            else:
                subject = f'Recordatorio: Subtarea vence en {days_remaining} días - {subtask.title}'

            message_lines = [
                f'Hola {subtask.task.created_by.get_full_name() or subtask.task.created_by.username},',
                '',
                f'Esta es un recordatorio de que la subtarea "{subtask.title}" de la tarea "{subtask.task.title}" vence el {subtask.due_date.strftime("%d/%m/%Y")}.',
                f'Quedan {days_remaining} día(s) para completarla.',
                '',
                f'Tarea: {subtask.task.title}',
                f'Lista: {subtask.task.list.name}',
                '',
                'Por favor, revisa el tablero Kanban para asegurarte de que el trabajo esté en curso.',
                '',
                'Saludos,',
                'Sistema de Gestión Kanban',
            ]
            
            message = '\n'.join(message_lines)

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient],
                    fail_silently=False,
                )
                reminders_sent += 1
                logger.info(f"Recordatorio enviado a {recipient} para subtarea '{subtask.title}' (vence en {days_remaining} días)")
            except Exception as e:
                errors += 1
                logger.error(f"Error al enviar recordatorio para subtarea '{subtask.title}': {e}", exc_info=True)

    logger.info(f"Proceso de recordatorios completado. Enviados: {reminders_sent}, Errores: {errors}")
    return {
        'reminders_sent': reminders_sent,
        'errors': errors
    }


@shared_task
def send_board_reminders_to_all_users(include_overdue=True, include_1_3_days=True, include_4_7_days=False):
    """
    Envía recordatorios por correo electrónico a TODOS los usuarios que tienen acceso al tablero.
    
    Args:
        include_overdue: Si True, incluye tareas y subtareas vencidas
        include_1_3_days: Si True, incluye tareas que vencen en 1-3 días
        include_4_7_days: Si True, incluye tareas que vencen en 4-7 días
    
    Returns:
        dict con estadísticas del envío
    """
    today = timezone.now().date()
    emails_sent = 0
    errors = 0
    
    # Obtener todos los usuarios que tienen acceso al tablero
    # 1. Usuarios que tienen listas (administradores)
    users_with_lists = User.objects.filter(lists__isnull=False).distinct()
    
    # 2. Usuarios invitados (estudiantes con invitaciones aceptadas)
    invited_users = User.objects.filter(
        received_invitations__accepted=True
    ).distinct()
    
    # 3. Administradores que han invitado (para incluir sus tableros)
    admin_users = User.objects.filter(
        sent_invitations__accepted=True
    ).distinct()
    
    # Combinar todos los usuarios únicos
    all_board_users = (users_with_lists | invited_users | admin_users).distinct()
    
    logger.info(f"Encontrados {all_board_users.count()} usuarios con acceso al tablero")
    
    for user in all_board_users:
        if not user.email:
            logger.warning(f"Usuario {user.username} no tiene correo electrónico configurado")
            continue
        
        # Obtener todas las tareas y subtareas relacionadas con este usuario
        user_tasks = []
        user_subtasks = []
        
        # Tareas creadas por el usuario
        tasks_created = Task.objects.filter(created_by=user).select_related('list', 'created_by')
        
        # Tareas en listas del usuario (si es administrador)
        tasks_in_user_lists = Task.objects.filter(list__user=user).select_related('list', 'created_by')
        
        # Tareas en listas de administradores que invitaron al usuario (si es estudiante invitado)
        if Invitation.objects.filter(student=user, accepted=True).exists():
            admin_ids = Invitation.objects.filter(
                student=user, accepted=True
            ).values_list('admin_id', flat=True)
            tasks_from_admins = Task.objects.filter(
                list__user_id__in=admin_ids
            ).select_related('list', 'created_by')
        else:
            tasks_from_admins = Task.objects.none()
        
        # Combinar todas las tareas
        all_user_tasks = (tasks_created | tasks_in_user_lists | tasks_from_admins).distinct()
        
        # Subtareas creadas por el usuario
        subtasks_created = Subtask.objects.filter(created_by=user).select_related('task', 'task__list', 'task__created_by')
        
        # Subtareas de tareas relacionadas con el usuario
        subtasks_from_user_tasks = Subtask.objects.filter(
            task__in=all_user_tasks
        ).select_related('task', 'task__list', 'task__created_by')
        
        all_user_subtasks = (subtasks_created | subtasks_from_user_tasks).distinct()
        
        # Clasificar tareas y subtareas por tipo de recordatorio
        overdue_tasks = []
        tasks_1_3_days = []
        tasks_4_7_days = []
        overdue_subtasks = []
        subtasks_1_3_days = []
        subtasks_4_7_days = []
        
        for task in all_user_tasks:
            if not task.due_date:
                continue
            
            days_remaining = (task.due_date - today).days
            
            if days_remaining < 0 and include_overdue:
                overdue_tasks.append((task, days_remaining))
            elif 1 <= days_remaining <= 3 and include_1_3_days:
                tasks_1_3_days.append((task, days_remaining))
            elif 4 <= days_remaining <= 7 and include_4_7_days:
                tasks_4_7_days.append((task, days_remaining))
        
        for subtask in all_user_subtasks:
            if not subtask.due_date or subtask.completed:
                continue
            
            days_remaining = (subtask.due_date - today).days
            
            if days_remaining < 0 and include_overdue:
                overdue_subtasks.append((subtask, days_remaining))
            elif 1 <= days_remaining <= 3 and include_1_3_days:
                subtasks_1_3_days.append((subtask, days_remaining))
            elif 4 <= days_remaining <= 7 and include_4_7_days:
                subtasks_4_7_days.append((subtask, days_remaining))
        
        # Si no hay nada que enviar, continuar con el siguiente usuario
        total_items = (len(overdue_tasks) + len(tasks_1_3_days) + len(tasks_4_7_days) +
                      len(overdue_subtasks) + len(subtasks_1_3_days) + len(subtasks_4_7_days))
        
        if total_items == 0:
            continue
        
        # Construir el mensaje de correo
        subject = "Recordatorios de Tareas - Tablero Kanban"
        if len(overdue_tasks) > 0 or len(overdue_subtasks) > 0:
            subject = "[URGENTE] " + subject
        
        message_lines = [
            f'Hola {user.get_full_name() or user.username},',
            '',
            'Este es un resumen de tus tareas y subtareas en el tablero Kanban:',
            '',
        ]
        
        # Tareas vencidas
        if overdue_tasks or overdue_subtasks:
            message_lines.append('[URGENTE] TAREAS Y SUBTAREAS VENCIDAS:')
            message_lines.append('')
            
            for task, days_overdue in overdue_tasks:
                message_lines.append(f'  - Tarea: "{task.title}"')
                message_lines.append(f'    Lista: {task.list.name}')
                message_lines.append(f'    Vencida hace {abs(days_overdue)} dia(s)')
                message_lines.append('')
            
            for subtask, days_overdue in overdue_subtasks:
                message_lines.append(f'  - Subtarea: "{subtask.title}"')
                message_lines.append(f'    Tarea: "{subtask.task.title}"')
                message_lines.append(f'    Lista: {subtask.task.list.name}')
                message_lines.append(f'    Vencida hace {abs(days_overdue)} dia(s)')
                message_lines.append('')
        
        # Tareas que vencen en 1-3 días
        if tasks_1_3_days or subtasks_1_3_days:
            message_lines.append('TAREAS Y SUBTAREAS QUE VENCEN EN 1-3 DIAS:')
            message_lines.append('')
            
            for task, days_remaining in tasks_1_3_days:
                message_lines.append(f'  - Tarea: "{task.title}"')
                message_lines.append(f'    Lista: {task.list.name}')
                message_lines.append(f'    Vence en {days_remaining} dia(s) ({task.due_date.strftime("%d/%m/%Y")})')
                message_lines.append('')
            
            for subtask, days_remaining in subtasks_1_3_days:
                message_lines.append(f'  - Subtarea: "{subtask.title}"')
                message_lines.append(f'    Tarea: "{subtask.task.title}"')
                message_lines.append(f'    Lista: {subtask.task.list.name}')
                message_lines.append(f'    Vence en {days_remaining} dia(s) ({subtask.due_date.strftime("%d/%m/%Y")})')
                message_lines.append('')
        
        # Tareas que vencen en 4-7 días
        if tasks_4_7_days or subtasks_4_7_days:
            message_lines.append('TAREAS Y SUBTAREAS QUE VENCEN EN 4-7 DIAS:')
            message_lines.append('')
            
            for task, days_remaining in tasks_4_7_days:
                message_lines.append(f'  - Tarea: "{task.title}"')
                message_lines.append(f'    Lista: {task.list.name}')
                message_lines.append(f'    Vence en {days_remaining} dia(s) ({task.due_date.strftime("%d/%m/%Y")})')
                message_lines.append('')
            
            for subtask, days_remaining in subtasks_4_7_days:
                message_lines.append(f'  - Subtarea: "{subtask.title}"')
                message_lines.append(f'    Tarea: "{subtask.task.title}"')
                message_lines.append(f'    Lista: {subtask.task.list.name}')
                message_lines.append(f'    Vence en {days_remaining} dia(s) ({subtask.due_date.strftime("%d/%m/%Y")})')
                message_lines.append('')
        
        message_lines.extend([
            '',
            'Por favor, revisa el tablero Kanban para asegurarte de que el trabajo esté en curso.',
            '',
            'Saludos,',
            'Sistema de Gestión Kanban',
        ])
        
        message = '\n'.join(message_lines)
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            emails_sent += 1
            logger.info(f"Recordatorio enviado a {user.email} ({user.username}) con {total_items} elementos")
        except Exception as e:
            errors += 1
            logger.error(f"Error al enviar recordatorio a {user.email} ({user.username}): {e}", exc_info=True)
    
    logger.info(f"Proceso de recordatorios masivos completado. Enviados: {emails_sent}, Errores: {errors}")
    return {
        'emails_sent': emails_sent,
        'errors': errors,
        'users_processed': all_board_users.count()
    }
