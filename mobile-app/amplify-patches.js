// Polyfills obligatorios para Hermes
import 'react-native-url-polyfill/auto';
import 'react-native-get-random-values';

// Configuración global de Amplify
import { configureAmplify } from './amplify-config';
import awsconfig from './src/aws-exports';

configureAmplify(awsconfig);
