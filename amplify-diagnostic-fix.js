#!/usr/bin/env node

/**
 * 🔧 AWS AMPLIFY v5 DIAGNOSTIC & FORCE FIX
 * 
 * Script de diagnóstico y corrección forzada para problemas de client.graphql()
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
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m',
  },
  backupSuffix: `.backup-force-fix-${Date.now()}`,
  serviceFiles: [
    'mobile-app/src/services/boatsService.ts',
    'mobile-app/src/services/bookingsService.ts', 
    'mobile-app/src/services/reservationsService.ts',
    'mobile-app/src/store/slices/authSlice.ts'
  ]
};

const log = {
  info: (msg) => console.log(`${CONFIG.colors.blue}ℹ${CONFIG.colors.reset}  ${msg}`),
  success: (msg) => console.log(`${CONFIG.colors.green}✅${CONFIG.colors.reset} ${msg}`),
  error: (msg) => console.log(`${CONFIG.colors.red}❌${CONFIG.colors.reset} ${msg}`),
  warning: (msg) => console.log(`${CONFIG.colors.yellow}⚠️${CONFIG.colors.reset}  ${msg}`),
  change: (msg) => console.log(`${CONFIG.colors.cyan}  →${CONFIG.colors.reset} ${msg}`),
};

/**
 * Diagnóstico detallado del archivo
 */
async function diagnoseFile(filePath) {
  try {
    const content = await fs.readFile(filePath, 'utf8');
    const problems = [];
    
    // Verificar imports
    const hasAPIImport = /import\s*{\s*API[^}]*}\s*from\s*['"]aws-amplify['"]/.test(content);
    const hasGraphqlOperation = content.includes('graphqlOperation');
    const hasGenerateClient = content.includes('generateClient');
    
    // Buscar problemas
    const clientDeclaration = content.match(/const\s+client\s*=\s*generateClient/);
    const clientGraphqlCalls = content.match(/client\.graphql/g);
    const awaitClientCalls = content.match(/await\s+client\.graphql/g);
    
    if (clientGraphqlCalls && clientGraphqlCalls.length > 0) {
      problems.push(`Encontradas ${clientGraphqlCalls.length} llamadas a client.graphql()`);
    }
    
    if (!hasAPIImport && clientGraphqlCalls) {
      problems.push('Falta import de API');
    }
    
    if (!hasGraphqlOperation && clientGraphqlCalls) {
      problems.push('Falta import de graphqlOperation');
    }
    
    if (hasGenerateClient) {
      problems.push('Todavía tiene referencias a generateClient');
    }
    
    return {
      hasProblems: problems.length > 0,
      problems,
      stats: {
        hasAPIImport,
        hasGraphqlOperation,
        clientCalls: clientGraphqlCalls ? clientGraphqlCalls.length : 0,
        awaitCalls: awaitClientCalls ? awaitClientCalls.length : 0
      }
    };
  } catch (error) {
    return {
      hasProblems: true,
      problems: [`Error leyendo archivo: ${error.message}`],
      stats: {}
    };
  }
}

/**
 * Corrección forzada y agresiva
 */
