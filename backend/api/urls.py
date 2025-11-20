from django.urls import path
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from . import views

app_name = 'api'

def root_redirect(request):
    """Redirige a login o board según si el usuario está autenticado"""
    if request.user.is_authenticated:
        return redirect('api:board')
    return redirect('api:login')

urlpatterns = [
    path('', root_redirect, name='root'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('board/', views.board_view, name='board'),
    path('logs/', views.system_logs_view, name='system_logs'),
    path('add-task/', views.add_task, name='add_task'),
    path('add-list/', views.add_list, name='add_list'),
    path('update-task/<int:task_id>/', views.update_task, name='update_task'),
    path('delete-task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('delete-list/<int:list_id>/', views.delete_list, name='delete_list'),
    path('change-list-color/<int:list_id>/', views.change_list_color, name='change_list_color'),
    path('move-task/<int:task_id>/', views.move_task, name='move_task'),
    path('add-subtask/<int:task_id>/', views.add_subtask, name='add_subtask'),
    path('update-subtask/<int:subtask_id>/', views.update_subtask, name='update_subtask'),
    path('delete-subtask/<int:subtask_id>/', views.delete_subtask, name='delete_subtask'),
    path('toggle-subtask/<int:subtask_id>/', views.toggle_subtask, name='toggle_subtask'),
    path('tasks/<int:task_id>/attachments/', views.upload_task_attachment, name='upload_task_attachment'),
    path('subtasks/<int:subtask_id>/attachments/', views.upload_subtask_attachment, name='upload_subtask_attachment'),
    path('attachments/task/<int:attachment_id>/delete/', views.delete_task_attachment, name='delete_task_attachment'),
    path('attachments/subtask/<int:attachment_id>/delete/', views.delete_subtask_attachment, name='delete_subtask_attachment'),
    path('reorder-tasks/', views.reorder_tasks, name='reorder_tasks'),
    path('reorder-subtasks/', views.reorder_subtasks, name='reorder_subtasks'),
    path('reorder-lists/', views.reorder_lists, name='reorder_lists'),
    path('invite-student/', views.invite_student, name='invite_student'),
    path('accept-invitation/<int:invitation_id>/', views.accept_invitation, name='accept_invitation'),
    path('reject-invitation/<int:invitation_id>/', views.reject_invitation, name='reject_invitation'),
    path('create-user/', views.create_user, name='create_user'),
    path('get-activities/', views.get_activities, name='get_activities'),
    path('activities/<int:activity_id>/comments/', views.add_activity_comment, name='add_activity_comment'),
    path('change-board-color/', views.change_board_color, name='change_board_color'),
    path('upload-board-background/', views.upload_board_background, name='upload_board_background'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/send-reminders/', views.send_calendar_reminders, name='send_calendar_reminders'),
    path('two-factor/setup/', views.two_factor_setup, name='two_factor_setup'),
    # API endpoints para React
    path('api/user/', views.api_get_current_user, name='api_get_current_user'),
    path('api/board-users-for-reminders/', views.api_board_users_for_reminders, name='api_board_users_for_reminders'),
]

