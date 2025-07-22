import { ResourcesConfig } from 'aws-amplify';

const amplifyConfig: ResourcesConfig = {
  Auth: {
    Cognito: {
      // ✅ User Pool (usuarios registrados)
      userPoolId: process.env.EXPO_PUBLIC_USER_POOL_ID || 'us-east-1_XXXXXXX',
      userPoolClientId: process.env.EXPO_PUBLIC_USER_POOL_CLIENT_ID || 'XXXXXXXXXXXXXXXXXXXXXXXXX',
      
      // ✅ Identity Pool (requerido para allowGuestAccess)
      identityPoolId: process.env.EXPO_PUBLIC_IDENTITY_POOL_ID || 'us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
      
      loginWith: {
        email: true,
        phone: false, // O true si quieres login por teléfono
        username: false,
      },
      signUpVerificationMethod: 'code',
      userAttributes: {
        email: {
          required: true,
        },
        // ✅ Agregar phone_number como atributo opcional
        phone_number: {
          required: false,
        },
        name: {
          required: false,
        },
      },
      allowGuestAccess: true, // Requiere identityPoolId
      passwordFormat: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireNumbers: true,
        requireSpecialCharacters: false,
      },
    },
  },
  API: {
    GraphQL: {
      endpoint: process.env.EXPO_PUBLIC_GRAPHQL_ENDPOINT ||
        'https://your-api-id.appsync-api.us-east-1.amazonaws.com/graphql',
      region: process.env.EXPO_PUBLIC_AWS_REGION || 'us-east-1',
      defaultAuthMode: 'userPool',
      apiKey: process.env.EXPO_PUBLIC_API_KEY || '',
    },
  },
  Storage: {
    S3: {
      region: process.env.EXPO_PUBLIC_AWS_REGION || 'us-east-1',
      bucket: process.env.EXPO_PUBLIC_S3_BUCKET || 'your-bucket-name',
    },
  },
};

export default amplifyConfig;
