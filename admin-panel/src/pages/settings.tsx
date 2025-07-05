import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Payment as PaymentIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export default function Settings() {
  const [tabValue, setTabValue] = useState(0);
  const [settings, setSettings] = useState({
    // General Settings
    siteName: 'Boat Rentals VE',
    siteDescription: 'Alquiler de embarcaciones en Venezuela',
    contactEmail: 'info@boatrentals.ve',
    contactPhone: '+58 212-1234567',

    // Business Settings
    businessHours: {
      start: '08:00',
      end: '18:00',
    },
    timezone: 'America/Caracas',
    currency: 'USD',
    taxRate: 16,

    // Booking Settings
    minBookingHours: 2,
    maxBookingDays: 7,
    advanceBookingDays: 30,
    cancellationHours: 24,

    // Notifications
    emailNotifications: true,
    smsNotifications: false,
    pushNotifications: true,

    // Security
    twoFactorAuth: false,
    sessionTimeout: 30,
    passwordExpiry: 90,

    // Payment
    paymentMethods: ['credit_card', 'bank_transfer', 'paypal'],
    requireDeposit: true,
    depositPercentage: 30,
  });

  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleSave = async () => {
    setSaveStatus('saving');
    // Simulate API call
    setTimeout(() => {
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }, 1000);
  };

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleNestedSettingChange = (parent: string, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [parent]: {
        ...(prev[parent as keyof typeof prev] as object || {}),
        [key]: value
      }
    }));
  };


  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            ⚙️ Configuraciones del Sistema
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Administra las configuraciones generales de la plataforma
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSave}
          disabled={saveStatus === 'saving'}
        >
          {saveStatus === 'saving' ? 'Guardando...' : 'Guardar Cambios'}
        </Button>
      </Box>

      {saveStatus === 'saved' && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Configuraciones guardadas exitosamente
        </Alert>
      )}

      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="General" icon={<SettingsIcon />} />
            <Tab label="Reservas" icon={<NotificationsIcon />} />
            <Tab label="Pagos" icon={<PaymentIcon />} />
            <Tab label="Seguridad" icon={<SecurityIcon />} />
          </Tabs>
        </Box>

        {/* General Settings */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Información General
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Nombre del Sitio"
                value={settings.siteName}
                onChange={(e) => handleSettingChange('siteName', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Email de Contacto"
                value={settings.contactEmail}
                onChange={(e) => handleSettingChange('contactEmail', e.target.value)}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Descripción del Sitio"
                multiline
                rows={3}
                value={settings.siteDescription}
                onChange={(e) => handleSettingChange('siteDescription', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Teléfono de Contacto"
                value={settings.contactPhone}
                onChange={(e) => handleSettingChange('contactPhone', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Zona Horaria</InputLabel>
                <Select
                  value={settings.timezone}
                  onChange={(e) => handleSettingChange('timezone', e.target.value)}
                  label="Zona Horaria"
                >
                  <MenuItem value="America/Caracas">Venezuela (UTC-4)</MenuItem>
                  <MenuItem value="America/New_York">New York (UTC-5)</MenuItem>
                  <MenuItem value="America/Los_Angeles">Los Angeles (UTC-8)</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Configuración de Negocio
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Hora de Apertura"
                type="time"
                value={settings.businessHours.start}
                onChange={(e) => handleNestedSettingChange('businessHours', 'start', e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Hora de Cierre"
                type="time"
                value={settings.businessHours.end}
                onChange={(e) => handleNestedSettingChange('businessHours', 'end', e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Moneda</InputLabel>
                <Select
                  value={settings.currency}
                  onChange={(e) => handleSettingChange('currency', e.target.value)}
                  label="Moneda"
                >
                  <MenuItem value="USD">USD - Dólar Americano</MenuItem>
                  <MenuItem value="VES">VES - Bolívar Venezolano</MenuItem>
                  <MenuItem value="EUR">EUR - Euro</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Tasa de Impuesto (%)"
                type="number"
                value={settings.taxRate}
                onChange={(e) => handleSettingChange('taxRate', Number(e.target.value))}
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Booking Settings */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Configuración de Reservas
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Mínimo de Horas por Reserva"
                type="number"
                value={settings.minBookingHours}
                onChange={(e) => handleSettingChange('minBookingHours', Number(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Máximo de Días por Reserva"
                type="number"
                value={settings.maxBookingDays}
                onChange={(e) => handleSettingChange('maxBookingDays', Number(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Días de Anticipación para Reservar"
                type="number"
                value={settings.advanceBookingDays}
                onChange={(e) => handleSettingChange('advanceBookingDays', Number(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Horas Mínimas para Cancelar"
                type="number"
                value={settings.cancellationHours}
                onChange={(e) => handleSettingChange('cancellationHours', Number(e.target.value))}
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Notificaciones
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.emailNotifications}
                    onChange={(e) => handleSettingChange('emailNotifications', e.target.checked)}
                  />
                }
                label="Notificaciones por Email"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.smsNotifications}
                    onChange={(e) => handleSettingChange('smsNotifications', e.target.checked)}
                  />
                }
                label="Notificaciones por SMS"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.pushNotifications}
                    onChange={(e) => handleSettingChange('pushNotifications', e.target.checked)}
                  />
                }
                label="Notificaciones Push"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Payment Settings */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Configuración de Pagos
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Métodos de Pago Activos
              </Typography>
              <Box display="flex" gap={1} flexWrap="wrap">
                <Chip label="💳 Tarjeta de Crédito" color="primary" />
                <Chip label="🏦 Transferencia Bancaria" color="primary" />
                <Chip label="💰 PayPal" color="primary" />
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.requireDeposit}
                    onChange={(e) => handleSettingChange('requireDeposit', e.target.checked)}
                  />
                }
                label="Requerir Depósito"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Porcentaje de Depósito (%)"
                type="number"
                value={settings.depositPercentage}
                onChange={(e) => handleSettingChange('depositPercentage', Number(e.target.value))}
                disabled={!settings.requireDeposit}
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Security Settings */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Configuración de Seguridad
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.twoFactorAuth}
                    onChange={(e) => handleSettingChange('twoFactorAuth', e.target.checked)}
                  />
                }
                label="Autenticación de Dos Factores"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Tiempo de Sesión (minutos)"
                type="number"
                value={settings.sessionTimeout}
                onChange={(e) => handleSettingChange('sessionTimeout', Number(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Expiración de Contraseña (días)"
                type="number"
                value={settings.passwordExpiry}
                onChange={(e) => handleSettingChange('passwordExpiry', Number(e.target.value))}
              />
            </Grid>
            <Grid item xs={12}>
              <Alert severity="info">
                Los cambios de seguridad requieren que los usuarios vuelvan a iniciar sesión.
              </Alert>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>
    </Box>
  );
}