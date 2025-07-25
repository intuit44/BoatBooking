// mobile-app/__tests__/App.test.js

import { act, render, waitFor } from '@testing-library/react-native';
import Constants from 'expo-constants';
import App from '../App';

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mockear console para evitar ruido en los tests
    jest.spyOn(console, 'log').mockImplementation(() => { });
    jest.spyOn(console, 'error').mockImplementation(() => { });
  });

  afterEach(() => {
    // Restaurar todos los mocks de forma segura
    jest.restoreAllMocks();
    jest.clearAllTimers();
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

  it('transitions to success state after configuration timeout', async () => {
    jest.useFakeTimers();

    const { queryByText, getByText } = render(<App />);

    // simula paso del tiempo
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    // fuerza ejecución de efectos colgados
    await Promise.resolve();

    // restaura timers REALES antes de usar waitFor
    jest.useRealTimers();

    await waitFor(() => {
      expect(queryByText('Configuring Amplify SDK 53...')).toBeNull();
      expect(getByText('🚤 Boat Rental v6')).toBeTruthy();
    });

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

  it('renders navigation container after successful configuration', async () => {
    const { queryByText, getByText } = render(<App />);

    await waitFor(() => {
      expect(queryByText('Configuring Amplify SDK 53...')).toBeNull();
      expect(queryByText('Configuration Error')).toBeNull();
      expect(getByText('🚤 Boat Rental v6')).toBeTruthy();
    }, { timeout: 3000, interval: 50 });
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