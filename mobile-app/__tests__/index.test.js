// mobile-app/__tests__/index.test.js

// Mock de react-native-url-polyfill ANTES de cualquier require
jest.mock('react-native-url-polyfill/auto', () => { });

// Mock de aws-amplify
jest.mock('aws-amplify', () => ({
  Amplify: {
    configure: jest.fn()
  }
}));

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
  const React = require('react');
  return function MockedApp() {
    return React.createElement('View', null, 'Mocked App');
  };
});

describe('index.js', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Resetear módulos para asegurar un estado limpio
    jest.resetModules();
  });

  test('configura Amplify correctamente', () => {
    // Ejecutar el archivo index.js
    require('../index');

    const { Amplify } = require('aws-amplify');

    // Verificar que Amplify.configure fue llamado
    expect(Amplify.configure).toHaveBeenCalledTimes(1);
    expect(Amplify.configure).toHaveBeenCalledWith(
      expect.objectContaining({
        aws_project_region: 'us-east-1',
        aws_appsync_graphqlEndpoint: 'https://test.appsync.endpoint'
      })
    );
  });

  test('registra el componente App', () => {
    // Ejecutar el archivo index.js
    require('../index');

    const expo = require('expo');

    // Verificar que se registró el componente
    expect(expo.registerRootComponent).toHaveBeenCalledTimes(1);
    expect(expo.registerRootComponent).toHaveBeenCalledWith(expect.any(Function));
  });
});