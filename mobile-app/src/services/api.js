// src/services/api.js
import { API, graphqlOperation } from 'aws-amplify';
import { listBoats } from '../graphql/queries';
import { createBoat } from '../graphql/mutations';

class BoatRentalAPI {
  // Función de prueba - obtener barcos
  static async getBoats() {
    try {
      console.log('🔍 Intentando obtener barcos desde API...');
      const result = await API.graphql(graphqlOperation(listBoats));
      console.log('✅ Barcos obtenidos:', result.data.listBoats.items);
      return result.data.listBoats.items;
    } catch (error) {
      console.log('❌ Error obteniendo barcos:', error);
      console.log('🔍 Detalles del error:', JSON.stringify(error, null, 2));
      throw error;
    }
  }

  // Función de prueba - crear barco de ejemplo
  static async createSampleBoat() {
    const sampleBoat = {
      name: "Barco de Prueba",
      type: "YACHT",
      description: "Barco creado desde la app móvil",
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
      ownerId: "temp-owner-id-" + Date.now() // ID temporal único
    };

    try {
      console.log('🔨 Creando barco de prueba...');
      const result = await API.graphql(
        graphqlOperation(createBoat, { input: sampleBoat })
      );
      console.log('✅ Barco creado:', result.data.createBoat);
      return result.data.createBoat;
    } catch (error) {
      console.log('❌ Error creando barco:', error);
      console.log('🔍 Detalles del error:', JSON.stringify(error, null, 2));
      throw error;
    }
  }

  // Función para probar conectividad básica
  static async testConnection() {
    try {
      console.log('🔗 Probando conexión con AWS...');
      console.log('🎯 Endpoint:', process.env.EXPO_PUBLIC_API_ENDPOINT || 'Endpoint desde aws-exports');
      
      // Intentar obtener barcos (lectura)
      const boats = await this.getBoats();
      
      console.log('✅ Conexión exitosa - Barcos encontrados:', boats.length);
      
      return { 
        success: true, 
        message: `Conexión exitosa! Encontrados ${boats.length} barcos.`,
        data: boats
      };
    } catch (error) {
      console.log('❌ Error de conexión:', error);
      
      let errorMessage = 'Error de conexión desconocido';
      
      if (error.message) {
        errorMessage = error.message;
      }
      
      if (error.errors && error.errors.length > 0) {
        errorMessage = error.errors[0].message;
      }
      
      return { 
        success: false, 
        message: `Error: ${errorMessage}`,
        error: error
      };
    }
  }

  // Función para obtener estadísticas básicas
  static async getStats() {
    try {
      const boats = await this.getBoats();
      
      const stats = {
        totalBoats: boats.length,
        featuredBoats: boats.filter(boat => boat.featured).length,
        boatTypes: [...new Set(boats.map(boat => boat.type))],
        avgPrice: boats.length > 0 
          ? boats.reduce((sum, boat) => sum + boat.pricePerDay, 0) / boats.length 
          : 0
      };
      
      console.log('📊 Estadísticas generadas:', stats);
      return stats;
    } catch (error) {
      console.log('❌ Error obteniendo estadísticas:', error);
      throw error;
    }
  }
}

export default BoatRentalAPI;