async function forceFixFile(filePath) {
  try {
    let content = await fs.readFile(filePath, 'utf8');
    const original = content;
    let changesMade = [];

    // 1. FORZAR import correcto
    if (!content.includes('graphqlOperation') || !content.includes('import { API')) {
      // Eliminar cualquier import de AWS Amplify existente
      content = content.replace(/import\s*{\s*API\s*}\s*from\s*['"]aws-amplify['"];?\s*\n?/g, '');
      content = content.replace(/import\s*{\s*generateClient\s*}\s*from\s*['"]aws-amplify\/api['"];?\s*\n?/g, '');
      
      // Añadir el import correcto al principio después del primer import
      const firstImportMatch = content.match(/import\s+.*?from\s+['"].*?['"];?\s*\n/);
      if (firstImportMatch) {
        const position = firstImportMatch.index + firstImportMatch[0].length;
        content = content.slice(0, position) + 
                 "import { API, graphqlOperation } from 'aws-amplify';\n" + 
                 content.slice(position);
        changesMade.push('Añadido import correcto de API y graphqlOperation');
      }
    }

    // 2. Eliminar CUALQUIER referencia a generateClient
    const beforeGenClient = content;
    content = content.replace(/const\s+client\s*=\s*generateClient\s*\(\s*\)\s*;?\s*\n?/g, '');
    content = content.replace(/\/\/\s*const\s+client\s*=\s*generateClient\s*\(\s*\)\s*;?\s*\n?/g, '');
    if (content !== beforeGenClient) {
      changesMade.push('Eliminadas referencias a generateClient');
    }

    // 3. TRANSFORMACIÓN AGRESIVA de client.graphql
    // Lista de todos los patrones posibles
    const patterns = [
      // Patrón 1: Simple sin variables
      {
        regex: /client\.graphql\s*\(\s*{\s*query:\s*(\w+)\s*}\s*\)/g,
        replacement: 'API.graphql(graphqlOperation($1))'
      },
      // Patrón 2: Con variables inline
      {
        regex: /client\.graphql\s*\(\s*{\s*query:\s*(\w+)\s*,\s*variables:\s*({[^}]+}|\w+)\s*}\s*\)/g,
        replacement: 'API.graphql(graphqlOperation($1, $2))'
      },
      // Patrón 3: Multi-línea simple
      {
        regex: /client\.graphql\s*\(\s*{\s*\n\s*query:\s*(\w+)\s*\n\s*}\s*\)/g,
        replacement: 'API.graphql(graphqlOperation($1))'
      },
      // Patrón 4: Multi-línea con variables
      {
        regex: /client\.graphql\s*\(\s*{\s*\n\s*query:\s*(\w+),?\s*\n\s*variables:\s*({[^}]+}|\w+)\s*\n\s*}\s*\)/g,
        replacement: 'API.graphql(\n        graphqlOperation($1, $2)\n      )'
      }
    ];

    let totalReplacements = 0;
    patterns.forEach(pattern => {
      const before = content;
      content = content.replace(pattern.regex, pattern.replacement);
      if (before !== content) {
        totalReplacements++;
      }
    });

    // 4. Transformación SUPER AGRESIVA para casos complejos
    // Buscar cualquier ocurrencia de client.graphql y transformarla manualmente
    if (content.includes('client.graphql')) {
      const lines = content.split('\n');
      const newLines = [];
      let inClientGraphql = false;
      let graphqlBlock = [];
      let indent = '';
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        if (line.includes('client.graphql(')) {
          inClientGraphql = true;
          indent = line.match(/^\s*/)[0];
          graphqlBlock = [line];
        } else if (inClientGraphql) {
          graphqlBlock.push(line);
          
          // Detectar el final del bloque
          if (line.includes('})')) {
            inClientGraphql = false;
            
            // Analizar el bloque completo
            const blockStr = graphqlBlock.join('\n');
            const queryMatch = blockStr.match(/query:\s*(\w+)/);
            const variablesMatch = blockStr.match(/variables:\s*({[\s\S]*?})\s*}/);
            
            if (queryMatch) {
              const query = queryMatch[1];
              let newCall;
              
              if (variablesMatch) {
                const vars = variablesMatch[1];
                newCall = `${indent}API.graphql(\n${indent}  graphqlOperation(${query}, ${vars})\n${indent})`;
              } else {
                newCall = `${indent}API.graphql(graphqlOperation(${query}))`;
              }
              
              // Reemplazar await si existe
              if (blockStr.includes('await')) {
                newCall = newCall.replace('API.graphql', 'await API.graphql');
              }
              
              // Preservar cualquier cosa después del paréntesis de cierre
              const afterMatch = blockStr.match(/\)\s*(.*)$/);
              if (afterMatch && afterMatch[1]) {
                newCall += afterMatch[1];
              }
              
              newLines.push(newCall);
              totalReplacements++;
            } else {
              // Si no podemos parsear, mantener original
              newLines.push(...graphqlBlock);
            }
            
            graphqlBlock = [];
          }
        } else {
          newLines.push(line);
        }
      }
      
      content = newLines.join('\n');
    }

    if (totalReplacements > 0) {
      changesMade.push(`Transformadas ${totalReplacements} llamadas client.graphql`);
    }

    // 5. Verificación final
    if (content.includes('client.graphql')) {
      changesMade.push('⚠️  ADVERTENCIA: Aún quedan llamadas client.graphql sin transformar');
    }

    // Guardar si hay cambios
    if (content !== original) {
      await fs.writeFile(filePath + CONFIG.backupSuffix, original);
      await fs.writeFile(filePath, content);
      return { success: true, changes: changesMade };
    }

    return { success: false, changes: [] };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Función principal
 */
async function main() {
  console.log(`\n${CONFIG.colors.bright}🔧 AWS AMPLIFY v5 DIAGNOSTIC & FORCE FIX${CONFIG.colors.reset}`);
  console.log('======================================================================\n');

  // Fase 1: Diagnóstico
  console.log(`${CONFIG.colors.bright}📊 FASE 1: DIAGNÓSTICO${CONFIG.colors.reset}`);
  console.log('----------------------------------------------------------------------');
  
  const problematicFiles = [];
  
  for (const file of CONFIG.serviceFiles) {
    const diagnosis = await diagnoseFile(file);
    console.log(`\n📁 ${path.basename(file)}:`);
    
    if (diagnosis.hasProblems) {
      problematicFiles.push(file);
      log.error('Problemas encontrados:');
      diagnosis.problems.forEach(problem => {
        log.change(problem);
      });
      
      if (diagnosis.stats.clientCalls) {
        log.warning(`Llamadas client.graphql: ${diagnosis.stats.clientCalls}`);
      }
    } else {
      log.success('Sin problemas detectados');
    }
  }

  // Fase 2: Corrección
  if (problematicFiles.length > 0) {
    console.log(`\n\n${CONFIG.colors.bright}🔧 FASE 2: CORRECCIÓN FORZADA${CONFIG.colors.reset}`);
    console.log('----------------------------------------------------------------------');
    
    for (const file of problematicFiles) {
      console.log(`\n📝 Corrigiendo ${path.basename(file)}...`);
      const result = await forceFixFile(file);
      
      if (result.success) {
        log.success('Archivo corregido exitosamente');
        result.changes.forEach(change => log.change(change));
      } else if (result.error) {
        log.error(`Error: ${result.error}`);
      } else {
        log.info('No se requirieron cambios');
      }
    }
  }

  // Fase 3: Verificación
  console.log(`\n\n${CONFIG.colors.bright}🔍 FASE 3: VERIFICACIÓN FINAL${CONFIG.colors.reset}`);
  console.log('----------------------------------------------------------------------');
  
  let allFixed = true;
  
  for (const file of CONFIG.serviceFiles) {
    const diagnosis = await diagnoseFile(file);
    
    if (diagnosis.stats.clientCalls > 0) {
      log.error(`${path.basename(file)} - Aún tiene ${diagnosis.stats.clientCalls} llamadas client.graphql`);
      allFixed = false;
    } else {
      log.success(`${path.basename(file)} - OK`);
    }
  }

  // Resumen final
  console.log(`\n\n${CONFIG.colors.bright}📋 RESUMEN${CONFIG.colors.reset}`);
  console.log('======================================================================');
  
  if (allFixed) {
    log.success('¡Todos los archivos están correctamente configurados!');
  } else {
    log.error('Algunos archivos aún tienen problemas. Revisa manualmente.');
  }

  console.log('\n💡 Siguientes pasos:');
  console.log('1. Limpia el cache de Metro: npx react-native start --reset-cache');
  console.log('2. Si es iOS: cd ios && pod install');
  console.log('3. Reconstruye la aplicación');
  
  console.log('\n✨ ¡Proceso completado!\n');
}

// Ejecutar
main().catch(error => {
  log.error(`Error fatal: ${error.message}`);
  process.exit(1);
});