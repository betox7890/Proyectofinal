// Configuración de la API
// En producción: usa la variable de entorno VITE_API_BASE_URL
// En desarrollo: usa ruta relativa para que Vite proxy redirija al backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? '' : 'https://kanban-backend.onrender.com');

export const API_CONFIG = {
  baseURL: API_BASE_URL,
  withCredentials: true, // Para incluir cookies en las peticiones
  headers: {
    'Content-Type': 'application/json',
  },
};

export default API_CONFIG;

