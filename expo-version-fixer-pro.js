#!/usr/bin/env node

/**
 * 🔧 EXPO VERSION COMPATIBILITY FIXER PRO
 * 
 * Corrige automáticamente todas las versiones de dependencias
 * para que sean compatibles con Expo SDK
 * 
 * @author Claude AI Assistant
 * @version 1.0.0
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

// Configuración
const CONFIG = {
  colors: {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    dim: '\x1b[2m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m',
  },
  backupSuffix: `.backup-versions-${Date.now()}`,
};

// Utilidades de logging
const log = {
  info: (msg) => console.log(`${CONFIG.colors.blue}ℹ${CONFIG.colors.reset}  ${msg}`),
  success: (msg) => console.log(`${CONFIG.colors.green}✅${CONFIG.colors.reset} ${msg}`),
  error: (msg) => console.log(`${CONFIG.colors.red}❌${CONFIG.colors.reset} ${msg}`),
  warning: (msg) => console.log(`${CONFIG.colors.yellow}⚠️${CONFIG.colors.reset}  ${msg}`),
  change: (msg) => console.log(`${CONFIG.colors.cyan}  →${CONFIG.colors.reset} ${msg}`),
};

/**
 * Versiones esperadas por Expo según el output
 */
const EXPECTED_VERSIONS = {
  '@expo/metro-runtime': '~5.0.1',
  '@react-native-async-storage/async-storage': '2.1.0',
  '@react-native-community/datetimepicker': '~7.7.0',
  'expo-status-bar': '~2.0.1',
  'react': '19.0.0',
  'react-dom': '19.0.0',
  'react-native': '0.76.3',
  'react-native-gesture-handler': '~2.20.2',
  'react-native-reanimated': '~3.16.3',
  'react-native-safe-area-context': '~4.14.0',
  'react-native-screens': '~4.4.0',
  'react-native-web': '~0.19.13',
  '@types/react': '~18.3.12',
  'typescript': '~5.7.3'
};

/**
 * Dependencias adicionales que pueden necesitar actualización
 */
const ADDITIONAL_FIXES = {
  // React Navigation - compatible con RN 0.76
  '@react-navigation/native': '^6.1.18',
  '@react-navigation/stack': '^6.4.1',
  '@react-navigation/bottom-tabs': '^6.6.1',
  '@react-navigation/native-stack': '^6.11.0',
  
  // AWS Amplify v5
  'aws-amplify': '^5.3.29',
  
  // Otras dependencias críticas
  'expo': '~52.0.0',
  'expo-font': '~13.0.0',
  'expo-splash-screen': '~0.29.0',
  'expo-location': '~18.0.0',
  'expo-image-picker': '~16.0.0',
  
  // Redux
  '@reduxjs/toolkit': '^2.2.7',
  'react-redux': '^9.1.2',
};

/**
 * Analiza el package.json actual
 */
async function analyzePackageJson(projectPath) {
  const packagePath = path.join(projectPath, 'package.json');
  
  try {
    const content = await fs.readFile(packagePath, 'utf8');
    const packageJson = JSON.parse(content);
    
    return {
      path: packagePath,
      content: packageJson,
      original: content
    };
  } catch (error) {
    throw new Error(`No se pudo leer package.json: ${error.message}`);
  }
}

/**
 * Actualiza las versiones en package.json
 */
async function updateVersions(packageInfo) {
  const { content: packageJson, path: packagePath, original } = packageInfo;
  const updates = [];
  
  // Crear backup
  await fs.writeFile(packagePath + CONFIG.backupSuffix, original);
  log.success(`Backup creado: package.json${CONFIG.backupSuffix}`);
  
  // Actualizar dependencies
  if (packageJson.dependencies) {
    for (const [pkg, expectedVersion] of Object.entries(EXPECTED_VERSIONS)) {
      if (packageJson.dependencies[pkg]) {
        const currentVersion = packageJson.dependencies[pkg];
        if (currentVersion !== expectedVersion) {
          updates.push({
            package: pkg,
            from: currentVersion,
            to: expectedVersion,
            type: 'dependencies'
          });
          packageJson.dependencies[pkg] = expectedVersion;
        }
      }
    }
    
    // Actualizar dependencias adicionales
    for (const [pkg, version] of Object.entries(ADDITIONAL_FIXES)) {
      if (packageJson.dependencies[pkg] && !EXPECTED_VERSIONS[pkg]) {
        packageJson.dependencies[pkg] = version;
        updates.push({
          package: pkg,
          to: version,
          type: 'dependencies'
        });
      }
    }
  }
  
  // Actualizar devDependencies
  if (packageJson.devDependencies) {
    // TypeScript y tipos
    if (packageJson.devDependencies['@types/react']) {
      packageJson.devDependencies['@types/react'] = EXPECTED_VERSIONS['@types/react'] || '~18.3.12';
    }
    if (packageJson.devDependencies['typescript']) {
      packageJson.devDependencies['typescript'] = EXPECTED_VERSIONS['typescript'] || '~5.7.3';
    }
    
    // Tipos adicionales compatibles
    const typeVersions = {
      '@types/react-native': '~0.73.0',
      '@types/react-redux': '^7.1.33',
      '@types/jest': '^29.5.12'
    };
    
    for (const [pkg, version] of Object.entries(typeVersions)) {
      if (packageJson.devDependencies[pkg]) {
        packageJson.devDependencies[pkg] = version;
        updates.push({
          package: pkg,
          to: version,
          type: 'devDependencies'
        });
      }
    }
  }
  
  // Guardar package.json actualizado
  await fs.writeFile(packagePath, JSON.stringify(packageJson, null, 2));
  
  return updates;
}

