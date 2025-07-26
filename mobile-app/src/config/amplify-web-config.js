// Configuración específica para web de AWS Amplify
import awsExportsWeb from '../aws-exports';
import { configureAmplify } from '../../amplify-config';

// Función para configurar Amplify para web
export function configureAmplifyForWeb(config = awsExportsWeb) {
  try {
    return configureAmplify(config);
  } catch (error) {
    console.error('❌ Error configurando AWS Amplify para web:', error);
    return false;
  }
}

// Exportar cliente para web
export function getWebClient() {
  try {
    const { generateClient } = require('aws-amplify/api');
    return generateClient();
  } catch (error) {
    console.error('❌ Error generando cliente para web:', error);
    return null;
  }
}
