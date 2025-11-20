import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Login.css';

// Configurar axios globalmente para incluir credenciales en TODAS las peticiones
// OBLIGATORIO: Sin esto, las cookies jamás llegan a React
axios.defaults.withCredentials = true;

// Función para obtener CSRF token de las cookies
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

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [requires2FA, setRequires2FA] = useState(false);
  const [pendingUsername, setPendingUsername] = useState('');
  const navigate = useNavigate();

  // Configurar axios para enviar cookies en todas las peticiones
  useEffect(() => {
    // Asegurar que axios envíe cookies por defecto
    axios.defaults.withCredentials = true;
  }, []);

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (!username.trim() || !password) {
      setError('Usuario y contraseña son requeridos');
      setLoading(false);
      return;
    }

    try {
      console.log('=== PASO 1: Autenticación con usuario y contraseña ===');
      console.log('Username:', username);
      console.log('Cookies antes de enviar:', document.cookie);

      // OBLIGATORIO: credentials/include es necesario para que las cookies se envíen
      // Usar ruta relativa - Vite proxy redirige al backend
      const response = await axios.post(
        '/api/login/',
        {
          username: username.trim(),
          password: password,
          step: 'password'
        },
        {
          withCredentials: true,  // NECESARIO: Sin esto, la cookie jamás llega a React
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      console.log('Respuesta del servidor:', response.data);
      console.log('Cookies después de recibir respuesta:', document.cookie);
      console.log('Headers de respuesta:', response.headers);
      
      // Verificar Set-Cookie en headers (puede estar en diferentes formatos)
      const setCookieHeaders = [];
      if (response.headers['set-cookie']) {
        setCookieHeaders.push(...(Array.isArray(response.headers['set-cookie']) ? response.headers['set-cookie'] : [response.headers['set-cookie']]));
      }
      if (response.headers['Set-Cookie']) {
        setCookieHeaders.push(...(Array.isArray(response.headers['Set-Cookie']) ? response.headers['Set-Cookie'] : [response.headers['Set-Cookie']]));
      }
      
      console.log('Set-Cookie headers encontrados:', setCookieHeaders.length);
      setCookieHeaders.forEach((header, idx) => {
        console.log(`Set-Cookie ${idx + 1}:`, header.substring(0, 100) + '...');
      });
      
      // Verificar inmediatamente si la cookie se recibió
      const checkCookie = () => {
        const sessionCookie = document.cookie.split(';').find(c => c.trim().startsWith('sessionid='));
        if (sessionCookie) {
          console.log('✅ Cookie de sesión recibida y guardada:', sessionCookie.substring(0, 30) + '...');
          return true;
        } else {
          console.warn('⚠️ Cookie de sesión NO recibida. Cookies disponibles:', document.cookie || 'ninguna');
          return false;
        }
      };
      
      // Verificar inmediatamente
      checkCookie();
      
      // Verificar después de un momento (el navegador puede tardar en procesar)
      setTimeout(() => {
        if (!checkCookie()) {
          console.error('❌ Cookie de sesión NO se guardó después de 500ms. Esto causará problemas en el paso 2FA.');
          console.error('Posibles causas:');
          console.error('1. SameSite=None requiere Secure=True (pero estamos en HTTP)');
          console.error('2. El navegador está bloqueando la cookie');
          console.error('3. CORS no está permitiendo la cookie');
        }
      }, 500);

      if (response.data.success) {
        // Login exitoso (sin 2FA)
        console.log('Login exitoso sin 2FA');
        if (onLogin) {
          onLogin();
        }
        navigate('/board');
      } else if (response.data.requires_2fa) {
        // Requiere verificación 2FA
        console.log('Se requiere 2FA');
        console.log('Username para 2FA:', response.data.username || username);
        setRequires2FA(true);
        setPendingUsername(response.data.username || username);
        setPassword(''); // Limpiar contraseña por seguridad
        setError(''); // Limpiar errores previos
      } else {
        setError(response.data.error || 'Error al iniciar sesión');
      }
    } catch (err) {
      console.error('Error en autenticación:', err);
      console.error('Error response:', err.response?.data);
      
      if (err.response?.data) {
        const errorData = err.response.data;
        if (errorData.requires_2fa) {
          console.log('Se requiere 2FA (desde error)');
          setRequires2FA(true);
          setPendingUsername(errorData.username || username);
          setPassword('');
          setError('');
        } else {
          setError(errorData.error || errorData.error_message || 'Usuario o contraseña incorrecta');
        }
      } else {
        setError('Error de conexión. Verifica que el servidor esté corriendo.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handle2FASubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Limpiar código completamente: eliminar TODOS los caracteres no numéricos
    // Incluye: espacios, saltos de línea, tabs, guiones, puntos, comas, etc.
    let codeValue = code
      .replace(/\s/g, '')           // Eliminar espacios
      .replace(/\n/g, '')            // Eliminar saltos de línea
      .replace(/\r/g, '')            // Eliminar retornos de carro
      .replace(/\t/g, '')            // Eliminar tabs
      .replace(/-/g, '')              // Eliminar guiones
      .replace(/\./g, '')             // Eliminar puntos
      .replace(/,/g, '')              // Eliminar comas
      .replace(/[^\d]/g, '')          // Eliminar cualquier otro carácter no numérico
      .slice(0, 6);                   // Limitar a 6 dígitos
    
    // Asegurar que sea string explícitamente
    codeValue = String(codeValue);
    
    console.log('=== PASO 2: Verificación 2FA ===');
    console.log('Código ingresado (raw):', JSON.stringify(code));
    console.log('Código procesado:', codeValue);
    console.log('Tipo del código:', typeof codeValue);
    console.log('Longitud del código:', codeValue.length);
    console.log('Username pendiente:', pendingUsername);
    console.log('Cookies antes de enviar:', document.cookie);
    
    if (!codeValue || codeValue.length !== 6) {
      setError('Por favor ingresa un código de 6 dígitos');
      setLoading(false);
      return;
    }

    // Validar que sea solo números
    if (!/^\d{6}$/.test(codeValue)) {
      setError('El código debe contener solo números');
      setLoading(false);
      return;
    }

    try {
      // Enviar código 2FA con username como respaldo
      // El backend intentará usar la sesión primero, pero si no existe, usará el username
      // Asegurar que code sea string explícitamente
      const requestData = {
        step: 'totp',
        code: String(codeValue),  // Forzar a string
        username: String(pendingUsername || '')  // Asegurar que username también sea string
      };

      console.log('Enviando petición 2FA:', requestData);
      console.log('Tipo de code en requestData:', typeof requestData.code);

      // Verificar cookies antes de enviar
      console.log('Cookies ANTES de enviar petición 2FA:', document.cookie);
      const sessionCookieBefore = document.cookie.split(';').find(c => c.trim().startsWith('sessionid='));
      if (sessionCookieBefore) {
        console.log('✅ Cookie de sesión presente antes de enviar:', sessionCookieBefore.substring(0, 30) + '...');
      } else {
        console.warn('⚠️ Cookie de sesión NO presente antes de enviar');
      }

      // Obtener la URL base de la API (reutilizar la función)
      const getApiBaseUrl = () => {
        if (import.meta.env.VITE_API_BASE_URL) {
          return import.meta.env.VITE_API_BASE_URL;
        }
        if (window.location.hostname === 'heiner2001.github.io') {
          return 'https://kanban-backend.onrender.com';
        }
        return '';
      };
      
      const apiBase = getApiBaseUrl();
      const loginUrl = apiBase ? `${apiBase}/api/login/` : '/api/login/';
      
      console.log('Intentando conectar a (2FA):', loginUrl);
      
      // OBLIGATORIO: credentials/include es necesario para que las cookies se envíen
      const response = await axios.post(
        loginUrl,
        requestData,
        {
          withCredentials: true,  // NECESARIO: Sin esto, la cookie jamás llega a React
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      console.log('Respuesta del servidor 2FA:', response.data);
      console.log('Cookies DESPUÉS de recibir respuesta 2FA:', document.cookie);
      const sessionCookieAfter = document.cookie.split(';').find(c => c.trim().startsWith('sessionid='));
      if (sessionCookieAfter) {
        console.log('✅ Cookie de sesión presente después:', sessionCookieAfter.substring(0, 30) + '...');
      } else {
        console.warn('⚠️ Cookie de sesión NO presente después');
      }

      if (response.data.success) {
        // Login exitoso con 2FA
        console.log('Login exitoso con 2FA');
        if (onLogin) {
          onLogin();
        }
        navigate('/board');
      } else {
        setError(response.data.error || 'Código inválido. Intenta nuevamente.');
        setCode(''); // Limpiar código para reintentar
      }
    } catch (err) {
      console.error('Error en 2FA:', err);
      console.error('Error response:', err.response?.data);
      
      if (err.response?.data) {
        const errorData = err.response.data;
        
        // Si el error es de sesión expirada, intentar restaurar
        if (errorData.error && errorData.error.includes('expiró')) {
          console.log('Sesión expirada, intentando restaurar...');
          // No hacer nada especial, el backend ya intentará restaurar con el username
          setError(errorData.error || 'La sesión expiró. Por favor, intenta nuevamente.');
        } else {
          setError(errorData.error || 'Código inválido. Intenta nuevamente.');
        }
        setCode('');
      } else {
        setError('Error de conexión. Verifica que el servidor esté corriendo.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleBackToLogin = () => {
    console.log('Volviendo a login inicial');
    setRequires2FA(false);
    setCode('');
    setError('');
    setPendingUsername('');
    setPassword('');
    setUsername('');
  };

  const handleCodeChange = (e) => {
    // Solo permitir números, máximo 6 dígitos
    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
    setCode(value);
    // Limpiar error cuando el usuario empiece a escribir
    if (error && error.includes('Código')) {
      setError('');
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>{requires2FA ? 'Verificación en dos pasos' : 'Iniciar Sesión'}</h1>
        
        {error && <div className="error-message">{error}</div>}
        
        {requires2FA ? (
          <form onSubmit={handle2FASubmit}>
            <p className="info-text">
              Hola <strong>{pendingUsername}</strong>, ingresa el código de 6 dígitos generado por tu aplicación de autenticación.
            </p>
            
            <div className="form-group">
              <label htmlFor="code">Código 2FA:</label>
              <input
                type="text"
                id="code"
                name="code"
                value={code}
                onChange={(e) => {
                  // Limpiar completamente: eliminar TODOS los caracteres no numéricos
                  let value = e.target.value
                    .replace(/\s/g, '')           // Eliminar espacios
                    .replace(/\n/g, '')            // Eliminar saltos de línea
                    .replace(/\r/g, '')            // Eliminar retornos de carro
                    .replace(/\t/g, '')            // Eliminar tabs
                    .replace(/-/g, '')              // Eliminar guiones
                    .replace(/\./g, '')             // Eliminar puntos
                    .replace(/,/g, '')              // Eliminar comas
                    .replace(/[^\d]/g, '')          // Eliminar cualquier otro carácter no numérico
                    .slice(0, 6);                   // Limitar a 6 dígitos
                  
                  // Asegurar que sea string
                  value = String(value);
                  
                  setCode(value);
                  // Limpiar error cuando el usuario empiece a escribir
                  if (error && error.includes('Código')) {
                    setError('');
                  }
                }}
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength="6"
                required
                autoFocus
                placeholder="000000"
                style={{ 
                  textAlign: 'center', 
                  letterSpacing: '8px', 
                  fontSize: '20px',
                  fontFamily: 'monospace'
                }}
                disabled={loading}
              />
            </div>
            
            <button 
              type="submit" 
              disabled={loading || code.length !== 6} 
              className="btn-login"
            >
              {loading ? 'Verificando...' : 'Verificar'}
            </button>
            
            <div className="two-factor-help">
              <button 
                type="button" 
                className="two-factor-back" 
                onClick={handleBackToLogin}
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  color: 'rgba(255, 255, 255, 0.7)', 
                  cursor: 'pointer', 
                  textDecoration: 'underline', 
                  padding: '10px 0',
                  width: '100%'
                }}
              >
                Iniciar sesión con otra cuenta
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handlePasswordSubmit}>
            <div className="form-group">
              <label htmlFor="username">Nombre de usuario:</label>
              <input
                type="text"
                id="username"
                name="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                disabled={loading}
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="password">Contraseña:</label>
              <input
                type="password"
                id="password"
                name="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            
            <button type="submit" disabled={loading} className="btn-login">
              {loading ? 'Iniciando sesión...' : 'Continuar'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

export default Login;
