import { generateClient } from 'aws-amplify/api';

const client = generateClient();

// ✅ Wrapper con logging para todas las llamadas GraphQL
export async function graphqlWithLogging(query: any, variables?: any) {
  console.log('🔍 GraphQL Query:', query);
  console.log('🔍 GraphQL Variables:', variables);
  console.log('🔍 API Endpoint:', process.env.EXPO_PUBLIC_GRAPHQL_ENDPOINT);
  
  try {
    const response = await client.graphql({
      query: query,
      variables: variables
    });
    
    console.log('✅ GraphQL Response:', response);
    return response;
  } catch (error) {
    console.error('❌ GraphQL Error:', error);
    console.error('❌ Error details:', JSON.stringify(error, null, 2));
    throw error;
  }
}