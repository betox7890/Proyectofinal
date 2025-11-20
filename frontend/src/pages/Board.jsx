import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { kanbanService } from '../services/api';
import './Board.css';

function Board() {
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [user, setUser] = useState(null);
  const [canDelete, setCanDelete] = useState(false);
  const [preferences, setPreferences] = useState(null);
  const [boardColors, setBoardColors] = useState([]);
  const [boardColor, setBoardColor] = useState(null);
  const [boardBackgroundImage, setBoardBackgroundImage] = useState(null);
  const [creators, setCreators] = useState([]);
  const [students, setStudents] = useState([]);
  const [pendingInvitations, setPendingInvitations] = useState([]);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [userType, setUserType] = useState('');
  const [isInvited, setIsInvited] = useState(false);
  const [canViewActivities, setCanViewActivities] = useState(false);
  const [activitiesHeading, setActivitiesHeading] = useState('');
  const [attachmentMaxSizeMb, setAttachmentMaxSizeMb] = useState(10);
  
  // Estados para filtros
  const [filters, setFilters] = useState({
    q: '',
    creator: '',
    due_from: '',
    due_to: ''
  });
  const [hasFilters, setHasFilters] = useState(false);
  const [totalFilteredTasks, setTotalFilteredTasks] = useState(0);
  
  // Estados para modales
  const [showAddListModal, setShowAddListModal] = useState(false);
  const [showAddTaskModal, setShowAddTaskModal] = useState(false);
  const [showEditTaskModal, setShowEditTaskModal] = useState(false);
  const [showEditSubtaskModal, setShowEditSubtaskModal] = useState(false);
  const [showColorPickerModal, setShowColorPickerModal] = useState(false);
  const [showActivitiesModal, setShowActivitiesModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showInvitationsModal, setShowInvitationsModal] = useState(false);
  const [showCreateUserModal, setShowCreateUserModal] = useState(false);
  const [showBoardColorModal, setShowBoardColorModal] = useState(false);
  const [showAddSubtaskModal, setShowAddSubtaskModal] = useState(false);
  
  // Estados para formularios
  const [newListName, setNewListName] = useState('');
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskListId, setNewTaskListId] = useState(null);
  const [editingTask, setEditingTask] = useState(null);
  const [editingSubtask, setEditingSubtask] = useState(null);
  const [selectedListId, setSelectedListId] = useState(null);
  const [selectedTaskId, setSelectedTaskId] = useState(null);
  const [activities, setActivities] = useState([]);
  const [selectedStudentId, setSelectedStudentId] = useState('');
  const [newUserData, setNewUserData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'student'
  });
  const [expandedSubtasks, setExpandedSubtasks] = useState(new Set());
  
  // Estados para drag & drop
  const [draggedList, setDraggedList] = useState(null);
  const [draggedTask, setDraggedTask] = useState(null);
  const [draggedSubtask, setDraggedSubtask] = useState(null);
  const [draggedFromList, setDraggedFromList] = useState(null);
  
  const navigate = useNavigate();
  const boardListsRef = useRef(null);
  const activitiesSocketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    loadBoard();
  }, []);

  // WebSocket para notificaciones en tiempo real
  const initActivitiesSocket = () => {
    // Cerrar conexión anterior si existe
    if (activitiesSocketRef.current && activitiesSocketRef.current.readyState !== WebSocket.CLOSED) {
      console.log('[WebSocket] Cerrando conexión anterior...');
      activitiesSocketRef.current.close();
    }

    try {
      // Conectar directamente al backend para WebSockets
      // Usar localhost en lugar de 127.0.0.1 para que las cookies se envíen correctamente
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      // Usar localhost:8000 para que las cookies de sesión se envíen correctamente
      const socketUrl = `${protocol}://localhost:8000/ws/activities/`;
      console.log('[WebSocket] Intentando conectar a:', socketUrl);
      
      // Obtener las cookies de sesión para enviarlas en el WebSocket
      const cookies = document.cookie;
      console.log('[WebSocket] Cookies disponibles:', cookies);
      
      const socket = new WebSocket(socketUrl);
      activitiesSocketRef.current = socket;

      socket.onopen = () => {
        console.log('[WebSocket] ✅ Conexión establecida exitosamente');
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[WebSocket] 📨 Mensaje recibido:', data);
          
          // El consumer envía el payload directamente, que tiene type: 'activity'
          if (data.type === 'activity') {
            console.log('[WebSocket] ✅ Tipo de mensaje correcto (activity)');
            console.log('[WebSocket] Detalles:', {
              activity_type: data.activity_type,
              description: data.description,
              user: data.user,
              task_title: data.task_title,
              list_name: data.list_name
            });
            showActivityNotification(data);
            // Refrescar la lista completa (solo si el modal está abierto)
            if (showActivitiesModal) {
              loadActivities();
            }
          } else {
            console.warn('[WebSocket] ⚠️ Mensaje con formato desconocido. Tipo recibido:', data.type, 'Datos completos:', data);
          }
        } catch (error) {
          console.error('[WebSocket] ❌ Error al procesar mensaje:', error, 'Datos:', event.data);
        }
      };

      socket.onclose = (event) => {
        console.log('[WebSocket] 🔌 Conexión cerrada. Código:', event.code);
        
        // No reconectar si fue cerrado intencionalmente (código 1000) o por autenticación (4001)
        if (event.code !== 1000 && event.code !== 4001 && event.code !== 4002 && event.code !== 4003) {
          console.log('[WebSocket] 🔄 Reintentando conexión en 5 segundos...');
          reconnectTimeoutRef.current = setTimeout(initActivitiesSocket, 5000);
        } else {
          console.log('[WebSocket] ⏹️ No se reintentará la conexión');
        }
      };

      socket.onerror = (error) => {
        console.error('[WebSocket] ❌ Error en WebSocket:', error);
      };
    } catch (error) {
      console.error('[WebSocket] ❌ Error al inicializar WebSocket:', error);
    }
  };

  const showActivityNotification = (payload) => {
    // Asegurarse de que tenemos un contenedor para las notificaciones
    let container = document.querySelector('.notifications-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'notifications-container';
      document.body.appendChild(container);
    }

    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = 'notification-toast';
    
    // Obtener el tipo de actividad y el icono correspondiente
    const activityType = payload.activity_type || '';
    const activityTypeLower = activityType.toLowerCase();
    let icon = '🔔';
    if (activityTypeLower.includes('mover') || activityTypeLower.includes('move')) {
      icon = '↔️';
    } else if (activityTypeLower.includes('crear') || activityTypeLower.includes('create')) {
      icon = '➕';
    } else if (activityTypeLower.includes('editar') || activityTypeLower.includes('edit')) {
      icon = '✏️';
    } else if (activityTypeLower.includes('eliminar') || activityTypeLower.includes('delete')) {
      icon = '🗑️';
    }
    
    console.log('[Notificación] Mostrando notificación:', {
      activityType,
      icon,
      description: payload.description,
      user: payload.user
    });

    const header = document.createElement('div');
    header.className = 'notification-header';
    
    const title = document.createElement('div');
    title.className = 'notification-title';
    title.textContent = `${icon} ${activityType || 'Actividad'}`;
    
    const time = document.createElement('div');
    time.className = 'notification-time';
    time.textContent = payload.created_at || '';
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'notification-close';
    closeBtn.textContent = '×';
    closeBtn.onclick = () => {
      notification.style.animation = 'slideOut 0.3s ease-out';
      setTimeout(() => notification.remove(), 300);
    };
    
    header.appendChild(title);
    header.appendChild(time);
    header.appendChild(closeBtn);

    const body = document.createElement('div');
    body.className = 'notification-body';
    body.innerHTML = `
      <div><strong>${payload.user || 'Usuario'}</strong></div>
      <div>${payload.description || ''}</div>
      ${payload.task_title ? `<div style="margin-top: 4px;"><strong>Tarea:</strong> ${payload.task_title}</div>` : ''}
      ${payload.subtask_title ? `<div style="margin-top: 4px;"><strong>Subtarea:</strong> ${payload.subtask_title}</div>` : ''}
      ${payload.list_name ? `<div style="margin-top: 4px;"><strong>Lista:</strong> ${payload.list_name}</div>` : ''}
    `;

    notification.appendChild(header);
    notification.appendChild(body);
    container.appendChild(notification);

    // Auto-remover después de 6 segundos
    setTimeout(() => {
      if (notification.parentElement) {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
      }
    }, 6000);
  };

  // Inicializar WebSocket cuando canViewActivities esté disponible
  useEffect(() => {
    // Inicializar WebSocket para notificaciones en tiempo real
    // Inicializar siempre, no solo si canViewActivities es true
    // Esto permite que todos los usuarios vean notificaciones en tiempo real
    initActivitiesSocket();
    
    // Limpiar al desmontar
    return () => {
      if (activitiesSocketRef.current) {
        activitiesSocketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []); // Ejecutar solo una vez al montar el componente

  // Removido: Este useEffect causaba problemas con el submit del formulario
  // Los filtros se aplican directamente cuando se hace submit

  const loadBoard = async (customFilters = null) => {
    try {
      setLoading(true);
      // Usar filtros personalizados si se proporcionan, sino usar el estado
      const filtersToUse = customFilters !== null ? customFilters : filters;
      const params = {};
      if (filtersToUse.q) params.q = filtersToUse.q;
      if (filtersToUse.creator) params.creator = filtersToUse.creator;
      if (filtersToUse.due_from) params.due_from = filtersToUse.due_from;
      if (filtersToUse.due_to) params.due_to = filtersToUse.due_to;
      
      console.log('Cargando tablero con filtros:', params);
      
      const response = await kanbanService.getBoard(params);
      if (response.data.success) {
        setLists(response.data.lists || []);
        setUser(response.data.user);
        setCanDelete(response.data.can_delete || false);
        setPreferences(response.data.preferences || {});
        setBoardColors(response.data.board_colors || []);
        setBoardColor(response.data.board_color);
        setBoardBackgroundImage(response.data.board_background_image);
        setCreators(response.data.creators || []);
        setStudents(response.data.students || []);
        setPendingInvitations(response.data.pending_invitations || []);
        setTwoFactorEnabled(response.data.two_factor_enabled || false);
        setUserType(response.data.user_type || '');
        setIsInvited(response.data.is_invited || false);
        setCanViewActivities(response.data.can_view_activities || false);
        setActivitiesHeading(response.data.activities_heading || 'Actividades');
        setAttachmentMaxSizeMb(response.data.attachment_max_size_mb || 10);
        setHasFilters(response.data.has_filters || false);
        setTotalFilteredTasks(response.data.total_filtered_tasks || 0);
        
        // NO actualizar filtros desde la respuesta para evitar sobrescribir los filtros del usuario
        // Los filtros se mantienen en el estado del componente
      } else {
        setError('Error al cargar el tablero');
      }
    } catch (err) {
      if (err.response?.status === 401) {
        navigate('/login');
      } else {
        setError('Error al cargar el tablero: ' + (err.response?.data?.error || err.message));
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Función para actualizar el tablero sin mostrar el estado de carga
  const refreshBoardSilently = async () => {
    try {
      // Usar los filtros actuales
      const filtersToUse = filters;
      const params = {};
      if (filtersToUse.q) params.q = filtersToUse.q;
      if (filtersToUse.creator) params.creator = filtersToUse.creator;
      if (filtersToUse.due_from) params.due_from = filtersToUse.due_from;
      if (filtersToUse.due_to) params.due_to = filtersToUse.due_to;
      
      const response = await kanbanService.getBoard(params);
      if (response.data.success) {
        setLists(response.data.lists || []);
        setUser(response.data.user);
        setCanDelete(response.data.can_delete || false);
        setPreferences(response.data.preferences || {});
        setBoardColors(response.data.board_colors || []);
        setBoardColor(response.data.board_color);
        setBoardBackgroundImage(response.data.board_background_image);
        setCreators(response.data.creators || []);
        setStudents(response.data.students || []);
        setPendingInvitations(response.data.pending_invitations || []);
        setTwoFactorEnabled(response.data.two_factor_enabled || false);
        setUserType(response.data.user_type || '');
        setIsInvited(response.data.is_invited || false);
        setCanViewActivities(response.data.can_view_activities || false);
        setActivitiesHeading(response.data.activities_heading || 'Actividades');
        setAttachmentMaxSizeMb(response.data.attachment_max_size_mb || 10);
        setHasFilters(response.data.has_filters || false);
        setTotalFilteredTasks(response.data.total_filtered_tasks || 0);
      }
    } catch (err) {
      if (err.response?.status === 401) {
        navigate('/login');
      } else {
        // No mostrar error en actualizaciones silenciosas para no interrumpir la experiencia
        console.error('Error al actualizar el tablero:', err);
      }
    }
  };

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    console.log('Submit de filtros - Estado actual:', filters);
    // Verificar si hay filtros activos
    const hasActiveFilters = !!(filters.q || filters.creator || filters.due_from || filters.due_to);
    console.log('Tiene filtros activos:', hasActiveFilters);
    setHasFilters(hasActiveFilters);
    // Cargar el tablero con los filtros del estado actual
    loadBoard();
  };

  const handleClearFilters = () => {
    const clearedFilters = {
      q: '',
      creator: '',
      due_from: '',
      due_to: ''
    };
    setFilters(clearedFilters);
    setHasFilters(false);
    // Pasar los filtros limpios directamente a loadBoard para evitar el problema de estado asíncrono
    loadBoard(clearedFilters);
  };

  const handleCreateList = async (e) => {
    e.preventDefault();
    if (!newListName.trim()) return;
    
    try {
      const response = await kanbanService.createList(newListName.trim());
      if (response.data.success) {
        setNewListName('');
        setShowAddListModal(false);
        loadBoard();
      } else {
        setError(response.data.error || 'Error al crear la lista');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al crear la lista');
    }
  };

  const handleDeleteList = async (listId) => {
    const list = lists.find(l => l.id === listId);
    const taskCount = list?.tasks?.length || 0;
    const message = `¿Estás seguro de que deseas eliminar la lista "${list?.name}"?\n\n` +
                   `Se eliminarán todas las ${taskCount} tarea${taskCount !== 1 ? 's' : ''} y sus subtareas asociadas.\n\n` +
                   `Esta acción no se puede deshacer.`;
    
    if (!window.confirm(message)) {
      return;
    }
    
    try {
      const response = await kanbanService.deleteList(listId);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al eliminar la lista');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al eliminar la lista');
    }
  };

  const handleChangeListColor = async (listId, color) => {
    if (!listId) {
      setError('No se ha seleccionado ninguna lista');
      setShowColorPickerModal(false);
      return;
    }
    
    console.log('Cambiando color de lista:', listId, 'a color:', color);
    
    try {
      const response = await kanbanService.changeListColor(listId, color);
      console.log('Respuesta del servidor:', response.data);
      if (response.data.success) {
        setShowColorPickerModal(false);
        setSelectedListId(null);
        // Recargar el tablero para ver el cambio
        await loadBoard();
      } else {
        setError(response.data.error || 'Error al cambiar el color');
      }
    } catch (err) {
      console.error('Error al cambiar el color:', err);
      setError(err.response?.data?.error || 'Error al cambiar el color: ' + err.message);
      // Cerrar el modal incluso si hay error
      setShowColorPickerModal(false);
      setSelectedListId(null);
    }
  };

  const handleCreateTask = async (e) => {
    e.preventDefault();
    if (!newTaskTitle.trim() || !newTaskListId) return;
    
    try {
      const response = await kanbanService.createTask(newTaskListId, newTaskTitle.trim());
      if (response.data.success) {
        setNewTaskTitle('');
        setNewTaskListId(null);
        setShowAddTaskModal(false);
        loadBoard();
      } else {
        setError(response.data.error || 'Error al crear la tarea');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al crear la tarea');
    }
  };

  const handleEditTask = async (e) => {
    e.preventDefault();
    if (!editingTask || !editingTask.title.trim()) return;
    
    try {
      const response = await kanbanService.updateTask(editingTask.id, {
        title: editingTask.title.trim(),
        due_date: editingTask.due_date || ''
      });
      if (response.data.success) {
        setEditingTask(null);
        setShowEditTaskModal(false);
        loadBoard();
      } else {
        setError(response.data.error || 'Error al actualizar la tarea');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al actualizar la tarea');
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar esta tarea?')) {
      return;
    }
    
    try {
      const response = await kanbanService.deleteTask(taskId);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al eliminar la tarea');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al eliminar la tarea');
    }
  };

  const handleMoveTask = async (taskId, newListId) => {
    if (!newListId) return;
    
    try {
      const response = await kanbanService.moveTask(taskId, newListId);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al mover la tarea');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al mover la tarea');
    }
  };

  const handleUpdateTaskDueDate = async (taskId, dueDate) => {
    try {
      const response = await kanbanService.updateTaskDueDate(taskId, dueDate);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al actualizar la fecha');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al actualizar la fecha');
    }
  };

  const handleCreateSubtask = async (taskId, title) => {
    if (!title.trim()) return;
    
    try {
      const response = await kanbanService.createSubtask(taskId, title.trim());
      if (response.data.success) {
        setShowAddSubtaskModal(false);
        setSelectedTaskId(null);
        loadBoard();
      } else {
        setError(response.data.error || 'Error al crear la subtarea');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al crear la subtarea');
    }
  };

  const handleEditSubtask = async (e) => {
    e.preventDefault();
    if (!editingSubtask || !editingSubtask.title.trim()) return;
    
    try {
      const response = await kanbanService.updateSubtask(editingSubtask.id, {
        title: editingSubtask.title.trim(),
        due_date: editingSubtask.due_date || ''
      });
      if (response.data.success) {
        setEditingSubtask(null);
        setShowEditSubtaskModal(false);
        loadBoard();
      } else {
        setError(response.data.error || 'Error al actualizar la subtarea');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al actualizar la subtarea');
    }
  };

  const handleToggleSubtask = async (subtaskId) => {
    try {
      const response = await kanbanService.toggleSubtask(subtaskId);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al cambiar el estado de la subtarea');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cambiar el estado de la subtarea');
    }
  };

  const handleDeleteSubtask = async (subtaskId) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar esta subtarea?')) {
      return;
    }
    
    try {
      const response = await kanbanService.deleteSubtask(subtaskId);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al eliminar la subtarea');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al eliminar la subtarea');
    }
  };

  const handleUpdateSubtaskDueDate = async (subtaskId, dueDate) => {
    try {
      const response = await kanbanService.updateSubtaskDueDate(subtaskId, dueDate);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al actualizar la fecha');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al actualizar la fecha');
    }
  };

  const toggleSubtasks = (taskId) => {
    const newExpanded = new Set(expandedSubtasks);
    if (newExpanded.has(taskId)) {
      newExpanded.delete(taskId);
    } else {
      newExpanded.add(taskId);
    }
    setExpandedSubtasks(newExpanded);
  };

  const loadActivities = async () => {
    try {
      const response = await kanbanService.getActivities();
      if (response.data.success) {
        setActivities(response.data.activities || []);
      }
    } catch (err) {
      console.error('Error al cargar actividades:', err);
    }
  };

  const handleInviteStudent = async () => {
    if (!selectedStudentId) {
      setError('Selecciona un estudiante');
      return;
    }
    
    try {
      const response = await kanbanService.inviteStudent(parseInt(selectedStudentId));
      if (response.data.success) {
        setSelectedStudentId('');
        setShowInviteModal(false);
        loadBoard();
      } else {
        setError(response.data.error || 'Error al enviar la invitación');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al enviar la invitación');
    }
  };

  const handleAcceptInvitation = async (invitationId) => {
    try {
      const response = await kanbanService.acceptInvitation(invitationId);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al aceptar la invitación');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al aceptar la invitación');
    }
  };

  const handleRejectInvitation = async (invitationId) => {
    try {
      const response = await kanbanService.rejectInvitation(invitationId);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al rechazar la invitación');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al rechazar la invitación');
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    if (!newUserData.username || !newUserData.email || !newUserData.password) {
      setError('Todos los campos son obligatorios');
      return;
    }
    
    try {
      const response = await kanbanService.createUser(newUserData);
      if (response.data.success) {
        setNewUserData({
          username: '',
          email: '',
          password: '',
          role: 'student'
        });
        setShowCreateUserModal(false);
        loadBoard();
        alert('Usuario creado exitosamente');
      } else {
        setError(response.data.error || 'Error al crear el usuario');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al crear el usuario');
    }
  };

  const handleChangeBoardColor = async (color) => {
    try {
      const response = await kanbanService.changeBoardColor(color);
      if (response.data.success) {
        setShowBoardColorModal(false);
        loadBoard();
      } else {
        setError(response.data.error || 'Error al cambiar el color del tablero');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cambiar el color del tablero');
    }
  };

  const handleUploadBoardBackground = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validar tamaño (4MB máximo)
    if (file.size > 4 * 1024 * 1024) {
      setError('El archivo es demasiado grande. Máximo 4MB.');
      return;
    }
    
    // Validar formato
    const validFormats = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validFormats.includes(file.type)) {
      setError('Formato no válido. Solo se admiten JPG, PNG y WEBP.');
      return;
    }
    
    try {
      const response = await kanbanService.uploadBoardBackground(file);
      if (response.data.success) {
        setShowBoardColorModal(false);
        loadBoard();
      } else {
        setError(response.data.error || 'Error al subir la imagen');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al subir la imagen');
    }
  };

  const handleUploadTaskAttachment = async (taskId, file) => {
    try {
      const response = await kanbanService.uploadTaskAttachment(taskId, file);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al subir el archivo');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al subir el archivo');
    }
  };

  const handleUploadSubtaskAttachment = async (subtaskId, file) => {
    try {
      const response = await kanbanService.uploadSubtaskAttachment(subtaskId, file);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al subir el archivo');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al subir el archivo');
    }
  };

  const handleDeleteTaskAttachment = async (attachmentId) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar este archivo?')) {
      return;
    }
    
    try {
      const response = await kanbanService.deleteTaskAttachment(attachmentId);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al eliminar el archivo');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al eliminar el archivo');
    }
  };

  const handleDeleteSubtaskAttachment = async (attachmentId) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar este archivo?')) {
      return;
    }
    
    try {
      const response = await kanbanService.deleteSubtaskAttachment(attachmentId);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al eliminar el archivo');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al eliminar el archivo');
    }
  };

  const handleAddActivityComment = async (activityId, comment) => {
    if (!comment.trim()) return;
    
    try {
      const response = await kanbanService.addActivityComment(activityId, comment);
      if (response.data.success) {
        loadActivities();
      } else {
        setError(response.data.error || 'Error al agregar el comentario');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al agregar el comentario');
    }
  };

  // Funciones para drag & drop de listas
  const handleListDragStart = (e, listId) => {
    // Solo permitir drag si no hay una tarea siendo arrastrada
    if (draggedTask || draggedSubtask) {
      e.preventDefault();
      return;
    }
    console.log('🔄 Lista drag start:', listId);
    setDraggedList(listId);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', `list-${listId}`); // Identificador único para listas
    e.currentTarget.style.opacity = '0.5';
    e.currentTarget.classList.add('dragging');
  };

  const handleListDragEnd = (e) => {
    e.currentTarget.style.opacity = '1';
    e.currentTarget.classList.remove('dragging');
    // Limpiar el estado después de un pequeño delay para permitir que el drop se procese
    setTimeout(() => {
      setDraggedList(null);
    }, 100);
  };

  const handleListDragOver = (e, listId) => {
    // Solo permitir drop si se está arrastrando una lista (no una tarea)
    if (draggedList && !draggedTask && !draggedSubtask) {
      e.preventDefault();
      e.stopPropagation();
      e.dataTransfer.dropEffect = 'move';
      e.currentTarget.classList.add('drag-over');
    }
  };

  const handleListDragLeave = (e) => {
    e.currentTarget.classList.remove('drag-over');
  };

  const handleListDrop = async (e, targetListId) => {
    e.preventDefault();
    e.stopPropagation();
    
    console.log('📦 Lista drop en:', targetListId, 'Lista arrastrada:', draggedList);
    
    // Solo procesar si se está arrastrando una lista (no una tarea)
    if (!draggedList || draggedList === targetListId || draggedTask || draggedSubtask) {
      console.log('❌ Drop cancelado - condiciones no cumplidas');
      setDraggedList(null);
      e.currentTarget.classList.remove('drag-over');
      return;
    }
    
    // Usar el estado actual de las listas para calcular el nuevo orden
    const currentListIds = lists.map(list => list.id);
    console.log('📋 Orden actual de listas:', currentListIds);
    
    const draggedIndex = currentListIds.indexOf(draggedList);
    const targetIndex = currentListIds.indexOf(targetListId);
    
    if (draggedIndex === -1 || targetIndex === -1) {
      console.log('❌ Índices no encontrados - draggedIndex:', draggedIndex, 'targetIndex:', targetIndex);
      setDraggedList(null);
      e.currentTarget.classList.remove('drag-over');
      return;
    }
    
    // Calcular la posición del mouse para determinar si va antes o después
    const targetElement = e.currentTarget;
    const rect = targetElement.getBoundingClientRect();
    const mouseX = e.clientX;
    const listMiddle = rect.left + rect.width / 2;
    
    // Crear nuevo orden
    const newListIds = [...currentListIds];
    
    // Remover el elemento arrastrado de su posición actual
    newListIds.splice(draggedIndex, 1);
    
    // Calcular la nueva posición de inserción
    let insertIndex = targetIndex;
    if (draggedIndex < targetIndex) {
      // Si se mueve hacia la derecha, el índice objetivo se reduce en 1
      insertIndex = targetIndex;
    } else {
      // Si se mueve hacia la izquierda, mantener el índice objetivo
      insertIndex = targetIndex;
    }
    
    // Ajustar según la posición del mouse
    if (mouseX < listMiddle && draggedIndex > targetIndex) {
      insertIndex = targetIndex;
    } else if (mouseX >= listMiddle && draggedIndex < targetIndex) {
      insertIndex = targetIndex + 1;
    }
    
    // Insertar en la nueva posición
    newListIds.splice(insertIndex, 0, draggedList);
    
    console.log('✅ Nuevo orden de listas:', newListIds);
    
    try {
      const response = await kanbanService.reorderLists(newListIds);
      console.log('📡 Respuesta del servidor:', response.data);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al reordenar las listas');
      }
    } catch (err) {
      console.error('❌ Error al reordenar listas:', err);
      setError(err.response?.data?.error || 'Error al reordenar las listas');
    }
    
    e.currentTarget.classList.remove('drag-over');
    setDraggedList(null);
  };

  // Funciones para drag & drop de tareas
  const handleTaskDragStart = (e, taskId, listId) => {
    // Solo permitir drag si no hay una lista siendo arrastrada
    if (draggedList) {
      e.preventDefault();
      return;
    }
    setDraggedTask({ id: taskId, listId });
    setDraggedFromList(listId);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', `task-${taskId}`); // Identificador único para tareas
    e.currentTarget.classList.add('dragging');
  };

  const handleTaskDragEnd = (e) => {
    e.currentTarget.classList.remove('dragging');
    // Limpiar el estado después de un pequeño delay para permitir que el drop se procese
    setTimeout(() => {
      setDraggedTask(null);
      setDraggedFromList(null);
    }, 100);
  };

  const handleTaskDragOver = (e, listId) => {
    if (draggedTask) {
      e.preventDefault(); // Necesario para permitir el drop
      e.stopPropagation();
      e.dataTransfer.dropEffect = 'move';
      e.currentTarget.classList.add('drag-over');
    }
  };

  const handleTaskDrop = async (e, targetListId) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!draggedTask) {
      setDraggedTask(null);
      setDraggedFromList(null);
      return;
    }
    
    const listElement = document.querySelector(`.list-cards[data-list-id="${targetListId}"]`);
    if (!listElement) {
      setDraggedTask(null);
      setDraggedFromList(null);
      return;
    }
    
    const taskElements = Array.from(listElement.querySelectorAll('.draggable-task'));
    
    // Si la tarea se movió a otra lista, usar moveTask
    if (draggedFromList !== targetListId) {
      try {
        const response = await kanbanService.moveTask(draggedTask.id, targetListId);
        if (response.data.success) {
          refreshBoardSilently();
        } else {
          setError(response.data.error || 'Error al mover la tarea');
        }
      } catch (err) {
        setError(err.response?.data?.error || 'Error al mover la tarea');
      }
      setDraggedTask(null);
      setDraggedFromList(null);
      return;
    }
    
    // Si está en la misma lista, reordenar
    // Excluir la tarea arrastrada del cálculo del orden
    const taskIds = taskElements
      .filter(el => parseInt(el.dataset.taskId) !== draggedTask.id)
      .map(el => parseInt(el.dataset.taskId));
    
    // Encontrar la posición donde se soltó
    const afterElement = taskElements.find(el => {
      const rect = el.getBoundingClientRect();
      return e.clientY < rect.top + rect.height / 2 && parseInt(el.dataset.taskId) !== draggedTask.id;
    });
    
    if (afterElement) {
      const insertIndex = taskIds.indexOf(parseInt(afterElement.dataset.taskId));
      taskIds.splice(insertIndex, 0, draggedTask.id);
    } else {
      // Si no se encontró, agregar al final
      taskIds.push(draggedTask.id);
    }
    
    try {
      const response = await kanbanService.reorderTasks(targetListId, taskIds);
      if (response.data.success) {
        refreshBoardSilently();
      } else {
        setError(response.data.error || 'Error al reordenar las tareas');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al reordenar las tareas');
    }
    
    setDraggedTask(null);
    setDraggedFromList(null);
  };

  // Funciones para drag & drop de subtareas
  const handleSubtaskDragStart = (e, subtaskId, taskId) => {
    setDraggedSubtask({ id: subtaskId, taskId });
    e.dataTransfer.effectAllowed = 'move';
    e.currentTarget.classList.add('dragging');
  };

  const handleSubtaskDragEnd = (e) => {
    e.currentTarget.classList.remove('dragging');
    setDraggedSubtask(null);
  };

  const handleSubtaskDragOver = (e) => {
    if (draggedSubtask) {
      e.preventDefault();
      e.stopPropagation();
      e.dataTransfer.dropEffect = 'move';
    }
  };

  const handleSubtaskDrop = async (e, targetTaskId) => {
    e.preventDefault();
    e.stopPropagation();
    if (!draggedSubtask) {
      setDraggedSubtask(null);
      return;
    }
    
    const subtaskList = document.querySelector(`.subtasks-list[data-task-id="${targetTaskId}"]`);
    if (!subtaskList) {
      setDraggedSubtask(null);
      return;
    }
    
    const subtaskElements = Array.from(subtaskList.querySelectorAll('.draggable-subtask'));
    
    // Excluir la subtarea arrastrada del cálculo del orden
    const subtaskIds = subtaskElements
      .filter(el => parseInt(el.dataset.subtaskId) !== draggedSubtask.id)
      .map(el => parseInt(el.dataset.subtaskId));
    
    // Encontrar la posición donde se soltó
    const afterElement = subtaskElements.find(el => {
      const rect = el.getBoundingClientRect();
      return e.clientY < rect.top + rect.height / 2 && parseInt(el.dataset.subtaskId) !== draggedSubtask.id;
    });
    
    if (afterElement) {
      const insertIndex = subtaskIds.indexOf(parseInt(afterElement.dataset.subtaskId));
      subtaskIds.splice(insertIndex, 0, draggedSubtask.id);
    } else {
      // Si no se encontró, agregar al final
      subtaskIds.push(draggedSubtask.id);
    }
    
    try {
      const response = await kanbanService.reorderSubtasks(targetTaskId, subtaskIds);
      if (response.data.success) {
        loadBoard();
      } else {
        setError(response.data.error || 'Error al reordenar las subtareas');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al reordenar las subtareas');
    }
    
    setDraggedSubtask(null);
  };

  const openAddTaskModal = (listId) => {
    setNewTaskListId(listId);
    setShowAddTaskModal(true);
  };

  const openEditTaskModal = (task) => {
    setEditingTask({ ...task });
    setShowEditTaskModal(true);
  };

  const openEditSubtaskModal = (subtask) => {
    setEditingSubtask({ ...subtask });
    setShowEditSubtaskModal(true);
  };

  const openAddSubtaskModal = (taskId) => {
    setSelectedTaskId(taskId);
    setShowAddSubtaskModal(true);
  };

  // Aplicar estilos al body cuando se monta el componente
  // IMPORTANTE: Este useEffect debe estar ANTES de cualquier return condicional
  useEffect(() => {
    // Calcular color de overlay (si hay un color de tablero personalizado)
    const overlayColor = boardColor ? `rgba(${parseInt(boardColor.slice(1, 3), 16)}, ${parseInt(boardColor.slice(3, 5), 16)}, ${parseInt(boardColor.slice(5, 7), 16)}, 0.65)` : 'transparent';
    
    // Aplicar clase y estilos al body
    // El fondo con patrón se aplica automáticamente mediante CSS
    document.body.classList.add('board-page');
    document.body.style.setProperty('--board-overlay-color', overlayColor);
    
    // Limpiar al desmontar
    return () => {
      document.body.classList.remove('board-page');
      document.body.style.removeProperty('--board-overlay-color');
    };
  }, [boardColor]);

  const boardStyle = {
    '--board-overlay-color': boardColor ? `rgba(${parseInt(boardColor.slice(1, 3), 16)}, ${parseInt(boardColor.slice(3, 5), 16)}, ${parseInt(boardColor.slice(5, 7), 16)}, 0.65)` : 'transparent'
  };

  if (loading) {
    return (
      <div className="board-container">
        <div className="loading">Cargando tablero...</div>
      </div>
    );
  }

  return (
    <div className="board-container" style={boardStyle}>
      <div className="board-header">
        <h1>Tablero Kanban</h1>
        <div className="user-info">
          <span>Usuario: {user?.username} - <strong>{userType}</strong>{isInvited && ' (Invitado)'}</span>
          {canDelete && (
            <>
              <button className="btn-invite" onClick={() => setShowInviteModal(true)} title="Invitar Estudiantes">
                📧 Invitar
              </button>
              <button className="btn-create-user" onClick={() => setShowCreateUserModal(true)} title="Crear Usuario">
                ➕ Usuario
              </button>
              <button className="btn-board-color" onClick={() => setShowBoardColorModal(true)} title="Cambiar color del tablero">
                🎨 Color
              </button>
              <Link to="/calendar" className="btn-calendar" title="Ver calendario">📅 Calendario</Link>
              <Link to="/logs" className="btn-calendar" title="Ver registros del sistema">🪵 Logs</Link>
            </>
          )}
          <Link to="/two-factor/setup/" className="btn-calendar" title="Configurar autenticación de dos pasos">
            🔐 2FA{twoFactorEnabled ? ' (Activo)' : ' (Inactivo)'}
          </Link>
          {canViewActivities && (
            <button className="btn-activities" onClick={() => { loadActivities(); setShowActivitiesModal(true); }} title="Ver Actividades">
              📋 Actividades
            </button>
          )}
          {pendingInvitations.length > 0 && (
            <button className="btn-invitations" onClick={() => setShowInvitationsModal(true)} title="Ver Invitaciones">
              📬 Invitaciones ({pendingInvitations.length})
            </button>
          )}
          <a href="/logout/" className="btn-logout" title="Cerrar sesión">Cerrar Sesión</a>
        </div>
      </div>

      {/* Filtros */}
      <form className="board-filters" onSubmit={handleFilterSubmit}>
        <div className="filter-row">
          <div className="filter-group">
            <label htmlFor="filter-q">Buscar tarea</label>
            <input
              id="filter-q"
              type="text"
              name="q"
              value={filters.q}
              onChange={(e) => setFilters({...filters, q: e.target.value})}
              placeholder="Nombre de la tarea"
            />
          </div>
          <div className="filter-group">
            <label htmlFor="filter-creator">Responsable</label>
            <select
              id="filter-creator"
              name="creator"
              value={filters.creator}
              onChange={(e) => setFilters({...filters, creator: e.target.value})}
            >
              <option value="">Todos</option>
              <option value="none">Sin responsable</option>
              {creators.map(creator => (
                <option key={creator.id} value={creator.id}>{creator.username}</option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label htmlFor="filter-due-from">Vence desde</label>
            <input
              id="filter-due-from"
              type="date"
              name="due_from"
              value={filters.due_from}
              onChange={(e) => setFilters({...filters, due_from: e.target.value})}
            />
          </div>
          <div className="filter-group">
            <label htmlFor="filter-due-to">Vence hasta</label>
            <input
              id="filter-due-to"
              type="date"
              name="due_to"
              value={filters.due_to}
              onChange={(e) => setFilters({...filters, due_to: e.target.value})}
            />
          </div>
          <div className="filter-actions">
            <button type="submit" className="btn-filter">Filtrar</button>
            {hasFilters && (
              <button type="button" className="btn-clear-filter" onClick={handleClearFilters}>Limpiar</button>
            )}
          </div>
        </div>
        {hasFilters && (
          <p className="filter-summary">Resultados: {totalFilteredTasks} tarea{totalFilteredTasks !== 1 ? 's' : ''}</p>
        )}
      </form>

      {hasFilters && totalFilteredTasks === 0 && (
        <div className="filter-empty">No se encontraron tareas con los filtros seleccionados.</div>
      )}

      <div className="board-lists" id="board-lists" ref={boardListsRef}>
        {lists.map(list => (
          <div
            key={list.id}
            className={`list-column list-${list.color} draggable-list`}
            data-list-id={list.id}
            onDragOver={(e) => handleListDragOver(e, list.id)}
            onDragLeave={handleListDragLeave}
            onDrop={(e) => handleListDrop(e, list.id)}
          >
            <div
              className="list-header draggable-list-header"
              draggable="true"
              onDragStart={(e) => handleListDragStart(e, list.id)}
              onDragEnd={handleListDragEnd}
            >
              <h2 className={`list-title list-title-${list.color}`}>
                {list.name}
                {list.created_by_username && (
                  <span className="creator-tag">- {list.created_by_username}</span>
                )}
              </h2>
              <div className="list-actions">
                <span className="icon-resize">⇄</span>
                <button
                  className="btn-menu-list"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setSelectedListId(list.id);
                    setShowColorPickerModal(true);
                  }}
                  title="Cambiar Color"
                >
                  <span className="icon-paintbrush">🖌️</span>
                </button>
                {canDelete && (
                  <button
                    className="btn-delete-list"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleDeleteList(list.id);
                    }}
                    title="Eliminar Lista"
                  >
                    <span className="icon-delete">✕</span>
                  </button>
                )}
              </div>
            </div>

            <div
              className="list-cards"
              data-list-id={list.id}
              onDragOver={(e) => {
                // Solo procesar si se está arrastrando una tarea, no una lista
                if (draggedTask && !draggedList) {
                  e.preventDefault();
                  handleTaskDragOver(e, list.id);
                } else if (draggedList) {
                  // Si se está arrastrando una lista, prevenir el drop de tareas
                  e.stopPropagation();
                }
              }}
              onDrop={(e) => {
                // Solo procesar si se está arrastrando una tarea, no una lista
                if (draggedTask && !draggedList) {
                  e.preventDefault();
                  e.stopPropagation();
                  handleTaskDrop(e, list.id);
                } else if (draggedList) {
                  // Si se está arrastrando una lista, prevenir el drop de tareas
                  e.stopPropagation();
                }
              }}
            >
              <div
                className="tasks-container"
                data-list-id={list.id}
                onDragOver={(e) => {
                  // Solo procesar si se está arrastrando una tarea, no una lista
                  if (draggedTask && !draggedList) {
                    e.preventDefault();
                    e.stopPropagation();
                    handleTaskDragOver(e, list.id);
                  } else if (draggedList) {
                    // Si se está arrastrando una lista, prevenir el drop de tareas
                    e.stopPropagation();
                  }
                }}
                onDrop={(e) => {
                  // Solo procesar si se está arrastrando una tarea, no una lista
                  if (draggedTask && !draggedList) {
                    e.preventDefault();
                    e.stopPropagation();
                    handleTaskDrop(e, list.id);
                  } else if (draggedList) {
                    // Si se está arrastrando una lista, prevenir el drop de tareas
                    e.stopPropagation();
                  }
                }}
              >
                {(() => {
                  // Si hay filtros activos, usar filtered_tasks (incluso si está vacío)
                  // Si no hay filtros, usar tasks normales
                  const tasksToShow = hasFilters 
                    ? (list.filtered_tasks || [])
                    : (list.tasks || []);
                  
                  return tasksToShow.length > 0 ? (
                    tasksToShow.map(task => (
                    <TaskCard
                      key={task.id}
                      task={task}
                      lists={lists}
                      canDelete={canDelete}
                      attachmentMaxSizeMb={attachmentMaxSizeMb}
                      expandedSubtasks={expandedSubtasks}
                      onToggleSubtasks={toggleSubtasks}
                      onEditTask={openEditTaskModal}
                      onDeleteTask={handleDeleteTask}
                      onMoveTask={handleMoveTask}
                      onUpdateTaskDueDate={handleUpdateTaskDueDate}
                      onCreateSubtask={handleCreateSubtask}
                      onEditSubtask={openEditSubtaskModal}
                      onToggleSubtask={handleToggleSubtask}
                      onDeleteSubtask={handleDeleteSubtask}
                      onUpdateSubtaskDueDate={handleUpdateSubtaskDueDate}
                      onUploadTaskAttachment={handleUploadTaskAttachment}
                      onUploadSubtaskAttachment={handleUploadSubtaskAttachment}
                      onDeleteTaskAttachment={handleDeleteTaskAttachment}
                      onDeleteSubtaskAttachment={handleDeleteSubtaskAttachment}
                      onSubtaskDragStart={handleSubtaskDragStart}
                      onSubtaskDragEnd={handleSubtaskDragEnd}
                      onSubtaskDragOver={handleSubtaskDragOver}
                      onSubtaskDrop={handleSubtaskDrop}
                      onTaskDragStart={handleTaskDragStart}
                      onTaskDragEnd={handleTaskDragEnd}
                      onAddSubtask={openAddSubtaskModal}
                    />
                    ))
                  ) : (
                    <div className="tasks-empty">{hasFilters ? 'Sin coincidencias' : 'No hay tareas'}</div>
                  );
                })()}
              </div>

              <button
                className={`btn-add-card btn-add-card-${list.color}`}
                onClick={() => openAddTaskModal(list.id)}
              >
                <span className="icon-plus">+</span>
                <span className="btn-text">Añade una tarjeta</span>
                <span className="icon-screen">🖥</span>
              </button>
            </div>
          </div>
        ))}

        <button className="btn-add-list" onClick={() => setShowAddListModal(true)}>
          <span className="icon-plus">+</span>
          <span className="btn-text">Añade otra lista</span>
        </button>
      </div>

      {/* Modales */}
      <AddListModal
        show={showAddListModal}
        onClose={() => setShowAddListModal(false)}
        onSubmit={handleCreateList}
        listName={newListName}
        onListNameChange={setNewListName}
      />

      <AddTaskModal
        show={showAddTaskModal}
        onClose={() => setShowAddTaskModal(false)}
        onSubmit={handleCreateTask}
        taskTitle={newTaskTitle}
        onTaskTitleChange={setNewTaskTitle}
      />

      <EditTaskModal
        show={showEditTaskModal}
        onClose={() => setShowEditTaskModal(false)}
        onSubmit={handleEditTask}
        task={editingTask}
        onTaskChange={setEditingTask}
      />

      <EditSubtaskModal
        show={showEditSubtaskModal}
        onClose={() => setShowEditSubtaskModal(false)}
        onSubmit={handleEditSubtask}
        subtask={editingSubtask}
        onSubtaskChange={setEditingSubtask}
      />

      <ColorPickerModal
        show={showColorPickerModal}
        onClose={() => {
          setShowColorPickerModal(false);
          setSelectedListId(null);
        }}
        onSelectColor={(color) => {
          if (selectedListId) {
            handleChangeListColor(selectedListId, color);
          } else {
            console.error('No hay lista seleccionada');
            setError('No se ha seleccionado ninguna lista');
          }
        }}
        selectedListId={selectedListId}
        lists={lists}
      />

      <ActivitiesModal
        show={showActivitiesModal}
        onClose={() => setShowActivitiesModal(false)}
        activities={activities}
        heading={activitiesHeading}
        onAddComment={handleAddActivityComment}
      />

      <InviteModal
        show={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        students={students}
        selectedStudentId={selectedStudentId}
        onStudentIdChange={setSelectedStudentId}
        onSubmit={handleInviteStudent}
      />

      <InvitationsModal
        show={showInvitationsModal}
        onClose={() => setShowInvitationsModal(false)}
        invitations={pendingInvitations}
        onAccept={handleAcceptInvitation}
        onReject={handleRejectInvitation}
      />

      <CreateUserModal
        show={showCreateUserModal}
        onClose={() => setShowCreateUserModal(false)}
        userData={newUserData}
        onUserDataChange={setNewUserData}
        onSubmit={handleCreateUser}
      />

      <BoardColorModal
        show={showBoardColorModal}
        onClose={() => {
          setShowBoardColorModal(false);
          setError(''); // Limpiar errores al cerrar
        }}
        boardColors={boardColors}
        onSelectColor={handleChangeBoardColor}
        onUploadBackground={handleUploadBoardBackground}
      />

      <AddSubtaskModal
        show={showAddSubtaskModal}
        onClose={() => setShowAddSubtaskModal(false)}
        taskId={selectedTaskId}
        onSubmit={(title) => handleCreateSubtask(selectedTaskId, title)}
      />

      {error && (
        <div className="error" onClick={() => setError('')}>
          {error} <span style={{float: 'right', cursor: 'pointer'}}>×</span>
        </div>
      )}

      {/* Contenedor para notificaciones en tiempo real */}
      <div id="notifications-container" className="notifications-container"></div>
    </div>
  );
}

