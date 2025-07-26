// Configuración específica para web de AWS Amplify
import { Amplify } from 'aws-amplify';
import awsExportsWeb from '../aws-exports';

// Función para configurar Amplify para web
export function configureAmplifyForWeb() {
  try {
    Amplify.configure(awsExportsWeb);
    console.log('✅ AWS Amplify configurado para web exitosamente');
    return true;
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
