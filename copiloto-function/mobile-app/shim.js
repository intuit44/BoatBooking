// Polyfills para módulos de Node.js
if (typeof __dirname === 'undefined') global.__dirname = '/';
if (typeof __filename === 'undefined') global.__filename = '';
if (typeof process === 'undefined') {
  global.process = require('process');
} else {
  const bProcess = require('process');
  for (const p in bProcess) {
    if (!(p in process)) {
      process[p] = bProcess[p];
    }
  }
}

global.Buffer = require('buffer').Buffer;
global.process.env.NODE_ENV = __DEV__ ? 'development' : 'production';

// Evitar que sea procesado recursivamente
if (typeof btoa === 'undefined') {
  global.btoa = function (str) {
    return new Buffer(str, 'utf-8').toString('base64');
  };
}

if (typeof atob === 'undefined') {
  global.atob = function (b64Encoded) {
    return new Buffer(b64Encoded, 'base64').toString('utf-8');
  };
}