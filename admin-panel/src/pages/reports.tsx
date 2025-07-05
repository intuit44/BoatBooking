import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
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
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Download as DownloadIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Assessment as AssessmentIcon,
  DateRange as DateRangeIcon,
} from '@mui/icons-material';

interface RevenueData {
  period: string;
  revenue: number;
  bookings: number;
  growth: number;
}

interface PopularBoat {
  name: string;
  bookings: number;
  revenue: number;
  rating: number;
}

interface CustomerData {
  segment: string;
  count: number;
  percentage: number;
  revenue: number;
}

// Mock data
const revenueData: RevenueData[] = [
  { period: 'Enero 2025', revenue: 15000, bookings: 45, growth: 12.5 },
  { period: 'Febrero 2025', revenue: 18000, bookings: 52, growth: 20.0 },
  { period: 'Marzo 2025', revenue: 22000, bookings: 68, growth: 22.2 },
  { period: 'Abril 2025', revenue: 19500, bookings: 58, growth: -11.4 },
  { period: 'Mayo 2025', revenue: 25000, bookings: 75, growth: 28.2 },
  { period: 'Junio 2025', revenue: 28000, bookings: 82, growth: 12.0 },
];

const popularBoats: PopularBoat[] = [
  { name: 'Sea Explorer', bookings: 35, revenue: 8750, rating: 4.8 },
  { name: 'Ocean Dream', bookings: 28, revenue: 5040, rating: 4.5 },
  { name: 'Wave Rider', bookings: 22, revenue: 7040, rating: 4.9 },
  { name: 'Marina Star', bookings: 18, revenue: 4500, rating: 4.3 },
  { name: 'Blue Horizon', bookings: 15, revenue: 3750, rating: 4.6 },
];

const customerSegments: CustomerData[] = [
  { segment: 'Clientes Frecuentes', count: 45, percentage: 35, revenue: 18500 },
  { segment: 'Clientes Ocasionales', count: 68, percentage: 53, revenue: 15200 },
  { segment: 'Clientes Nuevos', count: 15, percentage: 12, revenue: 4800 },
];

export default function Reports() {
  const [dateRange, setDateRange] = useState('last_6_months');
  const [reportType, setReportType] = useState('revenue');

  const totalRevenue = revenueData.reduce((sum, item) => sum + item.revenue, 0);
  const totalBookings = revenueData.reduce((sum, item) => sum + item.bookings, 0);
  const averageBookingValue = totalRevenue / totalBookings;

  const handleExport = (format: 'pdf' | 'excel') => {
    // Simulate export functionality
    alert(`Exportando reporte en formato ${format.toUpperCase()}...`);
  };

  const getGrowthIcon = (growth: number) => {
    return growth >= 0 ? (
      <TrendingUpIcon color="success" fontSize="small" />
    ) : (
      <TrendingDownIcon color="error" fontSize="small" />
    );
  };

  const getGrowthColor = (growth: number) => {
    return growth >= 0 ? 'success' : 'error';
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            📊 Reportes y Estadísticas
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Análisis detallado del rendimiento del negocio
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => handleExport('pdf')}
          >
            PDF
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => handleExport('excel')}
          >
            Excel
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Período</InputLabel>
                <Select
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value)}
                  label="Período"
                >
                  <MenuItem value="last_month">Último Mes</MenuItem>
                  <MenuItem value="last_3_months">Últimos 3 Meses</MenuItem>
                  <MenuItem value="last_6_months">Últimos 6 Meses</MenuItem>
                  <MenuItem value="last_year">Último Año</MenuItem>
                  <MenuItem value="custom">Personalizado</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Reporte</InputLabel>
                <Select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  label="Tipo de Reporte"
                >
                  <MenuItem value="revenue">Ingresos</MenuItem>
                  <MenuItem value="bookings">Reservas</MenuItem>
                  <MenuItem value="customers">Clientes</MenuItem>
                  <MenuItem value="boats">Embarcaciones</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="body2" color="text.secondary">
                Datos actualizados: {new Date().toLocaleDateString('es-VE')}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary" gutterBottom>
                💰 Ingresos Totales
              </Typography>
              <Typography variant="h4">
                ${totalRevenue.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Últimos 6 meses
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary" gutterBottom>
                📅 Total Reservas
              </Typography>
              <Typography variant="h4">
                {totalBookings}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Reservas completadas
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary" gutterBottom>
                💵 Valor Promedio
              </Typography>
              <Typography variant="h4">
                ${Math.round(averageBookingValue)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Por reserva
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary" gutterBottom>
                📈 Crecimiento
              </Typography>
              <Typography variant="h4" color="success.main">
                +15.2%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                vs. período anterior
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Revenue Trend */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📈 Tendencia de Ingresos
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Período</TableCell>
                      <TableCell align="right">Ingresos</TableCell>
                      <TableCell align="right">Reservas</TableCell>
                      <TableCell align="right">Crecimiento</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {revenueData.map((row) => (
                      <TableRow key={row.period}>
                        <TableCell>{row.period}</TableCell>
                        <TableCell align="right">
                          ${row.revenue.toLocaleString()}
                        </TableCell>
                        <TableCell align="right">{row.bookings}</TableCell>
                        <TableCell align="right">
                          <Box display="flex" alignItems="center" justifyContent="flex-end" gap={1}>
                            {getGrowthIcon(row.growth)}
                            <Typography
                              variant="body2"
                              color={getGrowthColor(row.growth) + '.main'}
                            >
                              {row.growth > 0 ? '+' : ''}{row.growth.toFixed(1)}%
                            </Typography>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Popular Boats */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🛥️ Embarcaciones Populares
              </Typography>
              {popularBoats.map((boat, index) => (
                <Box key={boat.name} sx={{ mb: 2 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" fontWeight="bold">
                      {index + 1}. {boat.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      ⭐ {boat.rating}
                    </Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {boat.bookings} reservas • ${boat.revenue.toLocaleString()}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(boat.bookings / popularBoats[0].bookings) * 100}
                    sx={{ mt: 1, height: 6, borderRadius: 3 }}
                  />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* Customer Segments */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                👥 Segmentación de Clientes
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Segmento</TableCell>
                      <TableCell align="right">Cantidad</TableCell>
                      <TableCell align="right">Porcentaje</TableCell>
                      <TableCell align="right">Ingresos</TableCell>
                      <TableCell align="right">Distribución</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {customerSegments.map((segment) => (
                      <TableRow key={segment.segment}>
                        <TableCell>{segment.segment}</TableCell>
                        <TableCell align="right">{segment.count}</TableCell>
                        <TableCell align="right">{segment.percentage}%</TableCell>
                        <TableCell align="right">
                          ${segment.revenue.toLocaleString()}
                        </TableCell>
                        <TableCell align="right">
                          <Box sx={{ width: 100 }}>
                            <LinearProgress
                              variant="determinate"
                              value={segment.percentage}
                              sx={{ height: 8, borderRadius: 4 }}
                            />
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}