// mobile-app/jest.config.js

module.exports = {
  preset: 'jest-expo',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  transformIgnorePatterns: [
    'node_modules/(?!(jest-)?react-native' +
    '|@react-native(-community)?' +
    '|expo/' +
    '|expo$' +
    '|@expo(nent)?' +
    '|expo-status-bar' +
    '|@expo-google-fonts' +
    '|react-navigation' +
    '|@react-navigation' +
    '|@unimodules' +
    '|unimodules' +
    '|sentry-expo' +
    '|native-base' +
    '|react-native-svg' +
    '|aws-amplify' +
    '|@aws-amplify' +
    '|uuid' +
    '|react-native-url-polyfill' +
    '|expo-modules-core' +
    ')'
  ],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  moduleDirectories: ['node_modules', '<rootDir>'],
  roots: ['<rootDir>'],
  fakeTimers: {
    enableGlobally: true
  }
};