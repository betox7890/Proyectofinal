// Script para construir el frontend para Render
// Funciona en Windows y Linux
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Copiar vite.config.render.js a vite.config.js
const renderConfig = path.join(__dirname, 'vite.config.render.js');
const mainConfig = path.join(__dirname, 'vite.config.js');
const githubConfig = path.join(__dirname, 'vite.config.github.js');

try {
  // Copiar config de Render
  fs.copyFileSync(renderConfig, mainConfig);
  console.log('✅ Configuración de Render copiada');
  
  // Ejecutar build
  console.log('🔨 Construyendo frontend...');
  execSync('npm run build', { stdio: 'inherit', cwd: __dirname });
  
  // Restaurar config de GitHub
  fs.copyFileSync(githubConfig, mainConfig);
  console.log('✅ Configuración de GitHub restaurada');
  
  console.log('✅ Build completado para Render');
} catch (error) {
  console.error('❌ Error en el build:', error);
  // Restaurar config de GitHub en caso de error
  if (fs.existsSync(githubConfig)) {
    fs.copyFileSync(githubConfig, mainConfig);
  }
  process.exit(1);
}

