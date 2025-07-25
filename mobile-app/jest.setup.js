// mobile-app/jest.setup.js

// Polyfills para setImmediate y clearImmediate
if (typeof global.setImmediate === 'undefined') {
  global.setImmediate = (cb) => setTimeout(cb, 0);
}
if (typeof global.clearImmediate === 'undefined') {
  global.clearImmediate = (id) => clearTimeout(id);
}

// Mock de Expo runtime que causa problemas en CI
jest.mock('expo/src/winter/runtime.native', () => ({}), { virtual: true });

// Configuración global de Jest
jest.setTimeout(10000); // 10 segundos como máximo por test

// Mock de expo-constants - DEBE IR PRIMERO
jest.mock('expo-constants', () => ({
  __esModule: true,
  default: {
    expoConfig: {
      extra: {
        // Variables como las usa App.tsx (sin prefijo EXPO_PUBLIC_)
        graphqlEndpoint: 'https://test.graphql.endpoint',
        userPoolId: 'test-user-pool',
        userPoolClientId: 'test-client-id',
        env: 'test',
        // También las originales con prefijo EXPO_PUBLIC_
        EXPO_PUBLIC_GRAPHQL_ENDPOINT: 'https://test.graphql.endpoint',
        EXPO_PUBLIC_API_KEY: 'test-api-key',
        EXPO_PUBLIC_USER_POOL_ID: 'test-user-pool',
        EXPO_PUBLIC_USER_POOL_CLIENT_ID: 'test-client-id',
        EXPO_PUBLIC_IDENTITY_POOL_ID: 'test-identity-pool',
        EXPO_PUBLIC_AWS_REGION: 'us-east-1'
      }
    }
  }
}));

// Polyfills para AWS Amplify
global.TextEncoder = require('util').TextEncoder;
global.TextDecoder = require('util').TextDecoder;
global.crypto = {
  getRandomValues: (arr) => require('crypto').randomBytes(arr.length)
};

// Mock del polyfill.js
jest.mock('./polyfill.js', () => ({}));

// Mock de aws-exports
jest.mock('./aws-exports', () => ({
  default: {
    aws_project_region: 'us-east-1',
    aws_appsync_graphqlEndpoint: 'https://test.appsync.endpoint',
    aws_appsync_region: 'us-east-1',
    aws_appsync_authenticationType: 'AMAZON_COGNITO_USER_POOLS',
    aws_cognito_identity_pool_id: 'test-identity-pool',
    aws_cognito_region: 'us-east-1',
    aws_user_pools_id: 'test-user-pool',
    aws_user_pools_web_client_id: 'test-client-id'
  }
}), { virtual: true });

// Mock de AWS Amplify - CORREGIDO para default export
const mockConfigure = jest.fn();
const mockGetCurrentUser = jest.fn(() => Promise.reject(new Error('No user')));
const mockSignIn = jest.fn(() => Promise.resolve({ userId: 'test-user' }));
const mockSignOut = jest.fn(() => Promise.resolve());

jest.mock('aws-amplify', () => {
  const actual = jest.requireActual('aws-amplify');
  return {
    ...actual,
    __esModule: true,
    // Default export - Amplify
    default: {
      configure: mockConfigure
    },
    // Named export - Amplify (para compatibilidad)
    Amplify: {
      configure: mockConfigure
    }
  };
});

jest.mock('aws-amplify/auth', () => ({
  getCurrentUser: mockGetCurrentUser,
  signIn: mockSignIn,
  signOut: mockSignOut,
  signUp: jest.fn(),
  confirmSignUp: jest.fn(),
  fetchAuthSession: jest.fn(() => Promise.resolve({ tokens: {} }))
}));

jest.mock('aws-amplify/api', () => ({
  generateClient: jest.fn(() => ({
    graphql: jest.fn(() => Promise.resolve({ data: {} }))
  }))
}));

// Exportar los mocks para usar en tests
global.mockAmplifyFunctions = {
  configure: mockConfigure,
  getCurrentUser: mockGetCurrentUser,
  signIn: mockSignIn,
  signOut: mockSignOut
};

// Mock de console.error y console.warn
beforeEach(() => {
  jest.spyOn(console, 'error').mockImplementation(() => { });
  jest.spyOn(console, 'warn').mockImplementation(() => { });
});

afterEach(() => {
  jest.restoreAllMocks();      // ✅ restaura todos los spyOn automáticamente
  jest.clearAllTimers();       // ✅ limpia timers
});
