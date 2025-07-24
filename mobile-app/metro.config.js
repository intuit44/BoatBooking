const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

console.log('🔧 [Metro] Configurando Metro para Expo SDK 53...');

const config = getDefaultConfig(__dirname);

// Configurar resolver para polyfills
config.resolver.alias = {
  ...config.resolver.alias,
  'crypto': require.resolve('crypto-browserify'),
  'stream': require.resolve('stream-browserify'),
  'buffer': require.resolve('buffer'),
  'process': require.resolve('process/browser'),
  'util': require.resolve('util'),
  'path': require.resolve('path-browserify'),
  'events': require.resolve('events')
};

// Configurar extensiones de archivos - ORDEN IMPORTANTE
config.resolver.sourceExts = [
  'tsx',
  'ts',
  'jsx',
  'js',
  'json',
  'cjs',
  'mjs'
];

// Asset extensions
config.resolver.assetExts = config.resolver.assetExts.filter(
  ext => ext !== 'svg'
);

// Configurar transformador
config.transformer = {
  ...config.transformer,
  babelTransformerPath: require.resolve('metro-react-native-babel-transformer'),
  minifierPath: require.resolve('metro-minify-terser'),
  assetPlugins: ['expo-asset/tools/hashAssetFiles'],
};

// Watchman config para mejor detección de cambios
config.watchFolders = [__dirname];
config.resetCache = true;

// Configuración para mejor debugging
config.server = {
  ...config.server,
  enhanceMiddleware: (middleware) => {
    return (req, res, next) => {
      console.log(`[Metro] ${req.method} ${req.url}`);
      return middleware(req, res, next);
    };
  },
};

// Cache configuration
config.cacheVersion = '1.0';

console.log('✅ [Metro] Configuración completada');
console.log('📁 [Metro] Project root:', __dirname);
console.log('📦 [Metro] Source extensions:', config.resolver.sourceExts);

module.exports = config;