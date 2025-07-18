// src/shims/react-native-shim.js
// Wrapper protectivo para React Native que maneja errores "typeof"

console.log('🔧 [ReactNativeShim] Cargando wrapper protectivo...');

let ReactNative;

try {
  // Intentar cargar React Native de la forma estándar
  ReactNative = require('react-native');
  console.log('✅ [ReactNativeShim] React Native cargado exitosamente');
} catch (error) {
  console.log('⚠️ [ReactNativeShim] Error cargando React Native:', error.message);
  
  // Fallback: crear mock básico para desarrollo
  ReactNative = {
    View: 'View',
    Text: 'Text',
    StyleSheet: {
      create: (styles) => styles,
    },
    TouchableOpacity: 'TouchableOpacity',
    ScrollView: 'ScrollView',
    SafeAreaView: 'SafeAreaView',
    Modal: 'Modal',
    Alert: {
      alert: (title, message, buttons) => {
        console.log(`Alert: ${title} - ${message}`);
      }
    },
    Platform: {
      OS: 'ios',
      select: (config) => config.ios || config.default,
    },
    Dimensions: {
      get: () => ({ width: 375, height: 812 }),
    },
    // Agregar más componentes según se necesiten
  };
  
  console.log('🔄 [ReactNativeShim] Usando mock básico para desarrollo');
}

module.exports = ReactNative;
