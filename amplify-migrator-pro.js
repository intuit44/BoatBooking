#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Colores
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m'
};

class AmplifyV5MigratorPro {
  constructor(options = {}) {
    this.rootPath = process.cwd();
    this.dryRun = options.dryRun || false;
    this.verbose = options.verbose || false;
    this.filesProcessed = 0;
    this.filesModified = 0;
    this.errors = [];
    this.warnings = [];
    this.changes = [];
    
    // Configuración completa de mapeos v6 → v5
    this.migrationConfig = {
      // Importaciones de módulos
      imports: {
        'aws-amplify/auth': {
          v5Import: "import { Auth } from 'aws-amplify';",
          methods: {
            'signUp': { v5: 'Auth.signUp', paramTransform: 'signUpParams' },
            'confirmSignUp': { v5: 'Auth.confirmSignUp', paramTransform: 'confirmSignUpParams' },
            'signIn': { v5: 'Auth.signIn', paramTransform: 'signInParams' },
            'signOut': { v5: 'Auth.signOut', paramTransform: null },
            'resendSignUpCode': { v5: 'Auth.resendSignUp', paramTransform: 'resendParams' },
            'resetPassword': { v5: 'Auth.forgotPassword', paramTransform: 'resetParams' },
            'confirmResetPassword': { v5: 'Auth.forgotPasswordSubmit', paramTransform: 'confirmResetParams' },
            'updatePassword': { v5: 'Auth.changePassword', paramTransform: 'updatePasswordParams' },
            'getCurrentUser': { v5: 'Auth.currentAuthenticatedUser', paramTransform: null },
            'fetchUserAttributes': { v5: 'Auth.userAttributes', paramTransform: 'fetchAttributesParams' },
            'updateUserAttributes': { v5: 'Auth.updateUserAttributes', paramTransform: 'updateAttributesParams' },
            'deleteUser': { v5: 'Auth.deleteUser', paramTransform: null }
          }
        },
        'aws-amplify/storage': {
          v5Import: "import { Storage } from 'aws-amplify';",
          methods: {
            'uploadData': { v5: 'Storage.put', paramTransform: 'uploadParams' },
            'downloadData': { v5: 'Storage.get', paramTransform: 'downloadParams' },
            'remove': { v5: 'Storage.remove', paramTransform: null },
            'list': { v5: 'Storage.list', paramTransform: null },
            'getUrl': { v5: 'Storage.get', paramTransform: 'getUrlParams' },
            'copy': { v5: 'Storage.copy', paramTransform: 'copyParams' }
          }
        },
        'aws-amplify/api': {
          v5Import: "import { API } from 'aws-amplify';",
          methods: {
            'generateClient': { v5: null, replacement: 'apiV5Client' },
            'graphql': { v5: 'API.graphql', paramTransform: 'graphqlParams' },
            'post': { v5: 'API.post', paramTransform: null },
            'get': { v5: 'API.get', paramTransform: null },
            'put': { v5: 'API.put', paramTransform: null },
            'del': { v5: 'API.del', paramTransform: null },
            'patch': { v5: 'API.patch', paramTransform: null },
            'head': { v5: 'API.head', paramTransform: null }
          }
        },
        'aws-amplify/analytics': {
          v5Import: "import { Analytics } from 'aws-amplify';",
          methods: {
            'record': { v5: 'Analytics.record', paramTransform: null },
            'autoTrack': { v5: 'Analytics.autoTrack', paramTransform: null }
          }
        },
        'aws-amplify/in-app-messaging': {
          v5Import: "import { Notifications } from 'aws-amplify';",
          methods: {
            'initializeInAppMessaging': { v5: 'Notifications.InAppMessaging.syncMessages', paramTransform: null },
            'syncMessages': { v5: 'Notifications.InAppMessaging.syncMessages', paramTransform: null }
          }
        }
      },
      
      // Hooks de UI components
      uiHooks: {
        '@aws-amplify/ui-react': {
          'useAuthenticator': {
            warning: 'useAuthenticator requiere @aws-amplify/ui-react v2.x que no es compatible con Amplify v5',
            suggestion: 'Crear componentes de autenticación personalizados'
          },
          'useTheme': {
            warning: 'useTheme de Amplify UI no está disponible',
            suggestion: 'Usar sistema de temas personalizado'
          }
        },
        '@aws-amplify/ui-react-native': {
          'useAuthenticator': {
            warning: 'useAuthenticator no está disponible en v5',
            suggestion: 'Usar Auth.currentAuthenticatedUser() con estados propios'
          }
        }
      },
      
      // Componentes UI
      uiComponents: {
        'Authenticator': {
          warning: 'Componente Authenticator no disponible con Amplify v5',
          suggestion: 'Crear formularios de autenticación personalizados'
        },
        'SignIn': {
          warning: 'Componente SignIn no disponible',
          suggestion: 'Crear componente SignIn personalizado'
        },
        'SignUp': {
          warning: 'Componente SignUp no disponible',
          suggestion: 'Crear componente SignUp personalizado'
        }
      }
    };
  }

