import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Dimensions,
  Linking,
  RefreshControl,
  ScrollView,
  Share,
  StyleSheet,
  TouchableOpacity,
  View,
} from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import {
  Button,
  Card,
  Chip,
  Divider,
  IconButton,
  List,
  Modal,
  Paragraph,
  Portal,
  ProgressBar,
  Surface,
  Text,
  Title,
  useTheme
} from 'react-native-paper';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { fetchBoatById } from '../../store/slices/boatsSlice';
import { BoatDetailsScreenProps } from '../../types/navigation';

// Importar RootState desde el store global
import { RootState } from '../../store/store';

// Importar componentes de animación
import { FadeInView } from '../../components/animations/FadeInView';
import { SlideTransition } from '../../components/animations/SlideTransition';

// Importar componentes de galería
import { AnimatedImageCarousel } from '../../components/gallery/AnimatedImageCarousel';
import { ImageGallery } from '../../components/gallery/ImageGallery';


// ELIMINA ESTE BLOQUE COMPLETO:

interface AuthState {
  user: {
    id: string;
    email: string;
    name: string;
  } | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface BoatsState {
  selectedBoat: Boat | null;
  isLoading: boolean;
  error: string | null;
}

// RootState para el store
interface RootState {
  auth: AuthState;
  boats: BoatsState;
}


const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const MAP_HEIGHT = 200;
const IMAGE_HEIGHT = 250;

const BoatDetailsScreen: React.FC<BoatDetailsScreenProps> = ({ navigation, route }) => { // <--- CAMBIA ESTA LÍNEA
  const { boatId } = route.params;
  const theme = useTheme();
  const dispatch = useAppDispatch();

  // Estado local
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [showGallery, setShowGallery] = useState(false);
  const [showFullDescription, setShowFullDescription] = useState(false);
  const [isFavorited, setIsFavorited] = useState(false);
  const [showContactModal, setShowContactModal] = useState(false);
  const [showReviews, setShowReviews] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Selectores del store con tipos explícitos
  const { selectedBoat: boat, isLoading, error } = useAppSelector(
    (state: RootState) => state.boats
  );
  const { user } = useAppSelector((state: RootState) => state.auth);

  // Cargar datos del bote
  useEffect(() => {
    if (boatId) {
      dispatch(fetchBoatById(boatId));
    }
  }, [boatId, dispatch]);

  // Callbacks optimizados con useCallback
  const handleShare = useCallback(async () => {
    if (!boat) return;

    try {
      await Share.share({
        message: `¡Mira esta embarcación! ${boat.name} - ${boat.description}`,
        title: boat.name,
      });
    } catch (error) {
      Alert.alert('Error', 'No se pudo compartir');
    }
  }, [boat]);

  const handleContact = useCallback(() => {
    if (!user) {
      Alert.alert(
        'Iniciar sesión',
        'Debes iniciar sesión para contactar al propietario',
        [
          { text: 'Cancelar', style: 'cancel' },
          { text: 'Iniciar sesión', onPress: () => navigation.navigate('Login') }
        ]
      );
      return;
    }
    setShowContactModal(true);
  }, [user, navigation]);

  const handlePhoneCall = useCallback((phoneNumber: string) => {
    if (phoneNumber) {
      Linking.openURL(`tel:${phoneNumber}`);
    }
  }, []);

  const handleWhatsApp = useCallback((phoneNumber: string) => {
    if (phoneNumber) {
      const message = `Hola, estoy interesado en tu embarcación ${boat?.name}`;
      Linking.openURL(`whatsapp://send?phone=${phoneNumber}&text=${encodeURIComponent(message)}`);
    }
  }, [boat]);

  const toggleFavorite = useCallback(() => {
    setIsFavorited(prev => !prev);
    // Aquí deberías dispatch a una acción para guardar en favoritos
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await dispatch(fetchBoatById(boatId));
    setRefreshing(false);
  }, [boatId, dispatch]);

  // Memoizar cálculos pesados
  const priceDisplay = useMemo(() => {
    if (!boat?.pricePerHour) return 'Consultar precio';
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'USD'
    }).format(boat.pricePerHour);
  }, [boat?.pricePerHour]);

  const availabilityText = useMemo(() => {
    if (!boat?.availability) return 'No disponible';
    return boat.availability.available ? 'Disponible' : 'No disponible';
  }, [boat?.availability]);

  const availabilityColor = useMemo(() => {
    if (!boat?.availability || !boat.availability.available) {
      return theme.colors.error;
    }
    return theme.colors.primary;
  }, [boat?.availability, theme]);

  // Estados de carga y error
  if (isLoading && !refreshing) {
    return (
      <View style={[styles.centered, { backgroundColor: theme.colors.background }]}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={{ marginTop: 16 }}>Cargando embarcación...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.centered, { backgroundColor: theme.colors.background }]}>
        <Text style={{ color: theme.colors.error }}>Error al cargar la embarcación</Text>
        <Button mode="contained" onPress={() => dispatch(fetchBoatById(boatId))} style={{ marginTop: 16 }}>
          Reintentar
        </Button>
      </View>
    );
  }

  if (!boat) {
    return (
      <View style={[styles.centered, { backgroundColor: theme.colors.background }]}>
        <Text>No se encontró la embarcación</Text>
        <Button mode="text" onPress={() => navigation.goBack()} style={{ marginTop: 16 }}>
          Volver
        </Button>
      </View>
    );
  }

  // Calcular el total de imágenes
  const totalImages = boat.images?.length || 3; // Default a 3 si no hay imágenes

  return (
    <>
      <ScrollView
        style={[styles.container, { backgroundColor: theme.colors.background }]}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Galería de imágenes */}
        <FadeInView delay={0}>
          <AnimatedImageCarousel
            images={boat.images || []}
            boatName={boat.name}
            boatType={boat.type}
            onImagePress={() => setShowGallery(true)}
            onIndexChange={setCurrentImageIndex}
            totalImages={totalImages}
          />
        </FadeInView>

        {/* Contenido principal */}
        <View style={styles.content}>
          {/* Header con título y precio */}
          <SlideTransition direction="right" delay={100}>
            <Surface style={styles.headerSurface} elevation={1}>
              <View style={styles.headerContent}>
                <View style={styles.titleContainer}>
                  <Title style={styles.title}>{boat.name}</Title>
                  <View style={styles.chipContainer}>
                    <Chip
                      icon="sail-boat"
                      mode="outlined"
                      style={[styles.chip, { borderColor: theme.colors.primary }]}
                    >
                      {boat.type}
                    </Chip>
                    <Chip
                      icon="check-circle"
                      mode="outlined"
                      style={[styles.chip, { borderColor: availabilityColor }]}
                      textStyle={{ color: availabilityColor }}
                    >
                      {availabilityText}
                    </Chip>
                  </View>
                </View>
                <Text style={[styles.price, { color: theme.colors.primary }]}>
                  {priceDisplay}
                </Text>
              </View>
            </Surface>
          </SlideTransition>

          {/* Acciones rápidas */}
          <SlideTransition direction="left" delay={200}>
            <View style={styles.actionButtons}>
              <Button
                mode="contained"
                icon="phone"
                onPress={handleContact}
                style={styles.actionButton}
              >
                Contactar
              </Button>
              <Button
                mode="outlined"
                icon="share-variant"
                onPress={handleShare}
                style={styles.actionButton}
              >
                Compartir
              </Button>
              <IconButton
                icon={isFavorited ? "heart" : "heart-outline"}
                iconColor={isFavorited ? theme.colors.error : theme.colors.onSurface}
                size={24}
                onPress={toggleFavorite}
              />
            </View>
          </SlideTransition>

          <Divider style={styles.divider} />

          {/* Descripción */}
          <FadeInView delay={300}>
            <Card style={styles.card}>
              <Card.Content>
                <Title style={styles.sectionTitle}>Descripción</Title>
                <Paragraph numberOfLines={showFullDescription ? undefined : 3}>
                  {boat.description}
                </Paragraph>
                {boat.description && boat.description.length > 150 && (
                  <Button
                    mode="text"
                    onPress={() => setShowFullDescription(!showFullDescription)}
                    style={styles.readMoreButton}
                  >
                    {showFullDescription ? 'Ver menos' : 'Ver más'}
                  </Button>
                )}
              </Card.Content>
            </Card>
          </FadeInView>

          {/* Características */}
          <FadeInView delay={400}>
            <Card style={styles.card}>
              <Card.Content>
                <Title style={styles.sectionTitle}>Características</Title>
                <List.Item
                  title="Tipo de embarcación"
                  description={boat.type}
                  left={props => <List.Icon {...props} icon="sail-boat" />}
                />
                <List.Item
                  title="Capacidad"
                  description={`${boat.capacity} personas`}
                  left={props => <List.Icon {...props} icon="account-group" />}
                />
                {boat.amenities && boat.amenities.length > 0 && (
                  <List.Item
                    title="Características adicionales"
                    description={boat.amenities.join(', ')}
                    left={props => <List.Icon {...props} icon="format-list-bulleted" />}
                  />
                )}
              </Card.Content>
            </Card>
          </FadeInView>

          {/* Ubicación */}
          {boat.location && (
            <FadeInView delay={500}>
              <Card style={styles.card}>
                <Card.Content>
                  <Title style={styles.sectionTitle}>Ubicación</Title>
                  <Paragraph>{boat.location.marina}</Paragraph>
                  <Paragraph style={styles.locationState}>{boat.location.state}</Paragraph>
                </Card.Content>
                <MapView
                  provider={PROVIDER_GOOGLE}
                  style={styles.map}
                  initialRegion={{
                    latitude: boat.location.coordinates.latitude,
                    longitude: boat.location.coordinates.longitude,
                    latitudeDelta: 0.01,
                    longitudeDelta: 0.01,
                  }}
                  scrollEnabled={false}
                  zoomEnabled={false}
                >
                  <Marker
                    coordinate={{
                      latitude: boat.location.coordinates.latitude,
                      longitude: boat.location.coordinates.longitude,
                    }}
                    title={boat.name}
                    description={boat.location.marina}
                  />
                </MapView>
              </Card>
            </FadeInView>
          )}

          {/* Disponibilidad */}
          {boat.availability && (
            <FadeInView delay={600}>
              <Card style={styles.card}>
                <Card.Content>
                  <Title style={styles.sectionTitle}>Disponibilidad</Title>
                  <View style={styles.availabilityContainer}>
                    <Chip
                      icon={boat.availability.available ? "check" : "close"}
                      mode="flat"
                      style={[
                        styles.availabilityChip,
                        { backgroundColor: boat.availability.available ? theme.colors.primaryContainer : theme.colors.errorContainer }
                      ]}
                    >
                      {availabilityText}
                    </Chip>
                  </View>
                  {boat.availability.blockedDates && boat.availability.blockedDates.length > 0 && (
                    <>
                      <Paragraph style={styles.blockedDatesTitle}>Fechas no disponibles:</Paragraph>
                      <View style={styles.blockedDatesContainer}>
                        {boat.availability.blockedDates.map((date: string, index: number) => (
                          <Chip key={index} style={styles.dateChip} compact>
                            {new Date(date).toLocaleDateString('es-ES')}
                          </Chip>
                        ))}
                      </View>
                    </>
                  )}
                </Card.Content>
              </Card>
            </FadeInView>
          )}

          {/* Reseñas */}
          {boat.rating !== undefined && (
            <FadeInView delay={700}>
              <Card style={styles.card}>
                <TouchableOpacity onPress={() => setShowReviews(!showReviews)}>
                  <Card.Content>
                    <View style={styles.reviewsHeader}>
                      <Title style={styles.sectionTitle}>Reseñas</Title>
                      <View style={styles.ratingContainer}>
                        <Text style={styles.rating}>{boat.rating.toFixed(1)}</Text>
                        <List.Icon icon="star" color={theme.colors.primary} />
                      </View>
                    </View>
                    <ProgressBar
                      progress={boat.rating / 5}
                      color={theme.colors.primary}
                      style={styles.ratingBar}
                    />
                  </Card.Content>
                </TouchableOpacity>
              </Card>
            </FadeInView>
          )}
        </View>
      </ScrollView>

      {/* Modales */}
      <Portal>
        {/* Modal de contacto */}
        <Modal
          visible={showContactModal}
          onDismiss={() => setShowContactModal(false)}
          contentContainerStyle={[styles.modal, { backgroundColor: theme.colors.surface }]}
        >
          <Title style={styles.modalTitle}>Contactar propietario</Title>
          {boat.owner && (
            <>
              <List.Item
                title="Llamar"
                description={boat.owner.phone}
                left={props => <List.Icon {...props} icon="phone" />}
                onPress={() => boat.owner && handlePhoneCall(boat.owner.phone)}
              />
              <List.Item
                title="WhatsApp"
                description="Enviar mensaje"
                left={props => <List.Icon {...props} icon="whatsapp" />}
                onPress={() => boat.owner && handleWhatsApp(boat.owner.phone)}
              />
              <List.Item
                title="Email"
                description={boat.owner.email}
                left={props => <List.Icon {...props} icon="email" />}
                onPress={() => boat.owner && Linking.openURL(`mailto:${boat.owner.email}`)}
              />
            </>
          )}
          <Button
            mode="text"
            onPress={() => setShowContactModal(false)}
            style={styles.modalButton}
          >
            Cerrar
          </Button>
        </Modal>

        {/* Modal de galería */}
        {showGallery && boat.images && boat.images.length > 0 && (
          <ImageGallery
            images={boat.images}
            initialIndex={currentImageIndex}
            boatName={boat.name}
            boatType={boat.type}
            onClose={() => setShowGallery(false)}
            totalImages={boat.images.length}
          />
        )}
      </Portal>
    </>
  );
};

