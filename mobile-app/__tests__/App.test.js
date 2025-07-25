// mobile-app/__tests__/App.test.js

import { act, render, waitFor } from '@testing-library/react-native';
import Constants from 'expo-constants';
import App from '../App';

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers('legacy');
    // Mockear console para evitar ruido en los tests
    jest.spyOn(console, 'log').mockImplementation(() => { });
    jest.spyOn(console, 'error').mockImplementation(() => { });
  });

  afterEach(() => {
    // Restaurar todos los mocks de forma segura
    jest.restoreAllMocks();
    // Limpiar timers
    jest.clearAllTimers();
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('renders without crashing', () => {
    const { toJSON } = render(<App />);
    expect(toJSON()).toBeTruthy();
  });

  it('shows loading state initially', () => {
    const { getByText } = render(<App />);

    // Verificar que muestra el texto de carga
    expect(getByText('Configuring Amplify SDK 53...')).toBeTruthy();

    // Verificar que se llamó el log de montaje
    expect(console.log).toHaveBeenCalledWith('🔍 [App] App component mounted - SDK 53');
  });

  it('transitions from loading to ready state', async () => {
    const { queryByText, getByText } = render(<App />);

    // Verificar estado inicial
    expect(queryByText('Configuring Amplify SDK 53...')).toBeTruthy();

    // Avanza el tiempo simulado
    await act(async () => {
      jest.advanceTimersByTime(1000);
      // Espera a que todos los microtasks se resuelvan
      await Promise.resolve();
    });

    // Espera a que desaparezca el texto de carga
    await waitFor(() => {
      expect(queryByText('Configuring Amplify SDK 53...')).toBeNull();
      expect(getByText('🚤 Boat Rental v6')).toBeTruthy();
    }, { timeout: 3000, interval: 50 });

    // Verificar que no hay errores de configuración
    expect(queryByText('Configuration Error')).toBeNull();

    // Verificar que se llamó el log de éxito
    expect(console.log).toHaveBeenCalledWith('✅ [App] Configuration successful');
  });

  it('verifies configuration on mount', () => {
    render(<App />);

    expect(console.log).toHaveBeenCalledWith(
      '🔍 [App] Config verification:',
      expect.objectContaining({
        hasGraphqlEndpoint: true,
        hasUserPoolId: true,
        hasUserPoolClientId: true,
        environment: 'test'
      })
    );
  });

  it('handles missing all environment variables', () => {
    // Cambiar el mock temporalmente
    const originalExtra = Constants.expoConfig.extra;
    Constants.expoConfig.extra = {};

    const { getByText } = render(<App />);

    // Verificar que muestra error
    expect(getByText('Configuration Error')).toBeTruthy();
    expect(getByText('Missing variables: graphqlEndpoint, userPoolId, userPoolClientId')).toBeTruthy();
    expect(getByText('Check your .env file and ensure all EXPO_PUBLIC_ variables are set')).toBeTruthy();

    // Verificar log de error
    expect(console.error).toHaveBeenCalledWith(
      '❌ [App] Configuration error:',
      'Missing variables: graphqlEndpoint, userPoolId, userPoolClientId'
    );

    // Restaurar
    Constants.expoConfig.extra = originalExtra;
  });

  it('validates specific missing environment variable', () => {
    const originalExtra = Constants.expoConfig.extra;
    Constants.expoConfig.extra = {
      graphqlEndpoint: 'test',
      userPoolId: 'test',
      // userPoolClientId faltante
    };

    const { getByText } = render(<App />);

    expect(getByText('Configuration Error')).toBeTruthy();
    expect(getByText('Missing variables: userPoolClientId')).toBeTruthy();

    Constants.expoConfig.extra = originalExtra;
  });

  it('renders navigation structure after successful configuration', async () => {
    const { queryByText, getByText } = render(<App />);

    // Avanza el tiempo simulado
    await act(async () => {
      jest.advanceTimersByTime(1000);
      // Espera a que todos los microtasks se resuelvan
      await Promise.resolve();
    });

    // Espera a que la UI actualice y aparezca la pantalla principal
    await waitFor(() => {
      expect(queryByText('Configuring Amplify SDK 53...')).toBeNull();
      expect(queryByText('Configuration Error')).toBeNull();
      expect(getByText('🚤 Boat Rental v6')).toBeTruthy();
    }, { timeout: 3000, interval: 50 });

    expect(console.log).toHaveBeenCalledWith('✅ [App] Configuration successful');
    expect(getByText('🚤 Boat Rental v6')).toBeTruthy();
  });

  it('maintains configuration state during render', async () => {
    const { rerender, queryByText, getByText } = render(<App />);

    // Avanza el tiempo simulado y espera a que la UI actualice
    await act(async () => {
      jest.advanceTimersByTime(1000);
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(queryByText('Configuring Amplify SDK 53...')).toBeNull();
      expect(getByText('🚤 Boat Rental v6')).toBeTruthy();
    }, { timeout: 3000, interval: 50 });

    // Re-renderizar el componente
    rerender(<App />);

    // El estado de configuración debe persistir
    expect(queryByText('Configuring Amplify SDK 53...')).toBeNull();
    expect(queryByText('Configuration Error')).toBeNull();
    expect(getByText('🚤 Boat Rental v6')).toBeTruthy();
  });
});

describe('App Configuration', () => {
  it('has access to environment variables through expo-constants', () => {
    const extra = Constants.expoConfig.extra;

    // Verificar variables con prefijo EXPO_PUBLIC_
    expect(extra.EXPO_PUBLIC_GRAPHQL_ENDPOINT).toBe('https://test.graphql.endpoint');
    expect(extra.EXPO_PUBLIC_USER_POOL_ID).toBe('test-user-pool');
    expect(extra.EXPO_PUBLIC_AWS_REGION).toBe('us-east-1');

    // Verificar variables sin prefijo (como las usa App.tsx)
    expect(extra.graphqlEndpoint).toBe('https://test.graphql.endpoint');
    expect(extra.userPoolId).toBe('test-user-pool');
    expect(extra.userPoolClientId).toBe('test-client-id');
  });

  it('exports a valid React component', () => {
    expect(App).toBeDefined();
    expect(typeof App).toBe('function');
  });
});