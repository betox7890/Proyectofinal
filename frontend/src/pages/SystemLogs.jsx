import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { kanbanService } from '../services/api';
import './SystemLogs.css';
import '../pages/Board.css';

function SystemLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [logFileExists, setLogFileExists] = useState(false);
  const [logFilePath, setLogFilePath] = useState('');

  useEffect(() => {
    // Aplicar clase board-page al body para el fondo con patrón
    document.body.classList.add('board-page');
    loadLogs();
    
    // Limpiar al desmontar
    return () => {
      document.body.classList.remove('board-page');
    };
  }, []);

  const loadLogs = async () => {
    try {
      const response = await kanbanService.getSystemLogs();
      if (response.data.success) {
        setLogs(response.data.log_lines || []);
        setLogFileExists(response.data.file_exists || false);
        setLogFilePath(response.data.log_file_path || '');
      } else {
        setError(response.data.error || 'Error al cargar los logs');
      }
    } catch (err) {
      if (err.response?.status === 403) {
        setError('No tienes permisos para ver los registros del sistema.');
      } else {
        setError('Error al cargar los logs: ' + (err.response?.data?.error || err.message));
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="logs-container">
      <div className="logs-box">
        <div className="logs-header">
          <h1>Registros del Sistema</h1>
          <Link to="/board" className="btn-back-board">← Volver al tablero</Link>
        </div>
        <p className="logs-meta">
          Archivo: {logFilePath ? <code>{logFilePath}</code> : <em>no configurado</em>}
        </p>
        {logFileExists && (
          <p className="logs-hint">Mostrando hasta las últimas 500 líneas (nuevas entradas aparecen al final).</p>
        )}
        <div className="logs-output">
          {loading && <div className="loading">Cargando logs...</div>}
          {error && <div className="error">{error}</div>}
          {!loading && !error && logs.length > 0 && (
            <pre>{logs.join('')}</pre>
          )}
          {!loading && !error && logs.length === 0 && (
            <div className="logs-empty">No hay registros que mostrar.</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SystemLogs;

