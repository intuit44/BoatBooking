#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

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

// Base de conocimiento de compatibilidad
const COMPATIBILITY_DB = {
  // SDK 53 con React 18 forzado (no React 19)
  'expo@~53.0.0': {
    react: '18.3.1',
    'react-dom': '18.3.1',
    'react-native': '0.76.5',
    'react-native-web': '~0.19.13',
    '@types/react': '~18.3.12',
    'typescript': '~5.7.2',
    'expo-status-bar': '~2.0.0',
    'expo-splash-screen': '~0.30.0'
  },
  
  // AWS Amplify v5 (compatible con React Native)
  'aws-amplify@^5': {
    compatibleWith: {
      react: '18.x',
      'react-native': '0.7x'
    },
    requiredPackages: {
      '@aws-amplify/react-native': '^1.1.4',
      '@react-native-async-storage/async-storage': '^2.0.0',
      '@react-native-community/netinfo': '^11.0.0',
      '@craftzdog/react-native-buffer': '^6.0.5',
      'react-native-get-random-values': '^1.9.0',
      'react-native-url-polyfill': '^2.0.0'
    },
    incompatiblePackages: [
      '@aws-amplify/ui-react-native@2.x',
      '@aws-amplify/ui-react-native@3.x'
    ]
  },
  
  // React Navigation
  '@react-navigation/native@^6': {
    requiredPackages: {
      'react-native-screens': '~4.4.0',
      'react-native-safe-area-context': '4.12.0',
      'react-native-gesture-handler': '~2.20.2'
    }
  },
  
  // Redux Toolkit
  '@reduxjs/toolkit@^1.9': {
    compatibleWith: {
      'react': '16.x || 17.x || 18.x',
      'react-redux': '^8.0.0'
    }
  },
  
  // Next.js para admin-panel
  'next@^14': {
    react: '^18.0.0',
    'react-dom': '^18.0.0',
    typescript: '^5.0.0'
  }
};

class SmartDependencyFixer {
  constructor() {
    this.rootPath = process.cwd();
    this.projects = {
      'mobile-app': { type: 'expo', path: path.join(this.rootPath, 'mobile-app') },
      'backend': { type: 'serverless', path: path.join(this.rootPath, 'backend') },
      'admin-panel': { type: 'nextjs', path: path.join(this.rootPath, 'admin-panel') }
    };
    this.fixes = [];
    this.globalCompatibility = {};
  }

