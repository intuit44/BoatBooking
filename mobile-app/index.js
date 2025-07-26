/**
 * Boat Rental App - Entry Point para Expo SDK 53
 * AWS Amplify v6 + React Native 0.79.5 + Expo 53.0.0
 */

// ============================================================================= 
// POLYFILLS - DEBEN IR PRIMERO ANTES DE CUALQUIER IMPORT
// =============================================================================
console.log('🚀 [index.js] ===== INICIO DE CARGA =====');
console.log('🎯 [index.js] Timestamp:', new Date().toISOString());

// 1. Importar polyfill.js PRIMERO
import './polyfill';

console.log('✅ [index.js] Polyfill.js cargado');

// 2. Polyfills específicos para React Native
import 'react-native-get-random-values';
import 'react-native-url-polyfill/auto';

console.log('✅ [index.js] Polyfills RN cargados');

// =============================================================================
// EXPO Y REACT NATIVE
// =============================================================================
import { registerRootComponent } from 'expo';
import { AppRegistry } from 'react-native';

console.log('✅ [index.js] Expo imports cargados');

// =============================================================================
// AWS AMPLIFY V6 CONFIGURATION
// =============================================================================
// Configuración centralizada de Amplify
import { configureAmplify } from './amplify-config';
// IMPORTANTE: Verificar la ruta correcta de aws-exports
import awsconfig from './aws-exports';

console.log('🔧 [index.js] Configurando AWS Amplify v6...');

try {
  configureAmplify(awsconfig);
  console.log('✅ [index.js] AWS Amplify v6 configurado exitosamente');
  console.log('🔍 [index.js] AWS Config:', {
    graphqlEndpoint: awsconfig.aws_appsync_graphqlEndpoint,
    region: awsconfig.aws_appsync_region,
    authType: awsconfig.aws_appsync_authenticationType,
  });
} catch (error) {
  console.error('❌ [index.js] Error configurando AWS Amplify:', error);
  console.error('❌ [index.js] Stack trace:', error.stack);
}

// =============================================================================
// APP COMPONENT IMPORT Y REGISTRO
// =============================================================================
console.log('📱 [index.js] Importando App component...');

// IMPORTANTE: Usar la extensión correcta
import App from './App'; // Si estás usando App.js

console.log('✅ [index.js] App component importado exitosamente');
console.log('📋 [index.js] Registrando componente principal...');

// Registrar componente principal
try {
  registerRootComponent(App);
  console.log('✅ [index.js] registerRootComponent exitoso');
} catch (error) {
  console.error('❌ [index.js] Error en registerRootComponent:', error);
}

// También registrar en AppRegistry como fallback
try {
  AppRegistry.registerComponent('main', () => App);
  AppRegistry.registerComponent('BoatRentalApp', () => App); // Nombre alternativo
  console.log('✅ [index.js] AppRegistry.registerComponent exitoso');
} catch (error) {
  console.error('❌ [index.js] Error en AppRegistry:', error);
}

console.log('🎉 [index.js] ===== CONFIGURACIÓN COMPLETA =====');
console.log('🚀 [index.js] App lista para renderizar');
console.log('📱 [index.js] Expo SDK 53 + RN 0.79.5');

// Debug final
console.log('🔍 [index.js] Debug final:', {
  App: typeof App,
  Amplify: typeof configureAmplify,
  awsconfig: typeof awsconfig,
  global: typeof global !== 'undefined'
});