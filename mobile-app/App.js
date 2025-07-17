/**
 * Boat Rental App - Main App Component SIMPLIFICADO
 * AWS Amplify v6 + React Native 0.79.5 + React 18.2.0
 */

// ORDEN CRÍTICO: Polyfills ANTES que cualquier otra cosa
import './polyfill';

// Polyfills específicos para React Native + AWS v6
import 'react-native-get-random-values';
import 'react-native-url-polyfill/auto';


import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Provider as PaperProvider } from 'react-native-paper';

// Importar HomeScreen directamente para evitar problemas de navegación
import HomeScreen from './src/screens/home/HomeScreen';

console.log('🚀 [App] Iniciando con AWS Amplify v6 Ultra Robusto...');

export default function App() {
  // Verificación crítica de global
  if (typeof global === 'undefined' || !global.__RN_GLOBAL_INSTALLED__) {
    console.error('❌ [App] CRITICAL: Global not available in App component!');
    return null;
  }
  
  console.log('🔥 [App] ===== APP FUNCTION EJECUTADA =====');
  console.log('🎯 [App] Timestamp:', new Date().toISOString());
  console.log('🔍 [App] Global status:', {
    available: typeof global !== 'undefined',
    installed: global.__RN_GLOBAL_INSTALLED__ === true,
    window: typeof global.window !== 'undefined'
  });
  console.log('🔥 [App] ===== APP FUNCTION EJECUTADA =====');
  console.log('🎯 [App] Timestamp:', new Date().toISOString());

  console.log('🚀 [App] RETURN STATEMENT - About to render App JSX');
  console.log('📦 [App] Rendering: SafeAreaProvider > PaperProvider > NavigationContainer > HomeScreen');
  
  return (
    <SafeAreaProvider>
      <PaperProvider>
        <NavigationContainer>
          <HomeScreen />
          <StatusBar style="light" />
        </NavigationContainer>
      </PaperProvider>
    </SafeAreaProvider>
  );
}
