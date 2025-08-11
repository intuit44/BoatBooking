// aws-exports.d.ts - Tipos TypeScript robustos para aws-exports
declare module '*/aws-exports' {
  interface AWSConfig {
    // Core AWS settings
    aws_project_region: string;
    aws_cognito_identity_pool_id: string;
    aws_cognito_region: string;
    aws_user_pools_id: string;
    aws_user_pools_web_client_id: string;
    
    // OAuth configuration
    oauth: {
      domain: string;
      scope: string[];
      redirectSignIn: string;
      redirectSignOut: string;
      responseType: string;
    };
    
    // Federation and auth settings
    federationTarget: string;
    aws_cognito_username_attributes: string[];
    aws_cognito_social_providers: string[];
    aws_cognito_signup_attributes: string[];
    aws_cognito_mfa_configuration: string;
    aws_cognito_mfa_types: string[];
    aws_cognito_password_protection_settings: {
      passwordPolicyMinLength: number;
      passwordPolicyCharacters: string[];
    };
    aws_cognito_verification_mechanisms: string[];
    
    // AppSync GraphQL settings
    aws_appsync_graphqlEndpoint: string;
    aws_appsync_region: string;
    aws_appsync_authenticationType: string;
    aws_appsync_apiKey: string;
    
    // Amplify configuration structure for getConfig()
    API?: {
      GraphQL?: {
        endpoint?: string;
        region?: string;
        defaultAuthMode?: string;
        apiKey?: string;
      };
    };
    
    Auth?: {
      Cognito?: {
        userPoolId?: string;
        userPoolClientId?: string;
        region?: string;
        identityPoolId?: string;
      };
    };
  }
  
  const awsmobile: AWSConfig;
  export default awsmobile;
}

// Tipos adicionales para Amplify.getConfig()
declare global {
  namespace Amplify {
    interface Config {
      API?: {
        GraphQL?: {
          endpoint?: string;
          region?: string;
          defaultAuthMode?: string;
          apiKey?: string;
        };
      };
      Auth?: {
        Cognito?: {
          userPoolId?: string;
          userPoolClientId?: string;
          region?: string;
          identityPoolId?: string;
        };
      };
    }
  }
}
