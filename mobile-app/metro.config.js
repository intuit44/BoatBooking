const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const config = getDefaultConfig(__dirname);

config.resolver.alias = {
  crypto: 'crypto-browserify',
  stream: 'stream-browserify',
  buffer: 'buffer',
  util: 'util',
  path: 'path-browserify',
  events: 'events',
  process: 'process',

  // ✅ Alias seguros absolutos para evitar ESM
  'aws-amplify': path.resolve(__dirname, 'node_modules/aws-amplify/src/index.ts'),
  'aws-amplify/auth': path.resolve(__dirname, 'node_modules/aws-amplify/src/auth/index.ts'),
  'aws-amplify/api': path.resolve(__dirname, 'node_modules/aws-amplify/src/api/index.ts'),
  'aws-amplify/utils': path.resolve(__dirname, 'node_modules/aws-amplify/src/utils/index.ts'),
  'aws-amplify/storage': path.resolve(__dirname, 'node_modules/aws-amplify/src/storage/index.ts'),
  'aws-amplify/analytics': path.resolve(__dirname, 'node_modules/aws-amplify/src/analytics/index.ts'),
};

config.resolver.conditionNames = ['react-native', 'require', 'import'];
config.resolver.sourceExts = ['js', 'jsx', 'ts', 'tsx', 'json'];
config.resolver.platforms = ['ios', 'android', 'native', 'web'];

config.resolver.resolverMainFields = [
  'react-native',
  'browser',
  'main'  // ❌ ELIMINAMOS 'module'
];

module.exports = config;