  log(message, color = 'reset', indent = 0) {
    const indentation = ' '.repeat(indent);
    console.log(`${indentation}${colors[color]}${message}${colors.reset}`);
  }

  // Parsear argumentos de línea de comandos
  static parseArgs() {
    const args = process.argv.slice(2);
    const options = {
      dryRun: false,
      verbose: false,
      path: null,
      help: false
    };

    for (let i = 0; i < args.length; i++) {
      switch (args[i]) {
        case '--dry-run':
        case '-d':
          options.dryRun = true;
          break;
        case '--verbose':
        case '-v':
          options.verbose = true;
          break;
        case '--help':
        case '-h':
          options.help = true;
          break;
        case '--path':
        case '-p':
          options.path = args[++i];
          break;
      }
    }

    return options;
  }

  static showHelp() {
    console.log(`
${colors.bright}AWS Amplify v6 → v5 Migrator Pro${colors.reset}

${colors.cyan}Uso:${colors.reset}
  node amplify-migrator-pro.js [opciones]

${colors.cyan}Opciones:${colors.reset}
  --dry-run, -d     Mostrar cambios sin modificar archivos
  --verbose, -v     Mostrar información detallada
  --path, -p        Ruta específica a procesar (default: mobile-app)
  --help, -h        Mostrar esta ayuda

${colors.cyan}Ejemplos:${colors.reset}
  node amplify-migrator-pro.js --dry-run
  node amplify-migrator-pro.js --path src/store --verbose
  node amplify-migrator-pro.js -d -v
`);
  }

  // Transformadores de parámetros
  paramTransformers = {
    signUpParams: (code) => {
      return code.replace(
        /\boptions:\s*{\s*userAttributes:\s*{([^}]+)}\s*}/g,
        'attributes: { $1 }'
      );
    },
    
