import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  InputAdornment,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';

interface Booking {
  id: string;
  boatName: string;
  customerName: string;
  startDate: string;
  endDate: string;
  totalAmount: number;
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled';
  paymentStatus: 'pending' | 'paid' | 'refunded';
  createdAt: string;
}

// Mock data
const mockBookings: Booking[] = [
  {
    id: 'BK001',
    boatName: 'Sea Explorer',
    customerName: 'Juan Pérez',
    startDate: '2025-07-01T10:00:00',
    endDate: '2025-07-01T14:00:00',
    totalAmount: 1000,
    status: 'confirmed',
    paymentStatus: 'paid',
    createdAt: '2025-06-25T15:30:00',
  },
  {
    id: 'BK002',
    boatName: 'Ocean Dream',
    customerName: 'María González',
    startDate: '2025-07-02T09:00:00',
    endDate: '2025-07-02T17:00:00',
    totalAmount: 1440,
    status: 'pending',
    paymentStatus: 'pending',
    createdAt: '2025-06-26T10:15:00',
  },
  {
    id: 'BK003',
    boatName: 'Wave Rider',
    customerName: 'Carlos Rodríguez',
    startDate: '2025-07-03T13:00:00',
    endDate: '2025-07-03T16:00:00',
    totalAmount: 960,
    status: 'completed',
    paymentStatus: 'paid',
    createdAt: '2025-06-26T16:45:00',
  },
];

export default function Bookings() {
  const [bookings, setBookings] = useState<Booking[]>(mockBookings);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterPayment, setFilterPayment] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed': return 'success';
      case 'pending': return 'warning';
      case 'completed': return 'info';
      case 'cancelled': return 'error';
      default: return 'default';
    }
  };

  const getPaymentStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'success';
      case 'pending': return 'warning';
      case 'refunded': return 'error';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'confirmed': return 'Confirmada';
      case 'pending': return 'Pendiente';
      case 'completed': return 'Completada';
      case 'cancelled': return 'Cancelada';
      default: return status;
    }
  };

  const getPaymentStatusLabel = (status: string) => {
    switch (status) {
      case 'paid': return 'Pagado';
      case 'pending': return 'Pendiente';
      case 'refunded': return 'Reembolsado';
      default: return status;
    }
  };

  const filteredBookings = bookings.filter(booking => {
    const matchesSearch =
      booking.boatName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = !filterStatus || booking.status === filterStatus;
    const matchesPayment = !filterPayment || booking.paymentStatus === filterPayment;

    return matchesSearch && matchesStatus && matchesPayment;
  });

  const handleView = (booking: Booking) => {
    setSelectedBooking(booking);
    setOpenDialog(true);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-VE', {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            📅 Gestión de Reservas
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Administra todas las reservas del sistema
          </Typography>
        </Box>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Buscar reservas..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Estado de Reserva</InputLabel>
                <Select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  label="Estado de Reserva"
                >
                  <MenuItem value="">Todos</MenuItem>
                  <MenuItem value="confirmed">Confirmada</MenuItem>
                  <MenuItem value="pending">Pendiente</MenuItem>
                  <MenuItem value="completed">Completada</MenuItem>
                  <MenuItem value="cancelled">Cancelada</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Estado de Pago</InputLabel>
                <Select
                  value={filterPayment}
                  onChange={(e) => setFilterPayment(e.target.value)}
                  label="Estado de Pago"
                >
                  <MenuItem value="">Todos</MenuItem>
                  <MenuItem value="paid">Pagado</MenuItem>
                  <MenuItem value="pending">Pendiente</MenuItem>
                  <MenuItem value="refunded">Reembolsado</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Typography variant="body2" color="text.secondary">
                {filteredBookings.length} reservas
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Bookings Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Embarcación</TableCell>
              <TableCell>Cliente</TableCell>
              <TableCell>Fecha Inicio</TableCell>
              <TableCell>Fecha Fin</TableCell>
              <TableCell>Monto</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell>Pago</TableCell>
              <TableCell>Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredBookings.map((booking) => (
              <TableRow key={booking.id}>
                <TableCell>{booking.id}</TableCell>
                <TableCell>{booking.boatName}</TableCell>
                <TableCell>{booking.customerName}</TableCell>
                <TableCell>{formatDate(booking.startDate)}</TableCell>
                <TableCell>{formatDate(booking.endDate)}</TableCell>
                <TableCell>${booking.totalAmount}</TableCell>
                <TableCell>
                  <Chip
                    label={getStatusLabel(booking.status)}
                    color={getStatusColor(booking.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={getPaymentStatusLabel(booking.paymentStatus)}
                    color={getPaymentStatusColor(booking.paymentStatus) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <IconButton size="small" onClick={() => handleView(booking)}>
                    <ViewIcon />
                  </IconButton>
                  <IconButton size="small" onClick={() => handleView(booking)}>
                    <EditIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* View/Edit Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Detalles de la Reserva
        </DialogTitle>
        <DialogContent>
          {selectedBooking && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="ID de Reserva"
                  value={selectedBooking.id}
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Embarcación"
                  value={selectedBooking.boatName}
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Cliente"
                  value={selectedBooking.customerName}
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Monto Total"
                  value={`$${selectedBooking.totalAmount}`}
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Fecha de Inicio"
                  value={formatDate(selectedBooking.startDate)}
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Fecha de Fin"
                  value={formatDate(selectedBooking.endDate)}
                  InputProps={{ readOnly: true }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Estado de Reserva</InputLabel>
                  <Select
                    value={selectedBooking.status}
                    label="Estado de Reserva"
                  >
                    <MenuItem value="confirmed">Confirmada</MenuItem>
                    <MenuItem value="pending">Pendiente</MenuItem>
                    <MenuItem value="completed">Completada</MenuItem>
                    <MenuItem value="cancelled">Cancelada</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Estado de Pago</InputLabel>
                  <Select
                    value={selectedBooking.paymentStatus}
                    label="Estado de Pago"
                  >
                    <MenuItem value="paid">Pagado</MenuItem>
                    <MenuItem value="pending">Pendiente</MenuItem>
                    <MenuItem value="refunded">Reembolsado</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>
            Cancelar
          </Button>
          <Button variant="contained" onClick={() => setOpenDialog(false)}>
            Guardar Cambios
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}