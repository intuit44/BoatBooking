const fs = require('fs');
const { execSync } = require('child_process');

console.log('🔧 Solucionando problema de TypeScript definitivamente...');

// Leer package.json
const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));

// Eliminar TypeScript duplicado de dependencies
if (packageJson.dependencies.typescript) {
  delete packageJson.dependencies.typescript;
  console.log('❌ Eliminado TypeScript de dependencies');
}

// Asegurar que esté en devDependencies con la versión correcta
packageJson.devDependencies.typescript = '5.8.3';
console.log('✅ TypeScript configurado en devDependencies: 5.8.3');

// Guardar package.json
fs.writeFileSync('package.json', JSON.stringify(packageJson, null, 2));
console.log('✅ package.json actualizado');

// Instalar dependencias
console.log('📦 Instalando dependencias...');
execSync('npm install', { stdio: 'inherit' });

console.log('🚀 Listo. Ejecuta: npx expo start');