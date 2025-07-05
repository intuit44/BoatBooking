// src/screens/auth/AuthScreen.tsx
import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import {
  Text,
  Card,
  Title,
  Button,
  TextInput,
  Surface,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';

interface Props {
  navigation: any;
}

export function AuthScreen({ navigation }: Props) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  const handleSubmit = () => {
    // TODO: Implement authentication logic
    console.log('Auth submit:', { isLogin, email, password, name });
    navigation.goBack();
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Surface style={styles.authCard}>
          <Card.Content>
            <Title style={styles.title}>
              {isLogin ? 'Iniciar Sesión' : 'Registrarse'}
            </Title>

            {!isLogin && (
              <TextInput
                label="Nombre completo"
                value={name}
                onChangeText={setName}
                mode="outlined"
                style={styles.input}
              />
            )}

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
              secureTextEntry
              style={styles.input}
            />

            <Button
              mode="contained"
              onPress={handleSubmit}
              style={styles.submitButton}
            >
              {isLogin ? 'Iniciar Sesión' : 'Registrarse'}
            </Button>

            <Button
              mode="text"
              onPress={() => setIsLogin(!isLogin)}
              style={styles.switchButton}
            >
              {isLogin
                ? '¿No tienes cuenta? Regístrate'
                : '¿Ya tienes cuenta? Inicia sesión'
              }
            </Button>

            <Button
              mode="outlined"
              onPress={() => navigation.goBack()}
              style={styles.cancelButton}
            >
              Cancelar
            </Button>
          </Card.Content>
        </Surface>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  authCard: {
    borderRadius: 16,
    elevation: 8,
  },
  title: {
    textAlign: 'center',
    marginBottom: 24,
    fontSize: 24,
    fontWeight: 'bold',
  },
  input: {
    marginBottom: 16,
  },
  submitButton: {
    marginTop: 8,
    marginBottom: 16,
  },
  switchButton: {
    marginBottom: 8,
  },
  cancelButton: {
    marginTop: 8,
  },
});