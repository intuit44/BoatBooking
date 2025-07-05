import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Auth } from 'aws-amplify';

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
  isLoading: false,
  error: null,
};

export const registerUser = createAsyncThunk(
  'auth/registerUser',
  async (
    { name, email, phone, password }: { name: string; email: string; phone: string; password: string },
    thunkAPI
  ) => {
    try {
      const result = await Auth.signUp({
        username: email,
        password,
        attributes: {
          email,
          phone_number: phone,
          name,
        },
      });

      return {
        user: {
          id: result.userSub || '',
          email,
          name,
          phone,
          role: 'user',
        },
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
      await Auth.confirmSignUp(email, code);
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
      const user = await Auth.signIn(email, password);
      const attributes = await Auth.currentAuthenticatedUser();
      
      return {
        user: {
          id: user.username || '',
          email: attributes.attributes?.email || email,
          name: attributes.attributes?.name || '',
          phone: attributes.attributes?.phone_number || '',
          role: 'user',
        },
        token: user.signInUserSession?.idToken?.jwtToken || '',
      };
    } catch (error: any) {
      return thunkAPI.rejectWithValue(error.message || 'Error al iniciar sesión');
    }
  }
);

export const resendConfirmationCode = createAsyncThunk(
  'auth/resendConfirmationCode',
  async (email: string, thunkAPI) => {
    try {
      await Auth.resendSignUp(email);
      return true;
    } catch (error: any) {
      return thunkAPI.rejectWithValue(error.message || 'Error al reenviar código');
    }
  }
);

export const forgotPassword = createAsyncThunk(
  'auth/forgotPassword',
  async (email: string, thunkAPI) => {
    try {
      await Auth.forgotPassword(email);
      return true;
    } catch (error: any) {
      return thunkAPI.rejectWithValue(error.message || 'Error al solicitar restablecimiento');
    }
  }
);

export const forgotPasswordSubmit = createAsyncThunk(
  'auth/forgotPasswordSubmit',
  async (
    { email, code, newPassword }: { email: string; code: string; newPassword: string },
    thunkAPI
  ) => {
    try {
      await Auth.forgotPasswordSubmit(email, code, newPassword);
      return true;
    } catch (error: any) {
      return thunkAPI.rejectWithValue(error.message || 'Error al restablecer contraseña');
    }
  }
);

export const changePassword = createAsyncThunk(
  'auth/changePassword',
  async (
    { oldPassword, newPassword }: { oldPassword: string; newPassword: string },
    thunkAPI
  ) => {
    try {
      const user = await Auth.currentAuthenticatedUser();
      await Auth.changePassword(user, oldPassword, newPassword);
      return true;
    } catch (error: any) {
      return thunkAPI.rejectWithValue(error.message || 'Error al cambiar contraseña');
    }
  }
);

export const signOutUser = createAsyncThunk(
  'auth/signOut',
  async (_, thunkAPI) => {
    try {
      await Auth.signOut();
      return true;
    } catch (error: any) {
      return thunkAPI.rejectWithValue(error.message || 'Error al cerrar sesión');
    }
  }
);

export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchCurrentUser',
  async (_, thunkAPI) => {
    try {
      const user = await Auth.currentAuthenticatedUser();
      return {
        id: user.username,
        email: user.attributes?.email || '',
        name: user.attributes?.name || '',
        phone: user.attributes?.phone_number || '',
        role: 'user',
      };
    } catch (error: any) {
      return thunkAPI.rejectWithValue(error.message || 'No hay usuario autenticado');
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
    },
    updateProfile: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },
  },
  extraReducers: (builder) => {
    builder
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
      // Resend Confirmation Code
      .addCase(resendConfirmationCode.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(resendConfirmationCode.fulfilled, (state) => {
        state.isLoading = false;
      })
      .addCase(resendConfirmationCode.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
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
        state.error = action.payload as string;
      })
      // Forgot Password Submit
      .addCase(forgotPasswordSubmit.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(forgotPasswordSubmit.fulfilled, (state) => {
        state.isLoading = false;
      })
      .addCase(forgotPasswordSubmit.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Change Password
      .addCase(changePassword.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(changePassword.fulfilled, (state) => {
        state.isLoading = false;
      })
      .addCase(changePassword.rejected, (state, action) => {
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
      })
      // Fetch Current User
      .addCase(fetchCurrentUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload;
        state.isAuthenticated = true;
      })
      .addCase(fetchCurrentUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        state.isAuthenticated = false;
      });
  },
});

export const { clearError, logout, updateProfile } = authSlice.actions;
export default authSlice.reducer;