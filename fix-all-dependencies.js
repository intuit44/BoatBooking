#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const readline = require('readline');

// Colores
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m'
};

class CompleteDependencyFixer {
  constructor() {
    this.rootPath = process.cwd();
    this.changes = [];
    this.globalVersions = {
      react: null,
      typescript: null,
      'aws-amplify': null
    };
    this.projectData = {
      'mobile-app': {},
      'backend': {},
      'admin-panel': {}
    };
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
  }

  log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
  }

  async question(prompt) {
    return new Promise(resolve => {
      this.rl.question(prompt, resolve);
    });
  }

  readJSON(filePath) {
    try {
      return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    } catch (error) {
      return null;
    }
  }

  execCommand(command, cwd = this.rootPath) {
    try {
      this.log(`\n  Ejecutando: ${command}`, 'cyan');
      execSync(command, {
        cwd,
        stdio: 'inherit',
        shell: true
      });
      return true;
    } catch (error) {
      this.log(`  Error: ${error.message}`, 'red');
      return false;
    }
  }

  // VERIFICACIÓN CRUZADA DE VERSIONES
  async crossValidateVersions() {
    this.log('\n🔍 VERIFICACIÓN CRUZADA DE VERSIONES', 'bright');
    this.log('=' .repeat(60), 'cyan');

    // Recopilar todas las versiones de los 3 proyectos
    const projects = ['mobile-app', 'backend', 'admin-panel'];
    const versionMap = {};

    for (const project of projects) {
      const packageJsonPath = path.join(this.rootPath, project, 'package.json');
      if (fs.existsSync(packageJsonPath)) {
        const pkg = this.readJSON(packageJsonPath);
        if (pkg) {
          this.projectData[project] = pkg;
          
          // Recopilar versiones clave
          const deps = { ...pkg.dependencies, ...pkg.devDependencies };
          for (const [key, version] of Object.entries(deps)) {
            if (!versionMap[key]) versionMap[key] = {};
            versionMap[key][project] = version;
          }
        }
      }
    }

    // Analizar conflictos
    const conflicts = [];
    const criticalPackages = ['react', 'typescript', 'aws-amplify', '@types/react'];

    this.log('\n📊 Versiones críticas por proyecto:', 'yellow');
    for (const pkg of criticalPackages) {
      if (versionMap[pkg]) {
        this.log(`\n  ${pkg}:`, 'cyan');
        for (const [project, version] of Object.entries(versionMap[pkg])) {
          this.log(`    ${project}: ${version}`, 'white');
        }
        
        // Detectar conflictos
        const versions = Object.values(versionMap[pkg]);
        const uniqueVersions = [...new Set(versions)];
        if (uniqueVersions.length > 1) {
          conflicts.push({
            package: pkg,
            projects: versionMap[pkg]
          });
        }
      }
    }

    // Reportar conflictos
    if (conflicts.length > 0) {
      this.log('\n⚠️  CONFLICTOS DETECTADOS:', 'red');
      for (const conflict of conflicts) {
        this.log(`\n  ${conflict.package} tiene versiones diferentes:`, 'yellow');
        for (const [project, version] of Object.entries(conflict.projects)) {
          this.log(`    ${project}: ${version}`, 'white');
        }
      }

      // Sugerir versiones unificadas
      this.log('\n💡 VERSIONES RECOMENDADAS PARA UNIFICAR:', 'green');
      this.globalVersions = {
        'react': '18.3.1',
        'react-dom': '18.3.1',
        'typescript': '~5.7.2',
        '@types/react': '~18.3.12',
        'aws-amplify': '^5.3.27'
      };

      for (const [pkg, version] of Object.entries(this.globalVersions)) {
        this.log(`  ${pkg}: ${version}`, 'cyan');
      }
    } else {
      this.log('\n✅ No se detectaron conflictos de versiones críticas', 'green');
    }

    return conflicts;
  }

  async processMobileApp() {
    const mobileAppPath = path.join(this.rootPath, 'mobile-app');
    
    if (!fs.existsSync(mobileAppPath)) {
      this.log('\n❌ No se encuentra mobile-app/', 'red');
      return;
    }

    this.log('\n📱 PROCESANDO MOBILE-APP', 'bright');
    this.log('=' .repeat(60), 'cyan');

    const packageJsonPath = path.join(mobileAppPath, 'package.json');
    
    // PASO 1: Leer package.json actual
    this.log('\n1️⃣ Leyendo package.json actual...', 'yellow');
    let packageJson = this.readJSON(packageJsonPath);
    if (!packageJson) {
      this.log('  ❌ Error leyendo package.json', 'red');
      return;
    }
    this.log('  ✅ package.json leído correctamente', 'green');

    // PASO 2: Crear backup
    this.log('\n2️⃣ Creando backup...', 'yellow');
    const backupPath = packageJsonPath + '.backup-' + Date.now();
    fs.copyFileSync(packageJsonPath, backupPath);
    this.log(`  ✅ Backup creado: ${path.basename(backupPath)}`, 'green');

    // PASO 3: Mostrar versiones actuales
    this.log('\n3️⃣ Versiones actuales:', 'yellow');
    const keysToCheck = [
      'expo', 'react', 'react-dom', 'react-native', 
      'aws-amplify', '@aws-amplify/ui-react-native',
      '@types/react', 'typescript'
    ];
    
    for (const key of keysToCheck) {
      const version = packageJson.dependencies?.[key] || packageJson.devDependencies?.[key];
      if (version) {
        this.log(`  ${key}: ${version}`, 'cyan');
      }
    }

    // PASO 4: Aplicar cambios necesarios
    this.log('\n4️⃣ Aplicando cambios necesarios:', 'yellow');
    
    const updates = {
      dependencies: {
        "expo": "~53.0.0",
        "expo-status-bar": "~2.0.0",
        "expo-splash-screen": "~0.30.0",
        "react": this.globalVersions.react || "18.3.1",
        "react-dom": this.globalVersions['react-dom'] || "18.3.1",
        "react-native": "0.76.5",
        "react-native-web": "~0.19.13",
        "aws-amplify": this.globalVersions['aws-amplify'] || "^5.3.27",
        "@aws-amplify/react-native": "^1.1.4",
        "@react-native-async-storage/async-storage": "2.1.0",
        "react-native-maps": "1.20.1",
        "@react-native-community/slider": "4.5.6",
        "react-native-screens": "~4.4.0",
        "react-native-safe-area-context": "4.12.0",
        "react-native-gesture-handler": "~2.20.2",
        "react-native-reanimated": "~3.16.5"
      },
      devDependencies: {
        "@types/react": this.globalVersions['@types/react'] || "~18.3.12",
        "typescript": this.globalVersions.typescript || "~5.7.2"
      },
      remove: [
        "@aws-amplify/ui-react-native"
      ],
      overrides: {
        "react": this.globalVersions.react || "18.3.1",
        "react-dom": this.globalVersions['react-dom'] || "18.3.1",
        "@types/react": this.globalVersions['@types/react'] || "~18.3.12",
        "expo": {
          "react": this.globalVersions.react || "18.3.1",
          "react-dom": this.globalVersions['react-dom'] || "18.3.1"
        },
        "react-native": {
          "react": this.globalVersions.react || "18.3.1"
        }
      }
    };

    // Aplicar actualizaciones
    for (const [pkg, newVersion] of Object.entries(updates.dependencies)) {
      if (packageJson.dependencies?.[pkg]) {
        const oldVersion = packageJson.dependencies[pkg];
        if (oldVersion !== newVersion) {
          this.log(`  📦 ${pkg}: ${oldVersion} → ${newVersion}`, 'green');
          packageJson.dependencies[pkg] = newVersion;
          this.changes.push(`mobile-app: Actualizado ${pkg} de ${oldVersion} a ${newVersion}`);
        }
      }
    }

    for (const [pkg, newVersion] of Object.entries(updates.devDependencies)) {
      if (packageJson.devDependencies?.[pkg]) {
        const oldVersion = packageJson.devDependencies[pkg];
        if (oldVersion !== newVersion) {
          this.log(`  📦 ${pkg}: ${oldVersion} → ${newVersion}`, 'green');
          packageJson.devDependencies[pkg] = newVersion;
          this.changes.push(`mobile-app: Actualizado ${pkg} de ${oldVersion} a ${newVersion}`);
        }
      }
    }

    // Eliminar paquetes incompatibles
    for (const pkg of updates.remove) {
      if (packageJson.dependencies?.[pkg]) {
        this.log(`  🗑️  Eliminando ${pkg}`, 'red');
        delete packageJson.dependencies[pkg];
        this.changes.push(`mobile-app: Eliminado ${pkg}`);
      }
    }

    // Aplicar overrides
    this.log(`  🔒 Aplicando overrides para forzar versiones`, 'yellow');
    packageJson.overrides = updates.overrides;
    this.changes.push('mobile-app: Aplicados overrides para forzar React 18');

    // PASO 5: Guardar cambios
    this.log('\n5️⃣ Guardando cambios en package.json...', 'yellow');
    try {
      fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
      this.log('  ✅ package.json actualizado correctamente', 'green');
    } catch (error) {
      this.log(`  ❌ Error guardando package.json: ${error.message}`, 'red');
      return;
    }

    // PASO 6: Simplificar babel.config.js
    this.log('\n6️⃣ Simplificando babel.config.js...', 'yellow');
    const babelPath = path.join(mobileAppPath, 'babel.config.js');
    if (fs.existsSync(babelPath)) {
      const babelBackup = babelPath + '.backup-' + Date.now();
      fs.copyFileSync(babelPath, babelBackup);
      
      const simpleBabel = `module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
  };
};`;
      
      fs.writeFileSync(babelPath, simpleBabel);
      this.log('  ✅ babel.config.js simplificado', 'green');
      this.changes.push('mobile-app: Simplificado babel.config.js');
    }

    // PASO 7: Crear metro.config.js
    this.log('\n7️⃣ Creando metro.config.js...', 'yellow');
    const metroPath = path.join(mobileAppPath, 'metro.config.js');
    if (!fs.existsSync(metroPath)) {
      const metroConfig = `const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);
config.resetCache = true;
config.resolver.nodeModulesPaths = ['./node_modules'];

module.exports = config;`;
      
      fs.writeFileSync(metroPath, metroConfig);
      this.log('  ✅ metro.config.js creado', 'green');
      this.changes.push('mobile-app: Creado metro.config.js');
    }

    // PASO 8: Limpiar e instalar
    const shouldClean = await this.question('\n¿Deseas limpiar e instalar mobile-app? (s/n): ');
    
    if (shouldClean.toLowerCase() === 's') {
      await this.cleanAndInstall(mobileAppPath, 'mobile-app');
    }
  }

  async processBackend() {
    const backendPath = path.join(this.rootPath, 'backend');
    const serverlessPath = path.join(backendPath, 'serverless.yml');
    const packageJsonPath = path.join(backendPath, 'package.json');

    if (!fs.existsSync(backendPath)) {
      this.log('\n❌ backend/ no encontrado', 'red');
      return;
    }

    this.log('\n🛠️ PROCESANDO BACKEND', 'bright');
    this.log('=' .repeat(60), 'cyan');

    // Validar runtimes en serverless.yml
    if (fs.existsSync(serverlessPath)) {
      this.log('\n1️⃣ Verificando serverless.yml...', 'yellow');
      let content = fs.readFileSync(serverlessPath, 'utf8');
      let modified = false;
      
      if (content.includes('nodejs14.x') || content.includes('nodejs16.x')) {
        this.log('  ⚠️ Runtime de Node.js obsoleto detectado', 'yellow');
        content = content.replace(/nodejs(14|16)\.x/g, 'nodejs18.x');
        fs.writeFileSync(serverlessPath, content);
        this.log('  ✅ Actualizado runtime Node.js a 18.x', 'green');
        this.changes.push('backend: Actualizado runtime Node.js a 18.x en serverless.yml');
        modified = true;
      }
      
      if (content.includes('python3.7') || content.includes('python3.8')) {
        this.log('  ⚠️ Runtime Python obsoleto detectado', 'yellow');
        content = content.replace(/python3\.[78]/g, 'python3.11');
        fs.writeFileSync(serverlessPath, content);
        this.log('  ✅ Actualizado runtime Python a 3.11', 'green');
        this.changes.push('backend: Actualizado runtime Python a 3.11 en serverless.yml');
        modified = true;
      }
      
      if (!modified) {
        this.log('  ✅ Runtimes actualizados', 'green');
      }
    }

    // Validar package.json si existe
    if (fs.existsSync(packageJsonPath)) {
      this.log('\n2️⃣ Verificando dependencias del backend...', 'yellow');
      const pkg = this.readJSON(packageJsonPath);
      if (pkg) {
        // Verificar aws-sdk
        const awsSdkVersion = pkg.dependencies?.['aws-sdk'];
        if (awsSdkVersion) {
          this.log('  ⚠️ Usando aws-sdk v2 (legacy)', 'yellow');
          this.log('  💡 Considera migrar a @aws-sdk/client-* (modular v3)', 'cyan');
          this.log('     Ejemplo: @aws-sdk/client-s3, @aws-sdk/client-dynamodb', 'cyan');
        }

        // Verificar versiones de typescript si existe
        if (pkg.devDependencies?.typescript) {
          const currentTs = pkg.devDependencies.typescript;
          const targetTs = this.globalVersions.typescript || "~5.7.2";
          if (currentTs !== targetTs) {
            this.log(`  📦 typescript: ${currentTs} → ${targetTs}`, 'yellow');
            const update = await this.question('\n  ¿Actualizar typescript? (s/n): ');
            if (update.toLowerCase() === 's') {
              pkg.devDependencies.typescript = targetTs;
              fs.writeFileSync(packageJsonPath, JSON.stringify(pkg, null, 2));
              this.changes.push(`backend: Actualizado typescript a ${targetTs}`);
            }
          }
        }
      }
    }

    // Preguntar si limpiar backend
    const clean = await this.question('\n¿Deseas limpiar e instalar backend? (s/n): ');
    if (clean.toLowerCase() === 's') {
      await this.cleanAndInstall(backendPath, 'backend');
    }
  }

  async processAdminPanel() {
    const panelPath = path.join(this.rootPath, 'admin-panel');
    if (!fs.existsSync(panelPath)) {
      this.log('\n❌ admin-panel/ no encontrado', 'red');
      return;
    }

    this.log('\n🖥️ PROCESANDO ADMIN PANEL (Next.js)', 'bright');
    this.log('=' .repeat(60), 'cyan');

    const packageJsonPath = path.join(panelPath, 'package.json');
    if (!fs.existsSync(packageJsonPath)) {
      this.log('  ❌ No se encuentra package.json', 'red');
      return;
    }

    const pkg = this.readJSON(packageJsonPath);
    if (!pkg) {
      this.log('  ❌ Error leyendo package.json', 'red');
      return;
    }

    // Crear backup
    const backupPath = packageJsonPath + '.backup-' + Date.now();
    fs.copyFileSync(packageJsonPath, backupPath);
    this.log(`  ✅ Backup creado: ${path.basename(backupPath)}`, 'green');

    // Mostrar versiones actuales
    this.log('\n1️⃣ Versiones actuales:', 'yellow');
    const criticalDeps = ['next', 'react', 'react-dom', '@mui/material', 'typescript'];
    for (const dep of criticalDeps) {
      const version = pkg.dependencies?.[dep] || pkg.devDependencies?.[dep];
      if (version) {
        this.log(`  ${dep}: ${version}`, 'cyan');
      }
    }

    // Definir actualizaciones necesarias
    const updates = {
      dependencies: {
        "react": this.globalVersions.react || "18.3.1",
        "react-dom": this.globalVersions['react-dom'] || "18.3.1"
      },
      devDependencies: {
        "typescript": this.globalVersions.typescript || "~5.7.2",
        "@types/react": this.globalVersions['@types/react'] || "~18.3.12"
      }
    };

    // Verificar compatibilidad con Next.js
    const nextVersion = pkg.dependencies?.next;
    if (nextVersion) {
      const nextMajor = parseInt(nextVersion.match(/\d+/)?.[0] || '0');
      if (nextMajor >= 13 && nextMajor < 15) {
        this.log('\n  ℹ️ Next.js 13+ requiere React 18', 'cyan');
      }
    }

    // Verificar Material UI
    if (pkg.dependencies?.['@material-ui/core']) {
      this.log('\n  ⚠️ Usando Material UI v4 (legacy)', 'yellow');
      this.log('  💡 Considera migrar a @mui/material v5', 'cyan');
      const migrate = await this.question('\n  ¿Migrar a @mui/material v5? (s/n): ');
      if (migrate.toLowerCase() === 's') {
        delete pkg.dependencies['@material-ui/core'];
        delete pkg.dependencies['@material-ui/icons'];
        pkg.dependencies['@mui/material'] = '^5.14.0';
        pkg.dependencies['@emotion/react'] = '^11.11.0';
        pkg.dependencies['@emotion/styled'] = '^11.11.0';
        this.changes.push('admin-panel: Migrado de Material UI v4 a v5');
      }
    }

    // Aplicar actualizaciones
    let modified = false;
    this.log('\n2️⃣ Aplicando actualizaciones:', 'yellow');
    
    for (const [pkg_name, targetVersion] of Object.entries(updates.dependencies)) {
      if (pkg.dependencies?.[pkg_name]) {
        const currentVersion = pkg.dependencies[pkg_name];
        if (currentVersion !== targetVersion) {
          this.log(`  📦 ${pkg_name}: ${currentVersion} → ${targetVersion}`, 'green');
          pkg.dependencies[pkg_name] = targetVersion;
          this.changes.push(`admin-panel: Actualizado ${pkg_name} a ${targetVersion}`);
          modified = true;
        }
      }
    }

    for (const [pkg_name, targetVersion] of Object.entries(updates.devDependencies)) {
      if (pkg.devDependencies?.[pkg_name]) {
        const currentVersion = pkg.devDependencies[pkg_name];
        if (currentVersion !== targetVersion) {
          this.log(`  📦 ${pkg_name}: ${currentVersion} → ${targetVersion}`, 'green');
          pkg.devDependencies[pkg_name] = targetVersion;
          this.changes.push(`admin-panel: Actualizado ${pkg_name} a ${targetVersion}`);
          modified = true;
        }
      }
    }

    if (modified) {
      fs.writeFileSync(packageJsonPath, JSON.stringify(pkg, null, 2));
      this.log('\n  ✅ package.json actualizado', 'green');
    }

    // Verificar tsconfig.json
    const tsconfigPath = path.join(panelPath, 'tsconfig.json');
    if (fs.existsSync(tsconfigPath)) {
      this.log('\n3️⃣ Verificando tsconfig.json...', 'yellow');
      const tsconfig = this.readJSON(tsconfigPath);
      if (tsconfig?.compilerOptions?.jsx !== 'preserve') {
        this.log('  ⚠️ jsx debería ser "preserve" para Next.js', 'yellow');
      } else {
        this.log('  ✅ tsconfig.json configurado correctamente', 'green');
      }
    }

    // Limpiar e instalar
    const clean = await this.question('\n¿Deseas limpiar e instalar admin-panel? (s/n): ');
    if (clean.toLowerCase() === 's') {
      await this.cleanAndInstall(panelPath, 'admin-panel');
    }
  }

  async cleanAndInstall(projectPath, projectName) {
    this.log(`\n🧹 Limpiando ${projectName}...`, 'cyan');
    
    // Eliminar carpetas
    const toDelete = ['node_modules', '.next', 'package-lock.json'];
    for (const item of toDelete) {
      const itemPath = path.join(projectPath, item);
      if (fs.existsSync(itemPath)) {
        this.log(`  Eliminando ${item}...`, 'cyan');
        if (fs.statSync(itemPath).isDirectory()) {
          fs.rmSync(itemPath, { recursive: true, force: true });
        } else {
          fs.unlinkSync(itemPath);
        }
      }
    }
    
    // Limpiar caché
    this.log('\n  🧹 Limpiando caché npm...', 'cyan');
    this.execCommand('npm cache clean --force');
    
    // Instalar
    this.log(`\n  📦 Instalando dependencias en ${projectName}...`, 'cyan');
    this.log('  Esto puede tomar varios minutos...', 'cyan');
    
    const installed = this.execCommand('npm install --legacy-peer-deps', projectPath);
    
    if (installed) {
      this.log(`\n  ✅ ${projectName}: Instalación completada`, 'green');
    } else {
      this.log(`\n  ❌ ${projectName}: Error en la instalación`, 'red');
      this.log('  Intenta ejecutar manualmente:', 'yellow');
      this.log(`    cd ${projectName}`, 'cyan');
      this.log('    npm install --force --legacy-peer-deps', 'cyan');
    }
  }

  async showSummary() {
    this.log('\n📊 RESUMEN COMPLETO DE CAMBIOS', 'bright');
    this.log('=' .repeat(60), 'cyan');
    
    if (this.changes.length === 0) {
      this.log('  No se realizaron cambios', 'yellow');
    } else {
      // Agrupar cambios por proyecto
      const groupedChanges = {
        'mobile-app': [],
        'backend': [],
        'admin-panel': []
      };
      
      for (const change of this.changes) {
        for (const project of Object.keys(groupedChanges)) {
          if (change.startsWith(project)) {
            groupedChanges[project].push(change.replace(`${project}: `, ''));
          }
        }
      }
      
      // Mostrar cambios agrupados
      for (const [project, changes] of Object.entries(groupedChanges)) {
        if (changes.length > 0) {
          this.log(`\n  ${project.toUpperCase()}:`, 'yellow');
          for (const change of changes) {
            this.log(`    ✅ ${change}`, 'green');
          }
        }
      }
    }
    
    this.log('\n🚀 PRÓXIMOS PASOS:', 'bright');
    this.log('\n  Para mobile-app:', 'cyan');
    this.log('    1. cd mobile-app', 'yellow');
    this.log('    2. npx expo start -c', 'yellow');
    this.log('    3. Escanea el código QR con Expo Go', 'yellow');
    
    this.log('\n  Para backend:', 'cyan');
    this.log('    1. cd backend', 'yellow');
    this.log('    2. serverless deploy (si hay cambios)', 'yellow');
    
    this.log('\n  Para admin-panel:', 'cyan');
    this.log('    1. cd admin-panel', 'yellow');
    this.log('    2. npm run dev', 'yellow');
    
    this.log('\n💡 VERSIONES UNIFICADAS:', 'bright');
    this.log('  • React: 18.3.1 (en todos los proyectos)', 'cyan');
    this.log('  • TypeScript: ~5.7.2 (en todos los proyectos)', 'cyan');
    this.log('  • AWS Amplify: ^5.3.27 (solo en mobile-app)', 'cyan');
    this.log('  • Expo SDK: 53 (compatible con Expo Go)', 'cyan');
  }

  async run() {
    this.log('🔧 CORRECTOR COMPLETO DE DEPENDENCIAS - BOAT RENTAL APP', 'bright');
    this.log('=' .repeat(60), 'bright');
    this.log('Este script procesa las 3 fases del proyecto\n', 'cyan');

    // Primero hacer verificación cruzada
    await this.crossValidateVersions();

    const proceed = await this.question('\n¿Continuar con las correcciones? (s/n): ');
    if (proceed.toLowerCase() !== 's') {
      this.log('\nProceso cancelado', 'yellow');
      this.rl.close();
      return;
    }

    // Procesar cada proyecto
    await this.processMobileApp();
    await this.processBackend();
    await this.processAdminPanel();
    
    // Mostrar resumen
    await this.showSummary();

    this.log('\n✨ Proceso completado!', 'green');
    this.rl.close();
  }
}

// Ejecutar
const fixer = new CompleteDependencyFixer();
fixer.run().catch(error => {
  console.error('Error:', error);
  process.exit(1);
});