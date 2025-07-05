import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import {
  Text,
  Card,
  Title,
  Paragraph,
  Button,
  Chip,
  Surface,
  IconButton,
  Searchbar,
  FAB,
} from 'react-native-paper';
import { RootState } from '../../store/store';
import { fetchUserBookings, cancelBooking, Booking } from '../../store/slices/bookingsSlice';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
interface Props {
  navigation: any;
}

const STATUS_COLORS = {
  pending: '#FF9800',
  confirmed: '#4CAF50',
  active: '#2196F3',
  completed: '#9C27B0',
  cancelled: '#F44336',
};

const STATUS_LABELS = {
  pending: 'Pendiente',
  confirmed: 'Confirmada',
  active: 'Activa',
  completed: 'Completada',
  cancelled: 'Cancelada',
};

const PAYMENT_STATUS_COLORS = {
  pending: '#FF9800',
  paid: '#4CAF50',
  failed: '#F44336',
  refunded: '#9C27B0',
};

const PAYMENT_STATUS_LABELS = {
  pending: 'Pendiente',
  paid: 'Pagado',
  failed: 'Fallido',
  refunded: 'Reembolsado',
};

export function BookingsScreen({ navigation }: Props) {
  const dispatch = useAppDispatch();
  const { bookings, isLoading } = useAppSelector((state: RootState) => state.bookings);
  const { user } = useAppSelector((state: RootState) => state.auth);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'active' | 'completed' | 'cancelled'>('all');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (user?.id) {
      dispatch(fetchUserBookings(user.id));
    }
  }, [dispatch, user?.id]);

  const onRefresh = async () => {
    setRefreshing(true);
    if (user?.id) {
      await dispatch(fetchUserBookings(user.id));
    }
    setRefreshing(false);
  };

  const handleCancelBooking = (bookingId: string) => {
    dispatch(cancelBooking(bookingId));
  };

  const filteredBookings = bookings.filter(booking => {
    const matchesSearch = booking.boatName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      booking.marina.name.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesFilter = selectedFilter === 'all' ||
      (selectedFilter === 'active' && ['pending', 'confirmed', 'active'].includes(booking.bookingStatus)) ||
      booking.bookingStatus === selectedFilter;

    return matchesSearch && matchesFilter;
  });

  const getStatusIcon = (status: Booking['bookingStatus']) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'confirmed': return '✅';
      case 'active': return '🚤';
      case 'completed': return '🏁';
      case 'cancelled': return '❌';
      default: return '📋';
    }
  };

  const renderBookingCard = (booking: Booking) => (
    <Card key={booking.id} style={styles.bookingCard}>
      <Card.Content>
        {/* Header */}
        <View style={styles.bookingHeader}>
          <View style={styles.bookingInfo}>
            <Title style={styles.boatName}>{booking.boatName}</Title>
            <Paragraph style={styles.marina}>📍 {booking.marina.name}</Paragraph>
          </View>
          <View style={styles.statusContainer}>
            <Chip
              style={[styles.statusChip, { backgroundColor: STATUS_COLORS[booking.bookingStatus] }]}
              textStyle={styles.statusText}
            >
              {getStatusIcon(booking.bookingStatus)} {STATUS_LABELS[booking.bookingStatus]}
            </Chip>
          </View>
        </View>

        {/* Booking Details */}
        <View style={styles.detailsContainer}>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>📅 Fecha:</Text>
            <Text style={styles.detailValue}>{booking.startDate}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>⏰ Horario:</Text>
            <Text style={styles.detailValue}>{booking.startTime} - {booking.endTime}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>👥 Huéspedes:</Text>
            <Text style={styles.detailValue}>{booking.guests} personas</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>💰 Total:</Text>
            <Text style={styles.priceValue}>${booking.totalPrice} {booking.currency}</Text>
          </View>
        </View>

        {/* Payment Status */}
        <View style={styles.paymentContainer}>
          <Text style={styles.paymentLabel}>Estado del Pago:</Text>
          <Chip
            style={[styles.paymentChip, { backgroundColor: PAYMENT_STATUS_COLORS[booking.paymentStatus] }]}
            textStyle={styles.paymentText}
          >
            {PAYMENT_STATUS_LABELS[booking.paymentStatus]}
          </Chip>
        </View>

        {/* Actions */}
        <View style={styles.actionsContainer}>
          <Button
            mode="outlined"
            onPress={() => navigation.navigate('BoatDetails', { boatId: booking.boatId })}
            style={styles.actionButton}
          >
            Ver Bote
          </Button>

          {booking.bookingStatus === 'pending' && (
            <Button
              mode="text"
              onPress={() => handleCancelBooking(booking.id)}
              textColor="#F44336"
              style={styles.actionButton}
            >
              Cancelar
            </Button>
          )}

          {booking.paymentStatus === 'pending' && booking.bookingStatus !== 'cancelled' && (
            <Button
              mode="contained"
              onPress={() => navigation.navigate('Payment', {
                bookingId: booking.id,
                totalAmount: booking.totalPrice,
                currency: booking.currency
              })}
              style={styles.payButton}
            >
              Pagar
            </Button>
          )}
        </View>
      </Card.Content>
    </Card>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyContainer}>
      <Text style={styles.emptyIcon}>🛥️</Text>
      <Title style={styles.emptyTitle}>No tienes reservas</Title>
      <Paragraph style={styles.emptyText}>
        ¡Explora nuestras embarcaciones y haz tu primera reserva!
      </Paragraph>
      <Button
        mode="contained"
        onPress={() => navigation.navigate('Search')}
        style={styles.exploreButton}
      >
        Explorar Botes
      </Button>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <Surface style={styles.header}>
        <View style={styles.headerContent}>
          <Title style={styles.headerTitle}>🗓️ Mis Reservas</Title>
          <IconButton
            icon="refresh"
            size={24}
            onPress={onRefresh}
          />
        </View>
      </Surface>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Searchbar
          placeholder="Buscar por bote o marina..."
          onChangeText={setSearchQuery}
          value={searchQuery}
          style={styles.searchBar}
        />
      </View>

      {/* Filter Chips */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filtersContainer}
        contentContainerStyle={styles.filtersContent}
      >
        <Chip
          selected={selectedFilter === 'all'}
          onPress={() => setSelectedFilter('all')}
          style={styles.filterChip}
        >
          Todas
        </Chip>
        <Chip
          selected={selectedFilter === 'active'}
          onPress={() => setSelectedFilter('active')}
          style={styles.filterChip}
        >
          Activas
        </Chip>
        <Chip
          selected={selectedFilter === 'completed'}
          onPress={() => setSelectedFilter('completed')}
          style={styles.filterChip}
        >
          Completadas
        </Chip>
        <Chip
          selected={selectedFilter === 'cancelled'}
          onPress={() => setSelectedFilter('cancelled')}
          style={styles.filterChip}
        >
          Canceladas
        </Chip>
      </ScrollView>

      {/* Bookings List */}
      <ScrollView
        style={styles.bookingsList}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        {filteredBookings.length === 0 ? (
          renderEmptyState()
        ) : (
          filteredBookings.map(renderBookingCard)
        )}
      </ScrollView>

      {/* FAB */}
      <FAB
        icon="plus"
        style={styles.fab}
        onPress={() => navigation.navigate('Search')}
        label="Nueva Reserva"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    elevation: 4,
    backgroundColor: 'white',
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    paddingTop: 60,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  searchContainer: {
    padding: 16,
  },
  searchBar: {
    elevation: 2,
  },
  filtersContainer: {
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  filtersContent: {
    paddingRight: 16,
  },
  filterChip: {
    marginRight: 8,
  },
  bookingsList: {
    flex: 1,
    paddingHorizontal: 16,
  },
  bookingCard: {
    marginBottom: 16,
    elevation: 3,
  },
  bookingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  bookingInfo: {
    flex: 1,
  },
  boatName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  marina: {
    fontSize: 14,
    color: '#666',
  },
  statusContainer: {
    marginLeft: 12,
  },
  statusChip: {
    elevation: 1,
  },
  statusText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 12,
  },
  detailsContainer: {
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  detailLabel: {
    fontSize: 14,
    color: '#666',
    flex: 1,
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
    textAlign: 'right',
  },
  priceValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#0066CC',
    flex: 1,
    textAlign: 'right',
  },
  paymentContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  paymentLabel: {
    fontSize: 14,
    color: '#666',
  },
  paymentChip: {
    elevation: 1,
  },
  paymentText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 12,
  },
  actionsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  actionButton: {
    flex: 1,
    marginHorizontal: 4,
  },
  payButton: {
    flex: 1,
    marginHorizontal: 4,
    backgroundColor: '#0066CC',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
    marginTop: 64,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  exploreButton: {
    backgroundColor: '#0066CC',
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
    backgroundColor: '#0066CC',
  },
});