/**
 * Boat Rental App - Main App Component ULTRA VERBOSE
 * AWS Amplify v6 + React Native 0.79.5 + React 18.2.0
 */

console.log('🔥 [App] ===== APP.JS INICIANDO CARGA =====');
console.log('🎯 [App] Timestamp INICIO:', new Date().toISOString());

// ORDEN CRÍTICO: Polyfills ANTES que cualquier otra cosa
import './polyfill';

console.log('✅ [App] Polyfill importado');

// Polyfills específicos para React Native + AWS v6
import 'react-native-get-random-values';
import 'react-native-url-polyfill/auto';

console.log('✅ [App] Polyfills RN importados');

import React, { useEffect } from 'react';
console.log('✅ [App] React importado');

import { StatusBar } from 'expo-status-bar';
console.log('✅ [App] StatusBar importado');

import { NavigationContainer } from '@react-navigation/native';
console.log('✅ [App] NavigationContainer importado');

import { SafeAreaProvider } from 'react-native-safe-area-context';
console.log('✅ [App] SafeAreaProvider importado');

import { Provider as PaperProvider } from 'react-native-paper';
console.log('✅ [App] PaperProvider importado');

// Importar HomeScreen directamente para evitar problemas de navegación
import HomeScreen from './src/screens/home/HomeScreen';
console.log('✅ [App] HomeScreen importado');

console.log('🚀 [App] TODOS LOS IMPORTS COMPLETADOS');
console.log('🚀 [App] Iniciando con AWS Amplify v6 Ultra Robusto...');

export default function App() {
  console.log('🔥 [App] ===== APP FUNCTION EJECUTADA =====');
  console.log('🎯 [App] Timestamp FUNCTION:', new Date().toISOString());
  
  // Verificación crítica de global
  if (typeof global === 'undefined' || !global.__RN_GLOBAL_INSTALLED__) {
    console.error('❌ [App] CRITICAL: Global not available in App component!');
    return null;
  }
  
  console.log('🔍 [App] Global status:', {
    available: typeof global !== 'undefined',
    installed: global.__RN_GLOBAL_INSTALLED__ === true,
    window: typeof global.window !== 'undefined'
  });
  
  // useEffect para logging de mount
  useEffect(() => {
    console.log('🎉 [App] ===== APP COMPONENT MOUNTED =====');
    console.log('🎯 [App] Mount timestamp:', new Date().toISOString());
    
    return () => {
      console.log('💀 [App] App component unmounting');
    };
  }, []);

  console.log('🚀 [App] RETURN STATEMENT - About to render App JSX');
  console.log('📦 [App] Rendering: SafeAreaProvider > PaperProvider > NavigationContainer > HomeScreen');
  
  try {
    const appJSX = (
      <SafeAreaProvider>
        <PaperProvider>
          <NavigationContainer>
            <HomeScreen />
            <StatusBar style="light" />
          </NavigationContainer>
        </PaperProvider>
      </SafeAreaProvider>
    );
    
    console.log('✅ [App] JSX creado exitosamente');
    console.log('🎉 [App] ===== APP RENDER COMPLETADO =====');
    
    return appJSX;
    
  } catch (error) {
    console.error('❌ [App] ERROR EN RENDER:', error);
    console.error('❌ [App] Error stack:', error.stack);
    
    return null;
  }
}

console.log('🎉 [App] ===== APP.JS CARGA COMPLETADA =====');
