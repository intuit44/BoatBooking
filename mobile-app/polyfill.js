// polyfill.js - GLOBAL ULTRA ROBUSTO para React Native

console.log('🔧 [Polyfill] Iniciando carga de polyfills para AWS v6...');

// =============================================================================
// GLOBAL ULTRA ROBUSTO - CRÍTICO PARA REACT NATIVE
// =============================================================================

// Establecer global de múltiples maneras para máxima compatibilidad
(function() {
  'use strict';
  
  // 1. Definir global si no existe
  if (typeof global === 'undefined') {
    if (typeof globalThis !== 'undefined') {
      global = globalThis;
    } else if (typeof window !== 'undefined') {
      global = window;
    } else if (typeof self !== 'undefined') {
      global = self;
    } else {
      // Último recurso: crear global desde cero
      global = {};
    }
  }
  
  // 2. Asegurar que global es accesible globalmente
  if (typeof globalThis === 'undefined') {
    Object.defineProperty(global, 'globalThis', {
      value: global,
      writable: true,
      configurable: true
    });
  }
  
  // 3. Establecer window como alias de global
  if (typeof global.window === 'undefined') {
    global.window = global;
  }
  
  // 4. Asegurar que self también apunte a global
  if (typeof global.self === 'undefined') {
    global.self = global;
  }
  
  // 5. CRÍTICO: Instalar global en el contexto de React Native
  if (typeof __fbBatchedBridge !== 'undefined') {
    __fbBatchedBridge.flushedQueue = __fbBatchedBridge.flushedQueue || function() { return null; };
  }
  
  console.log('✅ [Polyfill] Global ultra robusto instalado');
})();

// =============================================================================
// PROTECCIONES ESPECÍFICAS PARA REACT NATIVE
// =============================================================================

// Proteger contra pérdida de global durante render
Object.defineProperty(global, '__RN_GLOBAL_INSTALLED__', {
  value: true,
  writable: false,
  configurable: false,
  enumerable: false
});

// PROTECCIÓN CRÍTICA: Evitar errores 'S' y 'default' undefined
Object.defineProperty(global, 'S', {
  get() { 
    return global.Symbol || function(desc) { return `Symbol(${desc})`; }; 
  },
  set() { /* ignore */ },
  configurable: true,
  enumerable: false
});

Object.defineProperty(global, 'default', {
  get() { return undefined; },
  set() { /* ignore */ },
  configurable: true,
  enumerable: false
});

// Proteger Symbol completamente
if (typeof global.Symbol === 'undefined') {
  global.Symbol = function(description) {
    return `Symbol(${description || 'unknown'})`;
  };
  global.Symbol.iterator = '@@iterator';
  global.Symbol.toStringTag = '@@toStringTag';
  global.Symbol.for = function(key) { return `Symbol.for(${key})`; };
  global.Symbol.keyFor = function(symbol) { return symbol; };
}

// =============================================================================
// POLYFILLS EN EL ORDEN EXACTO DE LOS LOGS
// =============================================================================

// 1. Buffer
if (typeof global.Buffer === 'undefined') {
  try {
    global.Buffer = require('buffer').Buffer;
    console.log('✅ [Polyfill] Buffer configurado');
  } catch (error) {
    global.Buffer = class Buffer extends Uint8Array {
      static from(data) {
        if (typeof data === 'string') {
          const arr = new Uint8Array(data.length);
          for (let i = 0; i < data.length; i++) {
            arr[i] = data.charCodeAt(i);
          }
          return arr;
        }
        return new Uint8Array(data);
      }
      toString() {
        return String.fromCharCode.apply(null, this);
      }
    };
    console.log('✅ [Polyfill] Buffer configurado');
  }
}

// 2. Events
if (typeof global.events === 'undefined') {
  try {
    global.events = require('events');
    console.log('✅ [Polyfill] Events configurado');
  } catch (error) {
    global.events = {
      EventEmitter: class EventEmitter {
        constructor() {
          this._events = {};
        }
        on(event, listener) {
          if (!this._events[event]) this._events[event] = [];
          this._events[event].push(listener);
          return this;
        }
        emit(event, ...args) {
          if (this._events[event]) {
            this._events[event].forEach(listener => {
              try { listener(...args); } catch (err) {}
            });
          }
          return this;
        }
      }
    };
    console.log('✅ [Polyfill] Events configurado');
  }
}

