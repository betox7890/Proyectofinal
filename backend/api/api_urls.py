from django.urls import path
from . import api_views

app_name = 'api'

urlpatterns = [
    # Autenticación
    path('user/', api_views.api_user, name='user'),
    path('login/', api_views.api_login, name='login'),
    
    # Tablero
    path('board/', api_views.api_board, name='board'),
    
    # Listas
    path('lists/', api_views.api_create_list, name='create_list'),
    path('lists/<int:list_id>/delete/', api_views.api_delete_list, name='delete_list'),
    path('lists/<int:list_id>/color/', api_views.api_change_list_color, name='change_list_color'),
    
    # Tareas
    path('tasks/', api_views.api_create_task, name='create_task'),
    path('tasks/<int:task_id>/', api_views.api_update_task, name='update_task'),
    path('tasks/<int:task_id>/delete/', api_views.api_delete_task, name='delete_task'),
    path('tasks/<int:task_id>/move/', api_views.api_move_task, name='move_task'),
    
    # Subtareas
    path('tasks/<int:task_id>/subtasks/', api_views.api_create_subtask, name='create_subtask'),
    path('subtasks/<int:subtask_id>/', api_views.api_update_subtask, name='update_subtask'),
    path('subtasks/<int:subtask_id>/delete/', api_views.api_delete_subtask, name='delete_subtask'),
    path('subtasks/<int:subtask_id>/toggle/', api_views.api_toggle_subtask, name='toggle_subtask'),
    
    # Actividades
    path('activities/', api_views.api_activities, name='activities'),
    
    # Calendario
    path('calendar/', api_views.api_calendar, name='calendar'),
    
    # Reordenamiento
    path('reorder-lists/', api_views.api_reorder_lists, name='reorder_lists'),
    path('reorder-tasks/', api_views.api_reorder_tasks, name='reorder_tasks'),
    path('reorder-subtasks/', api_views.api_reorder_subtasks, name='reorder_subtasks'),
    
    # Adjuntos
    path('tasks/<int:task_id>/attachments/', api_views.api_upload_task_attachment, name='upload_task_attachment'),
    path('subtasks/<int:subtask_id>/attachments/', api_views.api_upload_subtask_attachment, name='upload_subtask_attachment'),
    path('tasks/attachments/<int:attachment_id>/delete/', api_views.api_delete_task_attachment, name='delete_task_attachment'),
    path('subtasks/attachments/<int:attachment_id>/delete/', api_views.api_delete_subtask_attachment, name='delete_subtask_attachment'),
    
    # Invitaciones
    path('invite-student/', api_views.api_invite_student, name='invite_student'),
    path('accept-invitation/<int:invitation_id>/', api_views.api_accept_invitation, name='accept_invitation'),
    path('reject-invitation/<int:invitation_id>/', api_views.api_reject_invitation, name='reject_invitation'),
    
    # Configuración del tablero
    path('change-board-color/', api_views.api_change_board_color, name='change_board_color'),
    path('upload-board-background/', api_views.api_upload_board_background, name='upload_board_background'),
    
    # Usuarios
    path('create-user/', api_views.api_create_user, name='create_user'),
    
    # Comentarios de actividades
    path('add-activity-comment/<int:activity_id>/', api_views.api_add_activity_comment, name='add_activity_comment'),
    
    # System Logs
    path('system-logs/', api_views.api_system_logs, name='system_logs'),
    
    # 2FA Setup
    path('two-factor-setup/', api_views.api_two_factor_setup, name='two_factor_setup'),
    
    # Recordatorios
    path('send-board-reminders/', api_views.api_send_board_reminders, name='send_board_reminders'),
    path('board-users-for-reminders/', api_views.api_get_board_users_for_reminders, name='get_board_users_for_reminders'),
]

