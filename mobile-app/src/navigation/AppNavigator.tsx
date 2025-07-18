import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { MaterialCommunityIcons } from '@expo/vector-icons';
// Pantallas principales
import HomeScreen from '../screens/home/HomeScreen';
import AuthNavigator from './AuthNavigator';

console.log('✅ [AppNavigator] Importaciones cargadas');



// ===================================
// TIPOS DE NAVEGACIÓN
// ===================================
export type RootStackParamList = {
  Main: undefined;
  Auth: undefined;
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
// PANTALLAS PLACEHOLDER MEJORADAS
// ===================================
function SearchScreen({ navigation }: any) {
  return (
    <View style={styles.placeholderContainer}>
      <Text style={styles.placeholderTitle}>🔍 Buscar Barcos</Text>
      <Text style={styles.placeholderSubtitle}>Encuentra la embarcación perfecta</Text>

      <TouchableOpacity
        style={styles.demoButton}
        onPress={() => navigation.navigate('Auth')}
      >
        <Text style={styles.demoButtonText}>🔐 Ir a Login Demo</Text>
      </TouchableOpacity>

      <Text style={styles.placeholderNote}>Pantalla de búsqueda (próximamente)</Text>
    </View>
  );
}

function BookingsScreen({ navigation }: any) {
  return (
    <View style={styles.placeholderContainer}>
      <Text style={styles.placeholderTitle}>📅 Mis Reservas</Text>
      <Text style={styles.placeholderSubtitle}>Gestiona tus reservaciones</Text>

      <TouchableOpacity
        style={styles.demoButton}
        onPress={() => navigation.navigate('Auth')}
      >
        <Text style={styles.demoButtonText}>🔐 Login para ver reservas</Text>
      </TouchableOpacity>

      <Text style={styles.placeholderNote}>Pantalla de reservas (próximamente)</Text>
    </View>
  );
}

function ProfileScreen({ navigation }: any) {
  return (
    <View style={styles.placeholderContainer}>
      <Text style={styles.placeholderTitle}>👤 Mi Perfil</Text>
      <Text style={styles.placeholderSubtitle}>Configuración y datos personales</Text>

      <TouchableOpacity
        style={styles.demoButton}
        onPress={() => navigation.navigate('Auth')}
      >
        <Text style={styles.demoButtonText}>🔐 Iniciar Sesión</Text>
      </TouchableOpacity>

      <Text style={styles.placeholderNote}>Pantalla de perfil (próximamente)</Text>
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
        tabBarActiveTintColor: '#2c3e50',
        tabBarInactiveTintColor: '#95a5a6',
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#fff',
          borderTopWidth: 1,
          borderTopColor: '#ecf0f1',
          paddingBottom: 5,
          height: 60,
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
// NAVEGADOR PRINCIPAL CON AUTH
// ===================================
export function AppNavigator() {
  console.log('🎯 [AppNavigator] Renderizando navegador principal');

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Main" component={BottomTabNavigator} />
      <Stack.Screen
        name="Auth"
        component={AuthNavigator}
        options={{
          presentation: 'modal',
          animation: 'slide_from_bottom'
        }}
      />
    </Stack.Navigator>
  );
}

// ===================================
// EXPORT DEFAULT (ARREGLA EL ERROR)
// ===================================
export default AppNavigator;

// ===================================
// ESTILOS PARA PLACEHOLDERS
// ===================================
const styles = StyleSheet.create({
  placeholderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    padding: 20,
  },
  placeholderTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 8,
  },
  placeholderSubtitle: {
    fontSize: 16,
    color: '#7f8c8d',
    textAlign: 'center',
    marginBottom: 30,
  },
  demoButton: {
    backgroundColor: '#3498db',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    marginBottom: 20,
  },
  demoButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  placeholderNote: {
    fontSize: 14,
    color: '#95a5a6',
    fontStyle: 'italic',
  },
});
