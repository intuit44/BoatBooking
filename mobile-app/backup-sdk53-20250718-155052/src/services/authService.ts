import { Auth } from 'aws-amplify';

export class AuthService {
  static async login(email: string, password: string) {
    try {
      const user = await Auth.signIn({ username: email, password });
      return { success: true, user };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Error desconocido' };
    }
  }

  static async logout() {
    try {
      await Auth.signOut();
      return { success: true };
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Error desconocido' };
    }
  }

  static async getCurrentUser() {
    try {
      const user = await Auth.currentAuthenticatedUser();
      return { success: true, user };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Error desconocido',
      };
    }
  }

}