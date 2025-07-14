import React from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { MaterialCommunityIcons } from '@expo/vector-icons';

// ===================================
// IMPORTACIONES ESTÁTICAS (HERMES-COMPATIBLE)
// ===================================

// Hooks del store
import { useAppSelector } from '../store/hooks';

// Navegador de autenticación
import { AuthNavigator } from './AuthNavigator';

// Pantallas principales
import HomeScreen from '../screens/home/HomeScreen';
import SearchScreen from '../screens/search/SearchScreen';
import BookingsScreen from '../screens/bookings/BookingsScreen';
import ProfileScreen from '../screens/profile/ProfileScreen';

// Pantallas de detalles y booking
import BoatDetailsScreen from '../screens/boats/BoatDetailsScreen';
import { BookingScreen } from '../screens/booking/BookingScreen';
import { PaymentScreen } from '../screens/payment/PaymentScreen';

console.log('✅ [AppNavigator] Todas las pantallas importadas estáticamente');

// ===================================
// TIPOS DE NAVEGACIÓN
// ===================================
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
  BoatDetails: { boatId: string };
  Booking: { boatId: string };
  Payment: { bookingId: string };
};

export type BottomTabParamList = {
  Home: undefined;
  Search: undefined;
  Bookings: undefined;
  Profile: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<BottomTabParamList>();

// ===================================
// NAVEGADOR DE PESTAÑAS INFERIOR
// ===================================
function BottomTabNavigator() {
  console.log('🎯 [BottomTabNavigator] Renderizando navegador de pestañas');

  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: '#0066CC',
        tabBarInactiveTintColor: 'gray',
        headerShown: false,
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarLabel: 'Inicio',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="home" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="Search"
        component={SearchScreen}
        options={{
          tabBarLabel: 'Buscar',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="magnify" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="Bookings"
        component={BookingsScreen}
        options={{
          tabBarLabel: 'Reservas',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="calendar" color={color} size={size} />
          ),
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          tabBarLabel: 'Perfil',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="account" color={color} size={size} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}

// ===================================
// NAVEGADOR PRINCIPAL
// ===================================
export function AppNavigator() {
  console.log('🎯 [AppNavigator] Renderizando navegador principal');

  // Obtener estado de autenticación usando hook estático
  const authState = useAppSelector((state: any) => state?.auth);
  const isAuthenticated = authState?.isAuthenticated || false;
  const isLoading = authState?.isLoading || false;

  console.log('🔐 [AppNavigator] Estado de auth:', { isAuthenticated, isLoading });

  // Pantalla de carga
  if (isLoading) {
    console.log('⏳ [AppNavigator] Mostrando pantalla de carga');
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#0066CC" />
        <Text style={{ marginTop: 10 }}>Verificando autenticación...</Text>
      </View>
    );
  }

  console.log(`🔄 [AppNavigator] Renderizando stack: ${isAuthenticated ? 'Main' : 'Auth'}`);

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {!isAuthenticated ? (
        <Stack.Screen name="Auth" component={AuthNavigator} />
      ) : (
        <>
          <Stack.Screen name="Main" component={BottomTabNavigator} />
          <Stack.Screen
            name="BoatDetails"
            component={BoatDetailsScreen}
            options={{
              headerShown: true,
              title: 'Detalles del Barco',
              headerBackTitle: 'Atrás'
            }}
          />
          <Stack.Screen
            name="Booking"
            component={BookingScreen}
            options={{
              headerShown: true,
              title: 'Reservar',
              headerBackTitle: 'Atrás'
            }}
          />
          <Stack.Screen
            name="Payment"
            component={PaymentScreen}
            options={{
              headerShown: true,
              title: 'Pago',
              headerBackTitle: 'Atrás'
            }}
          />
        </>
      )}
    </Stack.Navigator>
  );
}