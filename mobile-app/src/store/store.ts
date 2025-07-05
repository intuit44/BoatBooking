// src/store/store.ts
import { TypedUseSelectorHook, useSelector } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import boatsReducer from './slices/boatsSlice';
import authReducer from './slices/authSlice';
import bookingsReducer from './slices/bookingsSlice';

export const store = configureStore({
  reducer: {
    boats: boatsReducer,
    auth: authReducer,
    bookings: bookingsReducer,
  },
});

export type AppDispatch = typeof store.dispatch;
export type RootState = ReturnType<typeof store.getState>;
// Hook tipado para useSelector
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
