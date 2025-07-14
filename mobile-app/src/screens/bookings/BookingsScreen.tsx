import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert
} from 'react-native';

// Datos de reservas de ejemplo
const sampleBookings = [
  {
    id: '1',
    boatName: 'Sea Explorer',
    boatImage: '🛥️',
    date: '2025-07-20',
    time: '10:00 AM',
    duration: '4 horas',
    price: 150,
    status: 'confirmada',
    location: 'Puerto Marina',
    guests: 6
  },
  {
    id: '2',
    boatName: 'Ocean Breeze',
    boatImage: '⛵',
    date: '2025-07-25',
    time: '2:00 PM',
    duration: '6 horas',
    price: 200,
    status: 'pendiente',
    location: 'Bahía Azul',
    guests: 4
  },
  {
    id: '3',
    boatName: 'Wave Rider',
    boatImage: '🚤',
    date: '2025-07-15',
    time: '9:00 AM',
    duration: '3 horas',
    price: 120,
    status: 'completada',
    location: 'Costa Norte',
    guests: 2
  }
];

function BookingCard({ booking, onPress, onCancel }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'confirmada': return '#4CAF50';
      case 'pendiente': return '#FF9800';
      case 'completada': return '#2196F3';
      case 'cancelada': return '#F44336';
      default: return '#666';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'confirmada': return '✅ Confirmada';
      case 'pendiente': return '⏳ Pendiente';
      case 'completada': return '🎉 Completada';
      case 'cancelada': return '❌ Cancelada';
      default: return status;
    }
  };

  return (
    <TouchableOpacity style={styles.bookingCard} onPress={onPress}>
      <View style={styles.cardHeader}>
        <Text style={styles.boatEmoji}>{booking.boatImage}</Text>
        <View style={styles.headerInfo}>
          <Text style={styles.boatName}>{booking.boatName}</Text>
          <Text style={[styles.status, { color: getStatusColor(booking.status) }]}>
            {getStatusText(booking.status)}
          </Text>
        </View>
        <Text style={styles.price}>${booking.price}</Text>
      </View>

      <View style={styles.cardContent}>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>📅 Fecha:</Text>
          <Text style={styles.detailValue}>{booking.date}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>🕐 Hora:</Text>
          <Text style={styles.detailValue}>{booking.time}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>⏱️ Duración:</Text>
          <Text style={styles.detailValue}>{booking.duration}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>📍 Ubicación:</Text>
          <Text style={styles.detailValue}>{booking.location}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>👥 Huéspedes:</Text>
          <Text style={styles.detailValue}>{booking.guests} personas</Text>
        </View>
      </View>

      {booking.status === 'confirmada' && (
        <View style={styles.cardActions}>
          <TouchableOpacity 
            style={styles.cancelButton}
            onPress={() => onCancel(booking)}
          >
            <Text style={styles.cancelButtonText}>Cancelar Reserva</Text>
          </TouchableOpacity>
        </View>
      )}
    </TouchableOpacity>
  );
}

