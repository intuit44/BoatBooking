// Configuración específica para web de AWS Amplify
import { graphqlClient } from '../services/AmplifyService';

// Función para configurar Amplify para web
export function configureAmplifyForWeb() {
  console.log('ℹ️ Amplify ya se configura en AmplifyService');
  return true;
}

// Exportar cliente para web
export function getWebClient() {
  return graphqlClient;
}