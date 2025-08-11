// Polyfills obligatorios para Hermes
import 'react-native-url-polyfill/auto';
import 'react-native-get-random-values';

// Configuración global de Amplify
import { Amplify } from 'aws-amplify';
import awsconfig from './src/aws-exports';

Amplify.configure({
  ...awsconfig,
  Analytics: {
    disabled: true // Opcional: mejora rendimiento
  }
});