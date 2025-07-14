import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';

// IMPORTACIONES ESTÁTICAS con rutas CORREGIDAS
import { Amplify } from 'aws-amplify';
import awsExports from '../../aws-exports';
import AmplifyService from '../../services/AmplifyService'; // ← RUTA CORREGIDA

// Variables globales para el estado
let amplifyConfigured = false;

// Función para configurar Amplify de forma SEGURA con importación ESTÁTICA
const configureAmplifyAsync = async () => {
  try {
    console.log('🔧 [HomeScreen] Configurando Amplify con importación estática...');
    
    // Configuración con archivos ya importados
    const amplifyConfig = {
      ...awsExports,
      Analytics: {
        disabled: true,
      },
    };
    
    console.log('📋 [HomeScreen] Configurando Amplify...');
    console.log('🔗 [HomeScreen] Endpoint:', amplifyConfig.aws_appsync_graphqlEndpoint);
    console.log('🔑 [HomeScreen] Región:', amplifyConfig.aws_appsync_region);
    console.log('🔑 [HomeScreen] Tipo Auth:', amplifyConfig.aws_appsync_authenticationType);
    
    Amplify.configure(amplifyConfig);
    console.log('✅ [HomeScreen] Amplify configurado exitosamente');
    
    amplifyConfigured = true;
    return { success: true, message: 'Amplify configurado correctamente' };
  } catch (error) {
    console.log('❌ [HomeScreen] Error configurando Amplify:', error);
    amplifyConfigured = false;
    return { success: false, message: error.message, error };
  }
};

// Función para probar la conexión API
const testAPIConnection = async () => {
  try {
    console.log('🔗 [HomeScreen] Iniciando prueba de conexión...');
    
    if (!amplifyConfigured) {
      Alert.alert('⚠️ Configurando...', 'Configurando Amplify primero...');
      
      const result = await configureAmplifyAsync();
      
      if (!result.success) {
        Alert.alert(
          '❌ Error de Configuración', 
          `No se pudo configurar Amplify:\n\n${result.message}`,
          [{ text: 'OK' }]
        );
        return;
      }
    }
    
    Alert.alert('🔄 Probando...', 'Conectando con AWS GraphQL...');
    
    const result = await AmplifyService.testConnection();
    
    if (result.success) {
      // Obtener estadísticas adicionales si es posible
      try {
        const stats = await AmplifyService.getStats();
        Alert.alert(
          '✅ Conexión Exitosa', 
          `¡Conectado a AWS!\n\n📊 Estadísticas:\n• ${result.boatCount} barcos total\n• ${stats.featuredBoats} destacados\n• Tipos: ${stats.boatTypes.join(', ')}\n• Precio promedio: $${stats.avgPricePerDay}/día\n\n🎯 Siguiente paso: Integrar datos reales`,
          [{ text: 'Genial!' }]
        );
      } catch (statsError) {
        Alert.alert(
          '✅ Conexión Exitosa', 
          `¡Conectado a AWS!\n\n${result.message}\n\n🎯 Siguiente paso: Integrar datos reales`,
          [{ text: 'Genial!' }]
        );
      }
    } else {
      Alert.alert(
        '❌ Error de Conexión', 
        `No se pudo conectar con AWS:\n\n${result.message}\n\nPosibles causas:\n• Credenciales incorrectas\n• Endpoint inválido\n• Problemas de red\n\nRevisa los logs para más detalles.`,
        [{ text: 'OK' }]
      );
    }
  } catch (error) {
    console.log('❌ [HomeScreen] Error en testAPIConnection:', error);
    Alert.alert(
      '❌ Error Inesperado', 
      `Error: ${error.message}`,
      [{ text: 'OK' }]
    );
  }
};

