const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Resolver aliases para polyfills
config.resolver.alias = {
  crypto: 'crypto-browserify',
  stream: 'stream-browserify',
  buffer: 'buffer',
  util: 'util',
  path: 'path-browserify',
  events: 'events',
  process: 'process',
};

// Configuración específica para SDK 51
config.resolver.sourceExts = ['js', 'jsx', 'ts', 'tsx', 'json'];
config.resolver.platforms = ['ios', 'android', 'native', 'web'];

// Resolución de módulos optimizada
config.resolver.resolverMainFields = [
  'react-native',
  'browser',
  'main'
];

module.exports = config;
