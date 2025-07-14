// =============================================
// POLYFILLS CRÍTICOS (DEBEN SER LOS PRIMEROS)
// =============================================
import 'react-native-get-random-values'; // <-- Primer import absoluto
import 'react-native-url-polyfill/auto'; // <-- Segundo import absoluto
import { Buffer } from '@craftzdog/react-native-buffer';
(global as any).Buffer = Buffer;

// Configuración especial para Hermes
// @ts-expect-error: HermesInternal no está en los tipos
const isHermes = !!global.HermesInternal;
if (isHermes) {
  console.log('🔥 Hermes engine detected');
}

// =============================================
// CONFIGURACIÓN AMPLIFY (CON POLYFLLS CARGADOS)
// =============================================
import { loadGetRandomValues } from '@aws-amplify/react-native';
loadGetRandomValues(); // <-- Debe ir después de los polyfills

// =============================================
// IMPORTS DE REACT Y LIBRERÍAS
// =============================================
import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { Provider as PaperProvider } from 'react-native-paper';
import { Provider as ReduxProvider } from 'react-redux';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Platform, View, Text, ActivityIndicator } from 'react-native';
import Constants from 'expo-constants';

// =============================================
// COMPONENTES DE LA APP
// =============================================
import { store } from './src/store/store';
import { AppNavigator } from './src/navigation/AppNavigator';
import { checkAuthStatus } from './src/store/slices/authSlice';

// Debug info
console.log("📦 Expo Runtime Version:", Constants.expoConfig?.runtimeVersion ?? "Not defined");
console.log("🧠 Platform:", Platform.OS);
console.log("⚙️ JS engine:", isHermes ? "Hermes" : "JSC");

// UI theme
const theme = {
  colors: {
    primary: '#0066CC',
    accent: '#FF5A5F',
    background: '#FFFFFF',
    surface: '#FFFFFF',
    text: '#000000',
    disabled: '#CCCCCC',
    placeholder: '#666666',
    backdrop: 'rgba(0, 0, 0, 0.5)',
  },
};

// Componente de prueba simple
function TestComponent() {
  console.log('🎯 TestComponent rendered');
  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f0f0f0' }}>
      <Text style={{ fontSize: 24, marginBottom: 20 }}>Boat Rental App</Text>
      <Text style={{ fontSize: 16, marginBottom: 20 }}>Test Component</Text>
      <ActivityIndicator size="large" color="#0066CC" />
      <Text style={{ marginTop: 20 }}>Si ves esto, React está funcionando ✅</Text>
    </View>
  );
}

export default function App() {
  console.log("🚀 App component starting to render");

  useEffect(() => {
    console.log('🚤 App useEffect executed');

    // Check auth status on app start
    try {
      console.log('📱 Dispatching checkAuthStatus');
      store.dispatch(checkAuthStatus());
    } catch (error) {
      console.error('❌ Error dispatching checkAuthStatus:', error);
    }
  }, []);

  // Primero probemos con un componente simple
  const TESTING = false; // Cambia esto a false cuando funcione

  if (TESTING) {
    console.log('🧪 Rendering test component');
    return <TestComponent />;
  }

  console.log('🎨 Rendering full app');

  try {
    return (
      <SafeAreaProvider>
        <ReduxProvider store={store}>
          <PaperProvider theme={theme}>
            <NavigationContainer>
              <StatusBar style="auto" />
              <AppNavigator />
            </NavigationContainer>
          </PaperProvider>
        </ReduxProvider>
      </SafeAreaProvider>
    );
  } catch (error) {
    console.error('❌ Error rendering app:', error);
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <Text>Error al cargar la app</Text>
        <Text>{error?.toString()}</Text>
      </View>
    );
  }
}

console.log('📄 App.tsx loaded completely');