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
  console.log('✅ [App] Iniciando render con protecciones Hermes...');
  
  // Protección adicional contra errores Hermes en render
  try {
    console.log('✅ [App] Renderizando app principal');
    
    useEffect(() => {
      console.log('🎯 [App] App montada exitosamente');
    }, []);

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
} catch (error) {
    console.error('❌ [App] Error en render:', error);
    return (
      <SafeAreaProvider>
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f8f9fa' }}>
          <Text style={{ fontSize: 18, color: '#e74c3c', textAlign: 'center', margin: 20 }}>
            ❌ Error de Render{'\n'}
            Verificar logs de consola
          </Text>
        </View>
      </SafeAreaProvider>
    );
  }
}