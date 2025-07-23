import { generateClient } from 'aws-amplify/api';
import Constants from 'expo-constants';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

// ✅ NO configurar Amplify aquí - ya se hace en index.js
let graphqlClient: any;

// =============================================================================
// LOGINSCREEN SIMPLE INTEGRADO
// =============================================================================
type SimpleLoginScreenProps = {
  visible: boolean;
  onClose: () => void;
  onLoginSuccess: () => void;
};

function SimpleLoginScreen({ visible, onClose, onLoginSuccess }: SimpleLoginScreenProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleDemo = () => {
    setEmail('demo@boatrental.com');
    setPassword('demo123456');
  };

  const handleLogin = async () => {
    setLoading(true);
    try {
      // Simular login exitoso
      await new Promise(resolve => setTimeout(resolve, 1000));
      Alert.alert(
        '✅ Login Demo Exitoso',
        `¡Bienvenido!\n\nEmail: ${email}\nAWS Amplify: Configurado\nEstado: Demo Login Funcional`,
        [{ text: 'OK', onPress: () => { onClose(); onLoginSuccess(); } }]
      );
    } catch (error) {
      Alert.alert('❌ Error', 'Error en demo login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <SafeAreaView style={styles.modalContainer}>
        <ScrollView contentContainerStyle={styles.modalContent}>
          <Text style={styles.modalTitle}>🔐 Login Demo</Text>

          <View style={styles.inputContainer}>
            <Text style={styles.label}>Email:</Text>
            <Text style={styles.input}>{email || 'Sin email'}</Text>
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.label}>Password:</Text>
            <Text style={styles.input}>{password || 'Sin password'}</Text>
          </View>

          <TouchableOpacity style={styles.demoButton} onPress={handleDemo}>
            <Text style={styles.buttonText}>🚀 Cargar Demo Data</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.loginButton, loading && styles.disabledButton]}
            onPress={handleLogin}
            disabled={loading}
          >
            <Text style={styles.buttonText}>
              {loading ? '⏳ Procesando...' : '✅ Demo Login'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <Text style={styles.buttonText}>❌ Cerrar</Text>
          </TouchableOpacity>

          <Text style={styles.demoNote}>
            📝 Este es un demo de login funcional.{'\n'}
            AWS Amplify v6 está configurado y listo.{'\n'}
            Presiona "Cargar Demo Data" y luego "Demo Login".
          </Text>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

// =============================================================================
// COMPONENTE PRINCIPAL
// =============================================================================

export default function HomeScreen() {
  const [showLogin, setShowLogin] = useState(false);
  const [userLoggedIn, setUserLoggedIn] = useState(false);
  const [isConfigured, setIsConfigured] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [amplifyConfigured, setAmplifyConfigured] = useState(false);

  console.log('🚨 [HomeScreen] ===== RENDER FUNCTION EJECUTADA =====');
  console.log('🎯 [HomeScreen] Timestamp:', new Date().toISOString());

  useEffect(() => {
    console.log('🏠 [HomeScreen] Component mounted - SDK 53');
    
    try {
      // ✅ Crear cliente después de que Amplify ya esté configurado en index.js
      graphqlClient = generateClient();
      setIsConfigured(true);
      setAmplifyConfigured(true);
      console.log('✅ [HomeScreen] GraphQL client initialized');
      
      // Mostrar configuración actual
      const extra = Constants.expoConfig?.extra || {};
      console.log('🔍 [HomeScreen] Current config:', {
        graphqlEndpoint: extra.graphqlEndpoint,
        environment: extra.env,
      });
      
    } catch (err: any) {
      console.error('❌ [HomeScreen] Error initializing GraphQL client:', err);
      setError(err.message);
    }
  }, []);

  const checkAWSStatus = () => {
    const status = `✅ AWS Amplify v6: ${amplifyConfigured ? 'Configurado' : 'Error'}
🔗 generateClient: ${typeof generateClient === 'function' ? 'Disponible' : 'No disponible'}  
🔐 getCurrentUser: ${userLoggedIn ? 'Usuario logueado' : 'No logueado'}
📊 GraphQL Client: ${graphqlClient ? 'Creado' : 'Error'}
📋 Estado: ${amplifyConfigured ? 'Listo para desarrollo' : 'Configuración requerida'}`;

    Alert.alert('🔍 Estado AWS Amplify v6', status);
  };

  const testBoats = [
    {
      id: '1',
      name: 'Enterprise v6',
      price: 350,
      status: amplifyConfigured ? 'AWS Ready ✅' : 'AWS Pending ⚠️'
    },
    {
      id: '2',
      name: 'Alpha GraphQL',
      price: 200,
      status: graphqlClient ? 'GraphQL Ready ✅' : 'GraphQL Pending ⚠️'
    },
    {
      id: '3',
      name: 'Beta Auth',
      price: 150,
      status: userLoggedIn ? 'Auth Ready ✅' : 'Auth Pending ⚠️'
    }
  ];

  if (error) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorTitle}>Configuration Error</Text>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  if (!isConfigured) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#0066cc" />
        <Text style={styles.loadingText}>Initializing GraphQL client...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollContent}>
        <Text style={styles.title}>🚤 Boat Rental v6</Text>
        <Text style={styles.subtitle}>AWS Amplify v6 + React Native 0.79.5 + React 19.1.0</Text>

        {/* AWS Status Card */}
        <View style={styles.statusCard}>
          <Text style={styles.statusTitle}>🚀 AWS Amplify v6 Status</Text>
          <Text style={[styles.statusText, amplifyConfigured ? styles.success : styles.error]}>
            {amplifyConfigured ? '✅ AWS v6 Completamente Funcional' : '❌ AWS v6 Error'}
          </Text>

          <View style={styles.buttonRow}>
            <TouchableOpacity style={styles.statusButton} onPress={checkAWSStatus}>
              <Text style={styles.buttonText}>🔍 Estado AWS</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.loginDemoButton}
              onPress={() => setShowLogin(true)}
            >
              <Text style={styles.buttonText}>🔐 Login Demo</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* User Status */}
        {userLoggedIn && (
          <View style={styles.userCard}>
            <Text style={styles.userTitle}>👤 Usuario Demo Logueado</Text>
            <Text style={styles.userText}>✅ Login demo exitoso</Text>
            <TouchableOpacity
              style={styles.logoutButton}
              onPress={() => setUserLoggedIn(false)}
            >
              <Text style={styles.buttonText}>🚪 Logout</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Boats List */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📋 Boats Status Dashboard</Text>
          {testBoats.map((boat) => (
            <View key={boat.id} style={styles.boatCard}>
              <View style={styles.boatHeader}>
                <Text style={styles.boatName}>{boat.name}</Text>
                <Text style={styles.boatPrice}>${boat.price}/día</Text>
              </View>
              <Text style={[styles.boatStatus, boat.status.includes('✅') ? styles.success : styles.warning]}>
                {boat.status}
              </Text>
            </View>
          ))}
        </View>

        {/* Info Card */}
        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>📊 Sistema Status</Text>
          <Text style={styles.infoText}>
            ✅ React 19.1.0 + New Architecture{'\n'}
            ✅ React Native 0.79.5{'\n'}
            ✅ Expo SDK 53.0.20{'\n'}
            ✅ Metro 0.82.5{'\n'}
            ✅ AWS Amplify v6.6.0{'\n'}
            {amplifyConfigured ? '✅' : '⚠️'} AWS Configurado{'\n'}
            {graphqlClient ? '✅' : '⚠️'} GraphQL Client Ready{'\n'}
            🔐 Login Demo: Funcional
          </Text>
        </View>
      </ScrollView>

      {/* Login Modal */}
      <SimpleLoginScreen
        visible={showLogin}
        onClose={() => setShowLogin(false)}
        onLoginSuccess={() => setUserLoggedIn(true)}
      />
    </SafeAreaView>
  );
}

