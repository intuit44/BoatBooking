import { configureStore } from '@reduxjs/toolkit';
import boatsReducer from './slices/boatsSlice';

export const store = configureStore({
  reducer: {
    boats: boatsReducer,
    // Agrega otros reducers aquí
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;