// Función para cargar datos reales
const loadRealData = async () => {
  try {
    if (!amplifyConfigured) {
      Alert.alert('⚠️ Amplify no configurado', 'Configura Amplify primero');
      return;
    }

    Alert.alert('🔄 Cargando...', 'Obteniendo barcos reales de AWS...');
    
    const boats = await AmplifyService.getBoats();
    
    if (boats.length > 0) {
      Alert.alert(
        '📋 Datos Reales Cargados', 
        `✅ Se encontraron ${boats.length} barcos en la base de datos.\n\nEjemplos:\n${boats.slice(0, 3).map(boat => `• ${boat.name} - $${boat.pricePerDay}/día`).join('\n')}\n\n🚀 Próximo paso: Reemplazar datos mock`,
        [{ text: 'OK' }]
      );
    } else {
      Alert.alert(
        '📋 Base de Datos Vacía', 
        'No se encontraron barcos en la base de datos.\n\n💡 Puedes crear barcos de prueba desde la consola de AWS o usar el botón "Crear Barco de Prueba".',
        [{ text: 'OK' }]
      );
    }
    
    console.log('📊 [HomeScreen] Barcos reales:', boats);
  } catch (error) {
    console.log('❌ [HomeScreen] Error cargando datos:', error);
    Alert.alert('❌ Error', `No se pudieron cargar los datos: ${error.message}`);
  }
};

// Función para crear un barco de prueba
const createTestBoat = async () => {
  try {
    if (!amplifyConfigured) {
      Alert.alert('⚠️ Amplify no configurado', 'Configura Amplify primero');
      return;
    }

    Alert.alert('🔄 Creando...', 'Creando barco de prueba en AWS...');
    
    const newBoat = await AmplifyService.createSampleBoat();
    
    Alert.alert(
      '✅ Barco Creado', 
      `¡Barco de prueba creado exitosamente!\n\n🛥️ ${newBoat.name}\n💰 $${newBoat.pricePerDay}/día\n📍 ${newBoat.location.marina}\n\nAhora puedes usar "Cargar Datos Reales" para verlo.`,
      [{ text: 'Genial!' }]
    );
  } catch (error) {
    console.log('❌ [HomeScreen] Error creando barco:', error);
    Alert.alert('❌ Error', `No se pudo crear el barco: ${error.message}`);
  }
};

// Datos de ejemplo (mock) - próximamente se reemplazarán por datos reales
const featuredBoats = [
  {
    id: '1',
    name: 'Sea Explorer',
    location: 'Puerto Marina',
    price: 150,
    rating: 4.8,
    image: '🛥️',
    reviews: 24
  },
  {
    id: '2',
    name: 'Ocean Breeze',
    location: 'Bahía Azul', 
    price: 200,
    rating: 4.9,
    image: '⛵',
    reviews: 18
  },
  {
    id: '3',
    name: 'Wave Rider',
    location: 'Costa Norte',
    price: 120,
    rating: 4.7,
    image: '🚤',
    reviews: 31
  }
];

function BoatCard({ boat, onPress }) {
  return (
    <TouchableOpacity style={styles.boatCard} onPress={() => onPress(boat)}>
      <View style={styles.boatImageContainer}>
        <Text style={styles.boatEmoji}>{boat.image}</Text>
      </View>
      
      <View style={styles.boatInfo}>
        <Text style={styles.boatName}>{boat.name}</Text>
        <Text style={styles.boatLocation}>📍 {boat.location}</Text>
        
        <View style={styles.boatDetails}>
          <Text style={styles.boatPrice}>${boat.price}/día</Text>
          <View style={styles.ratingContainer}>
            <Text style={styles.ratingStar}>⭐</Text>
            <Text style={styles.ratingText}>{boat.rating}</Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

function QuickActionCard({ icon, title, subtitle, onPress }) {
  return (
    <TouchableOpacity style={styles.actionCard} onPress={onPress}>
      <Text style={styles.actionIcon}>{icon}</Text>
      <Text style={styles.actionTitle}>{title}</Text>
      <Text style={styles.actionSubtitle}>{subtitle}</Text>
    </TouchableOpacity>
  );
}

// Componente de estado de Amplify
function AmplifyStatusCard() {
  return (
    <View style={styles.amplifyCard}>
      <Text style={styles.amplifyTitle}>🔗 Estado de AWS Amplify</Text>
      <Text style={[styles.amplifyStatus, amplifyConfigured ? styles.amplifySuccess : styles.amplifyPending]}>
        {amplifyConfigured ? '✅ Configurado y Conectado' : '⏳ No Configurado'}
      </Text>
      
      <View style={styles.amplifyButtons}>
        <TouchableOpacity style={styles.configButton} onPress={configureAmplifyAsync}>
          <Text style={styles.configButtonText}>⚙️ Configurar</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.testButton} onPress={testAPIConnection}>
          <Text style={styles.testButtonText}>🔗 Probar API</Text>
        </TouchableOpacity>
      </View>
      
      <View style={styles.amplifyButtons}>
        <TouchableOpacity style={styles.dataButton} onPress={loadRealData}>
          <Text style={styles.dataButtonText}>📊 Cargar Datos</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.createButton} onPress={createTestBoat}>
          <Text style={styles.createButtonText}>🔨 Crear Barco</Text>
        </TouchableOpacity>
      </View>
      
      <Text style={styles.amplifyInfo}>
        Importación estática • AmplifyService.js • API.ts
      </Text>
    </View>
  );
}

