// HomeScreen.tsx
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
} from 'react-native';
import {
  Text,
  Searchbar,
  Chip,
  Button,
  Surface,
  IconButton,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { RootState } from '../../store/store';
import { fetchFeaturedBoats, fetchBoats, setFilters, Boat } from '../../store/slices/boatsSlice';

// Importar componentes de animación (comentados si no existen aún)
// import { FadeInView } from '../../components/animations/FadeInView';
// import { SlideTransition } from '../../components/animations/SlideTransition';
// import { ScaleAnimation } from '../../components/animations/ScaleAnimation';

// Importar tipos de navegación (comentado si no existe aún)
// import { HomeScreenNavigationProp } from '../../types/navigation';

// Tipo temporal para navegación
type HomeScreenNavigationProp = {
  navigate: (screen: string, params?: any) => void;
};

// Componentes de animación temporales (reemplazar cuando tengas los reales)
const FadeInView = ({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) => (
  <View>{children}</View>
);
const SlideTransition = ({ children, direction, delay = 0 }: { children: React.ReactNode; direction: string; delay?: number }) => (
  <View>{children}</View>
);
const ScaleAnimation = ({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) => (
  <View>{children}</View>
);

// URLs de imágenes de alta calidad para hero y cards
const HERO_IMAGE = 'https://images.unsplash.com/photo-1567899378494-47b22a2ae96a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80';

const BOAT_CATEGORIES = [
  {
    id: 1,
    name: 'Yates',
    type: 'yacht',
    image: 'https://images.unsplash.com/photo-1558482877-26430d09215e?q=80&w=2574&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D'
  },
  {
    id: 2,
    name: 'Lanchas Deportivas',
    type: 'sailboat',
    image: 'https://images.unsplash.com/photo-1540946485063-a40da27545f8?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80'
  },
  {
    id: 3,
    name: 'Motos de Agua',
    type: 'motorboat',
    image: 'https://images.unsplash.com/photo-1545566239-0b2fb5c50bc6?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80'
  },
  {
    id: 4,
    name: 'Catamaranes',
    type: 'catamaran',
    image: 'https://images.unsplash.com/photo-1599640842225-85d111c60e6b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80'
  },
];

const MARINA_LOCATIONS = [
  {
    name: 'Margarita Island',
    state: 'Nueva Esparta',
    count: 45,
    image: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
  },
  {
    name: 'La Guaira Marina',
    state: 'Vargas',
    count: 32,
    image: 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
  },
  {
    name: 'Coro Bay',
    state: 'Falcón',
    count: 28,
    image: 'https://images.unsplash.com/photo-1527004013197-933c4bb611b3?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
  },
  {
    name: 'Cumaná Port',
    state: 'Sucre',
    count: 21,
    image: 'https://images.unsplash.com/photo-1514282401047-d79a71a590e8?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
  },
];

const QUICK_FILTERS = [
  { label: 'Familias', icon: '👨‍👩‍👧‍👦', filter: { capacity: 8 }, color: '#FF6B6B' },
  { label: 'Romántico', icon: '💕', filter: { capacity: 2 }, color: '#FF69B4' },
  { label: 'Aventura', icon: '🏄‍♂️', filter: { type: 'jetski' }, color: '#4ECDC4' },
  { label: 'Premium', icon: '✨', filter: { priceRange: [500, 1000] }, color: '#FFD93D' },
];

export const HomeScreen = () => {
  const navigation = useNavigation<HomeScreenNavigationProp>();
  const dispatch = useAppDispatch();
  const { featuredBoats, boats, isLoading, filters } = useAppSelector(state => state.boats);

  const { user } = useAppSelector((state: RootState) => state.auth as { user: any });
  const [searchQuery, setSearchQuery] = useState('');
  const [heartAnimations, setHeartAnimations] = useState<{ [key: string]: boolean }>({});

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


  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return '¡Buenos días';
    if (hour < 18) return '¡Buenas tardes';
    return '¡Buenas noches';
  };

  const getTimeEmoji = () => {
    const hour = new Date().getHours();
    if (hour < 12) return '🌅';
    if (hour < 18) return '☀️';
    return '🌙';
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      const searchFilters = { ...filters, search: searchQuery };
      dispatch(setFilters(searchFilters));
      navigation.navigate('Search', searchFilters);
    } else {
      navigation.navigate('Search');
    }
  };

  const handleBoatTypePress = (boatType: string) => {
    const typeFilters = { type: boatType };
    dispatch(setFilters(typeFilters));
    navigation.navigate('Search', typeFilters);
  };

  const handleStatePress = (state: string) => {
    const stateFilters = { state };
    dispatch(setFilters(stateFilters));
    navigation.navigate('Search', stateFilters);
  };

  const handleQuickFilter = (filter: any) => {
    dispatch(setFilters(filter));
    navigation.navigate('Search', filter);
  };

  const handleBoatPress = (boatId: string) => {
    navigation.navigate('BoatDetails', { boatId });
  };

  const toggleHeart = (boatId: string) => {
    setHeartAnimations(prev => ({
      ...prev,
      [boatId]: !prev[boatId]
    }));
  };

  const renderBoatCategory = ({ item }: { item: typeof BOAT_CATEGORIES[0] }) => (
    <ScaleAnimation delay={300}>
      <TouchableOpacity
        style={styles.categoryCard}
        onPress={() => handleBoatTypePress(item.type)}
        activeOpacity={0.9}
      >
        <ImageBackground
          source={{ uri: item.image }}
          style={styles.categoryImage}
          imageStyle={styles.categoryImageStyle}
        >
          <View style={styles.categoryOverlay}>
            <Text style={styles.categoryName}>{item.name}</Text>
            <Text style={styles.categoryCount}>
              {boats.filter(b => b.type === item.type).length} disponibles
            </Text>
          </View>
        </ImageBackground>
      </TouchableOpacity>
    </ScaleAnimation>
  );

  const renderFeaturedBoat = ({ item }: { item: Boat }) => (
    <ScaleAnimation delay={400}>
      <TouchableOpacity
        style={[styles.featuredCard, { width: screenWidth * 0.85 }]}
        onPress={() => handleBoatPress(item.id)}
        activeOpacity={0.95}
      >
        <ImageBackground
          source={{ uri: `https://picsum.photos/400/240?random=${item.id}` }}
          style={styles.featuredImage}
          imageStyle={styles.featuredImageStyle}
        >
          <View style={styles.featuredOverlay}>
            {/* Favorite Heart Animated */}
            <ScaleAnimation>
              <TouchableOpacity
                style={styles.heartContainer}
                onPress={() => toggleHeart(item.id)}
                activeOpacity={0.8}
              >
                <Text style={[
                  styles.heartIcon,
                  heartAnimations[item.id] && styles.heartIconFilled
                ]}>
                  {heartAnimations[item.id] ? '❤️' : '🤍'}
                </Text>
              </TouchableOpacity>
            </ScaleAnimation>

            {/* Guest Favorite Badge */}
            <View style={styles.guestFavoriteBadge}>
              <Text style={styles.guestFavoriteText}>Favorito entre huéspedes</Text>
            </View>

            {/* Super Host Badge */}
            <View style={styles.superHostBadge}>
              <Text style={styles.superHostText}>✨ Super Anfitrión</Text>
            </View>
          </View>
        </ImageBackground>

        <View style={styles.featuredInfo}>
          <View style={styles.featuredHeader}>
            <Text style={styles.featuredName} numberOfLines={1}>
              {item.name}
            </Text>
            <View style={styles.ratingContainer}>
              <Text style={styles.starIcon}>⭐</Text>
              <Text style={styles.ratingText}>{item.rating}</Text>
            </View>
          </View>

          <Text style={styles.featuredLocation} numberOfLines={1}>
            {item.location.marina}, {item.location.state}
          </Text>

          <View style={styles.featuredDetails}>
            <Text style={styles.capacityText}>👥 {item.capacity} huéspedes</Text>
            <Text style={styles.priceText}>
              <Text style={styles.priceAmount}>${item.pricePerHour}</Text>
              <Text style={styles.priceUnit}> /hora</Text>
            </Text>
          </View>
        </View>
      </TouchableOpacity>
    </ScaleAnimation>
  );

  const renderMarinaLocation = ({ item }: { item: typeof MARINA_LOCATIONS[0] }) => (
    <ScaleAnimation delay={500}>
      <TouchableOpacity
        style={styles.marinaCard}
        onPress={() => handleStatePress(item.state)}
        activeOpacity={0.9}
      >
        <ImageBackground
          source={{ uri: item.image }}
          style={styles.marinaImage}
          imageStyle={styles.marinaImageStyle}
        >
          <View style={styles.marinaOverlay}>
            <Text style={styles.marinaName}>{item.name}</Text>
            <Text style={styles.marinaCount}>{item.count} embarcaciones</Text>
          </View>
        </ImageBackground>
      </TouchableOpacity>
    </ScaleAnimation>
  );


  const renderRecentBoat = ({ item }: { item: Boat }) => (
    <ScaleAnimation delay={600}>
      <TouchableOpacity
        style={styles.recentCard}
        onPress={() => handleBoatPress(item.id)}
        activeOpacity={0.95}
      >
        <ImageBackground
          source={{ uri: `https://picsum.photos/300/200?random=${item.id}1` }}
          style={styles.recentImage}
          imageStyle={styles.recentImageStyle}
        >
          <View style={styles.recentOverlay}>
            {/* New Badge */}
            <View style={styles.newBadge}>
              <Text style={styles.newBadgeText}>NUEVO</Text>
            </View>

            {/* Heart */}
            <TouchableOpacity
              style={styles.smallHeartContainer}
              onPress={() => toggleHeart(`recent_${item.id}`)}
              activeOpacity={0.8}
            >
              <Text style={styles.smallHeartIcon}>
                {heartAnimations[`recent_${item.id}`] ? '❤️' : '🤍'}
              </Text>
            </TouchableOpacity>
          </View>
        </ImageBackground>

        <View style={styles.recentInfo}>
          <Text style={styles.recentName} numberOfLines={1}>{item.name}</Text>
          <Text style={styles.recentLocation} numberOfLines={1}>
            {item.location.state}
          </Text>
          <View style={styles.recentDetails}>
            <Text style={styles.recentPrice}>
              <Text style={styles.recentPriceAmount}>${item.pricePerHour}</Text>
              <Text style={styles.recentPriceUnit}> /hora</Text>
            </Text>
            <View style={styles.recentRating}>
              <Text style={styles.smallStarIcon}>⭐</Text>
              <Text style={styles.recentRatingText}>{item.rating}</Text>
            </View>
          </View>
        </View>
      </TouchableOpacity>
    </ScaleAnimation>
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
        paddingTop: 50, // Ajusta según StatusBar/SafeArea
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
                <Text style={styles.heroSearchSubtext} children={''} />
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
        contentContainerStyle={{ paddingTop: 160 }} // Ajusta para dejar espacio al searchbar y título
        showsVerticalScrollIndicator={false}
      >

        {/* Hero Section con Imagen Real DENTRO del ScrollView */}
        {/* Filtros Rápidos Horizontales */}
        <SlideTransition direction="right" delay={700}>
          <View style={styles.quickFiltersSection}>
            <Text style={styles.sectionTitle}>Inspiraciones para tu viaje</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.quickFiltersContainer}
            >
              {QUICK_FILTERS.map((filter, index) => (
                <ScaleAnimation key={index} delay={400 + (index * 100)}>
                  <TouchableOpacity
                    style={[styles.quickFilterChip, { borderColor: filter.color }]}
                    onPress={() => handleQuickFilter(filter.filter)}
                    activeOpacity={0.8}
                  >
                    <Text style={styles.quickFilterIcon}>{filter.icon}</Text>
                    <Text style={[styles.quickFilterText, { color: filter.color }]}>
                      {filter.label}
                    </Text>
                  </TouchableOpacity>
                </ScaleAnimation>
              ))}
            </ScrollView>
          </View>
        </SlideTransition>

        {/* Categorías de Embarcaciones */}
        <SlideTransition direction="up" delay={500}>
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Explora por categoría</Text>
              <Button mode="text" onPress={() => navigation.navigate('Search')} compact>
                Ver todas
              </Button>
            </View>

            <FlatList
              data={BOAT_CATEGORIES}
              renderItem={renderBoatCategory}
              keyExtractor={(item) => item.id.toString()}
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.categoriesContainer}
              snapToInterval={screenWidth * 0.75 + 15}
              decelerationRate="fast"
            />
          </View>
        </SlideTransition>

        {/* Embarcaciones Destacadas */}
        <SlideTransition direction="up" delay={700}>
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Embarcaciones destacadas</Text>
              <Button
                mode="text"
                onPress={() => navigation.navigate('Search', { featured: true })}
                compact
              >
                Ver todas
              </Button>
            </View>

            {isLoading ? (
              <View style={styles.loadingContainer}>
                <Text style={styles.loadingText}>Descubriendo embarcaciones...</Text>
              </View>
            ) : (
              <FlatList
                data={featuredBoats.slice(0, 6)}
                renderItem={renderFeaturedBoat}
                keyExtractor={(item) => item.id}
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.featuredContainer}
                snapToInterval={screenWidth * 0.85 + 15}
                decelerationRate="fast"
              />
            )}
          </View>
        </SlideTransition>

        {/* Marinas Populares */}
        <SlideTransition direction="left" delay={900}>
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Destinos populares</Text>
            <FlatList
              data={MARINA_LOCATIONS}
              renderItem={renderMarinaLocation}
              keyExtractor={(item) => item.name}
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.marinasContainer}
              snapToInterval={200}
              decelerationRate="fast"
            />
          </View>
        </SlideTransition>

        {/* Disponibles este mes */}
        <SlideTransition direction="up" delay={1100}>
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Disponibles próximamente</Text>
              <Button mode="text" onPress={() => navigation.navigate('Search')} compact>
                Ver todas
              </Button>
            </View>

            <View style={styles.recentGrid}>
              {boats.slice(0, 4).map((boat, index) => (
                <View key={boat.id} style={styles.recentWrapper}>
                  {renderRecentBoat({ item: boat })}
                </View>
              ))}
            </View>
          </View>
        </SlideTransition>

        {/* CTA para Propietarios - Premium */}
        <SlideTransition direction="up" delay={1300}>
          <View style={styles.ownerCtaContainer}>
            <ImageBackground
              source={{ uri: 'https://images.unsplash.com/photo-1436491865332-7a61a109cc05?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80' }}
              style={styles.ctaBackground}
              imageStyle={styles.ctaBackgroundImage}
            >
              <View style={styles.ctaOverlay}>
                <FadeInView delay={1400}>
                  <View style={styles.ctaContent}>
                    <Text style={styles.ctaTitle}>🚢 ¿Tienes una embarcación?</Text>
                    <Text style={styles.ctaSubtitle}>
                      Convierte tu pasión en ganancias. Gana hasta
                      <Text style={styles.ctaHighlight}> $1,500/mes</Text>
                    </Text>
                    <Text style={styles.ctaDescription}>
                      Únete a +500 capitanes que ya generan ingresos pasivos
                    </Text>
                  </View>
                </FadeInView>

                <ScaleAnimation delay={1500}>
                  <TouchableOpacity
                    style={styles.ctaButton}
                    onPress={() => {/* TODO: Navigate to owner registration */ }}
                    activeOpacity={0.9}
                  >
                    <Text style={styles.ctaButtonText}>
                      🚀 Empezar ahora
                    </Text>
                  </TouchableOpacity>
                </ScaleAnimation>
              </View>
            </ImageBackground>
          </View>
        </SlideTransition>

        {/* Espaciado final ampliado para evitar solapamiento */}
        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
};

