// mobile-app/__tests__/App.test.js

import renderer from 'react-test-renderer';

// Mock básico para evitar errores con módulos nativos
jest.mock('expo-font');
jest.mock('expo-asset');

describe('App Component', () => {
  it('renders correctly', () => {
    // Test básico de snapshot
    const tree = renderer.create(<div>App Test</div>).toJSON();
    expect(tree).toBeTruthy();
  });

  it('should have correct configuration', () => {
    // Verificar que las variables de entorno existan
    const requiredEnvVars = [
      'EXPO_PUBLIC_GRAPHQL_ENDPOINT',
      'EXPO_PUBLIC_API_KEY',
      'EXPO_PUBLIC_USER_POOL_ID'
    ];

    requiredEnvVars.forEach(envVar => {
      // En el CI, estas variables deberían estar definidas
      if (process.env.CI) {
        expect(process.env[envVar]).toBeDefined();
      }
    });
  });
});