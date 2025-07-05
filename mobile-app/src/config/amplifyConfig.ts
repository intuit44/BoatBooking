import { Amplify } from 'aws-amplify';
import awsconfig from '../aws-exports';

// Configuración específica para React Native
const amplifyConfig = {
  ...awsconfig,
  Analytics: {
    disabled: true,
  },
  Storage: {
    S3: {
      bucket: 'boatrentalstorage-dev',
      region: 'us-east-1',
    }
  },
  // Configuración específica para React Native
  ssr: false,
};

// Configurar Amplify para React Native
Amplify.configure(amplifyConfig);

console.log('✅ AWS Amplify configured for React Native');

export default amplifyConfig;