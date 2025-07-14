const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Ruta al archivo package.json
const packageJsonPath = path.join(__dirname, '..', 'package.json');

// Leer el archivo package.json
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

// Dependencias a actualizar según el mensaje de error de Expo
const dependenciesToUpdate = {
  '@expo/metro-runtime': '~4.0.1',
  '@react-native-async-storage/async-storage': '1.23.1',
  '@react-native-community/datetimepicker': '8.2.0',
  '@react-native-community/slider': '4.5.5',
  'react-native': '0.76.9',
  'react-native-maps': '1.18.0',
  'react-native-safe-area-context': '4.12.0'
};

// Actualizar las versiones en el package.json
let updatedDependencies = false;
for (const [dependency, version] of Object.entries(dependenciesToUpdate)) {
  if (packageJson.dependencies[dependency]) {
    console.log(`Actualizando ${dependency} a ${version}`);
    packageJson.dependencies[dependency] = version;
    updatedDependencies = true;
  }
}

if (updatedDependencies) {
  // Crear una copia de seguridad del package.json actual
  const backupPath = `${packageJsonPath}.backup-${Date.now()}`;
  fs.copyFileSync(packageJsonPath, backupPath);
  console.log(`Copia de seguridad creada en: ${backupPath}`);

  // Guardar el package.json actualizado
  fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
  console.log('package.json actualizado correctamente');

  // Ejecutar npm install para aplicar los cambios
  console.log('Ejecutando npm install para aplicar los cambios...');
  try {
    execSync('npm install', { stdio: 'inherit', cwd: path.join(__dirname, '..') });
    console.log('Dependencias actualizadas correctamente');
  } catch (error) {
    console.error('Error al ejecutar npm install:', error.message);
  }
} else {
  console.log('No se encontraron dependencias para actualizar');
}