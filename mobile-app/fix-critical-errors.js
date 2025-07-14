const fs = require('fs');
const path = require('path');

console.log('🔧 Corrigiendo errores críticos en package.json...');

// Leer package.json
const packageJsonPath = path.join(__dirname, 'package.json');
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

// Crear backup
const backupPath = `${packageJsonPath}.backup-${Date.now()}`;
fs.copyFileSync(packageJsonPath, backupPath);
console.log(`✅ Backup creado: ${backupPath}`);

// 1. Eliminar la dependencia inválida "undefined"
if (packageJson.dependencies["undefined"]) {
  delete packageJson.dependencies["undefined"];
  console.log('❌ Eliminada dependencia inválida "undefined"');
}

// 2. Corregir @expo/metro-runtime a versión compatible
if (packageJson.dependencies["@expo/metro-runtime"]) {
  packageJson.dependencies["@expo/metro-runtime"] = "~4.0.1";
  console.log('✅ @expo/metro-runtime corregido a ~4.0.1');
}

// 3. Corregir react-native-maps a versión compatible
if (packageJson.dependencies["react-native-maps"]) {
  packageJson.dependencies["react-native-maps"] = "1.18.0";
  console.log('✅ react-native-maps corregido a 1.18.0');
}

// 4. Eliminar @react-native-community/cli de devDependencies (no necesario)
if (packageJson.devDependencies["@react-native-community/cli"]) {
  delete packageJson.devDependencies["@react-native-community/cli"];
  console.log('❌ Eliminado @react-native-community/cli innecesario');
}

// Guardar el archivo corregido
fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
console.log('✅ package.json corregido y guardado');

console.log('\n🎯 Errores críticos corregidos. Ejecuta los siguientes comandos:');
console.log('1. npm install');
console.log('2. npx expo start --clear');