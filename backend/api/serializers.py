from rest_framework import serializers
from django.contrib.auth.models import User
from .models import List, Task, Subtask, Activity, ActivityComment, Invitation, BoardPreference, TaskAttachment, SubtaskAttachment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'is_staff', 'is_superuser']


class SubtaskAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    filename = serializers.CharField(read_only=True)
    
    class Meta:
        model = SubtaskAttachment
        fields = ['id', 'file', 'filename', 'uploaded_by', 'uploaded_by_username', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class TaskAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    filename = serializers.CharField(read_only=True)
    
    class Meta:
        model = TaskAttachment
        fields = ['id', 'file', 'filename', 'uploaded_by', 'uploaded_by_username', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class SubtaskSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    attachments = SubtaskAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Subtask
        fields = ['id', 'title', 'task', 'completed', 'order', 'created_by', 'created_by_username', 'due_date', 'attachments']
        read_only_fields = ['id']


class TaskSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    list_name = serializers.CharField(source='list.name', read_only=True)
    subtasks = SubtaskSerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'list', 'list_name', 'order', 'created_by', 'created_by_username', 'due_date', 'reminder_sent', 'subtasks', 'attachments']
        read_only_fields = ['id', 'reminder_sent']


class ListSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)
    filtered_tasks = serializers.SerializerMethodField()
    task_count = serializers.IntegerField(source='tasks.count', read_only=True)
    
    class Meta:
        model = List
        fields = ['id', 'name', 'order', 'color', 'user', 'created_by', 'created_by_username', 'tasks', 'filtered_tasks', 'task_count']
        read_only_fields = ['id']
    
    def get_filtered_tasks(self, obj):
        # Si hay filtered_tasks (de Prefetch), usarlos; si no, usar tasks normales
        if hasattr(obj, 'filtered_tasks'):
            return TaskSerializer(obj.filtered_tasks, many=True).data
        return TaskSerializer(obj.tasks.all(), many=True).data


class ActivityCommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = ActivityComment
        fields = ['id', 'comment', 'author', 'author_username', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']


class ActivitySerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    subtask_title = serializers.CharField(source='subtask.title', read_only=True)
    list_name = serializers.CharField(source='list.name', read_only=True)
    comments = ActivityCommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Activity
        fields = ['id', 'user', 'user_username', 'activity_type', 'activity_type_display', 'description', 
                  'task', 'task_title', 'subtask', 'subtask_title', 'list', 'list_name', 'created_at', 'comments']
        read_only_fields = ['id', 'created_at']


class InvitationSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(source='admin.username', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    
    class Meta:
        model = Invitation
        fields = ['id', 'admin', 'admin_username', 'student', 'student_username', 'accepted', 'created_at']
        read_only_fields = ['id', 'created_at']


class BoardPreferenceSerializer(serializers.ModelSerializer):
    background_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BoardPreference
        fields = ['id', 'color', 'background_image', 'background_image_url', 'updated_at']
        read_only_fields = ['id', 'updated_at']
    
    def get_background_image_url(self, obj):
        if obj.background_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.background_image.url)
            return obj.background_image.url
        return None