/**
 * Limpia la instalación actual
 */
async function cleanInstallation(projectPath) {
  log.info('Limpiando instalación actual...');
  
  const commands = [
    'rm -rf node_modules',
    'rm -f package-lock.json',
    'rm -f yarn.lock',
    'npm cache clean --force'
  ];
  
  for (const cmd of commands) {
    try {
      execSync(cmd, { cwd: projectPath, stdio: 'ignore' });
      log.success(`Ejecutado: ${cmd}`);
    } catch (error) {
      // Ignorar errores (algunos archivos pueden no existir)
    }
  }
}

/**
 * Instala las dependencias
 */
async function installDependencies(projectPath) {
  log.info('Instalando dependencias con versiones corregidas...');
  
  try {
    execSync('npm install', { 
      cwd: projectPath, 
      stdio: 'inherit'
    });
    log.success('Dependencias instaladas correctamente');
    return true;
  } catch (error) {
    log.error('Error instalando dependencias');
    return false;
  }
}

/**
 * Arregla problemas específicos de iOS
 */
async function fixIOS(projectPath) {
  const iosPath = path.join(projectPath, 'ios');
  
  try {
    await fs.access(iosPath);
    log.info('Corrigiendo configuración iOS...');
    
    // Limpiar pods
    execSync('cd ios && pod deintegrate', { cwd: projectPath, stdio: 'ignore' });
    execSync('cd ios && rm -rf Pods Podfile.lock', { cwd: projectPath, stdio: 'ignore' });
    
    // Reinstalar pods
    execSync('cd ios && pod install', { cwd: projectPath, stdio: 'inherit' });
    log.success('Pods reinstalados correctamente');
  } catch (error) {
    log.warning('No se pudo actualizar iOS (puede ser un proyecto solo Android)');
  }
}

/**
 * Función principal
 */
async function main() {
  console.log(`\n${CONFIG.colors.bright}🔧 EXPO VERSION COMPATIBILITY FIXER PRO${CONFIG.colors.reset}`);
  console.log('======================================================================\n');
  
  const projectPath = 'mobile-app';
  
  try {
    // Paso 1: Analizar package.json
    log.info('📋 Analizando package.json...');
    const packageInfo = await analyzePackageJson(projectPath);
    
    // Paso 2: Actualizar versiones
    log.info('\n📝 Actualizando versiones...');
    const updates = await updateVersions(packageInfo);
    
    // Mostrar cambios
    if (updates.length > 0) {
      console.log(`\n${CONFIG.colors.bright}📊 CAMBIOS REALIZADOS${CONFIG.colors.reset}`);
      console.log('----------------------------------------------------------------------');
      
      updates.forEach(update => {
        if (update.from) {
          log.change(`${update.package}: ${CONFIG.colors.red}${update.from}${CONFIG.colors.reset} → ${CONFIG.colors.green}${update.to}${CONFIG.colors.reset}`);
        } else {
          log.change(`${update.package}: ${CONFIG.colors.green}${update.to}${CONFIG.colors.reset}`);
        }
      });
      
      // Paso 3: Limpiar instalación
      console.log(`\n${CONFIG.colors.bright}🧹 LIMPIEZA${CONFIG.colors.reset}`);
      console.log('----------------------------------------------------------------------');
      await cleanInstallation(projectPath);
      
      // Paso 4: Reinstalar dependencias
      console.log(`\n${CONFIG.colors.bright}📦 INSTALACIÓN${CONFIG.colors.reset}`);
      console.log('----------------------------------------------------------------------');
      const installed = await installDependencies(projectPath);
      
      if (installed) {
        // Paso 5: Arreglar iOS si es necesario
        console.log(`\n${CONFIG.colors.bright}🍎 iOS${CONFIG.colors.reset}`);
        console.log('----------------------------------------------------------------------');
        await fixIOS(projectPath);
      }
      
    } else {
      log.success('Todas las versiones ya son compatibles');
    }
    
    // Instrucciones finales
    console.log(`\n${CONFIG.colors.bright}✅ SIGUIENTES PASOS${CONFIG.colors.reset}`);
    console.log('======================================================================');
    console.log('1. Limpia el cache de Metro:');
    console.log(`   ${CONFIG.colors.cyan}cd mobile-app && npx react-native start --reset-cache${CONFIG.colors.reset}`);
    console.log('\n2. Ejecuta la aplicación:');
    console.log(`   ${CONFIG.colors.cyan}npx expo start --clear${CONFIG.colors.reset}`);
    console.log('   o');
    console.log(`   ${CONFIG.colors.cyan}npx react-native run-ios${CONFIG.colors.reset}`);
    console.log(`   ${CONFIG.colors.cyan}npx react-native run-android${CONFIG.colors.reset}`);
    console.log('\n3. Si hay problemas con tipos de TypeScript:');
    console.log(`   ${CONFIG.colors.cyan}cd mobile-app && npx tsc --skipLibCheck${CONFIG.colors.reset}`);
    
    console.log('\n✨ ¡Proceso completado!\n');
    
  } catch (error) {
    log.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

// Ejecutar
main();