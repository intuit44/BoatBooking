import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import { confirmSignUp, getCurrentUser, resetPassword, signIn, signOut, signUp } from 'aws-amplify/auth';

interface AuthState {
  user: any | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  isLoading: false,
  isAuthenticated: false,
  error: null,
};

// AsyncThunks para autenticación
export const loginUser = createAsyncThunk(
  'auth/loginUser',
  async ({ email, password }: { email: string; password: string }) => {
    const user = await signIn({ username: email, password });
    return user;
  }
);

// ✅ Actualizar registerUser para incluir phone
export const registerUser = createAsyncThunk(
  'auth/registerUser',
  async ({ email, password, name, phone }: { 
    email: string; 
    password: string; 
    name: string;
    phone: string;
  }) => {
    const result = await signUp({
      username: email,
      password,
      options: {
        userAttributes: {
          email,
          name,
          phone_number: phone, // ✅ AWS Cognito usa 'phone_number'
        },
      },
    });
    return result;
  }
);

export const confirmSignUpUser = createAsyncThunk(
  'auth/confirmSignUp',
  async ({ email, code }: { email: string; code: string }) => {
    const result = await confirmSignUp({ username: email, confirmationCode: code });
    return result;
  }
);

export const forgotPassword = createAsyncThunk(
  'auth/forgotPassword',
  async (email: string) => {
    const result = await resetPassword({ username: email });
    return result;
  }
);

export const logoutUser = createAsyncThunk(
  'auth/logoutUser',
  async () => {
    await signOut();
  }
);

export const checkAuthStatus = createAsyncThunk(
  'auth/checkAuthStatus',
  async () => {
    const user = await getCurrentUser();
    return user;
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload;
        state.isAuthenticated = true;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Error al iniciar sesión';
      })
      // Register
      .addCase(registerUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state) => {
        state.isLoading = false;
        // Usuario registrado, pero necesita confirmación
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Error al registrarse';
      })
      // Forgot Password
      .addCase(forgotPassword.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(forgotPassword.fulfilled, (state) => {
        state.isLoading = false;
      })
      .addCase(forgotPassword.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Error al enviar código de verificación';
      })
      // Logout
      .addCase(logoutUser.fulfilled, (state) => {
        state.user = null;
        state.isAuthenticated = false;
      })
      // Check auth status
      .addCase(checkAuthStatus.fulfilled, (state, action) => {
        state.user = action.payload;
        state.isAuthenticated = true;
      })
      .addCase(checkAuthStatus.rejected, (state) => {
        state.user = null;
        state.isAuthenticated = false;
      });
  },
});

export const { clearError } = authSlice.actions;
export default authSlice.reducer;