export default function HomeScreen() {
  const handleBoatPress = (boat) => {
    Alert.alert(
      boat.name,
      `Ubicación: ${boat.location}\nPrecio: $${boat.price}/día\nRating: ⭐ ${boat.rating}`,
      [
        { text: 'Ver Detalles', onPress: () => console.log('Ver detalles:', boat.id) },
        { text: 'Cerrar', style: 'cancel' }
      ]
    );
  };

  const handleQuickAction = (action) => {
    Alert.alert('Acción', `Función "${action}" en desarrollo`);
  };

  console.log('✅ HomeScreen cargado - Rutas corregidas definitivamente');

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.welcomeText}>¡Bienvenido! 👋</Text>
        <Text style={styles.subtitle}>Encuentra el barco perfecto para tu aventura</Text>
      </View>

      {/* Estado de Amplify */}
      <AmplifyStatusCard />

      {/* Barcos Destacados */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🛥️ Barcos Destacados (Mock)</Text>
        
        {featuredBoats.map((boat) => (
          <BoatCard 
            key={boat.id} 
            boat={boat} 
            onPress={handleBoatPress}
          />
        ))}
      </View>

      {/* Acción Rápida */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>⚡ Reserva Rápida</Text>
        
        <QuickActionCard
          icon="🔍"
          title="Buscar Barcos Disponibles"
          subtitle="Encuentra opciones para hoy"
          onPress={() => handleQuickAction('Buscar')}
        />
      </View>

      {/* Espaciado final */}
      <View style={styles.footer} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    padding: 20,
    backgroundColor: '#0066CC',
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#e3f2fd',
  },
  
  // ESTILOS PARA AMPLIFY CARD
  amplifyCard: {
    margin: 20,
    padding: 16,
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: amplifyConfigured ? '#28a745' : '#ffc107',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  amplifyTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
    textAlign: 'center',
  },
  amplifyStatus: {
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 12,
  },
  amplifySuccess: {
    color: '#28a745',
  },
  amplifyPending: {
    color: '#ffc107',
  },
  amplifyButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 10,
  },
  configButton: {
    backgroundColor: '#6f42c1',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
    flex: 0.45,
  },
  configButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  testButton: {
    backgroundColor: '#0066CC',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
    flex: 0.45,
  },
  testButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  dataButton: {
    backgroundColor: '#28a745',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
    flex: 0.45,
  },
  dataButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  createButton: {
    backgroundColor: '#fd7e14',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
    flex: 0.45,
  },
  createButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  amplifyInfo: {
    fontSize: 11,
    color: '#666',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  
  // ESTILOS ORIGINALES
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  boatCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginBottom: 12,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  boatImageContainer: {
    marginRight: 16,
    justifyContent: 'center',
  },
  boatEmoji: {
    fontSize: 48,
  },
  boatInfo: {
    flex: 1,
    justifyContent: 'space-between',
  },
  boatName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  boatLocation: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  boatDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  boatPrice: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#0066CC',
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ratingStar: {
    fontSize: 16,
    marginRight: 4,
  },
  ratingText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  actionCard: {
    backgroundColor: '#fff',
    marginHorizontal: 20,
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionIcon: {
    fontSize: 40,
    marginBottom: 12,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
    textAlign: 'center',
  },
  actionSubtitle: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  footer: {
    height: 20,
  },
});