// Componente TaskCard
function TaskCard({
  task,
  lists,
  canDelete,
  attachmentMaxSizeMb,
  expandedSubtasks,
  onToggleSubtasks,
  onEditTask,
  onDeleteTask,
  onMoveTask,
  onUpdateTaskDueDate,
  onCreateSubtask,
  onEditSubtask,
  onToggleSubtask,
  onDeleteSubtask,
  onUpdateSubtaskDueDate,
  onUploadTaskAttachment,
  onUploadSubtaskAttachment,
  onDeleteTaskAttachment,
  onDeleteSubtaskAttachment,
  onSubtaskDragStart,
  onSubtaskDragEnd,
  onSubtaskDragOver,
  onSubtaskDrop,
  onTaskDragStart,
  onTaskDragEnd,
  onAddSubtask
}) {
  const isExpanded = expandedSubtasks.has(task.id);
  const taskAttachmentInputRef = useRef(null);

  const handleAttachmentClick = (taskId) => {
    const input = document.getElementById(`task-attachment-input-${taskId}`);
    if (input) input.click();
  };

  const handleAttachmentChange = (e, taskId) => {
    const files = Array.from(e.target.files);
    files.forEach(file => {
      onUploadTaskAttachment(taskId, file);
    });
    e.target.value = '';
  };

  return (
    <div
      className="card draggable-task"
      draggable="true"
      data-task-id={task.id}
      data-list-id={task.list}
      onDragStart={(e) => onTaskDragStart(e, task.id, task.list)}
      onDragEnd={onTaskDragEnd}
    >
      <div className="card-content">
        <span className="card-title" onClick={() => onEditTask(task)} style={{ cursor: 'pointer' }}>
          {task.title}
          {task.created_by_username && (
            <span className="creator-tag">- {task.created_by_username}</span>
          )}
        </span>
      </div>

      <div className="task-meta">
        <label className="due-date-label">Vence:</label>
        <input
          type="date"
          className="due-date-input"
          value={task.due_date ? task.due_date.split('T')[0] : ''}
          onChange={(e) => onUpdateTaskDueDate(task.id, e.target.value)}
        />
      </div>

      <AttachmentsSection
        attachments={task.attachments || []}
        maxSizeMb={attachmentMaxSizeMb}
        canDelete={canDelete}
        onUploadClick={() => handleAttachmentClick(task.id)}
        onDelete={onDeleteTaskAttachment}
      />
      <input
        type="file"
        id={`task-attachment-input-${task.id}`}
        className="attachment-input"
        onChange={(e) => handleAttachmentChange(e, task.id)}
        multiple
        hidden
      />

      <div className="card-actions">
        <button className="btn-card-edit" onClick={() => onEditTask(task)} title="Editar">
          ✏️
        </button>
        {canDelete && (
          <button className="btn-card-delete" onClick={() => onDeleteTask(task.id)} title="Eliminar">
            🗑️
          </button>
        )}
      </div>

      <SubtasksSection
        task={task}
        isExpanded={isExpanded}
        canDelete={canDelete}
        attachmentMaxSizeMb={attachmentMaxSizeMb}
        onToggle={onToggleSubtasks}
        onEdit={onEditSubtask}
        onToggleSubtask={onToggleSubtask}
        onDelete={onDeleteSubtask}
        onUpdateDueDate={onUpdateSubtaskDueDate}
        onUploadAttachment={onUploadSubtaskAttachment}
        onDeleteAttachment={onDeleteSubtaskAttachment}
        onDragStart={onSubtaskDragStart}
        onDragEnd={onSubtaskDragEnd}
        onDragOver={onSubtaskDragOver}
        onDrop={onSubtaskDrop}
        onAddSubtask={onAddSubtask}
      />

      {lists.length > 1 && (
        <div className="task-move">
          <select
            value=""
            onChange={(e) => {
              if (e.target.value) {
                onMoveTask(task.id, parseInt(e.target.value));
                e.target.value = '';
              }
            }}
            className="move-select"
          >
            <option value="">Mover a...</option>
            {lists.filter(l => l.id !== task.list).map(otherList => (
              <option key={otherList.id} value={otherList.id}>
                {otherList.name}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}

// Componente AttachmentsSection
function AttachmentsSection({ attachments, maxSizeMb, canDelete, onUploadClick, onDelete }) {
  return (
    <div className="attachments-section">
      <div className="attachments-header">
        <span className="attachments-title">
          📎 Archivos (<span className="attachments-count">{attachments.length}</span>)
        </span>
        <div className="attachments-actions">
          <span className="attachment-hint">Máx {maxSizeMb} MB</span>
          <button className="btn-attachment-upload" onClick={onUploadClick} title="Adjuntar archivo">
            Adjuntar
          </button>
        </div>
      </div>
      <ul className="attachments-list">
        {attachments.length > 0 ? (
          attachments.map(attachment => (
            <li key={attachment.id} className="attachment-item">
              <div className="attachment-info">
                <a href={attachment.file_url} target="_blank" rel="noopener noreferrer" className="attachment-link">
                  {attachment.filename}
                </a>
                <span className="attachment-meta">
                  por {attachment.uploaded_by_username || 'Administrador'}
                  · {new Date(attachment.uploaded_at).toLocaleString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              {canDelete && (
                <button className="btn-attachment-delete" onClick={() => onDelete(attachment.id)} title="Eliminar adjunto">
                  ✕
                </button>
              )}
            </li>
          ))
        ) : (
          <li className="attachment-empty">No hay archivos adjuntos</li>
        )}
      </ul>
    </div>
  );
}

// Componente SubtasksSection
function SubtasksSection({
  task,
  isExpanded,
  canDelete,
  attachmentMaxSizeMb,
  onToggle,
  onEdit,
  onToggleSubtask,
  onDelete,
  onUpdateDueDate,
  onUploadAttachment,
  onDeleteAttachment,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDrop,
  onAddSubtask
}) {
  const subtaskAttachmentInputRefs = useRef({});

  const handleSubtaskAttachmentClick = (subtaskId) => {
    const input = document.getElementById(`subtask-attachment-input-${subtaskId}`);
    if (input) input.click();
  };

  const handleSubtaskAttachmentChange = (e, subtaskId) => {
    const files = Array.from(e.target.files);
    files.forEach(file => {
      onUploadAttachment(subtaskId, file);
    });
    e.target.value = '';
  };

  return (
    <div className="subtasks-section">
      <div className="subtasks-header" onClick={() => onToggle(task.id)}>
        <span className="subtasks-title">
          Subtareas (<span className="subtasks-count">{task.subtasks?.length || 0}</span>)
        </span>
        {task.created_by_username && (
          <span className="creator-tag">- {task.created_by_username}</span>
        )}
        <span className="subtasks-toggle">{isExpanded ? '▲' : '▼'}</span>
      </div>
      {isExpanded && (
        <div
          className="subtasks-list"
          data-task-id={task.id}
          onDragOver={onDragOver}
          onDrop={(e) => onDrop(e, task.id)}
        >
          {task.subtasks && task.subtasks.length > 0 ? (
            task.subtasks.map(subtask => (
              <div
                key={subtask.id}
                className="subtask-item draggable-subtask"
                draggable="true"
                data-subtask-id={subtask.id}
                data-task-id={task.id}
                onDragStart={(e) => onDragStart(e, subtask.id, task.id)}
                onDragEnd={onDragEnd}
              >
                <div className="subtask-main">
                  <input
                    type="checkbox"
                    className="subtask-checkbox"
                    checked={subtask.completed}
                    onChange={() => onToggleSubtask(subtask.id)}
                  />
                  <span
                    className={`subtask-title ${subtask.completed ? 'completed' : ''}`}
                    onClick={() => onEdit(subtask)}
                    style={{ cursor: 'pointer' }}
                  >
                    {subtask.title}
                    {subtask.created_by_username && (
                      <span className="creator-tag">- {subtask.created_by_username}</span>
                    )}
                  </span>
                  {canDelete && (
                    <button className="btn-subtask-delete" onClick={() => onDelete(subtask.id)} title="Eliminar subtarea">
                      🗑️
                    </button>
                  )}
                </div>
                <div className="subtask-meta">
                  <label className="due-date-label">Vence:</label>
                  <input
                    type="date"
                    className="due-date-input"
                    value={subtask.due_date ? subtask.due_date.split('T')[0] : ''}
                    onChange={(e) => onUpdateDueDate(subtask.id, e.target.value)}
                  />
                </div>
                <div className="subtask-attachments">
                  <div className="subtask-attachments-header">
                    <span className="attachments-title">📎 Adjuntos ({subtask.attachments?.length || 0})</span>
                    <div className="attachments-actions">
                      <span className="attachment-hint">Máx {attachmentMaxSizeMb} MB</span>
                      <button
                        className="btn-attachment-upload"
                        onClick={() => handleSubtaskAttachmentClick(subtask.id)}
                        title="Adjuntar archivo a la subtarea"
                      >
                        Adjuntar
                      </button>
                    </div>
                  </div>
                  <input
                    type="file"
                    id={`subtask-attachment-input-${subtask.id}`}
                    className="attachment-input"
                    onChange={(e) => handleSubtaskAttachmentChange(e, subtask.id)}
                    multiple
                    hidden
                  />
                  <ul className="attachments-list attachments-list-compact">
                    {subtask.attachments && subtask.attachments.length > 0 ? (
                      subtask.attachments.map(attachment => (
                        <li key={attachment.id} className="attachment-item">
                          <div className="attachment-info">
                            <a href={attachment.file_url} target="_blank" rel="noopener noreferrer" className="attachment-link">
                              {attachment.filename}
                            </a>
                            <span className="attachment-meta">
                              por {attachment.uploaded_by_username || 'Administrador'}
                              · {new Date(attachment.uploaded_at).toLocaleString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          {canDelete && (
                            <button className="btn-attachment-delete" onClick={() => onDeleteAttachment(attachment.id)} title="Eliminar adjunto">
                              ✕
                            </button>
                          )}
                        </li>
                      ))
                    ) : (
                      <li className="attachment-empty">Sin adjuntos</li>
                    )}
                  </ul>
                </div>
              </div>
            ))
          ) : (
            <div className="subtask-empty">No hay subtareas</div>
          )}
          <button className="btn-add-subtask" onClick={() => onAddSubtask(task.id)}>
            + Añadir subtarea
          </button>
        </div>
      )}
    </div>
  );
}

// Componentes de Modales
function Modal({ children, onClose, show }) {
  if (!show) return null;
  
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <span className="modal-close" onClick={onClose}>&times;</span>
        {children}
      </div>
    </div>
  );
}

function AddListModal({ show, onClose, onSubmit, listName, onListNameChange }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(e);
  };

  return (
    <Modal show={show} onClose={onClose}>
      <h3>Añadir Nueva Lista</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Nombre de la lista:</label>
          <input
            type="text"
            value={listName}
            onChange={(e) => onListNameChange(e.target.value)}
            required
            autoFocus
          />
        </div>
        <div className="form-actions">
          <button type="submit" className="btn-submit">Añadir</button>
          <button type="button" className="btn-cancel" onClick={onClose}>Cancelar</button>
        </div>
      </form>
    </Modal>
  );
}

function AddTaskModal({ show, onClose, onSubmit, taskTitle, onTaskTitleChange }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(e);
  };

  return (
    <Modal show={show} onClose={onClose}>
      <h3>Añadir Nueva Tarjeta</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Título de la tarjeta:</label>
          <input
            type="text"
            value={taskTitle}
            onChange={(e) => onTaskTitleChange(e.target.value)}
            required
            autoFocus
          />
        </div>
        <div className="form-actions">
          <button type="submit" className="btn-submit">Añadir</button>
          <button type="button" className="btn-cancel" onClick={onClose}>Cancelar</button>
        </div>
      </form>
    </Modal>
  );
}

function EditTaskModal({ show, onClose, onSubmit, task, onTaskChange }) {
  if (!task) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(e);
  };

  return (
    <Modal show={show} onClose={onClose}>
      <h3>Editar Tarea</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Título de la tarea:</label>
          <input
            type="text"
            value={task.title}
            onChange={(e) => onTaskChange({...task, title: e.target.value})}
            required
            autoFocus
          />
        </div>
        <div className="form-group">
          <label>Fecha de vencimiento:</label>
          <input
            type="date"
            value={task.due_date ? task.due_date.split('T')[0] : ''}
            onChange={(e) => onTaskChange({...task, due_date: e.target.value})}
          />
        </div>
        <div className="form-actions">
          <button type="submit" className="btn-submit">Guardar Cambios</button>
          <button type="button" className="btn-cancel" onClick={onClose}>Cancelar</button>
        </div>
      </form>
    </Modal>
  );
}

function EditSubtaskModal({ show, onClose, onSubmit, subtask, onSubtaskChange }) {
  if (!subtask) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(e);
  };

  return (
    <Modal show={show} onClose={onClose}>
      <h3>Editar Subtarea</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Título de la subtarea:</label>
          <input
            type="text"
            value={subtask.title}
            onChange={(e) => onSubtaskChange({...subtask, title: e.target.value})}
            required
            autoFocus
          />
        </div>
        <div className="form-group">
          <label>Fecha de vencimiento:</label>
          <input
            type="date"
            value={subtask.due_date ? subtask.due_date.split('T')[0] : ''}
            onChange={(e) => onSubtaskChange({...subtask, due_date: e.target.value})}
          />
        </div>
        <div className="form-actions">
          <button type="submit" className="btn-submit">Guardar Cambios</button>
          <button type="button" className="btn-cancel" onClick={onClose}>Cancelar</button>
        </div>
      </form>
    </Modal>
  );
}

function ColorPickerModal({ show, onClose, onSelectColor, selectedListId, lists }) {
  const colors = [
    { name: 'green', value: 'green', hex: '#14532d' },
    { name: 'yellow', value: 'yellow', hex: '#854d0e' },
    { name: 'black', value: 'black', hex: '#111827' },
    { name: 'purple', value: 'purple', hex: '#581c87' }
  ];
  
  // Obtener el color actual de la lista seleccionada
  const currentList = lists?.find(list => list.id === selectedListId);
  const currentColor = currentList?.color || null;
  
  return (
    <Modal show={show} onClose={onClose}>
      <h3>Seleccionar Color de Lista</h3>
      <div className="color-picker-container">
        <div className="color-picker-grid">
          {colors.map(color => (
            <div
              key={color.value}
              className={`color-option ${currentColor === color.value ? 'selected' : ''}`}
              style={{ backgroundColor: color.hex }}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Color seleccionado:', color.value, 'para lista:', selectedListId);
                if (selectedListId) {
                  onSelectColor(color.value);
                  // No cerrar el modal aquí, se cerrará después de que se complete la operación
                } else {
                  console.error('No hay lista seleccionada');
                  onClose();
                }
              }}
              title={color.name}
            />
          ))}
        </div>
      </div>
    </Modal>
  );
}

function ActivitiesModal({ show, onClose, activities, heading, onAddComment }) {
  const [commentTexts, setCommentTexts] = useState({});

  const handleAddComment = (activityId) => {
    const comment = commentTexts[activityId];
    if (comment && comment.trim()) {
      onAddComment(activityId, comment);
      setCommentTexts({...commentTexts, [activityId]: ''});
    }
  };

  return (
    <Modal show={show} onClose={onClose}>
      <h3>{heading}</h3>
      <div className="activities-list">
        {activities.length > 0 ? (
          activities.map(activity => (
            <div key={activity.id} className="activity-item">
              <div className="activity-header">
                <strong>{activity.user_username}</strong>
                <span className="activity-type">{activity.activity_type_display}</span>
                <span className="activity-date">
                  {new Date(activity.created_at).toLocaleString('es-ES')}
                </span>
              </div>
              <div className="activity-description">{activity.description}</div>
              {activity.comments && activity.comments.length > 0 && (
                <div className="activity-comments">
                  {activity.comments.map(comment => (
                    <div key={comment.id} className="activity-comment">
                      <strong>{comment.author_username}:</strong> {comment.comment}
                      <span className="comment-date">
                        {new Date(comment.created_at).toLocaleString('es-ES')}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              <div className="activity-comment-form">
                <input
                  type="text"
                  placeholder="Agregar comentario..."
                  value={commentTexts[activity.id] || ''}
                  onChange={(e) => setCommentTexts({...commentTexts, [activity.id]: e.target.value})}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleAddComment(activity.id);
                    }
                  }}
                />
                <button onClick={() => handleAddComment(activity.id)}>Comentar</button>
              </div>
            </div>
          ))
        ) : (
          <p>No hay actividades registradas</p>
        )}
      </div>
      <button className="btn-cancel" onClick={onClose}>Cerrar</button>
    </Modal>
  );
}

function InviteModal({ show, onClose, students, selectedStudentId, onStudentIdChange, onSubmit }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <Modal show={show} onClose={onClose}>
      <h3>Invitar Estudiante</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Seleccionar Estudiante:</label>
          <select
            value={selectedStudentId}
            onChange={(e) => onStudentIdChange(e.target.value)}
            className="form-control"
            required
          >
            <option value="">-- Seleccione un estudiante --</option>
            {students.map(student => (
              <option key={student.id} value={student.id}>{student.username}</option>
            ))}
          </select>
        </div>
        <div className="form-actions">
          <button type="submit" className="btn-submit">Enviar Invitación</button>
          <button type="button" className="btn-cancel" onClick={onClose}>Cancelar</button>
        </div>
      </form>
    </Modal>
  );
}

function InvitationsModal({ show, onClose, invitations, onAccept, onReject }) {
  return (
    <Modal show={show} onClose={onClose}>
      <h3>Invitaciones Pendientes</h3>
      <div className="invitations-list">
        {invitations.length > 0 ? (
          invitations.map(invitation => (
            <div key={invitation.id} className="invitation-item">
              <div className="invitation-info">
                <strong>{invitation.admin_username || invitation.student_username}</strong>
                <span className="invitation-date">
                  {new Date(invitation.created_at).toLocaleString('es-ES')}
                </span>
              </div>
              <div className="invitation-actions">
                <button className="btn-accept" onClick={() => onAccept(invitation.id)}>Aceptar</button>
                <button className="btn-reject" onClick={() => onReject(invitation.id)}>Rechazar</button>
              </div>
            </div>
          ))
        ) : (
          <p>No hay invitaciones pendientes</p>
        )}
      </div>
      <button className="btn-cancel" onClick={onClose}>Cerrar</button>
    </Modal>
  );
}

function CreateUserModal({ show, onClose, userData, onUserDataChange, onSubmit }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(e);
  };

  return (
    <Modal show={show} onClose={onClose}>
      <h3>Crear Usuario</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Nombre de usuario:</label>
          <input
            type="text"
            value={userData.username}
            onChange={(e) => onUserDataChange({...userData, username: e.target.value})}
            required
            autoFocus
          />
        </div>
        <div className="form-group">
          <label>Email:</label>
          <input
            type="email"
            value={userData.email}
            onChange={(e) => onUserDataChange({...userData, email: e.target.value})}
            required
          />
        </div>
        <div className="form-group">
          <label>Contraseña:</label>
          <input
            type="password"
            value={userData.password}
            onChange={(e) => onUserDataChange({...userData, password: e.target.value})}
            required
          />
        </div>
        <div className="form-group">
          <label>Rol:</label>
          <select
            value={userData.role}
            onChange={(e) => onUserDataChange({...userData, role: e.target.value})}
          >
            <option value="student">Estudiante</option>
            <option value="admin">Administrador</option>
          </select>
        </div>
        <div className="form-actions">
          <button type="submit" className="btn-submit">Crear Usuario</button>
          <button type="button" className="btn-cancel" onClick={onClose}>Cancelar</button>
        </div>
      </form>
    </Modal>
  );
}

function BoardColorModal({ show, onClose, boardColors, onSelectColor, onUploadBackground }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  // Limpiar el archivo seleccionado cuando se cierra el modal
  useEffect(() => {
    if (!show) {
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [show]);

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      const event = {
        target: {
          files: [selectedFile]
        }
      };
      onUploadBackground(event);
      // El estado se limpiará cuando se cierre el modal
    }
  };

  return (
    <Modal show={show} onClose={onClose}>
      <h3>Personalizar color del tablero</h3>
      <div className="color-palette">
        <button 
          className="color-swatch no-color" 
          onClick={() => {
            onSelectColor('transparent');
            onClose();
          }} 
          title="Sin color"
        >
          ✕
        </button>
        {boardColors.map(color => (
          <button
            key={color}
            className="color-swatch"
            style={{ backgroundColor: color }}
            onClick={() => {
              onSelectColor(color);
              onClose();
            }}
            title={color}
          />
        ))}
      </div>
      <div className="background-upload">
        <label htmlFor="boardBackgroundInput">Imagen personalizada</label>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', width: '100%' }}>
          <input
            type="file"
            id="boardBackgroundInput"
            ref={fileInputRef}
            accept="image/jpeg,image/png,image/webp"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          <button type="button" className="btn-select-file" onClick={handleFileSelect}>
            Seleccionar archivo
          </button>
          <span className="file-status">
            {selectedFile ? selectedFile.name : 'Sin archivos seleccionados'}
          </span>
        </div>
        <button type="button" className="btn-upload" onClick={handleUpload} disabled={!selectedFile}>
          Subir imagen
        </button>
        <p className="upload-hint">Formatos admitidos: JPG, PNG, WEBP. Máx. 4MB.</p>
      </div>
    </Modal>
  );
}

function AddSubtaskModal({ show, onClose, taskId, onSubmit }) {
  const [title, setTitle] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (title.trim()) {
      onSubmit(title.trim());
      setTitle('');
    }
  };

  return (
    <Modal show={show} onClose={onClose}>
      <h3>Añadir Nueva Subtarea</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Título de la subtarea:</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            autoFocus
          />
        </div>
        <div className="form-actions">
          <button type="submit" className="btn-submit">Añadir</button>
          <button type="button" className="btn-cancel" onClick={onClose}>Cancelar</button>
        </div>
      </form>
    </Modal>
  );
}

export default Board;
