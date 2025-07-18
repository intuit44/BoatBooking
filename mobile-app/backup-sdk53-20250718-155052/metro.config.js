const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const config = getDefaultConfig(__dirname);

// CRÍTICO: Resolver explícitamente desde node_modules local
const projectRoot = __dirname;
const localNodeModules = path.resolve(projectRoot, 'node_modules');

config.resolver.alias = {
  // Polyfills estándar
  crypto: 'crypto-browserify',
  stream: 'stream-browserify',
  buffer: 'buffer',
  util: 'util',
  path: 'path-browserify',
  events: 'events',
  process: 'process',
  
  // CRÍTICO: Forzar React Native local
  'react-native': path.resolve(localNodeModules, 'react-native'),
};

// Configuración específica para evitar resolución global
config.resolver.nodeModulesPaths = [localNodeModules];
config.resolver.conditionNames = ['react-native', 'require', 'import'];
config.resolver.sourceExts = ['js', 'jsx', 'ts', 'tsx', 'json'];
config.resolver.platforms = ['ios', 'android', 'native', 'web'];

// CRÍTICO: Solo usar resolución local
config.resolver.resolverMainFields = [
  'react-native',
  'browser', 
  'main'
];

// Evitar buscar en directorios padre
config.watchFolders = [projectRoot];
config.resolver.blockList = [
  // Bloquear directorios padre que puedan tener node_modules
  /.*\/ProyectosSimbolicos\/node_modules\/.*/,
  /.*\/boat-rental-app\/node_modules\/.*/,
];

module.exports = config;
