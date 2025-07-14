const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🔧 Solucionando error de módulo "ora"...');

try {
  // 1. Verificar si ora está instalado
  const nodeModulesPath = path.join(__dirname, 'node_modules');
  const oraPath = path.join(nodeModulesPath, 'ora');
  
  if (!fs.existsSync(oraPath)) {
    console.log('❌ Módulo "ora" no encontrado. Instalando...');
    execSync('npm install ora@5.4.1', { stdio: 'inherit' });
  } else {
    console.log('✅ Módulo "ora" encontrado');
  }

  // 2. Reinstalar @expo/cli para asegurar dependencias correctas
  console.log('🔄 Reinstalando @expo/cli...');
  execSync('npm install @expo/cli@latest', { stdio: 'inherit' });

  // 3. Limpiar caché de npm
  console.log('🧹 Limpiando caché de npm...');
  execSync('npm cache clean --force', { stdio: 'inherit' });

  console.log('✅ Corrección completada. Intenta iniciar la app con: npx expo start');

} catch (error) {
  console.error('❌ Error durante la corrección:', error.message);
  console.log('\n🔄 Intenta la solución manual:');
  console.log('1. npm install ora@5.4.1');
  console.log('2. npm install @expo/cli@latest');
  console.log('3. npx expo start');
}