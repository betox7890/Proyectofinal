import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { kanbanService } from '../services/api';
import './Calendar.css';

function Calendar() {
  const [calendarData, setCalendarData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth());
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailOptions, setEmailOptions] = useState({
    overdue: true,
    soon: true,
    week: false
  });
  const [emailStatus, setEmailStatus] = useState('');

  useEffect(() => {
    // Aplicar clase board-page al body para el fondo con patrón
    document.body.classList.add('board-page');
    loadCalendar();
    
    // Limpiar al desmontar
    return () => {
      document.body.classList.remove('board-page');
    };
  }, []);

  const loadCalendar = async () => {
    try {
      const response = await kanbanService.getCalendar();
      if (response.data.success) {
        setCalendarData(response.data);
      } else {
        setError('Error al cargar el calendario');
      }
    } catch (err) {
      setError('Error al cargar el calendario: ' + (err.response?.data?.error || err.message));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const monthNames = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 
                      'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  const dayNames = ['do.', 'lu.', 'ma.', 'mi.', 'ju.', 'vi.', 'sa.'];

  const pad = (num) => (num < 10 ? '0' + num : '' + num);

  const getEventMap = () => {
    if (!calendarData?.calendar_items) return {};
    const eventMap = {};
    const eventPriority = { 'overdue': 3, 'soon': 2, 'ok': 1 };
    
    calendarData.calendar_items.forEach(item => {
      if (item.due_date) {
        const dateStr = item.due_date.split('T')[0]; // Formato ISO
        if (!eventMap[dateStr] || (eventPriority[item.status] || 0) > (eventPriority[eventMap[dateStr]?.status] || 0)) {
          eventMap[dateStr] = item;
        }
      }
    });
    
    return eventMap;
  };

  const renderMiniCalendar = () => {
    const eventMap = getEventMap();
    const firstDay = new Date(currentYear, currentMonth, 1);
    const startingDay = firstDay.getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const today = new Date();

    const rows = [];
    let date = 1;

    for (let row = 0; row < 6; row++) {
      const cells = [];
      for (let col = 0; col < 7; col++) {
        if (row === 0 && col < startingDay) {
          cells.push(<td key={`empty-${col}`}></td>);
        } else if (date > daysInMonth) {
          cells.push(<td key={`empty-end-${col}`}></td>);
        } else {
          const isoDate = `${currentYear}-${pad(currentMonth + 1)}-${pad(date)}`;
          const event = eventMap[isoDate];
          let className = '';
          
          if (event && event.status === 'overdue') className = 'due-overdue';
          else if (event && event.status === 'soon') className = 'due-soon';
          else if (event && event.status === 'ok') className = 'due-ok';
          else if (today.getFullYear() === currentYear && today.getMonth() === currentMonth && today.getDate() === date) {
            className = 'today';
          }

          cells.push(
            <td key={date}>
              <span className={className}>{date}</span>
            </td>
          );
          date++;
        }
      }
      rows.push(<tr key={row}>{cells}</tr>);
      if (date > daysInMonth) break;
    }

    return rows;
  };

  const handlePrevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear(currentYear - 1);
    } else {
      setCurrentMonth(currentMonth - 1);
    }
  };

  const handleNextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear(currentYear + 1);
    } else {
      setCurrentMonth(currentMonth + 1);
    }
  };

  const handleSendEmail = async () => {
    if (!emailOptions.overdue && !emailOptions.soon && !emailOptions.week) {
      setEmailStatus('Por favor, selecciona al menos una opción de recordatorio.');
      return;
    }

    setEmailStatus('⏳ Enviando recordatorios...');

    try {
      const response = await kanbanService.sendCalendarReminders({
        overdue: emailOptions.overdue,
        soon: emailOptions.soon,
        week: emailOptions.week
      });

      if (response.data.success) {
        setEmailStatus(`✅ ${response.data.message}${response.data.details ? '\n' + response.data.details : ''}`);
        setTimeout(() => {
          setShowEmailModal(false);
          setEmailStatus('');
        }, 3000);
      } else {
        setEmailStatus(`❌ Error: ${response.data.error || 'No se pudieron enviar los correos'}`);
      }
    } catch (err) {
      setEmailStatus('❌ Error al enviar los correos. Por favor, intenta nuevamente.');
      console.error(err);
    }
  };

  return (
    <div className="board-container">
      <div className="calendar-container">
        <div className="calendar-header">
          <h1>Calendario de Vencimientos</h1>
          <div className="calendar-header-actions">
            <button className="btn-send-email" onClick={() => setShowEmailModal(true)} title="Enviar recordatorios por correo">
              📧 Enviar Recordatorios
            </button>
            <Link to="/board" className="btn-back-board">← Volver al tablero</Link>
          </div>
        </div>

      {loading && <div className="loading">Cargando calendario...</div>}
      {error && <div className="error">{error}</div>}

      {calendarData && (
        <>
          <div className="calendar-summary">
            <div className="calendar-card">
              <strong>{calendarData.total_items || 0}</strong>
              <span>Elementos totales</span>
            </div>
            <div className="calendar-card overdue">
              <strong>{calendarData.overdue_count || 0}</strong>
              <span>Vencidos</span>
            </div>
            <div className="calendar-card soon">
              <strong>{calendarData.soon_count || 0}</strong>
              <span>Vencen pronto (≤ 3 días)</span>
            </div>
          </div>

          <div className="mini-calendar">
            <div className="mini-calendar-header">
              <button type="button" className="mini-cal-btn" onClick={handlePrevMonth}>‹</button>
              <span className="mini-cal-title">{monthNames[currentMonth]} de {currentYear}</span>
              <button type="button" className="mini-cal-btn" onClick={handleNextMonth}>›</button>
            </div>
            <table className="mini-calendar-table">
              <thead>
                <tr>
                  {dayNames.map(day => (
                    <th key={day}>{day}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {renderMiniCalendar()}
              </tbody>
            </table>
            <div className="mini-calendar-legend">
              <span className="legend-item due-overdue">Vencido</span>
              <span className="legend-item due-soon">Pronto a vencer</span>
              <span className="legend-item due-ok">En plazo</span>
            </div>
          </div>

          {calendarData.calendar_items && calendarData.calendar_items.length > 0 ? (
            <table className="calendar-table">
              <thead>
                <tr>
                  <th>Tipo</th>
                  <th>Título</th>
                  <th>Lista</th>
                  <th>Pertenece a</th>
                  <th>Responsable</th>
                  <th>Fecha de vencimiento</th>
                  <th>Tiempo restante</th>
                </tr>
              </thead>
              <tbody>
                {calendarData.calendar_items.map((item, index) => (
                  <tr key={index}>
                    <td>
                      <span className={`badge-type ${item.type === 'Subtarea' ? 'badge-subtask' : ''}`}>
                        {item.type}
                      </span>
                    </td>
                    <td>{item.title}</td>
                    <td>{item.list_name}</td>
                    <td>{item.parent || '-'}</td>
                    <td>{item.created_by}</td>
                    <td>{item.due_date ? (() => {
                      const date = new Date(item.due_date);
                      const day = String(date.getDate()).padStart(2, '0');
                      const month = String(date.getMonth() + 1).padStart(2, '0');
                      const year = date.getFullYear();
                      return `${day}/${month}/${year}`;
                    })() : '-'}</td>
                    <td>
                      {item.status === 'overdue' && (
                        <span className="badge-overdue">
                          Vencido hace {item.due_in_abs} día{item.due_in_abs !== 1 ? 's' : ''}
                        </span>
                      )}
                      {item.status === 'soon' && (
                        <span className="badge-soon">
                          Vence en {item.due_in} día{item.due_in !== 1 ? 's' : ''}
                        </span>
                      )}
                      {item.status === 'ok' && (
                        <span className="badge-ok">
                          Vence en {item.due_in} día{item.due_in !== 1 ? 's' : ''}
                        </span>
                      )}
                      {!item.status || item.status === 'unknown' ? '-' : ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="calendar-empty">
              No hay tareas ni subtareas registradas.
            </div>
          )}
        </>
      )}

      {/* Modal para envío de correos */}
      {showEmailModal && (
        <div className="modal" onClick={(e) => e.target.className === 'modal' && setShowEmailModal(false)}>
          <div className="modal-content">
            <span className="close" onClick={() => setShowEmailModal(false)}>&times;</span>
            <h3>📧 Enviar Recordatorios por Correo</h3>
            <div className="email-form">
              <p className="email-description">
                Selecciona qué tipo de recordatorios deseas enviar. Los correos se enviarán a los responsables de las tareas y subtareas.
              </p>
              
              <div className="email-options">
                <label className="email-option">
                  <input
                    type="checkbox"
                    checked={emailOptions.overdue}
                    onChange={(e) => setEmailOptions({...emailOptions, overdue: e.target.checked})}
                  />
                  <span>Tareas y subtareas vencidas</span>
                </label>
                <label className="email-option">
                  <input
                    type="checkbox"
                    checked={emailOptions.soon}
                    onChange={(e) => setEmailOptions({...emailOptions, soon: e.target.checked})}
                  />
                  <span>Tareas y subtareas que vencen en 1-3 días</span>
                </label>
                <label className="email-option">
                  <input
                    type="checkbox"
                    checked={emailOptions.week}
                    onChange={(e) => setEmailOptions({...emailOptions, week: e.target.checked})}
                  />
                  <span>Tareas y subtareas que vencen en 4-7 días</span>
                </label>
              </div>

              <div className="email-actions">
                <button type="button" className="btn-submit" onClick={handleSendEmail}>
                  📧 Enviar Recordatorios
                </button>
                <button type="button" className="btn-cancel" onClick={() => { setShowEmailModal(false); setEmailStatus(''); }}>
                  Cancelar
                </button>
              </div>

              {emailStatus && (
                <div className={`email-status ${emailStatus.includes('✅') ? 'email-status-success' : emailStatus.includes('❌') ? 'email-status-error' : 'email-status-loading'}`}>
                  <p style={{ whiteSpace: 'pre-line' }}>{emailStatus}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}

export default Calendar;
