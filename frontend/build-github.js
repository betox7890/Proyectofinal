// Script para construir el frontend para GitHub Pages
// Funciona en Windows y Linux
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Copiar vite.config.github.js a vite.config.js
const githubConfig = path.join(__dirname, 'vite.config.github.js');
const mainConfig = path.join(__dirname, 'vite.config.js');

try {
  // Copiar config de GitHub
  fs.copyFileSync(githubConfig, mainConfig);
  console.log('✅ Configuración de GitHub copiada');
  
  // Ejecutar build
  console.log('🔨 Construyendo frontend...');
  execSync('npm run build', { stdio: 'inherit', cwd: __dirname });
  
  console.log('✅ Build completado para GitHub Pages');
} catch (error) {
  console.error('❌ Error en el build:', error);
  process.exit(1);
}

