import {
  Alert,
  ScrollView,
  StyleSheet,
  View
} from 'react-native';
import {
  Button,
  Card,
  Chip,
  Surface,
  Text,
  Title,
} from 'react-native-paper';
import { useAppSelector } from '../../store/hooks';
import { Booking } from '../../store/slices/bookingsSlice';
import { RootState } from '../../store/store';

// ✅ Interface para props de BookingCard
interface BookingCardProps {
  booking: Booking;
  onPress: (booking: Booking) => void;
  onCancel: (booking: Booking) => void;
}

// ✅ Interface para props del componente principal
interface BookingsScreenProps {
  navigation: any; // O usa el tipo específico de navigation si lo tienes
}

// ✅ Función BookingCard con tipos explícitos
function BookingCard({ booking, onPress, onCancel }: BookingCardProps) {
  // ✅ Función con tipo explícito para el parámetro
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'confirmed':
        return '#4CAF50';
      case 'pending':
        return '#FF9800';
      case 'cancelled':
        return '#F44336';
      case 'completed':
        return '#2196F3';
      case 'active':
        return '#9C27B0';
      default:
        return '#757575';
    }
  };

  // ✅ Función con tipo explícito para el parámetro
  const getStatusText = (status: string): string => {
    switch (status) {
      case 'confirmed':
        return 'Confirmado';
      case 'pending':
        return 'Pendiente';
      case 'cancelled':
        return 'Cancelado';
      case 'completed':
        return 'Completado';
      case 'active':
        return 'Activo';
      default:
        return 'Desconocido';
    }
  };

  return (
    <Card style={styles.bookingCard}>
      <Card.Content>
        <View style={styles.bookingHeader}>
          <View style={styles.bookingInfo}>
            <Title style={styles.boatName}>{booking.boatName}</Title>
            <Text style={styles.bookingDate}>
              📅 {new Date(booking.startDate).toLocaleDateString('es-ES')}
            </Text>
            <Text style={styles.bookingTime}>
              🕐 {booking.startTime} - {booking.endTime}
            </Text>
            <Text style={styles.bookingGuests}>
              👥 {booking.guests} huéspedes
            </Text>
            <Text style={styles.marina}>
              📍 {booking.marina.name}
            </Text>
          </View>
          <View style={styles.bookingStatus}>
            <Chip
              style={[
                styles.statusChip,
                { backgroundColor: getStatusColor(booking.bookingStatus) }
              ]}
              textStyle={styles.statusText}
            >
              {getStatusText(booking.bookingStatus)}
            </Chip>
            <Text style={styles.totalPrice}>
              ${booking.totalPrice} {booking.currency}
            </Text>
            <Text style={styles.paymentStatus}>
              💳 {booking.paymentStatus}
            </Text>
          </View>
        </View>

        {booking.specialRequests && (
          <View style={styles.specialRequests}>
            <Text style={styles.specialRequestsLabel}>Solicitudes especiales:</Text>
            <Text style={styles.specialRequestsText}>{booking.specialRequests}</Text>
          </View>
        )}

        <View style={styles.bookingActions}>
          <Button
            mode="outlined"
            onPress={() => onPress(booking)}
            style={styles.actionButton}
          >
            Ver Detalles
          </Button>
          {booking.bookingStatus === 'pending' && (
            <Button
              mode="contained"
              onPress={() => onCancel(booking)}
              buttonColor="#F44336"
              style={styles.actionButton}
            >
              Cancelar
            </Button>
          )}
        </View>
      </Card.Content>
    </Card>
  );
}

// ✅ Componente principal con tipos explícitos
export function BookingsScreen({ navigation }: BookingsScreenProps) {
  const { bookings, isLoading } = useAppSelector((state: RootState) => state.bookings);

  // ✅ Handler con tipo explícito para el parámetro
  const handleBookingPress = (booking: Booking): void => {
    navigation.navigate('BookingDetails', { booking });
  };

  // ✅ Handler con tipo explícito para el parámetro
  const handleCancelBooking = (booking: Booking): void => {
    Alert.alert(
      'Cancelar Reserva',
      `¿Estás seguro de que quieres cancelar la reserva de "${booking.boatName}"?`,
      [
        {
          text: 'No',
          style: 'cancel',
        },
        {
          text: 'Sí, Cancelar',
          style: 'destructive',
          onPress: () => {
            // TODO: Implementar lógica de cancelación
            console.log('Cancelling booking:', booking.id);
            // dispatch(cancelBooking(booking.id));
          },
        },
      ]
    );
  };

  // Estado de carga
  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.loadingText}>Cargando reservas...</Text>
      </View>
    );
  }

  // Sin reservas
  if (bookings.length === 0) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.emptyText}>No tienes reservas aún</Text>
        <Text style={styles.emptySubText}>
          ¡Explora nuestras embarcaciones y haz tu primera reserva!
        </Text>
        <Button
          mode="contained"
          onPress={() => navigation.navigate('Search')}
          style={styles.searchButton}
        >
          Buscar Embarcaciones
        </Button>
      </View>
    );
  }

  // Renderizar reservas
  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <Surface style={styles.header}>
        <Title style={styles.headerTitle}>Mis Reservas</Title>
        <Text style={styles.headerSubtitle}>
          {bookings.length} reserva{bookings.length !== 1 ? 's' : ''}
        </Text>
      </Surface>

      {bookings.map((booking: Booking) => (
        <BookingCard
          key={booking.id}
          booking={booking}
          onPress={handleBookingPress}
          onCancel={handleCancelBooking}
        />
      ))}
    </ScrollView>
  );
}

// ✅ Estilos actualizados
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    padding: 20,
  },
  header: {
    padding: 20,
    margin: 16,
    borderRadius: 12,
    elevation: 2,
    backgroundColor: 'white',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
    color: '#333',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#666',
  },
  bookingCard: {
    margin: 16,
    marginTop: 8,
    elevation: 2,
    borderRadius: 12,
  },
  bookingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  bookingInfo: {
    flex: 1,
    marginRight: 12,
  },
  boatName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  bookingDate: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  bookingTime: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  bookingGuests: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  marina: {
    fontSize: 14,
    color: '#666',
  },
  bookingStatus: {
    alignItems: 'flex-end',
  },
  statusChip: {
    marginBottom: 8,
  },
  statusText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 12,
  },
  totalPrice: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#0066CC',
    marginBottom: 4,
  },
  paymentStatus: {
    fontSize: 12,
    color: '#666',
    textTransform: 'capitalize',
  },
  specialRequests: {
    backgroundColor: '#f0f0f0',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  specialRequestsLabel: {
    fontWeight: 'bold',
    fontSize: 14,
    marginBottom: 4,
    color: '#333',
  },
  specialRequestsText: {
    fontSize: 14,
    color: '#666',
    fontStyle: 'italic',
  },
  bookingActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  actionButton: {
    flex: 1,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
  },
  emptyText: {
    fontSize: 20,
    color: '#333',
    marginBottom: 8,
    textAlign: 'center',
    fontWeight: 'bold',
  },
  emptySubText: {
    fontSize: 16,
    color: '#666',
    marginBottom: 24,
    textAlign: 'center',
    lineHeight: 22,
  },
  searchButton: {
    paddingHorizontal: 20,
    paddingVertical: 8,
  },
});
