from django.contrib import admin
from .models import List, Task, Subtask, Invitation, Activity, BoardPreference


@admin.register(List)
class ListAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'order', 'color', 'created_by')
    list_filter = ('user', 'color', 'created_by')
    search_fields = ('name', 'user__username', 'created_by__username')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'list', 'order', 'created_by', 'due_date')
    list_filter = ('list', 'created_by', 'due_date')
    search_fields = ('title', 'list__name', 'created_by__username')


@admin.register(Subtask)
class SubtaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'completed', 'order', 'created_by', 'due_date')
    list_filter = ('completed', 'task', 'created_by', 'due_date')
    search_fields = ('title', 'task__title', 'created_by__username')


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('admin', 'student', 'accepted', 'created_at')
    list_filter = ('accepted', 'created_at')
    search_fields = ('admin__username', 'student__username')


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'description', 'get_creator', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'description', 'task__title', 'subtask__title', 'list__name')
    readonly_fields = ('created_at',)

    @admin.display(description='Creado por')
    def get_creator(self, obj):
        creator = obj.related_creator
        return creator.username if creator else '-'


@admin.register(BoardPreference)
class BoardPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'color', 'has_background_image', 'updated_at')
    search_fields = ('user__username', 'color')
    list_filter = ('updated_at',)

    @admin.display(description='Imagen cargada', boolean=True)
    def has_background_image(self, obj):
        return bool(obj.background_image)

