// src/store/store.ts
import { TypedUseSelectorHook, useSelector } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import boatsReducer from './slices/boatsSlice';
import authReducer from './slices/authSlice';
import bookingsReducer from './slices/bookingsSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    boats: boatsReducer,
    bookings: bookingsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignorar estas acciones para AsyncStorage
        ignoredActions: [
          'auth/login/fulfilled',
          'auth/register/fulfilled',
          'auth/checkAuthStatus/fulfilled',
        ],
        // Ignorar estos paths en el estado
        ignoredPaths: ['auth.user'],
      },
    }),
});

export type AppDispatch = typeof store.dispatch;
export type RootState = ReturnType<typeof store.getState>;
// Hook tipado para useSelector
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
