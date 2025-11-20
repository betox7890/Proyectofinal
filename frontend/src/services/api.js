import axios from 'axios';
import { API_CONFIG } from '../config/api';

// Crear instancia de axios con configuración base
// IMPORTANTE: withCredentials es OBLIGATORIO para que las cookies se envíen
const api = axios.create({
  ...API_CONFIG,
  withCredentials: true,  // OBLIGATORIO: Sin esto, la cookie jamás llega a React
});

// Interceptor para agregar CSRF token a las peticiones
api.interceptors.request.use(
  (config) => {
    // Obtener CSRF token de las cookies
    const csrftoken = getCookie('csrftoken');
    if (csrftoken) {
      config.headers['X-CSRFToken'] = csrftoken;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de respuesta
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log detallado de errores para debugging
    if (error.response?.status === 404) {
      console.error('❌ Error 404 - Endpoint no encontrado:', error.config?.url);
      console.error('Verifica que la ruta esté correcta y que el backend esté corriendo');
    }
    if (error.response?.status === 401) {
      // Usuario no autenticado, redirigir a login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Función auxiliar para obtener cookies
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Servicios de autenticación
export const authService = {
  login: (username, password) => {
    return api.post('/api/login/', { username, password, step: 'password' });
  },
  
  logout: () => {
    return api.post('/logout/');
  },
  
  getCurrentUser: () => {
    return api.get('/api/board/');
  },
};

// Servicios del tablero Kanban
export const kanbanService = {
  // Tablero completo
  getBoard: (filters = {}) => {
    // Construir query string con los filtros
    const params = new URLSearchParams();
    if (filters.q) params.append('q', filters.q);
    if (filters.creator) params.append('creator', filters.creator);
    if (filters.due_from) params.append('due_from', filters.due_from);
    if (filters.due_to) params.append('due_to', filters.due_to);
    
    const queryString = params.toString();
    const url = queryString ? `/api/board/?${queryString}` : '/api/board/';
    console.log('Llamando a getBoard con URL:', url);
    console.log('Filtros enviados:', filters);
    return api.get(url);
  },
  
  // Listas
  createList: (name) => {
    return api.post('/api/lists/', { name });
  },
  
  deleteList: (listId) => {
    return api.post(`/api/lists/${listId}/delete/`);
  },
  
  changeListColor: (listId, color) => {
    return api.post(`/api/lists/${listId}/color/`, { color });
  },
  
  reorderLists: (listIds) => {
    return api.post('/api/reorder-lists/', { list_ids: listIds });
  },
  
  // Tareas
  createTask: (listId, title) => {
    return api.post('/api/tasks/', { list_id: listId, title });
  },
  
  updateTask: (taskId, data) => {
    return api.patch(`/api/tasks/${taskId}/`, data);
  },
  
  updateTaskDueDate: (taskId, dueDate) => {
    return api.patch(`/api/tasks/${taskId}/`, { due_date: dueDate });
  },
  
  deleteTask: (taskId) => {
    return api.post(`/api/tasks/${taskId}/delete/`);
  },
  
  moveTask: (taskId, listId) => {
    return api.post(`/api/tasks/${taskId}/move/`, { list_id: listId });
  },
  
  reorderTasks: (listId, taskIds) => {
    return api.post('/api/reorder-tasks/', { list_id: listId, task_ids: taskIds });
  },
  
  // Subtareas
  createSubtask: (taskId, title) => {
    return api.post(`/api/tasks/${taskId}/subtasks/`, { title });
  },
  
  updateSubtask: (subtaskId, data) => {
    return api.patch(`/api/subtasks/${subtaskId}/`, data);
  },
  
  updateSubtaskDueDate: (subtaskId, dueDate) => {
    return api.patch(`/api/subtasks/${subtaskId}/`, { due_date: dueDate });
  },
  
  deleteSubtask: (subtaskId) => {
    return api.post(`/api/subtasks/${subtaskId}/delete/`);
  },
  
  toggleSubtask: (subtaskId) => {
    return api.post(`/api/subtasks/${subtaskId}/toggle/`);
  },
  
  reorderSubtasks: (taskId, subtaskIds) => {
    return api.post('/api/reorder-subtasks/', { task_id: taskId, subtask_ids: subtaskIds });
  },
  
  // Actividades
  getActivities: () => {
    return api.get('/api/activities/');
  },
  
  // Calendario
  getCalendar: () => {
    return api.get('/api/calendar/');
  },
  
  sendCalendarReminders: (options) => {
    return api.post('/calendar/send-reminders/', options);
  },
  
  getBoardUsersForReminders: () => {
    return api.get('/api/board-users-for-reminders/');
  },
  
  // Adjuntos
  uploadTaskAttachment: (taskId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/tasks/${taskId}/attachments/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  
  uploadSubtaskAttachment: (subtaskId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/subtasks/${subtaskId}/attachments/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  
  deleteTaskAttachment: (attachmentId) => {
    return api.post(`/api/tasks/attachments/${attachmentId}/delete/`);
  },
  
  deleteSubtaskAttachment: (attachmentId) => {
    return api.post(`/api/subtasks/attachments/${attachmentId}/delete/`);
  },
  
  // Invitaciones
  inviteStudent: (studentId) => {
    return api.post('/api/invite-student/', { student_id: studentId });
  },
  
  acceptInvitation: (invitationId) => {
    return api.post(`/api/accept-invitation/${invitationId}/`);
  },
  
  rejectInvitation: (invitationId) => {
    return api.post(`/api/reject-invitation/${invitationId}/`);
  },
  
  // Configuración del tablero
  changeBoardColor: (color) => {
    return api.post('/api/change-board-color/', { color });
  },
  
  uploadBoardBackground: (file) => {
    const formData = new FormData();
    formData.append('image', file);
    return api.post('/api/upload-board-background/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  
  // Usuarios
  createUser: (userData) => {
    return api.post('/api/create-user/', userData);
  },
  
  // Comentarios de actividades
  addActivityComment: (activityId, comment) => {
    return api.post(`/api/add-activity-comment/${activityId}/`, { comment });
  },
  
  // System Logs
  getSystemLogs: () => {
    return api.get('/api/system-logs/');
  },
  
  // 2FA Setup
  getTwoFactorSetup: () => {
    return api.get('/api/two-factor-setup/');
  },
  
  enableTwoFactor: (code) => {
    return api.post('/api/two-factor-setup/', { action: 'enable', code });
  },
  
  regenerateTwoFactorSecret: () => {
    return api.post('/api/two-factor-setup/', { action: 'regenerate' });
  },
  
  disableTwoFactor: () => {
    return api.post('/api/two-factor-setup/', { action: 'disable' });
  },
};

export default api;

