#!/usr/bin/env node

/**
 * 🔧 FORCE EXPO VERSIONS
 * Fuerza las versiones exactas que Expo está pidiendo
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const packagePath = path.join('mobile-app', 'package.json');

// Versiones que Expo está pidiendo según el output
const REQUIRED_VERSIONS = {
  '@expo/metro-runtime': '~4.0.1',
  '@react-native-async-storage/async-storage': '1.23.1',
  '@react-native-community/datetimepicker': '8.2.0',
  '@react-native-community/slider': '4.5.5',
  'react-native': '0.76.9',
  'react-native-maps': '1.18.0',
  'react-native-safe-area-context': '4.12.0'
};

try {
  // Leer package.json
  const content = fs.readFileSync(packagePath, 'utf8');
  const packageJson = JSON.parse(content);
  
  console.log('🔧 Forzando versiones correctas de Expo SDK 52...\n');
  
  // Backup
  const backupPath = packagePath + '.backup-' + Date.now();
  fs.writeFileSync(backupPath, content);
  console.log(`✅ Backup creado: ${backupPath}\n`);
  
  // Actualizar versiones
  let changes = 0;
  for (const [pkg, version] of Object.entries(REQUIRED_VERSIONS)) {
    if (packageJson.dependencies && packageJson.dependencies[pkg]) {
      const oldVersion = packageJson.dependencies[pkg];
      packageJson.dependencies[pkg] = version;
      console.log(`📦 ${pkg}:`);
      console.log(`   ${oldVersion} → ${version}`);
      changes++;
    }
  }
  
  if (changes > 0) {
    // Guardar package.json
    fs.writeFileSync(packagePath, JSON.stringify(packageJson, null, 2));
    console.log(`\n✅ Actualizado ${changes} paquetes\n`);
    
    console.log('🔄 Reinstalando dependencias...\n');
    
    // Cambiar al directorio y ejecutar comandos
    process.chdir('mobile-app');
    
    // Limpiar
    console.log('🧹 Limpiando...');
    try {
      execSync('rm -rf node_modules package-lock.json', { stdio: 'inherit' });
    } catch (e) {
      // En Windows
      execSync('rmdir /s /q node_modules 2>nul & del package-lock.json 2>nul', { shell: true, stdio: 'inherit' });
    }
    
    // Reinstalar
    console.log('\n📦 Instalando...');
    execSync('npm install', { stdio: 'inherit' });
    
    console.log('\n✅ ¡Listo! Ahora ejecuta: npx expo start --clear');
  } else {
    console.log('❌ No se encontraron los paquetes para actualizar');
  }
  
} catch (error) {
  console.error('❌ Error:', error.message);
}