import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';

// IMPORTACIÓN AWS AMPLIFY V5 CORRECTA
import { Amplify } from 'aws-amplify';
import awsExports from '../../aws-exports';

// Variables globales para el estado
let amplifyConfigured = false;

// Configurar AWS Amplify v5 al inicio
try {
  console.log('🔧 [HomeScreen] Configurando AWS Amplify v5...');
  
  const amplifyConfig = {
    Auth: {
      Cognito: {
        userPoolId: awsExports.aws_user_pools_id,
        userPoolClientId: awsExports.aws_user_pools_web_client_id,
        identityPoolId: awsExports.aws_cognito_identity_pool_id,
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
  
  console.log('🔗 [HomeScreen] GraphQL Endpoint:', amplifyConfig.API.GraphQL.endpoint);
  
  Amplify.configure(amplifyConfig);
  amplifyConfigured = true;
  console.log('✅ [HomeScreen] AWS Amplify v5 configurado correctamente');
} catch (error) {
  console.log('❌ [HomeScreen] Error configurando AWS Amplify v5:', error);
  amplifyConfigured = false;
}

// Función para verificar AWS Amplify
const checkAWSAmplify = async () => {
  try {
    console.log('🔍 [HomeScreen] Verificando AWS Amplify v5...');
    
    const config = Amplify.getConfig();
    console.log('🔍 [HomeScreen] Configuración obtenida:', !!config);
    console.log('🔍 [HomeScreen] GraphQL endpoint:', config?.API?.GraphQL?.endpoint);
    
    Alert.alert(
      '🔍 Estado AWS Amplify v5',
      `Configurado: ${amplifyConfigured ? 'SÍ' : 'NO'}\nGraphQL Endpoint: ${config?.API?.GraphQL?.endpoint ? 'Disponible' : 'No disponible'}\nRegión: ${config?.API?.GraphQL?.region || 'No configurada'}`,
      [{ text: 'OK' }]
    );
  } catch (error) {
    console.log('❌ [HomeScreen] Error verificando AWS:', error);
    Alert.alert('❌ Error AWS', `Error: ${error.message}`);
  }
};

// Función para probar conexión AWS
const testAWSConnection = async () => {
  try {
    if (!amplifyConfigured) {
      Alert.alert('❌ Error', 'AWS Amplify v5 no está configurado');
      return;
    }

    const config = Amplify.getConfig();
    
    if (!config?.API?.GraphQL?.endpoint) {
      Alert.alert('❌ Error', 'No hay endpoint GraphQL configurado en AWS');
      return;
    }

    Alert.alert(
      '✅ AWS Amplify v5 OK', 
      `AWS Amplify v5 configurado correctamente!\n\nEndpoint: ${config.API.GraphQL.endpoint.substring(0, 50)}...\nRegión: ${config.API.GraphQL.region}\nAuth Mode: ${config.API.GraphQL.defaultAuthMode}\n\nNOTA: Para hacer queries reales instalar @aws-amplify/api-graphql`,
      [{ text: 'Perfecto!' }]
    );
  } catch (error) {
    console.log('❌ [HomeScreen] Error en test AWS:', error);
    Alert.alert('❌ Error AWS', `Error: ${error.message}`);
  }
};

// Función para próximos pasos
const showNextSteps = async () => {
  Alert.alert(
    '📋 Próximos Pasos AWS',
    '1. ✅ AWS Amplify v5 configurado\n2. ⏳ Instalar @aws-amplify/api-graphql\n3. ⏳ Implementar generateClient() para queries\n4. ⏳ Conectar con base de datos real\n5. ⏳ Implementar Auth (login/registro)\n\n¿Continuar con la instalación?',
    [
      { text: 'Más tarde', style: 'cancel' },
      { text: 'Instalar ahora', onPress: () => Alert.alert('💡 Comando', 'Ejecutar:\nnpm install @aws-amplify/api-graphql@5.3.21') }
    ]
  );
};

// Datos de prueba para mostrar funcionalidad
const testBoats = [
  { id: '1', name: 'Yacht Enterprise', price: 350, status: 'AWS Ready' },
  { id: '2', name: 'Boat Alpha', price: 200, status: 'GraphQL Connected' },
  { id: '3', name: 'Sea Beta', price: 150, status: 'Amplify v5' }
];

function TestCard({ boat }) {
  return (
    <View style={styles.testCard}>
      <Text style={styles.testName}>{boat.name}</Text>
      <Text style={styles.testPrice}>${boat.price}/día</Text>
      <Text style={styles.testStatus}>Status: {boat.status}</Text>
    </View>
  );
}

// Componente de estado de AWS Amplify v5
function AWSAmplifyStatusCard() {
  return (
    <View style={styles.awsCard}>
      <Text style={styles.awsTitle}>🚀 AWS Amplify v5 Status</Text>
      <Text style={[styles.awsStatus, amplifyConfigured ? styles.awsSuccess : styles.awsError]}>
        {amplifyConfigured ? '✅ AWS Configurado y Listo' : '❌ Error de Configuración AWS'}
      </Text>
      
      <View style={styles.awsButtons}>
        <TouchableOpacity style={styles.checkButton} onPress={checkAWSAmplify}>
          <Text style={styles.buttonText}>🔍 Verificar AWS</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.testButton} onPress={testAWSConnection}>
          <Text style={styles.buttonText}>🔗 Test AWS</Text>
        </TouchableOpacity>
      </View>
      
      <TouchableOpacity style={styles.nextButton} onPress={showNextSteps}>
        <Text style={styles.buttonText}>📋 Próximos Pasos</Text>
      </TouchableOpacity>
      
      <Text style={styles.awsInfo}>
        AWS Amplify v5.3.21 • GraphQL Ready • No Native Modules
      </Text>
    </View>
  );
}

export default function HomeScreen() {
  console.log('✅ HomeScreen cargado - AWS Amplify v5 integrado');

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.welcomeText}>AWS Amplify v5 Integration 🚀</Text>
        <Text style={styles.subtitle}>Backend as a Service Ready</Text>
      </View>

      {/* AWS Amplify Status */}
      <AWSAmplifyStatusCard />

      {/* Test Data */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🧪 Test Data (Mock)</Text>
        
        {testBoats.map((boat) => (
          <TestCard key={boat.id} boat={boat} />
        ))}
      </View>

      <View style={styles.footer} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: '#232F3E', // AWS Dark Blue
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FF9900', // AWS Orange
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#FFFFFF',
  },
  awsCard: {
    margin: 20,
    padding: 20,
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: amplifyConfigured ? '#28a745' : '#dc3545',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  awsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#232F3E',
    marginBottom: 12,
    textAlign: 'center',
  },
  awsStatus: {
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 16,
  },
  awsSuccess: { color: '#28a745' },
  awsError: { color: '#dc3545' },
  awsButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  checkButton: {
    backgroundColor: '#232F3E',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    flex: 0.48,
  },
  testButton: {
    backgroundColor: '#FF9900',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    flex: 0.48,
  },
  nextButton: {
    backgroundColor: '#28a745',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    marginBottom: 12,
  },
  buttonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  awsInfo: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  testCard: {
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginBottom: 12,
    borderRadius: 8,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#FF9900',
  },
  testName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  testPrice: {
    fontSize: 14,
    color: '#28a745',
    fontWeight: '600',
  },
  testStatus: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
  footer: {
    height: 20,
  },
});
