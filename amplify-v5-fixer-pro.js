#!/usr/bin/env node

/**
 * 🔧 AWS AMPLIFY v5 GRAPHQL SERVICES FIXER PRO
 * 
 * Este script corrige automáticamente todos los servicios GraphQL
 * después de la migración de AWS Amplify v6 a v5
 * 
 * @author Claude AI Assistant
 * @version 2.0.0
 */

const fs = require('fs').promises;
const path = require('path');

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
    white: '\x1b[37m',
  },
  backupSuffix: `.backup-graphql-fix-${Date.now()}`,
  projectPaths: ['mobile-app', 'web-app', 'admin-dashboard'],
  servicePaths: ['src/services', 'src/store/slices'],
  fileExtensions: ['.ts', '.tsx', '.js', '.jsx'],
};

// Estadísticas
const stats = {
  filesProcessed: 0,
  filesModified: 0,
  totalChanges: 0,
  errors: [],
  changes: {},
};

// Utilidades
const log = {
  info: (msg) => console.log(`${CONFIG.colors.blue}ℹ${CONFIG.colors.reset}  ${msg}`),
  success: (msg) => console.log(`${CONFIG.colors.green}✅${CONFIG.colors.reset} ${msg}`),
  warning: (msg) => console.log(`${CONFIG.colors.yellow}⚠️${CONFIG.colors.reset}  ${msg}`),
  error: (msg) => console.log(`${CONFIG.colors.red}❌${CONFIG.colors.reset} ${msg}`),
  change: (msg) => console.log(`${CONFIG.colors.cyan}  →${CONFIG.colors.reset} ${msg}`),
};

/**
 * Busca archivos recursivamente
 */
async function findFiles(dir, extensions) {
  const files = [];
  
  try {
    const items = await fs.readdir(dir, { withFileTypes: true });
    
    for (const item of items) {
      const fullPath = path.join(dir, item.name);
      
      if (item.isDirectory() && !item.name.includes('node_modules') && !item.name.startsWith('.')) {
        files.push(...await findFiles(fullPath, extensions));
      } else if (item.isFile() && extensions.some(ext => item.name.endsWith(ext))) {
        files.push(fullPath);
      }
    }
  } catch (error) {
    // Ignorar errores de directorios no encontrados
  }
  
  return files;
}

/**
 * Transforma el contenido de servicios GraphQL
 */
