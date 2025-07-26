// amplify-config.js - Configuración moderna para AWS Amplify v5
import { Amplify } from 'aws-amplify';
import awsExports from './aws-exports';

// Configuración específica para Amplify v5
const amplifyConfig = {
  Auth: {
    Cognito: {
      userPoolId: awsExports.aws_user_pools_id,
      userPoolClientId: awsExports.aws_user_pools_web_client_id,
      identityPoolId: awsExports.aws_cognito_identity_pool_id,
      loginWith: {
        oauth: {
          domain: awsExports.oauth?.domain,
          scopes: awsExports.oauth?.scope || [],
          redirectSignIn: awsExports.oauth?.redirectSignIn?.split(',') || [],
          redirectSignOut: awsExports.oauth?.redirectSignOut?.split(',') || [],
          responseType: awsExports.oauth?.responseType || 'code',
        },
        username: true,
        email: awsExports.aws_cognito_username_attributes?.includes('EMAIL') || false,
      },
      signUpVerificationMethod: 'code',
      userAttributes: {
        email: {
          required: awsExports.aws_cognito_signup_attributes?.includes('EMAIL') || false,
        },
      },
      allowGuestAccess: true,
      passwordFormat: {
        minLength: awsExports.aws_cognito_password_protection_settings?.passwordPolicyMinLength || 8,
        requireLowercase: false,
        requireUppercase: false,
        requireNumbers: false,
        requireSpecialCharacters: false,
      },
    },
  },
  API: {
    GraphQL: {
      endpoint: awsExports.aws_appsync_graphqlEndpoint,
      region: awsExports.aws_appsync_region,
      defaultAuthMode: 'userPool',
      apiKey: awsExports.aws_appsync_apiKey,
    },
  },
  Analytics: {
    disabled: true,
  },
};

let amplifyConfigured = false;

export const configureAmplify = (config = amplifyConfig) => {
  try {
    console.log('🔧 [AmplifyConfig] Configurando Amplify...');
    console.log('🔗 [AmplifyConfig] Endpoint:', config?.API?.GraphQL?.endpoint);

    Amplify.configure({
      ...config,
      Analytics: { disabled: true, ...(config.Analytics || {}) },
    });
    amplifyConfigured = true;
    console.log('✅ [AmplifyConfig] Amplify configurado correctamente');

    return true;
  } catch (error) {
    console.log('❌ [AmplifyConfig] Error configurando Amplify:', error);
    amplifyConfigured = false;
    return false;
  }
};

export const isAmplifyConfigured = () => amplifyConfigured;

export default amplifyConfig;
