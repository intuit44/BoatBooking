// File: mobile-app/src/navigation/index.tsx
// CORREGIDO: Sin Redux, solo exports simples

import React from 'react';

// Exports simples sin Redux
export { default as AppNavigator } from './AppNavigator';
export { default as AuthNavigator } from './AuthNavigator';

// RootNavigator simplificado (sin Redux)
export const RootNavigator = () => {
    console.log('🚦 [RootNavigator] Iniciando navegación simplificada');
    
    // Por ahora, siempre mostrar AppNavigator
    // TODO: Implementar lógica de autenticación cuando sea necesario
    const { default: AppNavigator } = require('./AppNavigator');
    return <AppNavigator />;
};

console.log('✅ [Navigation/Index] Navegación simplificada cargada');
