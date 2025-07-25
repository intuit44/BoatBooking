// mobile-app/__tests__/App.simple.test.js

import { act, render, waitFor } from '@testing-library/react-native';

// Mock HomeScreen para verificar que se renderiza
jest.mock('../src/screens/home/HomeScreen', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: function MockHomeScreen() {
      return React.createElement('View', null,
        React.createElement('Text', null, 'Mock HomeScreen Rendered')
      );
    }
  };
});

// Importar App después de los mocks
const App = require('../App').default;

describe('App Simple Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers('legacy');
    jest.spyOn(console, 'log').mockImplementation(() => { });
    jest.spyOn(console, 'error').mockImplementation(() => { });
  });

  afterEach(() => {
    jest.restoreAllMocks();
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  it('renders HomeScreen after configuration', async () => {
    const { queryByText, getByText } = render(<App />);

    // Verificar estado inicial
    expect(queryByText('Configuring Amplify SDK 53...')).toBeTruthy();

    // Completar configuración
    await act(async () => {
      jest.advanceTimersByTime(1000);
      await Promise.resolve();
    });

    // Esperar a que la configuración termine
    await waitFor(() => {
      expect(queryByText('Configuring Amplify SDK 53...')).toBeNull();
    });

    // Verificar que HomeScreen se renderizó
    await waitFor(() => {
      expect(getByText('Mock HomeScreen Rendered')).toBeTruthy();
    });
  });
});