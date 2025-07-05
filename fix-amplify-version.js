#!/usr/bin/env node

/**
 * 🔧 FIX AWS AMPLIFY VERSION
 * Corrige la versión de AWS Amplify a una que existe
 */

const fs = require('fs');
const path = require('path');

const packagePath = path.join('mobile-app', 'package.json');

try {
  // Leer package.json
  const content = fs.readFileSync(packagePath, 'utf8');
  const packageJson = JSON.parse(content);
  
  console.log('🔍 Verificando versión de AWS Amplify...\n');
  
  let modified = false;
  
  // Corregir AWS Amplify
  if (packageJson.dependencies && packageJson.dependencies['aws-amplify']) {
    const currentVersion = packageJson.dependencies['aws-amplify'];
    console.log(`Versión actual: ${currentVersion}`);
    
    if (currentVersion === '^5.3.29' || currentVersion === '5.3.29') {
      packageJson.dependencies['aws-amplify'] = '^5.3.27';
      console.log('✅ Corregida a: ^5.3.27 (última versión v5 disponible)');
      modified = true;
    }
  }
  
  // También verificar y sugerir cambio de React 19 a 18
  if (packageJson.dependencies && packageJson.dependencies['react'] === '19.0.0') {
    console.log('\n⚠️  Detectado React 19.0.0');
    console.log('Se recomienda cambiar a React 18.3.1 para mejor compatibilidad');
    
    // Descomentar para cambiar automáticamente:
    // packageJson.dependencies['react'] = '18.3.1';
    // packageJson.dependencies['react-dom'] = '18.3.1';
    // modified = true;
  }
  
  if (modified) {
    // Backup
    const backupPath = packagePath + '.backup-' + Date.now();
    fs.writeFileSync(backupPath, content);
    console.log(`\n✅ Backup creado: ${backupPath}`);
    
    // Guardar
    fs.writeFileSync(packagePath, JSON.stringify(packageJson, null, 2));
    console.log('✅ package.json actualizado\n');
    
    console.log('📋 Ahora ejecuta:');
    console.log('1. rm -rf node_modules package-lock.json');
    console.log('2. npm install');
    console.log('   o si hay problemas: npm install --force');
  } else {
    console.log('✅ Las versiones ya están correctas');
  }
  
} catch (error) {
  console.error('❌ Error:', error.message);
}