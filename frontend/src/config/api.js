// Configuración de la API
// Prioridad:
// 1. Variable de entorno VITE_API_BASE_URL (para Render, Vercel, etc.)
// 2. Render.com → usar backend de Render
// 3. GitHub Pages → usar Railway
// 4. Desarrollo local → localhost:8000
const getApiBaseUrl = () => {
  // Variable de entorno (tiene prioridad)
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  // Render.com
  if (window.location.host.includes('render.com')) {
    return 'https://proyectofinal-backend.onrender.com';
  }
  // GitHub Pages
  if (window.location.host.includes('github.io')) {
    return 'https://proyectofinal-production-bfac.up.railway.app';
  }
  // Desarrollo local
  return 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

export const API_CONFIG = {
  baseURL: API_BASE_URL,
  withCredentials: true, // Para incluir cookies en las peticiones
  headers: {
    'Content-Type': 'application/json',
  },
};

export default API_CONFIG;

