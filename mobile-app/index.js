/**
 * Boat Rental App - Entry Point
 */

// IMPORTANTE: Cargar polyfill ANTES de cualquier otra cosa
import './polyfill';

// Polyfills requeridos para React Native + AWS
import 'react-native-get-random-values';
import 'react-native-url-polyfill/auto';

import { AppRegistry } from 'react-native';
import App from './App';

console.log('🚀 [Index] Iniciando app con polyfills...');

// SOLUCIÓN: Usar nombre fijo en lugar de leer desde app.json
AppRegistry.registerComponent('main', () => App);
