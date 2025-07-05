#!/usr/bin/env node

/**
 * 🔍 DIAGNÓSTICO MANUAL DETALLADO
 * 
 * Script para buscar manualmente problemas en el código
 */

const fs = require('fs').promises;
const path = require('path');

const CONFIG = {
  colors: {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m',
  }
};

async function searchInFile(filePath, searchTerms) {
  try {
    const content = await fs.readFile(filePath, 'utf8');
    const lines = content.split('\n');
    const results = [];
    
    lines.forEach((line, index) => {
      searchTerms.forEach(term => {
        if (line.includes(term)) {
          results.push({
            line: index + 1,
            content: line.trim(),
            term: term
          });
        }
      });
    });
    
    return results;
  } catch (error) {
    return null;
  }
}

async function findAllFiles(dir, extensions) {
  const files = [];
  
  try {
    const items = await fs.readdir(dir, { withFileTypes: true });
    
    for (const item of items) {
      const fullPath = path.join(dir, item.name);
      
      if (item.isDirectory() && !item.name.includes('node_modules') && !item.name.startsWith('.')) {
        files.push(...await findAllFiles(fullPath, extensions));
      } else if (item.isFile() && extensions.some(ext => item.name.endsWith(ext))) {
        files.push(fullPath);
      }
    }
  } catch (error) {
    // Ignorar
  }
  
  return files;
}

async function main() {
  console.log(`\n${CONFIG.colors.bright}🔍 DIAGNÓSTICO MANUAL DETALLADO${CONFIG.colors.reset}`);
  console.log('======================================================================\n');

  // Términos problemáticos a buscar
  const searchTerms = [
    'client.graphql',
    'generateClient',
    'client =',
    'graphql({',
    '.graphql(',
    'API.graphql',
    'graphqlOperation',
    'aws-amplify/api',
    'aws-amplify/auth',
    'Auth.signIn',
    'Auth.signUp',
    'non-std C++ exception',
    'RCTFatal'
  ];

  // Buscar en todo el proyecto
  const directories = [
    'mobile-app/src',
    'mobile-app/App.tsx',
    'mobile-app/index.js'
  ];

  console.log('🔍 Buscando problemas potenciales...\n');

  for (const dir of directories) {
    const isFile = dir.endsWith('.tsx') || dir.endsWith('.ts') || dir.endsWith('.js');
    
    if (isFile) {
      // Es un archivo individual
      const results = await searchInFile(dir, searchTerms);
      if (results && results.length > 0) {
        console.log(`${CONFIG.colors.yellow}📄 ${dir}:${CONFIG.colors.reset}`);
        results.forEach(result => {
          console.log(`   ${CONFIG.colors.cyan}Línea ${result.line}:${CONFIG.colors.reset} ${result.content}`);
          console.log(`   ${CONFIG.colors.blue}(Encontrado: "${result.term}")${CONFIG.colors.reset}`);
        });
        console.log('');
      }
    } else {
      // Es un directorio
      const files = await findAllFiles(dir, ['.ts', '.tsx', '.js', '.jsx']);
      
      for (const file of files) {
        const results = await searchInFile(file, searchTerms);
        
        if (results && results.length > 0) {
          const relativePath = path.relative(process.cwd(), file);
          console.log(`${CONFIG.colors.yellow}📄 ${relativePath}:${CONFIG.colors.reset}`);
          
          results.forEach(result => {
            console.log(`   ${CONFIG.colors.cyan}Línea ${result.line}:${CONFIG.colors.reset} ${result.content}`);
            console.log(`   ${CONFIG.colors.blue}(Encontrado: "${result.term}")${CONFIG.colors.reset}`);
          });
          console.log('');
        }
      }
    }
  }

  // Verificar archivos de configuración específicos
  console.log(`\n${CONFIG.colors.bright}📋 VERIFICANDO CONFIGURACIÓN${CONFIG.colors.reset}`);
  console.log('----------------------------------------------------------------------\n');

  const configFiles = [
    'mobile-app/aws-exports.js',
    'mobile-app/src/aws-exports.js',
    'mobile-app/metro.config.js',
    'mobile-app/babel.config.js',
    'mobile-app/package.json'
  ];

  for (const file of configFiles) {
    try {
      await fs.access(file);
      console.log(`${CONFIG.colors.green}✅${CONFIG.colors.reset} ${file} existe`);
      
      // Verificar contenido específico
      if (file.includes('aws-exports')) {
        const content = await fs.readFile(file, 'utf8');
        if (content.includes('aws_appsync_graphqlEndpoint')) {
          console.log(`   ${CONFIG.colors.cyan}→ Contiene configuración GraphQL${CONFIG.colors.reset}`);
        }
      }
      
      if (file.includes('package.json')) {
        const content = await fs.readFile(file, 'utf8');
        const pkg = JSON.parse(content);
        console.log(`   ${CONFIG.colors.cyan}→ aws-amplify: ${pkg.dependencies['aws-amplify'] || 'NO ENCONTRADO'}${CONFIG.colors.reset}`);
      }
    } catch (error) {
      console.log(`${CONFIG.colors.red}❌${CONFIG.colors.reset} ${file} no encontrado`);
    }
  }

  console.log(`\n${CONFIG.colors.bright}💡 SUGERENCIAS${CONFIG.colors.reset}`);
  console.log('======================================================================');
  console.log('1. Si no se encontraron problemas en los archivos, el error puede venir de:');
  console.log('   - Configuración incorrecta de AWS Amplify');
  console.log('   - Falta el archivo aws-exports.js');
  console.log('   - Cache corrupto de Metro/React Native');
  console.log('   - Versión incompatible de dependencias');
  console.log('\n2. Intenta estos comandos de limpieza:');
  console.log(`   ${CONFIG.colors.cyan}cd mobile-app${CONFIG.colors.reset}`);
  console.log(`   ${CONFIG.colors.cyan}rm -rf node_modules${CONFIG.colors.reset}`);
  console.log(`   ${CONFIG.colors.cyan}npm install${CONFIG.colors.reset}`);
  console.log(`   ${CONFIG.colors.cyan}npx react-native start --reset-cache${CONFIG.colors.reset}`);
  console.log(`   ${CONFIG.colors.cyan}cd ios && pod install${CONFIG.colors.reset} (solo iOS)`);
  console.log('\n3. Verifica que App.tsx o index.js tengan:');
  console.log(`   ${CONFIG.colors.yellow}import { Amplify } from 'aws-amplify';${CONFIG.colors.reset}`);
  console.log(`   ${CONFIG.colors.yellow}import awsconfig from './aws-exports';${CONFIG.colors.reset}`);
  console.log(`   ${CONFIG.colors.yellow}Amplify.configure(awsconfig);${CONFIG.colors.reset}`);
  
  console.log('\n✨ Diagnóstico completado\n');
}

main().catch(console.error);