    confirmSignUpParams: (code) => {
      return code.replace(
        /{\s*username:\s*([^,]+),\s*confirmationCode:\s*([^}]+)}/g,
        '$1, $2'
      );
    },
    
    signInParams: (code) => {
      return code.replace(
        /{\s*username:\s*([^,]+),\s*password:\s*([^}]+)}/g,
        '$1, $2'
      );
    },
    
    resendParams: (code) => {
      return code.replace(
        /{\s*username:\s*([^}]+)}/g,
        '$1'
      );
    },
    
    resetParams: (code) => {
      return code.replace(
        /{\s*username:\s*([^}]+)}/g,
        '$1'
      );
    },
    
    confirmResetParams: (code) => {
      return code.replace(
        /{\s*username:\s*([^,]+),\s*confirmationCode:\s*([^,]+),\s*newPassword:\s*([^}]+)}/g,
        '$1, $2, $3'
      );
    },
    
    updatePasswordParams: (code) => {
      // Para updatePassword necesitamos el user actual
      return code.replace(
        /updatePassword\s*\(\s*{\s*oldPassword:\s*([^,]+),\s*newPassword:\s*([^}]+)}\s*\)/g,
        `Auth.currentAuthenticatedUser().then(user => Auth.changePassword(user, $1, $2))`
      );
    },
    
    graphqlParams: (code) => {
      // Convertir graphql({ query }) a graphql(graphqlOperation(query))
      return code.replace(
        /graphql\s*\(\s*{\s*query:\s*([^}]+)}\s*\)/g,
        'API.graphql(graphqlOperation($1))'
      );
    },
    
    uploadParams: (code) => {
      // uploadData({ key, data, options }) → Storage.put(key, data, options)
      return code.replace(
        /{\s*key:\s*([^,]+),\s*data:\s*([^,]+)(?:,\s*options:\s*([^}]+))?\s*}/g,
        '$1, $2' + (code.includes('options') ? ', $3' : '')
      );
    }
  };

  // Buscar archivos recursivamente
  findFiles(dir, extensions = ['.ts', '.tsx', '.js', '.jsx'], fileList = []) {
    try {
      const files = fs.readdirSync(dir);
      
      files.forEach(file => {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);
        
        if (stat.isDirectory()) {
          // Ignorar directorios
          const ignoreDirs = ['.', 'node_modules', 'dist', 'build', '.expo', 'coverage', '.next'];
          if (!ignoreDirs.some(ignore => file.startsWith(ignore))) {
            this.findFiles(filePath, extensions, fileList);
          }
        } else if (extensions.some(ext => file.endsWith(ext))) {
          fileList.push(filePath);
        }
      });
    } catch (error) {
      this.log(`Error leyendo directorio ${dir}: ${error.message}`, 'red');
    }
    
    return fileList;
  }

  // Detectar uso de generateClient (crítico para GraphQL v6)
  detectGenerateClient(content, filePath) {
    if (content.includes('generateClient')) {
      this.warnings.push({
        file: filePath,
        type: 'critical',
        message: 'generateClient() es específico de v6 y no tiene equivalente directo en v5',
        suggestion: 'Usar API.graphql() directamente con graphqlOperation()'
      });
      
      // Ofrecer código de reemplazo
      const replacement = `
// IMPORTANTE: generateClient() no existe en v5
// Reemplazar:
// const client = generateClient();
// const result = await client.graphql({ query: listTodos });

// Por:
import { API, graphqlOperation } from 'aws-amplify';
const result = await API.graphql(graphqlOperation(listTodos));`;
      
      this.changes.push({
        file: filePath,
        type: 'manual',
        description: 'Requiere refactorización manual de generateClient',
        code: replacement
      });
    }
  }

  // Detectar hooks de UI
  detectUIHooks(content, filePath) {
    Object.entries(this.migrationConfig.uiHooks).forEach(([pkg, hooks]) => {
      Object.entries(hooks).forEach(([hook, config]) => {
        if (content.includes(hook)) {
          this.warnings.push({
            file: filePath,
            type: 'ui-hook',
            message: config.warning,
            suggestion: config.suggestion,
            hook: hook
          });
        }
      });
    });
  }

  // Detectar componentes UI
  detectUIComponents(content, filePath) {
    Object.entries(this.migrationConfig.uiComponents).forEach(([component, config]) => {
      const componentRegex = new RegExp(`<${component}[\\s>]`, 'g');
      if (componentRegex.test(content)) {
        this.warnings.push({
          file: filePath,
          type: 'ui-component',
          message: config.warning,
          suggestion: config.suggestion,
          component: component
        });
      }
    });
  }

  // Procesar archivo
  processFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      let modifiedContent = content;
      let fileModified = false;
      const fileChanges = [];

      // Detectar problemas críticos primero
      this.detectGenerateClient(content, filePath);
      this.detectUIHooks(content, filePath);
      this.detectUIComponents(content, filePath);

      // Procesar importaciones
      Object.entries(this.migrationConfig.imports).forEach(([v6Module, config]) => {
        const importRegex = new RegExp(
          `import\\s*{([^}]+)}\\s*from\\s*['"]${v6Module.replace('/', '\\/')}['"]`,
          'g'
        );
        
        const matches = [...content.matchAll(importRegex)];
        
        if (matches.length > 0) {
          matches.forEach(match => {
            const fullImport = match[0];
            const importedItems = match[1]
              .split(',')
              .map(item => item.trim())
              .filter(item => item);
            
            if (this.verbose || this.dryRun) {
              this.log(`\n📄 ${path.relative(this.rootPath, filePath)}`, 'yellow');
              this.log(`Encontrado: ${fullImport}`, 'cyan', 2);
            }
            
            // Reemplazar importación
            modifiedContent = modifiedContent.replace(fullImport, config.v5Import);
            fileChanges.push({
              type: 'import',
              from: fullImport,
              to: config.v5Import
            });
            
            // Procesar cada método importado
            importedItems.forEach(item => {
              let methodName = item;
              let alias = item;
              
              // Manejar imports con alias
              if (item.includes(' as ')) {
                [methodName, alias] = item.split(' as ').map(s => s.trim());
              }
              
              const methodConfig = config.methods[methodName];
              
              if (!methodConfig) {
                this.warnings.push({
                  file: filePath,
                  type: 'unknown-method',
                  message: `Método '${methodName}' no reconocido`,
                  suggestion: 'Verificar documentación de AWS Amplify v5'
                });
                return;
              }
              
              if (methodConfig.v5 === null) {
                // Método no existe en v5
                if (methodConfig.replacement === 'apiV5Client') {
                  this.detectGenerateClient(content, filePath);
                }
                return;
              }
              
              // Buscar usos del método
              const methodRegex = new RegExp(`\\b${alias}\\s*\\(`, 'g');
              const methodMatches = [...modifiedContent.matchAll(methodRegex)];
              
              if (methodMatches.length > 0) {
                let tempContent = modifiedContent;
                
                // Aplicar transformación de parámetros si es necesario
                if (methodConfig.paramTransform && this.paramTransformers[methodConfig.paramTransform]) {
                  tempContent = this.paramTransformers[methodConfig.paramTransform](tempContent);
                }
                
                // Reemplazar llamadas al método
                tempContent = tempContent.replace(methodRegex, `${methodConfig.v5}(`);
                
                if (tempContent !== modifiedContent) {
                  modifiedContent = tempContent;
                  fileChanges.push({
                    type: 'method',
                    from: `${alias}()`,
                    to: `${methodConfig.v5}()`,
                    occurrences: methodMatches.length
                  });
                }
              }
            });
            
            fileModified = true;
          });
        }
      });

      // Aplicar correcciones específicas adicionales
      modifiedContent = this.applySpecificFixes(modifiedContent, filePath);

      // Si hay cambios y no es dry-run, guardar
      if (fileModified && modifiedContent !== content) {
        if (!this.dryRun) {
          // Crear backup
          const backupPath = `${filePath}.backup-v6-${Date.now()}`;
          fs.writeFileSync(backupPath, content);
          
          // Guardar archivo modificado
          fs.writeFileSync(filePath, modifiedContent);
          
          if (this.verbose) {
            this.log(`✅ Archivo actualizado`, 'green', 2);
            this.log(`📋 Backup: ${path.basename(backupPath)}`, 'blue', 2);
          }
        }
        
        this.filesModified++;
        this.changes.push({
          file: filePath,
          changes: fileChanges
        });
      }
      
      this.filesProcessed++;
      
    } catch (error) {
      this.errors.push({
        file: filePath,
        error: error.message
      });
    }
  }

  // Aplicar correcciones específicas
  applySpecificFixes(content, filePath) {
    let fixed = content;
    
    // Fix para getCurrentUser response
    if (fixed.includes('user.userId') || fixed.includes('user.username')) {
      fixed = fixed.replace(/user\.userId/g, 'user.username');
      fixed = fixed.replace(/user\.signInDetails\?\.loginId/g, 'user.attributes.email');
    }
    
    // Fix para atributos de usuario
    if (fixed.includes('fetchUserAttributes')) {
      const attributeFix = `
      const attributes = await Auth.userAttributes(user);
      const attributesMap = attributes.reduce((acc, attr) => {
        acc[attr.Name] = attr.Value;
        return acc;
      }, {});`;
      
      // Buscar donde se usa y sugerir el fix
      this.warnings.push({
        file: filePath,
        type: 'attributes',
        message: 'fetchUserAttributes retorna formato diferente en v5',
        suggestion: 'Los atributos vienen como array de {Name, Value}',
        code: attributeFix
      });
    }
    
    return fixed;
  }

  // Generar reporte
  generateReport() {
    this.log('\n📊 REPORTE DE MIGRACIÓN', 'bright');
    this.log('=' .repeat(70), 'cyan');
    
    // Resumen
    this.log(`\n📈 Resumen:`, 'bright');
    this.log(`  Archivos procesados: ${this.filesProcessed}`, 'green', 2);
    this.log(`  Archivos modificados: ${this.filesModified}`, 'yellow', 2);
    this.log(`  Errores: ${this.errors.length}`, 'red', 2);
    this.log(`  Advertencias: ${this.warnings.length}`, 'yellow', 2);
    
    // Cambios por archivo
    if (this.changes.length > 0) {
      this.log(`\n📝 Cambios realizados:`, 'bright');
      
      const fileChanges = this.changes.filter(c => c.changes);
      fileChanges.forEach(fileChange => {
        this.log(`\n  ${path.relative(this.rootPath, fileChange.file)}:`, 'cyan', 2);
        fileChange.changes.forEach(change => {
          if (change.type === 'import') {
            this.log(`    Import: ${change.from} → ${change.to}`, 'green', 4);
          } else if (change.type === 'method') {
            this.log(`    Método: ${change.from} → ${change.to} (${change.occurrences} usos)`, 'green', 4);
          }
        });
      });
    }
    
    // Advertencias críticas
    const criticalWarnings = this.warnings.filter(w => w.type === 'critical');
    if (criticalWarnings.length > 0) {
      this.log(`\n⚠️  ADVERTENCIAS CRÍTICAS:`, 'red');
      criticalWarnings.forEach(warning => {
        this.log(`\n  ${path.relative(this.rootPath, warning.file)}:`, 'yellow', 2);
        this.log(`    ${warning.message}`, 'red', 4);
        this.log(`    💡 ${warning.suggestion}`, 'cyan', 4);
      });
    }
    
    // Hooks y componentes UI
    const uiWarnings = this.warnings.filter(w => w.type === 'ui-hook' || w.type === 'ui-component');
    if (uiWarnings.length > 0) {
      this.log(`\n🎨 COMPONENTES UI NO DISPONIBLES:`, 'yellow');
      
      const groupedByFile = {};
      uiWarnings.forEach(w => {
        if (!groupedByFile[w.file]) groupedByFile[w.file] = [];
        groupedByFile[w.file].push(w);
      });
      
      Object.entries(groupedByFile).forEach(([file, warnings]) => {
        this.log(`\n  ${path.relative(this.rootPath, file)}:`, 'yellow', 2);
        warnings.forEach(w => {
          const item = w.hook || w.component;
          this.log(`    ${item}: ${w.message}`, 'yellow', 4);
          this.log(`    💡 ${w.suggestion}`, 'cyan', 4);
        });
      });
    }
    
    // Errores
    if (this.errors.length > 0) {
      this.log(`\n❌ ERRORES:`, 'red');
      this.errors.forEach(error => {
        this.log(`  ${path.relative(this.rootPath, error.file)}: ${error.error}`, 'red', 2);
      });
    }
    
    // Siguientes pasos
    this.log(`\n🚀 SIGUIENTES PASOS:`, 'bright');
    if (this.dryRun) {
      this.log(`  1. Revisa los cambios propuestos arriba`, 'cyan', 2);
      this.log(`  2. Ejecuta sin --dry-run para aplicar cambios`, 'cyan', 2);
    } else if (this.filesModified > 0) {
      this.log(`  1. Revisa los archivos modificados`, 'cyan', 2);
      this.log(`  2. Los backups tienen extensión .backup-v6-[timestamp]`, 'cyan', 2);
      this.log(`  3. Actualiza componentes UI manualmente si es necesario`, 'cyan', 2);
      this.log(`  4. Ejecuta: cd mobile-app && npm start`, 'cyan', 2);
    }
    
    if (criticalWarnings.length > 0) {
      this.log(`\n⚠️  IMPORTANTE: Hay ${criticalWarnings.length} advertencia(s) crítica(s) que requieren atención manual`, 'red');
    }
  }

  async run(targetPath = null) {
    this.log('🔧 AWS AMPLIFY v6 → v5 MIGRATOR PRO', 'bright');
    this.log('=' .repeat(70), 'cyan');
    
    if (this.dryRun) {
      this.log('🔍 Modo DRY RUN - No se modificarán archivos\n', 'yellow');
    }
    
    // Determinar ruta a procesar
    const searchPath = targetPath || path.join(this.rootPath, 'mobile-app');
    
    if (!fs.existsSync(searchPath)) {
      this.log(`❌ No se encuentra: ${searchPath}`, 'red');
      return;
    }
    
    this.log(`📁 Procesando: ${path.relative(this.rootPath, searchPath) || '.'}`, 'cyan');
    
    // Verificar versión instalada
    const packageJsonPath = path.join(
      searchPath.includes('mobile-app') ? searchPath : path.join(searchPath, '..'),
      'package.json'
    );
    
    if (fs.existsSync(packageJsonPath)) {
      const pkg = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
      const amplifyVersion = pkg.dependencies?.['aws-amplify'];
      if (amplifyVersion) {
        this.log(`📦 AWS Amplify version actual: ${amplifyVersion}\n`, 'cyan');
        
        if (amplifyVersion.includes('6')) {
          this.log('⚠️  Detectado Amplify v6 - El código será migrado a sintaxis v5', 'yellow');
          this.log('   Asegúrate de actualizar las dependencias a v5 después\n', 'yellow');
        }
      }
    }
    
    // Buscar archivos
    this.log('🔍 Buscando archivos...', 'cyan');
    const files = this.findFiles(searchPath);
    this.log(`  Encontrados: ${files.length} archivos\n`, 'green');
    
    // Procesar archivos
    if (!this.dryRun) {
      this.log('📝 Procesando archivos...', 'cyan');
    }
    
    files.forEach(file => {
      this.processFile(file);
    });
    
    // Generar reporte
    this.generateReport();
    
    this.log('\n✨ Proceso completado!', 'green');
  }
}

// Ejecutar
if (require.main === module) {
  const options = AmplifyV5MigratorPro.parseArgs();
  
  if (options.help) {
    AmplifyV5MigratorPro.showHelp();
    process.exit(0);
  }
  
  const migrator = new AmplifyV5MigratorPro(options);
  migrator.run(options.path).catch(error => {
    console.error('Error:', error);
    process.exit(1);
  });
}

module.exports = AmplifyV5MigratorPro;