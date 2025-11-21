// Configuración de Vite para Render (base: "/")
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/", // Para Render (sin subdirectorio)
  server: { port: 5173 }
});

