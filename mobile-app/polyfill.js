// polyfill.js - Polyfills críticos para AWS Amplify v6 en React Native
// DEBE cargarse ANTES que cualquier otra importación

console.log('🔧 [Polyfill] Iniciando carga de polyfills para AWS v6...');

// =============================================================================
// 1. CORRECCIONES HERMES
// =============================================================================
// Polyfill para $ si está undefined (común en algunos entornos)
if (typeof global.$ === 'undefined') {
  global.$ = {};
}

// Polyfill para Symbol si está undefined
if (typeof Symbol === 'undefined') {
  global.Symbol = {};
  global.Symbol.iterator = '@@iterator';
  global.Symbol.toStringTag = '@@toStringTag';
}

// =============================================================================
// 2. GLOBAL NAMESPACE
// =============================================================================
if (typeof global === 'undefined') {
  global = globalThis;
}

// =============================================================================
// 3. BUFFER POLYFILL (CRÍTICO PARA AWS V6)
// =============================================================================
if (typeof global.Buffer === 'undefined') {
  try {
    global.Buffer = require('buffer').Buffer;
    console.log('✅ [Polyfill] Buffer configurado');
  } catch (error) {
    console.warn('⚠️ [Polyfill] Error cargando Buffer:', error.message);
    // Fallback Buffer básico
    global.Buffer = {
      from: function(data) { return new Uint8Array(data); },
      alloc: function(size) { return new Uint8Array(size); }
    };
  }
}

// =============================================================================
// 4. EVENTS POLYFILL (CRÍTICO PARA STREAM-BROWSERIFY)
// =============================================================================
if (typeof global.events === 'undefined') {
  try {
    global.events = require('events');
    console.log('✅ [Polyfill] Events configurado');
  } catch (error) {
    console.warn('⚠️ [Polyfill] Error cargando Events:', error.message);
    // Fallback events básico
    global.events = {
      EventEmitter: class EventEmitter {
        constructor() {
          this._events = {};
        }
        on(event, listener) {
          if (!this._events[event]) this._events[event] = [];
          this._events[event].push(listener);
        }
        emit(event, ...args) {
          if (this._events[event]) {
            this._events[event].forEach(listener => listener(...args));
          }
        }
      }
    };
  }
}

// =============================================================================
// 5. PROCESS POLYFILL (CRÍTICO PARA AWS V6)
// =============================================================================
if (typeof global.process === 'undefined') {
  try {
    global.process = require('process');
    console.log('✅ [Polyfill] Process configurado');
  } catch (error) {
    console.warn('⚠️ [Polyfill] Error cargando Process:', error.message);
    // Fallback process básico
    global.process = {
      env: {},
      platform: 'react-native',
      version: 'v16.0.0',
      versions: { node: '16.0.0' },
      nextTick: function(fn) { setTimeout(fn, 0); }
    };
  }
  
  // Asegurar NODE_ENV
  global.process.env = global.process.env || {};
  global.process.env.NODE_ENV = global.process.env.NODE_ENV || (__DEV__ ? 'development' : 'production');
}

// =============================================================================
// 6. TEXT ENCODER/DECODER (REQUERIDO POR AWS V6)
// =============================================================================
if (typeof global.TextEncoder === 'undefined') {
  global.TextEncoder = class TextEncoder {
    encode(str) {
      const uint8Array = new Uint8Array(str.length);
      for (let i = 0; i < str.length; i++) {
        uint8Array[i] = str.charCodeAt(i);
      }
      return uint8Array;
    }
  };
  console.log('✅ [Polyfill] TextEncoder configurado');
}

if (typeof global.TextDecoder === 'undefined') {
  global.TextDecoder = class TextDecoder {
    decode(uint8Array) {
      return String.fromCharCode.apply(null, uint8Array);
    }
  };
  console.log('✅ [Polyfill] TextDecoder configurado');
}

// =============================================================================
// 7. CRYPTO POLYFILL PARA AWS
// =============================================================================
if (typeof global.crypto === 'undefined') {
  global.crypto = {
    getRandomValues: function(arr) {
      if (typeof require !== 'undefined') {
        try {
          const randomBytes = require('react-native-get-random-values');
          randomBytes(arr);
          return arr;
        } catch (error) {
          // Fallback a Math.random
          for (let i = 0; i < arr.length; i++) {
            arr[i] = Math.floor(Math.random() * 256);
          }
          return arr;
        }
      } else {
        for (let i = 0; i < arr.length; i++) {
          arr[i] = Math.floor(Math.random() * 256);
        }
        return arr;
      }
    }
  };
  console.log('✅ [Polyfill] Crypto configurado');
}

// =============================================================================
// 8. UTIL POLYFILL
// =============================================================================
if (typeof global.util === 'undefined') {
  try {
    global.util = require('util');
    console.log('✅ [Polyfill] Util configurado');
  } catch (error) {
    global.util = {
      inspect: function(obj) { return JSON.stringify(obj, null, 2); }
    };
  }
}

// =============================================================================
// 9. STREAM POLYFILL
// =============================================================================
if (typeof global.stream === 'undefined') {
  try {
    global.stream = require('stream-browserify');
    console.log('✅ [Polyfill] Stream configurado');
  } catch (error) {
    console.warn('⚠️ [Polyfill] Stream no disponible');
  }
}

// =============================================================================
// 10. PATH POLYFILL
// =============================================================================
if (typeof global.path === 'undefined') {
  try {
    global.path = require('path-browserify');
    console.log('✅ [Polyfill] Path configurado');
  } catch (error) {
    console.warn('⚠️ [Polyfill] Path no disponible');
  }
}

console.log('🎉 [Polyfill] AWS Amplify v6 polyfills cargados exitosamente');
