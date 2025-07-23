const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const config = getDefaultConfig(__dirname);

// Configurar resolver para polyfills
config.resolver.alias = {
  ...config.resolver.alias,
  'crypto': 'crypto-browserify',
  'stream': 'stream-browserify',
  'buffer': 'buffer',
  'process': 'process/browser',
  'util': 'util',
  'path': 'path-browserify',
  'events': 'events'
};

// Configurar extensiones de archivos
config.resolver.sourceExts = [
  ...config.resolver.sourceExts,
  'tsx',
  'ts',
  'jsx',
  'js',
  'json'
];

// Configurar transformadores
config.transformer = {
  ...config.transformer,
  babelTransformerPath: require.resolve('metro-react-native-babel-transformer'),
  assetPlugins: ['expo-asset/tools/hashAssetFiles'],
};

console.log('✅ [metro.config.js] Metro configurado con polyfills');

module.exports = config;
