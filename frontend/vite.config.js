import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Escuchar en todas las interfaces
    port: 5173,
    strictPort: false, // Si el puerto está ocupado, usar el siguiente disponible
    // Proxy para redirigir peticiones API al backend Django
    // Esto permite que frontend y backend estén en el mismo dominio
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        // Mantener las cookies y headers
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            // Asegurar que las cookies se envíen
            if (req.headers.cookie) {
              proxyReq.setHeader('Cookie', req.headers.cookie);
            }
          });
        },
      },
      // También proxy para rutas del backend tradicional si es necesario
      '/logout': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/calendar': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
