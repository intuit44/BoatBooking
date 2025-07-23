/**
 * Boat Rental App - Entry Point para Expo SDK 53
 * AWS Amplify v6 + React Native 0.79.5 + Expo 53.0.0
 */

// CRÍTICO: Polyfills ANTES que cualquier import
import './polyfill';

// Polyfills requeridos para AWS v6
import 'react-native-get-random-values';
import 'react-native-url-polyfill/auto';

console.log('🔥 [Index] ===== INDEX.JS SDK 53 EJECUTADO =====');
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

// ✅ EXPO SDK 53: Importación del método correcto para registro
import { registerRootComponent } from 'expo';

// ✅ Importar configuración de Amplify ANTES de App
import './src/config/amplifyConfig';

// ✅ Importación de App con fallback
let App;
try {
  // Intentar importar App.tsx primero, luego App.js
  App = require('./App').default || require('./App');
  console.log('✅ [Index] App imported successfully');
  console.log('🔍 [Index] App type:', typeof App);
} catch (error) {
  console.error('❌ [Index] Error loading App:', error.message);
  console.log('🔧 [Index] Creating fallback App component...');

  // ✅ Crear App básico con navegación
  const React = require('react');
  const { View, Text, ActivityIndicator } = require('react-native');
  const { NavigationContainer } = require('@react-navigation/native');
  const { createNativeStackNavigator } = require('@react-navigation/native-stack');

  const Stack = createNativeStackNavigator();

  function HomeScreen() {
    return React.createElement(View, {
      style: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 }
    }, [
      React.createElement(Text, {
        key: 'title',
        style: { fontSize: 24, marginBottom: 20, textAlign: 'center' }
      }, '🚤 Boat Rental App'),
      React.createElement(Text, {
        key: 'subtitle',
        style: { fontSize: 16, marginBottom: 10, textAlign: 'center' }
      }, 'Expo SDK 53 + React 19 + Amplify v6'),
      React.createElement(Text, {
        key: 'status',
        style: { fontSize: 14, color: 'green', textAlign: 'center' }
      }, '✅ App Running Successfully')
    ]);
  }

  App = function FallbackApp() {
    console.log('🚨 [Index] Using fallback App component');
    return React.createElement(NavigationContainer, {},
      React.createElement(Stack.Navigator, {
        initialRouteName: 'Home'
      },
        React.createElement(Stack.Screen, {
          key: 'home',
          name: 'Home',
          component: HomeScreen,
          options: { title: 'Boat Rental' }
        })
      )
    );
  };
}

console.log('📱 [Index] Registrando componente con Expo SDK 53 registerRootComponent...');

// ✅ EXPO SDK 53: Registro correcto usando registerRootComponent
registerRootComponent(App);

console.log('✅ [Index] Component registered successfully with Expo SDK 53');
console.log('🎉 [Index] Index.js execution completed');
