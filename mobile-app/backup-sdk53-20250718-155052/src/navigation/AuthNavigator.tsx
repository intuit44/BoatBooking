import React from 'react';
import { View, Text } from 'react-native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

// Screens
import LoginScreen from '../screens/auth/LoginScreen';

console.log('✅ [AuthNavigator] AuthNavigator cargado');

// ===================================
// TIPOS DE NAVEGACIÓN AUTH
// ===================================
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
};

const Stack = createNativeStackNavigator<AuthStackParamList>();

// ===================================
// SCREEN PLACEHOLDERS SIMPLES
// ===================================
function RegisterScreen() {
  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f8f9fa' }}>
      <Text style={{ fontSize: 18, fontWeight: 'bold' }}>📝 Registro</Text>
      <Text style={{ marginTop: 10, color: '#666' }}>Pantalla de registro (próximamente)</Text>
    </View>
  );
}

function ForgotPasswordScreen() {
  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f8f9fa' }}>
      <Text style={{ fontSize: 18, fontWeight: 'bold' }}>🔐 Recuperar Contraseña</Text>
      <Text style={{ marginTop: 10, color: '#666' }}>Pantalla de recuperación (próximamente)</Text>
    </View>
  );
}

// ===================================
// NAVEGADOR DE AUTENTICACIÓN
// ===================================
export default function AuthNavigator() {
  console.log('🔐 [AuthNavigator] Renderizando navegador de auth');

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        animation: 'slide_from_right'
      }}
      initialRouteName="Login"
    >
      <Stack.Screen
        name="Login"
        component={LoginScreen}
        options={{ title: 'Iniciar Sesión' }}
      />
      <Stack.Screen
        name="Register"
        component={RegisterScreen}
        options={{ title: 'Crear Cuenta' }}
      />
      <Stack.Screen
        name="ForgotPassword"
        component={ForgotPasswordScreen}
        options={{ title: 'Recuperar Contraseña' }}
      />
    </Stack.Navigator>
  );
}
