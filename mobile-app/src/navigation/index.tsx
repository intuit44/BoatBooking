// File: mobile-app/src/navigation/index.tsx

import React from 'react';
import { useAppSelector } from '../store/hooks';
import { RootState } from '../store/store';

export { default as AppNavigator } from './AppNavigator';
export { default as AuthNavigator } from './AuthNavigator';

// AGREGAR ESTE COMPONENTE PRINCIPAL:
export const RootNavigator = () => {
    const { isAuthenticated, isLoading } = useAppSelector((state: RootState) => state.auth);

    console.log('🚦 RootNavigator status:', { isAuthenticated, isLoading });

    if (isLoading) {
        return null;
    }

    if (isAuthenticated) {
        console.log('🔐 Mostrando AppNavigator');
        const { AppNavigator } = require('./AppNavigator');
        return <AppNavigator />;
    } else {
        console.log('👤 Mostrando AuthNavigator');
        const { AuthNavigator } = require('./AuthNavigator');
        return <AuthNavigator />;
    }
};
