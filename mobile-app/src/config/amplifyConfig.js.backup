// src/config/amplifyConfig.js - Configuración para React Native Bare
import { Amplify } from 'aws-amplify';

// Configuración básica de Amplify para React Native
const amplifyConfig = {
  Auth: {
    region: 'us-east-1', // Tu región AWS
    userPoolId: 'us-east-1_XXXXXXXXX', // Tu User Pool ID
    userPoolWebClientId: 'xxxxxxxxxxxxxxxxxxxxxxxxxx', // Tu App Client ID
  },
  API: {
    endpoints: [
      {
        name: "boatRentalAPI",
        endpoint: "https://your-api-gateway-url.execute-api.region.amazonaws.com/dev",
        region: 'us-east-1',
        custom_header: async () => {
          // Headers personalizados si es necesario
          return {};
        }
      }
    ]
  }
};

// Función para configurar Amplify de forma segura
export const configureAmplify = () => {
  try {
    Amplify.configure(amplifyConfig);
    console.log('✅ AWS Amplify configurado correctamente para React Native');
    return true;
  } catch (error) {
    console.error('❌ Error configurando AWS Amplify:', error);
    return false;
  }
};

export default amplifyConfig;
