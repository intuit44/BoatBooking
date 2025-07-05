import { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Button,
} from '@mui/material';
import {
  TrendingUp,
  DirectionsBoat,
  EventNote,
  People,
  AttachMoney,
  Visibility,
  Edit,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

// Mock data - En producción vendría de la API
const mockStats = {
  totalBoats: 45,
  totalBookings: 128,
  totalUsers: 89,
  totalRevenue: 15420,
  monthlyGrowth: 12.5,
};

const mockRecentBookings = [
  {
    id: '1',
    boatName: 'Sea Explorer',
    customerName: 'Juan Pérez',
    date: '2024-01-15',
    status: 'confirmed',
    amount: 250,
  },
  {
    id: '2',
    boatName: 'Ocean Dream',
    customerName: 'María González',
    date: '2024-01-14',
    status: 'pending',
    amount: 180,
  },
  {
    id: '3',
    boatName: 'Wave Rider',
    customerName: 'Carlos Rodríguez',
    date: '2024-01-13',
    status: 'completed',
    amount: 320,
  },
];

const mockChartData = [
  { name: 'Ene', reservas: 12, ingresos: 2400 },
  { name: 'Feb', reservas: 19, ingresos: 3800 },
  { name: 'Mar', reservas: 15, ingresos: 3000 },
  { name: 'Abr', reservas: 25, ingresos: 5000 },
  { name: 'May', reservas: 22, ingresos: 4400 },
  { name: 'Jun', reservas: 30, ingresos: 6000 },
];

const mockBoatTypes = [
  { name: 'Yates', value: 35, color: '#0066CC' },
  { name: 'Lanchas', value: 25, color: '#FF9800' },
  { name: 'Veleros', value: 20, color: '#4CAF50' },
  { name: 'Motos de Agua', value: 20, color: '#F44336' },
];

export default function Dashboard() {
  const [stats, setStats] = useState(mockStats);
  const [recentBookings, setRecentBookings] = useState(mockRecentBookings);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed': return 'success';
      case 'pending': return 'warning';
      case 'completed': return 'info';
      case 'cancelled': return 'error';
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

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        📊 Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Resumen general del sistema de alquiler de embarcaciones
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Total Embarcaciones
                  </Typography>
                  <Typography variant="h4">
                    {stats.totalBoats}
                  </Typography>
                </Box>
                <DirectionsBoat color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Total Reservas
                  </Typography>
                  <Typography variant="h4">
                    {stats.totalBookings}
                  </Typography>
                </Box>
                <EventNote color="secondary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Total Usuarios
                  </Typography>
                  <Typography variant="h4">
                    {stats.totalUsers}
                  </Typography>
                </Box>
                <People color="info" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Ingresos Totales
                  </Typography>
                  <Typography variant="h4">
                    ${stats.totalRevenue.toLocaleString()}
                  </Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    <TrendingUp color="success" sx={{ fontSize: 16, mr: 0.5 }} />
                    <Typography variant="body2" color="success.main">
                      +{stats.monthlyGrowth}%
                    </Typography>
                  </Box>
                </Box>
                <AttachMoney color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📈 Reservas e Ingresos Mensuales
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={mockChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Bar yAxisId="left" dataKey="reservas" fill="#0066CC" />
                  <Line yAxisId="right" type="monotone" dataKey="ingresos" stroke="#FF9800" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🛥️ Tipos de Embarcaciones
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={mockBoatTypes}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {mockBoatTypes.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Bookings */}
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              📋 Reservas Recientes
            </Typography>
            <Button variant="outlined" size="small">
              Ver Todas
            </Button>
          </Box>
          <TableContainer component={Paper} elevation={0}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Embarcación</TableCell>
                  <TableCell>Cliente</TableCell>
                  <TableCell>Fecha</TableCell>
                  <TableCell>Estado</TableCell>
                  <TableCell>Monto</TableCell>
                  <TableCell>Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recentBookings.map((booking) => (
                  <TableRow key={booking.id}>
                    <TableCell>{booking.boatName}</TableCell>
                    <TableCell>{booking.customerName}</TableCell>
                    <TableCell>{booking.date}</TableCell>
                    <TableCell>
                      <Chip
                        label={getStatusLabel(booking.status)}
                        color={getStatusColor(booking.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>${booking.amount}</TableCell>
                    <TableCell>
                      <IconButton size="small">
                        <Visibility />
                      </IconButton>
                      <IconButton size="small">
                        <Edit />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}