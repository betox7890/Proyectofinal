import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Board from './pages/Board';
import Calendar from './pages/Calendar';
import SystemLogs from './pages/SystemLogs';
import TwoFactorSetup from './pages/TwoFactorSetup';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // Obtener el base path para GitHub Pages
  const getBasePath = () => {
    // En producción (GitHub Pages), usar /Proyectofinal/
    if (window.location.hostname.includes('github.io')) {
      return '/Proyectofinal';
    }
    // En desarrollo, usar /
    return '';
  };

  const basePath = getBasePath();

  useEffect(() => {
    // Verificar si el usuario está autenticado
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // Usar el servicio de API configurado
      const { API_CONFIG } = await import('./config/api.js');
      const apiBase = API_CONFIG.baseURL;
      const response = await fetch(`${apiBase}/api/user/`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      // 400 y 401 son normales si no hay sesión, no son errores críticos
      if (response.ok) {
        const data = await response.json();
        setIsAuthenticated(data.authenticated || false);
      } else if (response.status === 400 || response.status === 401) {
        // No hay sesión activa, es normal
        setIsAuthenticated(false);
      } else {
        // Otro error, log solo en desarrollo
        if (import.meta.env.DEV) {
          console.warn('Error checking auth:', response.status, response.statusText);
        }
        setIsAuthenticated(false);
      }
    } catch (error) {
      // Error de red o CORS, solo log en desarrollo
      if (import.meta.env.DEV) {
        console.error('Error checking auth:', error);
      }
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        color: '#fff'
      }}>
        Cargando...
      </div>
    );
  }

  return (
    <Router basename={basePath}>
      <Routes>
        <Route 
          path="/login" 
          element={
            isAuthenticated ? <Navigate to="/board" /> : <Login onLogin={() => setIsAuthenticated(true)} />
          } 
        />
        <Route 
          path="/board" 
          element={
            isAuthenticated ? <Board /> : <Navigate to="/login" />
          } 
        />
        <Route 
          path="/calendar" 
          element={
            isAuthenticated ? <Calendar /> : <Navigate to="/login" />
          } 
        />
        <Route 
          path="/logs" 
          element={
            isAuthenticated ? <SystemLogs /> : <Navigate to="/login" />
          } 
        />
        <Route 
          path="/two-factor/setup/" 
          element={
            isAuthenticated ? <TwoFactorSetup /> : <Navigate to="/login" />
          } 
        />
        <Route path="/" element={<Navigate to="/board" />} />
      </Routes>
    </Router>
  );
}

export default App;