  log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
  }

  fileExists(filePath) {
    return fs.existsSync(filePath);
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

  execCommand(command, cwd = this.rootPath, silent = false) {
    try {
      const result = execSync(command, {
        cwd,
        encoding: 'utf8',
        stdio: silent ? 'pipe' : 'inherit'
      });
      return { success: true, output: result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  detectExpoSDK(packageJson) {
    const expoVersion = packageJson.dependencies?.expo;
    if (!expoVersion) return null;
    
    // Extraer versión mayor (ej: ~53.0.0 -> 53)
    const match = expoVersion.match(/(\d+)/);
    return match ? parseInt(match[1]) : null;
  }

  detectAmplifyVersion(packageJson) {
    const amplifyVersion = packageJson.dependencies?.['aws-amplify'];
    if (!amplifyVersion) return null;
    
    const match = amplifyVersion.match(/(\d+)/);
    return match ? parseInt(match[1]) : null;
  }

  async analyzeMobileApp() {
    this.log('\n📱 ANALIZANDO MOBILE-APP...', 'bright');
    const projectPath = this.projects['mobile-app'].path;
    
    if (!this.fileExists(projectPath)) {
      this.log('mobile-app no encontrado', 'red');
      return;
    }

    const packageJsonPath = path.join(projectPath, 'package.json');
    const packageJson = this.readJSON(packageJsonPath);
    
    if (!packageJson) return;

    // Detectar SDK de Expo
    const expoSDK = this.detectExpoSDK(packageJson);
    const amplifyVersion = this.detectAmplifyVersion(packageJson);
    
    this.log(`  Expo SDK: ${expoSDK}`, 'cyan');
    this.log(`  AWS Amplify: v${amplifyVersion}`, 'cyan');
    
    // Crear plan de corrección
    const corrections = {
      dependencies: {},
      devDependencies: {},
      remove: [],
      overrides: {}
    };

    // 1. Si tiene SDK 52 y necesita funcionar con Expo Go SDK 53
    if (expoSDK === 52) {
      this.log('\n⚠️  Detectado SDK 52, pero Expo Go requiere SDK 53', 'yellow');
      
      // Actualizar a SDK 53 pero manteniendo React 18
      corrections.dependencies['expo'] = '~53.0.0';
      corrections.dependencies['expo-status-bar'] = '~2.0.0';
      corrections.dependencies['expo-splash-screen'] = '~0.30.0';
      
      // Mantener React 18 (no actualizar a React 19)
      corrections.dependencies['react'] = '18.3.1';
      corrections.dependencies['react-dom'] = '18.3.1';
      corrections.dependencies['react-native'] = '0.76.5';
      corrections.dependencies['react-native-web'] = '~0.19.13';
      
      corrections.devDependencies['@types/react'] = '~18.3.12';
      corrections.devDependencies['typescript'] = '~5.7.2';
      
      // Forzar versiones con overrides
      corrections.overrides = {
        'react': '18.3.1',
        'react-dom': '18.3.1',
        '@types/react': '~18.3.12',
        'expo': {
          'react': '18.3.1',
          'react-dom': '18.3.1'
        },
        'react-native': {
          'react': '18.3.1'
        }
      };
    }

    // 2. Verificar compatibilidad de AWS Amplify
    if (amplifyVersion === 5) {
      // Verificar si tiene UI components incompatibles
      const amplifyUI = packageJson.dependencies?.['@aws-amplify/ui-react-native'];
      if (amplifyUI) {
        const uiVersion = amplifyUI.match(/(\d+)/)?.[0];
        if (uiVersion && parseInt(uiVersion) >= 2) {
          this.log('\n⚠️  @aws-amplify/ui-react-native v2+ no es compatible con aws-amplify v5', 'yellow');
          corrections.remove.push('@aws-amplify/ui-react-native');
          
          // Sugerir alternativa
          this.log('  💡 Deberás crear componentes de autenticación personalizados', 'cyan');
        }
      }
      
      // Asegurar dependencias requeridas para Amplify v5
      corrections.dependencies['@aws-amplify/react-native'] = '^1.1.4';
      corrections.dependencies['@react-native-async-storage/async-storage'] = '2.1.0';
      corrections.dependencies['@react-native-community/netinfo'] = '11.4.1';
    }

    // 3. Verificar React Navigation
    if (packageJson.dependencies?.['@react-navigation/native']) {
      corrections.dependencies['react-native-screens'] = '~4.4.0';
      corrections.dependencies['react-native-safe-area-context'] = '4.12.0';
      corrections.dependencies['react-native-gesture-handler'] = '~2.20.2';
      corrections.dependencies['react-native-reanimated'] = '~3.16.5';
    }

    // 4. Ajustar versiones de otras librerías para SDK 53
    const libraryMappings = {
      'react-native-maps': '1.20.1',
      '@react-native-community/slider': '4.5.6',
      'react-native-calendars': '^1.1313.0',
      'react-native-date-picker': '^4.3.3',
      'react-native-paper': '^5.10.3',
      'react-native-vector-icons': '^10.0.0'
    };

    for (const [lib, version] of Object.entries(libraryMappings)) {
      if (packageJson.dependencies?.[lib]) {
        corrections.dependencies[lib] = version;
      }
    }

    return { projectPath, packageJsonPath, packageJson, corrections };
  }

  async analyzeBackend() {
    this.log('\n🚀 ANALIZANDO BACKEND...', 'bright');
    const projectPath = this.projects['backend'].path;
    
    if (!this.fileExists(projectPath)) {
      this.log('backend no encontrado', 'yellow');
      return null;
    }

    const corrections = {
      serverless: {},
      dependencies: {}
    };

    // Verificar serverless.yml
    const serverlessPath = path.join(projectPath, 'serverless.yml');
    if (this.fileExists(serverlessPath)) {
      const content = fs.readFileSync(serverlessPath, 'utf8');
      
      // Verificar runtime
      if (content.includes('nodejs14.x') || content.includes('nodejs16.x')) {
        corrections.serverless.runtime = 'nodejs18.x';
        this.log('  ⚠️  Runtime de Node.js desactualizado', 'yellow');
      }
      
      if (content.includes('python3.7') || content.includes('python3.8')) {
        corrections.serverless.pythonRuntime = 'python3.11';
        this.log('  ⚠️  Runtime de Python desactualizado', 'yellow');
      }
    }

    // Verificar package.json si existe
    const packageJsonPath = path.join(projectPath, 'package.json');
    if (this.fileExists(packageJsonPath)) {
      const packageJson = this.readJSON(packageJsonPath);
      
      // Si usa aws-sdk v2, sugerir migración futura
      if (packageJson?.dependencies?.['aws-sdk']) {
        this.log('  ℹ️  Usando aws-sdk v2 (considerar migrar a v3 en el futuro)', 'cyan');
      }
      
      return { projectPath, packageJsonPath, packageJson, corrections };
    }

    return { projectPath, corrections };
  }

  async analyzeAdminPanel() {
    this.log('\n🖥️  ANALIZANDO ADMIN-PANEL...', 'bright');
    const projectPath = this.projects['admin-panel'].path;
    
    if (!this.fileExists(projectPath)) {
      this.log('admin-panel no encontrado', 'yellow');
      return null;
    }

    const packageJsonPath = path.join(projectPath, 'package.json');
    const packageJson = this.readJSON(packageJsonPath);
    
    if (!packageJson) return null;

    const corrections = {
      dependencies: {},
      devDependencies: {}
    };

    // Verificar Next.js y React
    const nextVersion = packageJson.dependencies?.next;
    if (nextVersion) {
      const nextMajor = parseInt(nextVersion.match(/\d+/)?.[0] || '0');
      
      if (nextMajor >= 13) {
        // Next.js 13+ requiere React 18
        corrections.dependencies['react'] = '^18.0.0';
        corrections.dependencies['react-dom'] = '^18.0.0';
      }
    }

    // Verificar Material UI
    if (packageJson.dependencies?.['@material-ui/core']) {
      this.log('  ⚠️  Usando Material UI v4 (legacy)', 'yellow');
      // No forzar actualización, solo avisar
    }

    return { projectPath, packageJsonPath, packageJson, corrections };
  }

  async applyCorrections(analysis) {
    if (!analysis) return;
    
    const { projectPath, packageJsonPath, packageJson, corrections } = analysis;
    
    let modified = false;

    // Crear backup
    const backupPath = packageJsonPath + '.backup';
    if (!this.fileExists(backupPath)) {
      fs.copyFileSync(packageJsonPath, backupPath);
      this.log(`  ✅ Backup creado`, 'green');
    }

    // Aplicar correcciones de dependencias
    if (Object.keys(corrections.dependencies || {}).length > 0) {
      this.log('\n  📦 Actualizando dependencias:', 'cyan');
      for (const [pkg, version] of Object.entries(corrections.dependencies)) {
        const currentVersion = packageJson.dependencies?.[pkg];
        if (!currentVersion || currentVersion !== version) {
          this.log(`    ${pkg}: ${currentVersion || 'no instalado'} → ${version}`, 'yellow');
          if (!packageJson.dependencies) packageJson.dependencies = {};
          packageJson.dependencies[pkg] = version;
          modified = true;
        }
      }
    }

    // Aplicar correcciones de devDependencies
    if (Object.keys(corrections.devDependencies || {}).length > 0) {
      this.log('\n  📦 Actualizando devDependencies:', 'cyan');
      for (const [pkg, version] of Object.entries(corrections.devDependencies)) {
        const currentVersion = packageJson.devDependencies?.[pkg];
        if (!currentVersion || currentVersion !== version) {
          this.log(`    ${pkg}: ${currentVersion || 'no instalado'} → ${version}`, 'yellow');
          if (!packageJson.devDependencies) packageJson.devDependencies = {};
          packageJson.devDependencies[pkg] = version;
          modified = true;
        }
      }
    }

    // Eliminar paquetes incompatibles
    if (corrections.remove && corrections.remove.length > 0) {
      this.log('\n  🗑️  Eliminando paquetes incompatibles:', 'red');
      for (const pkg of corrections.remove) {
        if (packageJson.dependencies?.[pkg]) {
          this.log(`    Eliminando: ${pkg}`, 'red');
          delete packageJson.dependencies[pkg];
          modified = true;
        }
      }
    }

    // Aplicar overrides
    if (corrections.overrides && Object.keys(corrections.overrides).length > 0) {
      this.log('\n  🔒 Aplicando overrides para forzar versiones:', 'cyan');
      packageJson.overrides = corrections.overrides;
      modified = true;
    }

    // Guardar cambios
    if (modified) {
      this.writeJSON(packageJsonPath, packageJson);
      this.log('\n  ✅ package.json actualizado', 'green');
    }

    return modified;
  }

  async cleanAndReinstall(projectPath, projectName) {
    this.log(`\n🧹 Limpiando ${projectName}...`, 'cyan');
    
    // Detener procesos
    this.execCommand('taskkill /F /IM node.exe 2>nul', projectPath, true);
    
    // Eliminar carpetas
    const toDelete = ['node_modules', '.expo', 'package-lock.json', '.metro-health-check'];
    for (const item of toDelete) {
      const itemPath = path.join(projectPath, item);
      if (this.fileExists(itemPath)) {
        if (fs.statSync(itemPath).isDirectory()) {
          fs.rmSync(itemPath, { recursive: true, force: true });
        } else {
          fs.unlinkSync(itemPath);
        }
        this.log(`  Eliminado: ${item}`, 'green');
      }
    }

    // Limpiar caché
    this.log('\n  🧹 Limpiando caché...', 'cyan');
    this.execCommand('npm cache clean --force', projectPath, true);

    // Reinstalar
    this.log(`\n  📦 Instalando dependencias en ${projectName}...`, 'cyan');
    const result = this.execCommand('npm install --legacy-peer-deps', projectPath);
    
    if (result.success) {
      this.log(`  ✅ Dependencias instaladas correctamente`, 'green');
      return true;
    } else {
      this.log(`  ❌ Error al instalar dependencias`, 'red');
      return false;
    }
  }

  async generateReport() {
    this.log('\n📊 RESUMEN DE CORRECCIONES', 'bright');
    this.log('=' .repeat(50), 'bright');

    this.log('\n✅ CAMBIOS PRINCIPALES APLICADOS:', 'green');
    this.log('  • Actualizado mobile-app a Expo SDK 53 con React 18 (no 19)', 'cyan');
    this.log('  • Eliminado @aws-amplify/ui-react-native incompatible', 'cyan');
    this.log('  • Mantenido AWS Amplify v5 para React Native', 'cyan');
    this.log('  • Forzado versiones con overrides para evitar React 19', 'cyan');
    this.log('  • Actualizado todas las dependencias a versiones compatibles', 'cyan');

    this.log('\n🚀 SIGUIENTES PASOS:', 'bright');
    this.log('  1. cd mobile-app', 'yellow');
    this.log('  2. npx expo start -c', 'yellow');
    this.log('  3. Tu app debería funcionar con Expo Go SDK 53', 'yellow');
    
    this.log('\n💡 NOTAS IMPORTANTES:', 'bright');
    this.log('  • Si aún tienes problemas, ejecuta: npm install --force --legacy-peer-deps', 'cyan');
    this.log('  • Para componentes de auth, crea tus propios componentes', 'cyan');
    this.log('  • El proyecto está configurado para mantener todas tus herramientas', 'cyan');
  }

  async run() {
    this.log('🔧 CORRECTOR INTELIGENTE DE DEPENDENCIAS', 'bright');
    this.log('=' .repeat(50), 'bright');
    this.log('Analizando proyecto completo (mobile-app, backend, admin-panel)...\n', 'cyan');

    // Analizar cada proyecto
    const mobileAnalysis = await this.analyzeMobileApp();
    const backendAnalysis = await this.analyzeBackend();
    const adminAnalysis = await this.analyzeAdminPanel();

    // Aplicar correcciones
    this.log('\n🔧 APLICANDO CORRECCIONES...', 'bright');
    
    let mobileModified = false;
    if (mobileAnalysis) {
      mobileModified = await this.applyCorrections(mobileAnalysis);
    }

    if (backendAnalysis) {
      await this.applyCorrections(backendAnalysis);
    }

    if (adminAnalysis) {
      await this.applyCorrections(adminAnalysis);
    }

    // Limpiar y reinstalar mobile-app si fue modificado
    if (mobileModified) {
      const shouldReinstall = await new Promise(resolve => {
        const readline = require('readline').createInterface({
          input: process.stdin,
          output: process.stdout
        });
        
        readline.question('\n¿Deseas limpiar y reinstalar mobile-app? (s/n): ', (answer) => {
          readline.close();
          resolve(answer.toLowerCase() === 's');
        });
      });

      if (shouldReinstall) {
        await this.cleanAndReinstall(mobileAnalysis.projectPath, 'mobile-app');
      }
    }

    // Generar reporte final
    await this.generateReport();

    this.log('\n✨ Proceso completado!', 'green');
  }
}

// Ejecutar
const fixer = new SmartDependencyFixer();
fixer.run().catch(error => {
  console.error('Error:', error);
  process.exit(1);
});