import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  FlatList
} from 'react-native';

// Datos de barcos expandidos para búsqueda
const allBoats = [
  { id: '1', name: 'Sea Explorer', price: 150, type: 'Yate', capacity: 8, location: 'Puerto Marina', image: '🛥️', rating: 4.8 },
  { id: '2', name: 'Ocean Breeze', price: 200, type: 'Velero', capacity: 6, location: 'Bahía Azul', image: '⛵', rating: 4.9 },
  { id: '3', name: 'Wave Rider', price: 120, type: 'Lancha', capacity: 4, location: 'Costa Norte', image: '🚤', rating: 4.7 },
  { id: '4', name: 'Blue Horizon', price: 180, type: 'Catamarán', capacity: 12, location: 'Puerto Marina', image: '⛵', rating: 4.6 },
  { id: '5', name: 'Speed Demon', price: 250, type: 'Lancha', capacity: 6, location: 'Bahía Azul', image: '🚤', rating: 4.8 },
  { id: '6', name: 'Calm Waters', price: 90, type: 'Velero', capacity: 4, location: 'Costa Norte', image: '⛵', rating: 4.5 },
];

function BoatSearchCard({ boat, onPress }) {
  return (
    <TouchableOpacity style={styles.boatCard} onPress={onPress}>
      <Text style={styles.boatEmoji}>{boat.image}</Text>
      <View style={styles.boatInfo}>
        <View style={styles.boatHeader}>
          <Text style={styles.boatName}>{boat.name}</Text>
          <Text style={styles.boatPrice}>${boat.price}/día</Text>
        </View>
        <Text style={styles.boatType}>{boat.type} • {boat.capacity} personas</Text>
        <Text style={styles.boatLocation}>📍 {boat.location}</Text>
        <Text style={styles.boatRating}>⭐ {boat.rating}</Text>
      </View>
    </TouchableOpacity>
  );
}

export default function SearchScreen() {
  const [searchText, setSearchText] = useState('');
  const [selectedType, setSelectedType] = useState('Todos');
  const [maxPrice, setMaxPrice] = useState('');

  // Filtrar barcos
  const filteredBoats = allBoats.filter(boat => {
    const matchesSearch = boat.name.toLowerCase().includes(searchText.toLowerCase()) ||
                         boat.location.toLowerCase().includes(searchText.toLowerCase());
    const matchesType = selectedType === 'Todos' || boat.type === selectedType;
    const matchesPrice = !maxPrice || boat.price <= parseInt(maxPrice);
    
    return matchesSearch && matchesType && matchesPrice;
  });

  const boatTypes = ['Todos', 'Yate', 'Velero', 'Lancha', 'Catamarán'];

  console.log('✅ SearchScreen cargado correctamente');

  return (
    <ScrollView style={styles.container}>
      {/* Header de búsqueda */}
      <View style={styles.header}>
        <Text style={styles.title}>🔍 Buscar Barcos</Text>
        <Text style={styles.subtitle}>Encuentra tu aventura perfecta</Text>
      </View>

      {/* Formulario de búsqueda */}
      <View style={styles.searchForm}>
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Nombre o Ubicación</Text>
          <TextInput
            style={styles.textInput}
            placeholder="Ej: Sea Explorer, Puerto Marina..."
            value={searchText}
            onChangeText={setSearchText}
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Tipo de Barco</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.typeButtons}>
              {boatTypes.map(type => (
                <TouchableOpacity
                  key={type}
                  style={[
                    styles.typeButton,
                    selectedType === type && styles.selectedTypeButton
                  ]}
                  onPress={() => setSelectedType(type)}
                >
                  <Text style={[
                    styles.typeButtonText,
                    selectedType === type && styles.selectedTypeButtonText
                  ]}>
                    {type}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Precio Máximo ($/día)</Text>
          <TextInput
            style={styles.textInput}
            placeholder="Ej: 200"
            value={maxPrice}
            onChangeText={setMaxPrice}
            keyboardType="numeric"
          />
        </View>
      </View>

      {/* Resultados */}
      <View style={styles.results}>
        <Text style={styles.resultsTitle}>
          📊 {filteredBoats.length} barcos encontrados
        </Text>
        
        {filteredBoats.map(boat => (
          <BoatSearchCard
            key={boat.id}
            boat={boat}
            onPress={() => console.log('Barco seleccionado:', boat.name)}
          />
        ))}

        {filteredBoats.length === 0 && (
          <View style={styles.noResults}>
            <Text style={styles.noResultsText}>😔 No se encontraron barcos</Text>
            <Text style={styles.noResultsSubtext}>Intenta ajustar tus filtros</Text>
          </View>
        )}
      </View>
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
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#e3f2fd',
  },
  searchForm: {
    padding: 20,
    backgroundColor: '#fff',
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  typeButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  typeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#0066CC',
    backgroundColor: '#fff',
  },
  selectedTypeButton: {
    backgroundColor: '#0066CC',
  },
  typeButtonText: {
    color: '#0066CC',
    fontWeight: 'bold',
  },
  selectedTypeButtonText: {
    color: '#fff',
  },
  results: {
    padding: 20,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  boatCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  boatEmoji: {
    fontSize: 40,
    marginRight: 16,
  },
  boatInfo: {
    flex: 1,
  },
  boatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  boatName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  boatPrice: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#0066CC',
  },
  boatType: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  boatLocation: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  boatRating: {
    fontSize: 14,
    color: '#ff9800',
  },
  noResults: {
    alignItems: 'center',
    padding: 40,
  },
  noResultsText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 8,
  },
  noResultsSubtext: {
    fontSize: 14,
    color: '#999',
  },
});
