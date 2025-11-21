// Configuración de Vite para GitHub Pages (base: "/Proyectofinal/")
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/Proyectofinal/", // Para GitHub Pages
  server: { port: 5173 }
});

