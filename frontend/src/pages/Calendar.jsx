import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { kanbanService } from '../services/api';
import emailjs from '@emailjs/browser';
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
  const [emailjsConfig, setEmailjsConfig] = useState({
    serviceId: '',
    templateId: '',
    publicKey: ''
  });
  const [showEmailjsConfig, setShowEmailjsConfig] = useState(false);

  useEffect(() => {
    // Cargar configuración de EmailJS desde variables de entorno o localStorage
    const envServiceId = import.meta.env.VITE_EMAILJS_SERVICE_ID;
    const envTemplateId = import.meta.env.VITE_EMAILJS_TEMPLATE_ID;
    const envPublicKey = import.meta.env.VITE_EMAILJS_PUBLIC_KEY;
    
    // Priorizar variables de entorno sobre localStorage
    if (envServiceId && envTemplateId && envPublicKey) {
      const config = {
        serviceId: envServiceId,
        templateId: envTemplateId,
        publicKey: envPublicKey
      };
      setEmailjsConfig(config);
      // Inicializar EmailJS
      try {
        emailjs.init(envPublicKey);
      } catch (initErr) {
        console.error('Error al inicializar EmailJS:', initErr);
      }
    } else {
      // Fallback a localStorage si no hay variables de entorno
      const savedConfig = localStorage.getItem('emailjs_config');
      if (savedConfig) {
        try {
          const config = JSON.parse(savedConfig);
          setEmailjsConfig(config);
          if (config.publicKey) {
            try {
              emailjs.init(config.publicKey);
            } catch (initErr) {
              console.error('Error al inicializar EmailJS:', initErr);
            }
          }
        } catch (e) {
          console.error('Error al cargar configuración EmailJS:', e);
        }
      }
    }
  }, []);

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

  const formatEmailContent = (user, includeOverdue, include1_3Days, include4_7Days) => {
    let content = `Hola ${user.full_name},\n\n`;
    content += 'Este es un resumen de tus tareas y subtareas en el tablero Kanban:\n\n';
    
    // Tareas vencidas
    if (includeOverdue && (user.overdue_tasks.length > 0 || user.overdue_subtasks.length > 0)) {
      content += '[URGENTE] TAREAS Y SUBTAREAS VENCIDAS:\n\n';
      
      user.overdue_tasks.forEach(task => {
        content += `  - Tarea: "${task.title}"\n`;
        content += `    Lista: ${task.list_name}\n`;
        content += `    Vencida hace ${task.days_overdue} dia(s)\n\n`;
      });
      
      user.overdue_subtasks.forEach(subtask => {
        content += `  - Subtarea: "${subtask.title}"\n`;
        content += `    Tarea: "${subtask.task_title}"\n`;
        content += `    Lista: ${subtask.list_name}\n`;
        content += `    Vencida hace ${subtask.days_overdue} dia(s)\n\n`;
      });
    }
    
    // Tareas que vencen en 1-3 días
    if (include1_3Days && (user.tasks_1_3_days.length > 0 || user.subtasks_1_3_days.length > 0)) {
      content += 'TAREAS Y SUBTAREAS QUE VENCEN EN 1-3 DIAS:\n\n';
      
      user.tasks_1_3_days.forEach(task => {
        content += `  - Tarea: "${task.title}"\n`;
        content += `    Lista: ${task.list_name}\n`;
        content += `    Vence en ${task.days_remaining} dia(s) (${task.due_date})\n\n`;
      });
      
      user.subtasks_1_3_days.forEach(subtask => {
        content += `  - Subtarea: "${subtask.title}"\n`;
        content += `    Tarea: "${subtask.task_title}"\n`;
        content += `    Lista: ${subtask.list_name}\n`;
        content += `    Vence en ${subtask.days_remaining} dia(s) (${subtask.due_date})\n\n`;
      });
    }
    
    // Tareas que vencen en 4-7 días
    if (include4_7Days && (user.tasks_4_7_days.length > 0 || user.subtasks_4_7_days.length > 0)) {
      content += 'TAREAS Y SUBTAREAS QUE VENCEN EN 4-7 DIAS:\n\n';
      
      user.tasks_4_7_days.forEach(task => {
        content += `  - Tarea: "${task.title}"\n`;
        content += `    Lista: ${task.list_name}\n`;
        content += `    Vence en ${task.days_remaining} dia(s) (${task.due_date})\n\n`;
      });
      
      user.subtasks_4_7_days.forEach(subtask => {
        content += `  - Subtarea: "${subtask.title}"\n`;
        content += `    Tarea: "${subtask.task_title}"\n`;
        content += `    Lista: ${subtask.list_name}\n`;
        content += `    Vence en ${subtask.days_remaining} dia(s) (${subtask.due_date})\n\n`;
      });
    }
    
    content += '\nPor favor, revisa el tablero Kanban para asegurarte de que el trabajo este en curso.\n\n';
    content += 'Saludos,\n';
    content += 'Sistema de Gestion Kanban';
    
    return content;
  };

  const handleSendEmail = async () => {
    if (!emailOptions.overdue && !emailOptions.soon && !emailOptions.week) {
      setEmailStatus('Por favor, selecciona al menos una opción de recordatorio.');
      return;
    }

    // Verificar configuración de EmailJS (variables de entorno o localStorage)
    const serviceId = import.meta.env.VITE_EMAILJS_SERVICE_ID || emailjsConfig.serviceId;
    const templateId = import.meta.env.VITE_EMAILJS_TEMPLATE_ID || emailjsConfig.templateId;
    const publicKey = import.meta.env.VITE_EMAILJS_PUBLIC_KEY || emailjsConfig.publicKey;

    if (!serviceId || !templateId || !publicKey) {
      setEmailStatus('❌ Error: Debes configurar EmailJS primero. Por favor, ingresa tus credenciales.');
      setShowEmailjsConfig(true);
      return;
    }

    setEmailStatus('⏳ Obteniendo usuarios del tablero...');

    try {
      // Obtener usuarios del tablero desde el API
      const usersResponse = await kanbanService.getBoardUsersForReminders();
      
      if (!usersResponse || !usersResponse.data) {
        setEmailStatus(`❌ Error: No se pudo conectar con el servidor. Verifica que el backend esté corriendo.`);
        console.error('Error en respuesta del servidor:', usersResponse);
        return;
      }
      
      if (!usersResponse.data.success) {
        setEmailStatus(`❌ Error: ${usersResponse.data.error || 'No se pudieron obtener los usuarios'}`);
        return;
      }

      const users = usersResponse.data.users || [];
      
      if (users.length === 0) {
        setEmailStatus('ℹ️ No hay usuarios con tareas pendientes para enviar recordatorios.');
        return;
      }

      setEmailStatus(`⏳ Enviando correos a ${users.length} usuario(s)...`);

      // Filtrar usuarios según las opciones seleccionadas
      const usersToEmail = users.filter(user => {
        if (emailOptions.overdue && (user.overdue_tasks.length > 0 || user.overdue_subtasks.length > 0)) {
          return true;
        }
        if (emailOptions.soon && (user.tasks_1_3_days.length > 0 || user.subtasks_1_3_days.length > 0)) {
          return true;
        }
        if (emailOptions.week && (user.tasks_4_7_days.length > 0 || user.subtasks_4_7_days.length > 0)) {
          return true;
        }
        return false;
      });

      if (usersToEmail.length === 0) {
        setEmailStatus('ℹ️ No hay usuarios con tareas que cumplan los criterios seleccionados.');
        return;
      }

      // Obtener configuración de EmailJS desde variables de entorno o estado
      const serviceId = import.meta.env.VITE_EMAILJS_SERVICE_ID || emailjsConfig.serviceId;
      const templateId = import.meta.env.VITE_EMAILJS_TEMPLATE_ID || emailjsConfig.templateId;
      const publicKey = import.meta.env.VITE_EMAILJS_PUBLIC_KEY || emailjsConfig.publicKey;

      // Inicializar EmailJS
      if (publicKey) {
        try {
          emailjs.init(publicKey);
        } catch (initErr) {
          console.error('Error al inicializar EmailJS:', initErr);
          setEmailStatus('❌ Error al inicializar EmailJS. Verifica tu Public Key.');
          return;
        }
      }

      let emailsSent = 0;
      let errors = 0;

      // Enviar correo a cada usuario
      for (const user of usersToEmail) {
        try {
          const emailContent = formatEmailContent(
            user,
            emailOptions.overdue,
            emailOptions.soon,
            emailOptions.week
          );

          const subject = user.overdue_tasks.length > 0 || user.overdue_subtasks.length > 0
            ? '[URGENTE] Recordatorios de Tareas - Tablero Kanban'
            : 'Recordatorios de Tareas - Tablero Kanban';

          // Crear formulario oculto para usar sendForm como muestra la imagen
          const form = document.createElement('form');
          form.style.display = 'none';
          
          // Agregar campos al formulario
          const toEmailInput = document.createElement('input');
          toEmailInput.type = 'hidden';
          toEmailInput.name = 'to_email';
          toEmailInput.value = user.email;
          form.appendChild(toEmailInput);

          const toNameInput = document.createElement('input');
          toNameInput.type = 'hidden';
          toNameInput.name = 'to_name';
          toNameInput.value = user.full_name;
          form.appendChild(toNameInput);

          const subjectInput = document.createElement('input');
          subjectInput.type = 'hidden';
          subjectInput.name = 'subject';
          subjectInput.value = subject;
          form.appendChild(subjectInput);

          const messageInput = document.createElement('textarea');
          messageInput.name = 'message';
          messageInput.value = emailContent;
          form.appendChild(messageInput);

          const userNameInput = document.createElement('input');
          userNameInput.type = 'hidden';
          userNameInput.name = 'user_name';
          userNameInput.value = user.full_name;
          form.appendChild(userNameInput);

          const totalTasksInput = document.createElement('input');
          totalTasksInput.type = 'hidden';
          totalTasksInput.name = 'total_tasks';
          totalTasksInput.value = user.total_items;
          form.appendChild(totalTasksInput);

          // Agregar formulario al DOM temporalmente
          document.body.appendChild(form);

          // Enviar correo usando EmailJS sendForm (como muestra la imagen)
          await emailjs.sendForm(
            serviceId,
            templateId,
            form,
            publicKey
          );

          // Remover formulario del DOM
          document.body.removeChild(form);

          emailsSent++;
          console.log(`Correo enviado a ${user.email}`);
        } catch (err) {
          errors++;
          console.error(`Error al enviar correo a ${user.email}:`, err);
        }
      }

      const message = `Se enviaron ${emailsSent} correo(s) exitosamente.`;
      const details = errors > 0 ? ` Hubo ${errors} error(es).` : '';
      
      setEmailStatus(`✅ ${message}${details}`);
      setTimeout(() => {
        setShowEmailModal(false);
        setEmailStatus('');
      }, 5000);
    } catch (err) {
      console.error('Error completo:', err);
      if (err.response) {
        // Error de respuesta del servidor
        if (err.response.status === 404) {
          setEmailStatus('❌ Error 404: El endpoint no se encontró. Verifica que el backend esté corriendo y que la ruta /api/board-users-for-reminders/ esté disponible.');
        } else if (err.response.status === 401) {
          setEmailStatus('❌ Error: No estás autenticado. Por favor, inicia sesión nuevamente.');
        } else {
          setEmailStatus(`❌ Error del servidor (${err.response.status}): ${err.response.data?.error || err.message}`);
        }
      } else if (err.request) {
        // Error de red
        setEmailStatus('❌ Error: No se pudo conectar con el servidor. Verifica que el backend esté corriendo en http://localhost:8000');
      } else {
        // Otro tipo de error
        setEmailStatus(`❌ Error al enviar los correos: ${err.message || 'Error desconocido'}`);
      }
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

      {/* Modal para configuración de EmailJS */}
      {showEmailjsConfig && (
        <div className="modal" onClick={(e) => e.target.className === 'modal' && setShowEmailjsConfig(false)}>
          <div className="modal-content">
            <span className="close" onClick={() => setShowEmailjsConfig(false)}>&times;</span>
            <h3>⚙️ Configurar EmailJS</h3>
            <div className="email-form">
              <p className="email-description">
                Para enviar correos desde el frontend, necesitas configurar EmailJS. 
                Obtén tus credenciales desde <a href="https://www.emailjs.com/" target="_blank" rel="noopener noreferrer">emailjs.com</a>
              </p>
              
              <div className="email-options">
                <label className="email-option">
                  <span>Service ID:</span>
                  <input
                    type="text"
                    value={emailjsConfig.serviceId}
                    onChange={(e) => setEmailjsConfig({...emailjsConfig, serviceId: e.target.value})}
                    placeholder="service_xxxxxxx"
                  />
                </label>
                <label className="email-option">
                  <span>Template ID:</span>
                  <input
                    type="text"
                    value={emailjsConfig.templateId}
                    onChange={(e) => setEmailjsConfig({...emailjsConfig, templateId: e.target.value})}
                    placeholder="template_xxxxxxx"
                  />
                </label>
                <label className="email-option">
                  <span>Public Key:</span>
                  <input
                    type="text"
                    value={emailjsConfig.publicKey}
                    onChange={(e) => setEmailjsConfig({...emailjsConfig, publicKey: e.target.value})}
                    placeholder="xxxxxxxxxxxxx"
                  />
                </label>
              </div>

              <div className="email-actions">
                <button type="button" className="btn-submit" onClick={() => {
                  if (!emailjsConfig.serviceId || !emailjsConfig.templateId || !emailjsConfig.publicKey) {
                    setEmailStatus('❌ Por favor, completa todos los campos.');
                    return;
                  }
                  try {
                    localStorage.setItem('emailjs_config', JSON.stringify(emailjsConfig));
                    if (emailjsConfig.publicKey) {
                      try {
                        emailjs.init(emailjsConfig.publicKey);
                      } catch (initErr) {
                        console.error('Error al inicializar EmailJS:', initErr);
                        setEmailStatus('❌ Error al inicializar EmailJS. Verifica tu Public Key.');
                        return;
                      }
                    }
                    setShowEmailjsConfig(false);
                    setEmailStatus('✅ Configuración guardada exitosamente.');
                    setTimeout(() => setEmailStatus(''), 3000);
                  } catch (err) {
                    console.error('Error al guardar configuración EmailJS:', err);
                    setEmailStatus('❌ Error al guardar la configuración. Por favor, verifica los datos.');
                  }
                }}>
                  💾 Guardar Configuración
                </button>
                <button type="button" className="btn-cancel" onClick={() => setShowEmailjsConfig(false)}>
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal para envío de correos */}
      {showEmailModal && (
        <div className="modal" onClick={(e) => e.target.className === 'modal' && setShowEmailModal(false)}>
          <div className="modal-content">
            <span className="close" onClick={() => setShowEmailModal(false)}>&times;</span>
            <h3>📧 Enviar Recordatorios por Correo</h3>
            <div className="email-form">
              <p className="email-description">
                Selecciona qué tipo de recordatorios deseas enviar. Los correos se enviarán a todos los usuarios con acceso al tablero.
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
                <button type="button" className="btn-cancel" onClick={() => setShowEmailjsConfig(true)} style={{ marginLeft: '10px' }}>
                  ⚙️ Configurar EmailJS
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
