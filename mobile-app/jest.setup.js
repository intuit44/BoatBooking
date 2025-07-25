// mobile-app/jest.setup.js

// Polyfills para setImmediate y clearImmediate
if (typeof global.setImmediate === 'undefined') {
  global.setImmediate = (cb) => setTimeout(cb, 0);
}
if (typeof global.clearImmediate === 'undefined') {
  global.clearImmediate = (id) => clearTimeout(id);
}

// Mock de módulos problemáticos de Expo ANTES de cualquier require
jest.mock('expo/src/winter/runtime.native', () => ({}), { virtual: true });
jest.mock('expo/src/winter/index', () => ({}), { virtual: true });

// Mock del preset de jest-expo que causa problemas
jest.mock('jest-expo/src/preset/setup.js', () => ({}), { virtual: true });

// Configuración global de Jest
jest.setTimeout(10000); // 10 segundos como máximo por test

// Mock de React Navigation
jest.mock('@react-navigation/native', () => {
  const React = require('react');
  return {
    NavigationContainer: ({ children }) => children,
    useNavigation: () => ({
      navigate: jest.fn(),
      goBack: jest.fn(),
    }),
    useRoute: () => ({
      params: {},
    }),
    useFocusEffect: jest.fn(),
    useIsFocused: () => true,
  };
});

jest.mock('@react-navigation/native-stack', () => {
  const React = require('react');
  return {
    createNativeStackNavigator: () => ({
      Navigator: ({ children }) => children,
      Screen: ({ component: Component, ...props }) => Component ? React.createElement(Component, props) : null,
    }),
  };
});

jest.mock('react-native-safe-area-context', () => {
  const React = require('react');
  return {
    SafeAreaProvider: ({ children }) => React.createElement('View', null, children),
    SafeAreaView: ({ children }) => React.createElement('View', null, children),
    useSafeAreaInsets: () => ({ top: 0, right: 0, bottom: 0, left: 0 }),
  };
});

jest.mock('react-native-screens', () => ({
  enableScreens: jest.fn(),
}));

jest.mock('react-native-gesture-handler', () => {
  const View = require('react-native').View;
  return {
    Swipeable: View,
    DrawerLayout: View,
    State: {},
    ScrollView: View,
    Slider: View,
    Switch: View,
    TextInput: View,
    ToolbarAndroid: View,
    ViewPagerAndroid: View,
    DrawerLayoutAndroid: View,
    WebView: View,
    NativeViewGestureHandler: View,
    TapGestureHandler: View,
    FlingGestureHandler: View,
    ForceTouchGestureHandler: View,
    LongPressGestureHandler: View,
    PanGestureHandler: View,
    PinchGestureHandler: View,
    RotationGestureHandler: View,
    RawButton: View,
    BaseButton: View,
    RectButton: View,
    BorderlessButton: View,
    FlatList: View,
    gestureHandlerRootHOC: (component) => component,
    Directions: {},
  };
});

jest.mock('react-native-reanimated', () => {
  const Reanimated = require('react-native-reanimated/mock');
  Reanimated.default.call = () => { };
  return Reanimated;
});

// Mock de expo-status-bar
jest.mock('expo-status-bar', () => ({
  StatusBar: () => null,
}));

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
jest.mock('./polyfill.js', () => ({}), { virtual: true });

// Mock de aws-exports
jest.mock('./aws-exports', () => ({
  __esModule: true,
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
const originalError = console.error;
const originalWarn = console.warn;

beforeEach(() => {
  // Solo mockear si no están haciendo referencia a errores reales de test
  jest.spyOn(console, 'error').mockImplementation((...args) => {
    // Permitir que errores de Jest pasen
    if (args.some(arg => typeof arg === 'string' && arg.includes('Warning:'))) {
      return;
    }
    originalError(...args);
  });
  jest.spyOn(console, 'warn').mockImplementation(() => { });
});

afterEach(() => {
  jest.restoreAllMocks();
  jest.clearAllTimers();
});