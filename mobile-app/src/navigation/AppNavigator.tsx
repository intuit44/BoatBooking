// src/navigation/AppNavigator.tsx
import React from 'react';
import { createStackNavigator, CardStyleInterpolators, TransitionPresets } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Animated, Easing } from 'react-native';
import { IconButton } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';

import { useAppSelector } from '../store/hooks';
import { RootState } from '../store/store';

// Importar pantallas
import { HomeScreen } from '../screens/home/HomeScreen';
// import { SearchScreen } from '../screens/search/SearchScreen';
// import BoatDetailsScreen from '../screens/boats/BoatDetailsScreen';
// import { BookingScreen } from '../screens/booking/BookingScreen';
// import { ProfileScreen } from '../screens/profile/ProfileScreen';
// import { PaymentScreen } from '../screens/payment/PaymentScreen';

// Importar AuthNavigator en lugar de AuthScreen
import { AuthNavigator } from './AuthNavigator';

// Pantallas temporales para evitar errores
const SearchScreen = () => <HomeScreen />;
const BoatDetailsScreen = () => <HomeScreen />;
const BookingScreen = () => <HomeScreen />;
const ProfileScreen = () => <HomeScreen />;
const PaymentScreen = () => <HomeScreen />;

// Tipos de navegación
export type RootStackParamList = {
  Main: undefined;
  BoatDetails: { boatId: string };
  Booking: { boatId: string };
  Auth: undefined;
  Payment: { bookingId: string };
};

export type MainTabParamList = {
  Home: undefined;
  Search: any;
  Profile: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

// Componente para proteger rutas autenticadas
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAppSelector((state: RootState) => state.auth);

  if (!isAuthenticated) {
    return <AuthNavigator />;
  }

  return <>{children}</>;
}

// Transición personalizada para pantallas principales
const slideFromRightTransition = {
  gestureEnabled: true,
  gestureDirection: 'horizontal' as const,
  transitionSpec: {
    open: {
      animation: 'timing' as const,
      config: {
        duration: 350,
        easing: Easing.bezier(0.4, 0, 0.2, 1),
      },
    },
    close: {
      animation: 'timing' as const,
      config: {
        duration: 300,
        easing: Easing.bezier(0.4, 0, 0.2, 1),
      },
    },
  },
  cardStyleInterpolator: ({ current, next, layouts }: any) => {
    const translateX = current.progress.interpolate({
      inputRange: [0, 1],
      outputRange: [layouts.screen.width, 0],
    });

    const opacity = current.progress.interpolate({
      inputRange: [0, 0.5, 1],
      outputRange: [0, 0.5, 1],
    });

    const scale = current.progress.interpolate({
      inputRange: [0, 1],
      outputRange: [0.9, 1],
    });

    return {
      cardStyle: {
        opacity,
        transform: [{ translateX }, { scale }],
      },
      overlayStyle: {
        opacity: current.progress.interpolate({
          inputRange: [0, 1],
          outputRange: [0, 0.1],
        }),
      },
    };
  },
};

// Transición para modales
const modalTransition = {
  presentation: 'modal' as const,
  gestureEnabled: true,
  gestureDirection: 'vertical' as const,
  transitionSpec: {
    open: {
      animation: 'timing' as const,
      config: {
        duration: 350,
        easing: Easing.bezier(0.4, 0, 0.2, 1),
      },
    },
    close: {
      animation: 'timing' as const,
      config: {
        duration: 300,
        easing: Easing.bezier(0.4, 0, 0.2, 1),
      },
    },
  },
  cardStyleInterpolator: ({ current }: any) => {
    const translateY = current.progress.interpolate({
      inputRange: [0, 1],
      outputRange: [600, 0],
    });

    const opacity = current.progress.interpolate({
      inputRange: [0, 0.3, 1],
      outputRange: [0, 0.8, 1],
    });

    return {
      cardStyle: {
        opacity,
        transform: [{ translateY }],
      },
      overlayStyle: {
        opacity: current.progress.interpolate({
          inputRange: [0, 1],
          outputRange: [0, 0.3],
        }),
      },
    };
  },
};

type MaterialIconName = keyof typeof MaterialCommunityIcons.glyphMap;

// Tab Navigator con animaciones
function MainTabNavigator() {
  return (
    <ProtectedRoute>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarIcon: ({ focused, color, size }) => {
            let iconName: MaterialIconName;

            if (route.name === 'Home') {
              iconName = focused ? 'home' : 'home-outline';
            } else if (route.name === 'Search') {
              iconName = 'magnify';
            } else if (route.name === 'Profile') {
              iconName = focused ? 'account' : 'account-outline';
            } else {
              iconName = 'home';
            }

            return (
              <MaterialCommunityIcons
                name={iconName}
                size={size}
                color={color}
              />
            );
          },

          tabBarActiveTintColor: '#0066CC',
          tabBarInactiveTintColor: '#666',
          tabBarStyle: {
            backgroundColor: '#fff',
            borderTopWidth: 1,
            borderTopColor: '#E0E0E0',
            elevation: 8,
            shadowColor: '#000',
            shadowOffset: { width: 0, height: -2 },
            shadowOpacity: 0.1,
            shadowRadius: 8,
            paddingTop: 8,
            paddingBottom: 8,
            height: 70,
          },
          tabBarLabelStyle: {
            fontSize: 12,
            fontWeight: '600',
            marginBottom: 4,
          },
          tabBarItemStyle: {
            paddingVertical: 4,
          },
        })}
      >
        <Tab.Screen
          name="Home"
          component={HomeScreen}
          options={{
            tabBarLabel: 'Inicio',
          }}
        />
        <Tab.Screen
          name="Search"
          component={SearchScreen}
          options={{
            tabBarLabel: 'Buscar',
          }}
        />
        <Tab.Screen
          name="Profile"
          component={ProfileScreen}
          options={{
            tabBarLabel: 'Perfil',
          }}
        />
      </Tab.Navigator>
    </ProtectedRoute>
  );
}

// Stack Navigator principal con transiciones mejoradas
export function AppNavigator() {
  return (
    <Stack.Navigator
      initialRouteName="Main"
      screenOptions={{
        headerShown: false, // 👈 Ocultar headers por defecto
        ...slideFromRightTransition,
      }}
    >
      {/* Tab Navigator principal */}
      <Stack.Screen
        name="Main"
        component={MainTabNavigator}
        options={{
          headerShown: false,
        }}
      />

      {/* Pantallas con transición desde la derecha */}
      <Stack.Screen
        name="BoatDetails"
        component={BoatDetailsScreen}
        options={{
          headerShown: true,
          headerTitle: 'Detalles de la Embarcación',
          headerBackTitleVisible: false,
          ...slideFromRightTransition,
        }}
      />

      <Stack.Screen
        name="Booking"
        component={BookingScreen}
        options={{
          headerShown: true,
          headerTitle: 'Reservar',
          headerBackTitleVisible: false,
          ...slideFromRightTransition,
        }}
      />

      {/* Pantallas modales */}
      <Stack.Screen
        name="Auth"
        component={AuthNavigator}
        options={{
          headerShown: false,
          ...modalTransition,
        }}
      />

      <Stack.Screen
        name="Payment"
        component={PaymentScreen}
        options={{
          headerShown: true,
          headerTitle: 'Pago',
          ...modalTransition,
        }}
      />
    </Stack.Navigator>
  );
}

// Exportación por defecto para compatibilidad
export default AppNavigator;