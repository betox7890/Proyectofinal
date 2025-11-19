import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Task, Subtask

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