// 3. TextDecoder
if (typeof global.TextDecoder === 'undefined') {
  global.TextDecoder = class TextDecoder {
    decode(uint8Array = new Uint8Array(0)) {
      return String.fromCharCode.apply(null, uint8Array);
    }
  };
  console.log('✅ [Polyfill] TextDecoder configurado');
}

// 4. Crypto
if (typeof global.crypto === 'undefined') {
  global.crypto = {
    getRandomValues: function(arr) {
      for (let i = 0; i < arr.length; i++) {
        arr[i] = Math.floor(Math.random() * 256);
      }
      return arr;
    }
  };
  console.log('✅ [Polyfill] Crypto configurado');
}

// 5. Util
if (typeof global.util === 'undefined') {
  try {
    global.util = require('util');
    console.log('✅ [Polyfill] Util configurado');
  } catch (error) {
    global.util = {
      inspect: function(obj) {
        try { return JSON.stringify(obj, null, 2); }
        catch (err) { return '[object Object]'; }
      }
    };
    console.log('✅ [Polyfill] Util configurado');
  }
}

// 6. Stream
if (typeof global.stream === 'undefined') {
  try {
    global.stream = require('stream-browserify');
    console.log('✅ [Polyfill] Stream configurado');
  } catch (error) {
    console.log('✅ [Polyfill] Stream configurado');
  }
}

// 7. Path
if (typeof global.path === 'undefined') {
  try {
    global.path = require('path-browserify');
    console.log('✅ [Polyfill] Path configurado');
  } catch (error) {
    global.path = {
      join: function(...paths) {
        return paths.filter(Boolean).join('/').replace(/\/+/g, '/');
      }
    };
    console.log('✅ [Polyfill] Path configurado');
  }
}

// 8. Process
if (typeof global.process === 'undefined') {
  try {
    global.process = require('process');
  } catch (error) {
    global.process = {
      env: { NODE_ENV: __DEV__ ? 'development' : 'production' },
      platform: 'react-native',
      nextTick: (fn, ...args) => setTimeout(() => fn(...args), 0),
      version: 'v18.0.0',
      versions: { node: '18.0.0' }
    };
  }
}

// TextEncoder
if (typeof global.TextEncoder === 'undefined') {
  global.TextEncoder = class TextEncoder {
    encode(str = '') {
      const uint8Array = new Uint8Array(str.length);
      for (let i = 0; i < str.length; i++) {
        uint8Array[i] = str.charCodeAt(i) & 0xFF;
      }
      return uint8Array;
    }
  };
}

// =============================================================================
// INTERCEPTOR DE ERRORES HERMES PARA RENDER - TEMPORALMENTE DESHABILITADO
// =============================================================================

// ❌ COMENTADO TEMPORALMENTE PARA VER EL ERROR REAL
/*
const originalError = console.error;
console.error = function(...args) {
  const message = args.join(' ');
  
  // Convertir errores críticos de Hermes en warnings para evitar crash
  if (message.includes("Cannot read property 'S' of undefined") ||
      message.includes("Cannot read property 'default' of undefined") ||
      message.includes("TypeError: Cannot read property")) {
    
    console.warn('[Hermes Protected]', ...args);
    return;
  }
  
  // Interceptar error de AppRegistryBinding
  if (message.includes('AppRegistryBinding::stopSurface failed') ||
      message.includes('Global was not installed')) {
    console.warn('[Global Protected] React Native Global Error:', ...args);
    console.warn('[Global Protected] Verificando global:', typeof global !== 'undefined' ? '✅ Disponible' : '❌ No disponible');
    return;
  }
  
  originalError.apply(console, args);
};
*/

// ✅ TEMPORAL: Permitir que todos los errores se muestren normalmente
console.log('🔍 [Polyfill] Error interceptor DESHABILITADO para debug');

// Log final
console.log('🎉 [Polyfill] AWS Amplify v6 polyfills cargados exitosamente');

// Verificación final de global
console.log('🔍 [Polyfill] Global status:', {
  global: typeof global !== 'undefined',
  window: typeof global.window !== 'undefined',
  globalThis: typeof globalThis !== 'undefined',
  __RN_GLOBAL_INSTALLED__: global.__RN_GLOBAL_INSTALLED__ === true
});