// Exportación por defecto para compatibilidad con React Navigation
export default BoatDetailsScreen;

// También exportar como named export
export { BoatDetailsScreen };

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    paddingBottom: 24,
  },
  imageIndicator: {
    position: 'absolute',
    top: IMAGE_HEIGHT - 30,
    right: 16,
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 16,
  },
  headerSurface: {
    margin: 16,
    padding: 16,
    borderRadius: 12,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  titleContainer: {
    flex: 1,
    marginRight: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    marginRight: 8,
  },
  price: {
    fontSize: 22,
    fontWeight: 'bold',
  },
  actionButtons: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 12,
    alignItems: 'center',
  },
  actionButton: {
    flex: 1,
  },
  divider: {
    marginVertical: 16,
    marginHorizontal: 16,
  },
  card: {
    margin: 16,
    borderRadius: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  readMoreButton: {
    marginTop: 8,
  },
  locationState: {
    marginTop: 4,
    opacity: 0.7,
  },
  map: {
    height: MAP_HEIGHT,
    marginTop: 12,
  },
  availabilityContainer: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  availabilityChip: {
    marginRight: 8,
  },
  blockedDatesTitle: {
    marginTop: 12,
    marginBottom: 8,
    fontWeight: '500',
  },
  blockedDatesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  dateChip: {
    marginRight: 4,
    marginBottom: 4,
  },
  reviewsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  rating: {
    fontSize: 18,
    fontWeight: 'bold',
    marginRight: 4,
  },
  ratingBar: {
    height: 8,
    borderRadius: 4,
    marginTop: 8,
  },
  modal: {
    margin: 20,
    padding: 20,
    borderRadius: 12,
  },
  modalTitle: {
    marginBottom: 16,
  },
  modalButton: {
    marginTop: 16,
  },
});