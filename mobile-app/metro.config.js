const { getDefaultConfig } = require('expo/metro-config');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// Configuración para polyfills de Node.js
config.resolver.alias = {
  crypto: 'crypto-browserify',
  stream: 'stream-browserify',
  buffer: 'buffer',
  events: 'events',
  path: 'path-browserify',
  util: 'util',
  process: 'process/browser',
};

// ✅ Configuración actualizada para Metro 0.82+ y Babel 8+
config.transformer = {
  ...config.transformer,
  babelTransformerPath: require.resolve('metro-react-native-babel-transformer'),
  // ✅ CRÍTICO: Deshabilitar completamente búsqueda de .babelrc
  enableBabelRCLookup: false,
  enableBabelRuntime: false,
  // ✅ Configuración explícita para Metro 0.82+
  experimentalImportSupport: false,
  inlineRequires: true,
};

// ✅ Resolver configuración actualizada
config.resolver = {
  ...config.resolver,
  alias: {
    ...config.resolver.alias,
    crypto: 'crypto-browserify',
    stream: 'stream-browserify',
    buffer: 'buffer',
    events: 'events',
    path: 'path-browserify',
    util: 'util',
    process: 'process/browser',
  },
  platforms: ['native', 'android', 'ios', 'web'],
  resolverMainFields: ['react-native', 'browser', 'main'],
};

module.exports = config;
