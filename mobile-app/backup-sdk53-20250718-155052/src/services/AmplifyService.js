// src/services/AmplifyService.js
// Wrapper para usar el API.ts existente con Amplify
import { API, graphqlOperation } from 'aws-amplify';
import { listBoats } from '../graphql/queries';
import { createBoat } from '../graphql/mutations';

class AmplifyService {
  // Función para obtener todos los barcos
  static async getBoats() {
    try {
      console.log('🔍 [AmplifyService] Obteniendo barcos desde GraphQL...');
      const result = await API.graphql(graphqlOperation(listBoats));
      console.log('✅ [AmplifyService] Barcos obtenidos:', result.data.listBoats.items.length);
      return result.data.listBoats.items;
    } catch (error) {
      console.log('❌ [AmplifyService] Error obteniendo barcos:', error);
      throw error;
    }
  }

  // Función para crear un barco de prueba
  static async createSampleBoat() {
    const sampleBoat = {
      name: "Barco de Prueba App",
      type: "YACHT",
      description: "Barco creado desde la app móvil para pruebas",
      capacity: 8,
      pricePerHour: 150,
      pricePerDay: 1200,
      images: ["https://example.com/boat.jpg"],
      location: {
        marina: "Marina de Prueba",
        state: "FL",
        coordinates: {
          latitude: 25.7617,
          longitude: -80.1918
        }
      },
      specifications: {
        length: 35,
        engine: "Twin 350HP",
        fuel: "Gasoline",
        year: 2023
      },
      amenities: ["GPS", "Sound System", "Cooler"],
      availability: {
        available: true,
        blockedDates: []
      },
      featured: true,
      ownerId: "test-owner-" + Date.now()
    };

    try {
      console.log('🔨 [AmplifyService] Creando barco de prueba...');
      const result = await API.graphql(
        graphqlOperation(createBoat, { input: sampleBoat })
      );
      console.log('✅ [AmplifyService] Barco creado:', result.data.createBoat);
      return result.data.createBoat;
    } catch (error) {
      console.log('❌ [AmplifyService] Error creando barco:', error);
      throw error;
    }
  }

  // Función principal de prueba de conexión
  static async testConnection() {
    try {
      console.log('🔗 [AmplifyService] Iniciando prueba de conexión...');
      
      // Intentar obtener barcos
      const boats = await this.getBoats();
      
      console.log('✅ [AmplifyService] Conexión exitosa');
      
      return { 
        success: true, 
        message: `Conexión exitosa! Encontrados ${boats.length} barcos en la base de datos.`,
        data: boats,
        boatCount: boats.length
      };
    } catch (error) {
      console.log('❌ [AmplifyService] Error de conexión:', error);
      
      let errorMessage = 'Error de conexión desconocido';
      
      if (error.message) {
        errorMessage = error.message;
      }
      
      if (error.errors && error.errors.length > 0) {
        errorMessage = error.errors[0].message;
      }
      
      // Errores comunes y sus soluciones
      if (errorMessage.includes('Unauthorized')) {
        errorMessage = 'Error de autenticación - Verifica credenciales AWS';
      } else if (errorMessage.includes('Network')) {
        errorMessage = 'Error de red - Verifica conexión a internet';
      } else if (errorMessage.includes('GraphQL')) {
        errorMessage = 'Error GraphQL - Verifica endpoint y esquema';
      }
      
      return { 
        success: false, 
        message: errorMessage,
        error: error
      };
    }
  }

  // Función para obtener estadísticas
  static async getStats() {
    try {
      const boats = await this.getBoats();
      
      const stats = {
        totalBoats: boats.length,
        featuredBoats: boats.filter(boat => boat.featured).length,
        boatTypes: [...new Set(boats.map(boat => boat.type))],
        avgPricePerDay: boats.length > 0 
          ? Math.round(boats.reduce((sum, boat) => sum + boat.pricePerDay, 0) / boats.length)
          : 0
      };
      
      console.log('📊 [AmplifyService] Estadísticas:', stats);
      return stats;
    } catch (error) {
      console.log('❌ [AmplifyService] Error obteniendo estadísticas:', error);
      throw error;
    }
  }
}

export default AmplifyService;
