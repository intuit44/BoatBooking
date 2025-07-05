#!/usr/bin/env node

/**
 * 🔧 FIX AUTHSLICE SYNTAX ERROR
 * Corrige el error de sintaxis en authSlice.ts
 */

const fs = require('fs').promises;
const path = require('path');

async function fixAuthSlice() {
  const filePath = path.join('mobile-app', 'src/store/slices/authSlice.ts');
  
  try {
    let content = await fs.readFile(filePath, 'utf8');
    
    // Crear backup
    await fs.writeFile(filePath + '.backup-syntax', content);
    console.log('✅ Backup creado: authSlice.ts.backup-syntax');
    
    // Buscar el problema alrededor de fetchCurrentUser
    // El problema parece estar en que el código está mal formateado
    
    // Reemplazar la función fetchCurrentUser completa
    const fetchCurrentUserFixed = `export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchCurrentUser',
  async (_, thunkAPI) => {
    try {
      const user = await Auth.currentAuthenticatedUser();
      return {
        id: user.username,
        email: user.attributes?.email || '',
        name: user.attributes?.name || '',
        phone: user.attributes?.phone_number || '',
        role: 'user',
      };
    } catch (error: any) {
      return thunkAPI.rejectWithValue(error.message || 'No hay usuario autenticado');
    }
  }
);`;

    // Buscar y reemplazar la función fetchCurrentUser mal formateada
    const fetchCurrentUserRegex = /export const fetchCurrentUser = createAsyncThunk\([^;]+;/gs;
    
    if (content.match(fetchCurrentUserRegex)) {
      content = content.replace(fetchCurrentUserRegex, fetchCurrentUserFixed);
      console.log('✅ Función fetchCurrentUser corregida');
    } else {
      // Si no encuentra el patrón, intentar una corrección más agresiva
      console.log('⚠️  No se encontró el patrón esperado, intentando corrección alternativa...');
      
      // Buscar desde el inicio de fetchCurrentUser hasta el siguiente export o const
      const startIndex = content.indexOf('export const fetchCurrentUser');
      if (startIndex !== -1) {
        // Buscar el siguiente 'export' o el final del archivo
        let endIndex = content.indexOf('\nexport', startIndex + 1);
        if (endIndex === -1) {
          endIndex = content.indexOf('\nconst authSlice', startIndex);
        }
        if (endIndex === -1) {
          endIndex = content.length;
        }
        
        // Reemplazar toda la sección
        content = content.substring(0, startIndex) + 
                 fetchCurrentUserFixed + '\n\n' +
                 content.substring(endIndex);
        
        console.log('✅ Sección fetchCurrentUser reemplazada');
      }
    }
    
    // Guardar el archivo corregido
    await fs.writeFile(filePath, content);
    console.log('✅ authSlice.ts corregido');
    
    // Verificar que el archivo se puede parsear
    console.log('\n🔍 Verificando sintaxis...');
    const { execSync } = require('child_process');
    try {
      execSync('npx tsc --noEmit --skipLibCheck src/store/slices/authSlice.ts', {
        cwd: 'mobile-app',
        stdio: 'pipe'
      });
      console.log('✅ Sintaxis verificada correctamente');
    } catch (error) {
      console.log('⚠️  Aún hay errores de sintaxis. Revisa manualmente el archivo.');
    }
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

async function main() {
  console.log('🔧 CORRECTOR DE SINTAXIS AUTHSLICE\n');
  await fixAuthSlice();
  console.log('\n✨ Proceso completado');
  console.log('\nEjecuta: cd mobile-app && npx tsc --noEmit --skipLibCheck');
}

main();