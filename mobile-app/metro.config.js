const {getDefaultConfig} = require('@react-native/metro-config');

/**
 * Metro configuration for React Native Bare Workflow + AWS Amplify
 * https://facebook.github.io/metro/docs/configuration
 */
const config = getDefaultConfig(__dirname);

// Configuración específica para AWS Amplify en React Native
config.resolver.alias = {
  ...config.resolver.alias,
  // Polyfills para APIs de Node.js
  crypto: 'crypto-browserify',
  stream: 'stream-browserify',
  buffer: '@craftzdog/react-native-buffer',
  process: 'process',
  path: 'path-browserify',
  util: 'util',
};

// Extensiones de archivo soportadas
config.resolver.sourceExts = [
  ...config.resolver.sourceExts,
  'cjs', // Para compatibilidad con algunos paquetes de AWS
];

// Configuración del transformer
config.transformer.getTransformOptions = async () => ({
  transform: {
    experimentalImportSupport: false,
    inlineRequires: true,
  },
});

// Ignorar módulos problemáticos
config.resolver.blacklistRE = /node_modules\/.*\/node_modules\/react-native\/.*/;

module.exports = config;