function transformGraphQLService(content, filePath) {
  let modified = content;
  let changeCount = 0;
  const changes = [];

  // 1. Detectar y transformar imports de generateClient
  const generateClientImportRegex = /import\s*{[^}]*generateClient[^}]*}\s*from\s*['"]aws-amplify\/api['"];?/g;
  if (generateClientImportRegex.test(modified)) {
    modified = modified.replace(generateClientImportRegex, "import { API, graphqlOperation } from 'aws-amplify';");
    changes.push('Import: generateClient → API, graphqlOperation');
    changeCount++;
  }

  // 2. Añadir import si no existe pero se usa client.graphql
  if (!modified.includes('import { API') && modified.includes('client.graphql')) {
    const firstImport = modified.match(/import\s+.*?from\s+['"].*?['"];?\s*\n/);
    if (firstImport) {
      modified = modified.replace(
        firstImport[0],
        firstImport[0] + "import { API, graphqlOperation } from 'aws-amplify';\n"
      );
      changes.push('Import: Añadido API, graphqlOperation');
      changeCount++;
    }
  }

  // 3. Eliminar líneas de generateClient
  const clientGeneratorRegex = /^\s*(?:const|let|var)\s+client\s*=\s*generateClient\s*\(\s*\)\s*;?\s*$/gm;
  if (clientGeneratorRegex.test(modified)) {
    modified = modified.replace(clientGeneratorRegex, '');
    changes.push('Eliminado: const client = generateClient()');
    changeCount++;
  }

  // 4. Eliminar comentarios de client = generateClient
  const commentedClientRegex = /^\s*\/\/\s*(?:const|let|var)\s+client\s*=\s*generateClient\s*\(\s*\)\s*;?\s*$/gm;
  if (commentedClientRegex.test(modified)) {
    modified = modified.replace(commentedClientRegex, '');
    changes.push('Eliminado: Comentario de generateClient');
    changeCount++;
  }

  // 5. Eliminar líneas de demostración/ejemplo
  const demoLineRegex = /^\s*(?:\/\/\s*)?await\s+API\.graphql\s*\(\s*graphqlOperation\s*\(\s*XYZ\s*\)\s*\)\s*;?\s*(?:\/\/.*)?$/gm;
  if (demoLineRegex.test(modified)) {
    modified = modified.replace(demoLineRegex, '');
    changes.push('Eliminado: Línea de demostración (XYZ)');
    changeCount++;
  }

  // 6. Transformar client.graphql a API.graphql con graphqlOperation
  // Patrón más robusto que maneja múltiples líneas y diferentes formatos
  const clientGraphqlRegex = /await\s+client\.graphql\s*\(\s*{([^}]+)}\s*\)/g;
  
  const matches = [...modified.matchAll(clientGraphqlRegex)];
  for (const match of matches) {
    const innerContent = match[1];
    
    // Extraer query y variables
    const queryMatch = innerContent.match(/query\s*:\s*(\w+)/);
    const variablesMatch = innerContent.match(/variables\s*:\s*({[^}]+}|\w+)/);
    
    if (queryMatch) {
      const queryName = queryMatch[1];
      let replacement;
      
      if (variablesMatch) {
        const variables = variablesMatch[1];
        replacement = `await API.graphql(graphqlOperation(${queryName}, ${variables}))`;
      } else {
        replacement = `await API.graphql(graphqlOperation(${queryName}))`;
      }
      
      modified = modified.replace(match[0], replacement);
      changeCount++;
    }
  }

  // 7. Manejar casos más complejos con graphql multi-línea
  const multiLineGraphqlRegex = /await\s+client\.graphql\s*\(\s*{\s*\n([^}]+)}\s*\)/g;
  const multiLineMatches = [...modified.matchAll(multiLineGraphqlRegex)];
  
  for (const match of multiLineMatches) {
    const lines = match[1].split('\n').map(l => l.trim()).filter(l => l);
    let queryName = '';
    let hasVariables = false;
    let variablesContent = '';
    
    for (const line of lines) {
      if (line.includes('query:')) {
        queryName = line.match(/query\s*:\s*(\w+)/)?.[1] || '';
      } else if (line.includes('variables:')) {
        hasVariables = true;
        // Capturar todo después de 'variables:'
        const varMatch = match[0].match(/variables\s*:\s*({[\s\S]*?})\s*(?:}|,)/);
        if (varMatch) {
          variablesContent = varMatch[1];
        }
      }
    }
    
    if (queryName) {
      let replacement;
      if (hasVariables && variablesContent) {
        replacement = `await API.graphql(\n        graphqlOperation(${queryName}, ${variablesContent})\n      )`;
      } else {
        replacement = `await API.graphql(\n        graphqlOperation(${queryName})\n      )`;
      }
      
      modified = modified.replace(match[0], replacement);
      changeCount++;
    }
  }

  if (changeCount > 0) {
    changes.push(`Transformado: ${changeCount} llamadas client.graphql → API.graphql`);
  }

  return { modified, changeCount, changes };
}

/**
 * Transforma authSlice.ts específicamente
 */
