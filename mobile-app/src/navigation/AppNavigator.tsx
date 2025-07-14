import React from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { AuthNavigator } from './AuthNavigator';  // ✅ Usar el archivo separado

console.log('🔧 [AppNavigator] Iniciando importación de pantallas...');
// Importar hooks del store
let useAppSelector: any;
try {
  const hooks = require('../store/hooks');
  useAppSelector = hooks.useAppSelector;
  console.log('✅ [AppNavigator] Hooks importados correctamente');
} catch (error) {
  console.error('❌ [AppNavigator] Error al importar hooks:', error);
}

// Importar las pantallas con manejo de errores
let HomeScreen: any, SearchScreen: any, BookingsScreen: any, ProfileScreen: any;
let BoatDetailsScreen: any, BookingScreen: any, PaymentScreen: any;
let LoginScreen: any, RegisterScreen: any, ForgotPasswordScreen: any;

try {
  HomeScreen = require('../screens/home/HomeScreen').default;
  console.log('✅ [AppNavigator] HomeScreen importado');
} catch (error) {
  console.error('❌ [AppNavigator] Error al importar HomeScreen:', error);
  HomeScreen = () => <View><Text>Error cargando HomeScreen</Text></View>;
}

try {
  const searchModule = require('../screens/search/SearchScreen');
  SearchScreen = searchModule.SearchScreen || searchModule.default;
  console.log('✅ [AppNavigator] SearchScreen importado');
} catch (error) {
  console.error('❌ [AppNavigator] Error al importar SearchScreen:', error);
  SearchScreen = () => <View><Text>Error cargando SearchScreen</Text></View>;
}

try {
  const bookingsModule = require('../screens/bookings/BookingsScreen');
  BookingsScreen = bookingsModule.BookingsScreen || bookingsModule.default;
  console.log('✅ [AppNavigator] BookingsScreen importado');
} catch (error) {
  console.error('❌ [AppNavigator] Error al importar BookingsScreen:', error);
  BookingsScreen = () => <View><Text>Error cargando BookingsScreen</Text></View>;
}

try {
  const profileModule = require('../screens/profile/ProfileScreen');
  ProfileScreen = profileModule.ProfileScreen || profileModule.default;
  console.log('✅ [AppNavigator] ProfileScreen importado');
} catch (error) {
  console.error('❌ [AppNavigator] Error al importar ProfileScreen:', error);
  ProfileScreen = () => <View><Text>Error cargando ProfileScreen</Text></View>;
}

try {
  BoatDetailsScreen = require('../screens/boats/BoatDetailsScreen').default;
  console.log('✅ [AppNavigator] BoatDetailsScreen importado');
} catch (error) {
  console.error('❌ [AppNavigator] Error al importar BoatDetailsScreen:', error);
  BoatDetailsScreen = () => <View><Text>Error cargando BoatDetailsScreen</Text></View>;
}

try {
  const bookingModule = require('../screens/booking/BookingScreen');
  BookingScreen = bookingModule.BookingScreen || bookingModule.default;
  console.log('✅ [AppNavigator] BookingScreen importado');
} catch (error) {
  console.error('❌ [AppNavigator] Error al importar BookingScreen:', error);
  BookingScreen = () => <View><Text>Error cargando BookingScreen</Text></View>;
}

try {
  const paymentModule = require('../screens/payment/PaymentScreen');
  PaymentScreen = paymentModule.PaymentScreen || paymentModule.default;
  console.log('✅ [AppNavigator] PaymentScreen importado');
} catch (error) {
  console.error('❌ [AppNavigator] Error al importar PaymentScreen:', error);
  PaymentScreen = () => <View><Text>Error cargando PaymentScreen</Text></View>;
}

try {
  LoginScreen = require('../screens/auth/LoginScreen').default;
  console.log('✅ [AppNavigator] LoginScreen importado');
} catch (error) {
  console.error('❌ [AppNavigator] Error al importar LoginScreen:', error);
  LoginScreen = () => <View><Text>Error cargando LoginScreen</Text></View>;
}

try {
  RegisterScreen = require('../screens/auth/RegisterScreen').default;
  console.log('✅ [AppNavigator] RegisterScreen importado');
} catch (error) {
  console.error('❌ [AppNavigator] Error al importar RegisterScreen:', error);
  RegisterScreen = () => <View><Text>Error cargando RegisterScreen</Text></View>;
}

try {
  ForgotPasswordScreen = require('../screens/auth/ForgotPasswordScreen').default;
  console.log('✅ [AppNavigator] ForgotPasswordScreen importado');
} catch (error) {
  console.error('❌ [AppNavigator] Error al importar ForgotPasswordScreen:', error);
  ForgotPasswordScreen = () => <View><Text>Error cargando ForgotPasswordScreen</Text></View>;
}

// Tipos de navegación
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

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator<BottomTabParamList>();


// Navegador de pestañas inferior
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

// Navegador principal
export function AppNavigator() {
  console.log('🎯 [AppNavigator] Renderizando navegador principal');

  let isAuthenticated = false;
  let isLoading = false;

  // Intentar obtener el estado de autenticación
  if (useAppSelector) {
    try {
      const authState = useAppSelector((state: any) => state.auth);
      isAuthenticated = authState?.isAuthenticated || false;
      isLoading = authState?.isLoading || false;
      console.log('🔐 [AppNavigator] Estado de auth:', { isAuthenticated, isLoading });
    } catch (error) {
      console.error('❌ [AppNavigator] Error al obtener estado de auth:', error);
      isLoading = false;
    }
  } else {
    console.warn('⚠️ [AppNavigator] useAppSelector no disponible, usando valores por defecto');
    isLoading = false;
  }

  if (isLoading) {
    console.log('⏳ [AppNavigator] Mostrando pantalla de carga de auth');
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
            options={{ headerShown: true, title: 'Detalles del Barco' }}
          />
          <Stack.Screen
            name="Booking"
            component={BookingScreen}
            options={{ headerShown: true, title: 'Reservar' }}
          />
          <Stack.Screen
            name="Payment"
            component={PaymentScreen}
            options={{ headerShown: true, title: 'Pago' }}
          />
        </>
      )}
    </Stack.Navigator>
  );
}