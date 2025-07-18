import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
  SafeAreaView,
} from 'react-native';
import {
  Text,
  TextInput,
  Button,
  Card,
  Title,
  Paragraph,
  Divider,
  ActivityIndicator,
} from 'react-native-paper';

// AWS Amplify Auth v6
import { signIn, signUp, confirmSignUp } from 'aws-amplify/auth';

console.log('✅ [LoginScreen] Component loaded');

interface Props {
  navigation?: any;
  onLoginSuccess?: () => void;
}

export default function LoginScreen({ navigation, onLoginSuccess }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<'login' | 'register'>('login');

  // Demo data
  const handleDemoLogin = () => {
    setEmail('demo@boatrental.com');
    setPassword('demo123456');
  };

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Por favor completa todos los campos');
      return;
    }

    setIsLoading(true);
    try {
      console.log('🔐 [LoginScreen] Intentando login con AWS Amplify Auth v6...');
      
      const result = await signIn({
        username: email,
        password: password
      });

      console.log('✅ [LoginScreen] Login exitoso:', result);
      
      Alert.alert(
        '✅ Login Exitoso',
        `¡Bienvenido!\n\nEmail: ${email}\nEstado: Autenticado correctamente`,
        [
          {
            text: 'Continuar',
            onPress: () => {
              onLoginSuccess?.();
              navigation?.navigate?.('Home');
            }
          }
        ]
      );

    } catch (error: any) {
      console.error('❌ [LoginScreen] Error en login:', error);
      
      let errorMessage = 'Error de autenticación';
      if (error.name === 'UserNotConfirmedException') {
        errorMessage = 'Usuario no confirmado. Revisa tu email.';
      } else if (error.name === 'NotAuthorizedException') {
        errorMessage = 'Credenciales incorrectas';
      } else if (error.name === 'UserNotFoundException') {
        errorMessage = 'Usuario no encontrado';
      }
      
      Alert.alert('❌ Error de Login', errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Por favor completa todos los campos');
      return;
    }

    setIsLoading(true);
    try {
      console.log('📝 [LoginScreen] Intentando registro con AWS Amplify Auth v6...');
      
      const result = await signUp({
        username: email,
        password: password,
        options: {
          userAttributes: {
            email: email
          }
        }
      });

      console.log('✅ [LoginScreen] Registro exitoso:', result);
      
      Alert.alert(
        '✅ Registro Exitoso',
        `¡Cuenta creada!\n\nEmail: ${email}\n\nRevisa tu email para confirmar la cuenta.`,
        [{ text: 'OK', onPress: () => setMode('login') }]
      );

    } catch (error: any) {
      console.error('❌ [LoginScreen] Error en registro:', error);
      
      let errorMessage = 'Error en el registro';
      if (error.name === 'UsernameExistsException') {
        errorMessage = 'El email ya está registrado';
      } else if (error.name === 'InvalidPasswordException') {
        errorMessage = 'La contraseña no cumple los requisitos';
      }
      
      Alert.alert('❌ Error de Registro', errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = () => {
    if (mode === 'login') {
      handleLogin();
    } else {
      handleRegister();
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.keyboardContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={styles.scrollContainer}>
          <View style={styles.header}>
            <Title style={styles.title}>🛥️ BoatRental</Title>
            <Paragraph style={styles.subtitle}>
              {mode === 'login' ? 'Iniciar Sesión' : 'Crear Cuenta'}
            </Paragraph>
          </View>

          <Card style={styles.card}>
            <Card.Content>
              <Title style={styles.cardTitle}>
                {mode === 'login' ? '🔐 Login' : '📝 Registro'}
              </Title>

              <TextInput
                label="Email"
                value={email}
                onChangeText={setEmail}
                mode="outlined"
                keyboardType="email-address"
                autoCapitalize="none"
                style={styles.input}
                disabled={isLoading}
              />

              <TextInput
                label="Contraseña"
                value={password}
                onChangeText={setPassword}
                mode="outlined"
                secureTextEntry={!showPassword}
                right={
                  <TextInput.Icon
                    icon={showPassword ? 'eye-off' : 'eye'}
                    onPress={() => setShowPassword(!showPassword)}
                  />
                }
                style={styles.input}
                disabled={isLoading}
              />

              {isLoading ? (
                <View style={styles.loadingContainer}>
                  <ActivityIndicator size="large" color="#0066CC" />
                  <Text style={styles.loadingText}>
                    {mode === 'login' ? 'Iniciando sesión...' : 'Creando cuenta...'}
                  </Text>
                </View>
              ) : (
                <>
                  <Button
                    mode="contained"
                    onPress={handleSubmit}
                    style={styles.button}
                  >
                    {mode === 'login' ? 'Iniciar Sesión' : 'Crear Cuenta'}
                  </Button>

                  {mode === 'login' && (
                    <>
                      <Divider style={styles.divider} />
                      <Button
                        mode="outlined"
                        onPress={handleDemoLogin}
                        style={styles.demoButton}
                      >
                        🚀 Usar Demo
                      </Button>
                    </>
                  )}

                  <Button
                    mode="text"
                    onPress={() => setMode(mode === 'login' ? 'register' : 'login')}
                    style={styles.linkButton}
                  >
                    {mode === 'login' 
                      ? '¿No tienes cuenta? Regístrate' 
                      : '¿Ya tienes cuenta? Inicia sesión'
                    }
                  </Button>

                  <Button
                    mode="text"
                    onPress={() => navigation?.goBack?.()}
                    style={styles.linkButton}
                  >
                    ← Volver al Inicio
                  </Button>
                </>
              )}
            </Card.Content>
          </Card>

          <View style={styles.footer}>
            <Text style={styles.footerText}>
              🚀 AWS Amplify v6 Auth • Hermes Compatible
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f7fa',
  },
  keyboardContainer: {
    flex: 1,
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#7f8c8d',
    textAlign: 'center',
  },
  card: {
    elevation: 4,
    marginBottom: 20,
    borderRadius: 12,
  },
  cardTitle: {
    textAlign: 'center',
    marginBottom: 20,
    color: '#2c3e50',
  },
  input: {
    marginBottom: 16,
  },
  button: {
    marginTop: 10,
    paddingVertical: 8,
  },
  divider: {
    marginVertical: 20,
  },
  demoButton: {
    marginBottom: 10,
  },
  linkButton: {
    marginTop: 10,
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#7f8c8d',
  },
  footer: {
    alignItems: 'center',
    marginTop: 20,
  },
  footerText: {
    fontSize: 12,
    color: '#95a5a6',
  },
});
