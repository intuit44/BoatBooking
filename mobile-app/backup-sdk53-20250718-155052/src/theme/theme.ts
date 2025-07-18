import { MD3LightTheme } from 'react-native-paper';

export const theme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: '#0066CC',
    primaryContainer: '#E3F2FD',
    secondary: '#FF9800',
    secondaryContainer: '#FFE0B2',
    surface: '#FFFFFF',
    surfaceVariant: '#F5F5F5',
    background: '#F8F9FA',
    error: '#F44336',
    errorContainer: '#FFEBEE',
    onPrimary: '#FFFFFF',
    onSecondary: '#000000',
    onSurface: '#000000',
    onBackground: '#000000',
    outline: '#E0E0E0',
    // Agregar niveles de elevación que faltan
    elevation: {
      level0: 'transparent',
      level1: '#F5F5F5',
      level2: '#EEEEEE',
      level3: '#E0E0E0',
      level4: '#BDBDBD',
      level5: '#9E9E9E',
    },
  },
  roundness: 12,
};