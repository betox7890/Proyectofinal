from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


def default_due_date():
    return timezone.now().date() + timedelta(days=60)


class List(models.Model):
    """Modelo para las columnas del tablero Kanban"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    order = models.IntegerField(default=0, verbose_name="Orden")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lists', verbose_name="Usuario")
    color = models.CharField(max_length=50, default='yellow', verbose_name="Color")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_lists', verbose_name="Creado por")

    class Meta:
        verbose_name = "Lista"
        verbose_name_plural = "Listas"
        ordering = ['order']

    def __str__(self):
        return self.name


class Task(models.Model):
    """Modelo para las tareas/tarjetas del tablero Kanban"""
    title = models.CharField(max_length=200, verbose_name="Título")
    list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='tasks', verbose_name="Lista")
    order = models.IntegerField(default=0, verbose_name="Orden")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tasks', verbose_name="Creado por")
    due_date = models.DateField(default=default_due_date, verbose_name="Fecha de vencimiento")
    reminder_sent = models.BooleanField(default=False, verbose_name="Recordatorio enviado")

    class Meta:
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"
        ordering = ['order']

    def __str__(self):
        return self.title


class Subtask(models.Model):
    """Modelo para las subtareas de una tarea"""
    title = models.CharField(max_length=200, verbose_name="Título")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks', verbose_name="Tarea")
    completed = models.BooleanField(default=False, verbose_name="Completada")
    order = models.IntegerField(default=0, verbose_name="Orden")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_subtasks', verbose_name="Creado por")
    due_date = models.DateField(default=default_due_date, verbose_name="Fecha de vencimiento")

    class Meta:
        verbose_name = "Subtarea"
        verbose_name_plural = "Subtareas"
        ordering = ['order']

    def __str__(self):
        return self.title


class Invitation(models.Model):
    """Modelo para las invitaciones de estudiantes a tableros compartidos"""
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations', verbose_name="Administrador")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations', verbose_name="Estudiante")
    accepted = models.BooleanField(default=False, verbose_name="Aceptada")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Invitación"
        verbose_name_plural = "Invitaciones"
        unique_together = ['admin', 'student']
        ordering = ['-created_at']

    def __str__(self):
        status = "Aceptada" if self.accepted else "Pendiente"
        return f"{self.admin.username} -> {self.student.username} ({status})"


class Activity(models.Model):
    """Modelo para registrar las actividades de los usuarios invitados en el tablero compartido"""
    ACTIVITY_TYPES = [
        ('create_task', 'Crear Tarea'),
        ('edit_task', 'Editar Tarea'),
        ('delete_task', 'Eliminar/Cerrar Tarea'),
        ('move_task', 'Mover Tarea'),
        ('create_list', 'Crear Lista'),
        ('create_subtask', 'Crear Subtarea'),
        ('edit_subtask', 'Editar Subtarea'),
        ('toggle_subtask', 'Completar/Descompletar Subtarea'),
        ('delete_subtask', 'Eliminar Subtarea'),
        ('add_attachment', 'Adjuntar archivo'),
        ('delete_attachment', 'Eliminar archivo'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', verbose_name="Usuario")
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES, verbose_name="Tipo de Actividad")
    description = models.CharField(max_length=500, verbose_name="Descripción")
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities', verbose_name="Tarea")
    list = models.ForeignKey(List, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities', verbose_name="Lista")
    subtask = models.ForeignKey(Subtask, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities', verbose_name="Subtarea")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.description}"

    @property
    def related_creator(self):
        if self.task and self.task.created_by:
            return self.task.created_by
        if self.subtask and self.subtask.created_by:
            return self.subtask.created_by
        if self.list and self.list.created_by:
            return self.list.created_by
        return None


class ActivityComment(models.Model):
    """Comentarios hechos por administradores sobre actividades registradas"""
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='comments', verbose_name="Actividad")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_comments', verbose_name="Autor")
    comment = models.TextField(verbose_name="Comentario")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Comentario de Actividad"
        verbose_name_plural = "Comentarios de Actividades"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username}: {self.comment[:40]}"


class TwoFactorProfile(models.Model):
    """Configuración de autenticación de dos factores basada en TOTP"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor_profile', verbose_name="Usuario")
    secret = models.CharField(max_length=32, blank=True, verbose_name="Secreto TOTP")
    enabled = models.BooleanField(default=False, verbose_name="2FA habilitado")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Perfil 2FA"
        verbose_name_plural = "Perfiles 2FA"

    def __str__(self):
        return f"2FA - {self.user.username} ({'Activo' if self.enabled else 'Inactivo'})"


def attachment_upload_path(instance, filename):
    if hasattr(instance, 'task') and instance.task_id:
        return f'attachments/tasks/{instance.task_id}/{filename}'
    if hasattr(instance, 'subtask') and instance.subtask_id:
        return f'attachments/subtasks/{instance.subtask_id}/{filename}'
    return f'attachments/others/{filename}'


class TaskAttachment(models.Model):
    """Archivos adjuntos a una tarea"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments', verbose_name="Tarea")
    file = models.FileField(upload_to=attachment_upload_path, verbose_name="Archivo")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='task_attachments', verbose_name="Subido por")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de subida")

    class Meta:
        verbose_name = "Adjunto de Tarea"
        verbose_name_plural = "Adjuntos de Tareas"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.task.title} - {self.file.name}"

    @property
    def filename(self):
        return self.file.name.split('/')[-1]


class SubtaskAttachment(models.Model):
    """Archivos adjuntos a una subtarea"""
    subtask = models.ForeignKey(Subtask, on_delete=models.CASCADE, related_name='attachments', verbose_name="Subtarea")
    file = models.FileField(upload_to=attachment_upload_path, verbose_name="Archivo")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='subtask_attachments', verbose_name="Subido por")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de subida")

    class Meta:
        verbose_name = "Adjunto de Subtarea"
        verbose_name_plural = "Adjuntos de Subtareas"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.subtask.title} - {self.file.name}"

    @property
    def filename(self):
        return self.file.name.split('/')[-1]


class BoardPreference(models.Model):
    """Preferencias visuales del tablero para cada usuario"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='board_preference', verbose_name="Usuario")
    color = models.CharField(max_length=20, default='transparent', verbose_name="Color del tablero")
    background_image = models.ImageField(upload_to='board_backgrounds/', null=True, blank=True, verbose_name="Imagen de fondo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Preferencia de Tablero"
        verbose_name_plural = "Preferencias de Tableros"

    def __str__(self):
        return f"{self.user.username} - {self.color}"

