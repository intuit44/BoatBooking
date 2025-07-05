#!/usr/bin/env node

/**
 * 🔧 AWS AMPLIFY v5 COMPLETE FIX
 * 
 * Script para completar las transformaciones que el script anterior no realizó correctamente
 * Específicamente diseñado para corregir las llamadas client.graphql() huérfanas
 * 
 * @author Claude AI Assistant
 * @version 1.0.0
 */

const fs = require('fs').promises;
const path = require('path');

// Configuración
const CONFIG = {
  colors: {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m',
  },
  backupSuffix: `.backup-complete-fix-${Date.now()}`,
  targetFiles: [
    'mobile-app/src/services/boatsService.ts',
    'mobile-app/src/services/bookingsService.ts', 
    'mobile-app/src/services/reservationsService.ts',
    'mobile-app/src/store/slices/authSlice.ts'
  ]
};

// Utilidades de logging
const log = {
  info: (msg) => console.log(`${CONFIG.colors.blue}ℹ${CONFIG.colors.reset}  ${msg}`),
  success: (msg) => console.log(`${CONFIG.colors.green}✅${CONFIG.colors.reset} ${msg}`),
  error: (msg) => console.log(`${CONFIG.colors.red}❌${CONFIG.colors.reset} ${msg}`),
  change: (msg) => console.log(`${CONFIG.colors.cyan}  →${CONFIG.colors.reset} ${msg}`),
};

/**
 * Corrige las llamadas client.graphql() huérfanas
 */
function fixOrphanedClientCalls(content) {
  let modified = content;
  let changeCount = 0;

  // 1. Asegurar que tiene el import correcto
  if (!modified.includes('graphqlOperation') && modified.includes('API.graphql')) {
    // Buscar el import de API y añadir graphqlOperation
    modified = modified.replace(
      /import\s*{\s*API\s*}\s*from\s*['"]aws-amplify['"];?/,
      "import { API, graphqlOperation } from 'aws-amplify';"
    );
    changeCount++;
  }

  // 2. Transformar todas las llamadas client.graphql a API.graphql(graphqlOperation())
  // Patrón simple: client.graphql({ query: xxx })
  const simplePattern = /client\.graphql\s*\(\s*{\s*query:\s*(\w+)\s*}\s*\)/g;
  modified = modified.replace(simplePattern, (match, queryName) => {
    changeCount++;
    return `API.graphql(graphqlOperation(${queryName}))`;
  });

  // 3. Patrón con variables inline
  const withVariablesPattern = /client\.graphql\s*\(\s*{\s*query:\s*(\w+)\s*,\s*variables:\s*({[^}]+}|\w+)\s*}\s*\)/g;
  modified = modified.replace(withVariablesPattern, (match, queryName, variables) => {
    changeCount++;
    return `API.graphql(graphqlOperation(${queryName}, ${variables}))`;
  });

  // 4. Patrón multi-línea más complejo
  const multiLinePattern = /client\.graphql\s*\(\s*{\s*\n\s*query:\s*(\w+),?\s*\n\s*(?:variables:\s*({[\s\S]*?}))?\s*\n\s*}\s*\)/g;
  modified = modified.replace(multiLinePattern, (match, queryName, variables) => {
    changeCount++;
    if (variables) {
      return `API.graphql(\n        graphqlOperation(${queryName}, ${variables.trim()})\n      )`;
    } else {
      return `API.graphql(\n        graphqlOperation(${queryName})\n      )`;
    }
  });

  // 5. Patrón específico para variables complejas multi-línea
  const complexPattern = /client\.graphql\s*\(\s*{\s*\n\s*query:\s*(\w+),\s*\n\s*variables:\s*{\s*\n([\s\S]*?)\n\s*}\s*\n\s*}\s*\)/g;
  modified = modified.replace(complexPattern, (match, queryName, variableContent) => {
    changeCount++;
    return `API.graphql(\n        graphqlOperation(${queryName}, {\n${variableContent}\n        })\n      )`;
  });

  // 6. Caso especial: variables en línea siguiente
  const splitVariablesPattern = /client\.graphql\s*\(\s*{\s*\n\s*query:\s*(\w+),\s*\n\s*variables:\s*([^}]+)\s*\n\s*}\s*\)/g;
  modified = modified.replace(splitVariablesPattern, (match, queryName, variables) => {
    changeCount++;
    return `API.graphql(\n        graphqlOperation(${queryName}, ${variables.trim()})\n      )`;
  });

  return { modified, changeCount };
}

/**
 * Corrige authSlice.ts específicamente
 */
