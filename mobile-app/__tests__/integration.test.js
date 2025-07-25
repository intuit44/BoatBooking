// mobile-app/__tests__/integration.test.js

import { act, render, waitFor } from '@testing-library/react-native';

// Mock de expo-constants para variables de entorno
jest.mock('expo-constants', () => ({
  expoConfig: {
    extra: {
      graphqlEndpoint: 'https://fake-endpoint',
      userPoolId: 'test-pool',
      userPoolClientId: 'test-client',
      awsRegion: 'us-east-1'
    }
  }
}));

import App from '../App';

// Mock mejorado para Stack.Screen que renderiza el componente
jest.mock('@react-navigation/native-stack', () => {
  const React = require('react');
  return {
    createNativeStackNavigator: () => ({
      Navigator: ({ children }) => children,
      Screen: ({ component: Component, ...props }) => {
        if (Component) {
          return React.createElement(Component, props);
        }
        return null;
      },
    }),
  };
});

describe('App Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers('legacy');
    jest.spyOn(console, 'log').mockImplementation(() => { });
    jest.spyOn(console, 'error').mockImplementation(() => { });
  });

  afterEach(() => {
    jest.restoreAllMocks();
    jest.clearAllTimers();
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('loads and displays HomeScreen content after configuration', async () => {
    const { queryByText, getByText, debug } = render(<App />);

    // Verificar estado inicial de carga
    expect(queryByText('Configuring Amplify SDK 53...')).toBeTruthy();

    // Avanzar el tiempo para completar la configuración
    await act(async () => {
      jest.advanceTimersByTime(1000);
      await Promise.resolve();
    });

    // Esperar a que el HomeScreen esté realmente renderizado
    let renderError = null;
    try {
      await waitFor(() => expect(getByText('🚤 Boat Rental v6')).toBeTruthy(), { timeout: 10000 });
    } catch (err) {
      renderError = err;
      debug(); // Imprime el árbol real si falla
    }
    if (renderError) throw renderError;

    // Verificar que desapareció el loading
    expect(queryByText('Configuring Amplify SDK 53...')).toBeNull();

    // Verificar otros elementos si están presentes
    if (queryByText('🚤 Boat Rental v6')) {
      expect(getByText('🚤 Boat Rental v6')).toBeTruthy();
      const enterpriseBoat = queryByText('Enterprise v6');
      if (enterpriseBoat) {
        expect(getByText('Alpha GraphQL')).toBeTruthy();
        expect(getByText('Beta Auth')).toBeTruthy();
      }
    }
  }, 20000);

  it('shows correct configuration flow', async () => {
    const { queryByText } = render(<App />);

    // 1. Estado inicial: cargando
    expect(queryByText('Configuring Amplify SDK 53...')).toBeTruthy();
    expect(console.log).toHaveBeenCalledWith('🔍 [App] App component mounted - SDK 53');

    // 2. Avanzar tiempo
    await act(async () => {
      jest.advanceTimersByTime(500);
    });

    // Todavía cargando
    expect(queryByText('Configuring Amplify SDK 53...')).toBeTruthy();

    // 3. Completar la configuración
    await act(async () => {
      jest.advanceTimersByTime(500);
      await Promise.resolve();
    });

    // 4. Verificar que la configuración se completó
    await waitFor(() => {
      expect(queryByText('Configuring Amplify SDK 53...')).toBeNull();
      expect(console.log).toHaveBeenCalledWith('✅ [App] Configuration successful');
    });
  });

  it('renders without configuration errors when environment is set', async () => {
    const { queryByText } = render(<App />);

    // Completar configuración
    await act(async () => {
      jest.advanceTimersByTime(1000);
      await Promise.resolve();
    });

    // No debe haber errores
    await waitFor(() => {
      expect(queryByText('Configuration Error')).toBeNull();
      expect(queryByText('Missing variables')).toBeNull();
    });
  });
});