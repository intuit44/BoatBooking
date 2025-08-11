module.exports = {
  preset: 'jest-expo',
  testEnvironment: 'node',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  transformIgnorePatterns: [
    'node_modules/(?!(jest-)?react-native' +
    '|@react-native(-community)?' +
    '|@react-navigation/.*' +
    '|react-navigation' +
    '|expo(nent)?|@expo(nent)?/.*' +
    '|@expo-google-fonts/.*' +
    '|expo-.*' +
    '|@unimodules/.*' +
    '|unimodules' +
    '|sentry-expo' +
    '|native-base' +
    '|react-native-svg' +
    '|react-native-screens' +
    '|react-native-safe-area-context' +
    '|react-native-gesture-handler' +
    '|react-native-reanimated' +
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
  moduleNameMapper: {
    // Mock crítico para evitar el error de runtime.native.ts
    '^expo/src/winter/runtime\\.native$': '<rootDir>/__mocks__/expoRuntimeStub.js',
    '^expo/src/winter/index$': '<rootDir>/__mocks__/expoWinterStub.js',
    // Mock adicional para evitar problemas con TypeScript
    '\\.tsx?$': '<rootDir>/__mocks__/fileMock.js',
    // Mock para aws-exports si no existe
    '^../aws-exports$': '<rootDir>/__mocks__/aws-exports.js'
  },
  testMatch: [
    '**/__tests__/**/*.(js|jsx|ts|tsx)',
    '**/?(*.)+(spec|test).(js|jsx|ts|tsx)'
  ],
  // Configuración para manejar archivos TypeScript
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest'
  },
  globals: {
    __DEV__: true
  },
  // Evitar que Jest procese archivos de Expo que causan problemas
  modulePathIgnorePatterns: [
    '<rootDir>/node_modules/expo/src/winter/'
  ]
};