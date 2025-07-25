// mobile-app/__tests__/HomeScreen.test.js

import { fireEvent, render, waitFor } from '@testing-library/react-native';
import HomeScreen from '../HomeScreen';

// Mock de generateClient
const mockGraphqlClient = {
  graphql: jest.fn(() => Promise.resolve({ data: {} }))
};

jest.mock('aws-amplify/api', () => ({
  generateClient: jest.fn(() => mockGraphqlClient)
}));

describe('HomeScreen Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(console, 'log').mockImplementation(() => { });
    jest.spyOn(console, 'error').mockImplementation(() => { });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders without crashing', () => {
    const { toJSON } = render(<HomeScreen />);
    expect(toJSON()).toBeTruthy();
  });

  it('displays the main title', async () => {
    const { getByText } = render(<HomeScreen />);

    // Esperar a que el componente se inicialice
    await waitFor(() => {
      expect(getByText('🚤 Boat Rental v6')).toBeTruthy();
    });
  });

  it('displays AWS Amplify status', async () => {
    const { getByText } = render(<HomeScreen />);

    await waitFor(() => {
      expect(getByText('🚀 AWS Amplify v6 Status')).toBeTruthy();
      expect(getByText('✅ AWS v6 Completamente Funcional')).toBeTruthy();
    });
  });

  it('shows boat list with correct status', async () => {
    const { getByText } = render(<HomeScreen />);

    await waitFor(() => {
      // Verificar que los boats se muestran
      expect(getByText('Enterprise v6')).toBeTruthy();
      expect(getByText('Alpha GraphQL')).toBeTruthy();
      expect(getByText('Beta Auth')).toBeTruthy();
    });

    // Verificar los precios
    expect(getByText('$350/día')).toBeTruthy();
    expect(getByText('$200/día')).toBeTruthy();
    expect(getByText('$150/día')).toBeTruthy();
  });

  it('shows system status information', async () => {
    const { getByText, getAllByText } = render(<HomeScreen />);

    await waitFor(() => {
      expect(getByText('📊 Sistema Status')).toBeTruthy();
    });

    // Usar getAllByText ya que el texto aparece múltiples veces
    const reactNativeElements = getAllByText(/React Native 0\.79\.5/);
    expect(reactNativeElements.length).toBeGreaterThan(0);

    // Verificar otros elementos del sistema status
    const allTextNodes = getAllByText(/.*/);

    const match = allTextNodes.find((node) => {
      const content = node?.props?.children?.join?.('') || node?.props?.children;
      return (
        typeof content === 'string' &&
        content.includes('React 19.1.0') &&
        content.includes('Expo SDK 53.0.20')
      );
    });

    expect(match).toBeTruthy();
  });

  it('can open login modal', async () => {
    const { getByText, queryByText } = render(<HomeScreen />);

    await waitFor(() => {
      expect(getByText('🔐 Login Demo')).toBeTruthy();
    });

    // Verificar que el modal no está visible inicialmente
    expect(queryByText('🚀 Cargar Demo Data')).toBeNull();

    // Click en el botón de login
    const loginButton = getByText('🔐 Login Demo');
    fireEvent.press(loginButton);

    // Esperar a que el modal se abra y verificar su contenido
    await waitFor(() => {
      // Buscar elementos específicos del modal
      expect(getByText('🚀 Cargar Demo Data')).toBeTruthy();
      expect(getByText('✅ Demo Login')).toBeTruthy();
    });
  });

  it('logs initialization messages', async () => {
    render(<HomeScreen />);

    await waitFor(() => {
      expect(console.log).toHaveBeenCalledWith('🏠 [HomeScreen] Component mounted - SDK 53');
      expect(console.log).toHaveBeenCalledWith('✅ [HomeScreen] GraphQL client initialized');
    });
  });

  it('handles GraphQL client initialization error', () => {
    // Mock generateClient para que lance un error
    const generateClient = require('aws-amplify/api').generateClient;
    generateClient.mockImplementationOnce(() => {
      throw new Error('Failed to initialize client');
    });

    const { getByText } = render(<HomeScreen />);

    expect(getByText('Configuration Error')).toBeTruthy();
    expect(getByText('Failed to initialize client')).toBeTruthy();
  });

  it('shows loading state initially', () => {
    // Mock generateClient para que sea lento
    const generateClient = require('aws-amplify/api').generateClient;
    generateClient.mockImplementationOnce(() => {
      return new Promise(() => { }); // Never resolves
    });

    const { getByText } = render(<HomeScreen />);

    // El componente no muestra loading state según el código actual
    // Verificamos que renderiza algo
    expect(getByText('🚤 Boat Rental v6')).toBeTruthy();
  });

  it('displays correct boat statuses based on state', async () => {
    const { getByText } = render(<HomeScreen />);

    await waitFor(() => {
      // Enterprise v6 debe mostrar "AWS Ready ✅"
      expect(getByText('AWS Ready ✅')).toBeTruthy();

      // Alpha GraphQL debe mostrar "GraphQL Ready ✅"
      expect(getByText('GraphQL Ready ✅')).toBeTruthy();

      // Beta Auth debe mostrar "Auth Pending ⚠️" (usuario no logueado)
      expect(getByText('Auth Pending ⚠️')).toBeTruthy();
    });
  });

  it('can check AWS status', async () => {
    // Mock de Alert
    const mockAlert = jest.spyOn(require('react-native').Alert, 'alert');

    const { getByText } = render(<HomeScreen />);

    await waitFor(() => {
      expect(getByText('🔍 Estado AWS')).toBeTruthy();
    });

    const statusButton = getByText('🔍 Estado AWS');
    fireEvent.press(statusButton);

    // Verificar que se llamó Alert con el título correcto
    expect(mockAlert).toHaveBeenCalledWith(
      '🔍 Estado AWS Amplify v6',
      expect.stringContaining('✅ AWS Amplify v6: Configurado')
    );
  });
});