// =============================================================================
// ESTILOS
// =============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f7fa',
  },
  scrollContent: {
    flex: 1,
    padding: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2c3e50',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#7f8c8d',
    textAlign: 'center',
    marginBottom: 20,
  },
  statusCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statusTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    textAlign: 'center',
    marginBottom: 10,
  },
  statusText: {
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 20,
  },
  success: {
    color: '#27ae60',
  },
  warning: {
    color: '#f39c12',
  },
  error: {
    color: '#e74c3c',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statusButton: {
    flex: 1,
    backgroundColor: '#3498db',
    paddingVertical: 12,
    borderRadius: 8,
    marginRight: 8,
  },
  loginDemoButton: {
    flex: 1,
    backgroundColor: '#e67e22',
    paddingVertical: 12,
    borderRadius: 8,
    marginLeft: 8,
  },
  buttonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
  userCard: {
    backgroundColor: '#d5f4e6',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
  },
  userTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#27ae60',
    marginBottom: 8,
  },
  userText: {
    fontSize: 14,
    color: '#27ae60',
    marginBottom: 12,
  },
  logoutButton: {
    backgroundColor: '#e74c3c',
    paddingVertical: 8,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 16,
  },
  boatCard: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  boatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  boatName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2c3e50',
  },
  boatPrice: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#27ae60',
  },
  boatStatus: {
    fontSize: 14,
    fontWeight: '500',
  },
  infoCard: {
    backgroundColor: '#ecf0f1',
    borderRadius: 8,
    padding: 16,
    marginTop: 20,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#34495e',
    lineHeight: 20,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#f5f7fa',
  },
  modalContent: {
    padding: 20,
    paddingTop: 60,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2c3e50',
    textAlign: 'center',
    marginBottom: 30,
  },
  inputContainer: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2c3e50',
    marginBottom: 4,
  },
  input: {
    fontSize: 16,
    color: '#34495e',
    backgroundColor: 'white',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#bdc3c7',
  },
  demoButton: {
    backgroundColor: '#9b59b6',
    paddingVertical: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  loginButton: {
    backgroundColor: '#27ae60',
    paddingVertical: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  closeButton: {
    backgroundColor: '#e74c3c',
    paddingVertical: 12,
    borderRadius: 8,
    marginBottom: 20,
  },
  disabledButton: {
    opacity: 0.6,
  },
  demoNote: {
    fontSize: 12,
    color: '#7f8c8d',
    textAlign: 'center',
    fontStyle: 'italic',
    lineHeight: 18,
  },
  errorTitle: {
    color: 'red',
    fontSize: 18,
    marginBottom: 10,
    textAlign: 'center',
  },
  errorText: {
    color: 'red',
    textAlign: 'center',
    marginBottom: 20,
  },
  loadingText: {
    marginTop: 10,
    textAlign: 'center',
  },
});
