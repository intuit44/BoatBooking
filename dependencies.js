#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const readline = require('readline');

// Colores para la consola
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

class DependencyFixer {
  constructor() {
    this.rootPath = process.cwd();
    this.fixes = [];
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
  }

  log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
  }

  async prompt(question) {
    return new Promise((resolve) => {
      this.rl.question(`${colors.yellow}${question} (y/n): ${colors.reset}`, (answer) => {
        resolve(answer.toLowerCase() === 'y');
      });
    });
  }

  execCommand(command, cwd = this.rootPath) {
    try {
      this.log(`Ejecutando: ${command}`, 'cyan');
      const result = execSync(command, {
        cwd,
        encoding: 'utf8',
        stdio: 'inherit'
      });
      return true;
    } catch (error) {
      this.log(`Error ejecutando comando: ${error.message}`, 'red');
      return false;
    }
  }

  readJSON(filePath) {
    try {
      return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    } catch (error) {
      return null;
    }
  }

  writeJSON(filePath, data) {
    try {
      fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
      return true;
    } catch (error) {
      this.log(`Error escribiendo ${filePath}: ${error.message}`, 'red');
      return false;
    }
  }

  async fixMobileApp() {
    this.log('\n🔧 CORRIGIENDO mobile-app...', 'bright');
    const projectPath = path.join(this.rootPath, 'mobile-app');
    
    if (!fs.existsSync(projectPath)) {
      this.log('mobile-app no encontrado', 'red');
      return;
    }

    const packageJsonPath = path.join(projectPath, 'package.json');
    let packageJson = this.readJSON(packageJsonPath);
    
    if (!packageJson) {
      this.log('No se pudo leer package.json', 'red');
      return;
    }

    // Backup del package.json original
    const backupPath = path.join(projectPath, 'package.json.backup');
    if (!fs.existsSync(backupPath)) {
      fs.copyFileSync(packageJsonPath, backupPath);
      this.log('Backup creado: package.json.backup', 'green');
    }

    let modified = false;

    // 1. ELIMINAR @aws-amplify/ui-react-native si existe
    if (packageJson.dependencies['@aws-amplify/ui-react-native']) {
      this.log('\n⚠️  Encontrado: @aws-amplify/ui-react-native (incompatible con aws-amplify v5)', 'yellow');
      
      if (await this.prompt('¿Eliminar @aws-amplify/ui-react-native?')) {
        delete packageJson.dependencies['@aws-amplify/ui-react-native'];
        modified = true;
        this.log('✅ Eliminado @aws-amplify/ui-react-native', 'green');
      }
    }

    // 2. CORREGIR versiones para Expo SDK 52
    const correctVersions = {
      "expo": "~52.0.0",
      "react": "18.3.1",
      "react-dom": "18.3.1",
      "react-native": "0.76.5",
      "react-native-web": "~0.19.13",
      "@types/react": "~18.3.12",
      "typescript": "~5.7.2",
      "aws-amplify": "^5.3.27",
      "@aws-amplify/react-native": "^1.1.4"
    };

    this.log('\n📋 Verificando versiones principales...', 'cyan');
    
    for (const [pkg, correctVersion] of Object.entries(correctVersions)) {
      const currentVersion = packageJson.dependencies?.[pkg] || packageJson.devDependencies?.[pkg];
      
      if (currentVersion && currentVersion !== correctVersion) {
        this.log(`\n${pkg}: ${currentVersion} → ${correctVersion}`, 'yellow');
        
        if (await this.prompt(`¿Actualizar ${pkg}?`)) {
          if (packageJson.dependencies?.[pkg]) {
            packageJson.dependencies[pkg] = correctVersion;
          } else if (packageJson.devDependencies?.[pkg]) {
            packageJson.devDependencies[pkg] = correctVersion;
          }
          modified = true;
        }
      }
    }

    // 3. AGREGAR overrides para forzar versiones
    if (!packageJson.overrides) {
      packageJson.overrides = {};
    }
    
    packageJson.overrides = {
      ...packageJson.overrides,
      "react": "18.3.1",
      "react-dom": "18.3.1",
      "@types/react": "~18.3.12"
    };
    modified = true;

    // 4. SIMPLIFICAR babel.config.js
    const babelPath = path.join(projectPath, 'babel.config.js');
    const simpleBabelConfig = `module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
  };
};`;

    if (fs.existsSync(babelPath)) {
      const currentBabel = fs.readFileSync(babelPath, 'utf8');
      if (currentBabel.includes('plugin-transform')) {
        this.log('\n⚠️  babel.config.js tiene plugins adicionales que pueden causar problemas', 'yellow');
        
        if (await this.prompt('¿Simplificar babel.config.js?')) {
          fs.writeFileSync(babelPath + '.backup', currentBabel);
          fs.writeFileSync(babelPath, simpleBabelConfig);
          this.log('✅ babel.config.js simplificado', 'green');
        }
      }
    }

    // 5. CREAR metro.config.js si no existe
    const metroPath = path.join(projectPath, 'metro.config.js');
    if (!fs.existsSync(metroPath)) {
      const metroConfig = `const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Limpiar caché
config.resetCache = true;

// Resolver problemas de módulos
config.resolver.nodeModulesPaths = ['./node_modules'];

module.exports = config;`;

      if (await this.prompt('¿Crear metro.config.js para resolver problemas de caché?')) {
        fs.writeFileSync(metroPath, metroConfig);
        this.log('✅ metro.config.js creado', 'green');
      }
    }

    // Guardar cambios
    if (modified) {
      this.writeJSON(packageJsonPath, packageJson);
      this.log('\n✅ package.json actualizado', 'green');
    }

    // 6. LIMPIAR Y REINSTALAR
    if (modified || await this.prompt('\n¿Ejecutar limpieza completa y reinstalación?')) {
      this.log('\n🧹 Limpiando proyecto...', 'cyan');
      
      // Matar procesos
      this.execCommand('taskkill /F /IM node.exe 2>nul', projectPath);
      
      // Limpiar todo
      const toDelete = ['node_modules', '.expo', 'package-lock.json', '.metro-health-check'];
      for (const item of toDelete) {
        const itemPath = path.join(projectPath, item);
        if (fs.existsSync(itemPath)) {
          if (fs.statSync(itemPath).isDirectory()) {
            fs.rmSync(itemPath, { recursive: true, force: true });
          } else {
            fs.unlinkSync(itemPath);
          }
          this.log(`Eliminado: ${item}`, 'green');
        }
      }

      // Limpiar caché global
      this.log('\n🧹 Limpiando caché global...', 'cyan');
      this.execCommand('npm cache clean --force');
      
      // Limpiar caché de Metro y Expo
      const tempDir = process.env.TEMP || process.env.TMPDIR;
      if (tempDir) {
        const patterns = ['metro-*', 'haste-*', 'react-*'];
        for (const pattern of patterns) {
          try {
            this.execCommand(`del /s /q "${path.join(tempDir, pattern)}" 2>nul`, projectPath);
          } catch {}
        }
      }

      // Reinstalar
      this.log('\n📦 Instalando dependencias...', 'cyan');
      const installed = this.execCommand('npm install --legacy-peer-deps', projectPath);
      
      if (installed) {
        this.log('\n✅ Dependencias instaladas correctamente', 'green');
        
        // Intentar iniciar
        if (await this.prompt('\n¿Iniciar Expo para probar?')) {
          this.log('\n🚀 Iniciando Expo...', 'cyan');
          this.log('Presiona Ctrl+C para detener\n', 'yellow');
          this.execCommand('npx expo start -c', projectPath);
        }
      }
    }
  }

  async fixBackend() {
    this.log('\n🔧 VERIFICANDO backend...', 'bright');
    const projectPath = path.join(this.rootPath, 'backend');
    
    if (!fs.existsSync(projectPath)) {
      this.log('backend no encontrado', 'yellow');
      return;
    }

    // Verificar serverless.yml
    const serverlessPath = path.join(projectPath, 'serverless.yml');
    if (fs.existsSync(serverlessPath)) {
      let serverlessContent = fs.readFileSync(serverlessPath, 'utf8');
      let modified = false;

      // Actualizar runtime si es antiguo
      if (serverlessContent.includes('nodejs14.x') || serverlessContent.includes('nodejs16.x')) {
        this.log('\n⚠️  Runtime de Node.js desactualizado en serverless.yml', 'yellow');
        
        if (await this.prompt('¿Actualizar a nodejs18.x?')) {
          serverlessContent = serverlessContent.replace(/nodejs(14|16)\.x/g, 'nodejs18.x');
          fs.writeFileSync(serverlessPath, serverlessContent);
          this.log('✅ Runtime actualizado a nodejs18.x', 'green');
          modified = true;
        }
      }

      // Python runtime
      if (serverlessContent.includes('python3.7') || serverlessContent.includes('python3.8')) {
        this.log('\n⚠️  Runtime de Python desactualizado', 'yellow');
        
        if (await this.prompt('¿Actualizar a python3.11?')) {
          serverlessContent = serverlessContent.replace(/python3\.[78]/g, 'python3.11');
          fs.writeFileSync(serverlessPath, serverlessContent);
          this.log('✅ Runtime actualizado a python3.11', 'green');
          modified = true;
        }
      }
    }

    // Verificar package.json del backend
    const packageJsonPath = path.join(projectPath, 'package.json');
    if (fs.existsSync(packageJsonPath)) {
      const packageJson = this.readJSON(packageJsonPath);
      
      if (packageJson?.dependencies?.['aws-sdk']) {
        this.log('\n⚠️  Usando aws-sdk v2 (legacy)', 'yellow');
        this.log('Considera migrar a @aws-sdk/* v3 en el futuro', 'cyan');
      }
    }
  }

  async createEmergencyFix() {
    this.log('\n🚨 MODO EMERGENCIA - Creando configuración mínima funcional', 'bright');
    
    const mobileAppPath = path.join(this.rootPath, 'mobile-app');
    
    if (!fs.existsSync(mobileAppPath)) {
      this.log('Error: mobile-app no encontrado', 'red');
      return;
    }

    // Package.json mínimo que DEBE funcionar
    const minimalPackageJson = {
      "name": "boat-rental-app",
      "version": "1.0.0",
      "main": "node_modules/expo/AppEntry.js",
      "scripts": {
        "start": "expo start",
        "android": "expo start --android",
        "ios": "expo start --ios",
        "web": "expo start --web"
      },
      "dependencies": {
        "expo": "~52.0.0",
        "expo-status-bar": "~2.0.0",
        "react": "18.3.1",
        "react-dom": "18.3.1",
        "react-native": "0.76.5",
        "react-native-web": "~0.19.13",
        "react-native-safe-area-context": "4.12.0",
        "react-native-screens": "4.4.0"
      },
      "devDependencies": {
        "@babel/core": "^7.25.2"
      },
      "private": true
    };

    // App.js mínima
    const minimalApp = `import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

export default function App() {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>✅ App Funcionando!</Text>
      <Text style={styles.subtext}>Configuración de emergencia activa</Text>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#0066CC',
    marginBottom: 10,
  },
  subtext: {
    fontSize: 16,
    color: '#666',
  },
});`;

    if (await this.prompt('¿Aplicar configuración de emergencia? (Esto creará una app mínima funcional)')) {
      // Backup
      const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
      const backupDir = path.join(mobileAppPath, `backup-${timestamp}`);
      
      fs.mkdirSync(backupDir, { recursive: true });
      
      // Backup de archivos importantes
      const filesToBackup = ['package.json', 'App.tsx', 'App.js', 'babel.config.js'];
      for (const file of filesToBackup) {
        const filePath = path.join(mobileAppPath, file);
        if (fs.existsSync(filePath)) {
          fs.copyFileSync(filePath, path.join(backupDir, file));
        }
      }
      
      this.log(`✅ Backup creado en: backup-${timestamp}`, 'green');

      // Aplicar configuración mínima
      this.writeJSON(path.join(mobileAppPath, 'package.json'), minimalPackageJson);
      fs.writeFileSync(path.join(mobileAppPath, 'App.js'), minimalApp);
      
      // Babel config simple
      const simpleBabel = `module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
  };
};`;
      fs.writeFileSync(path.join(mobileAppPath, 'babel.config.js'), simpleBabel);

      // Eliminar App.tsx si existe (para evitar conflictos)
      const appTsxPath = path.join(mobileAppPath, 'App.tsx');
      if (fs.existsSync(appTsxPath)) {
        fs.renameSync(appTsxPath, path.join(backupDir, 'App.tsx.original'));
      }

      this.log('\n✅ Configuración de emergencia aplicada', 'green');
      
      // Limpiar e instalar
      this.log('\n🧹 Limpiando completamente...', 'cyan');
      
      const toDelete = ['node_modules', '.expo', 'package-lock.json', '.metro-health-check'];
      for (const item of toDelete) {
        const itemPath = path.join(mobileAppPath, item);
        if (fs.existsSync(itemPath)) {
          if (fs.statSync(itemPath).isDirectory()) {
            fs.rmSync(itemPath, { recursive: true, force: true });
          } else {
            fs.unlinkSync(itemPath);
          }
        }
      }

      this.execCommand('npm cache clean --force');
      
      this.log('\n📦 Instalando configuración mínima...', 'cyan');
      const installed = this.execCommand('npm install', mobileAppPath);
      
      if (installed) {
        this.log('\n✅ Instalación completada', 'green');
        this.log('\n🎯 SIGUIENTE PASO:', 'bright');
        this.log('1. cd mobile-app', 'cyan');
        this.log('2. npx expo start -c', 'cyan');
        this.log('3. Si funciona, agrega tus dependencias de a una', 'cyan');
        this.log('\nTu código original está en el backup', 'yellow');
      }
    }
  }

  async run() {
    this.log('🔧 AUTO-FIX PARA BOAT RENTAL APP', 'bright');
    this.log('=' .repeat(50), 'bright');
    this.log('Este script intentará corregir automáticamente los problemas\n', 'cyan');

    // Verificar si estamos en el directorio correcto
    const dirs = ['mobile-app', 'backend', 'admin-panel'];
    const foundDirs = dirs.filter(dir => fs.existsSync(path.join(this.rootPath, dir)));
    
    if (foundDirs.length === 0) {
      this.log('Error: No se encontraron los directorios del proyecto', 'red');
      this.log('Asegúrate de ejecutar este script desde la raíz del proyecto', 'yellow');
      this.rl.close();
      return;
    }

    // Preguntar qué hacer
    this.log('\n¿Qué deseas hacer?', 'bright');
    this.log('1. Corregir problemas detectados automáticamente', 'cyan');
    this.log('2. Aplicar configuración de emergencia (app mínima funcional)', 'yellow');
    this.log('3. Ambas (primero intentar corrección, luego emergencia si falla)', 'green');
    
    const choice = await new Promise(resolve => {
      this.rl.question('\nElige una opción (1-3): ', resolve);
    });

    switch (choice) {
      case '1':
        await this.fixMobileApp();
        await this.fixBackend();
        break;
      case '2':
        await this.createEmergencyFix();
        break;
      case '3':
        await this.fixMobileApp();
        await this.fixBackend();
        if (await this.prompt('\n¿Aplicar también configuración de emergencia?')) {
          await this.createEmergencyFix();
        }
        break;
      default:
        this.log('Opción no válida', 'red');
    }

    this.log('\n✨ Proceso completado!', 'green');
    this.rl.close();
  }
}

// Ejecutar
const fixer = new DependencyFixer();
fixer.run().catch(error => {
  console.error('Error:', error);
  process.exit(1);
});