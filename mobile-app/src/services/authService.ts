// ✅ AWS Amplify v6 - Nuevos imports
import {
  confirmResetPassword,
  confirmSignUp,
  getCurrentUser,
  resetPassword,
  signIn,
  signOut,
  signUp
} from 'aws-amplify/auth';

export class AuthService {
  // ✅ Login con nueva sintaxis
  static async login(email: string, password: string) {
    try {
      const result = await signIn({ 
        username: email, 
        password 
      });
      return { success: true, user: result };
    } catch (error) {
      console.error('Error en login:', error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Error desconocido' 
      };
    }
  }

  // ✅ Logout con nueva sintaxis
  static async logout() {
    try {
      await signOut();
      return { success: true };
    } catch (error) {
      console.error('Error en logout:', error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Error desconocido' 
      };
    }
  }

  // ✅ Obtener usuario actual con nueva sintaxis
  static async getCurrentUser() {
    try {
      const user = await getCurrentUser();
      return { success: true, user };
    } catch (error) {
      console.error('Error obteniendo usuario:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Usuario no autenticado',
      };
    }
  }

  // ✅ Registro de usuario
  static async register(email: string, password: string, attributes?: Record<string, string>) {
    try {
      const result = await signUp({
        username: email,
        password,
        options: {
          userAttributes: {
            email,
            ...attributes,
          },
        },
      });
      return { success: true, user: result };
    } catch (error) {
      console.error('Error en registro:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Error en registro',
      };
    }
  }

  // ✅ Confirmar registro
  static async confirmRegistration(email: string, confirmationCode: string) {
    try {
      const result = await confirmSignUp({
        username: email,
        confirmationCode,
      });
      return { success: true, result };
    } catch (error) {
      console.error('Error confirmando registro:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Error confirmando registro',
      };
    }
  }

  // ✅ Recuperar contraseña
  static async forgotPassword(email: string) {
    try {
      const result = await resetPassword({
        username: email,
      });
      return { success: true, result };
    } catch (error) {
      console.error('Error recuperando contraseña:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Error recuperando contraseña',
      };
    }
  }

  // ✅ Confirmar nueva contraseña
  static async confirmNewPassword(email: string, confirmationCode: string, newPassword: string) {
    try {
      const result = await confirmResetPassword({
        username: email,
        confirmationCode,
        newPassword,
      });
      return { success: true, result };
    } catch (error) {
      console.error('Error confirmando nueva contraseña:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Error confirmando nueva contraseña',
      };
    }
  }

  // ✅ Verificar estado de autenticación
  static async checkAuthStatus() {
    try {
      const user = await getCurrentUser();
      return {
        success: true,
        isAuthenticated: true,
        user,
      };
    } catch (error) {
      return {
        success: false,
        isAuthenticated: false,
        error: 'No hay usuario autenticado',
      };
    }
  }
}