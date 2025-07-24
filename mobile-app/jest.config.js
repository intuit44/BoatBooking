// mobile-app/jest.config.js

module.exports = {
  preset: 'jest-expo',
  testEnvironment: 'jest-expo/environment/jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg|aws-amplify|@aws-amplify/.*|uuid|react-native-url-polyfill)'
  ],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': [
      'babel-jest',
      {
        presets: ['babel-preset-expo']
      }
    ]
  },
  // Para manejar correctamente los módulos de Expo
  moduleNameMapper: {
    '^expo$': '<rootDir>/node_modules/expo/build/index.js'
  },
  // Variables globales
  globals: {
    __DEV__: true
  },
  // Para manejar timers correctamente
  fakeTimers: {
    enableGlobally: true
  }
};