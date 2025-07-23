const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

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

// ✅ CONFIGURACIÓN CLAVE: Excluir módulos problemáticos completamente
config.resolver.blacklistRE = /(.*\/__tests__\/.*|.*\/node_modules\/@egjs\/hammerjs\/.*\.babelrc|.*\/node_modules\/expo-keep-awake\/.*\.babelrc|.*\/node_modules\/esrecurse\/.*\.babelrc|.*\/node_modules\/find-babel-config\/.*\.babelrc|.*\/node_modules\/gensync\/test\/.*\.babelrc)$/;

// ✅ Configurar transformer con configuraciones explícitas
config.transformer = {
  ...config.transformer,
  babelTransformerPath: require.resolve('metro-react-native-babel-transformer'),
  enableBabelRCLookup: false,
  enableBabelRuntime: false,
  // ✅ Configuración explícita para ignorar .babelrc
  transform: {
    experimentalImportSupport: false,
    inlineRequires: true,
  },
};

// ✅ Configurar watchFolders para excluir módulos problemáticos
config.watchFolders = [
  path.resolve(__dirname, './src'),
  path.resolve(__dirname, './assets'),
  path.resolve(__dirname, './')
];

// ✅ Configurar qué archivos Metro debe procesar
config.resolver.platforms = ['native', 'android', 'ios', 'web'];

// ✅ Excluir archivos específicos del bundling
config.resolver.resolverMainFields = ['react-native', 'browser', 'main'];

module.exports = config;
