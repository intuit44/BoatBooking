import { Amplify } from 'aws-amplify';
import { generateClient } from 'aws-amplify/api';
import awsExports from '../aws-exports';

let amplifyConfigured = false;
let graphqlClient: ReturnType<typeof generateClient> | null = null;

if (!amplifyConfigured) {
  try {
    Amplify.configure(awsExports);
    graphqlClient = generateClient();
    amplifyConfigured = true;
    console.log('✅ [AmplifyService] AWS Amplify configurado');
  } catch (error) {
    console.error('❌ [AmplifyService] Error configurando AWS Amplify:', error);
  }
}

export { graphqlClient, amplifyConfigured };