function transformAuthSlice(content, filePath) {
  let modified = content;
  let changeCount = 0;
  const changes = [];

  // 1. Transformar options → attributes en signUp
  const signUpOptionsRegex = /await\s+Auth\.signUp\s*\(\s*{\s*([^}]*?)options\s*:\s*{([^}]+)}/gs;
  if (signUpOptionsRegex.test(modified)) {
    modified = modified.replace(signUpOptionsRegex, (match, before, attrs) => {
      return `await Auth.signUp({\n        ${before}attributes: {${attrs}}`;
    });
    changes.push('Auth.signUp: options → attributes');
    changeCount++;
  }

  // 2. Transformar userId → userSub
  const userIdRegex = /result\.userId/g;
  if (userIdRegex.test(modified)) {
    modified = modified.replace(userIdRegex, 'result.userSub');
    changes.push('Auth.signUp: userId → userSub');
    changeCount++;
  }

  // 3. Arreglar changePassword para incluir user como primer parámetro
  const changePasswordRegex = /await\s+Auth\.changePassword\s*\(\s*{\s*oldPassword[^}]+}\s*\)/g;
  if (changePasswordRegex.test(modified)) {
    // Buscar si ya existe la obtención del usuario
    const hasUserFetch = /const\s+user\s*=\s*await\s+Auth\.currentAuthenticatedUser\s*\(\s*\)/.test(modified);
    
    if (!hasUserFetch) {
      // Insertar obtención del usuario antes de changePassword
      modified = modified.replace(
        /(try\s*{\s*\n)([\s\S]*?)(await\s+Auth\.changePassword)/gm,
        '$1      const user = await Auth.currentAuthenticatedUser();\n$2$3'
      );
    }
    
    // Actualizar la llamada a changePassword
    modified = modified.replace(
      /await\s+Auth\.changePassword\s*\(\s*{\s*oldPassword\s*,\s*newPassword\s*}\s*\)/g,
      'await Auth.changePassword(user, oldPassword, newPassword)'
    );
    
    changes.push('Auth.changePassword: Añadido user como primer parámetro');
    changeCount++;
  }

  // 4. Mejorar loginUser para obtener atributos correctamente
  const loginUserRegex = /(const\s+result\s*=\s*await\s+Auth\.signIn[^;]+;)/g;
  if (loginUserRegex.test(modified) && !modified.includes('await Auth.currentAuthenticatedUser()')) {
    modified = modified.replace(loginUserRegex, (match) => {
      return match + '\n      const attributes = await Auth.currentAuthenticatedUser();';
    });
    
    // Actualizar el mapeo de atributos
    modified = modified.replace(
      /id:\s*result\.nextStep\?\.signInStep\s*\|\|\s*''/g,
      "id: result.username || ''"
    );
    
    modified = modified.replace(
      /email:\s*email,/g,
      "email: attributes.attributes?.email || email,"
    );
    
    modified = modified.replace(
      /name:\s*'',/g,
      "name: attributes.attributes?.name || '',"
    );
    
    modified = modified.replace(
      /phone:\s*'',/g,
      "phone: attributes.attributes?.phone_number || '',"
    );
    
    changes.push('Auth.signIn: Mejorado manejo de atributos de usuario');
    changeCount++;
  }

  // 5. Arreglar confirmSignUp si tiene parámetros incorrectos
  const confirmSignUpRegex = /await\s+Auth\.confirmSignUp\s*\(\s*email\s*,\s*code\s*\)/g;
  if (confirmSignUpRegex.test(modified)) {
    // Ya está correcto, no hacer nada
  }

  // 6. Arreglar imports duplicados de Auth
  const duplicateAuthImportRegex = /(import\s*{\s*Auth\s*}\s*from\s*['"]aws-amplify['"];?\s*;?\s*\n)+/g;
  const authImports = modified.match(duplicateAuthImportRegex);
  if (authImports && authImports.length > 1) {
    // Mantener solo el primer import
    modified = modified.replace(duplicateAuthImportRegex, authImports[0]);
    changes.push('Eliminados imports duplicados de Auth');
    changeCount++;
  }

  return { modified, changeCount, changes };
}

/**
 * Procesa un archivo
 */
async function processFile(filePath) {
  try {
    const content = await fs.readFile(filePath, 'utf8');
    let result = { modified: content, changeCount: 0, changes: [] };
    
    // Determinar qué transformaciones aplicar
    const fileName = path.basename(filePath);
    
    if (fileName === 'authSlice.ts' || fileName === 'authSlice.tsx') {
      result = transformAuthSlice(content, filePath);
    } else if (
      filePath.includes('/services/') || 
      (filePath.includes('Service.ts') || filePath.includes('Service.tsx'))
    ) {
      result = transformGraphQLService(content, filePath);
    }
    
    // Si hay cambios, guardar el archivo
    if (result.changeCount > 0) {
      // Crear backup
      await fs.writeFile(filePath + CONFIG.backupSuffix, content);
      
      // Escribir archivo modificado
      await fs.writeFile(filePath, result.modified);
      
      stats.filesModified++;
      stats.totalChanges += result.changeCount;
      
      if (!stats.changes[filePath]) {
        stats.changes[filePath] = [];
      }
      stats.changes[filePath].push(...result.changes);
      
      return true;
    }
    
    return false;
  } catch (error) {
    stats.errors.push({ file: filePath, error: error.message });
    return false;
  }
}

/**
 * Arregla tsconfig.json si es necesario
 */
async function fixTsConfig(projectPath) {
  const tsconfigPath = path.join(projectPath, 'tsconfig.json');
  
  try {
    const content = await fs.readFile(tsconfigPath, 'utf8');
    const tsconfig = JSON.parse(content);
    
    // Verificar si tiene el problema de types jest
    if (tsconfig.compilerOptions?.types?.includes('jest')) {
      log.warning(`Detectado 'jest' en types de ${tsconfigPath}`);
      log.info('Ejecuta: npm install --save-dev @types/jest');
      log.info('O elimina "jest" del array types en tsconfig.json');
    }
  } catch (error) {
    // Ignorar si no existe tsconfig
  }
}

/**
 * Función principal
 */
async function main() {
  console.log(`\n${CONFIG.colors.bright}🔧 AWS AMPLIFY v5 GRAPHQL SERVICES FIXER PRO${CONFIG.colors.reset}`);
  console.log('======================================================================');
  
  // Buscar archivos en todos los proyectos
  const allFiles = [];
  
  for (const projectPath of CONFIG.projectPaths) {
    if (await fs.access(projectPath).then(() => true).catch(() => false)) {
      log.info(`📁 Procesando proyecto: ${projectPath}`);
      
      for (const servicePath of CONFIG.servicePaths) {
        const fullPath = path.join(projectPath, servicePath);
        const files = await findFiles(fullPath, CONFIG.fileExtensions);
        allFiles.push(...files);
      }
      
      // Verificar tsconfig
      await fixTsConfig(projectPath);
    }
  }
  
  log.info(`📝 Archivos encontrados: ${allFiles.length}`);
  
  // Procesar archivos
  console.log('\n🔄 Procesando archivos...');
  
  for (const file of allFiles) {
    stats.filesProcessed++;
    const modified = await processFile(file);
    
    if (modified) {
      log.success(`Modificado: ${path.relative(process.cwd(), file)}`);
      if (stats.changes[file]) {
        stats.changes[file].forEach(change => log.change(change));
      }
    }
  }
  
  // Mostrar resumen
  console.log(`\n${CONFIG.colors.bright}📊 RESUMEN DE CAMBIOS${CONFIG.colors.reset}`);
  console.log('======================================================================');
  console.log(`📈 Estadísticas:`);
  console.log(`   • Archivos procesados: ${stats.filesProcessed}`);
  console.log(`   • Archivos modificados: ${CONFIG.colors.green}${stats.filesModified}${CONFIG.colors.reset}`);
  console.log(`   • Total de cambios: ${CONFIG.colors.cyan}${stats.totalChanges}${CONFIG.colors.reset}`);
  console.log(`   • Errores: ${CONFIG.colors.red}${stats.errors.length}${CONFIG.colors.reset}`);
  
  if (stats.errors.length > 0) {
    console.log(`\n${CONFIG.colors.red}❌ ERRORES:${CONFIG.colors.reset}`);
    stats.errors.forEach(({ file, error }) => {
      console.log(`   ${file}: ${error}`);
    });
  }
  
  // Instrucciones finales
  console.log(`\n${CONFIG.colors.bright}✅ SIGUIENTES PASOS:${CONFIG.colors.reset}`);
  console.log('======================================================================');
  console.log('1. Revisa los cambios realizados');
  console.log(`2. Los backups tienen extensión: ${CONFIG.colors.yellow}${CONFIG.backupSuffix}${CONFIG.colors.reset}`);
  console.log('3. Si detectaste advertencias de Jest, ejecuta:');
  console.log(`   ${CONFIG.colors.cyan}npm install --save-dev @types/jest${CONFIG.colors.reset}`);
  console.log('4. Ejecuta tu aplicación para verificar que todo funcione:');
  console.log(`   ${CONFIG.colors.cyan}cd mobile-app && npm start${CONFIG.colors.reset}`);
  console.log('\n✨ ¡Proceso completado!\n');
}

// Ejecutar
main().catch(error => {
  log.error(`Error fatal: ${error.message}`);
  process.exit(1);
});