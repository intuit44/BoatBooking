// mobile-app/__tests__/App.test.js

import { waitFor } from '@testing-library/react-native';
import Constants from 'expo-constants';
import renderer from 'react-test-renderer';
import App from '../App';

// Obtener los mocks
const { configure, getCurrentUser } = global.mockAmplifyFunctions;

describe('App Component', () => {
  beforeEach(() => {
    // Limpiar mocks antes de cada test
    jest.clearAllMocks();
    // Resetear el mock de console.log
    jest.spyOn(console, 'log').mockImplementation(() => { });
  });

  afterEach(() => {
    console.log.mockRestore();
  });

  it('renders without crashing', async () => {
    let component;

    await renderer.act(async () => {
      component = renderer.create(<App />);
    });

    await waitFor(() => {
      expect(component).toBeTruthy();
      expect(component.toJSON()).toBeTruthy();
    });
  }, 30000);

  it('logs app mounting with SDK 53', async () => {
    await renderer.act(async () => {
      renderer.create(<App />);
    });

    await waitFor(() => {
      expect(console.log).toHaveBeenCalledWith('🔍 [App] App component mounted - SDK 53');
    });
  }, 30000);

  it('verifies configuration on mount', async () => {
    await renderer.act(async () => {
      renderer.create(<App />);
    });

    await waitFor(() => {
      expect(console.log).toHaveBeenCalledWith(
        '🔍 [App] Config verification:',
        expect.objectContaining({
          hasGraphqlEndpoint: true,
          hasUserPoolId: true,
          hasUserPoolClientId: true
        })
      );
    });
  }, 30000);

  it('shows loading state initially', async () => {
    let component;

    await renderer.act(async () => {
      component = renderer.create(<App />);
    });

    // Verificar estado inicial de carga
    const tree = component.toJSON();

    // Buscar el ActivityIndicator y texto de carga
    const texts = tree.children.filter(child => child.type === 'Text');
    expect(texts.some(text =>
      text.children && text.children.includes('Configuring Amplify SDK 53...')
    )).toBeTruthy();
  }, 30000);

  it('transitions to success state after configuration', async () => {
    let component;

    await renderer.act(async () => {
      component = renderer.create(<App />);
    });

    // Esperar a que el componente transite al estado de éxito
    await waitFor(() => {
      expect(console.log).toHaveBeenCalledWith('✅ [App] Configuration successful');
    }, { timeout: 2000 });

    // Verificar que ahora muestra NavigationContainer
    const tree = component.toJSON();
    expect(tree).toBeTruthy();
  }, 30000);

  it('handles missing environment variables', async () => {
    // Temporalmente cambiar el mock para simular variables faltantes
    const originalExtra = Constants.expoConfig.extra;
    Constants.expoConfig.extra = {};

    let component;

    await renderer.act(async () => {
      component = renderer.create(<App />);
    });

    await waitFor(() => {
      expect(console.error).toHaveBeenCalledWith(
        '❌ [App] Configuration error:',
        expect.stringContaining('Missing variables')
      );
    });

    // Verificar que muestra la pantalla de error
    const tree = component.toJSON();
    const texts = tree.children.filter(child => child.type === 'Text');
    expect(texts.some(text =>
      text.children && text.children.includes('Configuration Error')
    )).toBeTruthy();

    // Restaurar el mock original
    Constants.expoConfig.extra = originalExtra;
  }, 30000);

  it('validates all required environment variables', async () => {
    // Test con una variable faltante
    const originalExtra = Constants.expoConfig.extra;
    Constants.expoConfig.extra = {
      graphqlEndpoint: 'test',
      userPoolId: 'test',
      // userPoolClientId faltante
    };

    await renderer.act(async () => {
      renderer.create(<App />);
    });

    await waitFor(() => {
      expect(console.error).toHaveBeenCalledWith(
        '❌ [App] Configuration error:',
        'Missing variables: userPoolClientId'
      );
    });

    // Restaurar
    Constants.expoConfig.extra = originalExtra;
  }, 30000);

  it('creates a valid component tree after successful configuration', async () => {
    let component;

    await renderer.act(async () => {
      component = renderer.create(<App />);
    });

    // Esperar a que complete la configuración y esté en estado estable
    await waitFor(() => {
      expect(console.log).toHaveBeenCalledWith('✅ [App] Configuration successful');
    }, { timeout: 2000 });

    // Ahora que está en estado estable, actualizar el componente para obtener el árbol final
    await renderer.act(async () => {
      component.update(<App />);
    });

    // Tomar el snapshot del estado final (después de la configuración)
    const tree = component.toJSON();

    // Verificar que ya no está en estado de carga
    expect(tree).toBeTruthy();
    expect(typeof tree).toBe('object');

    // Verificar que no hay ActivityIndicator (estado de carga)
    const hasActivityIndicator = JSON.stringify(tree).includes('ActivityIndicator');
    expect(hasActivityIndicator).toBe(false);

    // Ahora sí, guardar el snapshot del estado final
    expect(tree).toMatchSnapshot();
  }, 30000);
});

describe('App Configuration', () => {
  it('has access to environment variables through expo-constants', () => {
    const extra = Constants.expoConfig.extra;

    // Verificar que las variables mockeadas están disponibles
    expect(extra.EXPO_PUBLIC_GRAPHQL_ENDPOINT).toBe('https://test.graphql.endpoint');
    expect(extra.EXPO_PUBLIC_USER_POOL_ID).toBe('test-user-pool');
    expect(extra.EXPO_PUBLIC_AWS_REGION).toBe('us-east-1');
  });

  it('exports a valid React component', () => {
    expect(App).toBeDefined();
    expect(typeof App).toBe('function');
  });
});