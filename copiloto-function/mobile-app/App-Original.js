import React, { useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import './amplify-config'; // Configurar Amplify
import BoatRentalAPI from './src/services/api';

// Importar las 4 pantallas migradas
let HomeScreen, SearchScreen, BookingsScreen, ProfileScreen;

try {
  HomeScreen = require('./src/screens/home/HomeScreen').default;
  console.log('✅ HomeScreen importado correctamente');
} catch (error) {
  console.log('⚠️ HomeScreen no encontrado, usando versión simple');
  HomeScreen = null;
}

try {
  SearchScreen = require('./src/screens/search/SearchScreen').default;
  console.log('✅ SearchScreen importado correctamente');
} catch (error) {
  console.log('⚠️ SearchScreen no encontrado, usando versión simple');
  SearchScreen = null;
}

try {
  BookingsScreen = require('./src/screens/bookings/BookingsScreen').default;
  console.log('✅ BookingsScreen importado correctamente');
} catch (error) {
  console.log('⚠️ BookingsScreen no encontrado, usando versión simple');
  BookingsScreen = null;
}

try {
  ProfileScreen = require('./src/screens/profile/ProfileScreen').default;
  console.log('✅ ProfileScreen importado correctamente');
} catch (error) {
  console.log('⚠️ ProfileScreen no encontrado, usando versión simple');
  ProfileScreen = null;
}

// Función para probar la conexión API
const testAPIConnection = async () => {
  try {
    Alert.alert('🔄 Probando...', 'Conectando con AWS Amplify...');
    
    const result = await BoatRentalAPI.testConnection();
    
    if (result.success) {
      Alert.alert(
        '✅ Conexión Exitosa', 
        'La app se conectó correctamente a AWS Amplify!\n\nPuedes revisar los logs en la consola.',
        [{ text: 'Genial!' }]
      );
    } else {
      Alert.alert(
        '❌ Error de Conexión', 
        result.message + '\n\nRevisa la configuración de AWS.',
        [{ text: 'OK' }]
      );
    }
  } catch (error) {
    Alert.alert(
      '❌ Error', 
      `Error inesperado: ${error.message}`,
      [{ text: 'OK' }]
    );
  }
};

// Componente simple como fallback
function SimpleScreen({ title, emoji, subtitle }) {
  return (
    <View style={styles.screen}>
      <Text style={styles.emoji}>{emoji}</Text>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
      
      {/* Botón de prueba API solo en HomeScreen */}
      {title === 'Inicio' && (
        <View style={styles.buttonContainer}>
          <TouchableOpacity 
            style={styles.testButton}
            onPress={testAPIConnection}
          >
            <Text style={styles.testButtonText}>🔗 Probar Conexión API</Text>
          </TouchableOpacity>
          
          <Text style={styles.infoText}>
            Toca para probar la conexión con AWS Amplify
          </Text>
        </View>
      )}
    </View>
  );
}

function SimpleNavigator() {
  const [currentScreen, setCurrentScreen] = React.useState('home');

  // Probar conexión al iniciar la app
  useEffect(() => {
    console.log('🚀 App iniciada - Amplify configurado');
    // Dar tiempo para que la app se estabilice antes de probar
    setTimeout(async () => {
      console.log('🔗 Probando conexión automática...');
      try {
        const result = await BoatRentalAPI.testConnection();
        console.log('📊 Resultado conexión automática:', result);
      } catch (error) {
        console.log('⚠️ Error en conexión automática:', error.message);
      }
    }, 3000);
  }, []);

  const renderScreen = () => {
    switch (currentScreen) {
      case 'home':
        return HomeScreen ? <HomeScreen /> : <SimpleScreen title="Inicio" emoji="🏠" subtitle="Bienvenido a Boat Rental" />;
      case 'search':
        return SearchScreen ? <SearchScreen /> : <SimpleScreen title="Buscar" emoji="🔍" subtitle="Encuentra tu barco ideal" />;
      case 'bookings':
        return BookingsScreen ? <BookingsScreen /> : <SimpleScreen title="Reservas" emoji="📅" subtitle="Tus reservas activas" />;
      case 'profile':
        return ProfileScreen ? <ProfileScreen /> : <SimpleScreen title="Perfil" emoji="👤" subtitle="Tu información personal" />;
      default:
        return <SimpleScreen title="Inicio" emoji="🏠" subtitle="Bienvenido a Boat Rental" />;
    }
  };

  const tabs = [
    { key: 'home', title: 'Inicio', emoji: '🏠' },
    { key: 'search', title: 'Buscar', emoji: '🔍' },
    { key: 'bookings', title: 'Reservas', emoji: '📅' },
    { key: 'profile', title: 'Perfil', emoji: '👤' }
  ];

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        {renderScreen()}
      </View>
      
      <View style={styles.tabBar}>
        {tabs.map((tab) => {
          const isActive = currentScreen === tab.key;
          
          return (
            <TouchableOpacity
              key={tab.key}
              style={[styles.tab, isActive && styles.activeTab]}
              onPress={() => setCurrentScreen(tab.key)}
            >
              <Text style={[styles.tabEmoji, isActive && styles.activeTabEmoji]}>
                {tab.emoji}
              </Text>
              <Text style={[styles.tabText, isActive && styles.activeTabText]}>
                {tab.title}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

export default function App() {
  console.log('🚀 App COMPLETO + AMPLIFY - Fase 1 Lista');
  
  return <SimpleNavigator />;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
  },
  screen: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  emoji: {
    fontSize: 80,
    marginBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#0066CC',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 30,
  },
  buttonContainer: {
    alignItems: 'center',
  },
  testButton: {
    backgroundColor: '#0066CC',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  testButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  infoText: {
    fontSize: 12,
    color: '#999',
    marginTop: 10,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    paddingVertical: 8,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 8,
  },
  activeTab: {
    backgroundColor: '#f0f8ff',
  },
  tabEmoji: {
    fontSize: 24,
    marginBottom: 4,
  },
  activeTabEmoji: {
    fontSize: 26,
  },
  tabText: {
    fontSize: 12,
    color: '#666',
  },
  activeTabText: {
    color: '#0066CC',
    fontWeight: 'bold',
  },
});
