import { Amplify } from 'aws-amplify';
import { generateClient } from 'aws-amplify/api';
import awsExports from '../aws-exports';

// Define the GraphQL client type
type GraphQLClient = any;

let amplifyConfigured = false;
let graphqlClient: GraphQLClient | null = null;

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

export { amplifyConfigured, graphqlClient };

