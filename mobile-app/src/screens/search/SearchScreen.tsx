import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Image,
} from 'react-native';
import {
  Text,
  Card,
  Title,
  Paragraph,
  Searchbar,
  Chip,
  Button,
  Modal,
  Portal,
  Surface,
} from 'react-native-paper';
import { CustomSlider } from '../../components/CustomSlider';
import { useAppDispatch } from '../../store/hooks';
import { AppDispatch, RootState } from '../../store/store';
import { fetchBoats, setFilters, Boat } from '../../store/slices/boatsSlice';
import { useAppSelector } from '../../store/hooks';
interface Props {
  navigation: any;
  route: any;
}

// ✅ Definir el tipo localmente para evitar problemas de importación
interface LocalBoatFilters {
  state: string;
  type: string;
  priceRange: [number, number];
  capacity: number;
  search: string;
}

const auth = useAppSelector(state => state.auth);
const STATES = ['Nueva Esparta', 'Vargas', 'Falcón', 'Sucre'];
const BOAT_TYPES = [
  { value: 'yacht', label: 'Yates' },
  { value: 'sailboat', label: 'Veleros' },
  { value: 'motorboat', label: 'Lanchas' },
  { value: 'catamaran', label: 'Catamaranes' },
  { value: 'jetski', label: 'Motos de Agua' },
];

