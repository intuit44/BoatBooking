module.exports = {
  preset: 'jest-expo',
  testEnvironment: 'jest-expo/environment',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  transform: {
    '^.+\\.[jt]sx?$': 'babel-jest',
  },
  transformIgnorePatterns: [
    'node_modules/(?!(jest-)?react-native' +
    '|@react-native(-community)?' +
    '|expo' +
    '|expo/.+' +
    '|@expo(nent)?' +
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
    '|react-native-url-polyfill)'
  ],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleDirectories: ['node_modules', '<rootDir>'],
  roots: ['<rootDir>'],
  fakeTimers: {
    enableGlobally: true
  }
};
