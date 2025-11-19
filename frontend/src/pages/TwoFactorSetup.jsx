import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { kanbanService } from '../services/api';
import './TwoFactorSetup.css';

function TwoFactorSetup() {
  const [profile, setProfile] = useState(null);
  const [qrCode, setQrCode] = useState('');
  const [provisioningUri, setProvisioningUri] = useState('');
  const [totpInterval, setTotpInterval] = useState(30);
  const [code, setCode] = useState('000000');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await kanbanService.getTwoFactorSetup();
      console.log('2FA Setup Response:', response.data);
      if (response.data.success) {
        setProfile(response.data.profile);
        if (response.data.qr_code_data_uri) {
          setQrCode(response.data.qr_code_data_uri);
          console.log('QR Code cargado, longitud:', response.data.qr_code_data_uri.length);
        } else {
          console.error('QR Code no está presente en la respuesta');
          setError('No se pudo generar el código QR. Por favor, intenta nuevamente.');
        }
        setProvisioningUri(response.data.provisioning_uri || '');
        setTotpInterval(response.data.totp_interval || 30);
      } else {
        setError(response.data.error || 'Error al cargar la configuración 2FA');
      }
    } catch (err) {
      console.error('Error completo:', err);
      console.error('Error response:', err.response);
      setError('Error al cargar la configuración 2FA: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleEnable = async (e) => {
    e.preventDefault();
    if (!code || code.length !== 6) {
      setError('Por favor, ingresa un código de 6 dígitos');
      return;
    }

    setActionLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await kanbanService.enableTwoFactor(code);
      if (response.data.success) {
        setMessage(response.data.message);
        setProfile({ ...profile, enabled: true });
        setCode('000000');
        setTimeout(() => {
          navigate('/board');
        }, 2000);
      } else {
        setError(response.data.error || 'Error al habilitar 2FA');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al habilitar 2FA');
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!window.confirm('¿Seguro que deseas generar un nuevo código secreto? Deberás escanear el nuevo código QR antes de habilitar 2FA.')) {
      return;
    }

    setActionLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await kanbanService.regenerateTwoFactorSecret();
      if (response.data.success) {
        setMessage(response.data.message);
        setProfile({ ...profile, enabled: false, secret: response.data.secret });
        setQrCode(response.data.qr_code_data_uri);
        setProvisioningUri(response.data.provisioning_uri);
        setCode('000000');
      } else {
        setError(response.data.error || 'Error al regenerar el secreto');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al regenerar el secreto');
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDisable = async () => {
    if (!window.confirm('¿Seguro que deseas deshabilitar 2FA?')) {
      return;
    }

    setActionLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await kanbanService.disableTwoFactor();
      if (response.data.success) {
        setMessage(response.data.message);
        setProfile({ ...profile, enabled: false });
      } else {
        setError(response.data.error || 'Error al deshabilitar 2FA');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al deshabilitar 2FA');
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="settings-container">
        <div className="loading">Cargando configuración...</div>
      </div>
    );
  }

  return (
    <div className="settings-container">
      <div className="settings-box">
        <div className="two-factor-header">
          <h1>Autenticación de Dos Pasos (TOTP)</h1>
          <Link to="/board" className="btn-back-board">⬅ Volver al tablero</Link>
        </div>

        {message && (
          <div className="message message-success">{message}</div>
        )}
        {error && (
          <div className="message message-error">{error}</div>
        )}

        <section className="two-factor-status">
          <h2>Estado actual</h2>
          <p>2FA: <strong>{profile?.enabled ? 'Activo' : 'Inactivo'}</strong></p>
          <p>Escanea el código QR o ingresa el siguiente código secreto en tu aplicación de autenticación:</p>
          <div className="two-factor-secret">
            <code>{profile?.secret}</code>
          </div>
          <div className="two-factor-qr">
            {qrCode ? (
              <img src={qrCode} alt="Código QR 2FA" onError={(e) => {
                console.error('Error al cargar imagen QR');
                setError('Error al mostrar el código QR. Por favor, recarga la página.');
              }} />
            ) : (
              <div style={{ padding: '20px', color: '#666', textAlign: 'center' }}>
                <p>Generando código QR...</p>
                {error && <p style={{ color: '#ef4444', marginTop: '10px' }}>{error}</p>}
              </div>
            )}
          </div>
          <p className="provisioning-uri">URI de configuración (para importar manualmente):</p>
          <textarea className="provisioning-text" readOnly value={provisioningUri}></textarea>
        </section>

        <section className="two-factor-actions">
          <h2>Acciones</h2>
          <form onSubmit={handleEnable}>
            <div className="form-group">
              <label htmlFor="code">Introduce un código generado por tu app para confirmar:</label>
              <input
                type="text"
                id="code"
                name="code"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength="6"
                placeholder="000000"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                disabled={actionLoading}
              />
            </div>
            <button type="submit" className="btn-submit" disabled={actionLoading}>
              {actionLoading ? 'Procesando...' : 'Habilitar 2FA'}
            </button>
          </form>

          <form className="inline-form" onSubmit={(e) => { e.preventDefault(); handleRegenerate(); }}>
            <button
              type="submit"
              className="btn-secondary"
              disabled={actionLoading}
            >
              Generar nuevo secreto
            </button>
          </form>

          {profile?.enabled && (
            <form className="inline-form" onSubmit={(e) => { e.preventDefault(); handleDisable(); }}>
              <button
                type="submit"
                className="btn-danger"
                disabled={actionLoading}
              >
                Deshabilitar 2FA
              </button>
            </form>
          )}
        </section>

        <div className="two-factor-help">
          <p>Los códigos caducan cada {totpInterval} segundos. Si cambias el secreto, vuelve a escanear el QR antes de habilitar 2FA.</p>
        </div>
      </div>
    </div>
  );
}

export default TwoFactorSetup;

