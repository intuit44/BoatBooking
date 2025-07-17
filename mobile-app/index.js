/**
 * Boat Rental App - Entry Point Ultra Robusto
 * AWS Amplify v6 + React Native 0.79.5 Compatible
 */

// CRÍTICO: Polyfills ANTES que cualquier import
import './polyfill';

// Polyfills requeridos para AWS v6
import 'react-native-get-random-values';
import 'react-native-url-polyfill/auto';

import { AppRegistry } from 'react-native';

// Verificación crítica de global antes de continuar
if (typeof global === 'undefined' || !global.__RN_GLOBAL_INSTALLED__) {
  console.error('❌ [Index] CRITICAL: Global not properly installed!');
  // Intentar instalar global de emergencia
  if (typeof globalThis !== 'undefined') {
    global = globalThis;
    global.__RN_GLOBAL_INSTALLED__ = true;
    console.log('🚨 [Index] Emergency global installation successful');
  }
}

// Importación defensiva de App
let App;
try {
  App = require('./App').default;
  console.log('✅ [Index] App imported successfully');
} catch (error) {
  console.error('❌ [Index] Error loading App:', error);
  App = () => null; // Fallback
}

console.log('🔥 [Index] ===== INDEX.JS EJECUTADO =====');
console.log('🚀 [Index] Iniciando con AWS Amplify v6 Ultra Robusto...');
console.log('📱 [Index] Registrando componente principal...');
console.log('🔍 [Index] Global verification:', {
  global: typeof global !== 'undefined',
  installed: global?.__RN_GLOBAL_INSTALLED__ === true
});

// Registro correcto de la aplicación
AppRegistry.registerComponent('main', () => App);

console.log('✅ [Index] Component registered successfully');
