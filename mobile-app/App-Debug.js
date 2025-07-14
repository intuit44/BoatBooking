import React, { useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';

// NO importar Amplify por ahora para aislar el error

// Función de prueba simple sin API
const testBasicFunction = () => {
  try {
    Alert.alert(
      '✅ App Funcionando', 
      'La app básica funciona correctamente.\n\nError está en la configuración de Amplify.',
      [{ text: 'OK' }]
    );
    console.log('✅ Función básica funciona');
  } catch (error) {
    Alert.alert('❌ Error básico', error.message);
    console.log('❌ Error en función básica:', error);
  }
};

// Componente simple de prueba
function TestScreen({ title, emoji, subtitle }) {
  return (
    <View style={styles.screen}>
      <Text style={styles.emoji}>{emoji}</Text>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
      
      {title === 'Inicio' && (
        <View style={styles.buttonContainer}>
          <TouchableOpacity 
            style={styles.testButton}
            onPress={testBasicFunction}
          >
            <Text style={styles.testButtonText}>🧪 Prueba Básica</Text>
          </TouchableOpacity>
          
          <Text style={styles.infoText}>
            Versión de debug - sin Amplify
          </Text>
        </View>
      )}
    </View>
  );
}

function SimpleNavigator() {
  const [currentScreen, setCurrentScreen] = React.useState('home');

  useEffect(() => {
    console.log('🚀 App de DEBUG iniciada correctamente');
  }, []);

  const renderScreen = () => {
    switch (currentScreen) {
      case 'home':
        return <TestScreen title="Inicio" emoji="🏠" subtitle="Debug - Sin Amplify" />;
      case 'search':
        return <TestScreen title="Buscar" emoji="🔍" subtitle="Pantalla de prueba" />;
      case 'bookings':
        return <TestScreen title="Reservas" emoji="📅" subtitle="Pantalla de prueba" />;
      case 'profile':
        return <TestScreen title="Perfil" emoji="👤" subtitle="Pantalla de prueba" />;
      default:
        return <TestScreen title="Inicio" emoji="🏠" subtitle="Debug - Sin Amplify" />;
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
  console.log('🧪 App DEBUG - Versión simplificada sin Amplify');
  
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
    backgroundColor: '#28a745',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 20,
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