const { height } = Dimensions.get('window');

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },

  // Hero Section con Imagen Real
  heroContainer: {
    position: 'relative',
  },

  heroImage: {
    width: '100%',
    height: height * 0.45,
    justifyContent: 'flex-end',
  },

  heroImageStyle: {
    opacity: 0.9,
  },
  heroOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.35)',
    justifyContent: 'space-between',
  },
  heroContent: {
    paddingHorizontal: 24,
    paddingTop: 5,
  },
  heroGreeting: {
    fontSize: 26,
    fontWeight: '400',
    color: 'white',
    marginBottom: 8,
    textShadowColor: 'rgba(0, 0, 0, 0.7)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 3,
  },
  heroTitle: {
    fontSize: 22,
    fontWeight: '400',
    color: 'white',
    marginBottom: 8,
    textShadowColor: 'rgba(0, 0, 0, 0.7)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 3,
  },
  heroSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    lineHeight: 22,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  heroSearchContainer: {
    paddingHorizontal: 24,
    paddingBottom: 30,
  },
  heroSearchSurface: {
    borderRadius: 32,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    paddingVertical: 6,
    paddingHorizontal: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 6, // para Android
  },

  heroSearchButton: {
    padding: 4,
  },
  heroSearchContent: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  heroSearchIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FF5A5F',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  searchIconText: {
    fontSize: 18,
  },
  heroSearchText: {
    flex: 1,
  },
  heroSearchPlaceholder: {
    fontSize: 16,
    fontWeight: '600',
    color: '#222222',
    marginBottom: 2,
  },
  heroSearchSubtext: {
    fontSize: 13,
    color: '#717171',
  },

  // Scroll Content
  scrollContent: {
    flex: 1,
    backgroundColor: '#ffffff',
  },

  // Quick Filters
  quickFiltersSection: {
    paddingTop: 24,
    paddingBottom: 8,
  },
  quickFiltersContainer: {
    paddingHorizontal: 24,
  },
  quickFilterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 25,
    borderWidth: 2,
    marginRight: 12,
    backgroundColor: 'white',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  quickFilterIcon: {
    fontSize: 18,
    marginRight: 8,
  },
  quickFilterText: {
    fontSize: 14,
    fontWeight: '600',
  },

  // Sections
  section: {
    paddingVertical: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '500',
    color: '#222222',
    flex: 1,
    paddingLeft: 24,
  },

  // Categories
  categoriesContainer: {
    paddingHorizontal: 24,
  },
  categoryCard: {
    width: 280,
    height: 180,
    marginRight: 15,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 5,
  },
  categoryImage: {
    width: '100%',
    height: '100%',
  },
  categoryImageStyle: {
    borderRadius: 16,
  },
  categoryOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  categoryIcon: {
    fontSize: 40,
    marginBottom: 12,
  },
  categoryName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
    textAlign: 'center',
    marginBottom: 8,
    textShadowColor: 'rgba(0, 0, 0, 0.7)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 3,
  },
  categoryCount: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
  },

  // Featured Boats
  featuredContainer: {
    paddingHorizontal: 24,
  },
  featuredCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    marginRight: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 12,
    elevation: 5,
    overflow: 'hidden',
  },
  featuredImage: {
    height: 220,
    position: 'relative',
  },
  featuredImageStyle: {
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
  },
  featuredOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    padding: 12,
  },
  heartContainer: {
    position: 'absolute',
    top: 12,
    right: 12,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  heartIcon: {
    fontSize: 16,
  },
  heartIconFilled: {
    transform: [{ scale: 1.2 }],
  },
  guestFavoriteBadge: {
    position: 'absolute',
    top: 12,
    left: 12,
    backgroundColor: 'white',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  guestFavoriteText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#222222',
  },
  superHostBadge: {
    position: 'absolute',
    bottom: 12,
    left: 12,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  superHostText: {
    fontSize: 12,
    fontWeight: '600',
    color: 'white',
  },
  featuredInfo: {
    padding: 16,
  },
  featuredHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 6,
  },
  featuredName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#222222',
    flex: 1,
    marginRight: 8,
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  starIcon: {
    fontSize: 14,
    marginRight: 2,
  },
  ratingText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#222222',
  },
  featuredLocation: {
    fontSize: 14,
    color: '#717171',
    marginBottom: 8,
  },
  featuredDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  capacityText: {
    fontSize: 14,
    color: '#717171',
  },
  priceText: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  priceAmount: {
    fontSize: 16,
    fontWeight: '600',
    color: '#222222',
  },
  priceUnit: {
    fontSize: 14,
    color: '#717171',
  },

  // Marinas
  marinasContainer: {
    paddingHorizontal: 24,
  },
  marinaCard: {
    width: 180,
    height: 120,
    marginRight: 12,
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 3,
  },
  marinaImage: {
    width: '100%',
    height: '100%',
  },
  marinaImageStyle: {
    borderRadius: 12,
  },
  marinaOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
    justifyContent: 'flex-end',
    padding: 12,
  },
  marinaName: {
    fontSize: 14,
    fontWeight: '600',
    color: 'white',
    marginBottom: 2,
  },
  marinaCount: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.9)',
  },

  // Recent Boats Grid
  recentGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 24,
    justifyContent: 'space-between',
  },
  recentWrapper: {
    width: '48%',
    marginBottom: 20,
  },
  recentCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 3,
    overflow: 'hidden',
  },
  recentImage: {
    height: 140,
    position: 'relative',
  },
  recentImageStyle: {
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
  },
  recentOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    padding: 8,
  },
  newBadge: {
    position: 'absolute',
    top: 8,
    left: 8,
    backgroundColor: '#34C759',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  newBadgeText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: 'white',
  },
  smallHeartContainer: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  smallHeartIcon: {
    fontSize: 14,
  },
  recentInfo: {
    padding: 12,
  },
  recentName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#222222',
    marginBottom: 4,
  },
  recentLocation: {
    fontSize: 12,
    color: '#717171',
    marginBottom: 8,
  },
  recentDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  recentPrice: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  recentPriceAmount: {
    fontSize: 14,
    fontWeight: '600',
    color: '#222222',
  },
  recentPriceUnit: {
    fontSize: 12,
    color: '#717171',
  },
  recentRating: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  smallStarIcon: {
    fontSize: 12,
    marginRight: 2,
  },
  recentRatingText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#222222',
  },

  // Owner CTA
  ownerCtaContainer: {
    marginHorizontal: 24,
    marginBottom: 24,
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.2,
    shadowRadius: 16,
    elevation: 8,
  },
  ctaBackground: {
    height: 200,
  },
  ctaBackgroundImage: {
    borderRadius: 20,
  },
  ctaOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  ctaContent: {
    alignItems: 'center',
    marginBottom: 20,
  },
  ctaTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    textAlign: 'center',
    marginBottom: 8,
    textShadowColor: 'rgba(0, 0, 0, 0.7)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 3,
  },
  ctaSubtitle: {
    fontSize: 16,
    color: 'white',
    textAlign: 'center',
    marginBottom: 8,
    lineHeight: 22,
  },
  ctaHighlight: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFD700',
  },
  ctaDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
  },
  ctaButton: {
    backgroundColor: '#FF5A5F',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 30,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  ctaButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: 'white',
  },

  // Loading
  loadingContainer: {
    paddingHorizontal: 24,
    paddingVertical: 40,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#717171',
    fontStyle: 'italic',
  },

  // Bottom Spacing
  bottomSpacing: {
    height: 32,
  },
});

// Exportación por defecto para compatibilidad
export default HomeScreen;

