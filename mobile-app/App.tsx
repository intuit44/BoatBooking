// Polyfills necesarios para React Native y AWS SDK
import 'react-native-get-random-values';
import { loadGetRandomValues } from '@aws-amplify/react-native';
loadGetRandomValues();
import { Amplify } from 'aws-amplify';


import 'react-native-url-polyfill/auto';

// Buffer polyfill - Corrección para TypeScript
import { Buffer } from '@craftzdog/react-native-buffer';
// @ts-ignore - Ignorar error de tipos para Buffer global
global.Buffer = Buffer;

// Stream polyfill - Comentado temporalmente para resolver el error
// import 'readable-stream';

import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { Provider as PaperProvider } from 'react-native-paper';
import { Provider as ReduxProvider } from 'react-redux';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';

// Configurar Amplify
import './src/config/amplifyConfig';

// Store
import { store } from './src/store/store';

// Navigation
import { AppNavigator } from './src/navigation/AppNavigator';

// Theme
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

export default function App() {
  console.log("🚀 App loaded");
  useEffect(() => {
    console.log('🚤 Boat Rental App initialized with AWS Amplify');
  }, []);

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
}