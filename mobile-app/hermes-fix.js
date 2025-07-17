// hermes-fix.js - Corrección para errores Hermes específicos
console.log('🔧 [HermesFix] Aplicando correcciones para Hermes...');

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

// Asegurar que console esté disponible
if (typeof global.console === 'undefined') {
  global.console = {
    log: function() {},
    warn: function() {},
    error: function() {}
  };
}

console.log('✅ [HermesFix] Correcciones Hermes aplicadas');
