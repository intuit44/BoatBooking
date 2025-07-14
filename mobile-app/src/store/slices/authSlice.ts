import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_ENDPOINT || 'https://sb3qdlv3j3.execute-api.us-east-1.amazonaws.com/prod';

interface User {
  id: string;
  email: string;
  name: string;
  phone?: string;
  role?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true, // Cambiar a true inicialmente
  error: null,
};

// Check for existing auth token on app start
export const checkAuthStatus = createAsyncThunk(
  'auth/checkAuthStatus',
  async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      const userStr = await AsyncStorage.getItem('userData');
      
      if (token && userStr) {
        const user = JSON.parse(userStr);
        return { user, isAuthenticated: true };
      }
      
      return { user: null, isAuthenticated: false };
    } catch (error) {
      return { user: null, isAuthenticated: false };
    }
  }
);

export const registerUser = createAsyncThunk(
  'auth/registerUser',
  async (
    { name, email, phone, password }: { name: string; email: string; phone: string; password: string },
    thunkAPI
  ) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, phone, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Error al registrar usuario');
      }

      return {
        user: data.user,
        needsConfirmation: true,
      };
    } catch (error: any) {
      return thunkAPI.rejectWithValue(error.message || 'Error al registrar usuario');
    }
  }
);

export const confirmSignup = createAsyncThunk(
  'auth/confirmSignup',
  async ({ email, code }: { email: string; code: string }, thunkAPI) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/confirm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, code }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Error al confirmar registro');
      }

      return true;
    } catch (error: any) {
      return thunkAPI.rejectWithValue(error.message || 'Error al confirmar registro');
    }
  }
);

export const loginUser = createAsyncThunk(
  'auth/loginUser',
  async ({ email, password }: { email: string; password: string }, thunkAPI) => {
    try {
      console.log('🔍 Intentando login con:', { email, apiUrl: API_BASE_URL });
      
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      console.log('📡 Response status:', response.status);
      const data = await response.json();
      console.log('📦 Response data:', data);

      if (!response.ok) {
        throw new Error(data.message || 'Error al iniciar sesión');
      }

      // Guardar token y datos del usuario en AsyncStorage
      await AsyncStorage.setItem('authToken', data.token);
      await AsyncStorage.setItem('refreshToken', data.refreshToken || '');
      await AsyncStorage.setItem('userData', JSON.stringify(data.user));
      
      return {
        user: data.user,
        token: data.token,
        refreshToken: data.refreshToken,
      };
    } catch (error: any) {
      console.error('❌ Error en login:', error);
      return thunkAPI.rejectWithValue(error.message || 'Error al iniciar sesión');
    }
  }
);

export const signOutUser = createAsyncThunk(
  'auth/signOut',
  async (_, thunkAPI) => {
    try {
      // Limpiar AsyncStorage
      await AsyncStorage.multiRemove(['authToken', 'refreshToken', 'userData']);
      return true;
    } catch (error: any) {
      return thunkAPI.rejectWithValue(error.message || 'Error al cerrar sesión');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    logout: (state) => {
      state.user = null;
      state.isAuthenticated = false;
      state.error = null;
      // Limpiar AsyncStorage
      AsyncStorage.multiRemove(['authToken', 'refreshToken', 'userData']);
    },
    updateProfile: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // Check Auth Status
      .addCase(checkAuthStatus.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(checkAuthStatus.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.isAuthenticated = action.payload.isAuthenticated;
      })
      .addCase(checkAuthStatus.rejected, (state) => {
        state.isLoading = false;
        state.isAuthenticated = false;
      })
      // Register User
      .addCase(registerUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.isAuthenticated = false;
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Confirm Signup
      .addCase(confirmSignup.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(confirmSignup.fulfilled, (state) => {
        state.isLoading = false;
        state.isAuthenticated = true;
      })
      .addCase(confirmSignup.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Login User
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.isAuthenticated = true;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Sign Out
      .addCase(signOutUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(signOutUser.fulfilled, (state) => {
        state.user = null;
        state.isAuthenticated = false;
        state.isLoading = false;
      })
      .addCase(signOutUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError, logout, updateProfile, setLoading } = authSlice.actions;
export default authSlice.reducer;