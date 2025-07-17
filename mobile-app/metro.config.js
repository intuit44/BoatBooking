const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Configuración para AWS Amplify v6 + polyfills
config.resolver.alias = {
  crypto: 'crypto-browserify',
  stream: 'stream-browserify',
  buffer: 'buffer',
  util: 'util',
  path: 'path-browserify',
  events: 'events',  // ✅ AGREGADO: polyfill events
  process: 'process',
};

// Extensiones de archivo
config.resolver.sourceExts = ['js', 'jsx', 'ts', 'tsx', 'json'];

// Configuración para React Native
config.resolver.platforms = ['ios', 'android', 'native', 'web'];

module.exports = config;
