import { useState, useEffect } from 'react';
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
  Avatar,
  CardMedia,
  CardActions,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';

interface Boat {
  id: string;
  name: string;
  type: string;
  capacity: number;
  pricePerHour: number;
  location: {
    state: string;
    marina: string;
  };
  images: string[];
  status: 'active' | 'inactive' | 'maintenance';
  rating: number;
  featured: boolean;
}

// Mock data
const mockBoats: Boat[] = [
  {
    id: '1',
    name: 'Sea Explorer',
    type: 'yacht',
    capacity: 12,
    pricePerHour: 250,
    location: { state: 'Nueva Esparta', marina: 'Marina Margarita' },
    images: ['https://example.com/boat1.jpg'],
    status: 'active',
    rating: 4.8,
    featured: true,
  },
  {
    id: '2',
    name: 'Ocean Dream',
    type: 'motorboat',
    capacity: 8,
    pricePerHour: 180,
    location: { state: 'Vargas', marina: 'Marina La Guaira' },
    images: ['https://example.com/boat2.jpg'],
    status: 'active',
    rating: 4.5,
    featured: false,
  },
  {
    id: '3',
    name: 'Wave Rider',
    type: 'sailboat',
    capacity: 6,
    pricePerHour: 320,
    location: { state: 'Falcón', marina: 'Marina Tucacas' },
    images: ['https://example.com/boat3.jpg'],
    status: 'maintenance',
    rating: 4.9,
    featured: true,
  },
];

const boatTypes = [
  { value: 'yacht', label: '🛥️ Yate' },
  { value: 'motorboat', label: '🚤 Lancha' },
  { value: 'sailboat', label: '⛵ Velero' },
  { value: 'jetski', label: '🏄‍♂️ Moto de Agua' },
  { value: 'catamaran', label: '🛥️ Catamarán' },
];

export default function Boats() {
  const [boats, setBoats] = useState<Boat[]>(mockBoats);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedBoat, setSelectedBoat] = useState<Boat | null>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'maintenance': return 'warning';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active': return 'Activo';
      case 'inactive': return 'Inactivo';
      case 'maintenance': return 'Mantenimiento';
      default: return status;
    }
  };

  const getTypeLabel = (type: string) => {
    const typeObj = boatTypes.find(t => t.value === type);
    return typeObj ? typeObj.label : type;
  };

  const filteredBoats = boats.filter(boat => {
    const matchesSearch = boat.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      boat.location.marina.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = !filterType || boat.type === filterType;
    const matchesStatus = !filterStatus || boat.status === filterStatus;

    return matchesSearch && matchesType && matchesStatus;
  });

  const handleEdit = (boat: Boat) => {
    setSelectedBoat(boat);
    setOpenDialog(true);
  };

  const handleDelete = (boatId: string) => {
    if (confirm('¿Estás seguro de que deseas eliminar esta embarcación?')) {
      setBoats(boats.filter(boat => boat.id !== boatId));
    }
  };

  const handleAddNew = () => {
    setSelectedBoat(null);
    setOpenDialog(true);
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            🛥️ Gestión de Embarcaciones
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Administra el catálogo de embarcaciones disponibles
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddNew}
        >
          Nueva Embarcación
        </Button>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Buscar embarcaciones..."
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
                <InputLabel>Tipo</InputLabel>
                <Select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  label="Tipo"
                >
                  <MenuItem value="">Todos</MenuItem>
                  {boatTypes.map(type => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Estado</InputLabel>
                <Select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  label="Estado"
                >
                  <MenuItem value="">Todos</MenuItem>
                  <MenuItem value="active">Activo</MenuItem>
                  <MenuItem value="inactive">Inactivo</MenuItem>
                  <MenuItem value="maintenance">Mantenimiento</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Typography variant="body2" color="text.secondary">
                {filteredBoats.length} embarcaciones
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Boats Grid */}
      <Grid container spacing={3}>
        {filteredBoats.map((boat) => (
          <Grid item xs={12} sm={6} md={4} key={boat.id}>
            <Card>
              <CardMedia
                component="img"
                height="200"
                image={boat.images[0] || '/placeholder-boat.jpg'}
                alt={boat.name}
              />
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="start" mb={1}>
                  <Typography variant="h6" component="div">
                    {boat.name}
                  </Typography>
                  {boat.featured && (
                    <Chip label="⭐ Destacado" size="small" color="warning" />
                  )}
                </Box>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {getTypeLabel(boat.type)} • {boat.capacity} personas
                </Typography>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  📍 {boat.location.marina}, {boat.location.state}
                </Typography>

                <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
                  <Typography variant="h6" color="primary">
                    ${boat.pricePerHour}/hora
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body2">⭐ {boat.rating}</Typography>
                    <Chip
                      label={getStatusLabel(boat.status)}
                      color={getStatusColor(boat.status) as any}
                      size="small"
                    />
                  </Box>
                </Box>
              </CardContent>

              <CardActions>
                <IconButton size="small" onClick={() => handleEdit(boat)}>
                  <ViewIcon />
                </IconButton>
                <IconButton size="small" onClick={() => handleEdit(boat)}>
                  <EditIcon />
                </IconButton>
                <IconButton size="small" onClick={() => handleDelete(boat.id)}>
                  <DeleteIcon />
                </IconButton>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedBoat ? 'Editar Embarcación' : 'Nueva Embarcación'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Nombre"
                defaultValue={selectedBoat?.name || ''}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Tipo</InputLabel>
                <Select
                  defaultValue={selectedBoat?.type || ''}
                  label="Tipo"
                >
                  {boatTypes.map(type => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Capacidad"
                type="number"
                defaultValue={selectedBoat?.capacity || ''}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Precio por Hora ($)"
                type="number"
                defaultValue={selectedBoat?.pricePerHour || ''}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Descripción"
                multiline
                rows={3}
                placeholder="Describe las características de la embarcación..."
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>
            Cancelar
          </Button>
          <Button variant="contained" onClick={() => setOpenDialog(false)}>
            {selectedBoat ? 'Actualizar' : 'Crear'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}