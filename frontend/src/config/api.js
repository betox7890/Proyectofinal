// Configuración de la API
// Si window.location.host incluye "github.io" → usar Railway
// Si existe import.meta.env.VITE_API_BASE_URL → usar esa
// En desarrollo → usar "http://localhost:8000"
const getApiBaseUrl = () => {
  if (window.location.host.includes('github.io')) {
    // URL de Railway
    return 'https://proyectofinal-production-bfac.up.railway.app';
  }
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
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

