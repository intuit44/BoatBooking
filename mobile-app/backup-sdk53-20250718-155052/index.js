/**
 * Boat Rental App - Entry Point para Expo SDK 53
 * AWS Amplify v6 + React Native 0.72.6 + Expo 53.0.19
 */

// CRÍTICO: Polyfills ANTES que cualquier import
import './polyfill';

// Polyfills requeridos para AWS v6
import 'react-native-get-random-values';
import 'react-native-url-polyfill/auto';

console.log('🔥 [Index] ===== INDEX.JS EXPO EJECUTADO =====');
console.log('🚀 [Index] Iniciando con AWS Amplify v6 + Expo SDK 53...');
console.log('🎯 [Index] Timestamp:', new Date().toISOString());

// Verificación crítica de global antes de continuar
if (typeof global === 'undefined' || !global.__RN_GLOBAL_INSTALLED__) {
  console.error('❌ [Index] CRITICAL: Global not properly installed!');
  // Intentar instalar global de emergencia
  if (typeof globalThis !== 'undefined') {
    globalThis.global = globalThis;
    globalThis.global.__RN_GLOBAL_INSTALLED__ = true;
    console.log('🚨 [Index] Emergency global installation successful');
  }
} else {
  console.log('✅ [Index] Global verification passed');
}

console.log('🔍 [Index] Global status:', {
  global: typeof global !== 'undefined',
  installed: global?.__RN_GLOBAL_INSTALLED__ === true,
  window: typeof global?.window !== 'undefined'
});

// EXPO: Importación del método correcto para registro
import { registerRootComponent } from 'expo';

// Importación defensiva de App
let App;
try {
  App = require('./App').default || require('./App');
  console.log('✅ [Index] App imported successfully');
  console.log('🔍 [Index] App type:', typeof App);
} catch (error) {
  console.error('❌ [Index] Error loading App:', error.message);
  
  // Fallback App básico
  App = function FallbackApp() {
    console.log('🚨 [Index] Using fallback App component');
    return null;
  };
}

console.log('📱 [Index] Registrando componente con Expo registerRootComponent...');

// EXPO: Registro correcto usando registerRootComponent (NO AppRegistry)
registerRootComponent(App);

console.log('✅ [Index] Component registered successfully with Expo');
console.log('🎉 [Index] Index.js execution completed');
