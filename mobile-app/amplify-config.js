// amplify-config.js
import { Amplify } from 'aws-amplify';
import awsExports from './src/aws-exports';

// Configuración específica para React Native
const amplifyConfig = {
  ...awsExports,
  Analytics: {
    disabled: true, // Deshabilitamos Analytics por ahora
  },
};

console.log('🔧 Configurando Amplify...');
Amplify.configure(amplifyConfig);
console.log('✅ Amplify configurado correctamente');

export default amplifyConfig;
