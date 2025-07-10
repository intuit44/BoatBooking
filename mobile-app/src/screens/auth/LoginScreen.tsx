import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import {
  Text,
  TextInput,
  Button,
  Card,
  Title,
  Paragraph,
  Divider,
} from 'react-native-paper';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { loginUser } from '../../store/slices/authSlice';
import { RootState } from '../../store/store';
import { StackScreenProps } from '@react-navigation/stack';
import { useNavigation } from '@react-navigation/native';

type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
};

type Props = StackScreenProps<AuthStackParamList, 'Login'>;

export function LoginScreen({ navigation }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const dispatch = useAppDispatch();
  const { isLoading, error } = useAppSelector((state: RootState) => state.auth);

  // Hook adicional para navegación más flexible
  const rootNavigation = useNavigation();

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Por favor completa todos los campos');
      return;
    }

    try {
      await dispatch(loginUser({ email, password })).unwrap();
    } catch (error) {
      Alert.alert('Error', 'Credenciales incorrectas');
    }
  };

  const handleDemoLogin = () => {
    setEmail('demo@boatrental.ve');
    setPassword('demo123');
  };

  const handleForgotPassword = () => {
    try {
      // Intentar navegación directa primero
      navigation.navigate('ForgotPassword');
    } catch (error) {
      // Si falla, intentar con el navegador raíz
      try {
        (rootNavigation as any).navigate('Auth', { screen: 'ForgotPassword' });
      } catch (secondError) {
        // Si ambos fallan, mostrar alerta
        Alert.alert(
          'Navegación no disponible',
          'La pantalla de recuperación de contraseña no está disponible en este momento.'
        );
      }
    }
  };

  const handleRegister = () => {
    try {
      // Intentar navegación directa primero
      navigation.navigate('Register');
    } catch (error) {
      // Si falla, intentar con el navegador raíz
      try {
        (rootNavigation as any).navigate('Auth', { screen: 'Register' });
      } catch (secondError) {
        // Si ambos fallan, mostrar alerta
        Alert.alert(
          'Navegación no disponible',
          'La pantalla de registro no está disponible en este momento.'
        );
      }
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.header}>
          <Title style={styles.title}>🛥️ BoatRental</Title>
          <Paragraph style={styles.subtitle}>
            Alquila embarcaciones en Venezuela
          </Paragraph>
        </View>

        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>Iniciar Sesión</Title>

            <TextInput
              label="Email"
              value={email}
              onChangeText={setEmail}
              mode="outlined"
              keyboardType="email-address"
              autoCapitalize="none"
              style={styles.input}
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
            />

            <Button
              mode="contained"
              onPress={handleLogin}
              loading={isLoading}
              disabled={isLoading}
              style={styles.button}
            >
              Iniciar Sesión
            </Button>

            <Divider style={styles.divider} />

            <Button
              mode="outlined"
              onPress={handleDemoLogin}
              style={styles.demoButton}
            >
              🚀 Probar Demo
            </Button>

            <Button
              mode="text"
              onPress={handleForgotPassword}
              style={styles.linkButton}
            >
              ¿Olvidaste tu contraseña?
            </Button>

            <Button
              mode="text"
              onPress={handleRegister}
              style={styles.linkButton}
            >
              ¿No tienes cuenta? Regístrate
            </Button>
          </Card.Content>
        </Card>

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            🇻🇪 Hecho en Venezuela con ❤️
          </Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
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
    color: '#0066CC',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  card: {
    elevation: 4,
    marginBottom: 20,
  },
  cardTitle: {
    textAlign: 'center',
    marginBottom: 20,
    color: '#333',
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
  footer: {
    alignItems: 'center',
    marginTop: 20,
  },
  footerText: {
    fontSize: 14,
    color: '#666',
  },
});

// Exportación por defecto para compatibilidad
export default LoginScreen;
