// mobile-app/__tests__/index.test.js

// Mock de react-native-url-polyfill ANTES de cualquier require
jest.mock('react-native-url-polyfill/auto', () => { });

// Mock de aws-amplify
jest.mock('aws-amplify', () => {
  return {
    Amplify: {
      configure: jest.fn()
    }
  };
});

// Mock de aws-exports
jest.mock('../aws-exports', () => ({
  aws_appsync_graphqlEndpoint: 'https://test-endpoint',
  aws_appsync_region: 'us-east-1',
  aws_appsync_authenticationType: 'AMAZON_COGNITO_USER_POOLS'
}), { virtual: true });

// Mock de Expo
jest.mock('expo', () => ({
  registerRootComponent: jest.fn()
}));

// Mock de React Native
jest.mock('react-native', () => ({
  AppRegistry: {
    registerComponent: jest.fn()
  }
}));

// Mock del App component para evitar su ejecución
jest.mock('../App', () => {
  return function MockedApp() {
    return null;
  };
});

describe('index.js', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('configura Amplify correctamente', () => {
    // Ejecutar el archivo index.js
    require('../index');

    const { Amplify } = require('aws-amplify');
    const config = require('../aws-exports');

    // Verificar que Amplify.configure fue llamado con la configuración correcta
    expect(Amplify.configure).toHaveBeenCalledWith(config);
    expect(Amplify.configure).toHaveBeenCalledTimes(1);
  });

  test('registra el componente App', () => {
    // El index.js ya fue ejecutado en el test anterior, pero lo ejecutamos de nuevo por claridad
    jest.resetModules();
    require('../index');

    const expo = require('expo');

    // Verificar que se registró el componente
    expect(expo.registerRootComponent).toHaveBeenCalled();
  });
});