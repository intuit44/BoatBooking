import React from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { MaterialCommunityIcons } from '@expo/vector-icons';

// Pantallas principales
import HomeScreen from '../screens/home/HomeScreen';

console.log('✅ [AppNavigator] Importaciones cargadas');

// ===================================
// TIPOS DE NAVEGACIÓN
// ===================================
export type RootStackParamList = {
  Main: undefined;
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
// PANTALLAS PLACEHOLDER SIMPLES
// ===================================
function SearchScreen() {
  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f8f9fa' }}>
      <Text style={{ fontSize: 18, fontWeight: 'bold' }}>🔍 Buscar Barcos</Text>
      <Text style={{ marginTop: 10, color: '#666' }}>Pantalla de búsqueda (próximamente)</Text>
    </View>
  );
}

function BookingsScreen() {
  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f8f9fa' }}>
      <Text style={{ fontSize: 18, fontWeight: 'bold' }}>📅 Mis Reservas</Text>
      <Text style={{ marginTop: 10, color: '#666' }}>Pantalla de reservas (próximamente)</Text>
    </View>
  );
}

function ProfileScreen() {
  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f8f9fa' }}>
      <Text style={{ fontSize: 18, fontWeight: 'bold' }}>👤 Mi Perfil</Text>
      <Text style={{ marginTop: 10, color: '#666' }}>Pantalla de perfil (próximamente)</Text>
    </View>
  );
}

// ===================================
// NAVEGADOR DE PESTAÑAS INFERIOR
// ===================================
function BottomTabNavigator() {
  console.log('🎯 [BottomTabNavigator] Renderizando navegador');

  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: '#0066CC',
        tabBarInactiveTintColor: 'gray',
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#fff',
          borderTopWidth: 1,
          borderTopColor: '#e0e0e0',
        },
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

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Main" component={BottomTabNavigator} />
    </Stack.Navigator>
  );
}

// ===================================
// EXPORT DEFAULT (ARREGLA EL ERROR)
// ===================================
export default AppNavigator;
