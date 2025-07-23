import type { ResourcesConfig } from 'aws-amplify';
import { Amplify } from 'aws-amplify';
import Constants from 'expo-constants';

// ✅ Acceso correcto a variables de entorno en Expo
const extra = Constants.expoConfig?.extra || {};

console.log('🔍 Expo Config Extra:', extra);
console.log('🔍 Environment Variables Available:', {
  graphqlEndpoint: extra.graphqlEndpoint,
  userPoolId: extra.userPoolId,
  region: extra.awsRegion,
});

// ✅ Configuración con estructura correcta de Amplify v6
const amplifyConfig: ResourcesConfig = {
  Auth: {
    Cognito: {
      // ✅ User Pool Configuration
      userPoolId: extra.userPoolId || 'us-east-1_XXXXXXX',
      userPoolClientId: extra.userPoolClientId || 'XXXXXXXXXXXXXXXXXXXXXXXXXX',

      // ✅ Identity Pool Configuration (separada)
      ...(extra.identityPoolId && {
        identityPoolId: extra.identityPoolId,
      }),

      // ✅ Login Configuration
      loginWith: {
        email: true,
        username: false,
        // ✅ OAuth opcional - solo si necesitas
        ...(extra.oauthDomain && {
          oauth: {
            domain: extra.oauthDomain || 'your-domain.auth.us-east-1.amazoncognito.com',
            scopes: ['openid', 'email', 'profile'],
            redirectSignIn: ['boat-rental-app://'],
            redirectSignOut: ['boat-rental-app://'],
            responseType: 'code' as const,
          },
        }),
      },

      // ✅ Verification Method
      signUpVerificationMethod: 'code' as const,
    },
  },

  // ✅ API Configuration con región en el nivel correcto
  API: {
    GraphQL: {
      endpoint: extra.graphqlEndpoint || 'https://your-api.amazonaws.com/graphql',
      region: extra.awsRegion || 'us-east-1', // ✅ Región aquí está bien
      defaultAuthMode: 'userPool' as const,
      ...(extra.apiKey && { apiKey: extra.apiKey }),
    },
  },

  // ✅ Storage Configuration con región en el nivel correcto
  ...(extra.s3Bucket && {
    Storage: {
      S3: {
        bucket: extra.s3Bucket,
        region: extra.awsRegion || 'us-east-1', // ✅ Región aquí está bien
      },
    },
  }),
};

// ✅ Validación de configuración
const requiredVars = ['graphqlEndpoint', 'userPoolId', 'userPoolClientId'];
const missingVars = requiredVars.filter((varName) => !extra[varName]);

if (missingVars.length > 0) {
  console.error('❌ Missing required environment variables:', missingVars);
  console.error('❌ Make sure your .env file contains all EXPO_PUBLIC_ variables');
  console.error('❌ Available variables:', Object.keys(extra));
} else {
  console.log('✅ All required environment variables are present');
}

// ✅ Configurar Amplify con validación de tipo
try {
  Amplify.configure(amplifyConfig);
  console.log('✅ Amplify configured successfully');
} catch (error) {
  console.error('❌ Error configuring Amplify:', error);
}

export default amplifyConfig;
