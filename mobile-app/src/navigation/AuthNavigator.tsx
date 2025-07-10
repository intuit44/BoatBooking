// File: mobile-app/src/navigation/AuthNavigator.tsx

import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { LoginScreen } from '../screens/auth/LoginScreen';
import { RegisterScreen } from '../screens/auth/RegisterScreen';
import ForgotPasswordScreen from '../screens/auth/ForgotPasswordScreen';


// AGREGAR ESTAS IMPORTACIONES:
import { useAppSelector } from '../store/hooks';
import { RootState } from '../store/store';
import { HomeScreen } from '../screens/home/HomeScreen';

// Tipos de navegación para Auth
export type AuthStackParamList = {
    Login: undefined;
    Register: undefined;
    ForgotPassword: undefined;
};

const Stack = createStackNavigator<AuthStackParamList>();

// AGREGAR ESTE COMPONENTE DE PROTECCIÓN:
function AuthGuard({ children }: { children: React.ReactNode }) {
    const { isAuthenticated } = useAppSelector((state: RootState) => state.auth);

    if (isAuthenticated) {
        return <HomeScreen />;
    }

    return <>{children}</>;
}

export const AuthNavigator = () => {
    return (
        <AuthGuard>
            <Stack.Navigator screenOptions={{ headerShown: false }}>
                <Stack.Screen name="Login" component={LoginScreen} />
                <Stack.Screen name="Register" component={RegisterScreen} />
                <Stack.Screen name="ForgotPassword" component={ForgotPasswordScreen} />
            </Stack.Navigator>
        </AuthGuard>
    );
};

// Exportación por defecto para compatibilidad
export default AuthNavigator;
