import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import boatsReducer from './slices/boatsSlice';
import bookingsReducer from './slices/bookingsSlice';

export const store = configureStore({
  reducer: {
    boats: boatsReducer,      // ✅ Dominio independiente
    auth: authReducer,        // ✅ Dominio independiente  
    bookings: bookingsReducer, // ✅ Dominio independiente
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false, // Para AWS Amplify
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;