function fixAuthSlice(content) {
  let modified = content;
  let changeCount = 0;

  // 1. Arreglar changePassword - añadir obtención de usuario si no existe
  if (modified.includes('Auth.changePassword(user,') && !modified.includes('const user = await Auth.currentAuthenticatedUser()')) {
    // Buscar el bloque try donde está changePassword
    const changePasswordPattern = /(async\s*\([^)]*\)[^{]*{[^{]*try\s*{)([\s\S]*?)(await\s+Auth\.changePassword\s*\(user,)/;
    
    modified = modified.replace(changePasswordPattern, (match, p1, p2, p3) => {
      // Solo añadir si no existe ya
      if (!p2.includes('currentAuthenticatedUser')) {
        changeCount++;
        return p1 + '\n      const user = await Auth.currentAuthenticatedUser();' + p2 + p3;
      }
      return match;
    });
  }

  // 2. Si Auth.changePassword todavía tiene el formato antiguo con objeto
  const oldChangePasswordPattern = /Auth\.changePassword\s*\(\s*{\s*oldPassword[^}]+}\s*\)/g;
  if (oldChangePasswordPattern.test(modified)) {
    modified = modified.replace(oldChangePasswordPattern, 'Auth.changePassword(user, oldPassword, newPassword)');
    
    // Asegurar que user está definido
    if (!modified.includes('const user = await Auth.currentAuthenticatedUser()')) {
      const tryBlockPattern = /(try\s*{\s*\n)([\s\S]*?)(Auth\.changePassword)/;
      modified = modified.replace(tryBlockPattern, '$1      const user = await Auth.currentAuthenticatedUser();\n$2$3');
    }
    changeCount++;
  }

  return { modified, changeCount };
}

/**
 * Procesa un archivo específico
 */
async function processFile(filePath) {
  try {
    // Verificar que el archivo existe
    await fs.access(filePath);
    
    const content = await fs.readFile(filePath, 'utf8');
    let totalChanges = 0;
    let modified = content;

    // Aplicar correcciones según el tipo de archivo
    if (filePath.includes('Service.ts')) {
      const result = fixOrphanedClientCalls(modified);
      modified = result.modified;
      totalChanges += result.changeCount;
    } else if (filePath.includes('authSlice.ts')) {
      const result = fixAuthSlice(modified);
      modified = result.modified;
      totalChanges += result.changeCount;
    }

    // Si hay cambios, guardar
    if (totalChanges > 0) {
      // Crear backup
      await fs.writeFile(filePath + CONFIG.backupSuffix, content);
      
      // Escribir archivo modificado
      await fs.writeFile(filePath, modified);
      
      log.success(`Corregido: ${path.basename(filePath)} (${totalChanges} cambios)`);
      return totalChanges;
    } else {
      log.info(`Sin cambios necesarios: ${path.basename(filePath)}`);
      return 0;
    }
  } catch (error) {
    log.error(`Error procesando ${filePath}: ${error.message}`);
    return 0;
  }
}

/**
 * Función principal
 */
async function main() {
  console.log(`\n${CONFIG.colors.bright}🔧 AWS AMPLIFY v5 COMPLETE FIX${CONFIG.colors.reset}`);
  console.log('======================================================================');
  console.log('Completando transformaciones faltantes...\n');

  let totalChanges = 0;
  let filesFixed = 0;

  // Procesar cada archivo objetivo
  for (const file of CONFIG.targetFiles) {
    const changes = await processFile(file);
    if (changes > 0) {
      filesFixed++;
      totalChanges += changes;
    }
  }

  // Resumen
  console.log(`\n${CONFIG.colors.bright}📊 RESUMEN${CONFIG.colors.reset}`);
  console.log('======================================================================');
  console.log(`✅ Archivos corregidos: ${CONFIG.colors.green}${filesFixed}${CONFIG.colors.reset}`);
  console.log(`📝 Total de cambios: ${CONFIG.colors.cyan}${totalChanges}${CONFIG.colors.reset}`);
  
  if (filesFixed > 0) {
    console.log(`\n💾 Backups creados con extensión: ${CONFIG.colors.yellow}${CONFIG.backupSuffix}${CONFIG.colors.reset}`);
  }

  // Verificación final
  console.log(`\n${CONFIG.colors.bright}🔍 VERIFICACIÓN RECOMENDADA${CONFIG.colors.reset}`);
  console.log('======================================================================');
  console.log('1. Revisa que no haya errores de "client is not defined"');
  console.log('2. Verifica que todas las llamadas GraphQL usen API.graphql(graphqlOperation(...))');
  console.log('3. Ejecuta los tests si tienes configurados');
  console.log('4. Prueba la aplicación:');
  console.log(`   ${CONFIG.colors.cyan}cd mobile-app && npm start${CONFIG.colors.reset}`);
  
  console.log('\n✨ ¡Corrección completada!\n');
}

// Ejecutar
main().catch(error => {
  log.error(`Error fatal: ${error.message}`);
  process.exit(1);
});