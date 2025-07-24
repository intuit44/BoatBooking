// mobile-app/jest.config.js

module.exports = {
  preset: 'jest-expo',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  transformIgnorePatterns: [
    'node_modules/(?!(jest-)?react-native|@react-native(-community)?|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg|aws-amplify|@aws-amplify/.*|uuid|react-native-url-polyfill)'
  ],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  testEnvironment: 'node',
  // Para manejar timers correctamente
  fakeTimers: {
    enableGlobally: true
  },
  roots: ['<rootDir>'],
  moduleDirectories: ['node_modules', '<rootDir>'],
};