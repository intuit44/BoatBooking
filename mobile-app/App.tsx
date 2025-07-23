import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import Constants from 'expo-constants';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';

// ✅ Importar configuración de Amplify (ya se hace en index.js)
// import './src/config/amplifyConfig'; // Ya se importa en index.js

// Importar pantallas
import HomeScreen from './src/screens/home/HomeScreen';


const Stack = createNativeStackNavigator();

export default function App() {
  const [configStatus, setConfigStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    console.log('🔍 [App] App component mounted - SDK 53');
    
    // ✅ Verificar que las variables de entorno se cargaron
    const extra = Constants.expoConfig?.extra || {};
    
    console.log('🔍 [App] Config verification:', {
      hasGraphqlEndpoint: !!extra.graphqlEndpoint,
      hasUserPoolId: !!extra.userPoolId,
      hasUserPoolClientId: !!extra.userPoolClientId,
      environment: extra.env,
    });

    // Validar variables críticas
    const requiredVars = ['graphqlEndpoint', 'userPoolId', 'userPoolClientId'];
    const missingVars = requiredVars.filter(varName => !extra[varName]);

    if (missingVars.length > 0) {
      const errorMsg = `Missing variables: ${missingVars.join(', ')}`;
      console.error('❌ [App] Configuration error:', errorMsg);
      setErrorMessage(errorMsg);
      setConfigStatus('error');
      return;
    }

    // Dar tiempo para que Amplify se configure completamente
    setTimeout(() => {
      console.log('✅ [App] Configuration successful');
      setConfigStatus('success');
    }, 1000);

  }, []);

  if (configStatus === 'error') {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 }}>
        <Text style={{ color: 'red', textAlign: 'center', marginBottom: 10, fontSize: 18 }}>
          Configuration Error
        </Text>
        <Text style={{ textAlign: 'center', marginBottom: 20 }}>
          {errorMessage}
        </Text>
        <Text style={{ textAlign: 'center', color: 'gray' }}>
          Check your .env file and ensure all EXPO_PUBLIC_ variables are set
        </Text>
      </View>
    );
  }

  if (configStatus === 'loading') {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#0066cc" />
        <Text style={{ marginTop: 10 }}>Configuring Amplify SDK 53...</Text>
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Home">
        <Stack.Screen 
          name="Home" 
          component={HomeScreen}
          options={{ title: 'Boat Rental App' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}