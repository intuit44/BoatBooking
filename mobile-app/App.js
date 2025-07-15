import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

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

// Componente simple como fallback
function SimpleScreen({ title, emoji, subtitle }) {
  return (
    <View style={styles.screen}>
      <Text style={styles.emoji}>{emoji}</Text>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
    </View>
  );
}

function SimpleNavigator() {
  const [currentScreen, setCurrentScreen] = React.useState('home');

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
  console.log('🚀 App SIMPLE - Sin configuración compleja de Amplify');
  
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
