/**
 * Boat Rental App - Entry Point Ultra Robusto
 * AWS Amplify v6 + React Native 0.79.5 Compatible
 */

// CRÍTICO: Polyfills ANTES que cualquier import
import './polyfill';

// Polyfills requeridos para AWS v6
import 'react-native-get-random-values';
import 'react-native-url-polyfill/auto';

import { AppRegistry } from 'react-native';

// Importación defensiva de App
let App;
try {
  App = require('./App').default;
} catch (error) {
  console.error('❌ Error cargando App:', error);
  App = () => null; // Fallback
}

console.log('🚀 [Index] Iniciando con AWS Amplify v6 Ultra Robusto...');

// Registro correcto de la aplicación
AppRegistry.registerComponent('main', () => App);
