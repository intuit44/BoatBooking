import React, { useState } from 'react';
import { useRouter } from 'next/router';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  InputAdornment,
  IconButton,
  Container,
  Paper,
  Avatar,
  Divider,
  Chip
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  AdminPanelSettings,
  Security,
  VpnKey,
  Login as LoginIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Validaciones básicas
      if (!email || !password) {
        setError('Por favor complete todos los campos');
        return;
      }

      if (!email.includes('@')) {
        setError('Por favor ingrese un email válido');
        return;
      }

      // La función login no retorna nada, pero redirige automáticamente en caso de éxito
      // o lanza un error en caso de fallo
      await login(email, password);

      // Si llegamos aquí, el login fue exitoso
      toast.success('¡Bienvenido al Panel de Administración!');
      // No necesitamos router.push aquí porque login() ya lo hace

    } catch (err: any) {
      setError(err.message || 'Error de conexión. Intente nuevamente.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };


  const handleTogglePassword = () => {
    setShowPassword(!showPassword);
  };

  // Credenciales de demostración
  const demoCredentials = [
    { role: 'Super Admin', email: 'admin@boatrentals.ve', password: 'admin123' },
    { role: 'Operador', email: 'operador@boatrentals.ve', password: 'operador123' }
  ];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 2
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={24}
          sx={{
            borderRadius: 4,
            overflow: 'hidden',
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)'
          }}
        >
          {/* Header */}
          <Box
            sx={{
              background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
              color: 'white',
              padding: 4,
              textAlign: 'center'
            }}
          >
            <Avatar
              sx={{
                width: 80,
                height: 80,
                margin: '0 auto 16px',
                background: 'rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)'
              }}
            >
              <AdminPanelSettings sx={{ fontSize: 40 }} />
            </Avatar>
            <Typography variant="h4" fontWeight="bold" gutterBottom>
              Panel de Administración
            </Typography>
            <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
              Boat Rentals Venezuela
            </Typography>
          </Box>

          <CardContent sx={{ padding: 4 }}>
            {/* Formulario de Login */}
            <form onSubmit={handleSubmit}>
              <Box sx={{ mb: 3 }}>
                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  variant="outlined"
                  disabled={loading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <VpnKey color="primary" />
                      </InputAdornment>
                    )
                  }}
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  label="Contraseña"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  variant="outlined"
                  disabled={loading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Security color="primary" />
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={handleTogglePassword}
                          edge="end"
                          disabled={loading}
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    )
                  }}
                />
              </Box>

              {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  {error}
                </Alert>
              )}

              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={loading}
                startIcon={<LoginIcon />}
                sx={{
                  py: 1.5,
                  background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #1976D2 30%, #0288D1 90%)'
                  }
                }}
              >
                {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
              </Button>
            </form>

            {/* Credenciales de Demostración */}
            <Divider sx={{ my: 4 }}>
              <Chip label="Credenciales de Demostración" color="primary" variant="outlined" />
            </Divider>

            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Usa estas credenciales para probar el sistema:
              </Typography>

              {demoCredentials.map((cred, index) => (
                <Paper
                  key={index}
                  variant="outlined"
                  sx={{
                    p: 2,
                    mb: 2,
                    background: 'rgba(33, 150, 243, 0.05)',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    '&:hover': {
                      background: 'rgba(33, 150, 243, 0.1)',
                      transform: 'translateY(-2px)'
                    }
                  }}
                  onClick={() => {
                    setEmail(cred.email);
                    setPassword(cred.password);
                    toast.success(`Credenciales de ${cred.role} cargadas`);
                  }}
                >
                  <Typography variant="subtitle2" color="primary" fontWeight="bold">
                    {cred.role}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Email: {cred.email}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Contraseña: {cred.password}
                  </Typography>
                </Paper>
              ))}
            </Box>

            {/* Footer */}
            <Box sx={{ textAlign: 'center', mt: 4, pt: 3, borderTop: '1px solid #e0e0e0' }}>
              <Typography variant="body2" color="text.secondary">
                © 2024 Boat Rentals Venezuela - Panel Administrativo
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Versión 1.0.0 | Desarrollado con ❤️ en Venezuela
              </Typography>
            </Box>
          </CardContent>
        </Paper>
      </Container>
    </Box>
  );
};

export default LoginPage;