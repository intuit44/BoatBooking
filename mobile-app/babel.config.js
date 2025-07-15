module.exports = {
  presets: ['@react-native/babel-preset'],
  plugins: [
    // Plugins necesarios para AWS Amplify v5 en React Native
    ['@babel/plugin-proposal-class-properties', { loose: true }],
    ['@babel/plugin-transform-classes', { loose: true }],
    ['@babel/plugin-transform-runtime', { 
      helpers: true, 
      regenerator: false 
    }],
    [
      'module-resolver',
      {
        alias: {
          // Polyfills para crypto y otras APIs de Node.js
          crypto: 'crypto-browserify',
          stream: 'stream-browserify',
          buffer: '@craftzdog/react-native-buffer',
          process: 'process',
          path: 'path-browserify',
          util: 'util',
          // Alias específicos para Amplify v5
          'aws-amplify/api': '@aws-amplify/api',
          'aws-amplify/core': '@aws-amplify/core',
        },
      },
    ],
  ],
};