export default function BookingsScreen() {
  const [bookings, setBookings] = useState(sampleBookings);
  const [selectedFilter, setSelectedFilter] = useState('todas');

  const filteredBookings = bookings.filter(booking => {
    if (selectedFilter === 'todas') return true;
    return booking.status === selectedFilter;
  });

  const handleBookingPress = (booking) => {
    Alert.alert(
      'Detalles de Reserva',
      `Reserva para ${booking.boatName}\nFecha: ${booking.date}\nEstado: ${booking.status}`,
      [{ text: 'OK' }]
    );
  };

  const handleCancelBooking = (booking) => {
    Alert.alert(
      'Cancelar Reserva',
      `¿Estás seguro de que quieres cancelar la reserva para ${booking.boatName}?`,
      [
        { text: 'No', style: 'cancel' },
        { 
          text: 'Sí, cancelar', 
          style: 'destructive',
          onPress: () => {
            setBookings(prev => 
              prev.map(b => 
                b.id === booking.id 
                  ? { ...b, status: 'cancelada' }
                  : b
              )
            );
          }
        }
      ]
    );
  };

  const filters = [
    { key: 'todas', label: 'Todas', count: bookings.length },
    { key: 'confirmada', label: 'Confirmadas', count: bookings.filter(b => b.status === 'confirmada').length },
    { key: 'pendiente', label: 'Pendientes', count: bookings.filter(b => b.status === 'pendiente').length },
    { key: 'completada', label: 'Completadas', count: bookings.filter(b => b.status === 'completada').length }
  ];

  console.log('✅ BookingsScreen cargado correctamente');

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>📅 Mis Reservas</Text>
        <Text style={styles.subtitle}>Gestiona tus aventuras acuáticas</Text>
      </View>

      {/* Filtros */}
      <View style={styles.filtersContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.filters}>
            {filters.map(filter => (
              <TouchableOpacity
                key={filter.key}
                style={[
                  styles.filterButton,
                  selectedFilter === filter.key && styles.selectedFilterButton
                ]}
                onPress={() => setSelectedFilter(filter.key)}
              >
                <Text style={[
                  styles.filterButtonText,
                  selectedFilter === filter.key && styles.selectedFilterButtonText
                ]}>
                  {filter.label} ({filter.count})
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </View>

      {/* Estadísticas rápidas */}
      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{bookings.filter(b => b.status === 'confirmada').length}</Text>
          <Text style={styles.statLabel}>Confirmadas</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{bookings.filter(b => b.status === 'completada').length}</Text>
          <Text style={styles.statLabel}>Completadas</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>${bookings.reduce((sum, b) => sum + b.price, 0)}</Text>
          <Text style={styles.statLabel}>Total Gastado</Text>
        </View>
      </View>

      {/* Lista de reservas */}
      <View style={styles.bookingsContainer}>
        <Text style={styles.sectionTitle}>
          🎯 {filteredBookings.length} reservas encontradas
        </Text>
        
        {filteredBookings.map(booking => (
          <BookingCard
            key={booking.id}
            booking={booking}
            onPress={() => handleBookingPress(booking)}
            onCancel={handleCancelBooking}
          />
        ))}

        {filteredBookings.length === 0 && (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>🏖️ No hay reservas</Text>
            <Text style={styles.emptySubtext}>
              {selectedFilter === 'todas' 
                ? 'Aún no has hecho ninguna reserva' 
                : `No tienes reservas ${selectedFilter}`}
            </Text>
          </View>
        )}
      </View>

      {/* Botón para nueva reserva */}
      <View style={styles.actionContainer}>
        <TouchableOpacity style={styles.newBookingButton}>
          <Text style={styles.newBookingButtonText}>+ Nueva Reserva</Text>
        </TouchableOpacity>
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
  filtersContainer: {
    backgroundColor: '#fff',
    paddingVertical: 15,
  },
  filters: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    gap: 10,
  },
  filterButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#0066CC',
    backgroundColor: '#fff',
  },
  selectedFilterButton: {
    backgroundColor: '#0066CC',
  },
  filterButtonText: {
    color: '#0066CC',
    fontWeight: 'bold',
    fontSize: 14,
  },
  selectedFilterButtonText: {
    color: '#fff',
  },
  statsContainer: {
    flexDirection: 'row',
    padding: 20,
    justifyContent: 'space-around',
  },
  statCard: {
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    minWidth: 80,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  statNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#0066CC',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  bookingsContainer: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  bookingCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  boatEmoji: {
    fontSize: 32,
    marginRight: 12,
  },
  headerInfo: {
    flex: 1,
  },
  boatName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  status: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  price: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#0066CC',
  },
  cardContent: {
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  detailLabel: {
    fontSize: 14,
    color: '#666',
    flex: 1,
  },
  detailValue: {
    fontSize: 14,
    color: '#333',
    fontWeight: '500',
    flex: 1,
    textAlign: 'right',
  },
  cardActions: {
    borderTopWidth: 1,
    borderTopColor: '#eee',
    paddingTop: 12,
  },
  cancelButton: {
    backgroundColor: '#F44336',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  emptyState: {
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  actionContainer: {
    padding: 20,
  },
  newBookingButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  newBookingButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
