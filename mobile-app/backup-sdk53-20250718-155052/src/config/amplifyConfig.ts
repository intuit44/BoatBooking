import { Amplify } from 'aws-amplify';

// Intenta usar aws-exports.js si existe
try {
  const awsconfig = require('../aws-exports').default;
  Amplify.configure(awsconfig);
  console.log('✅ Amplify configurado con aws-exports.js');
} catch (error) {
  // Si no existe aws-exports.js, usa configuración manual
  console.log('⚠️ aws-exports.js no encontrado, usando configuración manual');
  
  const amplifyConfig = {
    Auth: {
      region: process.env.EXPO_PUBLIC_AWS_REGION || 'us-east-1',
      userPoolId: process.env.EXPO_PUBLIC_USER_POOL_ID || 'us-east-1_XXXXXXXXX',
      userPoolWebClientId: process.env.EXPO_PUBLIC_USER_POOL_CLIENT_ID || 'XXXXXXXXXXXXXXXXXXXXXXXXX',
      mandatorySignIn: false,
      authenticationFlowType: 'USER_PASSWORD_AUTH',
    },
    API: {
      endpoints: [
        {
          name: 'BoatRentalAPI',
          endpoint: process.env.EXPO_PUBLIC_API_ENDPOINT || 'http://localhost:3000',
          region: process.env.EXPO_PUBLIC_AWS_REGION || 'us-east-1'
        }
      ]
    }
  };
  
  Amplify.configure(amplifyConfig);
}

export default {};