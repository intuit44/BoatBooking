import { useState } from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View
} from 'react-native';

// ✅ Interfaces para definir tipos
interface Boat {
  id: string;
  name: string;
  price: number;
  type: string;
  capacity: number;
  location: string;
  image: string;
  rating: number;
}

interface BoatSearchCardProps {
  boat: Boat;
  onPress: (boat: Boat) => void;
}

interface SearchScreenProps {
  navigation?: any; // Opcional si no siempre se pasa
}

// Datos de barcos expandidos para búsqueda
const allBoats: Boat[] = [
  { id: '1', name: 'Sea Explorer', price: 150, type: 'Yate', capacity: 8, location: 'Puerto Marina', image: '🛥️', rating: 4.8 },
  { id: '2', name: 'Ocean Breeze', price: 200, type: 'Velero', capacity: 6, location: 'Bahía Azul', image: '⛵', rating: 4.9 },
  { id: '3', name: 'Wave Rider', price: 120, type: 'Lancha', capacity: 4, location: 'Costa Norte', image: '🚤', rating: 4.7 },
  { id: '4', name: 'Blue Horizon', price: 180, type: 'Catamarán', capacity: 12, location: 'Puerto Marina', image: '⛵', rating: 4.6 },
  { id: '5', name: 'Speed Demon', price: 250, type: 'Lancha', capacity: 6, location: 'Bahía Azul', image: '🚤', rating: 4.8 },
  { id: '6', name: 'Calm Waters', price: 90, type: 'Velero', capacity: 4, location: 'Costa Norte', image: '⛵', rating: 4.5 },
];

// ✅ Componente BoatSearchCard con tipos explícitos
function BoatSearchCard({ boat, onPress }: BoatSearchCardProps) {
  return (
    <TouchableOpacity style={styles.boatCard} onPress={() => onPress(boat)}>
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

// ✅ Componente principal con tipos
export default function SearchScreen({ navigation }: SearchScreenProps = {}) {
  const [searchText, setSearchText] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('Todos');
  const [maxPrice, setMaxPrice] = useState<string>('');

  // ✅ Función de filtrado tipada
  const filteredBoats: Boat[] = allBoats.filter((boat: Boat) => {
    const matchesSearch = boat.name.toLowerCase().includes(searchText.toLowerCase()) ||
                         boat.location.toLowerCase().includes(searchText.toLowerCase());
    const matchesType = selectedType === 'Todos' || boat.type === selectedType;
    const matchesPrice = !maxPrice || boat.price <= parseInt(maxPrice);
    
    return matchesSearch && matchesType && matchesPrice;
  });

  const boatTypes: string[] = ['Todos', 'Yate', 'Velero', 'Lancha', 'Catamarán'];

  // ✅ Handler con tipo explícito
  const handleBoatPress = (boat: Boat): void => {
    console.log('Barco seleccionado:', boat.name);
    if (navigation) {
      navigation.navigate('BoatDetails', { boat });
    }
  };

  // ✅ Handler para tipo de barco con tipo explícito
  const handleTypeSelection = (type: string): void => {
    setSelectedType(type);
  };

  // ✅ Handler para búsqueda con tipo explícito
  const handleSearchChange = (text: string): void => {
    setSearchText(text);
  };

  // ✅ Handler para precio con tipo explícito
  const handlePriceChange = (text: string): void => {
    setMaxPrice(text);
  };

  // ✅ Función para limpiar filtros
  const clearFilters = (): void => {
    setSearchText('');
    setSelectedType('Todos');
    setMaxPrice('');
  };

  console.log('✅ SearchScreen cargado correctamente');

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
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
            onChangeText={handleSearchChange}
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Tipo de Barco</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.typeButtons}>
              {boatTypes.map((type: string) => (
                <TouchableOpacity
                  key={type}
                  style={[
                    styles.typeButton,
                    selectedType === type && styles.selectedTypeButton
                  ]}
                  onPress={() => handleTypeSelection(type)}
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
            onChangeText={handlePriceChange}
            keyboardType="numeric"
          />
        </View>

        {/* Botón para limpiar filtros */}
        {(searchText || selectedType !== 'Todos' || maxPrice) && (
          <TouchableOpacity style={styles.clearButton} onPress={clearFilters}>
            <Text style={styles.clearButtonText}>🗑️ Limpiar Filtros</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Resultados */}
      <View style={styles.results}>
        <View style={styles.resultsHeader}>
          <Text style={styles.resultsTitle}>
            📊 {filteredBoats.length} barcos encontrados
          </Text>
          {filteredBoats.length > 0 && (
            <Text style={styles.resultsSubtitle}>
              Precio promedio: ${Math.round(filteredBoats.reduce((acc, boat) => acc + boat.price, 0) / filteredBoats.length)}/día
            </Text>
          )}
        </View>
        
        {filteredBoats.map((boat: Boat) => (
          <BoatSearchCard
            key={boat.id}
            boat={boat}
            onPress={handleBoatPress}
          />
        ))}

        {filteredBoats.length === 0 && (
          <View style={styles.noResults}>
            <Text style={styles.noResultsEmoji}>😔</Text>
            <Text style={styles.noResultsText}>No se encontraron barcos</Text>
            <Text style={styles.noResultsSubtext}>
              Intenta ajustar tus filtros de búsqueda
            </Text>
            <TouchableOpacity style={styles.retryButton} onPress={clearFilters}>
              <Text style={styles.retryButtonText}>Mostrar Todos</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      {/* Footer con información adicional */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          💡 Tip: Usa filtros específicos para encontrar exactamente lo que buscas
        </Text>
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
  clearButton: {
    backgroundColor: '#f44336',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    marginTop: 10,
  },
  clearButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  results: {
    padding: 20,
  },
  resultsHeader: {
    marginBottom: 16,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  resultsSubtitle: {
    fontSize: 14,
    color: '#666',
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
  noResultsEmoji: {
    fontSize: 48,
    marginBottom: 16,
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
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 20,
  },
  retryButton: {
    backgroundColor: '#0066CC',
    borderRadius: 8,
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  retryButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  footer: {
    padding: 20,
    paddingTop: 0,
  },
  footerText: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    fontStyle: 'italic',
  },
});
