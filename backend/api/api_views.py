from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Max, Prefetch, Q
from django.utils import timezone
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.http import HttpResponse
from datetime import datetime, timedelta
import json

from .models import List, Task, Subtask, Activity, ActivityComment, Invitation, BoardPreference, TaskAttachment, SubtaskAttachment, TwoFactorProfile
from .serializers import (
    ListSerializer, TaskSerializer, SubtaskSerializer, ActivitySerializer,
    InvitationSerializer, BoardPreferenceSerializer, UserSerializer
)
from .views import (
    get_user_for_board, can_delete, get_board_preference, ensure_default_lists,
    log_activity, get_pending_2fa_user, clear_pending_2fa_session, login_with_backend,
    get_two_factor_profile
)
from .tasks import send_board_reminders_to_all_users

import logging
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_user(request):
    """Endpoint API para obtener información del usuario actual"""
    if request.user.is_authenticated:
        return Response({
            'authenticated': True,
            'user': UserSerializer(request.user).data
        })
    else:
        return Response({
            'authenticated': False,
            'user': None
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """
    Endpoint API para login - Replica EXACTAMENTE el flujo del backend tradicional
    Basado en kanban/views.py login_view (líneas 244-310)
    """
    # Forzar creación de sesión si no existe (necesario para API)
    if not request.session.session_key:
        request.session.create()
        logger.info(f"=== LOGIN API - Nueva sesión creada ===")
    
    # Log para depuración
    logger.info(f"=== LOGIN API ===")
    logger.info(f"Step: {request.data.get('step', 'password')}")
    logger.info(f"Session key: {request.session.session_key}")
    logger.info(f"Cookies recibidas: {list(request.COOKIES.keys())}")
    logger.info(f"Session data keys: {list(request.session.keys())}")
    logger.info(f"Cookie sessionid recibida: {'sessionid' in request.COOKIES}")
    
    if request.user.is_authenticated:
        return Response({
            'success': True,
            'message': 'Ya estás autenticado',
            'user': UserSerializer(request.user).data
        })
    
    # Obtener step - igual que en el backend tradicional (línea 254)
    step = request.data.get('step', 'password')
    
    if step == 'totp':
        # Paso 2FA - EXACTAMENTE como en login_view (líneas 256-280)
        logger.info(f"2FA step - Buscando pending_user en sesión")
        logger.info(f"Session keys antes de get_pending_2fa_user: {list(request.session.keys())}")
        
        pending_user = get_pending_2fa_user(request)
        backend = request.session.get('pending_2fa_backend')
        username = request.session.get('pending_2fa_username', '')
        
        # Si no hay sesión, intentar obtener username del request (respaldo desde frontend)
        if not pending_user:
            username_from_request = request.data.get('username', '').strip()
            logger.info(f"2FA step - No hay pending_user en sesión. Username del request: {username_from_request}")
            
            if username_from_request:
                try:
                    from django.contrib.auth.models import User
                    user_by_username = User.objects.get(username=username_from_request)
                    logger.info(f"2FA step - Usuario encontrado en BD: {user_by_username.username}")
                    
                    # Verificar que el usuario tenga 2FA habilitado
                    profile = TwoFactorProfile.objects.filter(user=user_by_username, enabled=True).first()
                    logger.info(f"2FA step - Profile encontrado: {profile is not None}, enabled: {profile.enabled if profile else False}")
                    
                    if profile and profile.enabled:
                        pending_user = user_by_username
                        backend = 'django.contrib.auth.backends.ModelBackend'
                        username = username_from_request
                        # Guardar en sesión para futuras peticiones
                        request.session['pending_2fa_user'] = pending_user.id
                        request.session['pending_2fa_backend'] = backend
                        request.session['pending_2fa_username'] = username
                        request.session.modified = True
                        logger.info(f"2FA step - ✅ Usuario encontrado por username, sesión restaurada. pending_user_id: {pending_user.id}")
                    else:
                        logger.warning(f"2FA step - Usuario encontrado pero no tiene 2FA habilitado")
                except User.DoesNotExist:
                    logger.warning(f"2FA step - Usuario no existe en BD: {username_from_request}")
                except Exception as e:
                    logger.error(f"2FA step - Error al buscar usuario: {e}")
        
        logger.info(f"2FA step - pending_user: {pending_user}, backend: {backend}, username: {username}")
        
        if not pending_user:
            logger.warning(f"2FA step - ❌ No se encontró pending_user. Session keys: {list(request.session.keys())}")
            clear_pending_2fa_session(request)
            return Response({
                'success': False,
                'error': 'La sesión de verificación expiró. Ingresa tus credenciales nuevamente.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Usar get_two_factor_profile igual que en el backend (línea 265)
        profile = get_two_factor_profile(pending_user)
        
        if not profile.enabled or not profile.secret:
            login_with_backend(request, pending_user, backend)
            clear_pending_2fa_session(request)
            return Response({
                'success': True,
                'message': 'Login exitoso',
                'user': UserSerializer(pending_user).data
            })
        
        # Limpiar código completamente - asegurar que sea string
        code_raw = request.data.get('code', '')
        if code_raw is None:
            code_raw = ''
        
        # Convertir a string y limpiar
        code = str(code_raw).strip()
        # Eliminar todos los caracteres no numéricos
        code = ''.join(c for c in code if c.isdigit())
        code = code[:6]  # Limitar a 6 dígitos
        
        logger.info(f"2FA step - Código recibido (raw): {repr(code_raw)}, tipo: {type(code_raw)}")
        logger.info(f"2FA step - Código limpiado: {code}, longitud: {len(code)}")
        
        if not code or len(code) != 6:
            logger.warning(f"2FA step - Código inválido: longitud={len(code) if code else 0}")
            return Response({
                'success': False,
                'error': 'El código debe tener 6 dígitos',
                'requires_2fa': True
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que sea solo números
        if not code.isdigit():
            logger.warning(f"2FA step - Código contiene caracteres no numéricos: {code}")
            return Response({
                'success': False,
                'error': 'El código debe contener solo números',
                'requires_2fa': True
            }, status=status.HTTP_400_BAD_REQUEST)
        
        import pyotp
        import time
        from django.utils import timezone as django_timezone
        
        # Obtener tiempo actual del servidor
        server_time = time.time()
        server_datetime = django_timezone.now()
        
        logger.info(f"2FA step - Tiempo del servidor: {server_datetime}, timestamp: {server_time}")
        logger.info(f"2FA step - Validando código. Código recibido: {code}, Secret presente: {bool(profile.secret)}")
        
        totp = pyotp.TOTP(profile.secret)
        
        # Obtener código actual para comparación
        current_code = totp.now()
        logger.info(f"2FA step - Código actual esperado: {current_code}")
        
        # Validar con ventana de tiempo para permitir desfases de reloj
        # valid_window=1 significa que acepta códigos de -1 a +1 períodos (30 segundos antes o después)
        # Esto es necesario para React y sistemas con posibles desfases de tiempo
        if totp.verify(code, valid_window=1):
            logger.info(f"2FA step - Código válido, iniciando sesión")
            login_with_backend(request, pending_user, backend)
            clear_pending_2fa_session(request)
            
            # IMPORTANTE: Guardar la sesión después del login para asegurar que session_key esté disponible
            request.session.save()
            logger.info(f"2FA step - Sesión guardada después del login. Session key: {request.session.session_key}")
            
            # Asegurar que la cookie de sesión se envíe también en login exitoso con 2FA
            response = Response({
                'success': True,
                'message': 'Login exitoso',
                'user': UserSerializer(pending_user).data
            })
            
            # Enviar cookie de sesión explícitamente
            if request.session.session_key:
                cookie_name = getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')
                cookie_age = getattr(settings, 'SESSION_COOKIE_AGE', 1209600)
                cookie_path = getattr(settings, 'SESSION_COOKIE_PATH', '/')
                cookie_secure = getattr(settings, 'SESSION_COOKIE_SECURE', False)
                cookie_httponly = getattr(settings, 'SESSION_COOKIE_HTTPONLY', True)
                cookie_samesite = getattr(settings, 'SESSION_COOKIE_SAMESITE', 'Lax')
                
                response.set_cookie(
                    cookie_name,
                    request.session.session_key,
                    max_age=cookie_age,
                    domain=None,
                    path=cookie_path,
                    secure=cookie_secure,
                    httponly=cookie_httponly,
                    samesite=cookie_samesite
                )
                logger.info(f"2FA step (login exitoso) - ✅ Cookie enviada: {cookie_name}={request.session.session_key[:20]}...")
            
            return response
        else:
            logger.warning(f"2FA step - Código inválido. Código recibido: {code}")
            # Generar código actual para comparación (solo para logging)
            current_code = totp.now()
            logger.info(f"2FA step - Código actual esperado: {current_code}")
            return Response({
                'success': False,
                'error': 'Código inválido. Intenta nuevamente.',
                'requires_2fa': True
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        # Paso password - EXACTAMENTE como en login_view (líneas 281-301)
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        
        if not username or not password:
            return Response({
                'success': False,
                'error': 'Usuario y contraseña son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            backend = getattr(user, 'backend', 'django.contrib.auth.backends.ModelBackend')
            profile = TwoFactorProfile.objects.filter(user=user, enabled=True).first()
            
            if profile:
                # Guardar en sesión - EXACTAMENTE como en login_view (líneas 291-293)
                request.session['pending_2fa_user'] = user.id
                request.session['pending_2fa_backend'] = backend
                request.session['pending_2fa_username'] = username
                # Marcar sesión como modificada para que Django la guarde
                request.session.modified = True
                # Guardar sesión ANTES de crear la respuesta
                request.session.save()
                
                logger.info(f"Password step - Sesión guardada. Session key: {request.session.session_key}, pending_user_id: {user.id}")
                
                # Crear respuesta y asegurar que la cookie se envíe
                response = Response({
                    'success': False,
                    'error': 'Se requiere verificación en dos pasos',
                    'requires_2fa': True,
                    'username': username
                }, status=status.HTTP_200_OK)
                
                # Asegurar que la cookie de sesión se envíe explícitamente
                # Django REST Framework no maneja automáticamente las cookies de sesión
                # CRÍTICO: La cookie DEBE enviarse para que el frontend pueda mantener la sesión
                if request.session.session_key:
                    cookie_name = getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')
                    cookie_age = getattr(settings, 'SESSION_COOKIE_AGE', 1209600)
                    cookie_path = getattr(settings, 'SESSION_COOKIE_PATH', '/')
                    cookie_secure = getattr(settings, 'SESSION_COOKIE_SECURE', False)
                    cookie_httponly = getattr(settings, 'SESSION_COOKIE_HTTPONLY', True)
                    cookie_samesite = getattr(settings, 'SESSION_COOKIE_SAMESITE', 'Lax')
                    
                    # Usar el valor configurado en settings.py
                    # Ahora que frontend y backend están en el mismo dominio (vía proxy),
                    # SameSite='Lax' funciona perfectamente
                    
                    # Configurar cookie explícitamente usando el método de Response
                    # Esto es OBLIGATORIO para que la cookie se envíe al frontend
                    response.set_cookie(
                        cookie_name,
                        request.session.session_key,
                        max_age=cookie_age,
                        domain=None,  # No establecer domain para localhost
                        path=cookie_path,
                        secure=cookie_secure,
                        httponly=cookie_httponly,
                        samesite=cookie_samesite
                    )
                    
                    logger.info(f"Password step - ✅ Cookie configurada: {cookie_name}={request.session.session_key[:20]}...")
                    logger.info(f"Password step - Cookie config: samesite={cookie_samesite}, secure={cookie_secure}, httponly={cookie_httponly}, path={cookie_path}, max_age={cookie_age}")
                    
                    # Verificar que la cookie esté en response.cookies
                    if cookie_name in response.cookies:
                        cookie_obj = response.cookies[cookie_name]
                        logger.info(f"Password step - ✅ Cookie en response.cookies: value={cookie_obj.value[:20]}..., samesite={getattr(cookie_obj, 'samesite', 'N/A')}")
                    else:
                        logger.error(f"Password step - ❌ Cookie NO está en response.cookies")
                    
                    # También verificar headers directamente
                    set_cookie_headers = [h for h in response.items() if h[0].lower() == 'set-cookie']
                    if set_cookie_headers:
                        logger.info(f"Password step - ✅ Set-Cookie header presente: {len(set_cookie_headers)} header(s)")
                        for header_name, header_value in set_cookie_headers:
                            logger.info(f"Password step - Set-Cookie header: {header_value[:150]}...")
                    else:
                        logger.warning(f"Password step - ⚠️ Set-Cookie header NO presente en response")
                else:
                    logger.error(f"Password step - ❌ No hay session_key para enviar cookie")
                
                return response
            else:
                # Usuario sin 2FA - hacer login directamente
                clear_pending_2fa_session(request)
                login(request, user, backend=backend)
                
                # Asegurar que la cookie de sesión se envíe también en login exitoso
                response = Response({
                    'success': True,
                    'message': 'Login exitoso',
                    'user': UserSerializer(user).data
                })
                
                # Enviar cookie de sesión explícitamente
                if request.session.session_key:
                    cookie_name = getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')
                    cookie_age = getattr(settings, 'SESSION_COOKIE_AGE', 1209600)
                    cookie_path = getattr(settings, 'SESSION_COOKIE_PATH', '/')
                    cookie_secure = getattr(settings, 'SESSION_COOKIE_SECURE', False)
                    cookie_httponly = getattr(settings, 'SESSION_COOKIE_HTTPONLY', True)
                    cookie_samesite = getattr(settings, 'SESSION_COOKIE_SAMESITE', 'Lax')
                    
                    response.set_cookie(
                        cookie_name,
                        request.session.session_key,
                        max_age=cookie_age,
                        domain=None,
                        path=cookie_path,
                        secure=cookie_secure,
                        httponly=cookie_httponly,
                        samesite=cookie_samesite
                    )
                    logger.info(f"Password step (sin 2FA) - ✅ Cookie enviada: {cookie_name}={request.session.session_key[:20]}...")
                
                return response
        else:
            clear_pending_2fa_session(request)
            return Response({
                'success': False,
                'error': 'Usuario o contraseña incorrectos'
            }, status=status.HTTP_401_UNAUTHORIZED)


# ========== ENDPOINTS DEL TABLERO ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_board(request):
    """Endpoint API para obtener el tablero completo"""
    from django.contrib.auth.models import User
    from django.templatetags.static import static
    from .views import (
        get_user_type, BOARD_COLORS, hex_to_rgba, get_board_color, get_max_attachment_size
    )
    
    is_admin = request.user.is_staff or request.user.is_superuser
    is_invited = False
    board_user = get_user_for_board(request.user)
    
    ensure_default_lists(board_user)
    
    # Filtros
    search_query = request.GET.get('q', '').strip()
    creator_filter = request.GET.get('creator', '').strip()
    due_from = request.GET.get('due_from', '').strip()
    due_to = request.GET.get('due_to', '').strip()
    
    logger.info(f"=== API BOARD - Filtros recibidos ===")
    logger.info(f"q: {search_query}")
    logger.info(f"creator: {creator_filter}")
    logger.info(f"due_from: {due_from}")
    logger.info(f"due_to: {due_to}")
    logger.info(f"request.GET completo: {dict(request.GET)}")
    
    all_task_qs = Task.objects.filter(list__user=board_user)
    task_filters = all_task_qs
    initial_count = task_filters.count()
    logger.info(f"Tareas iniciales (sin filtros): {initial_count}")
    
    if search_query:
        task_filters = task_filters.filter(title__icontains=search_query)
        logger.info(f"Aplicado filtro de búsqueda: '{search_query}' - Tareas después: {task_filters.count()}")
    
    if creator_filter:
        if creator_filter == 'none':
            task_filters = task_filters.filter(created_by__isnull=True)
            logger.info(f"Aplicado filtro de creador: 'none' - Tareas después: {task_filters.count()}")
        else:
            try:
                creator_id = int(creator_filter)
                task_filters = task_filters.filter(created_by_id=creator_id)
                logger.info(f"Aplicado filtro de creador: ID {creator_id} - Tareas después: {task_filters.count()}")
            except ValueError:
                logger.warning(f"Valor inválido para creator_filter: {creator_filter}")
    
    if due_from:
        try:
            due_from_date = datetime.strptime(due_from, '%Y-%m-%d').date()
            task_filters = task_filters.filter(due_date__gte=due_from_date)
            logger.info(f"Aplicado filtro due_from: {due_from_date} - Tareas después: {task_filters.count()}")
        except ValueError:
            logger.warning(f"Fecha inválida para due_from: {due_from}")
    
    if due_to:
        try:
            due_to_date = datetime.strptime(due_to, '%Y-%m-%d').date()
            task_filters = task_filters.filter(due_date__lte=due_to_date)
            logger.info(f"Aplicado filtro due_to: {due_to_date} - Tareas después: {task_filters.count()}")
        except ValueError:
            logger.warning(f"Fecha inválida para due_to: {due_to}")
    
    final_count = task_filters.count()
    logger.info(f"Tareas finales (con filtros): {final_count}")
    
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
    
    lists = List.objects.filter(user=board_user).select_related('created_by').prefetch_related(prefetch_tasks).order_by('order')
    
    board_color = get_board_color(board_user)
    board_overlay_color = hex_to_rgba(board_color)
    preference = get_board_preference(board_user)
    if preference.background_image:
        board_background_image = request.build_absolute_uri(preference.background_image.url)
    else:
        board_background_image = request.build_absolute_uri(static('kanban/img/board-bg.jpg'))
    
    total_filtered_tasks = sum(len(getattr(lst, 'filtered_tasks', [])) for lst in lists)
    
    creator_ids = all_task_qs.exclude(created_by__isnull=True).values_list('created_by', flat=True).distinct()
    creators = User.objects.filter(id__in=creator_ids).order_by('username')
    
    # Invitaciones
    pending_invitations = Invitation.objects.none()
    students = User.objects.none()
    activities = Activity.objects.none()
    can_view_activities = False
    activities_heading = 'Actividades recientes'
    
    if is_admin:
        invited_student_ids = Invitation.objects.filter(admin=request.user).values_list('student_id', flat=True)
        students = User.objects.filter(is_staff=False, is_superuser=False).exclude(id__in=invited_student_ids)
        pending_invitations = Invitation.objects.filter(admin=request.user, accepted=False)
        invited_students = Invitation.objects.filter(admin=request.user, accepted=True).values_list('student_id', flat=True)
        comment_prefetch = Prefetch(
            'comments',
            queryset=ActivityComment.objects.select_related('author').order_by('created_at')
        )
        activities = Activity.objects.filter(
            Q(user_id__in=invited_students) | Q(user=request.user)
        ).select_related(
            'user',
            'task__created_by',
            'task__list',
            'list__created_by',
            'subtask__created_by',
            'subtask__task'
        ).prefetch_related(comment_prefetch).order_by('-created_at')[:100]
        can_view_activities = True
        activities_heading = 'Actividades de usuarios invitados'
    else:
        is_invited = Invitation.objects.filter(student=request.user, accepted=True).exists()
        if is_invited:
            comment_prefetch = Prefetch(
                'comments',
                queryset=ActivityComment.objects.select_related('author').order_by('created_at')
            )
            activities = Activity.objects.filter(user=request.user).select_related(
                'user',
                'task__created_by',
                'task__list',
                'list__created_by',
                'subtask__created_by',
                'subtask__task'
            ).prefetch_related(comment_prefetch).order_by('-created_at')[:100]
            can_view_activities = True
            activities_heading = 'Mis actividades'
        pending_invitations = Invitation.objects.filter(student=request.user, accepted=False)
    
    try:
        tf_profile = request.user.two_factor_profile
    except TwoFactorProfile.DoesNotExist:
        tf_profile = None
    
    return Response({
        'success': True,
        'lists': ListSerializer(lists, many=True, context={'request': request}).data,
        'user': UserSerializer(request.user).data,
        'user_type': get_user_type(request.user),
        'can_delete': can_delete(request.user),
        'is_invited': is_invited if not is_admin else False,
        'students': UserSerializer(students, many=True).data if is_admin else [],
        'pending_invitations': InvitationSerializer(pending_invitations, many=True).data,
        'activities': ActivitySerializer(activities, many=True).data if can_view_activities else [],
        'can_view_activities': can_view_activities,
        'activities_heading': activities_heading,
        'board_colors': BOARD_COLORS,
        'board_color': board_color,
        'board_overlay_color': board_overlay_color,
        'board_background_image': board_background_image,
        'preferences': BoardPreferenceSerializer(preference, context={'request': request}).data,
        'creators': UserSerializer(creators, many=True).data,
        'filters': {
            'q': search_query,
            'creator': creator_filter,
            'due_from': due_from,
            'due_to': due_to,
        },
        'has_filters': any([search_query, creator_filter, due_from, due_to]),
        'total_filtered_tasks': total_filtered_tasks,
        'two_factor_enabled': tf_profile.enabled if tf_profile else False,
        'attachment_max_size_mb': get_max_attachment_size() // (1024 * 1024),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_create_list(request):
    """Crear una nueva lista"""
    name = request.data.get('name', 'Nueva Lista').strip()
    
    if not name:
        return Response({
            'success': False,
            'error': 'El nombre de la lista es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    board_user = get_user_for_board(request.user)
    max_order = List.objects.filter(user=board_user).aggregate(Max('order'))['order__max'] or 0
    
    list_obj = List.objects.create(
        name=name,
        user=board_user,
        order=max_order + 1,
        color='purple',
        created_by=request.user
    )
    
    log_activity(
        request.user,
        'create_list',
        f'{name} - Creada por {request.user.username}',
        list_obj=list_obj
    )
    
    return Response({
        'success': True,
        'list': ListSerializer(list_obj, context={'request': request}).data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_delete_list(request, list_id):
    """Eliminar una lista"""
    if not can_delete(request.user):
        return Response({
            'success': False,
            'error': 'No tienes permisos para eliminar listas'
        }, status=status.HTTP_403_FORBIDDEN)
    
    board_user = get_user_for_board(request.user)
    list_obj = get_object_or_404(List, id=list_id, user=board_user)
    
    list_name = list_obj.name
    task_count = list_obj.tasks.count()
    subtask_count = Subtask.objects.filter(task__list=list_obj).count()
    
    log_activity(
        request.user,
        'delete_list',
        f'Eliminó la lista "{list_name}" con {task_count} tarea(s) y {subtask_count} subtarea(s)',
        list_obj=list_obj
    )
    
    list_obj.delete()
    
    return Response({
        'success': True,
        'message': f'Lista eliminada exitosamente. Se eliminaron {task_count} tareas y {subtask_count} subtareas.'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_change_list_color(request, list_id):
    """Cambiar el color de una lista"""
    new_color = request.data.get('color')
    valid_colors = ['green', 'yellow', 'black', 'purple']
    
    if not new_color:
        return Response({
            'success': False,
            'error': 'Color no especificado'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if new_color not in valid_colors:
        return Response({
            'success': False,
            'error': f'Color no válido: {new_color}. Colores válidos: {", ".join(valid_colors)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    board_user = get_user_for_board(request.user)
    list_obj = get_object_or_404(List, id=list_id, user=board_user)
    old_color = list_obj.color
    list_obj.color = new_color
    list_obj.save()
    
    log_activity(
        request.user,
        'edit_list',
        f'Cambió el color de la lista "{list_obj.name}" de {old_color} a {new_color}',
        list_obj=list_obj
    )
    
    return Response({
        'success': True,
        'message': f'Color de lista cambiado de {old_color} a {new_color}',
        'color': list_obj.color,
        'list': ListSerializer(list_obj, context={'request': request}).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_create_task(request):
    """Crear una nueva tarea"""
    list_id = request.data.get('list_id')
    title = request.data.get('title', 'Nueva Tarea').strip()
    
    if not list_id or not title:
        return Response({
            'success': False,
            'error': 'Lista y título son requeridos'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    board_user = get_user_for_board(request.user)
    list_obj = get_object_or_404(List, id=list_id, user=board_user)
    
    max_order = list_obj.tasks.aggregate(Max('order'))['order__max'] or 0
    
    task = Task.objects.create(
        title=title,
        list=list_obj,
        order=max_order + 1,
        created_by=request.user
    )
    
    log_activity(
        request.user,
        'create_task',
        f'{title} - Creada por {request.user.username}',
        task=task,
        list_obj=list_obj
    )
    
    return Response({
        'success': True,
        'task': TaskSerializer(task, context={'request': request}).data
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def api_update_task(request, task_id):
    """Actualizar una tarea"""
    board_user = get_user_for_board(request.user)
    task = get_object_or_404(Task, id=task_id, list__user=board_user)
    
    old_title = task.title
    old_due_date = task.due_date
    title = request.data.get('title')
    due_date_str = request.data.get('due_date', '').strip()
    
    changes = []
    
    if title is not None:
        title = title.strip()
        if title:
            task.title = title
            if title != old_title:
                changes.append(f'título a "{title}"')
        else:
            return Response({
                'success': False,
                'error': 'El título no puede estar vacío'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    if 'due_date' in request.data:
        if due_date_str:
            try:
                new_due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                if new_due_date != old_due_date:
                    task.due_date = new_due_date
                    changes.append(f'fecha de vencimiento a {new_due_date.strftime("%d/%m/%Y")}')
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Formato de fecha inválido'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            if old_due_date:
                task.due_date = None
                changes.append('fecha de vencimiento (eliminada)')
    
    task.save()
    
    if changes:
        log_activity(
            request.user,
            'edit_task',
            f'Actualizó {" y ".join(changes)} en la tarea "{task.title}"',
            task=task,
            list_obj=task.list
        )
    
    return Response({
        'success': True,
        'task': TaskSerializer(task, context={'request': request}).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_delete_task(request, task_id):
    """Eliminar una tarea"""
    if not can_delete(request.user):
        return Response({
            'success': False,
            'error': 'No tienes permisos para eliminar tareas'
        }, status=status.HTTP_403_FORBIDDEN)
    
    board_user = get_user_for_board(request.user)
    task = get_object_or_404(Task, id=task_id, list__user=board_user)
    
    task_title = task.title
    task_list = task.list
    
    log_activity(
        request.user,
        'delete_task',
        f'Eliminó/cerró la tarea "{task_title}" de la lista "{task_list.name}"',
        task=task,
        list_obj=task_list
    )
    
    task.delete()
    
    return Response({
        'success': True,
        'message': 'Tarea eliminada exitosamente'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_move_task(request, task_id):
    """Mover una tarea a otra lista"""
    new_list_id = request.data.get('list_id')
    
    if not new_list_id:
        return Response({
            'success': False,
            'error': 'ID de lista es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    board_user = get_user_for_board(request.user)
    task = get_object_or_404(Task, id=task_id, list__user=board_user)
    old_list = task.list
    new_list = get_object_or_404(List, id=new_list_id, user=board_user)
    
    max_order = new_list.tasks.aggregate(Max('order'))['order__max'] or 0
    
    task.list = new_list
    task.order = max_order + 1
    task.save()
    
    # Registrar actividad y enviar notificación en tiempo real
    logger.info(f"Usuario {request.user.username} moviendo tarea {task.id} de lista {old_list.id} a {new_list.id}")
    log_activity(
        request.user,
        'move_task',
        f'Movió la tarea "{task.title}" de "{old_list.name}" a "{new_list.name}"',
        task=task,
        list_obj=new_list
    )
    logger.info(f"Actividad registrada para movimiento de tarea {task.id}")
    
    return Response({
        'success': True,
        'task': TaskSerializer(task, context={'request': request}).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_create_subtask(request, task_id):
    """Crear una nueva subtarea"""
    title = request.data.get('title', 'Nueva Subtarea').strip()
    
    if not title:
        return Response({
            'success': False,
            'error': 'El título de la subtarea es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    board_user = get_user_for_board(request.user)
    task = get_object_or_404(Task, id=task_id, list__user=board_user)
    
    max_order = task.subtasks.aggregate(Max('order'))['order__max'] or 0
    
    subtask = Subtask.objects.create(
        title=title,
        task=task,
        order=max_order + 1,
        completed=False,
        created_by=request.user
    )
    
    log_activity(
        request.user,
        'create_subtask',
        f'{title} - Creada por {request.user.username}',
        task=task,
        list_obj=task.list,
        subtask=subtask
    )
    
    return Response({
        'success': True,
        'subtask': SubtaskSerializer(subtask, context={'request': request}).data
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def api_update_subtask(request, subtask_id):
    """Actualizar una subtarea"""
    board_user = get_user_for_board(request.user)
    subtask = get_object_or_404(Subtask, id=subtask_id, task__list__user=board_user)
    
    old_title = subtask.title
    old_completed = subtask.completed
    old_due_date = subtask.due_date
    title = request.data.get('title')
    completed = request.data.get('completed')
    due_date_str = request.data.get('due_date', '').strip()
    
    changes = []
    
    if title is not None:
        title = title.strip()
        if title:
            subtask.title = title
            if title != old_title:
                changes.append(f'título a "{title}"')
        else:
            return Response({
                'success': False,
                'error': 'El título de la subtarea no puede estar vacío'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    if completed is not None:
        subtask.completed = completed if isinstance(completed, bool) else completed.lower() in ('true', '1', 'on')
        if subtask.completed != old_completed:
            estado_texto = 'completada' if subtask.completed else 'pendiente'
            changes.append(f'estado a {estado_texto}')
    
    if 'due_date' in request.data:
        if due_date_str:
            try:
                new_due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                if new_due_date != old_due_date:
                    subtask.due_date = new_due_date
                    changes.append(f'fecha de vencimiento a {new_due_date.strftime("%d/%m/%Y")}')
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Formato de fecha inválido'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            if old_due_date:
                subtask.due_date = None
                changes.append('fecha de vencimiento (eliminada)')
    
    subtask.save()
    
    if changes:
        log_activity(
            request.user,
            'edit_subtask',
            f'Actualizó {" y ".join(changes)} en la subtarea "{subtask.title}"',
            task=subtask.task,
            list_obj=subtask.task.list,
            subtask=subtask
        )
    
    return Response({
        'success': True,
        'subtask': SubtaskSerializer(subtask, context={'request': request}).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_delete_subtask(request, subtask_id):
    """Eliminar una subtarea"""
    if not can_delete(request.user):
        return Response({
            'success': False,
            'error': 'No tienes permisos para eliminar subtareas'
        }, status=status.HTTP_403_FORBIDDEN)
    
    board_user = get_user_for_board(request.user)
    subtask = get_object_or_404(Subtask, id=subtask_id, task__list__user=board_user)
    
    subtask_title = subtask.title
    subtask_task = subtask.task
    subtask_list = subtask.task.list
    
    log_activity(
        request.user,
        'delete_subtask',
        f'Eliminó la subtarea "{subtask_title}" de la tarea "{subtask_task.title}"',
        task=subtask_task,
        list_obj=subtask_list,
        subtask=subtask
    )
    
    subtask.delete()
    
    return Response({
        'success': True,
        'message': 'Subtarea eliminada exitosamente'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_toggle_subtask(request, subtask_id):
    """Cambiar el estado de completado de una subtarea"""
    board_user = get_user_for_board(request.user)
    subtask = get_object_or_404(Subtask, id=subtask_id, task__list__user=board_user)
    
    old_completed = subtask.completed
    subtask.completed = not subtask.completed
    subtask.save()
    
    status_text = "completó" if subtask.completed else "descompletó"
    log_activity(
        request.user,
        'toggle_subtask',
        f'{status_text.capitalize()} la subtarea "{subtask.title}" de la tarea "{subtask.task.title}"',
        task=subtask.task,
        list_obj=subtask.task.list,
        subtask=subtask
    )
    
    return Response({
        'success': True,
        'subtask': SubtaskSerializer(subtask, context={'request': request}).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_activities(request):
    """Obtener actividades"""
    from .views import get_user_for_board
    from django.db.models import Q
    
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
        else:
            activities = Activity.objects.none()
    
    return Response({
        'success': True,
        'activities': ActivitySerializer(activities, many=True).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_calendar(request):
    """Obtener datos del calendario"""
    from django.templatetags.static import static
    from .views import get_board_color, hex_to_rgba
    from .views import classify_due
    
    board_user = get_user_for_board(request.user)
    ensure_default_lists(board_user)
    
    preference = get_board_preference(board_user)
    board_color = get_board_color(board_user)
    board_overlay_color = hex_to_rgba(board_color)
    
    if preference.background_image:
        board_background_image = request.build_absolute_uri(preference.background_image.url)
    else:
        board_background_image = request.build_absolute_uri(static('kanban/img/board-bg.jpg'))
    
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
            'due_date': due_date.strftime('%Y-%m-%d') if due_date else None,
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
            'due_date': due_date.strftime('%Y-%m-%d') if due_date else None,
            'due_in': due_in,
            'due_in_abs': abs(due_in) if due_in is not None else None,
            'status': classify_due(due_in),
        })
    
    calendar_items.sort(key=lambda item: (item['due_date'] or '9999-12-31', item['type']))
    
    overdue = sum(1 for item in calendar_items if item['status'] == 'overdue')
    soon = sum(1 for item in calendar_items if item['status'] == 'soon')
    
    return Response({
        'success': True,
        'calendar_items': calendar_items,
        'overdue_count': overdue,
        'soon_count': soon,
        'total_items': len(calendar_items),
        'board_overlay_color': board_overlay_color,
        'board_background_image': board_background_image,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_reorder_lists(request):
    """Reordenar las listas del tablero"""
    try:
        list_ids = request.data.get('list_ids', [])
        
        # Usar usuario compartido si es administrador
        board_user = get_user_for_board(request.user)
        
        # Actualizar el orden de las listas
        for index, list_id in enumerate(list_ids):
            list_obj = get_object_or_404(List, id=list_id, user=board_user)
            list_obj.order = index
            list_obj.save()
        
        return Response({
            'success': True,
            'message': 'Listas reordenadas exitosamente'
        })
    except Exception as e:
        logger.error(f'Error al reordenar listas: {str(e)}')
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_reorder_tasks(request):
    """Reordenar tareas dentro de una lista o entre listas"""
    try:
        task_ids = request.data.get('task_ids', [])
        list_id = request.data.get('list_id')
        
        if not list_id:
            return Response({
                'success': False,
                'error': 'list_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        return Response({
            'success': True,
            'message': 'Tareas reordenadas exitosamente'
        })
    except Exception as e:
        logger.error(f'Error al reordenar tareas: {str(e)}')
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_reorder_subtasks(request):
    """Reordenar subtareas dentro de una tarea"""
    try:
        subtask_ids = request.data.get('subtask_ids', [])
        task_id = request.data.get('task_id')
        
        if not task_id:
            return Response({
                'success': False,
                'error': 'task_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Usar usuario compartido si es administrador
        board_user = get_user_for_board(request.user)
        
        task = get_object_or_404(Task, id=task_id, list__user=board_user)
        
        # Actualizar el orden de las subtareas
        for index, subtask_id in enumerate(subtask_ids):
            subtask = get_object_or_404(Subtask, id=subtask_id, task__list__user=board_user)
            subtask.task = task
            subtask.order = index + 1
            subtask.save()
        
        return Response({
            'success': True,
            'message': 'Subtareas reordenadas exitosamente'
        })
    except Exception as e:
        logger.error(f'Error al reordenar subtareas: {str(e)}')
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_upload_task_attachment(request, task_id):
    """Subir adjunto a una tarea"""
    from .views import get_user_for_board, get_max_attachment_size, log_activity
    
    board_user = get_user_for_board(request.user)
    task = get_object_or_404(Task, id=task_id, list__user=board_user)
    
    attachment_file = request.FILES.get('file')
    if not attachment_file:
        return Response({'success': False, 'error': 'No se envió ningún archivo.'}, status=status.HTTP_400_BAD_REQUEST)
    
    max_size = get_max_attachment_size()
    if attachment_file.size > max_size:
        return Response({
            'success': False,
            'error': f'El archivo excede el tamaño máximo permitido ({max_size // (1024 * 1024)} MB).'
        }, status=status.HTTP_400_BAD_REQUEST)
    
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
    
    return Response({
        'success': True,
        'attachment': {
            'id': attachment.id,
            'filename': attachment.filename,
            'file_url': request.build_absolute_uri(attachment.file.url),
            'uploaded_by_username': attachment.uploaded_by.username if attachment.uploaded_by else 'Administrador',
            'uploaded_at': attachment.uploaded_at.isoformat(),
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_upload_subtask_attachment(request, subtask_id):
    """Subir adjunto a una subtarea"""
    from .views import get_user_for_board, get_max_attachment_size, log_activity
    
    board_user = get_user_for_board(request.user)
    subtask = get_object_or_404(Subtask, id=subtask_id, task__list__user=board_user)
    
    attachment_file = request.FILES.get('file')
    if not attachment_file:
        return Response({'success': False, 'error': 'No se envió ningún archivo.'}, status=status.HTTP_400_BAD_REQUEST)
    
    max_size = get_max_attachment_size()
    if attachment_file.size > max_size:
        return Response({
            'success': False,
            'error': f'El archivo excede el tamaño máximo permitido ({max_size // (1024 * 1024)} MB).'
        }, status=status.HTTP_400_BAD_REQUEST)
    
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
    
    return Response({
        'success': True,
        'attachment': {
            'id': attachment.id,
            'filename': attachment.filename,
            'file_url': request.build_absolute_uri(attachment.file.url),
            'uploaded_by_username': attachment.uploaded_by.username if attachment.uploaded_by else 'Administrador',
            'uploaded_at': attachment.uploaded_at.isoformat(),
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_delete_task_attachment(request, attachment_id):
    """Eliminar adjunto de una tarea"""
    from .views import can_delete, get_user_for_board, log_activity
    
    if not can_delete(request.user):
        return Response({'success': False, 'error': 'No tienes permisos para eliminar adjuntos.'}, status=status.HTTP_403_FORBIDDEN)
    
    attachment = get_object_or_404(TaskAttachment, id=attachment_id)
    board_user = get_user_for_board(request.user)
    if not (request.user.is_staff or request.user.is_superuser):
        if attachment.task.list.user != board_user:
            return Response({'success': False, 'error': 'No tienes acceso a este adjunto.'}, status=status.HTTP_403_FORBIDDEN)
    
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
    
    return Response({'success': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_delete_subtask_attachment(request, attachment_id):
    """Eliminar adjunto de una subtarea"""
    from .views import can_delete, get_user_for_board, log_activity
    
    if not can_delete(request.user):
        return Response({'success': False, 'error': 'No tienes permisos para eliminar adjuntos.'}, status=status.HTTP_403_FORBIDDEN)
    
    attachment = get_object_or_404(SubtaskAttachment, id=attachment_id)
    board_user = get_user_for_board(request.user)
    if not (request.user.is_staff or request.user.is_superuser):
        if attachment.subtask.task.list.user != board_user:
            return Response({'success': False, 'error': 'No tienes acceso a este adjunto.'}, status=status.HTTP_403_FORBIDDEN)
    
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
    
    return Response({'success': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_invite_student(request):
    """Invitar un estudiante al tablero compartido (solo administradores)"""
    from django.contrib.auth.models import User
    
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({
            'success': False,
            'error': 'Solo los administradores pueden invitar estudiantes'
        }, status=status.HTTP_403_FORBIDDEN)
    
    student_id = request.data.get('student_id')
    if not student_id:
        return Response({
            'success': False,
            'error': 'ID de estudiante no especificado'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        student = User.objects.get(id=student_id, is_staff=False, is_superuser=False)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Estudiante no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    invitation, created = Invitation.objects.get_or_create(
        admin=request.user,
        student=student,
        defaults={'accepted': False}
    )
    
    if not created:
        if invitation.accepted:
            return Response({
                'success': False,
                'error': f'El estudiante {student.username} ya está invitado y ha aceptado'
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'success': False,
                'error': f'Ya existe una invitación pendiente para {student.username}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True,
        'message': f'Invitación enviada a {student.username}'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_accept_invitation(request, invitation_id):
    """Aceptar una invitación (solo estudiantes)"""
    if request.user.is_staff or request.user.is_superuser:
        return Response({
            'success': False,
            'error': 'Los administradores no pueden aceptar invitaciones'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        invitation = Invitation.objects.get(id=invitation_id, student=request.user)
        if invitation.accepted:
            return Response({
                'success': False,
                'error': 'Esta invitación ya fue aceptada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        invitation.accepted = True
        invitation.save()
        
        return Response({
            'success': True,
            'message': 'Invitación aceptada. Ahora puedes ver el tablero compartido'
        })
    except Invitation.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Invitación no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_reject_invitation(request, invitation_id):
    """Rechazar una invitación"""
    try:
        invitation = Invitation.objects.get(id=invitation_id)
        if invitation.student != request.user and invitation.admin != request.user:
            return Response({
                'success': False,
                'error': 'No tienes permiso para rechazar esta invitación'
            }, status=status.HTTP_403_FORBIDDEN)
        
        invitation.delete()
        
        return Response({
            'success': True,
            'message': 'Invitación rechazada'
        })
    except Invitation.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Invitación no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_create_user(request):
    """Crear un nuevo usuario (administrador o estudiante) desde el tablero"""
    from django.contrib.auth.models import User
    
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({
            'success': False,
            'error': 'Solo los administradores pueden crear usuarios'
        }, status=status.HTTP_403_FORBIDDEN)
    
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()
    email = request.data.get('email', '').strip()
    role = request.data.get('role', '').strip().lower()
    
    if not username or not password or not email:
        return Response({
            'success': False,
            'error': 'Todos los campos son obligatorios'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if role not in ['admin', 'student']:
        return Response({
            'success': False,
            'error': 'Rol inválido. Debe ser "admin" o "student"'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({
            'success': False,
            'error': 'El nombre de usuario ya existe'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=email).exists():
        return Response({
            'success': False,
            'error': 'Ya existe un usuario con ese correo'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(
        username=username,
        password=password,
        email=email
    )
    
    if role == 'admin':
        user.is_staff = True
        user.is_superuser = True
        user.save(update_fields=['is_staff', 'is_superuser'])
    
    return Response({
        'success': True,
        'message': f'Usuario {username} creado correctamente como {"Administrador" if role == "admin" else "Estudiante"}'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_change_board_color(request):
    """Actualizar el color de fondo del tablero"""
    from .views import BOARD_COLORS, get_user_for_board, get_board_preference
    
    color = request.data.get('color')
    if not color:
        return Response({'success': False, 'error': 'Color no proporcionado'}, status=status.HTTP_400_BAD_REQUEST)
    
    if color not in BOARD_COLORS and color != 'transparent':
        return Response({'success': False, 'error': 'Color no permitido'}, status=status.HTTP_400_BAD_REQUEST)
    
    board_user = get_user_for_board(request.user)
    preference = get_board_preference(board_user)
    preference.color = color
    preference.save(update_fields=['color', 'updated_at'])
    
    return Response({'success': True, 'message': 'Color actualizado correctamente', 'color': color})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_upload_board_background(request):
    """Subir imagen de fondo del tablero"""
    from .views import get_user_for_board, get_board_preference
    
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({'success': False, 'error': 'Solo los administradores pueden subir fondos'}, status=status.HTTP_403_FORBIDDEN)
    
    image = request.FILES.get('image')
    if not image:
        return Response({'success': False, 'error': 'No se recibió ninguna imagen'}, status=status.HTTP_400_BAD_REQUEST)
    
    if image.size > 4 * 1024 * 1024:
        return Response({'success': False, 'error': 'La imagen debe pesar menos de 4MB'}, status=status.HTTP_400_BAD_REQUEST)
    
    valid_content_types = {'image/png', 'image/jpeg', 'image/jpg', 'image/webp'}
    if image.content_type not in valid_content_types:
        return Response({'success': False, 'error': 'Formato de imagen no soportado'}, status=status.HTTP_400_BAD_REQUEST)
    
    board_user = get_user_for_board(request.user)
    preference = get_board_preference(board_user)
    
    if preference.background_image:
        preference.background_image.delete(save=False)
    
    preference.background_image = image
    preference.save(update_fields=['background_image', 'updated_at'])
    
    return Response({
        'success': True,
        'message': 'Imagen de fondo actualizada correctamente',
        'background_image_url': request.build_absolute_uri(preference.background_image.url)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_add_activity_comment(request, activity_id):
    """Permitir que administradores agreguen comentarios a actividades"""
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({
            'success': False,
            'error': 'Solo los administradores pueden comentar actividades'
        }, status=status.HTTP_403_FORBIDDEN)
    
    comment_text = request.data.get('comment', '').strip()
    if not comment_text:
        return Response({
            'success': False,
            'error': 'El comentario no puede estar vacío'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    activity = get_object_or_404(Activity, id=activity_id)
    comment = ActivityComment.objects.create(
        activity=activity,
        author=request.user,
        comment=comment_text
    )
    
    return Response({
        'success': True,
        'comment': {
            'id': comment.id,
            'author_username': comment.author.username,
            'comment': comment.comment,
            'created_at': comment.created_at.isoformat()
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_system_logs(request):
    """Endpoint API para obtener los logs del sistema"""
    try:
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({
                'success': False,
                'error': 'No tienes permisos para ver los registros del sistema.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        from pathlib import Path
        log_file = getattr(settings, 'LOG_FILE_PATH', None)
        log_lines = []
        file_exists = False
        
        if log_file:
            # Convertir a Path si es necesario
            if isinstance(log_file, str):
                log_file_path = Path(log_file)
            else:
                log_file_path = log_file
            
            if log_file_path.exists():
                try:
                    with open(log_file_path, 'r', encoding='utf-8', errors='replace') as fh:
                        lines = fh.readlines()
                        log_lines = lines[-500:] if lines else []
                    file_exists = True
                except OSError as exc:
                    logger.error(f'Error al leer archivo de logs: {exc}')
                    log_lines = [f'No se pudo leer el archivo de logs: {exc}']
            else:
                log_lines = ['El archivo de logs aún no ha sido creado.']
        else:
            log_lines = ['El archivo de logs no está configurado en settings.LOG_FILE_PATH.']
        
        return Response({
            'success': True,
            'log_lines': log_lines,
            'file_exists': file_exists,
            'log_file_path': str(log_file) if log_file else None
        })
    except Exception as e:
        logger.error(f'Error en api_system_logs: {str(e)}', exc_info=True)
        return Response({
            'success': False,
            'error': f'Error al cargar los logs: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_two_factor_setup(request):
    """Endpoint API para configurar 2FA"""
    from .views import generate_qr_code_base64
    import pyotp
    
    try:
        profile = get_two_factor_profile(request.user, ensure_secret=True)
        logger.info(f"2FA Setup - Usuario: {request.user.username}, Profile ID: {profile.id if profile else None}, Secret: {profile.secret[:10] if profile.secret else 'None'}...")
        
        # Asegurar que el perfil tenga un secreto
        if not profile.secret:
            import pyotp
            profile.secret = pyotp.random_base32()
            profile.save(update_fields=['secret', 'updated_at'])
            logger.info(f"2FA Setup - Secreto generado para usuario {request.user.username}")
    except Exception as e:
        logger.error(f"Error al obtener perfil 2FA: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': f'Error al obtener perfil 2FA: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    if request.method == 'POST':
        action = request.data.get('action')
        if action == 'enable':
            code = request.data.get('code', '').strip().replace(' ', '')
            totp = pyotp.TOTP(profile.secret)
            if totp.verify(code, valid_window=1):
                if not profile.enabled:
                    profile.enabled = True
                    profile.save(update_fields=['enabled', 'updated_at'])
                return Response({
                    'success': True,
                    'message': 'Autenticación de dos pasos habilitada correctamente.',
                    'enabled': True
                })
            else:
                return Response({
                    'success': False,
                    'error': 'El código proporcionado no es válido. Intenta nuevamente.'
                }, status=status.HTTP_400_BAD_REQUEST)
        elif action == 'regenerate':
            profile.secret = pyotp.random_base32()
            profile.enabled = False
            profile.save(update_fields=['secret', 'enabled', 'updated_at'])
            # Regenerar QR
            totp = pyotp.TOTP(profile.secret)
            provisioning_uri = totp.provisioning_uri(name=request.user.username, issuer_name='Kanban Board')
            qr_data_uri = generate_qr_code_base64(provisioning_uri)
            return Response({
                'success': True,
                'message': 'Se generó un nuevo código secreto. Debes escanear el nuevo código QR antes de habilitar 2FA.',
                'secret': profile.secret,
                'qr_code_data_uri': qr_data_uri,
                'provisioning_uri': provisioning_uri,
                'enabled': False
            })
        elif action == 'disable':
            if profile.enabled:
                profile.enabled = False
                profile.save(update_fields=['enabled', 'updated_at'])
            return Response({
                'success': True,
                'message': 'Autenticación de dos pasos deshabilitada.',
                'enabled': False
            })
        else:
            return Response({
                'success': False,
                'error': 'Acción no reconocida.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # GET: Retornar información del perfil 2FA
    try:
        totp = pyotp.TOTP(profile.secret)
        provisioning_uri = totp.provisioning_uri(name=request.user.username, issuer_name='Kanban Board')
        logger.info(f"2FA Setup - Provisioning URI generado para {request.user.username}")
        
        try:
            qr_data_uri = generate_qr_code_base64(provisioning_uri)
            logger.info(f"2FA Setup - QR code generado exitosamente (longitud: {len(qr_data_uri)} caracteres)")
        except Exception as e:
            logger.error(f"Error al generar QR code: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response({
                'success': False,
                'error': f'Error al generar código QR: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'profile': {
                'enabled': profile.enabled,
                'secret': profile.secret
            },
            'qr_code_data_uri': qr_data_uri,
            'provisioning_uri': provisioning_uri,
            'totp_interval': totp.interval
        })
    except Exception as e:
        logger.error(f"Error en 2FA Setup GET: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': f'Error al generar configuración 2FA: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_board_users_for_reminders(request):
    """
    Endpoint API para obtener todos los usuarios con acceso al tablero y sus tareas
    organizadas por tipo de recordatorio. Para usar con EmailJS desde el frontend.
    """
    try:
        from django.contrib.auth.models import User
        from .models import Task, Subtask, Invitation, List
        from django.db.models import Q
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        
        # Obtener todos los usuarios que tienen acceso al tablero
        users_with_lists = User.objects.filter(lists__isnull=False).distinct()
        invited_users = User.objects.filter(received_invitations__accepted=True).distinct()
        admin_users = User.objects.filter(sent_invitations__accepted=True).distinct()
        all_board_users = (users_with_lists | invited_users | admin_users).distinct()
        
        users_data = []
        
        for user in all_board_users:
            if not user.email:
                continue
            
            # Obtener todas las tareas y subtareas relacionadas con este usuario
            tasks_created = Task.objects.filter(created_by=user).select_related('list', 'created_by')
            tasks_in_user_lists = Task.objects.filter(list__user=user).select_related('list', 'created_by')
            
            if Invitation.objects.filter(student=user, accepted=True).exists():
                admin_ids = Invitation.objects.filter(
                    student=user, accepted=True
                ).values_list('admin_id', flat=True)
                tasks_from_admins = Task.objects.filter(
                    list__user_id__in=admin_ids
                ).select_related('list', 'created_by')
            else:
                tasks_from_admins = Task.objects.none()
            
            all_user_tasks = (tasks_created | tasks_in_user_lists | tasks_from_admins).distinct()
            subtasks_created = Subtask.objects.filter(created_by=user).select_related('task', 'task__list', 'task__created_by')
            subtasks_from_user_tasks = Subtask.objects.filter(
                task__in=all_user_tasks
            ).select_related('task', 'task__list', 'task__created_by')
            all_user_subtasks = (subtasks_created | subtasks_from_user_tasks).distinct()
            
            # Clasificar tareas y subtareas
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
                
                if days_remaining < 0:
                    overdue_tasks.append({
                        'title': task.title,
                        'list_name': task.list.name,
                        'due_date': task.due_date.strftime('%d/%m/%Y'),
                        'days_overdue': abs(days_remaining)
                    })
                elif 1 <= days_remaining <= 3:
                    tasks_1_3_days.append({
                        'title': task.title,
                        'list_name': task.list.name,
                        'due_date': task.due_date.strftime('%d/%m/%Y'),
                        'days_remaining': days_remaining
                    })
                elif 4 <= days_remaining <= 7:
                    tasks_4_7_days.append({
                        'title': task.title,
                        'list_name': task.list.name,
                        'due_date': task.due_date.strftime('%d/%m/%Y'),
                        'days_remaining': days_remaining
                    })
            
            for subtask in all_user_subtasks:
                if not subtask.due_date or subtask.completed:
                    continue
                days_remaining = (subtask.due_date - today).days
                
                if days_remaining < 0:
                    overdue_subtasks.append({
                        'title': subtask.title,
                        'task_title': subtask.task.title,
                        'list_name': subtask.task.list.name,
                        'due_date': subtask.due_date.strftime('%d/%m/%Y'),
                        'days_overdue': abs(days_remaining)
                    })
                elif 1 <= days_remaining <= 3:
                    subtasks_1_3_days.append({
                        'title': subtask.title,
                        'task_title': subtask.task.title,
                        'list_name': subtask.task.list.name,
                        'due_date': subtask.due_date.strftime('%d/%m/%Y'),
                        'days_remaining': days_remaining
                    })
                elif 4 <= days_remaining <= 7:
                    subtasks_4_7_days.append({
                        'title': subtask.title,
                        'task_title': subtask.task.title,
                        'list_name': subtask.task.list.name,
                        'due_date': subtask.due_date.strftime('%d/%m/%Y'),
                        'days_remaining': days_remaining
                    })
            
            # Solo incluir usuarios que tienen tareas pendientes
            total_items = (len(overdue_tasks) + len(tasks_1_3_days) + len(tasks_4_7_days) +
                          len(overdue_subtasks) + len(subtasks_1_3_days) + len(subtasks_4_7_days))
            
            if total_items > 0:
                users_data.append({
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.get_full_name() or user.username,
                    'overdue_tasks': overdue_tasks,
                    'tasks_1_3_days': tasks_1_3_days,
                    'tasks_4_7_days': tasks_4_7_days,
                    'overdue_subtasks': overdue_subtasks,
                    'subtasks_1_3_days': subtasks_1_3_days,
                    'subtasks_4_7_days': subtasks_4_7_days,
                    'total_items': total_items
                })
        
        return Response({
            'success': True,
            'users': users_data,
            'total_users': len(users_data)
        })
        
    except Exception as e:
        logger.error(f"Error al obtener usuarios del tablero: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': f'Error al obtener usuarios: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_send_board_reminders(request):
    """
    Endpoint API para enviar recordatorios por correo a todos los usuarios del tablero.
    Usa Celery para procesar el envío de forma asíncrona.
    """
    try:
        data = request.data
        include_overdue = data.get('include_overdue', True)
        include_1_3_days = data.get('include_1_3_days', True)
        include_4_7_days = data.get('include_4_7_days', False)
        
        if not (include_overdue or include_1_3_days or include_4_7_days):
            return Response({
                'success': False,
                'error': 'Debes seleccionar al menos una opción de recordatorio'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Intentar ejecutar la tarea de Celery de forma asíncrona
        # Si Celery no está disponible, ejecutar de forma síncrona
        try:
            task = send_board_reminders_to_all_users.delay(
                include_overdue=include_overdue,
                include_1_3_days=include_1_3_days,
                include_4_7_days=include_4_7_days
            )
            
            logger.info(f"Tarea de recordatorios iniciada por {request.user.username}. Task ID: {task.id}")
            
            return Response({
                'success': True,
                'message': 'Los recordatorios se están enviando. Esto puede tomar unos momentos.',
                'task_id': task.id
            })
        except Exception as celery_error:
            # Si Celery no está disponible, ejecutar de forma síncrona
            logger.warning(f"Celery no disponible, ejecutando de forma síncrona: {celery_error}")
            try:
                result = send_board_reminders_to_all_users(
                    include_overdue=include_overdue,
                    include_1_3_days=include_1_3_days,
                    include_4_7_days=include_4_7_days
                )
                
                return Response({
                    'success': True,
                    'message': f'Se enviaron {result.get("emails_sent", 0)} correo(s) exitosamente.',
                    'emails_sent': result.get('emails_sent', 0),
                    'errors': result.get('errors', 0)
                })
            except Exception as sync_error:
                logger.error(f"Error al ejecutar recordatorios de forma síncrona: {sync_error}")
                raise
        
    except Exception as e:
        logger.error(f"Error al iniciar envío de recordatorios: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': f'Error al enviar recordatorios: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