export function SearchScreen({ navigation, route }: Props) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [tempFilters, setTempFilters] = useState<LocalBoatFilters>({
    state: '',
    type: '',
    priceRange: [0, 1000],
    capacity: 1,
    search: '',
  });

  const dispatch = useAppDispatch();
  const { boats, isLoading, filters } = useAppSelector((state: RootState) => state.boats);

  useEffect(() => {
    if (route.params) {
      const newFilters = { ...filters, ...route.params };
      dispatch(setFilters(newFilters));
      setTempFilters(newFilters as LocalBoatFilters);
    }
    dispatch(fetchBoats(filters));
  }, []);

  const handleSearch = () => {
    // ✅ Usar casting para evitar errores de TypeScript
    const updatedFilters = { ...filters, search: searchQuery } as any;
    dispatch(setFilters(updatedFilters));
    dispatch(fetchBoats(updatedFilters));
  };

  const applyFilters = () => {
    dispatch(setFilters(tempFilters as any));
    dispatch(fetchBoats(tempFilters));
    setShowFilters(false);
  };

  const clearFilters = () => {
    const emptyFilters: LocalBoatFilters = {
      state: '',
      type: '',
      priceRange: [0, 1000],
      capacity: 1,
      search: '',
    };
    setTempFilters(emptyFilters);
    dispatch(setFilters(emptyFilters as any));
    dispatch(fetchBoats(emptyFilters));
    setShowFilters(false);
  };

  const renderBoatItem = ({ item }: { item: Boat }) => (
    <TouchableOpacity
      onPress={() => navigation.navigate('BoatDetails', { boatId: item.id })}
    >
      <Card style={styles.boatCard}>
        <View style={styles.cardContent}>
          <Image source={{ uri: item.images[0] }} style={styles.boatImage} />
          <View style={styles.boatInfo}>
            <Title style={styles.boatName}>{item.name}</Title>
            <Paragraph style={styles.boatLocation}>
              📍 {item.location.marina}, {item.location.state}
            </Paragraph>
            <View style={styles.boatDetails}>
              <Chip icon="account-group" compact style={styles.capacityChip}>
                {item.capacity}
              </Chip>
              <Text style={styles.boatType}>
                {BOAT_TYPES.find(t => t.value === item.type)?.label}
              </Text>
            </View>
            <View style={styles.priceRow}>
              <Text style={styles.price}>${item.pricePerHour}/hora</Text>
              <View style={styles.rating}>
                <Text style={styles.ratingText}>⭐ {item.rating}</Text>
              </View>
            </View>
          </View>
        </View>
      </Card>
    </TouchableOpacity>
  );

  const activeFiltersCount = Object.values(filters).filter(value =>
    value && value !== '' && (Array.isArray(value) ? value[0] !== 0 || value[1] !== 1000 : true)
  ).length;

  return (
    <View style={styles.container}>
      {/* Search Header */}
      <View style={styles.searchHeader}>
        <Searchbar
          placeholder="Buscar botes, yates, lanchas..."
          onChangeText={setSearchQuery}
          value={searchQuery}
          onSubmitEditing={handleSearch}
          style={styles.searchbar}
        />
        <Button
          mode="outlined"
          onPress={() => setShowFilters(true)}
          style={styles.filterButton}
          icon="filter-variant"
        >
          Filtros {activeFiltersCount > 0 && `(${activeFiltersCount})`}
        </Button>
      </View>

      {/* Active Filters */}
      {activeFiltersCount > 0 && (
        <View style={styles.activeFilters}>
          {filters.state && (
            <Chip
              onClose={() => dispatch(setFilters({ ...filters, state: '' } as any))}
              style={styles.filterChip}
            >
              📍 {filters.state}
            </Chip>
          )}
          {filters.type && (
            <Chip
              onClose={() => dispatch(setFilters({ ...filters, type: '' } as any))}
              style={styles.filterChip}
            >
              🛥️ {BOAT_TYPES.find(t => t.value === filters.type)?.label}
            </Chip>
          )}
          {(filters.capacity && filters.capacity > 1) && (
            <Chip
              onClose={() => dispatch(setFilters({ ...filters, capacity: 1 } as any))}
              style={styles.filterChip}
            >
              👥 {filters.capacity}+ personas
            </Chip>
          )}
          {(filters as any).search && (
            <Chip
              onClose={() => dispatch(setFilters({ ...filters, search: '' } as any))}
              style={styles.filterChip}
            >
              🔍 "{(filters as any).search}"
            </Chip>
          )}
        </View>
      )}

      {/* Results */}
      <FlatList
        data={boats}
        renderItem={renderBoatItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.resultsList}
        showsVerticalScrollIndicator={false}
        refreshing={isLoading}
        onRefresh={() => dispatch(fetchBoats(filters))}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>🔍 No se encontraron embarcaciones</Text>
            <Text style={styles.emptySubtext}>
              Intenta ajustar tus filtros de búsqueda
            </Text>
          </View>
        }
      />

      {/* Filters Modal */}
      <Portal>
        <Modal
          visible={showFilters}
          onDismiss={() => setShowFilters(false)}
          contentContainerStyle={styles.modalContainer}
        >
          <Surface style={styles.filtersModal}>
            <Title style={styles.modalTitle}>Filtros de Búsqueda</Title>

            {/* State Filter */}
            <View style={styles.filterSection}>
              <Text style={styles.filterLabel}>Estado</Text>
              <View style={styles.chipContainer}>
                {STATES.map((state) => (
                  <Chip
                    key={state}
                    selected={tempFilters.state === state}
                    onPress={() => setTempFilters({
                      ...tempFilters,
                      state: tempFilters.state === state ? '' : state
                    })}
                    style={styles.filterOptionChip}
                  >
                    {state}
                  </Chip>
                ))}
              </View>
            </View>

            {/* Boat Type Filter */}
            <View style={styles.filterSection}>
              <Text style={styles.filterLabel}>Tipo de Embarcación</Text>
              <View style={styles.chipContainer}>
                {BOAT_TYPES.map((type) => (
                  <Chip
                    key={type.value}
                    selected={tempFilters.type === type.value}
                    onPress={() => setTempFilters({
                      ...tempFilters,
                      type: tempFilters.type === type.value ? '' : type.value
                    })}
                    style={styles.filterOptionChip}
                  >
                    {type.label}
                  </Chip>
                ))}
              </View>
            </View>

            {/* Price Range */}
            <View style={styles.filterSection}>
              <Text style={styles.filterLabel}>
                Precio por hora: ${tempFilters.priceRange[0]} - ${tempFilters.priceRange[1]}
              </Text>
              <CustomSlider
                style={styles.slider}
                minimumValue={0}
                maximumValue={1000}
                value={tempFilters.priceRange[1]}
                onValueChange={(value: number) => setTempFilters({
                  ...tempFilters,
                  priceRange: [tempFilters.priceRange[0], Math.round(value)]
                })}
                step={50}
                minimumTrackTintColor="#0066CC"
                maximumTrackTintColor="#d3d3d3"
              />
            </View>

            {/* Capacity */}
            <View style={styles.filterSection}>
              <Text style={styles.filterLabel}>
                Capacidad mínima: {tempFilters.capacity} personas
              </Text>
              <CustomSlider
                style={styles.slider}
                minimumValue={1}
                maximumValue={20}
                value={tempFilters.capacity}
                onValueChange={(value: number) => setTempFilters({
                  ...tempFilters,
                  capacity: Math.round(value)
                })}
                step={1}
                minimumTrackTintColor="#0066CC"
                maximumTrackTintColor="#d3d3d3"
              />
            </View>

            {/* Modal Actions */}
            <View style={styles.modalActions}>
              <Button
                mode="outlined"
                onPress={clearFilters}
                style={styles.modalButton}
              >
                Limpiar
              </Button>
              <Button
                mode="contained"
                onPress={applyFilters}
                style={styles.modalButton}
              >
                Aplicar
              </Button>
            </View>
          </Surface>
        </Modal>
      </Portal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  searchHeader: {
    flexDirection: 'row',
    padding: 16,
    paddingTop: 60,
    gap: 12,
  },
  searchbar: {
    flex: 1,
  },
  filterButton: {
    alignSelf: 'center',
  },
  activeFilters: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
    paddingBottom: 8,
    gap: 8,
  },
  filterChip: {
    backgroundColor: '#E3F2FD',
  },
  resultsList: {
    padding: 16,
  },
  boatCard: {
    marginBottom: 16,
    elevation: 2,
  },
  cardContent: {
    flexDirection: 'row',
    padding: 12,
  },
  boatImage: {
    width: 100,
    height: 100,
    borderRadius: 8,
  },
  boatInfo: {
    flex: 1,
    marginLeft: 12,
  },
  boatName: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  boatLocation: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  boatDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  capacityChip: {
    backgroundColor: '#E8F5E8',
  },
  boatType: {
    fontSize: 12,
    color: '#666',
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  price: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#0066CC',
  },
  rating: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ratingText: {
    fontSize: 14,
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
  },
  modalContainer: {
    margin: 20,
  },
  filtersModal: {
    padding: 20,
    borderRadius: 12,
    maxHeight: '80%',
  },
  modalTitle: {
    textAlign: 'center',
    marginBottom: 20,
  },
  filterSection: {
    marginBottom: 20,
  },
  filterLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  filterOptionChip: {
    marginBottom: 8,
  },
  slider: {
    marginTop: 8,
    height: 40,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
    gap: 12,
  },
  modalButton: {
    flex: 1,
  },
});