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
  Avatar,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';

interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: 'admin' | 'customer' | 'operator';
  status: 'active' | 'inactive' | 'blocked';
  avatar?: string;
  createdAt: string;
  lastLogin?: string;
  totalBookings: number;
  totalSpent: number;
}

// Mock data
const mockUsers: User[] = [
  {
    id: 'USR001',
    name: 'Juan Pérez',
    email: 'juan.perez@email.com',
    phone: '+58 412-1234567',
    role: 'customer',
    status: 'active',
    createdAt: '2025-01-15T10:30:00',
    lastLogin: '2025-06-27T14:20:00',
    totalBookings: 5,
    totalSpent: 2500,
  },
  {
    id: 'USR002',
    name: 'María González',
    email: 'maria.gonzalez@email.com',
    phone: '+58 414-9876543',
    role: 'customer',
    status: 'active',
    createdAt: '2025-02-20T16:45:00',
    lastLogin: '2025-06-26T09:15:00',
    totalBookings: 3,
    totalSpent: 1800,
  },
  {
    id: 'USR003',
    name: 'Carlos Admin',
    email: 'carlos.admin@boatrentals.com',
    phone: '+58 416-5555555',
    role: 'admin',
    status: 'active',
    createdAt: '2024-12-01T08:00:00',
    lastLogin: '2025-06-27T15:30:00',
    totalBookings: 0,
    totalSpent: 0,
  },
  {
    id: 'USR004',
    name: 'Ana Operadora',
    email: 'ana.operadora@boatrentals.com',
    phone: '+58 424-7777777',
    role: 'operator',
    status: 'active',
    createdAt: '2025-03-10T12:00:00',
    lastLogin: '2025-06-27T11:45:00',
    totalBookings: 0,
    totalSpent: 0,
  },
];

export default function Users() {
  const [users, setUsers] = useState<User[]>(mockUsers);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin': return 'error';
      case 'operator': return 'warning';
      case 'customer': return 'primary';
      default: return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'blocked': return 'error';
      default: return 'default';
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'admin': return 'Administrador';
      case 'operator': return 'Operador';
      case 'customer': return 'Cliente';
      default: return role;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active': return 'Activo';
      case 'inactive': return 'Inactivo';
      case 'blocked': return 'Bloqueado';
      default: return status;
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch =
      user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.phone.includes(searchTerm);
    const matchesRole = !filterRole || user.role === filterRole;
    const matchesStatus = !filterStatus || user.status === filterStatus;

    return matchesSearch && matchesRole && matchesStatus;
  });

  const handleView = (user: User) => {
    setSelectedUser(user);
    setOpenDialog(true);
  };

  const handleAddNew = () => {
    setSelectedUser(null);
    setOpenDialog(true);
  };

  const handleToggleStatus = (userId: string) => {
    setUsers(users.map(user =>
      user.id === userId
        ? { ...user, status: user.status === 'active' ? 'inactive' : 'active' }
        : user
    ));
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
            👥 Administración de Usuarios
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Gestiona todos los usuarios del sistema
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddNew}
        >
          Nuevo Usuario
        </Button>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Buscar usuarios..."
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
                <InputLabel>Rol</InputLabel>
                <Select
                  value={filterRole}
                  onChange={(e) => setFilterRole(e.target.value)}
                  label="Rol"
                >
                  <MenuItem value="">Todos</MenuItem>
                  <MenuItem value="admin">Administrador</MenuItem>
                  <MenuItem value="operator">Operador</MenuItem>
                  <MenuItem value="customer">Cliente</MenuItem>
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
                  <MenuItem value="blocked">Bloqueado</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Typography variant="body2" color="text.secondary">
                {filteredUsers.length} usuarios
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Users Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Usuario</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Teléfono</TableCell>
              <TableCell>Rol</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell>Reservas</TableCell>
              <TableCell>Total Gastado</TableCell>
              <TableCell>Último Acceso</TableCell>
              <TableCell>Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredUsers.map((user) => (
              <TableRow key={user.id}>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Avatar src={user.avatar}>
                      {user.name.charAt(0)}
                    </Avatar>
                    <Box>
                      <Typography variant="body2" fontWeight="bold">
                        {user.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ID: {user.id}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>{user.phone}</TableCell>
                <TableCell>
                  <Chip
                    label={getRoleLabel(user.role)}
                    color={getRoleColor(user.role) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={getStatusLabel(user.status)}
                    color={getStatusColor(user.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>{user.totalBookings}</TableCell>
                <TableCell>${user.totalSpent}</TableCell>
                <TableCell>
                  {user.lastLogin ? formatDate(user.lastLogin) : 'Nunca'}
                </TableCell>
                <TableCell>
                  <IconButton size="small" onClick={() => handleView(user)}>
                    <ViewIcon />
                  </IconButton>
                  <IconButton size="small" onClick={() => handleView(user)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleToggleStatus(user.id)}
                    color={user.status === 'active' ? 'error' : 'success'}
                  >
                    {user.status === 'active' ? <BlockIcon /> : <CheckCircleIcon />}
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedUser ? 'Editar Usuario' : 'Nuevo Usuario'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Nombre Completo"
                defaultValue={selectedUser?.name || ''}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                defaultValue={selectedUser?.email || ''}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Teléfono"
                defaultValue={selectedUser?.phone || ''}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Rol</InputLabel>
                <Select
                  defaultValue={selectedUser?.role || 'customer'}
                  label="Rol"
                >
                  <MenuItem value="admin">Administrador</MenuItem>
                  <MenuItem value="operator">Operador</MenuItem>
                  <MenuItem value="customer">Cliente</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Estado</InputLabel>
                <Select
                  defaultValue={selectedUser?.status || 'active'}
                  label="Estado"
                >
                  <MenuItem value="active">Activo</MenuItem>
                  <MenuItem value="inactive">Inactivo</MenuItem>
                  <MenuItem value="blocked">Bloqueado</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={<Switch defaultChecked={selectedUser?.status === 'active'} />}
                label="Usuario Activo"
              />
            </Grid>
            {selectedUser && (
              <>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Total de Reservas"
                    value={selectedUser.totalBookings}
                    InputProps={{ readOnly: true }}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Total Gastado"
                    value={`$${selectedUser.totalSpent}`}
                    InputProps={{ readOnly: true }}
                  />
                </Grid>
              </>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>
            Cancelar
          </Button>
          <Button variant="contained" onClick={() => setOpenDialog(false)}>
            {selectedUser ? 'Actualizar' : 'Crear'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}