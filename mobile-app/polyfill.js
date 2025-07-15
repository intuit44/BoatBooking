// polyfill.js - Configuración global requerida por AWS SDK
if (typeof global === 'undefined') {
  global = globalThis;
}

// Polyfill para TextEncoder/TextDecoder (requerido por AWS)
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
}

if (typeof global.TextDecoder === 'undefined') {
  global.TextDecoder = class TextDecoder {
    decode(uint8Array) {
      return String.fromCharCode.apply(null, uint8Array);
    }
  };
}

console.log('✅ [Polyfill] Global y TextEncoder/Decoder configurados');
