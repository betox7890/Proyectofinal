import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // En desarrollo: usar "/", en producción se cambia a "/Proyectofinal/" con build-github.js
  base: "/",
  server: { port: 5173 }
});

