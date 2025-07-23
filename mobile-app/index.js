/**
 * Boat Rental App - Entry Point para Expo SDK 53
 * AWS Amplify v6 + React Native 0.79.5 + Expo 53.0.0
 */

// ============================================================================= 
// POLYFILLS - DEBEN IR PRIMERO ANTES DE CUALQUIER IMPORT
// =============================================================================
console.log('🚀 [index.js] ===== INICIO DE CARGA =====');
console.log('🎯 [index.js] Timestamp:', new Date().toISOString());

// 1. Polyfills críticos
import 'react-native-get-random-values';
import 'react-native-url-polyfill/auto';

// 2. Buffer y crypto polyfills
import { Buffer } from 'buffer';
global.Buffer = Buffer;

// 3. Process polyfill
import process from 'process';
global.process = process;

// 4. Stream y util polyfills
import 'stream-browserify';
import 'util';

console.log('✅ [index.js] Polyfills cargados correctamente');

// =============================================================================
// EXPO Y REACT NATIVE
// =============================================================================
import { registerRootComponent } from 'expo';
import { AppRegistry } from 'react-native';

console.log('✅ [index.js] Expo imports cargados');

// =============================================================================
// AWS AMPLIFY V6 CONFIGURATION
// =============================================================================
import { Amplify } from 'aws-amplify';
import awsconfig from './src/aws-exports';

console.log('🔧 [index.js] Configurando AWS Amplify v6...');

try {
  Amplify.configure(awsconfig);
  console.log('✅ [index.js] AWS Amplify v6 configurado exitosamente');
  console.log('🔍 [index.js] AWS Config:', {
    graphqlEndpoint: awsconfig.aws_appsync_graphqlEndpoint,
    region: awsconfig.aws_appsync_region,
    authType: awsconfig.aws_appsync_authenticationType
  });
} catch (error) {
  console.error('❌ [index.js] Error configurando AWS Amplify:', error);
}

// =============================================================================
// APP COMPONENT IMPORT Y REGISTRO
// =============================================================================
console.log('📱 [index.js] Importando App component...');

import App from './App';

console.log('✅ [index.js] App component importado exitosamente');
console.log('📋 [index.js] Registrando componente principal...');

// Registrar componente principal
registerRootComponent(App);

// También registrar en AppRegistry como fallback
AppRegistry.registerComponent('main', () => App);

console.log('🎉 [index.js] ===== CONFIGURACIÓN COMPLETA =====');
console.log('🚀 [index.js] App lista para renderizar');
