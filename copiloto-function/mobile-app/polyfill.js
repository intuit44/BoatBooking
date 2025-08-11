/**
 * Polyfills para AWS Amplify v6 + React Native 0.79.5
 * DEBE cargarse ANTES que cualquier otro módulo
 */

console.log('🔧 [Polyfill] Iniciando carga de polyfills para AWS v6...');

// 1. Global setup - CRÍTICO para React Native
if (typeof global === 'undefined') {
  console.error('❌ [Polyfill] CRITICAL: global is undefined!');
  global = globalThis || {};
}

// Marcar que los polyfills están instalados
global.__RN_GLOBAL_INSTALLED__ = true;
global.global = global;
global.globalThis = global;

// Window para compatibilidad browser
if (typeof global.window === 'undefined') {
  global.window = global;
}

console.log('✅ [Polyfill] Global configurado');

// 2. Buffer polyfill
import { Buffer } from 'buffer';
global.Buffer = Buffer;
console.log('✅ [Polyfill] Buffer configurado');

// 3. Process polyfill
import process from 'process';
global.process = process;
console.log('✅ [Polyfill] Process configurado');

// 4. TextEncoder/TextDecoder
import { TextDecoder, TextEncoder } from 'util';
if (typeof global.TextEncoder === 'undefined') {
  global.TextEncoder = TextEncoder;
}
if (typeof global.TextDecoder === 'undefined') {
  global.TextDecoder = TextDecoder;
}
console.log('✅ [Polyfill] TextEncoder/TextDecoder configurado');

// 5. Crypto polyfill básico
if (typeof global.crypto === 'undefined') {
  global.crypto = {
    getRandomValues: (arr) => {
      for (let i = 0; i < arr.length; i++) {
        arr[i] = Math.floor(Math.random() * 256);
      }
      return arr;
    },
    randomUUID: () => {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
    }
  };
}
console.log('✅ [Polyfill] Crypto básico configurado');

// 6. Hermes error handler
if (global.HermesInternal) {
  console.log('🔍 [Polyfill] Hermes detectado, instalando error handler...');

  const originalError = global.Error;
  global.Error = function (...args) {
    const error = new originalError(...args);
    // Capturar stack trace si está disponible
    if (Error.captureStackTrace) {
      Error.captureStackTrace(error, global.Error);
    }
    return error;
  };
  global.Error.prototype = originalError.prototype;

  // Interceptor de errores para debugging
  if (global.ErrorUtils) {
    const originalHandler = global.ErrorUtils.getGlobalHandler();
    global.ErrorUtils.setGlobalHandler((error, isFatal) => {
      console.error('🚨 [Polyfill] Error capturado:', {
        message: error?.message,
        stack: error?.stack,
        isFatal
      });
      if (originalHandler) {
        originalHandler(error, isFatal);
      }
    });
  }
}

// 7. Verificación final
console.log('🎉 [Polyfill] AWS Amplify v6 polyfills cargados exitosamente');
console.log('🔍 [Polyfill] Estado final:', {
  global: typeof global !== 'undefined',
  Buffer: typeof Buffer !== 'undefined',
  process: typeof process !== 'undefined',
  TextEncoder: typeof TextEncoder !== 'undefined',
  crypto: typeof global.crypto !== 'undefined',
  hermes: !!global.HermesInternal
});

// Exportar para verificación
export default {
  isLoaded: true,
  timestamp: new Date().toISOString()
};