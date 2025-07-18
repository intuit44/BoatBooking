```tsx
import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  FlatList,
  ImageBackground,
  StatusBar,
  Animated,
  Text,
} from 'react-native';
import { Searchbar, Button, Surface } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { fetchFeaturedBoats, fetchBoats, setFilters, Boat } from '../../store/slices/boatsSlice';

const HERO_IMAGE = 'https://images.unsplash.com/photo-1567899378494-47b22a2ae96a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80';

const BOAT_CATEGORIES = [
  // ...
];

const MARINA_LOCATIONS = [
  // ...
];

const QUICK_FILTERS = [
  // ...
];

export const HomeScreen = () => {
  const navigation = useNavigation<HomeScreenNavigationProp>();
  const dispatch = useAppDispatch();
  const { featuredBoats, boats, isLoading, filters } = useAppSelector(state => state.boats);

  const { user } = useAppSelector((state: RootState) => state.auth);
  const [searchQuery, setSearchQuery] = useState('');
  const [heartAnimations, setHeartAnimations] = useState<Record<string, boolean>>({});

  const screenData = Dimensions.get('window');
  const screenWidth = screenData.width;
  const screenHeight = screenData.height;

  const [showGreeting, setShowGreeting] = useState(true);
  const fadeAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    dispatch(fetchFeaturedBoats());
    dispatch(fetchBoats({}));
  }, [dispatch]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }).start(() => setShowGreeting(false));
    }, 5000);

    return () => clearTimeout(timeout);
  }, []);

  // ...

  const renderBoatCategory = ({ item }: { item: typeof BOAT_CATEGORIES[number] }) => (
    // ...
  );

  const renderFeaturedBoat = ({ item }: { item: Boat }) => (
    // ...
  );

  const renderMarinaLocation = ({ item }: { item: typeof MARINA_LOCATIONS[number] }) => (
    // ...
  );

  const renderRecentBoat = ({ item }: { item: Boat }) => (
    // ...
  );

  return (
    <View style={[styles.container, { position: 'relative' }]}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />

      {/* SearchBar ABSOLUTO, fuera del ScrollView */}
      <View style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 10,
        paddingHorizontal: 24,
        paddingTop: StatusBar.currentHeight || 40,
      }}>
        <Surface style={styles.heroSearchSurface} elevation={4}>
          <TouchableOpacity
            style={styles.heroSearchButton}
            onPress={() => navigation.navigate('Search')}
            activeOpacity={0.9}
          >
            <View style={styles.heroSearchContent}>
              <View style={styles.heroSearchIcon}>
                <Text style={styles.searchIconText}>🔍</Text>
              </View>
              <View style={styles.heroSearchText}>
                <Text style={styles.heroSearchPlaceholder}>¿A dónde quieres navegar?</Text>
              </View>
            </View>
          </TouchableOpacity>
        </Surface>
      </View>

      {/* Título debajo del buscador, sobre fondo blanco y SIEMPRE visible */}
      {/* Saludo flotante animado que desaparece */}
      {showGreeting && (
        <Animated.View
          style={{
            position: 'absolute',
            top: (StatusBar.currentHeight || 40) + 20,
            left: 20,
            right: 20,
            zIndex: 99,
            opacity: fadeAnim,
          }}
        >
          <View
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              padding: 12,
              borderRadius: 12,
              alignItems: 'center',
              shadowColor: '#000',
              shadowOffset: { width: 0, height: 3 },
              shadowOpacity: 0.2,
              shadowRadius: 4,
              elevation: 5,
            }}
          >
            <Text style={[styles.heroGreeting, {
              color: '#0066CC',
              fontWeight: '600',
              fontSize: 18,
              textAlign: 'center',
            }]}>
              {getGreeting()}, {user?.name || 'Navegante'}! {getTimeEmoji()}
            </Text>
          </View>
        </Animated.View>
      )}

      <ScrollView
        style={styles.scrollContent}
        contentContainerStyle={{ paddingTop: StatusBar.currentHeight ? StatusBar.currentHeight + 120 : 160 }}
        showsVerticalScrollIndicator={false}
      >
        {/* ... */}
      </ScrollView>
    </View>
  );
};

// Estilos y otros componentes...

// Exportación por defecto para compatibilidad
export default HomeScreen;
```